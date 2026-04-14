"""Italian company official document tools."""

import base64
import io
import logging
import mimetypes
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any

from fastmcp import Context  # pylint: disable=import-error

from ..mcp_core import getSessionHash, make_api_call, mcp, processPolling
from ..memory_store import MCP_BASE_URL, OPENAPI_HOST_PREFIX, callbackUrl, set_callback_result
from ..storage_backend import save_file

logger = logging.getLogger(__name__)
logger.debug("module loaded")

@mcp.tool
async def get_italian_company_official_documents_list(vat_or_tax_code:str, ctx: Context) -> Any:
    """
    Returns the list of available official company registry document endpoints for a company,
    identified by its VAT number or tax code. Use with get_italian_company_official_document.
    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    url = f"https://{OPENAPI_HOST_PREFIX}visurecamerali.openapi.it/impresa/{vat_or_tax_code}"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def get_italian_company_official_document(document_url:str,vat_or_tax_code:str, ctx: Context) -> Any:
    """
    Retrieves an official company registry document (visura camerale) for a company
    identified by its VAT number or tax code.
    Args:
        document_url: url of the requested document
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    url = f"https://{document_url}"
    request_id = getSessionHash(ctx)
    custom_context = {
        "request_id": request_id,
        "document_url": document_url,
        "vat_or_tax_code": vat_or_tax_code,
    }
    response = make_api_call(ctx, "POST", url, json_payload={
        "callback": {
            "url": callbackUrl,
            "data": custom_context,
            "method":"JSON",
            "field":"data"
        },
        "cf_piva_id":vat_or_tax_code
    })
    state = response.get("stato_richiesta")

    if state == "In erogazione":
        # Store partial result immediately for polling
        set_callback_result(request_id, response, custom_context)
        # Poll for final state
        response = await processPolling(ctx, request_id, ["Dati disponibili"],"stato_richiesta")
    return response
@mcp.tool
async def download_italian_company_official_document(document_id:str,document_url:str, ctx: Context) -> Any:
    """
    Download a document when the "stato_richiesta" of a get_italian_company_official_document call is "Dati disponibili"
    Response is a json containing one or more files with attributes: file_name, file_size, download_link, content, expire.

    Args:
        document_id: the value id in return of a previous request.
        document_url: the value id in return of a previous request.
    """
    url = f"https://{document_url}/{document_id}/allegati"
    document_response = make_api_call(ctx, "GET", url)
    if "file" in document_response:
        # Decode the base64 file content
        zip_file_content = base64.b64decode(document_response["file"])
        request_id = getSessionHash(ctx)

        # Unzip the content
        with zipfile.ZipFile(io.BytesIO(zip_file_content)) as z:
            files = []
            for file_name in z.namelist():
                with z.open(file_name) as f:
                    file_content = f.read()
                    file_size = len(file_content)
                    content_type, _ = mimetypes.guess_type(file_name)
                    file_path = f"{request_id}/{file_name}"
                    remote_path = f"/status/{request_id}/files/{file_name}"

                    save_file(file_path, file_content, content_type or "application/octet-stream")

                    files.append({
                        "file_name": file_name,
                        "file_size": file_size,
                        "file_type": content_type,
                        "download_link": MCP_BASE_URL + remote_path,
                        "content": base64.b64encode(file_content).decode('utf-8'),
                        "expire": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
                    })
            return files
    return
