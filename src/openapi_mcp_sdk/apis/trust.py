import logging
logging.getLogger(__name__).debug("module loaded")
from ..memory_store import callback_results, callbackUrl,SANDBOX_PREFIX
from fastmcp import Context
from typing import Any
import asyncio
from ..mcp_core import make_api_call, mcp, processPolling
import json

@mcp.tool(
    annotations={
        "title": "check_email_start",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def check_email_start(email: str, ctx: Context) -> Any:
    """Retrieves detailed information about an email address (spf, dmark, disposability, frauds)  
    Args:
        email: the email to check
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = ctx.request_id
    # Serialize context
    custom_context = {
        "request_id": request_id,
        "email": email
    }
    url = f"https://{SANDBOX_PREFIX}trust.openapi.com/email-start/{email}"
    json_payload = {
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    response = make_api_call(ctx, "POST", url, json_payload=json_payload)
    state = response.get("state")
    
    if state == "PENDING":
        # Store partial result immediately for polling
        callback_results[request_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }

        ctx.report_progress(progress=1, total=100)
        

        # Poll callback_results once per second 
        res = None
        for i in range(100):  # Poll up to 10 seconds
            await asyncio.sleep(1)
            result = callback_results.get(request_id)
            if result:
                res = result.get("data")
                if res:
                    state = res.get("state")
                    if state == "DONE":
                        return res
                
            ctx.report_progress(progress=(i + 1), total=100)
        ctx.report_progress(progress=100, total=100)
    return response

@mcp.tool(
    annotations={
        "title": "check_email_advanced",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def check_email_advanced(email: str, ctx: Context) -> Any:
    """Retrieves advanced information about an email address (spfDetails, dmarcDetails, createdAt, updatedAt, state, message, success, valid, disposable, smtpScore, overallScore, firstName, generic, common, dnsValid, honeypot, deliverability, frequentComplainer, spamTrapScore, catchAll, timedOut, suspect, recentAbuse, fraudScore, suggestedDomain, leaked, sanitizedEmail, identityData, domainAge, firstSeen, riskyTld, spfRecord, dmarcRecord, mxRecords, aRecords)  
    Args:
        email: the email to check
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = ctx.request_id
    # Serialize context
    custom_context = {
        "request_id": request_id,
        "email": email
    }
    url = f"https://{SANDBOX_PREFIX}trust.openapi.com/email-advanced/{email}"
    json_payload = {
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    response = make_api_call(ctx, "POST", url, json_payload=json_payload)
    state = response.get("state")
    
    if state == "PENDING":
        # Store partial result immediately for polling
        callback_results[request_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }

        ctx.report_progress(progress=1, total=100)
        

        # Poll callback_results once per second 
        res = None
        for i in range(100):  # Poll up to 10 seconds
            await asyncio.sleep(1)
            result = callback_results.get(request_id)
            if result:
                res = result.get("data")
                if res:
                    state = res.get("state")
                    if state == "DONE":
                        return res
                
            ctx.report_progress(progress=(i + 1), total=100)
        ctx.report_progress(progress=100, total=100)
    return response

@mcp.tool(
    annotations={
        "title": "check_mobile_start",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def check_mobile_start(mobile: str, ctx: Context) -> Any:
    """Retrieves basic information about a mobile number (requestedNumber, formattedNumber, numberType, isPossible, isValid, regionCode, isValidNumberForRegion, network, originalNetwork, roaming, ported, country, countryPrefix, details)  
    Args:
        mobile: with international prefix es +39
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = ctx.request_id
    # Serialize context
    custom_context = {
        "request_id": request_id,
        "mobile": mobile
    }
    url = f"https://{SANDBOX_PREFIX}trust.openapi.com/mobile-start/{mobile}"
    json_payload = {
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    response = make_api_call(ctx, "POST", url, json_payload=json_payload)
    state = response.get("state")
    
    if state == "PENDING":
        # Store partial result immediately for polling
        callback_results[request_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }

        ctx.report_progress(progress=1, total=100)
        

        # Poll callback_results once per second 
        res = None
        for i in range(100):  # Poll up to 10 seconds
            await asyncio.sleep(1)
            result = callback_results.get(request_id)
            if result:
                res = result.get("data")
                if res:
                    state = res.get("state")
                    if state == "DONE":
                        return res
                
            ctx.report_progress(progress=(i + 1), total=100)
        ctx.report_progress(progress=100, total=100)
    return response

@mcp.tool(
    annotations={
        "title": "check_mobile_advanced",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def check_mobile_advanced(mobile: str, ctx: Context) -> Any:
    """Retrieves advanced information about a mobile number (requestedNumber, formattedNumber, createdAt, updatedAt, state, message, success, valid, active, localFormat, fraudScore, recentAbuse, voip, prepaid, risky, name, identityData, carrier, lineType, country, region, city, accurateCountryCode, zipCode, timezone, dialingCode, doNotCall, leaked, spammer, activeStatus, mcc, mnc, transactionDetails)  
    Args:
        mobile: with international prefix es +39
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = ctx.request_id
    # Serialize context
    custom_context = {
        "request_id": request_id,
        "mobile": mobile
    }
    url = f"https://{SANDBOX_PREFIX}trust.openapi.com/mobile-advanced/{mobile}"
    json_payload = {
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    response = make_api_call(ctx, "POST", url, json_payload=json_payload)
    state = response.get("state")
    
    if state == "PENDING":
        # Store partial result immediately for polling
        callback_results[request_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }

        ctx.report_progress(progress=1, total=100)
        

        # Poll callback_results once per second 
        res = None
        for i in range(100):  # Poll up to 10 seconds
            await asyncio.sleep(1)
            result = callback_results.get(request_id)
            if result:
                res = result.get("data")
                if res:
                    state = res.get("state")
                    if state == "DONE":
                        return res
                
            ctx.report_progress(progress=(i + 1), total=100)
        ctx.report_progress(progress=100, total=100)
    return response

@mcp.tool(
    annotations={
        "title": "check_ip_advanced",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def check_ip_advanced(ip: str, ctx: Context) -> Any:
    """Retrieves advanced information about an ip address (ip, createdAt, updatedAt, state, requestedIp, message, success, proxy, host, isp, organization, asn, countryCode, city, region, timezone, latitude, longitude, zipCode, isCrawler, connectionType, recentAbuse, abuseVelocity, botStatus, frequentAbuser, highRiskAttacks, sharedConnection, dynamicConnection, securityScanner, trustedNetwork, operatingSystem, browser, deviceBrand, deviceModel, transactionDetails, errors, vpn, tor, activeVpn, activeTor, mobile, fraudScore)  
    Args:
        ip: valid ip number
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = ctx.request_id
    # Serialize context
    custom_context = {
        "request_id": request_id,
        "ip": ip
    }
    url = f"https://{SANDBOX_PREFIX}trust.openapi.com/ip-advanced/{ip}"
    json_payload = {
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    response = make_api_call(ctx, "POST", url, json_payload=json_payload)
    state = response.get("state")
    
    if state == "PENDING":
        # Store partial result immediately for polling
        callback_results[request_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }

        ctx.report_progress(progress=1, total=100)
        

        # Poll callback_results once per second 
        res = None
        for i in range(100):  # Poll up to 10 seconds
            await asyncio.sleep(1)
            result = callback_results.get(request_id)
            if result:
                res = result.get("data")
                if res:
                    state = res.get("state")
                    if state == "DONE":
                        return res
                
            ctx.report_progress(progress=(i + 1), total=100)
        ctx.report_progress(progress=100, total=100)
    return response

@mcp.tool(
    annotations={
        "title": "check_url_advanced",
        "readOnlyHint": True,
        "openWorldHint": False,
        "idempotentHint": True
    }
)
async def check_url_advanced(url: str, ctx: Context) -> Any:
    """Retrieves advanced information about an url address (url, createdAt, updatedAt, state, requestedUrl, message, success, unsafe, domain, ipAddress, countryCode, languageCode, server, contentType, statusCode, pageSize, domainRank, dnsValid, parking, pageTitle, shortLinkRedirect, hostedContent, riskyTld, spfRecord, dmarcRecord, mxRecords, nsRecords, aRecords, errors, riskScore, suspicious, phishing, malware, spamming, adult, category, technologies, domainAge, redirected, scannedUrl, finalUrl)  
    Args:
        url: valid url address
    """
    auth_header = ctx.request_context.request.headers.get('authorization') or ctx.request_context.request.headers.get('Authorization')
    
    # Usa un request_id
    request_id = ctx.request_id
    # Serialize context
    custom_context = {
        "request_id": request_id,
        "url": url
    }
    url = f"https://{SANDBOX_PREFIX}trust.openapi.com/url-advanced/{url}"
    json_payload = {
        "callback": {
            "url": callbackUrl,
            "custom": custom_context,
            "headers": {
                "Authorization": auth_header
            }
        }
    }
    response = make_api_call(ctx, "POST", url, json_payload=json_payload)
    state = response.get("state")
    
    if state == "PENDING":
        # Store partial result immediately for polling
        callback_results[request_id] = {
            "progress": "progress",
            "result": response,
            "custom": custom_context
        }

        ctx.report_progress(progress=1, total=100)
        

        # Poll callback_results once per second 
        res = None
        for i in range(100):  # Poll up to 10 seconds
            await asyncio.sleep(1)
            result = callback_results.get(request_id)
            if result:
                res = result.get("data")
                if res:
                    state = res.get("state")
                    if state == "DONE":
                        return res
                
            ctx.report_progress(progress=(i + 1), total=100)
        ctx.report_progress(progress=100, total=100)
    return response

