# memory_store.py
# Singleton in-memory store for callback results
import os
from typing import Dict
# TODO: Remove legacy dependency — pymemcache is tied to the Google Cloud VPC-internal Memcached
# instance (hardcoded IPs X.X.X.X / X.X.X.X). Replace with an environment-agnostic cache
# abstraction: use a simple in-process dict for local/dev, and allow plugging in Redis
# (e.g. via redis-py + CACHE_URL env var) or any other backend for production.
# Remove pymemcache from requirements.txt and pyproject.toml when done.
from pymemcache.client import base
import json

callback_results = {}

# TODO: Remove legacy dependency — K_SERVICE is a Google Cloud Run reserved env var injected
# automatically by the platform. It encodes the service name which is used here to derive:
# sandbox/production prefix, BASE_URL and callback URL. Replace with explicit env vars:
#   SANDBOX_PREFIX, BASE_URL, CALLBACK_URL so the app works on any platform.
K_SERVICE = os.getenv("K_SERVICE")
# Estrae il prefisso ambiente da K_SERVICE (es: "dev-mcp-openapi-com" -> "dev.")
if K_SERVICE and K_SERVICE != "mcp-openapi-com":
    env_prefix = K_SERVICE.split("-")[0]  # estrae "test", "dev", "alpha"
    SANDBOX_PREFIX = f"{env_prefix}."
else:
    SANDBOX_PREFIX = ""

# TODO: Remove legacy dependency — X-DEV-VM is an internal convention for a specific GCP VM.
# Replace with a standard ENVIRONMENT=dev|staging|production env var.
DEV_VM = os.getenv("X-DEV-VM")
BASE_URL = "https://mcp.openapi.com"
callbackUrl = None
if K_SERVICE:
    # TODO: Remove legacy dependency — BASE_URL derived from K_SERVICE (Cloud Run naming convention).
    # Replace with an explicit BASE_URL env var.
    BASE_URL = "https://" + K_SERVICE.replace("-", ".")
    callbackUrl = BASE_URL + "/callbacks"
    callbackUrl = callbackUrl.replace("alpha", "dev") if DEV_VM else callbackUrl

# TODO: Remove legacy dependency — Memcached IPs (X.X.X.X, X.X.X.X) are hardcoded VPC-internal
# addresses specific to the current GCP deployment. For local dev use the in-process dict fallback
# already present below. For production replace with CACHE_URL=redis://... or similar.
MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", 'X.X.X.X' if DEV_VM or K_SERVICE != "mcp-openapi-com" else "X.X.X.X" )
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", 11211))
# connect_timeout / timeout = 1 s: when Memcached is unreachable (e.g. local dev,
# Docker without the VPC network) the client fails fast and the except block
# falls back to the in-process dict, keeping every endpoint responsive.
memcached_client = base.Client((MEMCACHED_HOST, MEMCACHED_PORT), connect_timeout=1, timeout=1)

# Funzioni aggiornate per supportare Memcached
def get_callback_result(request_id: str):
    """
    Retrieves the result of a callback given the request_id.
    """
    try:
        return get_from_memcached(memcached_client, request_id)
    except Exception as e:
        # Fallback al dizionario in memoria
        print(f"Error retrieving from Memcached: {e}")
        if request_id not in callback_results:
            raise KeyError(f"Result not found for request_id: {request_id}")
        return callback_results[request_id]


def set_callback_result(request_id: str, data: Dict, custom: Dict):
    """
    Saves or updates the result of a callback given the request_id.
    """
    result = {
        "data": data,
        "custom": custom
    }
    try:
        save_to_memcached(memcached_client, request_id, result)
    except Exception as e:
        # Fallback al dizionario in memoria
        print(f"Memcached not enabled: {e}")
        callback_results[request_id] = result

def save_to_memcached(client, key, value):
    # Serializza i dati in JSON e codifica in UTF-8
    binary_value = json.dumps(value).encode('utf-8')
    client.set(key, binary_value)

# Funzione per recuperare i dati da Memcached
def get_from_memcached(client, key):
    binary_value = client.get(key)
    if binary_value is not None:
        # Decodifica i dati da UTF-8 e deserializza da JSON
        return json.loads(binary_value.decode('utf-8'))
    return None
