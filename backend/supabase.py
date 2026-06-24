"""Supabase client and auth database helpers for Unweb."""

import hashlib
import os
import secrets
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
    if r.data and r.data["password_hash"] == _hash(password):
        return r.data["id"]
    return None


def create_api_key(user_id: str) -> str:
    sup = _get()
    key = _token()
    sup.table("api_keys").insert({"user_id": user_id, "key": key}).execute()
    return key


def verify_api_key(key: str) -> Optional[str]:
    sup = _get()
    r = sup.table("api_keys").select("user_id").eq("key", key).maybe_single().execute()
    return r.data["user_id"] if r.data else None


def list_user_keys(user_id: str) -> list[dict]:
    sup = _get()
    r = sup.table("api_keys").select("id", "key", "created_at").eq("user_id", user_id).execute()
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
    return r.data[0]["id"]


def get_site_by_name(site_name: str) -> Optional[dict]:
    sup = _get()
    r = sup.table("sites").select("*").eq("site_name", site_name).maybe_single().execute()
    return r.data if r.data else None


def get_site_by_id(site_id: str) -> Optional[dict]:
    sup = _get()
    r = sup.table("sites").select("*").eq("id", site_id).maybe_single().execute()
    return r.data if r.data else None


def list_user_sites(user_id: str) -> list[dict]:
    sup = _get()
    r = sup.table("sites").select("*").eq("user_id", user_id).execute()
    return r.data


def update_site(site_id: str, content: str) -> bool:
    sup = _get()
    r = sup.table("sites").update({"content": content}).eq("id", site_id).execute()
    return bool(r.data)
