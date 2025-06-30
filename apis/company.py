print("company.py importato")
from pydantic import BaseModel
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def get_company_IT_full(vat_or_taxCode: str, ctx: Context) -> Any:
    """Restituisce il profilo completo e dettagliato di un'azienda italiana dato Partita IVA o Codice Fiscale."""
    url = f"https://company.openapi.com/IT-full/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool
async def get_company_IT_advanced(vat_or_taxCode: str, ctx: Context) -> Any:
    """Restituisce il profilo avanzato di un'azienda italiana dato Partita IVA o Codice Fiscale."""
    url = f"https://company.openapi.com/IT-advanced/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool
async def get_company_IT_base(vat_or_taxCode: str, ctx: Context) -> Any:
    """Restituisce il profilo base di un'azienda italiana dato Partita IVA o Codice Fiscale."""
    url = f"https://company.openapi.com/IT-start/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool
async def get_company_IT_search(companyName: str, ctx: Context) -> Any:
    """Restituisce un elenco di aziende italiane dato il nome o parte di esso."""
    url = f"https://company.openapi.com/IT-search?companyName={companyName}&limit=10&dataEnrichment=name"
    return make_api_call(ctx, "GET", url)