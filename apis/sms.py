print("exchange.py importato")
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def sendSms(sender: str,body: str,recipientMobileNumeber: str, ctx: Context) -> Any:
    """
    Invia un sms a partire dai seguenti parametri: sender es: "Openapi", body es: "Ciao!", recipientMobileNumeber ovvero il numero di cellulare del destinatario es: "+39-1234567890"
    Il parametro sender è opzionale
    """
    print(f"Esecuzione tool: sendSms da {sender} a {recipientMobileNumeber}")
    url = f"https://ws.messaggisms.com/messages/"
    return make_api_call(ctx, "POST", url, json_payload={
        "sender":sender,
        "body":body,
        "recipients":recipientMobileNumeber
    })