import requests
from fastmcp import FastMCP, Context
from fastapi import FastAPI, Request, APIRouter
from typing import Any, Optional
from pydantic import BaseModel

mcp = FastMCP(
    name="OpenAPI.com Gateway",
    instructions="Questo server fornisce un gateway unificato per diversi servizi di openapi.com."
)

class ApiError(BaseModel):
    error: str
    message: str

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
        return ApiError(error="Auth Error", message=f"Token non fornito dal client: {e}").dict()

    headers = {"Authorization": auth_header, **kwargs.pop("headers", {})}
    try:
        request_args = dict(method=method, url=url, headers=headers, **kwargs)
        if json_payload is not None:
            request_args["json"] = json_payload
        response = requests.request(**request_args)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.exceptions.HTTPError as e:
        error_details = e.response.text
        return ApiError(error="API HTTP Error", message=f"{e.response.status_code}: {error_details}").dict()
    except requests.exceptions.RequestException as e:
        return ApiError(error="API Request Error", message=str(e)).dict()