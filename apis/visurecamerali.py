print("visurecamerali.py importato")
from memory_store import set_callback_result,callbackUrl, BASE_URL  # usa sempre il singleton globale
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp, processPolling, getSessionHash
import base64
import zipfile
import io
import json
from google.cloud import storage
import os
import mimetypes

@mcp.tool
async def get_italian_company_official_documents_list(vat_or_tax_code:str, ctx: Context) -> Any:
    """
    Recupera un elenco di endpoint di visure camerali disponibili per una azienda da usare con il tool get_italian_company_official_document
    fornendo la sua Partita IVA o il suo Codice Fiscale.
    Args:
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    print(f"Esecuzione tool: get_official_documents_list per {vat_or_tax_code}")
    url = f"https://visurecamerali.openapi.it/impresa/{vat_or_tax_code}"
    return make_api_call(ctx, "GET", url)
@mcp.tool
async def get_italian_company_official_document(document_url:str,vat_or_tax_code:str, ctx: Context) -> Any:
    """
    Recupera una visura camerale di una azienda fornendo la sua Partita IVA o il suo Codice Fiscale.
    Args:
        document_url: url of the requested document
        vat_or_taxCode: vatCode or taxCode of an italian company
    """
    print(f"Esecuzione tool: get_italian_company_official_document su {document_url} per {vat_or_tax_code}")
    url = f"https://{document_url}"
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    # Usa un request_id
    request_id = getSessionHash(ctx)
    # Serializza il contesto
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
    print(f"response: {response}")
    state = response.get("stato_richiesta")
    
    if state == "In erogazione":
        # Salva subito il risultato parziale per il polling
        set_callback_result(request_id, response, custom_context)
        # avvia un polling ogni secondo su callback_results 
        response =  await processPolling(ctx, request_id, ["Dati disponibili"],"stato_richiesta")
        print(f"response: {response}")
        # if response.get("data").get("stato_richiesta") == "Visura evasa":
        #     response = make_api_call(ctx, "GET", url+"/"+response.get("data").get("id")+"/allegati")
        #     set_callback_result(request_id, response, custom_context)
    return response
@mcp.tool
async def download_italian_company_official_document(document_id:str,document_url:str, ctx: Context) -> Any:
    """
    Download a document when the "stato_richiesta" of a get_italian_company_official_document call is "Dati disponibili"
    Response is a json containing a file property in base64 of a zip file containing the document selected.
    
    Args:
        document_id: the value id in return of a previous request.
        document_url: the value id in return of a previous request.
    """
    print(f"Esecuzione tool: download_italian_company_official_document ")
    url = f"https://{document_url}/{document_id}/allegati"
    document_response = make_api_call(ctx, "GET", url);
    if "file" in document_response:
        # Decode the base64 file content
        zip_file_content = base64.b64decode(document_response["file"])
        request_id = getSessionHash(ctx)
        
        # Unzip the content
        with zipfile.ZipFile(io.BytesIO(zip_file_content)) as z:
            if len(z.namelist()) == 1:
                # If there is only one file, return it directly
                file_name = z.namelist()[0]

                # Scrive il file in un bucket GCP che si chiama come la variabile K_SERVICE
                bucket_name = os.getenv("K_SERVICE")
                # Il path sarà /status/{request_id}/files/{file_name}
                file_path = f"{request_id}/{file_name}"
                remote_path = f"/status/{request_id}/files/{file_name}"

                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(file_path)

                with z.open(file_name) as f:
                    file_content = f.read()
                    content_type, _ = mimetypes.guess_type(file_name)
                    blob.upload_from_string(file_content, content_type=content_type or "application/octet-stream")

                return {
                    "file_name": file_name,
                    "download_link": BASE_URL+remote_path,
                    "content": base64.b64encode(file_content).decode('utf-8')
                }
            else:
            # If there are multiple files, return them as a JSON object
                files = {}
                for file_name in z.namelist():
                    with z.open(file_name) as f:
                        files[file_name] = base64.b64encode(f.read()).decode('utf-8')
            return files
    return 