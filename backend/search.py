"""Web search + batch extraction + LLM summarization."""

import asyncio
import json
import os
from typing import Optional

import httpx

from .extractor import extract_content
from .crawler import fetch_url
from .llm_extractor import extract_with_llm, merge_extraction
from .supabase import cache_get, cache_set

SEARCH_URL = "https://html.duckduckgo.com/html/"

SUMMARY_PROMPT = """You are a research assistant. Summarize the following web extracts into a concise report.

Query: {query}

Web extracts:
{extracts}

Return ONLY valid JSON:
{{
  "summary": "2-3 paragraph synthesis of findings",
  "key_points": ["5-8 key takeaways as bullet points"],
  "sources": [{{"title": "source title", "url": "source url", "relevance": "high/medium/low"}}]
}}
"""


async def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web using DuckDuckGo HTML and return result URLs/titles."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(SEARCH_URL, params={"q": query}, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for item in soup.select(".result")[:max_results]:
                title_el = item.select_one(".result__title a")
                snippet_el = item.select_one(".result__snippet")
                url_el = item.select_one(".result__url")
                if title_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": url_el.get_text(strip=True) if url_el else "",
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
            return results
    except Exception:
        return []


async def batch_extract(urls: list[str], use_llm: bool = False) -> list[dict]:
    """Extract content from multiple URLs in parallel."""
    async def extract_one(url: str) -> Optional[dict]:
        cached = cache_get(url)
        if cached is not None:
            return {
                "title": cached["title"],
                "url": url,
                "content": cached["content"][:3000],
            }
        try:
            result = await fetch_url(url)
            if result["status_code"] != 200:
                return None
            extracted = await extract_content(result["html"], result["final_url"])
            if use_llm:
                llm_data = await extract_with_llm(extracted.content, url)
                extracted = merge_extraction(extracted, llm_data)
            cache_set(url, extracted.title, extracted.content, extracted.structured_data)
            return {
                "title": extracted.title,
                "url": url,
                "content": extracted.content[:3000],
            }
        except Exception:
            return None

    tasks = [extract_one(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


async def summarize_results(query: str, extracts: list[dict]) -> dict:
    """Use LLM to summarize multiple extracts into a report."""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        return {"summary": "LLM not configured", "key_points": [], "sources": []}

    extracts_text = "\n\n---\n\n".join(
        f"Source: {e['title']}\n{e['content'][:2000]}" for e in extracts[:8]
    )
    prompt = SUMMARY_PROMPT.format(query=query, extracts=extracts_text)

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1500,
                    "response_format": {"type": "json_object"},
                },
            )
            data = resp.json()
            return json.loads(data["choices"][0]["message"]["content"])
    except Exception:
        return {"summary": "Summarization failed", "key_points": [], "sources": []}
