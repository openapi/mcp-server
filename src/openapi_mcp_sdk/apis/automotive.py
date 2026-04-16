"""Automotive tools."""

# MCP tool names and parameter names intentionally mirror the public API.
# pylint: disable=invalid-name,redefined-builtin

import logging
from typing import Any

from fastmcp import Context  # pylint: disable=import-error

from ..mcp_core import make_api_call, mcp
from ..memory_store import OPENAPI_HOST_PREFIX

logger = logging.getLogger(__name__)
logger.debug("module loaded")


@mcp.tool
async def check_license_plate(countryCode: str, type: str, licensePlate: str, ctx: Context) -> Any:
    """Retrieve vehicle data for a supported country and plate.

    Available combinations:
    IT-car, IT-bike, IT-insurance, FR-car, FR-bike, UK-car, UK-bike,
    UK-mot, PT-car, PT-insurance, ES-car, ES-bike.

    Args:
        countryCode: required, 2 digit country code (IT|FR|UK|DE|PT|ES)
        type: required, type of information needed (car|bike|insurance|mot)
        licensePlate: required, the license plate to check
    """
    url = f"https://{OPENAPI_HOST_PREFIX}automotive.openapi.com/{countryCode}-{type}/{licensePlate}"
    return make_api_call(ctx, "GET", url)
