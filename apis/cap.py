print("cap.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def elenco_regioni_italiane(ctx: Context) -> Any:
    """
    Ritorna l'elenco delle regioni italiane
    """
    print(f"Esecuzione tool: elenco_regioni_italiane")
    url = "https://cap.openapi.it/regioni"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def elenco_province_italiane(ctx: Context) -> Any:
    """
    Ritorna l'elenco delle province italiane
    """
    print(f"Esecuzione tool: elenco_province_italiane")
    url = "https://cap.openapi.it/province"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def elenco_citta_metropolitane_italiane(ctx: Context) -> Any:
    """
    Ritorna l'elenco citta metropolitane italiane
    """
    print(f"Esecuzione tool: elenco_citta_metropolitane_italiane")
    url = "https://cap.openapi.it/citta_metropolitane"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def elenco_comuni_soppressi_italiani(ctx: Context) -> Any:
    """
    Ritorna l'elenco dei comuni soppressi o accorpati italiani
    """
    print(f"Esecuzione tool: elenco_comuni_soppressi_italiani")
    url = "https://cap.openapi.it/comuni_soppressi"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def find_istat_by_comune_name(comune: str, ctx: Context) -> Any:
    """
    Cerca il codice istat associato a un dato comune italiano.
    """
    print(f"Esecuzione tool: find_istat_by_comune_name per {comune}")
    url = "https://cap.openapi.it/cerca_comuni"
    params = {"comune": comune}
    return make_api_call(ctx, "GET", url, params=params)
@mcp.tool
async def find_comune_by_istat(istatCode: str, ctx: Context) -> Any:
    """
    Recupera dati approfonditi su un comune italiano a partire dal codice istat.
    """
    print(f"Esecuzione tool: find_comune_by_istat per {istatCode}")
    url = f"https://cap.openapi.it/comuni_advance/{istatCode}"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def find_comuni_by_cap(cap: str, ctx: Context) -> Any:
    """
    Recupera l'elenco dei comuni italiani ed il loro codice istat a partire dal CAP (zip code).
    """
    print(f"Esecuzione tool: find_comuni_by_cap per {cap}")
    url = f"https://cap.openapi.it/cap/{cap}"
    return make_api_call(ctx, "GET", url)