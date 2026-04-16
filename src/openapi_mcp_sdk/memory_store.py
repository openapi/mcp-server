"""Shared storage for async callback results."""

from __future__ import annotations

import json
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)
try:
    from pymemcache.client import base

    _PYMEMCACHE_AVAILABLE = True
except ImportError:
    base = None  # type: ignore[assignment]
    _PYMEMCACHE_AVAILABLE = False

callback_results = {}

MCP_ENV = os.getenv("MCP_ENV", "production").strip().lower()
if MCP_ENV not in {"dev", "staging", "production"}:
    logger.warning("Invalid MCP_ENV=%r, defaulting to 'production'", MCP_ENV)
    MCP_ENV = "production"

MCP_OPENAPI_ENV = os.getenv("MCP_OPENAPI_ENV", "").strip().lower()
if MCP_OPENAPI_ENV == "sandbox":
    MCP_OPENAPI_ENV = "test"
if MCP_OPENAPI_ENV not in {"", "dev", "test"}:
    logger.warning("Invalid MCP_OPENAPI_ENV=%r, defaulting to production", MCP_OPENAPI_ENV)
    MCP_OPENAPI_ENV = ""
OPENAPI_HOST_PREFIX = f"{MCP_OPENAPI_ENV}." if MCP_OPENAPI_ENV else ""

MCP_BASE_URL = os.getenv("MCP_BASE_URL", "http://localhost:8080")

callbackUrl = os.getenv("MCP_CALLBACK_URL")
if not callbackUrl:
    callbackUrl = MCP_BASE_URL + "/callbacks"
    if MCP_ENV == "dev":
        callbackUrl = callbackUrl.replace("alpha", "dev")

MEMCACHED_HOST = os.getenv("MCP_CACHE_HOST", "0.0.0.0")
MEMCACHED_PORT = int(os.getenv("MCP_CACHE_PORT", "11211"))
# connect_timeout / timeout = 1 s: when Memcached is unreachable (e.g. local dev,
# Docker without the VPC network) the client fails fast and the except block
# falls back to the in-process dict, keeping every endpoint responsive.
memcached_client = (
    base.Client((MEMCACHED_HOST, MEMCACHED_PORT), connect_timeout=1, timeout=1) if _PYMEMCACHE_AVAILABLE else None
)


# Funzioni aggiornate per supportare Memcached
def get_callback_result(request_id: str):
    """
    Retrieves the result of a callback given the request_id.
    """
    try:
        if memcached_client is None:
            raise RuntimeError("pymemcache not available")
        return get_from_memcached(memcached_client, request_id)
    except (RuntimeError, OSError, ValueError, TypeError) as e:
        # Fallback al dizionario in memoria
        logger.debug("memcached get failed, falling back to in-memory store: %s", e)
        if request_id not in callback_results:
            raise KeyError(f"Result not found for request_id: {request_id}") from e
        return callback_results[request_id]


def set_callback_result(request_id: str, data: Dict, custom: Dict):
    """
    Saves or updates the result of a callback given the request_id.
    """
    result = {"data": data, "custom": custom}
    try:
        if memcached_client is None:
            raise RuntimeError("pymemcache not available")
        save_to_memcached(memcached_client, request_id, result)
    except (RuntimeError, OSError, ValueError, TypeError) as e:
        # Fallback al dizionario in memoria
        logger.debug("memcached set failed, falling back to in-memory store: %s", e)
        callback_results[request_id] = result


def save_to_memcached(client, key, value):
    """Serialize a callback payload and store it in Memcached."""
    binary_value = json.dumps(value).encode("utf-8")
    client.set(key, binary_value)


def get_from_memcached(client, key):
    """Read a callback payload from Memcached and decode it from JSON."""
    binary_value = client.get(key)
    if binary_value is not None:
        return json.loads(binary_value.decode("utf-8"))
    return None
