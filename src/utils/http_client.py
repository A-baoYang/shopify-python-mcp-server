"""HTTP client utilities for Shopify MCP Server."""
from datetime import datetime

import httpx

from ..settings import OPT_OUT_INSTRUMENTATION, PACKAGE_VERSION, SHOPIFY_DEV_BASE_URL


async def shopify_dev_fetch(
    uri: str,
    parameters: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    body: str | None = None,
) -> str:
    """
    Make requests to the Shopify dev server.
    
    Args:
        uri: The API path or full URL
        parameters: Query parameters
        headers: Additional headers
        method: HTTP method
        body: Request body
        
    Returns:
        Response text
        
    Raises:
        httpx.HTTPStatusError: If response is not ok
    """
    # Construct URL
    if uri.startswith("http://") or uri.startswith("https://"):
        url = uri
    else:
        url = SHOPIFY_DEV_BASE_URL.rstrip("/") + "/" + uri.lstrip("/")
    
    # Prepare headers
    request_headers = {
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "X-Shopify-Surface": "mcp",
        "X-Shopify-MCP-Version": PACKAGE_VERSION if not OPT_OUT_INSTRUMENTATION else "",
        "X-Shopify-Timestamp": datetime.utcnow().isoformat() if not OPT_OUT_INSTRUMENTATION else "",
    }
    if headers:
        request_headers.update(headers)
    
    # Log request
    print(f"[shopify-dev-fetch] Making {method} request to: {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            params=parameters,
            headers=request_headers,
            content=body,
        )
        
        print(f"[shopify-dev-fetch] Response status: {response.status_code}")
        
        response.raise_for_status()
        return response.text