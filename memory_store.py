# memory_store.py
# Singleton in-memory store for callback results
import os
from typing import Dict
callback_results = {}

# #prelevo le variabili ambiente 
K_SERVICE = os.getenv("K_SERVICE")
DEV_VM = os.getenv("X-DEV-VM")
callbackUrl = "https://" + K_SERVICE.replace("-", ".") + "/callbacks";
callbackUrl = callbackUrl.replace("alpha","dev") if DEV_VM else callbackUrl

def get_callback_result(request_id: str):
    """
    Recupera il risultato di una callback dato il request_id.
    """
    if request_id not in callback_results:
        raise KeyError(f"Risultato non trovato per request_id: {request_id}")
    return callback_results[request_id]


def set_callback_result(request_id: str, data: Dict, custom: Dict):
    """
    Salva o aggiorna il risultato di una callback dato il request_id.
    """
    callback_results[request_id] = {
        "data": data,
        "custom": custom
    }
