# memory_store.py
# Singleton in-memory store for callback results
import os
callback_results = {}

# #prelevo le variabili ambiente 
K_SERVICE = os.getenv("K_SERVICE")
DEV_VM = os.getenv("X-DEV-VM")
localDomain = K_SERVICE.replace("-",".")
localDomain = localDomain.replace("alpha","dev") if DEV_VM and localDomain == "alpha.mcp.openapi.com" else localDomain

