print("visurecamerali.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def get_italian_official_documents_list(vat_or_tax_code:str, ctx: Context) -> Any:
    """
    Recupera un elenco di visure camerali disponibili per una azienda
    fornendo la sua Partita IVA o il suo Codice Fiscale.
    """
    print(f"Esecuzione tool: get_official_documents_list per {vat_or_tax_code}")
    url = f"https://visurecamerali.openapi.it/impresa/{vat_or_tax_code}"
    return make_api_call(ctx, "GET", url)