"""Unweb API – FastAPI application."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from os import environ
from time import time

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .auth import verify_api_key
from .crawler import fetch_url
from .extractor import extract_content
from .llm_extractor import extract_with_llm, merge_extraction
from .rate_limit import FreeTierLimiter, local_dev_limiter
from .search import batch_extract, search_web, summarize_results
from .schemas import (
    AuthRequest,
    AuthResponse,
    ErrorResponse,
    ExtractRequest,
    ExtractResponse,
    KeyItem,
    KeysResponse,
    PublishRequest,
    PublishResponse,
    SearchRequest,
    SearchResponse,
    SiteInfo,
)
from .metrics import get_dashboard_stats, get_timeline
from .supabase import (
    authenticate_user,
    cache_get,
    cache_set,
    create_api_key,
    create_site,
    create_user,
    get_site_by_id,
    get_site_by_name,
    list_user_keys,
    list_user_sites,
    track_event,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.limiter = local_dev_limiter._limiter
    logger.info("startup complete")
    yield
    logger.info("shutdown complete")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Unweb API",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Health check endpoint"},
        {"name": "extract", "description": "Extract structured content from a URL"},
        {"name": "publish", "description": "Publish content as a new site"},
        {"name": "sites", "description": "Retrieve published site information"},
        {"name": "auth", "description": "User registration, login, and API key management"},
    ],
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
origins = environ.get("CORS_ORIGINS", "http://localhost:3000,https://fuhon42-cmyk.github.io").split(",")
origin_regex = environ.get("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app|https://.*\.github\.io")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)


# ---------------------------------------------------------------------------
# Request logging + metrics middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def track_requests(request: Request, call_next):
    start = time()

    user_id = None
    api_key = request.headers.get("x-api-key")
    if api_key:
        if environ.get("UNWEB_DEV", "").lower() == "true":
            user_id = environ.get("DEV_USER_ID", "062b5af1-9058-44dd-b2e2-6d60b90cda15")
        else:
            try:
                from .auth import verify_api_key as _vk
                user_id = _vk(request, api_key)
            except Exception:
                pass

    response = await call_next(request)
    duration = time() - start
    logger.info("%s %s %.3fs", request.method, request.url.path, duration)

    try:
        track_event("api_call", {
            "route": request.url.path,
            "method": request.method,
            "user_id": user_id,
            "status_code": response.status_code,
            "duration_s": round(duration, 3),
        })
    except Exception:
        pass

    return response


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": "Too many requests. Please try again later.",
        },
        headers={"Retry-After": "60"},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"])
async def root():
    return {
        "name": "Unweb API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "GET /api/v1/health": "Health check",
            "POST /api/v1/extract": "Extract structured content from any URL",
            "POST /api/v1/publish": "Register a site for AI-readable access",
            "GET /api/v1/sites/{id}": "Get published site info"
        }
    }

@app.get("/api/v1/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get(
    "/api/v1/metrics",
    tags=["metrics"],
    responses={401: {"model": ErrorResponse}},
)
async def metrics(user_id: str = Depends(verify_api_key)):
    return {
        "dashboard": get_dashboard_stats(),
        "timeline": get_timeline(24),
    }


@app.post(
    "/api/v1/extract",
    response_model=ExtractResponse,
    responses={
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    tags=["extract"],
)
@local_dev_limiter.limit()
async def extract(request: Request, body: ExtractRequest, user_id: str = Depends(verify_api_key)):
    track_event("extract", {"url": body.url, "user_id": user_id})
    cached = cache_get(body.url)
    if cached is not None:
        track_event("cache_hit", {"url": body.url})
        return ExtractResponse(
            title=cached["title"],
            description="",
            content=cached["content"],
            structured_data=cached.get("structured_data", {}),
            actions=[],
            metadata={"url": body.url, "word_count": 0},
        )
    track_event("cache_miss", {"url": body.url})
    result = await fetch_url(body.url)
    if result["status_code"] == -1:
        return JSONResponse(
            status_code=403,
            content={
                "error": "robots_blocked",
                "detail": f"Access to {body.url} is blocked by robots.txt",
            },
        )
    if result["status_code"] == 0:
        return JSONResponse(
            status_code=502,
            content={
                "error": "fetch_failed",
                "detail": f"Failed to fetch URL: {body.url}",
            },
        )
    extracted = await extract_content(result["html"], result["final_url"])
    if body.use_llm:
        llm_data = await extract_with_llm(
            extracted.content, body.url,
            title=extracted.title, description=extracted.description
        )
        extracted = merge_extraction(extracted, llm_data)
    cache_set(body.url, extracted.title, extracted.content, extracted.structured_data)
    return extracted


@app.post(
    "/api/v1/publish",
    response_model=PublishResponse,
    tags=["publish"],
)
async def publish(body: PublishRequest, user_id: str = Depends(verify_api_key)):
    track_event("publish", {"site_name": body.site_name, "url": body.url, "user_id": user_id})
    site_name = body.site_name
    existing = get_site_by_name(site_name)
    if existing:
        return JSONResponse(
            status_code=409,
            content={
                "error": "conflict",
                "detail": f"Site name '{site_name}' already exists",
            },
        )
    site_id = create_site(
        user_id=user_id,
        site_name=site_name,
        url=body.url,
        content=body.content,
        description=body.content[:200],
    )
    base_url = environ.get("LLMS_BASE_URL", "")
    llms_url = f"{base_url}/llms/{site_name}"
    return PublishResponse(llms_url=llms_url, site_id=site_id)


@app.get(
    "/api/v1/sites/{site_id}",
    tags=["sites"],
    responses={404: {"model": ErrorResponse}},
)
async def get_site(site_id: str, user_id: str = Depends(verify_api_key)):
    site = get_site_by_id(site_id)
    if site is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "detail": f"Site with id '{site_id}' not found",
            },
        )
    return site


@app.get(
    "/api/v1/sites",
    tags=["sites"],
    responses={404: {"model": ErrorResponse}},
)
async def list_sites(user_id: str = Depends(verify_api_key)):
    sites = list_user_sites(user_id)
    return sites


@app.get(
    "/llms/{site_name}",
    response_model=SiteInfo,
    tags=["sites"],
)
@local_dev_limiter.limit("30/minute")
async def get_llms_site(request: Request, site_name: str):
    site = get_site_by_name(site_name)
    if site is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": "not_found",
                "detail": f"Site '{site_name}' not found",
            },
        )
    return site


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post(
    "/api/v1/search",
    response_model=SearchResponse,
    tags=["search"],
    responses={
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
)
@local_dev_limiter.limit("10/minute")
async def search(request: Request, body: SearchRequest, user_id: str = Depends(verify_api_key)):
    track_event("search", {"query": body.query, "max_results": body.max_results, "user_id": user_id})
    results = await search_web(body.query, body.max_results)
    urls = [r["url"] for r in results if r["url"]]
    extracts = await batch_extract(urls, use_llm=True)
    summary = await summarize_results(body.query, extracts)
    return SearchResponse(
        query=body.query,
        summary=summary.get("summary", ""),
        key_points=summary.get("key_points", []),
        sources=summary.get("sources", []),
        raw_results=results,
    )


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@app.post(
    "/api/v1/auth/register",
    response_model=AuthResponse,
    tags=["auth"],
    responses={409: {"model": ErrorResponse}},
)
async def register(body: AuthRequest):
    try:
        user_id = create_user(body.email, body.password)
    except ValueError as e:
        return JSONResponse(
            status_code=409,
            content={"error": "conflict", "detail": str(e)},
        )
    api_key = create_api_key(user_id)
    return AuthResponse(user_id=user_id, api_key=api_key)


@app.post(
    "/api/v1/auth/login",
    response_model=AuthResponse,
    tags=["auth"],
    responses={401: {"model": ErrorResponse}},
)
async def login(body: AuthRequest):
    user_id = authenticate_user(body.email, body.password)
    if user_id is None:
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "detail": "Invalid email or password",
            },
        )
    api_key = create_api_key(user_id)
    return AuthResponse(user_id=user_id, api_key=api_key)


@app.get(
    "/api/v1/keys",
    response_model=KeysResponse,
    tags=["auth"],
)
async def list_keys(user_id: str = Depends(verify_api_key)):
    keys = list_user_keys(user_id)
    return KeysResponse(keys=keys)


# ── Aiso / ChuanSha AI proxy endpoints ──────────────────────────────────

DEEPSEEK_KEY = environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

from pydantic import BaseModel, field_validator

ALLOWED_OCCASIONS = {"上班", "约会", "日常", "运动"}

class OutfitTextRequest(BaseModel):
    image_base64: str = ""
    occasion: str = "日常"
    weather: str = ""
    profile: dict = {}

    @field_validator("occasion")
    @classmethod
    def validate_occasion(cls, v: str) -> str:
        if v not in ALLOWED_OCCASIONS:
            raise ValueError(f"occasion must be one of {sorted(ALLOWED_OCCASIONS)}")
        return v


@app.post("/api/aiso/outfit-text")
async def outfit_text(request: Request, body: OutfitTextRequest):
    if not DEEPSEEK_KEY:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": {"code": "ai_service_error", "message": "AI service not configured"}},
        )

    p = body.profile
    gender = p.get("gender", "未设置")
    height = p.get("height", 170)
    weight = p.get("weight", 65)
    body_type = p.get("bodyType", "标准")
    style = p.get("stylePreference", "休闲")
    skin = p.get("skinTone", "自然")

    prompt = f"""你是专业穿搭顾问。根据用户画像推荐一套完整穿搭。

用户画像：{gender}，{height}cm，{weight}kg，{body_type}身材，喜欢{style}风格，{skin}
穿搭场合：{body.occasion}
天气：{body.weather}

请推荐一套完整的穿搭方案。严格返回JSON（不要其他文字）：
{{"description":"整体穿搭描述，100字左右，说明为什么这样搭","items":[{{"name":"单品名称","category":"上装/下装/鞋/配饰","taobaoKeyword":"淘宝搜索关键词","estimatedPrice":"预估价格区间如¥199-299"}}]}}
要求：
- 推荐5-7件单品，覆盖上装、下装、鞋、配饰
- taobaoKeyword要是真实可搜的淘宝关键词
- estimatedPrice要符合市场行情
- 穿搭要考虑天气和场合"""

    import httpx

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                DEEPSEEK_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1200,
                },
            )
    except Exception:
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": {"code": "ai_service_error", "message": "Failed to reach AI service"}},
        )

    if resp.status_code != 200:
        logger.error("DeepSeek error (outfit-text): %s %s", resp.status_code, resp.text[:300])
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": {"code": "ai_service_error", "message": f"AI service error: {resp.status_code}"}},
        )

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": {"code": "ai_service_error", "message": "Unexpected AI response format"}},
        )

    # Parse JSON from content (handle markdown fences)
    json_text = content.strip()
    if json_text.startswith("```json"):
        json_text = json_text[7:]
    elif json_text.startswith("```"):
        json_text = json_text[3:]
    if json_text.endswith("```"):
        json_text = json_text[:-3]
    json_text = json_text.strip()

    import json as _json
    try:
        result = _json.loads(json_text)
    except _json.JSONDecodeError:
        return JSONResponse(
            status_code=502,
            content={"success": False, "error": {"code": "ai_service_error", "message": f"Failed to parse AI response: {json_text[:200]}"}},
        )

    return JSONResponse(
        content={
            "success": True,
            "data": {
                "description": result.get("description", ""),
                "items": result.get("items", []),
            },
        }
    )


@app.options("/api/aiso/outfit-text")
async def outfit_text_options():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )
