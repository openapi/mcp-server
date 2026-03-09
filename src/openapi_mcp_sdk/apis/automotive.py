import logging
logging.getLogger(__name__).debug("module loaded")
from fastmcp import Context
from typing import Any
from ..mcp_core import make_api_call, mcp
from ..memory_store import SANDBOX_PREFIX

logger = logging.getLogger(__name__)

@mcp.tool
async def check_license_plate(countryCode: str, type: str, licensePlate: str, ctx: Context) -> Any:
    """Retrieve informations about type=car,bike,insurance,mot from a countryCode=IT,FR,UK,DE,PT,ES and a licensePlate.
    Available Combinations: IT-car, IT-bike, IT-insurance,FR-car,FR-bike,UK-car,UK-bike,UK-mot,PT-car,PT-insurance,ES-car,ES-bike
    Args:
        countryCode: required, 2 digit country code (IT|FR|UK|DE|PT|ES)
        type: required, type of information needed (car|bike|insurance|mot)
        licensePlate: required, the license plate to check
    """
    url = f"https://{SANDBOX_PREFIX}automotive.openapi.com/{countryCode}-{type}/{licensePlate}"
    return make_api_call(ctx, "GET", url)
