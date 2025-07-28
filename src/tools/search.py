"""Search-related tools for Shopify MCP Server."""
import json

from ..settings import LIQUID_MCP_ENABLED, POLARIS_UNIFIED_ENABLED
from ..types import FetchDocsParams, SearchDocsParams
from ..utils.http_client import shopify_dev_fetch
from ..utils.instrumentation import record_usage


async def search_docs_chunks(params: SearchDocsParams) -> dict:
    """
    Search across all shopify.dev documentation to find relevant chunks.
    
    Args:
        params: Search parameters
        
    Returns:
        Search results
    """
    parameters = {}
    
    if params.max_num_results:
        parameters["max_num_results"] = str(params.max_num_results)
    
    if POLARIS_UNIFIED_ENABLED:
        parameters["polaris_unified"] = "true"
    
    try:
        response_text = await shopify_dev_fetch(
            "/mcp/search",
            parameters={
                "query": params.prompt,
                **parameters,
            },
        )
        
        print(f"[search-shopify-docs] Response text (truncated): {response_text[:200]}...")
        
        # Try to parse as JSON, otherwise return raw text
        try:
            json_data = json.loads(response_text)
            formatted_text = json.dumps(json_data, indent=2)
        except json.JSONDecodeError as e:
            print(f"[search-shopify-docs] Error parsing JSON response: {e}")
            formatted_text = response_text
        
        await record_usage("search_docs_chunks", params.model_dump(by_alias=True), formatted_text)
        
        return {
            "content": [{
                "type": "text",
                "text": formatted_text,
            }],
            "isError": False,
        }
        
    except Exception as error:
        error_msg = str(error)
        print(f"[search-shopify-docs] Error searching Shopify documentation: {error}")
        
        return {
            "content": [{
                "type": "text",
                "text": error_msg,
            }],
            "isError": True,
        }


async def fetch_full_docs(params: FetchDocsParams) -> dict:
    """
    Retrieve complete documentation for specific paths from shopify.dev.
    
    Args:
        params: Fetch parameters
        
    Returns:
        Documentation content
    """
    async def fetch_doc_text(path: str) -> dict:
        try:
            appended_path = path if path.endswith(".txt") else f"{path}.txt"
            response_text = await shopify_dev_fetch(appended_path)
            return {
                "text": f"## {path}\n\n{response_text}\n\n",
                "path": path,
                "success": True,
            }
        except Exception as error:
            print(f"Error fetching document at {path}: {error}")
            return {
                "text": f"Error fetching document at {path}: {error}",
                "path": path,
                "success": False,
            }
    
    # Fetch all documents in parallel
    import asyncio
    results = await asyncio.gather(*[fetch_doc_text(path) for path in params.paths])
    
    combined_text = "---\n\n".join(result["text"] for result in results)
    
    await record_usage(
        "fetch_full_docs",
        params.model_dump(by_alias=True),
        combined_text,
    )
    
    return {
        "content": [{
            "type": "text",
            "text": combined_text,
        }],
        "isError": any(not result["success"] for result in results),
    }