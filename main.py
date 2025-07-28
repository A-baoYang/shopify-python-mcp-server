"""Shopify MCP Server - Main entry point."""
import asyncio
import os
from typing import Any

from fastmcp import FastMCP

from src.settings import PACKAGE_VERSION, SERVER_NAME
from src.tools.api_tools import fetch_getting_started_apis, learn_shopify_api
from src.tools.graphql_introspection import introspect_graphql_schema
from src.tools.schemas import fetch_graphql_schemas
from src.tools.search import fetch_full_docs, search_docs_chunks
from src.tools.validation_tools import validate_graphql_codeblocks
from src.types import (
    FetchDocsParams,
    IntrospectGraphQLParams,
    LearnShopifyAPIParams,
    SearchDocsParams,
    ValidateGraphQLParams,
)

# Create server instance
mcp = FastMCP(SERVER_NAME, version=PACKAGE_VERSION)

# Cache for schemas and APIs
_schemas_cache = None
_apis_cache = None
_versions_cache = None
_latest_version_cache = None


async def get_schemas_data():
    """Get cached schemas data or fetch if not cached."""
    global _schemas_cache, _apis_cache, _versions_cache, _latest_version_cache
    
    if _schemas_cache is None:
        data = await fetch_graphql_schemas()
        _schemas_cache = data["schemas"]
        _apis_cache = data["apis"]
        _versions_cache = data["versions"]
        _latest_version_cache = data["latest_version"]
    
    return {
        "schemas": _schemas_cache,
        "apis": _apis_cache,
        "versions": _versions_cache,
        "latest_version": _latest_version_cache,
    }


@mcp.tool
async def search_docs_chunks(
    conversationId: str,
    prompt: str,
    max_num_results: int | None = None,
) -> str:
    """
    Search across all shopify.dev documentation to find relevant chunks matching your query.
    Useful for getting content from many different documentation categories.
    
    Args:
        conversationId: 🔗 REQUIRED: conversationId from learn_shopify_api tool
        prompt: The search query for Shopify documentation
        max_num_results: Maximum number of results to return
        
    Returns:
        Relevant documentation chunks
    """
    params = SearchDocsParams(
        conversationId=conversationId,
        prompt=prompt,
        max_num_results=max_num_results,
    )
    result = await search_docs_chunks(params)
    return result["content"][0]["text"]


@mcp.tool
async def fetch_full_docs(
    conversationId: str,
    paths: list[str],
) -> str:
    """
    Retrieve complete documentation for specific paths from shopify.dev.
    Provides full context without chunking loss.
    
    Args:
        conversationId: 🔗 REQUIRED: conversationId from learn_shopify_api tool
        paths: The paths to the full documentation pages to read
        
    Returns:
        Complete documentation content
    """
    params = FetchDocsParams(
        conversationId=conversationId,
        paths=paths,
    )
    result = await fetch_full_docs(params)
    return result["content"][0]["text"]


@mcp.tool
async def introspect_graphql_schema(
    conversationId: str,
    query: str,
    filter: list[str] | None = None,
    api: str = "admin",
    version: str | None = None,
) -> str:
    """
    Explore and search Shopify GraphQL schemas to find specific types, queries, and mutations.
    Only use this for the Shopify Admin API.
    
    Args:
        conversationId: 🔗 REQUIRED: conversationId from learn_shopify_api tool
        query: Search term to filter schema elements by name
        filter: Filter results - valid values are 'types', 'queries', 'mutations', or 'all'
        api: The API to introspect (default: 'admin')
        version: The version of the API to introspect
        
    Returns:
        Filtered schema elements
    """
    # Get schemas data
    schemas_data = await get_schemas_data()
    
    # Set default version if not provided
    if not version and schemas_data["latest_version"]:
        version = schemas_data["latest_version"]
    
    params = IntrospectGraphQLParams(
        conversationId=conversationId,
        query=query,
        filter=filter or ["all"],
        api=api,
        version=version,
    )
    
    result = await introspect_graphql_schema(params, schemas_data["schemas"])
    return result["content"][0]["text"]


@mcp.tool
async def validate_graphql_codeblocks(
    conversationId: str,
    codeblocks: list[str],
    api: str = "admin",
    version: str | None = None,
) -> str:
    """
    Validate GraphQL code blocks against the Shopify GraphQL schema.
    Ensures they don't contain hallucinated fields or operations.
    
    Args:
        conversationId: 🔗 REQUIRED: conversationId from learn_shopify_api tool
        codeblocks: Array of GraphQL code blocks to validate
        api: The GraphQL API to validate against (default: 'admin')
        version: The version of the API to validate against
        
    Returns:
        Comprehensive validation results
    """
    # Get schemas data
    schemas_data = await get_schemas_data()
    
    # Set default version if not provided
    if not version and schemas_data["latest_version"]:
        version = schemas_data["latest_version"]
    
    params = ValidateGraphQLParams(
        conversationId=conversationId,
        api=api,
        version=version,
        codeblocks=codeblocks,
    )
    
    result = await validate_graphql_codeblocks(params, schemas_data["schemas"])
    return result["content"][0]["text"]


@mcp.tool
async def learn_shopify_api(
    api: str,
    conversationId: str | None = None,
) -> str:
    """
    🚨 MANDATORY FIRST STEP: This tool MUST be called before any other Shopify tools.
    
    Teaches about supported Shopify APIs and generates a conversationId that is REQUIRED
    for all subsequent tool calls.
    
    Args:
        api: The Shopify API you are building for
        conversationId: Optional existing conversation UUID
        
    Returns:
        API documentation and REQUIRED conversationId
    """
    # Get available APIs
    apis = await fetch_getting_started_apis()
    api_names = [a.name for a in apis]
    
    # Validate API name
    if api not in api_names:
        return f"Invalid API '{api}'. Valid options are: {', '.join(api_names)}"
    
    params = LearnShopifyAPIParams(
        api=api,
        conversationId=conversationId,
    )
    
    result = await learn_shopify_api(params)
    return result["content"][0]["text"]


# Prompts
@mcp.prompt("shopify_admin_graphql")
async def shopify_admin_graphql_prompt(query: str) -> list[dict[str, Any]]:
    """
    Help write GraphQL operations for the Shopify Admin API.
    
    Args:
        query: The specific Shopify Admin API question or request
        
    Returns:
        Prompt messages for GraphQL operation creation
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""I need help writing a GraphQL operation for the Shopify Admin API.

Here is my specific request: {query}

Please help me create a complete and correct GraphQL operation (query or mutation) for the Shopify Admin API that accomplishes this task. Include:
1. The full GraphQL operation with proper syntax
2. A brief explanation of what each part of the operation does
3. Any variables needed for the operation
4. How to handle the response data
5. Relevant documentation links if applicable

When formulating your response, make sure to:
- Use the latest Shopify Admin API best practices
- Structure the query efficiently, requesting only necessary fields
- Follow proper naming conventions for the GraphQL operation
- Handle error cases appropriately
- Ensure the query is optimized for performance

The GraphQL operation should be ready to use with minimal modification.""",
            },
        }
    ]


def main():
    """Run the MCP server."""
    # Print server info
    print(f"Starting {SERVER_NAME} v{PACKAGE_VERSION}")
    print(f"Using Shopify Dev URL: {os.getenv('DEV', 'https://shopify.dev/')}")
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
