"""Analytics / metrics helpers for the Unweb dashboard."""

from datetime import datetime, timedelta, timezone

from .supabase import _get as _supabase


def get_dashboard_stats() -> dict:
    sup = _supabase()

    def _count(event: str) -> int:
        r = sup.table("metrics").select("*", count="exact").eq("event", event).execute()
        return r.count if hasattr(r, "count") and r.count is not None else len(r.data)

    total_extracts = _count("extract")
    total_searches = _count("search")
    total_publishes = _count("publish")

    r = sup.table("users").select("*", count="exact").execute()
    total_users = r.count if hasattr(r, "count") and r.count is not None else len(r.data)

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    r = sup.table("metrics").select("detail").eq("event", "extract").gte("created_at", cutoff).execute()
    urls = set()
    for row in r.data:
        url = (row.get("detail") or {}).get("url")
        if url:
            urls.add(url)
    unique_urls_24h = len(urls)

    r_hits = sup.table("metrics").select("*", count="exact").eq("event", "cache_hit").execute()
    r_misses = sup.table("metrics").select("*", count="exact").eq("event", "cache_miss").execute()
    hits = r_hits.count if hasattr(r_hits, "count") and r_hits.count is not None else len(r_hits.data)
    misses = r_misses.count if hasattr(r_misses, "count") and r_misses.count is not None else len(r_misses.data)
    total = hits + misses
    cache_hit_rate = round(hits / total, 4) if total > 0 else 0.0

    return {
        "total_extracts": total_extracts,
        "total_searches": total_searches,
        "total_publishes": total_publishes,
        "total_users": total_users,
        "unique_urls_24h": unique_urls_24h,
        "cache_hit_rate": cache_hit_rate,
    }


def get_timeline(hours: int = 24) -> list[dict]:
    sup = _supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    r = sup.table("metrics").select("created_at").gte("created_at", cutoff).execute()

    hourly: dict[str, int] = {}
    for row in r.data:
        ts = row.get("created_at", "")
        hour = ts[:13]
        hourly[hour] = hourly.get(hour, 0) + 1

    return [{"hour": k, "count": v} for k, v in sorted(hourly.items())]
