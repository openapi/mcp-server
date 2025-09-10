from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers
from hashlib import md5
from typing import Any, Optional
from pydantic import BaseModel
from src.openapi_mcp_server.memory_store import get_callback_result,BASE_URL
import asyncio
import requests
import json

mcp = FastMCP(
    name="OpenAPI.com MCP Gateway",
    instructions="This server provides a unified gateway for various services of openapi.com. using a token as autentication."
)

class ApiError(BaseModel):
    error: str
    message: str

def getSessionHash(ctx: Context): 
    session_hash = ctx.request_id+ctx.session_id+ctx.fastmcp.name+(ctx.client_id or "Unknown client")
    headers = get_http_headers()
    if headers:
        session_hash += json.dumps(dict(headers))
    return md5(session_hash.encode('utf-8')).hexdigest()

async def processPolling(ctx: Context, request_id: str, final_states: Optional[list] = None, state_field: Optional[str] = "state"):
    timeout = 45
    if final_states is None:
        final_states = ["DONE"]
    # Riporto il progresso
    progress_report = ctx.report_progress(progress=1, total=45)
    # avvia un polling ogni secondo su callback_results 
    result = None
    for i in range(timeout):  # Poll up to 10 seconds
        await asyncio.sleep(1)
        print(f"Wait: {i}")
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

def make_api_call(ctx: Context, method: str, url: str, json_payload: Optional[dict] = None, **kwargs) -> Any:
    print(f"Call api url: {url}")
    for attr in dir(ctx):
        if not attr.startswith('__'):
            try:
                value = getattr(ctx, attr)
                # print(f"  ctx.{attr} = {value}")
            except Exception as e:
                print(f"  ctx.{attr} = <errore: {e}>")
    
    try:
        auth_header = None
        
        # Prova a ottenere l'header Authorization usando il metodo FastMCP
        headers = get_http_headers()
        if headers:
            auth_header = headers.get('authorization') or headers.get('Authorization')
        
        # Se non trovato, prova con il context
        if not auth_header and hasattr(ctx, 'request_context'):
            request_context = ctx.request_context
            # Controlla se request_context ha l'attributo request
            if hasattr(request_context, 'request'):
                request = request_context.request
                # Controlla se request ha headers
                if hasattr(request, 'headers'):
                    headers_obj = request.headers
                    # Se headers è un dizionario
                    if hasattr(headers_obj, 'get'):
                        auth_header = headers_obj.get('authorization') or headers_obj.get('Authorization')
                    # Se headers è un oggetto con attributi
                    elif hasattr(headers_obj, 'authorization'):
                        auth_header = getattr(headers_obj, 'authorization', None) or getattr(headers_obj, 'Authorization', None)
        
        if not auth_header or not auth_header.lower().startswith('bearer '):
            raise ValueError("Missing or malformed Header 'Authorization: Bearer <token>'.")
            
    except Exception as e:
        return ApiError(error="Auth Error", message=f"Missing Token from client: {e}").model_dump()

    headers = {"Authorization": auth_header, **kwargs.pop("headers", {})}
    try:
        request_args = dict(method=method, url=url, headers=headers, **kwargs)
        if json_payload is not None:
            request_args["json"] = json_payload
        response = requests.request(**request_args)
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
