import logging
logging.getLogger(__name__).debug("module loaded")
from ..memory_store import set_callback_result, callbackUrl, MCP_BASE_URL, OPENAPI_HOST_PREFIX

logger = logging.getLogger(__name__)
from fastmcp import Context
from typing import Any
from ..mcp_core import make_api_call, mcp, processPolling, getSessionHash
import base64
import zipfile
import io
import json
# TODO: Remove legacy dependency — google-cloud-storage is used to store downloaded document
# files in a GCS bucket. Replace with a storage-agnostic abstraction: write to local filesystem
# (e.g. /tmp or MCP_STORAGE_PATH env var) for dev/portable deployments, and optionally support
# S3-compatible backends (boto3 + MCP_STORAGE_BACKEND env var) for other clouds.
# Remove google-cloud-storage from requirements.txt and pyproject.toml when done.
# Import is deferred to the functions that need it to keep google-cloud-storage optional.
import os
import mimetypes
from datetime import datetime, timedelta, timezone

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
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
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

        # TODO: Remove legacy dependency — bucket name taken from K_SERVICE (Google Cloud Run env var).
        # Replace with MCP_STORAGE_BUCKET env var and abstract the upload behind a storage interface
        # so it can use local disk, S3, GCS, or Azure Blob interchangeably.
        bucket_name = os.getenv("K_SERVICE")
        from google.cloud import storage  # lazy import — optional legacy dependency
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

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

                    # Upload each file to the GCP bucket
                    blob = bucket.blob(file_path)
                    blob.upload_from_string(file_content, content_type=content_type or "application/octet-stream")

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
