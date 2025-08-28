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


async def get_company_IT_search(
    ctx: Context,
    companyName: Union[str, None] = None,
    province: Union[str, None] = None,
    skip: Union[int, None] = None,
    limit: int = 10,
    dataEnrichment: Union[str, None] = None,
    sortBy: Union[str, None] = None,
    vatGroup: Union[bool, None] = None,
    legalForm: Union[str, None] = None,
    startDate: Union[str, None] = None,
    endDate: Union[str, None] = None,
    dryRun: Union[int, None] = None,
    lat: Union[float, None] = None,
    long: Union[float, None] = None,
    radius: Union[int, None] = None,
    autocomplete: Union[str, None] = None,
    townCode: Union[str, None] = None,
    atecoCode: Union[str, None] = None,
    cciaa: Union[str, None] = None,
    reaCode: Union[str, None] = None,
    minTurnover: Union[int, None] = None,
    maxTurnover: Union[int, None] = None,
    minEmployees: Union[int, None] = None,
    maxEmployees: Union[int, None] = None,
    sdiCode: Union[str, None] = None,
    legalFormCode: Union[str, None] = None,
    shareHolderTaxCode: Union[str, None] = None,
    activityStatus: Union[str, None] = None,
    pec: Union[str, None] = None,
    creationTimestamp: Union[int, None] = None,
    lastUpdateTimestamp: Union[int, None] = None
) -> Any:
    """Returns a list of italian companies based on the search criteria. Use this tool if you don't know the VAT number of a company.
    Args:
        companyName: The name or part of it of an Italian company (optional).
        province: The province where the company is located to restrict the results (optional).
        skip: The number of records to skip for pagination (optional).
        limit: The maximum number of results to return (default is 10).
        dataEnrichment: Additional data enrichment options for the search (optional). Available values : start, advanced, pec, address, shareholders, name
        sortBy: The field to sort the results by (optional).
        vatGroup: Filter by VAT group status (optional).
        legalForm: Filter by legal form of the company (optional).
        startDate: Filter by the start date of the company (optional).
        endDate: Filter by the end date of the company (optional).
        dryRun: Simulates a request by returning only the number of records found and the price (optional).
        lat: Latitude for geographical search (optional).
        long: Longitude for geographical search (optional).
        radius: Radius in meters for geographical search (optional).
        autocomplete: Search for strings that begin with the specified query (optional).
        townCode: The cadastral code for the town (optional).
        atecoCode: ATECO code for the company (optional).
        cciaa: Chamber of Commerce code (optional).
        reaCode: REA code (optional).
        minTurnover: Minimum turnover value (optional).
        maxTurnover: Maximum turnover value (optional).
        minEmployees: Minimum number of employees (optional).
        maxEmployees: Maximum number of employees (optional).
        sdiCode: SDI code (optional).
        legalFormCode: Legal form code (optional).
        shareHolderTaxCode: Tax code of a company member (optional).
        activityStatus: Status of the company in the Chamber of Commerce (optional), Available values : ATTIVA, CESSATA, REGISTRATA, INATTIVA, SOSPESA, IN_ISCRIZIONE.
        pec: PEC email address of the company (optional).
        creationTimestamp: Filter by creation timestamp (optional).
        lastUpdateTimestamp: Filter by last update timestamp (optional).
    """
    url = f"https://company.openapi.com/IT-search?limit={limit}"

    if companyName:
        if companyName != "*":
            url += f"&companyName={companyName}"
    if province:
        url += f"&province={province}"
    if skip is not None:
        url += f"&skip={skip}"
    if dataEnrichment:
        url += f"&dataEnrichment={dataEnrichment}"
    if sortBy:
        url += f"&sortBy={sortBy}"
    if vatGroup is not None:
        url += f"&vatGroup={str(vatGroup).lower()}"
    if legalForm:
        url += f"&legalForm={legalForm}"
    if startDate:
        url += f"&startDate={startDate}"
    if endDate:
        url += f"&endDate={endDate}"
    if dryRun is not None:
        url += f"&dryRun={dryRun}"
    if lat is not None:
        url += f"&lat={lat}"
    if long is not None:
        url += f"&long={long}"
    if radius is not None:
        url += f"&radius={radius}"
    if autocomplete:
        url += f"&autocomplete={autocomplete}"
    if townCode:
        url += f"&townCode={townCode}"
    if atecoCode:
        url += f"&atecoCode={atecoCode}"
    if cciaa:
        url += f"&cciaa={cciaa}"
    if reaCode:
        url += f"&reaCode={reaCode}"
    if minTurnover is not None:
        url += f"&minTurnover={minTurnover}"
    if maxTurnover is not None:
        url += f"&maxTurnover={maxTurnover}"
    if minEmployees is not None:
        url += f"&minEmployees={minEmployees}"
    if maxEmployees is not None:
        url += f"&maxEmployees={maxEmployees}"
    if sdiCode:
        url += f"&sdiCode={sdiCode}"
    if legalFormCode:
        url += f"&legalFormCode={legalFormCode}"
    if shareHolderTaxCode:
        url += f"&shareHolderTaxCode={shareHolderTaxCode}"
    if activityStatus:
        url += f"&activityStatus={activityStatus}"
    if pec:
        url += f"&pec={pec}"
    if creationTimestamp is not None:
        url += f"&creationTimestamp={creationTimestamp}"
    if lastUpdateTimestamp is not None:
        url += f"&lastUpdateTimestamp={lastUpdateTimestamp}"

    print(url)

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