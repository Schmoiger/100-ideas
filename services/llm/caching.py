"""Gemini context caching management for shared resource documents."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from google import genai
from google.genai import types

from services.llm.governance import estimate_token_count

# Gemini context caching minimum threshold is 32,768 tokens
GEMINI_CACHE_MIN_TOKENS = 32_768

# In-memory registry of active caches by content fingerprint
_CACHE_REGISTRY: dict[str, dict[str, Any]] = {}


def get_content_cache_key(model: str, contents: list[str]) -> str:
    """Compute unique deterministic fingerprint for cached contents."""
    hasher = hashlib.sha256()
    hasher.update(model.encode("utf-8"))
    for item in contents:
        hasher.update(item.encode("utf-8"))
    return hasher.hexdigest()


def should_create_cache(contents: list[str], min_tokens: int = GEMINI_CACHE_MIN_TOKENS) -> bool:
    """Return True if total estimated content volume exceeds context caching threshold."""
    total_text = "".join(contents)
    return estimate_token_count(total_text) >= min_tokens


def get_or_create_context_cache(
    client: genai.Client,
    model: str,
    contents: list[str],
    ttl: str = "3600s",
    force: bool = False,
) -> str | None:
    """Create or return an active Gemini Context Cache if content volume justifies it.

    Returns the cache name (e.g. 'cachedContents/xyz') or None if below threshold.
    """
    if not force and not should_create_cache(contents):
        return None

    cache_key = get_content_cache_key(model, contents)
    now = time.time()

    # Check local registry
    if cache_key in _CACHE_REGISTRY:
        entry = _CACHE_REGISTRY[cache_key]
        if entry["expires_at"] > now:
            return entry["name"]

    try:
        cache = client.caches.create(
            model=model,
            config=types.CreateCachedContentConfig(
                contents=contents,
                ttl=ttl,
            ),
        )
        cache_name = cache.name
        # Approximate 1 hour expiration
        _CACHE_REGISTRY[cache_key] = {
            "name": cache_name,
            "expires_at": now + 3500,
        }
        return cache_name
    except Exception:
        # Fall back to un-cached generation if caching creation fails or is unsupported
        return None
