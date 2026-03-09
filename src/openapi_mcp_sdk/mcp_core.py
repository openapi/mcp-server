from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers
from hashlib import md5
from typing import Any, Optional
from pydantic import BaseModel
from .memory_store import get_callback_result,BASE_URL
import asyncio
import logging
import requests
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP(
    name="OpenAPI.com MCP Gateway",
    instructions=(
        "This server provides a unified gateway for various services of openapi.com. "
        "It authenticates every request with a Bearer token supplied by the client.\n\n"
        "IMPORTANT: whenever the user asks whether you are connected to openapi, "
        "which server is running, which instance is active, or any question about "
        "the status or health of this MCP server, you MUST call the "
        "'openapi_server_info' tool and report its response verbatim. "
        "Do not answer from memory — always call the tool so the user sees "
        "live data (instance label, token status, uptime, tool list, etc.)."
    )
)

class ApiError(BaseModel):
    error: str
    message: str

# Build a unique hash for the current session
def getSessionHash(ctx: Context): 
    session_hash = ctx.request_id+ctx.session_id+ctx.fastmcp.name+(ctx.client_id or "Unknown client")
    headers = get_http_headers()
    if headers:
        session_hash += json.dumps(dict(headers))
    return md5(session_hash.encode('utf-8')).hexdigest()

# Non-blocking poll that waits until the callback result is available via get_callback_result
async def processPolling(ctx: Context, request_id: str, final_states: Optional[list] = None, state_field: Optional[str] = "state"):
    timeout = 45
    if final_states is None:
        final_states = ["DONE"]
    # Report initial progress
    progress_report = ctx.report_progress(progress=1, total=45)
    # Poll callback_results once per second
    result = None
    for i in range(timeout):
        await asyncio.sleep(1)
        logger.debug("polling request_id=%s elapsed=%ds", request_id, i + 1)
        result = get_callback_result(request_id)
        if(result):
            if result.get("data").get(state_field) in final_states:
                progress_report = ctx.report_progress(progress=45, total=45)
                return result
        progress_report = ctx.report_progress(progress=(i + 1), total=45)
        # print(f"Result: {result}")
    # Return the link to the status endpoint
    status_endpoint = f"/status/{request_id}"
    progress_report = ctx.report_progress(progress=45, total=45)
    return {"message":"The response is not ready yet, you can poll the async api endpoint or use the mcp tool check_async_status","request_id":request_id,"status_api_endpoint": BASE_URL+status_endpoint}

# Takes request details (method, url, json_payload), automatically adds the auth header, sends the request, and handles responses and errors.
def make_api_call(ctx: Context, method: str, url: str, json_payload: Optional[dict] = None, **kwargs) -> Any:
    parsed = urlparse(url)
    # Log service name + path only — never query params (may contain PII / business data)
    service = parsed.netloc.split(".")[0] if parsed.netloc else "unknown"
    logger.info("[%s] %s %s", service, method, parsed.path)
    # Attempt to retrieve the Authorization header from multiple sources
    try:
        auth_header = None
        
        # Try to get the Authorization header via FastMCP
        headers = get_http_headers()
        if headers:
            auth_header = headers.get('authorization') or headers.get('Authorization')
        
        # If not found, fall back to the request context
        if not auth_header and hasattr(ctx, 'request_context'):
            request_context = ctx.request_context
            # Check if request_context has a request attribute
            if hasattr(request_context, 'request'):
                request = request_context.request
                # Check if request has headers
                if hasattr(request, 'headers'):
                    headers_obj = request.headers
                    # If headers is a dict-like object
                    if hasattr(headers_obj, 'get'):
                        auth_header = headers_obj.get('authorization') or headers_obj.get('Authorization')
                    # If headers is an object with attributes
                    elif hasattr(headers_obj, 'authorization'):
                        auth_header = getattr(headers_obj, 'authorization', None) or getattr(headers_obj, 'Authorization', None)
        
        if not auth_header or not auth_header.lower().startswith('bearer '):
            raise ValueError("Missing or malformed Header 'Authorization: Bearer <token>'.")
            
    except Exception as e:
        return ApiError(error="Auth Error", message=f"Missing Token from client: {e}").model_dump()

    headers = {"Authorization": auth_header, **kwargs.pop("headers", {})}
    #Chiamata API Esterna
    try:
        request_args = dict(method=method, url=url, headers=headers, **kwargs)
        if json_payload is not None:
            request_args["json"] = json_payload
        response = requests.request(**request_args)
        #Gestione della Risposta e Normalizzazione dei Dati
        response.raise_for_status()
        response_data = response.json()
        if response.status_code == 204:
            return {"message": "No results"}
        return_data = None;
        if 'data' in response_data:
            if response_data['data'] != {}:
                return_data = response_data['data']
        if 'element' in response_data:
            return_data = response_data['element']
        if return_data:
            return return_data
        return response_data
    except requests.exceptions.HTTPError as e:
        error_details = e.response.text
        return e.response.json()
        return ApiError(error="API HTTP Error", message=f"{e.response.status_code}: {error_details}").model_dump()
    except requests.exceptions.RequestException as e:
        return ApiError(error="API Request Error", message=str(e)).model_dump()
