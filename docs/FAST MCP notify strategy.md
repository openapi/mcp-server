esiste un metodo per mandare una notifica al client?  
Searched notification client send notify  
Searched send notification context ctx send\_tool\_list\_changed send\_resource\_list\_changed  
Sì, esistono diversi metodi per inviare notifiche al client in FastMCP\! Basandomi sui risultati della ricerca, ecco le opzioni disponibili:

## Notifiche Automatiche di Cambiamento Lista

Versione 2.9.1+: FastMCP invia automaticamente notifiche ai client quando tools, resources o prompts vengono aggiunti, rimossi, abilitati o disabilitati.

### Notifiche Tools

```

@mcp.tool
def example_tool() -> str:
   return "Hello!"

# Queste operazioni inviano automaticamente notifiche:
mcp.add_tool(example_tool)     # Invia tools/list_changed notification
example_tool.disable()         # Invia tools/list_changed notification 
example_tool.enable()          # Invia tools/list_changed notification
mcp.remove_tool("example_tool") # Invia tools/list_changed notification
```

### Notifiche Resources

```

@mcp.resource("data://example")
def example_resource() -> str:
   return "Hello!"

# Queste operazioni inviano automaticamente notifiche:
mcp.add_resource(example_resource)  # Invia resources/list_changed notification
example_resource.disable()          # Invia resources/list_changed notification 
example_resource.enable()           # Invia resources/list_changed notification
```

### Notifiche Prompts

```

@mcp.prompt
def example_prompt() -> str:
   return "Hello!"

# Queste operazioni inviano automaticamente notifiche:
mcp.add_prompt(example_prompt)  # Invia prompts/list_changed notification
example_prompt.disable()        # Invia prompts/list_changed notification 
example_prompt.enable()         # Invia prompts/list_changed notification
```

## Notifiche Manuali tramite Context

Per casi rari dove hai bisogno di inviare notifiche manualmente, puoi usare i metodi del contesto:

```

from fastmcp import FastMCP, Context

mcp = FastMCP(name="NotificationServer")

@mcp.tool
async def custom_tool_management(ctx: Context) -> str:
   """Esempio di notifica manuale dopo modifiche personalizzate ai tools."""
  
   # Dopo aver fatto modifiche personalizzate ai tools
   await ctx.send_tool_list_changed()
   await ctx.send_resource_list_changed()
   await ctx.send_prompt_list_changed()
  
   return "Notifiche inviate"
```

## Altri Tipi di Notifiche

FastMCP supporta anche altri tipi di notifiche attraverso il contesto:

### Progress Notifications

```

@mcp.tool
async def long_running_task(ctx: Context) -> str:
   """Task con notifiche di progresso."""
   await ctx.report_progress(progress=50, total=100)
   # ... lavoro ...
   await ctx.report_progress(progress=100, total=100)
   return "Completato"
```

### Log Notifications

```

@mcp.tool
async def debug_tool(ctx: Context) -> str:
   """Tool con notifiche di log."""
   await ctx.debug("Inizio elaborazione")
   await ctx.info("Elaborazione in corso")
   await ctx.warning("Attenzione: parametro deprecato")
   await ctx.error("Errore durante l'elaborazione")
   return "Elaborazione completata"
```

## Note Importanti

* Contesto di Richiesta: Le notifiche automatiche vengono inviate solo quando le operazioni avvengono all'interno di un contesto di richiesta MCP attivo  
* Inizializzazione: Le operazioni eseguite durante l'inizializzazione del server non attivano notifiche  
* Gestione Client: I client possono gestire queste notifiche usando un [message handler](https://gofastmcp.com/clients/messages) per aggiornare automaticamente le loro interfacce

[Message Handling documentation](https://gofastmcp.com/clients/messages)  
[MCP Context documentation](https://gofastmcp.com/servers/context)  
[Progress Reporting documentation](https://gofastmcp.com/servers/progress)  
come notifica quando un processo asincrono iniziato da un tool è terminato evitando il polling?  
Searched async background task notification completion webhook  
Searched background task asyncio task completion notification webhook callback  
Basandomi sui risultati della ricerca, posso fornirti diverse strategie per notificare quando un processo asincrono iniziato da un tool è terminato, evitando il polling:

## Strategie per Notifiche di Completamento

### 1\. Progress Reporting con Stato Finale

Il modo più diretto è utilizzare il sistema di progress reporting di FastMCP per notificare il completamento:

```

import asyncio
from fastmcp import FastMCP, Context

mcp = FastMCP("AsyncTaskServer")

# Dizionario per tracciare i task in corso
running_tasks = {}

@mcp.tool
async def start_long_task(task_id: str, ctx: Context) -> dict:
   """Avvia un task asincrono e restituisce immediatamente un ID."""
  
   # Avvia il task in background
   task = asyncio.create_task(long_running_process(task_id, ctx))
   running_tasks[task_id] = task
  
   await ctx.info(f"Task {task_id} avviato")
   await ctx.report_progress(progress=0, total=100)
  
   return {
       "task_id": task_id,
       "status": "started",
       "message": "Task avviato in background"
   }

async def long_running_process(task_id: str, ctx: Context):
   """Processo lungo che riporta il progresso."""
   try:
       # Simula lavoro con progress reporting
       for i in range(1, 101):
           await asyncio.sleep(0.1)  # Simula lavoro
           await ctx.report_progress(progress=i, total=100)
          
           if i % 20 == 0:
               await ctx.info(f"Task {task_id}: {i}% completato")
      
       # Notifica completamento
       await ctx.info(f"✅ Task {task_id} completato con successo!")
       await ctx.report_progress(progress=100, total=100)
      
   except Exception as e:
       await ctx.error(f"❌ Task {task_id} fallito: {str(e)}")
   finally:
       # Rimuovi il task dalla lista
       running_tasks.pop(task_id, None)

@mcp.tool
async def check_task_status(task_id: str) -> dict:
   """Controlla lo stato di un task."""
   if task_id in running_tasks:
       task = running_tasks[task_id]
       return {
           "task_id": task_id,
           "status": "running" if not task.done() else "completed",
           "done": task.done()
       }
   else:
       return {
           "task_id": task_id,
           "status": "not_found"
       }
```

### 2\. Sistema di Callback con Resource Updates

Utilizza le risorse dinamiche per fornire aggiornamenti di stato:

```

import asyncio
from datetime import datetime
from fastmcp import FastMCP, Context

mcp = FastMCP("CallbackTaskServer")

# Storage per i risultati dei task
task_results = {}
task_status = {}

@mcp.tool
async def start_background_task(task_name: str, ctx: Context) -> dict:
   """Avvia un task in background e restituisce un ID per il tracking."""
   task_id = f"{task_name}_{datetime.now().isoformat()}"
  
   # Inizializza lo stato
   task_status[task_id] = {
       "status": "running",
       "started_at": datetime.now().isoformat(),
       "progress": 0
   }
  
   # Avvia il task
   asyncio.create_task(background_worker(task_id, task_name, ctx))
  
   await ctx.info(f"Task {task_id} avviato")
  
   return {
       "task_id": task_id,
       "status": "started",
       "resource_uri": f"task://{task_id}/status"
   }

async def background_worker(task_id: str, task_name: str, ctx: Context):
   """Worker che esegue il lavoro in background."""
   try:
       # Simula lavoro
       for i in range(1, 11):
           await asyncio.sleep(1)
          
           # Aggiorna lo stato
           task_status[task_id]["progress"] = i * 10
           await ctx.info(f"Task {task_id}: {i*10}% completato")
      
       # Completamento
       task_status[task_id].update({
           "status": "completed",
           "completed_at": datetime.now().isoformat(),
           "progress": 100
       })
      
       task_results[task_id] = {
           "result": f"Task {task_name} completato con successo!",
           "data": {"processed_items": 100, "errors": 0}
       }
      
       await ctx.info(f"✅ Task {task_id} completato!")
      
       # Invia notifica di cambiamento risorsa
       await ctx.send_resource_list_changed()
      
   except Exception as e:
       task_status[task_id].update({
           "status": "failed",
           "error": str(e),
           "failed_at": datetime.now().isoformat()
       })
       await ctx.error(f"❌ Task {task_id} fallito: {str(e)}")

# Resource per controllare lo stato
@mcp.resource("task://{task_id}/status")
def get_task_status(task_id: str) -> dict:
   """Ottieni lo stato corrente di un task."""
   return task_status.get(task_id, {"status": "not_found"})

# Resource per ottenere i risultati
@mcp.resource("task://{task_id}/result")
def get_task_result(task_id: str) -> dict:
   """Ottieni il risultato di un task completato."""
   if task_id in task_results:
       return task_results[task_id]
   return {"error": "Task not found or not completed"}
```

### 3\. Sistema di Notifiche con Custom Routes (HTTP)

Per server HTTP, puoi implementare webhook o endpoint di notifica:

```

import asyncio
from fastmcp import FastMCP, Context
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("WebhookTaskServer")

# Storage per task e callback
active_tasks = {}
task_callbacks = {}

@mcp.tool
async def start_task_with_webhook(
   task_name: str,
   webhook_url: str = None,
   ctx: Context
) -> dict:
   """Avvia un task con notifica webhook opzionale."""
   task_id = f"task_{len(active_tasks) + 1}"
  
   active_tasks[task_id] = {
       "name": task_name,
       "status": "running",
       "webhook_url": webhook_url
   }
  
   # Avvia il task
   asyncio.create_task(webhook_worker(task_id, task_name, webhook_url, ctx))
  
   return {
       "task_id": task_id,
       "status": "started",
       "webhook_url": webhook_url,
       "status_endpoint": f"/task/{task_id}/status"
   }

async def webhook_worker(task_id: str, task_name: str, webhook_url: str, ctx: Context):
   """Worker che notifica via webhook al completamento."""
   try:
       # Simula lavoro
       await asyncio.sleep(5)
      
       # Aggiorna stato
       active_tasks[task_id]["status"] = "completed"
       active_tasks[task_id]["result"] = f"Task {task_name} completato!"
      
       await ctx.info(f"✅ Task {task_id} completato!")
      
       # Invia webhook se configurato
       if webhook_url:
           await send_webhook_notification(webhook_url, task_id, "completed")
          
   except Exception as e:
       active_tasks[task_id]["status"] = "failed"
       active_tasks[task_id]["error"] = str(e)
       await ctx.error(f"❌ Task {task_id} fallito: {str(e)}")

async def send_webhook_notification(webhook_url: str, task_id: str, status: str):
   """Invia notifica webhook."""
   import aiohttp
  
   payload = {
       "task_id": task_id,
       "status": status,
       "timestamp": datetime.now().isoformat()
   }
  
   try:
       async with aiohttp.ClientSession() as session:
           async with session.post(webhook_url, json=payload) as response:
               print(f"Webhook inviato: {response.status}")
   except Exception as e:
       print(f"Errore invio webhook: {e}")

# Endpoint per controllare lo stato
@mcp.custom_route("/task/{task_id}/status", methods=["GET"])
async def task_status_endpoint(request: Request) -> JSONResponse:
   task_id = request.path_params["task_id"]
   task = active_tasks.get(task_id, {"status": "not_found"})
   return JSONResponse(task)
```

### 4\. Pattern Event-Driven con Notifiche

Implementa un sistema di eventi per notifiche più sofisticate:

```

import asyncio
from typing import Dict, List, Callable
from fastmcp import FastMCP, Context

mcp = FastMCP("EventDrivenServer")

class TaskEventManager:
   def __init__(self):
       self.listeners: Dict[str, List[Callable]] = {}
       self.task_states = {}
  
   def subscribe(self, event_type: str, callback: Callable):
       if event_type not in self.listeners:
           self.listeners[event_type] = []
       self.listeners[event_type].append(callback)
  
   async def emit(self, event_type: str, data: dict):
       if event_type in self.listeners:
           for callback in self.listeners[event_type]:
               await callback(data)

# Manager globale degli eventi
event_manager = TaskEventManager()

@mcp.tool
async def start_monitored_task(task_name: str, ctx: Context) -> dict:
   """Avvia un task con monitoraggio eventi."""
   task_id = f"monitored_{len(event_manager.task_states) + 1}"
  
   # Registra listener per questo task
   async def task_completion_handler(data):
       if data["task_id"] == task_id:
           await ctx.info(f"🔔 Notifica: Task {task_id} {data['status']}")
           if data["status"] == "completed":
               await ctx.info(f"✅ Risultato: {data.get('result', 'N/A')}")
  
   event_manager.subscribe("task_completed", task_completion_handler)
   event_manager.subscribe("task_failed", task_completion_handler)
  
   # Avvia il task
   asyncio.create_task(monitored_worker(task_id, task_name))
  
   return {
       "task_id": task_id,
       "status": "started",
       "monitoring": "enabled"
   }

async def monitored_worker(task_id: str, task_name: str):
   """Worker con eventi."""
   try:
       event_manager.task_states[task_id] = "running"
      
       # Simula lavoro
       await asyncio.sleep(3)
      
       # Emetti evento di completamento
       await event_manager.emit("task_completed", {
           "task_id": task_id,
           "status": "completed",
           "result": f"Task {task_name} completato con successo!"
       })
      
       event_manager.task_states[task_id] = "completed"
      
   except Exception as e:
       await event_manager.emit("task_failed", {
           "task_id": task_id,
           "status": "failed",
           "error": str(e)
       })
       event_manager.task_states[task_id] = "failed"
```

## Raccomandazioni

1. Per task brevi (\< 30 secondi): Usa progress reporting  
2. Per task lunghi: Combina progress reporting con resource updates  
3. Per sistemi distribuiti: Implementa webhook o sistemi di messaggistica  
4. Per alta affidabilità: Usa un sistema di eventi con persistenza

La scelta dipende dalla durata dei task, dall'architettura del sistema e dai requisiti di affidabilità.  
[Progress Reporting documentation](https://gofastmcp.com/servers/progress)  
[Server Context documentation](https://gofastmcp.com/servers/context)  
[Custom Routes documentation](https://gofastmcp.com/deployment/running-server)

