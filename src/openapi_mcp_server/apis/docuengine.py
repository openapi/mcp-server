print("docuengine.py Imported")
from fastmcp import Context
from typing import Any, Dict, List, Optional
from src.openapi_mcp_server.mcp_core import make_api_call, mcp, processPolling, getSessionHash
from src.openapi_mcp_server.memory_store import SANDBOX_PREFIX, set_callback_result, callbackUrl

class DocuEngineHelper:
    """Helper class to manage DocuEngine services and parameter mapping."""
    
    @staticmethod
    def map_params(service_data: Dict[str, Any], input_params: Dict[str, Any]) -> Dict[str, Any]:
        """Maps logical parameter names to API field keys (field0, field1, etc.)."""
        fields = service_data.get("requestStructure", {}).get("fields", {})
        mapped_search = {}
        
        # Create a mapping from logical name to field key
        name_to_key = {}
        for key, field_info in fields.items():
            name_to_key[field_info.get("name")] = key
            
        for name, value in input_params.items():
            if name in name_to_key:
                mapped_search[name_to_key[name]] = value
            else:
                # Fallback to direct key if logical name not found
                mapped_search[name] = value
                
        return mapped_search

@mcp.tool()
async def get_docuengine_services(ctx: Context) -> Any:
    """
    Returns the list of all available DocuEngine services with their required parameters.
    Categories and services include:
    - Camerali: Visura Camerale (Ordinaria/Storica for Capitale, Persone, Individuale), Bilancio (Ottico, XBRL, Riclassificato), Statuto, Soci Attivi, Certificati (Iscrizione, Artigiano, Storico).
    - Catastali: Planimetria Catastale, Estratto Mappa, Elaborato Planimetrico, Registrazione/Proroga/Disdetta Contratti Affitto, Preliminare Compravendita.
    - Patronato: Certificato/Estratto di Matrimonio, Stato di Famiglia, Residenza (Anagrafica, AIRE, Storico), Visura Targa PRA, NASPI (Regular, COM, Anticipata).
    
    Use this to discover the document_id and logical parameter names (e.g., 'reaCode', 'cciaa', 'taxCode', 'ownerName').
    """
    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/documents"
    return make_api_call(ctx, "GET", url)

@mcp.tool()
async def post_docuengine_request(document_id: str, parameters: Dict[str, Any], ctx: Context) -> Any:
    """
    Request any DocuEngine service. 
    The tool handles document_id lookup and parameter mapping automatically.
    
    Available Services:
    
    CHAMBER OF COMMERCE (CAMERALI):
    - Visura Camerale Ordinaria - Societa' Di Capitale (Ordinary Chamber search for corporations)
    - Visura Camerale Ordinaria - Societa' Di Persone (Ordinary Chamber search for partnerships)
    - Visura Camerale Ordinaria - Impresa Individuale (Ordinary Chamber search for sole proprietorships)
    - Visura Camerale Storica - Societa' Di Capitale (Historical Chamber search for corporations)
    - Visura Camerale Storica - Societa' Di Persone (Historical Chamber search for partnerships)
    - Visura Camerale Storica - Impresa Individuale (Historical Chamber search for sole proprietorships)
    - Visura Camerale Inglese (English language Chamber Search)
    - Bilancio Ottico (Optical PDF Balance Sheets)
    - Bilancio XBRL (Structured XBRL Balance Sheets)
    - Bilancio Riclassificato (Reclassified Balance Sheets)
    - Statuto (Company Bylaws)
    - Atto Ottico (Official Deeds or Documents)
    - Soci Attivi Azienda (Active Shareholders/Partners search)
    - Certificato Di Iscrizione (Official Registration Certificate)
    - Certificato Artigiano (Artisan Certificate)
    - Certificato Storico (Historical Registration Certificate)
    
    PATRONATO & CIVIL CERTIFICATES:
    - Certificato Di Matrimonio (Marriage Certificate)
    - Estratto Di Matrimonio (Marriage Extract)
    - Copia Integrale Atto Di Matrimonio (Certified full copy of Marriage Record)
    - Certificato Stato Di Famiglia (Family Status Certificate)
    - Certificato Di Residenza Anagrafica (Residency Certificate)
    - Certificato Di Residenza AIRE (Residency Certificate for Italians living abroad)
    - Certificato Storico Di Residenza (Historical Residency Certificate)
    - Visura Targa PRA (Vehicle License Plate search)
    - NASPI (Unemployment Benefit request - Regular, COM variation, or Advance)
    - ... Con Marca Da Bollo (Residence/Family certificates with Revenue Stamp)
    
    CADASTRAL & REAL ESTATE (CATASTALI):
    - Registrazione Contratti Affitto (Rental/Lease Agreement registration)
    - Proroga Contratto Locazione (Rental/Lease Agreement extension)
    - Disdetta Contratto Di Affitto (Rental/Lease Agreement termination)
    - Registrazione Preliminare Compravendita (Preliminary Sale Agreement registration)
    - Planimetria Catastale (Cadastral Floor Plan)
    - Estratto Mappa Catastale (Cadastral Map Extract)
    - Elaborato Planimetrico (Planimetric Layout)
    
    Args:
        document_id: The exact Italian Name or ID of the service.
        parameters: Logical parameters (mapped internally). Call get_docuengine_services for field details.
    """
    print(f"Running Tool: post_docuengine_request id={document_id}, params={parameters}")
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    request_id = getSessionHash(ctx)
    
    # 1. chiamo il server per la lista dei servizi
    services_response = make_api_call(ctx, "GET", f"https://{SANDBOX_PREFIX}docuengine.openapi.com/documents")
    
    if isinstance(services_response, dict) and "error" in services_response:
        return services_response
    # estraggo la lista dei servizi
    services_list = services_response if isinstance(services_response, list) else []
    # cerco il servizio con l'id passato
    service_data = next((s for s in services_list if s.get("id") == document_id), None)
    
    if not service_data:
        return {"error": "Invalid document_id", "message": f"Service with ID {document_id} not found."}
    # mappo i parametri passati in quelli richiesti dal servizio    
    search_payload = DocuEngineHelper.map_params(service_data, parameters)
  
    custom_context = {
        "request_id": request_id,
        "document_id": document_id,
        "parameters": parameters,
    }
    
    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/requests"
    json_payload = {
        "documentId": document_id,
        "search": search_payload,
        "callback": {
            "url": callbackUrl,
            "data": custom_context,
            "method": "JSON",
            "field": "data",
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    
    response = make_api_call(ctx, "POST", url, json_payload)
    
    # se lo stato è WAIT allora devo fare polling
    if response.get("state") == "WAIT":
        set_callback_result(request_id, response, custom_context)
        response = await processPolling(ctx, request_id, ["DONE", "CANCELLED"], "state")
        
    return response

@mcp.tool()
async def get_docuengine_request_status(request_id: str, ctx: Context) -> Any:
    """Returns the details and status of a specific DocuEngine request."""
    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/requests/{request_id}"
    return make_api_call(ctx, "GET", url)

@mcp.tool()
async def get_docuengine_documents(request_id: str, ctx: Context) -> Any:
    """Returns the download links for the documents produced by a request."""
    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/requests/{request_id}/documents"
    return make_api_call(ctx, "GET", url)
