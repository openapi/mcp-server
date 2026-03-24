# Progetto Architetturale: Implementazione di un Gateway MCP Sicuro per l'Accesso ad API Autenticate

## Sezione 1: Concetti Fondamentali: L'Architettura del Model Context Protocol (MCP)

[cite\_start]Prima di intraprendere la progettazione e l'implementazione di una soluzione specifica, è indispensabile stabilire una solida comprensione dei principi architetturali che governano il Model Context Protocol (MCP). [cite: 1] [cite\_start]L'MCP non è semplicemente una tecnologia, ma un paradigma emergente per l'integrazione dell'Intelligenza Artificiale, progettato per standardizzare e rendere sicura la comunicazione tra i Large Language Models (LLM) e l'universo di strumenti e dati esterni. [cite: 2] [cite\_start]Introdotto da Anthropic, l'MCP si propone di risolvere il problema della frammentazione delle integrazioni, agendo come una "porta USB-C per le applicazioni AI", ovvero un connettore universale che permette a qualsiasi modello AI di interfacciarsi con sorgenti dati e tool esterni senza la necessità di sviluppare codice custom per ogni singola connessione. [cite: 2]

### 1.1. Il Paradigma Client-Host-Server: Un'Architettura Tripartita

[cite\_start]L'architettura del Model Context Protocol si fonda su una chiara separazione delle responsabilità tra tre componenti distinti: l'Host, il Client e il Server. [cite: 3] [cite\_start]Questa struttura tripartita è progettata per massimizzare la modularità, la sicurezza e la componibilità dell'ecosistema. [cite: 4]

  * [cite\_start]**Host**: L'Host è l'applicazione orchestratrice che funge da contenitore per l'intera interazione AI. [cite: 4] [cite\_start]Esempi comuni includono ambienti di sviluppo integrati (IDE) come Cursor, applicazioni desktop come Claude Desktop, o un'interfaccia utente di un chatbot personalizzato. [cite: 5] [cite\_start]Il suo ruolo primario è quello di agire come una "torre di controllo": gestisce la sessione dell'utente, avvia e termina le istanze dei Client e, soprattutto, è responsabile dell'applicazione delle policy di sicurezza. [cite: 5] [cite\_start]Un compito cruciale dell'Host è la gestione del consenso dell'utente[cite: 6]; [cite\_start]è l'Host che deve richiedere e ottenere l'approvazione esplicita dell'utente prima che un qualsiasi "Tool" esposto da un Server venga eseguito. [cite: 7]

  * [cite\_start]**Client**: Il Client è un'istanza software che risiede all'interno dell'Host. [cite: 8] [cite\_start]La sua funzione è quella di agire come un agente specializzato nella comunicazione protocollare. [cite: 9] [cite\_start]Ogni Client stabilisce e mantiene una connessione stato-pieno (stateful) e uno-a-uno con un singolo MCP Server. [cite: 10] [cite\_start]Il Client traduce le richieste di alto livello dall'Host in messaggi JSON-RPC 2.0 e li instrada al Server appropriato. [cite: 10] [cite\_start]Gestisce inoltre il ciclo di vita della connessione, la negoziazione delle capacità e la ricezione di notifiche dal Server. [cite: 11]

  * [cite\_start]**Server**: Il Server è il servizio specializzato che espone capacità esterne al mondo AI. [cite: 12] [cite\_start]Questo è il componente che verrà costruito per soddisfare la richiesta dell'utente. [cite: 13] [cite\_start]Un Server MCP è progettato per essere focalizzato su un compito specifico e altamente componibile. [cite: 14] [cite\_start]Può esporre l'accesso a un file system, a un database, o agire da gateway verso un set di API esterne. [cite: 14] [cite\_start]La responsabilità principale del nostro Server sarà quella di fungere da intermediario intelligente e sicuro, gestendo l'autenticazione e inoltrando le richieste alle API di backend. [cite: 15] [cite\_start]Questo eleva il suo ruolo a quello di un componente critico per la sicurezza, la cui progettazione deve seguire standard di robustezza e sicurezza elevati. [cite: 18]

### 1.2. Canali di Comunicazione e Livelli di Trasporto

[cite\_start]L'MCP definisce due meccanismi di trasporto primari per la comunicazione tra Client e Server[cite: 19]:

  * [cite\_start]**stdio (Standard Input/Output)**: Ideale per scenari di sviluppo locale, dove l'Host può gestire il Server come un sottoprocesso. [cite: 19] [cite\_start]È efficiente per la comunicazione sulla stessa macchina e semplifica la gestione del processo del server. [cite: 20]

  * [cite\_start]**HTTP con Server-Sent Events (SSE)**: Richiesto per i Server remoti e centralizzati, accessibili attraverso una rete. [cite: 20] [cite\_start]La comunicazione avviene tramite un endpoint HTTP, tipico per un ambiente di produzione. [cite: 21, 22] [cite\_start]La scelta del trasporto influisce sulla strategia di deployment e sulla sicurezza; un server remoto, ad esempio, richiederà l'uso di TLS (https). [cite: 23, 24]

### 1.3. Il Linguaggio dell'MCP: Primitive e Messaggi

[cite\_start]La comunicazione nell'ecosistema MCP si basa sul formato JSON-RPC 2.0. [cite: 25] [cite\_start]Questo standard definisce la struttura dei messaggi, che si dividono in quattro tipi[cite: 26]:

  * [cite\_start]**Requests**: Messaggi che si aspettano una risposta. [cite: 26]
  * [cite\_start]**Results**: Risposte di successo a una richiesta. [cite: 27]
  * [cite\_start]**Errors**: Risposte che indicano il fallimento di una richiesta. [cite: 27]
  * [cite\_start]**Notifications**: Messaggi unidirezionali che non richiedono risposta. [cite: 28]

[cite\_start]Un Server MCP espone le sue capacità attraverso tre primitive fondamentali[cite: 28]:

  * [cite\_start]**Tools (Strumenti)**: Funzioni che un LLM può decidere di eseguire per compiere azioni, come chiamare un'API esterna. [cite: 29] [cite\_start]Questa è la primitiva centrale per la nostra implementazione. [cite: 30]
  * [cite\_start]**Resources (Risorse)**: Dati di sola lettura che arricchiscono il contesto dell'LLM, come il contenuto di un file o la documentazione di un'API. [cite: 32, 33]
  * [cite\_start]**Prompts (Suggerimenti)**: Template di interazione riutilizzabili per guidare l'utente. [cite: 35]

[cite\_start]L'implementazione si concentrerà esclusivamente sulla creazione di **Tools**. [cite: 36]

### 1.4. Sicurezza e Fiducia by Design

[cite\_start]La sicurezza è un pilastro dell'MCP, con diversi principi incorporati[cite: 37, 38]:

  * [cite\_start]**Consenso e Controllo dell'Utente**: L'Host è l'unico responsabile di ottenere il consenso esplicito dell'utente prima di invocare un tool. [cite: 39] [cite\_start]Il server assume che ogni chiamata ricevuta sia stata pre-approvata. [cite: 40]
  * [cite\_start]**Privacy e Isolamento dei Dati**: I server operano in isolamento, senza accesso alla cronologia della conversazione o ai dati gestiti da altri server. [cite: 41, 42] [cite\_start]L'Host fornisce a ciascun server solo il contesto strettamente necessario. [cite: 43]
  * [cite\_start]**Sicurezza dei Tool**: I tool sono trattati con massima cautela. [cite: 44] [cite\_start]La loro descrizione è considerata non attendibile dall'Host, che deve informare chiaramente l'utente sull'azione imminente. [cite: 45] [cite\_start]È compito dell'Host iniettare in modo sicuro le credenziali (come API key) attraverso le variabili d'ambiente. [cite: 47] [cite\_start]Di conseguenza, il codice del server non deve contenere segreti hardcoded, ma deve leggerli dal suo ambiente di esecuzione. [cite: 48]

## Sezione 2: Progetto Architetturale per un Server Gateway di API Autenticate

L'architettura da implementare è centralizzata e orientata alla produzione:

  * [cite\_start]**Client Fornisce il Bearer Token**: Il client (es. VS Code) viene configurato con un Bearer Token di produzione pre-esistente. [cite: 49] [cite\_start]Questo token è inviato al server MCP tramite l'header `Authorization`. [cite: 50]
  * [cite\_start]**Server MCP come Proxy Autenticato**: Il server agisce come un proxy. [cite: 51] [cite\_start]Riceve la richiesta, estrae il Bearer Token e lo utilizza per chiamare l'API di backend. [cite: 52]
  * [cite\_start]**Endpoint di Produzione**: Le chiamate sono dirette agli URL di produzione (es. `https://company.openapi.com`). [cite: 53]

[cite\_start]Questo design è efficiente e sicuro, poiché il server MCP gestisce solo il token di sessione, non le credenziali utente. [cite: 54]

## Sezione 3: Implementazione Approfondita: Costruire il Server MCP in Python con FastMCP

### 3.1. Gestione dell'Ambiente e delle Dipendenze

Le dipendenze sono semplificate. [cite\_start]Si utilizzano `fastmcp`, `requests` e `pydantic`. [cite: 56]

```bash
uv add "fastmcp" requests pydantic
```

### 3.2. Struttura di Base del Server

[cite\_start]Il file `.env` non è più necessario, poiché il server non gestisce configurazioni o credenziali esterne. [cite: 57]

### 3.3. Codice Server Finale con Pass-through del Token

Di seguito il codice `server.py` completo e semplificato. [cite\_start]Non è presente un `AuthenticationService` in quanto il token viene passato direttamente. [cite: 58, 59]

```python
import os
import sys
import requests
from fastmcp import FastMCP, Context
from typing import Dict, Any, Optional
from pydantic import BaseModel

# --- Modello Pydantic per Risposte di Errore Standard ---
class ApiError(BaseModel):
    error: str
    message: str

# --- Funzione Helper per Chiamate API ---
def make_api_call(ctx: Context, method: str, url: str, **kwargs) -> Any:
    """
    Funzione helper per estrarre il token e fare la chiamata API.
    """
    try:
        # Recupera l'header 'Authorization' inviato dal client mcp.json
        auth_header = ctx.request.headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith('bearer '):
            raise ValueError("Header 'Authorization: Bearer <token>' mancante o malformato.")
    except Exception as e:
        return ApiError(error="Auth Error", message=f"Token non fornito dal client: {e}").dict()

    headers = {"Authorization": auth_header, **kwargs.pop("headers", {})}

    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.exceptions.HTTPError as e:
        # Tenta di leggere il corpo della risposta per un messaggio di errore più chiaro
        error_details = e.response.text
        return ApiError(error="API HTTP Error", message=f"{e.response.status_code}: {error_details}").dict()
    except requests.exceptions.RequestException as e:
        return ApiError(error="API Request Error", message=str(e)).dict()

# --- Inizializzazione del Server MCP ---
mcp = FastMCP(
    name="Openapi.com Gateway",
    instructions="Questo server fornisce un gateway unificato per diversi servizi di openapi.com."
)

# --- Definizione Manuale dei Tool ---
@mcp.tool
async def get_company_full_profile(vat_or_tax_code: str, ctx: Context) -> Any:
    """
    Recupera il profilo completo e dettagliato di un'azienda italiana 
    fornendo la sua Partita IVA o il suo Codice Fiscale.
    """
    print(f"Running Tool: get_company_full_profile per {vat_or_tax_code}")
    url = f"https://company.openapi.com/IT-full/{vat_or_tax_code}"
    return make_api_call(ctx, "GET", url)

@mcp.tool
async def find_cap_by_comune(comune: str, ctx: Context) -> Any:
    """
    Cerca i CAP associati a un dato comune italiano.
    """
    print(f"Running Tool: find_cap_by_comune per {comune}")
    url = "https://cap.openapi.com/cerca_comuni"
    params = {"comune": comune}
    return make_api_call(ctx, "GET", url, params=params)

# --- Puoi aggiungere altri tool per le altre API qui seguendo lo stesso pattern ---

if __name__ == "__main__":
    print(f"\n--- Server Pronto ---")
    print("Per avviare in modalità remota, eseguire:")
    print("python server.py")
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

## Sezione 6: Guida Pratica al Test (Scenario Remoto Protetto e Multi-API)

### 6.1. Configurazione dell'Ambiente di Sviluppo (Esempio Ubuntu 24.04 LTS)

#### 6.1.1. Prerequisiti Software

  * [cite\_start]**Sistema Operativo**: Ubuntu 24.04 LTS (Noble Numbat) [cite: 67]
  * [cite\_start]Accesso al Terminale [cite: 67]
  * [cite\_start]Connessione Internet [cite: 67]

#### 6.1.2. Passaggi di Configurazione

1.  **Aggiornamento del Sistema**:
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```
2.  **Installazione di Python e Strumenti Correlati**:
    ```bash
    sudo apt install python3 python3-pip python3-venv -y
    ```
3.  **Installazione di uv**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    [cite\_start]Dopo l'installazione, segui le istruzioni per aggiungere `uv` al PATH. [cite: 68]
4.  **Installazione di Visual Studio Code**:
    ```bash
    sudo snap install --classic code
    ```
    [cite\_start]Avvia VS Code e installa l'estensione **GitHub Copilot Chat**. [cite: 69]
5.  **Creazione della Struttura del Progetto**:
    ```bash
    mkdir mcp_gateway
    cd mcp_gateway
    uv init
    uv venv
    source .venv/bin/activate
    uv add "fastmcp" requests pydantic
    ```
6.  [cite\_start]**Creazione dei File di Progetto**: Crea il file `server.py` come descritto nella Sezione 3.3. [cite: 70]

### 6.2. Avviare il Server MCP Remoto

1.  [cite\_start]**Prepara il Server**: Assicurati che la directory del progetto con `server.py` sia sulla macchina server. [cite: 71]
2.  [cite\_start]**Avvia il Server**: Nel terminale del server, attiva l'ambiente virtuale e avvia lo script. [cite: 72]
    ```bash
    cd mcp_gateway
    source .venv/bin/activate
    python server.py
    ```
    [cite\_start]Il server sarà in esecuzione su `http://0.0.0.0:8000`. [cite: 73]

### 6.3. Configurare e Testare il Client VS Code Remoto

[cite\_start]Sulla macchina client, configura VS Code per inviare il Bearer Token. [cite: 74]

1.  [cite\_start]**Ottieni il Tuo Bearer Token**: Genera un Bearer Token valido dal portale `https://console.openapi.com/oauth`. [cite: 75] [cite\_start]Assicurati di creare un token con gli scope necessari (es. `*:*/*`). [cite: 76]

2.  [cite\_start]**Crea la Configurazione `.vscode/mcp.json`**: Nel progetto VS Code, crea il file `.vscode/mcp.json` con la seguente configurazione[cite: 77]:

    ```json
    {
      "servers": {
        "openapi.com": {
          "type": "http",
          "url": "http://INDIRIZZO_IP_DEL_TUO_SERVER:8000/mcp/",
          "headers": {
            "Authorization": "Bearer IL_TUO_BEARER_TOKEN_DI_PRODUZIONE"
          }
        }
      }
    }
    ```

      * [cite\_start]Sostituisci `INDIRIZZO_IP_DEL_TUO_SERVER` con l'IP della macchina server. [cite: 78]
      * [cite\_start]Sostituisci `IL_TUO_BEARER_TOKEN_DI_PRODUZIONE` con il token generato. [cite: 79]

3.  **Esegui il Test**:

      * [cite\_start]Ricarica la finestra di VS Code. [cite: 79]
      * Apri la chat di Copilot e digita `@workspace`. [cite\_start]Vedrai il tool `openapi.com`. [cite: 80]
      * [cite\_start]Invia un prompt per testare una delle API, ad esempio[cite: 81]:
        ```
        @workspace usa lo strumento di openapi.com per trovare i dati dell'azienda con partita IVA 12485671007
        ```

4.  **Analizza il Flusso**:

      * [cite\_start]VS Code invia la richiesta al server MCP, includendo l'header `Authorization: Bearer ...`. [cite: 81]
      * [cite\_start]La funzione helper `make_api_call` estrae questo header. [cite: 81]
      * [cite\_start]Il token viene usato direttamente per chiamare l'API di backend richiesta. [cite: 82]

[cite\_start]Questo completa il ciclo, dimostrando un'architettura di produzione efficiente, sicura e scalabile. [cite: 83]