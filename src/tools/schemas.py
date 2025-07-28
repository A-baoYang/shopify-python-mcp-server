"""Schema management tools for Shopify MCP Server."""
import json

from ..types import API, GraphQLSchemasResponse, Schema
from ..utils.http_client import shopify_dev_fetch


async def fetch_graphql_schemas() -> dict:
    """
    Fetch available GraphQL schemas from Shopify.
    
    Returns:
        Dict containing schemas, apis, versions, and latestVersion
    """
    try:
        response_text = await shopify_dev_fetch("/mcp/graphql_schemas")
        
        try:
            json_data = json.loads(response_text)
            parsed_response = GraphQLSchemasResponse(**json_data)
        except Exception as parse_error:
            print(f"Error parsing schemas JSON: {parse_error}")
            print(f"Response text: {response_text[:500]}...")
            return {
                "schemas": [],
                "apis": [],
                "versions": [],
                "latest_version": None,
            }
        
        # Extract unique APIs and versions
        apis_map = {}
        versions = set()
        schemas = []
        
        for api in parsed_response.apis:
            apis_map[api.name] = {
                "name": api.name,
                "description": api.description,
            }
            
            for schema in api.schemas:
                versions.add(schema.version)
                schemas.append({
                    "api": api.name,
                    "id": schema.id,
                    "version": schema.version,
                    "url": schema.url,
                })
        
        return {
            "schemas": [Schema(**s) for s in schemas],
            "apis": [API(**api_data) for api_data in apis_map.values()],
            "versions": sorted(list(versions)),
            "latest_version": parsed_response.latest_version,
        }
        
    except Exception as error:
        print(f"Error fetching schemas: {error}")
        return {
            "schemas": [],
            "apis": [],
            "versions": [],
            "latest_version": None,
        }