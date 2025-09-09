# memory_store.py
# Singleton in-memory store for callback results
import os
from typing import Dict
from pymemcache.client import base
import json

callback_results = {}

# ENV VARIABLES: todo better env astraction for envs
K_SERVICE = os.getenv("K_SERVICE")
DEV_VM = os.getenv("X-DEV-VM")
BASE_URL = "https://mcp.openapi.com"
callbackUrl = None
if K_SERVICE:
    BASE_URL = "https://" + K_SERVICE.replace("-", ".")
    callbackUrl = BASE_URL + "/callbacks"
    callbackUrl = callbackUrl.replace("alpha", "dev") if DEV_VM else callbackUrl

# Configurazione Memcached
MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", 'X.X.X.X' if DEV_VM or K_SERVICE != "mcp-openapi-com" else "X.X.X.X" )
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", 11211))
memcached_client = base.Client((MEMCACHED_HOST, MEMCACHED_PORT))

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

# Funzione per salvare i dati in Memcached in modo binary-safe
def save_to_memcached(client, key, value):
    try:
        # Serializza i dati in JSON e codifica in UTF-8
        binary_value = json.dumps(value).encode('utf-8')
        client.set(key, binary_value)
    except Exception as e:
        print(f"Errore durante il salvataggio in Memcached: {e}")

# Funzione per recuperare i dati da Memcached
def get_from_memcached(client, key):
    try:
        binary_value = client.get(key)
        if binary_value is not None:
            # Decodifica i dati da UTF-8 e deserializza da JSON
            return json.loads(binary_value.decode('utf-8'))
        return None
    except Exception as e:
        print(f"Errore durante il recupero da Memcached: {e}")
        return None
