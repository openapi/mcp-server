print("company.py importato")
from memory_store import set_callback_result,callbackUrl  # usa sempre il singleton globale
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp, processPolling
from typing import Union



@mcp.tool(
    annotations={
        "title": "Full italian companies data from VAT",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def get_company_IT_full(vat_or_taxCode: str, ctx: Context) -> Any:
    """Returns the complete and detailed profile of an Italian company given a VAT number or Tax Code.  
        - Company Data (Name, VAT Number, Tax Code, CCIAA, and REA)
        - Managers
        - Registered Office and other types of offices
        - Activity Classifications (New ATECO 2025, ATECO history since 2022, NACE, SIC, RAE, and SAE)
        - Corporate Affiliation
        - Exporter / Importer Status
        - Company Size
        - Company Contacts (Email, phone, fax, website, social media)
        - Shareholders and their ownership shares
        - Employees, number, trends, statistics on contract duration and types
        - Regarding shareholders, it is possible to access the list of the top 10 (based on ownership share size) and view their respective ownership shares.
        - Liquidity and profitability
        - Receivables and Payables
        - EBITDA and EBIT
        - Cashflow with a 2-year history
        - Financial fixed assets
        - Production value and costs
        - Financial revenues and expenses
        - Tangible, intangible, and financial assets
        - Net profit/loss
    Use get_company_IT_search to obtain VAT  
    Args:
        vat_or_taxCode: VAT number or Tax Code of an Italian company
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = ctx.request_id
    # Serializza il contesto
    custom_context = {
        "request_id": request_id,
        "vat_or_taxCode": vat_or_taxCode
    }
    url = f"https://company.openapi.com/IT-full/{vat_or_taxCode}"
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    })
    
    #gestione asincrona
    if response.get("state") == "PENDING":
        # Salva subito il risultato parziale per il polling
        set_callback_result(request_id, response, custom_context)
        # avvia un polling ogni secondo su callback_results 
        response = await processPolling(ctx, request_id, ["DONE"])
    return response

@mcp.tool(
    annotations={
        "title": "Advanced italian companies data from VAT",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def get_company_IT_advanced(vat_or_taxCode: str, ctx: Context) -> Any:
    """Returns taxCode, companyName, vatCode,address,activityStatus,reaCode,cciaa,atecoClassification,detailedLegalForm,startDate,registrationDate,endDate,pec,taxCodeCeased,taxCodeCeasedTimestamp,vatGroup,sdiCode,sdiCodeTimestamp,balanceSheets (turnover,employee,networt,staffCost,totalAssets.avgGrossSalary of the last 10 years),shareHolders	
    of an italian company from vatCode or taxCode.
    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    url = f"https://company.openapi.com/IT-advanced/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool(
    annotations={
        "title": "Start italian companies data from VAT",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def get_company_IT_start(vat_or_taxCode: str, ctx: Context) -> Any:
    """Returns taxCode,companyName,vatCode,address,activityStatus,sdiCode,registrationDate of an italian company from vatCode or taxCode.
    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    url = f"https://company.openapi.com/IT-start/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)

@mcp.tool(
    annotations={
        "title": "Search italian companies by name",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)


async def get_company_IT_search(companyName: str, ctx: Context, province: Union[str, None] = None) -> Any:
    """Returns a list of 10 taxCode,companyName,vatCode,address of italian companies from the name
    Use this tool if you don't know the vat number of a company.
    Args:
        companyName: the name or part of it of an italian company
        province: the province where the company is to restrict the results
    """
    url = f"https://company.openapi.com/IT-search?companyName={companyName}&limit=10&dataEnrichment=name"
    if province:
        url += f"&province={province}"
    return make_api_call(ctx, "GET", url)

@mcp.tool(
    annotations={
        "title": "Start worldwide companies data from VAT or company number",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def get_company_WW_top(vat_or_taxCode: str,country_code: str, ctx: Context) -> Any:
    """Returns companyName,nativeCompanyName,companySize,address,gps,activityStatus,incorporationDate,contacts,nace,nationalClassification,balanceSheets data like employees,netWorth,operatingRevenue,equity,totalAssets .
    Args:
        vat_or_taxCode: vatCode or taxCode of a company
        country_code: country code of the company
    """
    url = f"https://company.openapi.com/WW-top/{country_code}/{vat_or_taxCode}"
    return make_api_call(ctx, "GET", url)