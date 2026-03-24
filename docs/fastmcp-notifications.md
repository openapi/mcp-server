# FastMCP Notifications

Reference for sending notifications from an MCP server to a connected client using FastMCP.

---

## Automatic list-change notifications

Since FastMCP 2.9.1, the server automatically sends a list-changed notification to the
client whenever tools, resources, or prompts are added, removed, enabled, or disabled.
No manual code is needed for these cases.

### Tools

```python
@mcp.tool
def example_tool() -> str:
    return "Hello!"

mcp.add_tool(example_tool)       # sends tools/list_changed
example_tool.disable()           # sends tools/list_changed
example_tool.enable()            # sends tools/list_changed
mcp.remove_tool("example_tool")  # sends tools/list_changed
```

### Resources

```python
@mcp.resource("data://example")
def example_resource() -> str:
    return "Hello!"

mcp.add_resource(example_resource)  # sends resources/list_changed
example_resource.disable()          # sends resources/list_changed
example_resource.enable()           # sends resources/list_changed
```

### Prompts

```python
@mcp.prompt
def example_prompt() -> str:
    return "Hello!"

mcp.add_prompt(example_prompt)  # sends prompts/list_changed
example_prompt.disable()        # sends prompts/list_changed
example_prompt.enable()         # sends prompts/list_changed
```

---

## Manual notifications via Context

For edge cases where you need to send notifications explicitly:

```python
from fastmcp import FastMCP, Context

mcp = FastMCP(name="MyServer")

@mcp.tool
async def refresh_all(ctx: Context) -> str:
    await ctx.send_tool_list_changed()
    await ctx.send_resource_list_changed()
    await ctx.send_prompt_list_changed()
    return "Notifications sent"
```

---

## Progress notifications

Report progress during long-running tool calls:

```python
@mcp.tool
async def long_task(ctx: Context) -> str:
    await ctx.report_progress(progress=0, total=100)
    # ... work ...
    await ctx.report_progress(progress=50, total=100)
    # ... more work ...
    await ctx.report_progress(progress=100, total=100)
    return "Done"
```

---

## Log notifications

Send log messages to the client from inside a tool:

```python
@mcp.tool
async def debug_tool(ctx: Context) -> str:
    await ctx.debug("Starting processing")
    await ctx.info("Processing in progress")
    await ctx.warning("Deprecated parameter detected")
    await ctx.error("Error during processing")
    return "Processing complete"
```

---

## Notifying async task completion (without polling)

When a tool starts a background task, use one of the following patterns to push
completion back to the client instead of requiring it to poll.

### Pattern 1 — Progress reporting as completion signal

Keep the MCP connection open and stream progress until the task finishes:

```python
import asyncio
from fastmcp import FastMCP, Context

mcp = FastMCP("AsyncTaskServer")
running_tasks = {}

@mcp.tool
async def start_long_task(task_id: str, ctx: Context) -> dict:
    """Start an async task and return immediately with an ID."""
    task = asyncio.create_task(_run(task_id, ctx))
    running_tasks[task_id] = task
    await ctx.report_progress(progress=0, total=100)
    return {"task_id": task_id, "status": "started"}

async def _run(task_id: str, ctx: Context):
    for i in range(1, 101):
        await asyncio.sleep(0.1)
        await ctx.report_progress(progress=i, total=100)
    await ctx.info(f"Task {task_id} completed")
    running_tasks.pop(task_id, None)
```

### Pattern 2 — Resource updates

Publish task state as a resource and notify the client when it changes:

```python
import asyncio
from datetime import datetime
from fastmcp import FastMCP, Context

mcp = FastMCP("CallbackTaskServer")
task_results: dict = {}
task_status: dict = {}

@mcp.tool
async def start_background_task(task_name: str, ctx: Context) -> dict:
    task_id = f"{task_name}_{datetime.now().isoformat()}"
    task_status[task_id] = {"status": "running", "progress": 0}
    asyncio.create_task(_worker(task_id, ctx))
    return {"task_id": task_id, "resource_uri": f"task://{task_id}/status"}

async def _worker(task_id: str, ctx: Context):
    for i in range(1, 11):
        await asyncio.sleep(1)
        task_status[task_id]["progress"] = i * 10
    task_status[task_id]["status"] = "completed"
    task_results[task_id] = {"result": "success"}
    await ctx.send_resource_list_changed()

@mcp.resource("task://{task_id}/status")
def get_task_status(task_id: str) -> dict:
    return task_status.get(task_id, {"status": "not_found"})
```

### Pattern 3 — Webhook

For distributed or multi-instance deployments, fire an HTTP webhook when the task completes:

```python
import asyncio
import aiohttp
from fastmcp import FastMCP, Context

mcp = FastMCP("WebhookTaskServer")
active_tasks: dict = {}

@mcp.tool
async def start_task_with_webhook(task_name: str, webhook_url: str, ctx: Context) -> dict:
    task_id = f"task_{len(active_tasks) + 1}"
    active_tasks[task_id] = {"name": task_name, "status": "running"}
    asyncio.create_task(_webhook_worker(task_id, task_name, webhook_url, ctx))
    return {"task_id": task_id, "status": "started"}

async def _webhook_worker(task_id: str, task_name: str, webhook_url: str, ctx: Context):
    await asyncio.sleep(5)  # simulate work
    active_tasks[task_id]["status"] = "completed"
    await ctx.info(f"Task {task_id} completed")
    if webhook_url:
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json={"task_id": task_id, "status": "completed"})
```

---

## Choosing a pattern

| Task duration | Deployment | Recommended pattern |
|---|---|---|
| < 30 s | Single server | Progress reporting |
| > 30 s | Single server | Progress + resource updates |
| Any | Multi-instance / distributed | Webhook |
| Any | High reliability required | Event-driven with persistence |

---

## References

- [Progress Reporting](https://gofastmcp.com/servers/progress)
- [Server Context](https://gofastmcp.com/servers/context)
- [Message Handling (client side)](https://gofastmcp.com/clients/messages)
