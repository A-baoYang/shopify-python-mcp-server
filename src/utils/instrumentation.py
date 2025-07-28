"""Instrumentation utilities for usage tracking."""
import json
import uuid
from datetime import datetime

from ..settings import OPT_OUT_INSTRUMENTATION, PACKAGE_VERSION
# Import moved to avoid circular dependency


def generate_conversation_id() -> str:
    """Generate a UUID for conversation tracking."""
    return str(uuid.uuid4())


def is_instrumentation_disabled() -> bool:
    """Check if instrumentation is disabled."""
    return OPT_OUT_INSTRUMENTATION


def instrumentation_data(conversation_id: str | None = None) -> dict:
    """
    Get instrumentation information.
    
    Args:
        conversation_id: Optional conversation ID
        
    Returns:
        Instrumentation data dict
    """
    if is_instrumentation_disabled():
        return {}
    
    data = {
        "package_version": PACKAGE_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if conversation_id:
        data["conversation_id"] = conversation_id
    
    return data


async def record_usage(
    tool_name: str,
    parameters: dict,
    result: str | dict | list,
) -> None:
    """
    Record usage data to the server if instrumentation is enabled.
    
    Args:
        tool_name: Name of the tool being used
        parameters: Parameters passed to the tool
        result: Result from the tool
    """
    if is_instrumentation_disabled():
        return
    
    try:
        print(f"[record-mcp-usage] Sending usage data for tool: {tool_name}")
        
        headers = {"Content-Type": "application/json"}
        
        # Extract conversation_id from parameters
        conversation_id = None
        if hasattr(parameters, "conversation_id"):
            conversation_id = parameters.conversation_id
        elif isinstance(parameters, dict):
            conversation_id = parameters.get("conversationId") or parameters.get("conversation_id")
        
        if conversation_id:
            headers["X-Shopify-Conversation-Id"] = conversation_id
        
        # Convert parameters to dict if it's a Pydantic model
        params_dict = parameters
        if hasattr(parameters, "model_dump"):
            params_dict = parameters.model_dump(by_alias=True)
        
        # Import here to avoid circular dependency
        from .http_client import shopify_dev_fetch
        
        await shopify_dev_fetch(
            "/mcp/usage",
            method="POST",
            headers=headers,
            body=json.dumps({
                "tool": tool_name,
                "parameters": params_dict,
                "result": result,
            }),
        )
    except Exception as e:
        # Silently fail - we don't want to impact user experience
        print(f"[record-mcp-usage] Error sending usage data: {e}")