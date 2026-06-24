"""LLM-powered content extraction using DeepSeek API."""

import json
import os
from typing import Optional

import httpx

from .schemas import ExtractResponse

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

EXTRACTION_PROMPT = """You are a web content extractor for AI agents. Analyze this webpage content and extract structured information.

Return ONLY valid JSON (no markdown, no explanation) with these fields:
{{
  "title": "Clean page title",
  "description": "One-paragraph summary",
  "summary": "Concise 3-5 bullet-point summary",
  "category": "One of: article, product, documentation, company, blog, news, other",
  "entities": ["List of key entities"],
  "topics": ["3-5 topic tags"],
  "language": "Detected language code (en, zh, etc.)",
  "sentiment": "positive, negative, or neutral",
  "actionable": true or false
}}

Webpage content:
{content}

URL: {url}

Return ONLY the JSON object, nothing else."""


async def extract_with_llm(
    raw_content: str,
    url: str,
    title: str = "",
    description: str = "",
) -> Optional[dict]:
    """Use DeepSeek to intelligently extract and structure webpage content.

    Returns enhanced extraction data, or None if LLM is unavailable/fails.
    """
    if not DEEPSEEK_API_KEY:
        return None

    content_preview = raw_content[:8000]  # Limit tokens

    prompt = EXTRACTION_PROMPT.format(
        content=content_preview,
        url=url,
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1000,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            result_text = data["choices"][0]["message"]["content"]
            return json.loads(result_text)

    except Exception:
        return None


def merge_extraction(base: ExtractResponse, llm_data: Optional[dict]) -> ExtractResponse:
    """Merge LLM extraction results into the base extraction, with fallbacks."""
    if not llm_data:
        return base

    # Use LLM title if base is weak
    if (not base.title or base.title in base.content[:50]) and llm_data.get("title"):
        base.title = llm_data["title"]

    # Use LLM description if base is empty
    if not base.description and llm_data.get("description"):
        base.description = llm_data["description"]

    # Add LLM-specific fields to structured_data
    structured = base.structured_data
    structured["llm"] = {
        "summary": llm_data.get("summary", ""),
        "category": llm_data.get("category", "other"),
        "entities": llm_data.get("entities", []),
        "topics": llm_data.get("topics", []),
        "language": llm_data.get("language", "unknown"),
        "sentiment": llm_data.get("sentiment", "neutral"),
        "actionable": llm_data.get("actionable", False),
    }

    base.structured_data = structured
    return base
