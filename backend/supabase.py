"""Supabase client and auth database helpers for Unweb.

RLS note: if queries return None/hang, run these SQL statements in the Supabase dashboard SQL editor:

  alter table users disable row level security;
  alter table api_keys disable row level security;
  alter table sites disable row level security;
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from supabase import create_client

_URL: Optional[str] = os.environ.get("SUPABASE_URL")
_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")
_client = None


def _get():
    global _client
    if _client is None:
        if _URL is None or _KEY is None:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(_URL, _KEY)
    return _client


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _token() -> str:
    return "unweb_" + secrets.token_hex(32)


def create_user(email: str, password: str) -> str:
    sup = _get()
    existing = sup.table("users").select("id").eq("email", email).maybe_single().execute()
    if existing and hasattr(existing, 'data') and existing.data:
        raise ValueError(f"User with email {email!r} already exists")
    r = sup.table("users").insert({"email": email, "password_hash": _hash(password)}).execute()
    if not r or not hasattr(r, 'data') or not r.data:
        raise RuntimeError("Failed to create user")
    return r.data[0]["id"]


def authenticate_user(email: str, password: str) -> Optional[str]:
    sup = _get()
    r = sup.table("users").select("id", "password_hash").eq("email", email).maybe_single().execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return None
    if r.data["password_hash"] == _hash(password):
        return r.data["id"]
    return None


def create_api_key(user_id: str) -> str:
    sup = _get()
    key = _token()
    r = sup.table("api_keys").insert({"user_id": user_id, "key": key}).execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        raise RuntimeError("Failed to create API key")
    return key


def verify_api_key(key: str) -> Optional[str]:
    sup = _get()
    r = sup.table("api_keys").select("user_id").eq("key", key).maybe_single().execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return None
    return r.data["user_id"]


def list_user_keys(user_id: str) -> list[dict]:
    sup = _get()
    r = sup.table("api_keys").select("id", "key", "created_at").eq("user_id", user_id).execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return []
    return r.data


def create_site(user_id: str, site_name: str, url: str, content: str, description: str) -> str:
    sup = _get()
    r = sup.table("sites").insert({
        "user_id": user_id,
        "site_name": site_name,
        "url": url,
        "content": content,
        "description": description,
    }).execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        raise RuntimeError("Failed to create site")
    return r.data[0]["id"]


def get_site_by_name(site_name: str) -> Optional[dict]:
    sup = _get()
    r = sup.table("sites").select("*").eq("site_name", site_name).maybe_single().execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return None
    return r.data


def get_site_by_id(site_id: str) -> Optional[dict]:
    sup = _get()
    r = sup.table("sites").select("*").eq("id", site_id).maybe_single().execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return None
    return r.data


def list_user_sites(user_id: str) -> list[dict]:
    sup = _get()
    r = sup.table("sites").select("*").eq("user_id", user_id).execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return []
    return r.data


def update_site(site_id: str, content: str) -> bool:
    sup = _get()
    r = sup.table("sites").update({"content": content}).eq("id", site_id).execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return False
    return bool(r.data)


def cache_get(url: str) -> Optional[dict]:
    sup = _get()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    r = sup.table("search_cache").select("*").eq("url", url).gte("cached_at", cutoff).maybe_single().execute()
    if r is None or not hasattr(r, 'data') or r.data is None:
        return None
    return r.data


def cache_set(url: str, title: str, content: str, structured_data: Optional[dict] = None) -> None:
    sup = _get()
    record = {
        "url": url,
        "title": title,
        "content": content,
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }
    if structured_data is not None:
        record["structured_data"] = structured_data
    sup.table("search_cache").upsert(record, on_conflict="url").execute()


# ---------------------------------------------------------------------------
# Metrics / event tracking
#
# Requires the following table in Supabase:
#
#   create table metrics (
#     id uuid primary key default gen_random_uuid(),
#     event text not null,
#     detail jsonb default '{}',
#     created_at timestamptz default now()
#   );
# ---------------------------------------------------------------------------

def track_event(event: str, detail: dict) -> None:
    sup = _get()
    record = {
        "event": event,
        "detail": detail,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    sup.table("metrics").insert(record).execute()
