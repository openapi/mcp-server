import logging
logging.getLogger(__name__).debug("module loaded")

logger = logging.getLogger(__name__)
from fastmcp import Context
import os
from typing import Any, Dict, List, Optional
from ..mcp_core import make_api_call, mcp, processPolling, getSessionHash
from ..memory_store import SANDBOX_PREFIX, set_callback_result, callbackUrl

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
    
    @staticmethod
    def validate_params(service_data: Dict[str, Any], input_params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validates input parameters against service requestStructure.
        Returns (is_valid, error_message).
        """
        import re
        from datetime import datetime
        
        request_structure = service_data.get("requestStructure", {})
        fields = request_structure.get("fields", {})
        validation_rule = request_structure.get("validation")
        
        # Build name to field mapping
        name_to_field = {}
        for field_key, field_info in fields.items():
            name = field_info.get("name")
            if name:
                name_to_field[name] = (field_key, field_info)
        
        # 1. Validate individual field types and options
        for param_name, param_value in input_params.items():
            if param_name not in name_to_field:
                continue  # Allow extra params (they'll be ignored in mapping)
            
            field_key, field_info = name_to_field[param_name]
            field_type = field_info.get("type", "string")
            
            # Type validation
            if field_type == "taxCode" and param_value:
                if not isinstance(param_value, str) or not re.match(r'^[A-Z0-9]{11,16}$', param_value.upper()):
                    return False, f"Field '{param_name}' must be a valid tax code (11-16 alphanumeric characters)"
            
            elif field_type == "email" and param_value:
                if not isinstance(param_value, str) or '@' not in param_value:
                    return False, f"Field '{param_name}' must be a valid email address"
            
            elif field_type == "date" and param_value:
                if isinstance(param_value, str):
                    try:
                        datetime.fromisoformat(param_value.replace('Z', '+00:00'))
                    except:
                        return False, f"Field '{param_name}' must be a valid date (ISO format: YYYY-MM-DD)"
            
            elif field_type == "integer" and param_value is not None:
                try:
                    int(param_value)
                except:
                    return False, f"Field '{param_name}' must be an integer"
            
            elif field_type == "float" and param_value is not None:
                try:
                    float(param_value)
                except:
                    return False, f"Field '{param_name}' must be a number"
            
            # Options validation
            options = field_info.get("options")
            if options and isinstance(options, list) and param_value:
                valid_codes = [o.get("code") for o in options if isinstance(o, dict) and o.get("code")]
                if param_value not in valid_codes:
                    return False, f"Field '{param_name}' must be one of: {', '.join(valid_codes)}"
        
        # 2. Validate required fields and validation logic
        if validation_rule:
            field_presence = {}
            for field_key, field_info in fields.items():
                param_name = field_info.get("name")
                field_presence[field_key] = param_name in input_params and input_params[param_name] not in [None, "", []]
            
            try:
                eval_rule = validation_rule
                for field_key, is_present in field_presence.items():
                    eval_rule = eval_rule.replace(field_key, str(is_present))
                
                if not eval(eval_rule):
                    return False, f"Validation failed: {validation_rule}. Please check required field combinations."
            except Exception:
                pass
        
        return True, None

@mcp.tool()
async def get_docuengine_services(ctx: Context) -> Any:
    """
    Returns the list of all available DocuEngine services with their required parameters.
    """
    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/documents"
    return make_api_call(ctx, "GET", url)

async def _post_docuengine_request(document_id: str, parameters: Dict[str, Any], ctx: Context) -> Any:
    """
    Internal helper to request any DocuEngine service. 
    """
    logger.debug("tool: post_docuengine_request id=%s", document_id)
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    request_id = getSessionHash(ctx)
    
    services_response = make_api_call(ctx, "GET", f"https://{SANDBOX_PREFIX}docuengine.openapi.com/documents")
    
    if isinstance(services_response, dict) and "error" in services_response:
        return services_response
    services_list = services_response if isinstance(services_response, list) else []
    service_data = next((s for s in services_list if s.get("id") == document_id), None)
    
    if not service_data:
        return {"error": "Invalid document_id", "message": f"Service with ID {document_id} not found."}
    
    is_valid, error_message = DocuEngineHelper.validate_params(service_data, parameters)
    if not is_valid:
        return {"error": "Validation Error", "message": error_message}
    
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



_dynamic_tools_initialized = False

def init_dynamic_tools(token: Optional[str] = None) -> bool:
    """Dynamically registers a specialized MCP tool for each DocuEngine service.
    Idempotent: subsequent calls are no-ops and return True if already registered.
    """
    global _dynamic_tools_initialized
    if _dynamic_tools_initialized:
        return True

    import requests
    import re
    import keyword
    from inspect import Parameter, Signature

    logger.info('%-18s "Initializing"', "[JIT]")

    token = (token or os.getenv("OPENAPI_TOKEN", "")).strip()
    if not token:
        logger.warning('%-18s "No token provided"', "[JIT]")
        return False

    url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/documents"

    headers = {"Authorization": f"Bearer {token}"}
    services = []

    try:
        logger.debug('%-18s "Fetching services"', "[JIT]")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            response_data = response.json()
            services = response_data.get("data", []) if isinstance(response_data, dict) else response_data
            if services and isinstance(services, list):
                logger.info('%-18s "Fetched %d services"', "[JIT]", len(services))
        else:
            logger.warning('%-18s "Fetch failed" status=%s', "[JIT]", response.status_code)
    except Exception as e:
        logger.error('%-18s "Fetch error" detail=%s', "[JIT]", e)

    if not services or not isinstance(services, list):
        logger.warning('%-18s "No services found"', "[JIT]")
        return False

    def sanitize_name(name):
        return re.sub(r'[^a-z0-9_]', '_', name.lower())

    def create_tool_fn(s_id, s_name, s_desc, s_fields, t_name):
        params = []
        for field_key, field_info in s_fields.items():
            param_name = field_info.get("name")
            if not param_name or keyword.iskeyword(param_name):
                continue
            
            field_type = field_info.get("type", "string")
            type_map = {"string": str, "taxCode": str, "email": str, "date": str, "integer": int, "float": float}
            param_type = type_map.get(field_type, str)
            
            is_required = field_info.get("required", False)
            default = Parameter.empty if is_required else None
            
            params.append(Parameter(param_name, Parameter.KEYWORD_ONLY, default=default, annotation=param_type if is_required else Optional[param_type]))
        
        params.append(Parameter("ctx", Parameter.KEYWORD_ONLY, annotation=Context))
        
        async def specialized_tool(**kwargs):
            ctx = kwargs.pop("ctx")
            parameters = {k: v for k, v in kwargs.items() if v is not None}
            return await _post_docuengine_request(s_id, parameters, ctx)
        
        specialized_tool.__name__ = t_name
        specialized_tool.__signature__ = Signature(params)
        specialized_tool.__annotations__ = {p.name: p.annotation for p in params}
        specialized_tool.__doc__ = f"Direct tool for DocuEngine service: {s_name} (ID: {s_id}). {s_desc}"
        return specialized_tool

    def create_patch_tool_fn(s_id, s_name, p_name, t_name):
        """Creates a specialized PATCH tool for finalizing a request step."""
        # Define common selection parameters that are typically returned in search results
        params = [
            Parameter("request_id", Parameter.KEYWORD_ONLY, annotation=str),
            Parameter("id", Parameter.KEYWORD_ONLY, annotation=str),
            Parameter("year", Parameter.KEYWORD_ONLY, default=None, annotation=Optional[str]),
            Parameter("ctx", Parameter.KEYWORD_ONLY, annotation=Context)
        ]
        
        async def specialized_patch_tool(request_id: str, id: str, year: Optional[str] = None, ctx: Context = None):
            # Build the selection payload from provided parameters
            selected_option = {"id": id}
            if year is not None:
                selected_option["year"] = year
            
            url = f"https://{SANDBOX_PREFIX}docuengine.openapi.com/requests/{request_id}"
            return make_api_call(ctx, "PATCH", url, selected_option)
            
        specialized_patch_tool.__name__ = t_name
        specialized_patch_tool.__signature__ = Signature(params)
        specialized_patch_tool.__annotations__ = {"request_id": str, "id": str, "year": Optional[str], "ctx": Context}
        specialized_patch_tool.__doc__ = f"""Finalize selection for DocuEngine service: {s_name}.
        
Use this AFTER calling '{p_name}' when it returns a list of options.
Provide the 'id' from your chosen option, and 'year' if applicable (e.g., for balance sheets).
        
Example: If the search returned options with 'id' and 'year' fields, pass those values here."""
        return specialized_patch_tool

    try:
        registered_count = 0
        for service in services:
            try:
                service_id = service.get("id")
                service_name = service.get("name")
                category = service.get("category", "")
                
                # Skip services that are not in the "camerali" category
                if category.lower() != "camerali":
                    continue
                
                if not service_id or not service_name: continue
                
                sanitized = sanitize_name(service_name)
                tool_name = f"docuengine_{sanitized}"
                tool_name = re.sub(r'_+', '_', tool_name).strip('_')
                
                request_structure = service.get("requestStructure", {})
                fields = request_structure.get("fields", {})
                search_price = service.get("searchPrice", 0)
                doc_price = service.get("documentPrice", 0)
                total_price = service.get("totalPrice", 0)
                is_sync = service.get("isSync", False)
                
                # Build enhanced description
                param_desc = f"[{category}] {service_name}"
                
                # Add base description if available
                base_desc = service.get("description", "")
                if base_desc:
                    param_desc += f"\n{base_desc}"
                
                # Add pricing info
                if total_price > 0:
                    param_desc += f"\n💰 Price: €{total_price:.2f}"
                    if search_price > 0:
                        param_desc += f" (search: €{search_price:.2f}, document: €{doc_price:.2f})"
                
                # Add sync/async info
                if is_sync:
                    param_desc += "\n⚡ Synchronous service (instant response)"
                
                # List required parameters
                required_params = [field_info.get("name") for field_key, field_info in fields.items() 
                                 if field_info.get("required", False) and field_info.get("name")]
                if required_params:
                    param_desc += f"\n📋 Required: {', '.join(required_params)}"
                
                # Add search step note
                has_search = service.get("hasSearch", False)
                if has_search:
                    param_desc += f"\n🔍 Two-step process: This returns search results. Use 'patch_{tool_name}' to select and finalize."
                
                # 1. Register primary tool
                tool_fn = create_tool_fn(service_id, service_name, param_desc, fields, tool_name)
                mcp.tool(name=tool_name)(tool_fn)
                registered_count += 1
                
                # 2. If hasSearch, register selection tool with patch_ prefix
                if has_search:
                    patch_tool_name = f"patch_{tool_name}"
                    patch_fn = create_patch_tool_fn(service_id, service_name, tool_name, patch_tool_name)
                    mcp.tool(name=patch_tool_name)(patch_fn)
                    registered_count += 1
                    
            except Exception as e:
                logger.error('%-18s "Register failed" service=%s detail=%s', "[JIT]", service.get('name'), e)

        logger.info('%-18s "Registered %d tools"', "[JIT]", registered_count)
        _dynamic_tools_initialized = registered_count > 0
        return _dynamic_tools_initialized
    except Exception as e:
        logger.error('%-18s "Registration error" detail=%s', "[JIT]", e)
        return False
