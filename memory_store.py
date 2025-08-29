# memory_store.py
# Singleton in-memory store for callback results
import os
from typing import Dict
from pymemcache.client import base

callback_results = {}

# #prelevo le variabili ambiente 
K_SERVICE = os.getenv("K_SERVICE")
DEV_VM = os.getenv("X-DEV-VM")
BASE_URL = "https://mcp.openapi.com"
callbackUrl = None
if K_SERVICE:
    BASE_URL = "https://" + K_SERVICE.replace("-", ".")
    callbackUrl = BASE_URL + "/callbacks"
    callbackUrl = callbackUrl.replace("alpha", "dev") if DEV_VM else callbackUrl

    


# Configurazione Memcached
MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", '10.2.1.3' if DEV_VM or K_SERVICE != "mcp-openapi-com" else "10.3.0.3" )
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", 11211))
memcached_client = base.Client((MEMCACHED_HOST, MEMCACHED_PORT))

# Funzioni aggiornate per supportare Memcached
def get_callback_result(request_id: str):
    """
    Recupera il risultato di una callback dato il request_id.
    """
    try:
        result = memcached_client.get(request_id)
        if result is None:
            raise KeyError(f"Risultato non trovato per request_id: {request_id}")
        return eval(result)  # Convertire la stringa in dizionario
    except Exception as e:
        # Fallback al dizionario in memoria
        if request_id not in callback_results:
            raise KeyError(f"Risultato non trovato per request_id: {request_id}")
        return callback_results[request_id]


def set_callback_result(request_id: str, data: Dict, custom: Dict):
    """
    Salva o aggiorna il risultato di una callback dato il request_id.
    """
    result = {
        "data": data,
        "custom": custom
    }
    try:
        memcached_client.set(request_id, str(result))  # Convertire il dizionario in stringa
    except Exception as e:
        # Fallback al dizionario in memoria
        callback_results[request_id] = result
