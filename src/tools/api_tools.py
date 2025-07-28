"""API-related tools for Shopify MCP Server."""
import json

from ..settings import LIQUID_MCP_ENABLED, POLARIS_UNIFIED_ENABLED
from ..types import GettingStartedAPI, LearnShopifyAPIParams
from ..utils.http_client import shopify_dev_fetch
from ..utils.instrumentation import generate_conversation_id, record_usage


async def fetch_getting_started_apis() -> list[GettingStartedAPI]:
    """
    Fetch and validate information about available APIs.
    
    Returns:
        List of available APIs
    """
    try:
        parameters = {}
        if POLARIS_UNIFIED_ENABLED:
            parameters["polaris_unified"] = "true"
        if LIQUID_MCP_ENABLED:
            parameters["liquid_mcp"] = "true"
        
        response_text = await shopify_dev_fetch(
            "/mcp/getting_started_apis",
            parameters=parameters,
        )
        
        print(f"[fetch-getting-started-apis] Response text (truncated): {response_text[:200]}...")
        
        try:
            json_data = json.loads(response_text)
            # Validate data
            apis = []
            for api_data in json_data:
                api = GettingStartedAPI(**api_data)
                apis.append(api)
            return apis
        except Exception as e:
            print(f"[fetch-getting-started-apis] Error parsing JSON response: {e}")
            return []
            
    except Exception as error:
        print(f"[fetch-getting-started-apis] Error fetching API information: {error}")
        return []


async def learn_shopify_api(params: LearnShopifyAPIParams) -> dict:
    """
    Entry point tool that teaches about Shopify APIs and generates conversation ID.
    
    Args:
        params: API parameters
        
    Returns:
        API documentation and conversation ID
    """
    current_conversation_id = params.conversation_id or generate_conversation_id()
    
    try:
        response_text = await shopify_dev_fetch(
            "/mcp/getting_started",
            parameters={"api": params.api},
        )
        
        await record_usage(
            "learn_shopify_api",
            params.model_dump(by_alias=True),
            response_text,
        )
        
        # Include the conversation ID in the response
        text = f"""🔗 **IMPORTANT - SAVE THIS CONVERSATION ID:** {current_conversation_id}
⚠️  CRITICAL: You MUST use this exact conversationId in ALL subsequent Shopify tool calls in this conversation.
🚨 ALL OTHER SHOPIFY TOOLS WILL RETURN ERRORS if you don't provide this conversationId.
---
{response_text}"""
        
        return {
            "content": [{
                "type": "text",
                "text": text,
            }],
            "isError": False,
        }
        
    except Exception as error:
        error_msg = f"Error fetching getting started information for {params.api}: {error}"
        print(error_msg)
        
        return {
            "content": [{
                "type": "text",
                "text": error_msg,
            }],
            "isError": True,
        }