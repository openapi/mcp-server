from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers
from hashlib import md5
from fastapi import FastAPI, Request, HTTPException
# from fastapi import FastAPI, Request, APIRouter
from typing import Any, Optional
from pydantic import BaseModel
from memory_store import get_callback_result,BASE_URL
import asyncio

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
    ctx.report_progress(progress=1, total=45)
    # avvia un polling ogni secondo su callback_results 
    result = None
    for i in range(timeout):  # Poll up to 10 seconds
        await asyncio.sleep(1)
        print(f"Wait: {i}")
        result = get_callback_result(request_id)
        if result.get("data").get(state_field) in final_states:
            ctx.report_progress(progress=45, total=45)
            return result
        ctx.report_progress(progress=(i + 1), total=45)
        # print(f"Result: {result}")
    # Return the link to the status endpoint
    status_endpoint = f"/status/{request_id}"
    ctx.report_progress(progress=45, total=45)
    return {"message":"The response is not ready yet, you can poll the async api endpoint or use the mcp tool check_async_status","request_id":request_id,"status_api_endpoint": BASE_URL+status_endpoint}

import requests
import json
"""
Makes an API call to the specified URL using the provided HTTP method and optional JSON payload.

Args:
    ctx (Context): The context object containing request-related information, such as headers.
    method (str): The HTTP method to use for the API call (e.g., 'GET', 'POST', 'PUT', 'DELETE').
    url (str): The URL of the API endpoint to call.
    json_payload (Optional[dict], optional): A dictionary containing the JSON payload to send with the request. Defaults to None.
    **kwargs: Additional keyword arguments to pass to the `requests.request` function (e.g., query parameters, timeout).

Returns:
    Any: The response data from the API call. If the response contains a 'data' or 'element' key, its value is returned.
         Otherwise, the entire response JSON is returned. In case of errors, a dictionary with error details is returned.

Raises:
    ValueError: If the 'Authorization' header is missing or malformed.
    requests.exceptions.HTTPError: If the HTTP request returns an unsuccessful status code.
    requests.exceptions.RequestException: For other request-related errors.

Notes:
    - The function extracts the 'Authorization' header from the request context and ensures it is in the correct format ('Bearer <token>').
    - If the 'Authorization' header is missing or malformed, an error response is returned.
    - The function handles HTTP and request exceptions, returning error details in a structured format.
    - The function logs the API URL being called and attempts to print attributes of the context object for debugging purposes.
"""
def make_api_call(ctx: Context, method: str, url: str, json_payload: Optional[dict] = None, **kwargs) -> Any:
    print(f"Call api url: {url}")
    for attr in dir(ctx):
        if not attr.startswith('__'):
            try:
                value = getattr(ctx, attr)
            except Exception as e:
                print(f"  ctx.{attr} = <errore: {e}>")
    headers_dict = None
    if hasattr(ctx, 'request_context') and hasattr(ctx.request_context, 'request'):
        headers_dict = ctx.request_context.request.headers
    try:
        auth_header = None
        if headers_dict:
            auth_header = headers_dict.get('authorization') or headers_dict.get('Authorization')
        if not auth_header or not auth_header.lower().startswith('bearer '):
            raise ValueError("Header 'Authorization: Bearer <token>' mancante o malformato.")
    except Exception as e:
        return ApiError(error="Auth Error", message=f"Missing Token from client: {e}").dict()

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
        return ApiError(error="API HTTP Error", message=f"{e.response.status_code}: {error_details}").dict()
    except requests.exceptions.RequestException as e:
        return ApiError(error="API Request Error", message=str(e)).dict()
