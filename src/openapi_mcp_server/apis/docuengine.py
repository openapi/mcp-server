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
    Includes categories like:
    - Camerali (Visure ordinarie/storiche, Bilanci Ottici/XBRL, Atti Ottici, Statuto, Certificati di Iscrizione/Storico)
    - Catastali (Planimetria Catastale, Estratto Mappa, Elaborato Planimetrico)
    - Patronato (Certificato di Matrimonio, Registrazione Contratti Affitto)
    
    Use this to discover the document_id and logical parameter names (e.g., 'reaCode', 'cciaa', 'taxCode').
    """
    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/documents"
    return make_api_call(ctx, "GET", url)

@mcp.tool()
async def post_docuengine_request(document_id: str, parameters: Dict[str, Any], ctx: Context) -> Any:
    """
    Generic tool to request any DocuEngine service (Visure, Bilanci, Planimetrie, etc.).
    
    Common examples:
    - Visura Camerale Ordinaria (Società di Capitale): document_id="663df75d19a52195e23e315c", parameters={"reaCode": "123", "cciaa": "RM"}
    - Bilancio XBRL: document_id="667c131a9e6f0e447bc265c1", parameters={"taxCode": "..."}
    - Planimetria Catastale: document_id="68ac694e7a0be68c265a749e", parameters={"province": "RM", "municipality": "Roma", "cadastralSheet": "1", "cadastralParcel": "100", "ownerTaxCode": "...", "ownerName": "..."}
    - Certificato Di Matrimonio: document_id="67cf18292cbb7e30d3d93e17"
    
    Args:
        document_id: The ID of the document service to request (obtain from get_docuengine_services).
        parameters: A dictionary of logical parameters for the service (mapped internally to field0, field1, etc.).
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
