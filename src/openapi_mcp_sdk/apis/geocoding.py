import logging
logging.getLogger(__name__).debug("module loaded")
from fastmcp import Context
from typing import Any
from ..mcp_core import make_api_call, mcp
from ..memory_store import SANDBOX_PREFIX

@mcp.tool
async def geocode(address: str, ctx: Context) -> Any:
    """Retrieve informations about a place supplying address.
    To improve success of results, please specify an address conforming to the following format: [street], [city] [postal code] [country]
    Args:
        address: string
    """
    print(f"Running Tool: geocode {address}")
    
    url = f"https://{SANDBOX_PREFIX}geocoding.openapi.it/geocode"
    api_call =  make_api_call(ctx, "POST", url, json_payload={
        "address": address
    })
    print(api_call)
    return api_call
@mcp.tool
async def reverse_geocode(type: str,id: str,lat: float,long: float, ctx: Context) -> Any:
    """Get place information from ID or latitude/longitude:
    To obtain infos via ID make sure to pass the following format:
    {"type": "id", "id": "<id>"}
    To obtain infos via lat/long, make sure to provide the following format:
    {"type": "coordinates", "lat": "<lat>", "long": "<long>"}
    Args:
        type: required, can be "coordinates" or "id"
        id: string required only for type=id
        lat: the latitude number($float) example: 41.289294
        long: the longitude number($float) example: 13.2349029
    """
    print(f"Running Tool: reverse_geocode {type}")
    json_payload = {"type": type}
    if id:
        json_payload["id"] = id
    if lat:
        json_payload["lat"] = lat
    if long:
        json_payload["long"] = long
    url = f"https://{SANDBOX_PREFIX}geocoding.openapi.it/reverse"
    return make_api_call(ctx, "POST", url, json_payload=json_payload)