"""Italian postal code and municipality tools."""

# MCP tool names and parameter names intentionally mirror the public API.
# pylint: disable=invalid-name

import logging
from typing import Any

from fastmcp import Context  # pylint: disable=import-error

from ..mcp_core import make_api_call, mcp
from ..memory_store import OPENAPI_HOST_PREFIX

logger = logging.getLogger(__name__)
logger.debug("module loaded")


@mcp.tool
async def get_IT_regions_list(ctx: Context) -> Any:
    """
    Returns the list of Italian regions
    """
    url = f"https://{OPENAPI_HOST_PREFIX}cap.openapi.it/regioni"
    return make_api_call(ctx, "GET", url)


@mcp.tool
async def get_IT_provinces_list(ctx: Context) -> Any:
    """
     Returns the list of Italian provinces
    """
    url = f"https://{OPENAPI_HOST_PREFIX}cap.openapi.it/province"
    return make_api_call(ctx, "GET", url)


@mcp.tool
async def get_IT_metropolitan_cities_list(ctx: Context) -> Any:
    """
    Returns the list of Italian metropolitan cities
    """
    url = f"https://{OPENAPI_HOST_PREFIX}cap.openapi.it/citta_metropolitane"
    return make_api_call(ctx, "GET", url)


@mcp.tool
async def get_suppressed_italian_municipalities(ctx: Context) -> Any:
    """
    Returns the list of suppressed or merged Italian municipalities
    """
    url = f"https://{OPENAPI_HOST_PREFIX}cap.openapi.it/comuni_soppressi"
    return make_api_call(ctx, "GET", url)


@mcp.tool
async def find_IT_istat_by_comune_name(comune: str, ctx: Context) -> Any:
    """
    Searches for the ISTAT code associated with a given Italian municipality.
    """
    url = f"https://{OPENAPI_HOST_PREFIX}cap.openapi.it/cerca_comuni"
    params = {"comune": comune}
    return make_api_call(ctx, "GET", url, params=params)


@mcp.tool
async def find_IT_municipality_by_istat(istatCode: str, ctx: Context) -> Any:
    """
    Retrieves detailed data about an Italian municipality using the ISTAT code:
    - istat:istatCode
    - comune:municipalityName
    - regione:regionName
    - provincia:provinceName
    - prefisso:telephoneLocalPrefix
    - cod_fisco:cadastralCodeor BelfioreCode of town,
    - superficie:surfaceArea
    - num_residenti:numberOfResidents
    - nome_abitanti:inhabitantsName
    - patrono.nomepatronSaintName,
    - patrono.datapatronSaintDate,
    - municipio:municipalityAddress
    - istat_old:oldIstatCode
    - sigla_provincia:provinceAbbreviation
    - email:emailAddress
    - pec:certifiedEmailAddress
    - tel:telephoneNumber
    - fax:faxNumber
    - frazioni:fractions
    - cap:postalCodes
    """
    url = f"https://{OPENAPI_HOST_PREFIX}cap.openapi.it/comuni_advance/{istatCode}"
    return make_api_call(ctx, "GET", url)


@mcp.tool
async def find_IT_municipalities_by_zip(zip_code: str, ctx: Context) -> Any:
    """
    Retrieves the list of Italian municipalities and their ISTAT code based on the ZIP code.
    """
    url = f"https://{OPENAPI_HOST_PREFIX}cap.openapi.it/cap/{zip_code}"
    return make_api_call(ctx, "GET", url)
