print("automotive.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp
from memory_store import SANDBOX_PREFIX

@mcp.tool
async def check_license_plate(countryCode: str, type: str, licensePlate: str, ctx: Context) -> Any:
    """Retrieve informations about type=car,bike,insurance,mot from a countryCode=IT,FR,UK,DE,PT,ES and a licensePlate.
    Available Combinations: IT-car, IT-bike, IT-insurance,FR-car,FR-bike,UK-car,UK-bike,UK-mot,PT-car,PT-insurance,ES-car,ES-bike
    Args:
        countryCode: required, 2 digit country code (IT|FR|UK|DE|PT|ES)
        type: required, type of information needed (car|bike|insurance|mot)
        licensePlate: required, the license plate to check
    """
    print(f"Esecuzione tool: check_license_plate {licensePlate}")
    
    url = f"https://{SANDBOX_PREFIX}automotive.openapi.com/{countryCode}-{type}/{licensePlate}"
    api_call =  make_api_call(ctx, "GET", url)
    return api_call
