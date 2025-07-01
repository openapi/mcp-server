# mcp.openapi.com MCP Gateway

Questo progetto implementa un server **Model Context Protocol (MCP)** che funge da gateway sicuro e unificato per l’accesso a servizi autenticati di openapi.com. Il server è progettato per essere integrato con ambienti AI come VS Code, Claude Desktop e altri host MCP.

## Caratteristiche

- **Proxy sicuro**: Pass-through del Bearer Token fornito dal client, senza gestione diretta di credenziali sensibili.
- **Estendibile**: Aggiungi facilmente nuovi tool/API creando moduli in [`/apis/`](apis/).
- **Compatibile MCP**: Progettato secondo le best practice del protocollo MCP.
- **Modulare**: Tutta la logica di chiamata API e la registrazione dei tool è centralizzata in [`mcp_core.py`](mcp_core.py).

---

## Prerequisiti

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (per la gestione delle dipendenze)
- Connessione Internet
- **(Opzionale)** [Docker](https://www.docker.com/) per esecuzione containerizzata

---

## Installazione (Ambiente Locale)

1. **Clona il repository**  
   ```bash
   git clone <URL_DEL_REPO>
   cd mcp.openapi.com
   ```

2. **Crea e attiva un ambiente virtuale**  
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Installa le dipendenze**  
   ```bash
   uv pip install -r requirements.txt
   # oppure, se usi uv:
   uv add "fastmcp" requests pydantic
   ```

---

## Avvio del Server

```bash
python main.py
```

Il server sarà disponibile su `http://0.0.0.0:8080`.

---

## Esecuzione con Docker

1. **Costruisci l'immagine Docker**
   ```bash
   docker build -t mcp-openapi .
   ```

2. **Avvia il container**
   ```bash
   docker run -it --rm -p 8080:8080 mcp-openapi
   ```

Il server sarà accessibile su `http://localhost:8080`.

---

## Debug e Sviluppo

- Il server stampa a console dettagli su ogni richiesta, inclusi header e parametri.
- Per vedere i log, avvia il server da terminale:
  ```bash
  python main.py
  ```
- Puoi modificare la funzione `make_api_call` in [`mcp_core.py`](mcp_core.py) per aggiungere ulteriori print/logging.
- Usa strumenti come [httpie](https://httpie.io/) o `curl` per testare manualmente gli endpoint:
  ```bash
  curl -H "Authorization: Bearer IL_TUO_TOKEN" http://localhost:8080/mcp/
  ```

### Hot Reload (opzionale)

Per sviluppo rapido, puoi usare [watchdog](https://pypi.org/project/watchdog/) o [entr](https://eradman.com/entrproject/) per riavviare il server ad ogni modifica:
```bash
pip install watchdog
watchmedo auto-restart --pattern="*.py" -- python main.py
```

---

## Configurazione MCP Client (VS Code)

1. **Genera un Bearer Token**  
   Dal portale https://console.openapi.com/oauth, crea un token con gli scope necessari.

2. **Crea il file `.vscode/mcp.json`**  
   Esempio:
   ```json
   {
     "servers": {
       "openapi.com": {
         "type": "http",
         "url": "http://INDIRIZZO_IP_DEL_TUO_SERVER:8080/mcp/",
         "headers": {
           "Authorization": "Bearer IL_TUO_BEARER_TOKEN_DI_PRODUZIONE"
         }
       }
     }
   }
   ```

3. **Testa l’integrazione**  
   - Ricarica VS Code.
   - Apri la chat Copilot e digita `@workspace`.
   - Usa i tool esposti dal server MCP.

---

## Struttura del Progetto

- [`main.py`](main.py): Entry point FastAPI + MCP server.
- [`mcp_core.py`](mcp_core.py): Inizializzazione MCP, helper per chiamate API, error handling.
- [`/apis/`](apis/): Moduli Python che definiscono i tool MCP (uno per API/ambito).
- [`requirements.txt`](requirements.txt): Dipendenze Python.
- [`docs/`](docs/): Documentazione e configurazioni di esempio.
- [`Dockerfile`](Dockerfile): Build e avvio container Docker.

---

## Aggiungere Nuovi Tool/API

1. Crea o modifica un file in [`/apis/`](apis/), seguendo il pattern:
   ```python
   from fastmcp import Context
   from typing import Any
   from mcp_core import make_api_call, mcp

   @mcp.tool
   async def nome_tool(parametri..., ctx: Context) -> Any:
       # ...logica...
       return make_api_call(ctx, "GET", url, params=params)
   ```
2. Riavvia il server per applicare le modifiche.

---

## Note di Sicurezza

- **Mai** inserire credenziali o token hardcoded nel codice.
- Il server si aspetta che il Bearer Token sia fornito dal client tramite header HTTP.
- Tutte le chiamate API sono proxyate con il token fornito dal client.

---

## Risorse Utili

- [Documentazione MCP](https://github.com/anthropics/model-context-protocol)
- [fastmcp](https://pypi.org/project/fastmcp/)
- [openapi.com](https://openapi.com/)

---

## Licenza

MIT

---

Se hai domande o problemi, apri una issue!