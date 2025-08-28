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
        "title": "Search italian companies by advanced search criteria",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def get_company_IT_search(
    ctx: Context,
    companyName: Union[str, None] = None,
    province: Union[str, None] = None,
    skip: Union[int, None, str] = None,
    limit: Union[int, None, str] = None,
    dataEnrichment: str = "name",
    startDate: Union[str, None] = None,
    endDate: Union[str, None] = None,
    dryRun: Union[int, None, str] = None,
    lat: Union[float, None, str] = None,
    long: Union[float, None, str] = None,
    radius: Union[int, None, str] = None,
    autocomplete: Union[str, None] = None,
    townCode: Union[str, None] = None,
    atecoCode: Union[str, None] = None,
    cciaa: Union[str, None] = None,
    reaCode: Union[str, None] = None,
    minTurnover: Union[int, None, str] = None,
    maxTurnover: Union[int, None, str] = None,
    minEmployees: Union[int, None, str] = None,
    maxEmployees: Union[int, None, str] = None,
    sdiCode: Union[str, None] = None,
    legalFormCode: Union[str, None] = None,
    shareHolderTaxCode: Union[str, None] = None,
    activityStatus: Union[str, None] = None,
    pec: Union[str, None] = None,
    creationTimestamp: Union[int, None, str] = None,
    lastUpdateTimestamp: Union[int, None, str] = None
) -> Any:
    """Returns a list of italian companies based on the search criteria. Use this tool if you don't know the VAT number of a company.
    Args:
        companyName: The name or part of it of an Italian company (optional).
        province: The province where the company is located to restrict the results (optional).
        skip: The number of records to skip for pagination (optional).
        limit: The maximum number of results to return (default is 10, in dryRun default is null). 
        dataEnrichment: Avoid further queries receiving Additional data enrichment options in the results (default is name),  Available values : start, advanced, pec, address, shareholders, name
        legalFormCode: Filter by legalformcode of the company (optional). For Available values use get_company_IT_legal_forms_list
        startDate: Filter by the start date of the company (optional).
        endDate: Filter by the end date of the company (optional).
        dryRun: Simulates a request by returning only the number of records found and the price (optional) Available values :0,1.
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
        shareHolderTaxCode: Tax code of a company member (optional).
        activityStatus: Status of the company in the Chamber of Commerce (optional), Available values : ATTIVA, CESSATA, REGISTRATA, INATTIVA, SOSPESA, IN_ISCRIZIONE.
        pec: PEC email address of the company (optional).
        creationTimestamp: Filter by creation unix timestamp (optional).
        lastUpdateTimestamp: Filter by last update unix timestamp (optional).
    """
    url = f"https://company.openapi.com/IT-search?limit={limit}"

    if companyName:
        if companyName != "*":
            url += f"&companyName={companyName}"
    if province:
        url += f"&province={province}"
    if skip is not None and skip != "null":
        url += f"&skip={skip}"
    if limit is not None and limit != "null":
        url += f"&limit={limit}"
    if dryRun is None and limit is None:
        url += f"&limit=10"
    if dataEnrichment:
        url += f"&dataEnrichment={dataEnrichment}"
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

@mcp.tool
async def get_company_IT_legal_forms_list(ctx: Context) -> Any:
    """Obtain all the updated legalFormsCodes and descriptions available in italy. Usefull with get_company_IT_search.

    "EI"="ENTE IMPRESA","EL"="ENTE SOCIALE","OO"="COOPERATIVA SOCIALE","OS"="SOCIETA' CONSORTILE COOPERATIVA A RESPONSABILITA' LIMITATA","RC"="CONTRATTO DI RETE DOTATO DI SOGGETTIVITA' GIURIDICA","ST"="SOGGETTO ESTERO","AF"="ALTRE FORME","AP"="AZIENDA PROVINCIALE","AS"="SOCIETA' IN ACCOMANDITA SEMPLICE","CO"="CONSORZIO","EE"="ENTE ECCLESIASTICO","FO"="FONDAZIONE","SL"="SOCIETA' CONSORTILE A RESPONSABILITA' LIMITATA","SR"="SOCIETA' A RESPONSABILITA' LIMITATA","SZ"="SOCIETA' NON PREVISTA DALLA LEGISLAZIONE ITALIANA","AL"="AZIENDA SPECIALE","AN"="SOCIETA' CONSORTILE IN NOME COLLETTIVO","CC"="CONSORZIO CON ATTIVITA' ESTERNA","CF"="CONSORZIO FIDI","EC"="ENTE PUBBLICO COMMERCIALE","ED"="ENTE DIRITTO PUBBLICO","EN"="ENTE","OC"="SOCIETA' COOPERATIVA CONSORTILE","PA"="ASSOCIAZIONE IN PARTECIPAZIONE","SF"="SOCIETA' DI FATTO","SO"="SOCIETA' CONSORTILE PER AZIONI","AA"="SOCIETA' IN ACCOMANDITA PER AZIONI","AC"="ASSOCIAZIONE","AI"="ASSOCIAZIONE IMPRESA","AM"="AZIENDA MUNICIPALE","AT"="AZIENDA AUTONOMA STATALE","CR"="CONSORZIO INTERCOMUNALE","ES"="ENTE DI CUI ALLA L.R. 21-12-93 N88","GE"="GRUPPO EUROPEO DI INTERESSE ECONOMICO","IF"="IMPRESA FAMILIARE","LL"="AZIENDA SPECIALE DI CUI AL DLGS 267/2000","RS"="SOCIETA' A RESPONSABILITA' LIMITATA SEMPLIFICATA","SI"="SOCIETA' IRREGOLARE","AR"="AZIENDA REGIONALE","CS"="CONSORZIO SENZA ATTIVITA' ESTERNA","SA"="SOCIETA' ANONIMA","SC"="SOCIETA' COOPERATIVA","SD"="SOCIETA' EUROPEA","SG"="SOCIETA' COOPERATIVA EUROPEA","AE"="SOCIETA' CONSORTILE IN ACCOMANDITA SEMPLICE","EP"="ENTE PUBBLICO ECONOMICO","PF"="PERSONA FISICA","SN"="SOCIETA' IN NOME COLLETTIVO","SP"="SOCIETA' PER AZIONI","XX"="NON PRECISATA","AU"="SOCIETA'  PER AZIONI CON SOCIO UNICO","CE"="COMUNIONE EREDITARIA","CI"="SOCIETA' COOPERATIVA A RESPONSABILITA ILLIMITATA","CL"="SOCIETA' COOPERATIVA A RESPONSABILITA LIMITATA","CN"="SOCIETA' CONSORTILE","CZ"="CONSORZIO DI CUI AL DLGS 267/2000","DI"="IMPRESA INDIVIDUALE","RR"="SOCIETA' A RESPONSABILITA' LIMITATA A CAPITALE RIDOTTO","SE"="SOCIETA' SEMPLICE","SU"="SOCIETA' A RESPONSABILITA' LIMITATA CON UNICO SOCIO","AZ"="AZIENDA SPECIALE REA","CM"="CONSORZIO MUNICIPALE","EM"="ENTE MORALE","ER"="ENTE ECCLESIASTICO CIVILMENTE RICONOSCIUTO","FI"="FONDAZIONE IMPRESA","IC"="ISTITUTO DI CREDITO","ID"="ISTITUTO DI CREDITO DI DIRITTO PUBBLICO","IR"="ISTITUTO RELIGIOSO","MA"="MUTUA ASSICURAZIONE","PC"="PICCOLA SOCIETA' COOPERATIVA","PS"="PICCOLA SOCIETA' COOPERATIVA A RESPONSABILITA' LIMITATA","SM"="SOCIETA' DI MUTUO SOCCORSO","SS"="SOCIETA' COSTITUITA IN BASE A LEGGI DI ALTRO STATO","SV"="SOCIETA' TRA PROFESSIONISTI"

    """
    print(f"Esecuzione tool: get_company_IT_legal_forms_list")
    
    url = f"https://company.openapi.com/IT-legalforms/"
    api_call =  make_api_call(ctx, "GET", url)
    return api_call
