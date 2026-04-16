"""SMS tools."""

import logging
from typing import Any

from fastmcp import Context  # pylint: disable=import-error

from ..mcp_core import make_api_call, mcp
from ..memory_store import OPENAPI_HOST_PREFIX

logger = logging.getLogger(__name__)
logger.debug("module loaded")


@mcp.tool
async def send_sms(sender: str, body: str, mobile: str, ctx: Context) -> Any:
    """
    Send an SMS to a mobile number using minus sign to separate international prefix from the number
    Args:
        sender: optional, can be a 11 char long string
        body: the body of the message string
        mobile: the recipient mobile number. Eg.:"+39-1234567890"
    """
    # Ensure the mobile number has a '-' between the international prefix and the number
    if mobile.startswith("+") and "-" not in mobile:
        return {
            "success": False,
            "error": 111,
            "message": ("please use minus simbol to separate international prefix and the number"),
        }

    url = f"https://{OPENAPI_HOST_PREFIX}ws.messaggisms.com/messages/"
    return make_api_call(ctx, "POST", url, json_payload={"sender": sender, "body": body, "recipients": mobile})
