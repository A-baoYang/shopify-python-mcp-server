"""GraphQL introspection tools for Shopify MCP Server."""
import json
from pathlib import Path

from ..settings import SCHEMAS_CACHE_DIR
from ..types import IntrospectGraphQLParams, Schema
from ..utils.http_client import shopify_dev_fetch
from ..utils.instrumentation import record_usage

# Constants
MAX_FIELDS_TO_SHOW = 50
MAX_RESULTS = 10


async def get_schema(api: str, version: str, schemas: list[Schema]) -> Schema:
    """Find matching schema for given API and version."""
    for schema in schemas:
        if schema.api == api and (not version or schema.version == version):
            return schema
    
    supported_schemas = ", ".join(
        f"{schema.api} ({schema.version})" for schema in schemas
    )
    
    version_str = f' version "{version}"' if version else ""
    raise ValueError(
        f'Schema configuration for API "{api}"{version_str} not found in provided schemas. '
        f'Currently supported schemas: {supported_schemas}'
    )


async def load_schema_content(schema: Schema) -> str:
    """Load schema content from cache or API."""
    # Ensure cache directory exists
    SCHEMAS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    cache_file_path = SCHEMAS_CACHE_DIR / f"{schema.id}.json"
    
    try:
        # Check if we have a cached version
        if cache_file_path.exists():
            print(f"[introspect-graphql-schema] Reading cached schema from {cache_file_path}")
            return cache_file_path.read_text()
        
        print(f"[introspect-graphql-schema] Fetching schema from API for {schema.id}")
        
        schema_content = await shopify_dev_fetch(
            schema.url,
            headers={"Accept-Encoding": "gzip"},
        )
        
        # Cache the schema content
        cache_file_path.write_text(schema_content)
        print(f"[introspect-graphql-schema] Cached schema to {cache_file_path}")
        
        return schema_content
        
    except Exception as error:
        print(f"[introspect-graphql-schema] Error loading schema: {error}")
        raise


def format_type(type_obj: dict) -> str:
    """Format GraphQL type as string."""
    if not type_obj:
        return "null"
    
    if type_obj.get("kind") == "NON_NULL":
        return f"{format_type(type_obj.get('ofType'))}!"
    elif type_obj.get("kind") == "LIST":
        return f"[{format_type(type_obj.get('ofType'))}]"
    else:
        return type_obj.get("name", "")


def format_arg(arg: dict) -> str:
    """Format GraphQL argument."""
    result = f"{arg['name']}: {format_type(arg['type'])}"
    if arg.get("defaultValue") is not None:
        result += f" = {arg['defaultValue']}"
    return result


def format_field(field: dict) -> str:
    """Format GraphQL field."""
    result = f"  {field['name']}"
    
    # Add arguments if present
    if field.get("args"):
        result += f"({', '.join(format_arg(arg) for arg in field['args'])})"
    
    result += f": {format_type(field['type'])}"
    
    # Add deprecation info if present
    if field.get("isDeprecated"):
        result += " @deprecated"
        if field.get("deprecationReason"):
            result += f" ({field['deprecationReason']})"
    
    return result


def format_schema_type(item: dict) -> str:
    """Format GraphQL schema type."""
    result = f"{item['kind']} {item['name']}"
    
    if item.get("description"):
        # Truncate description if too long
        desc = item["description"].replace("\n", " ")
        if len(desc) > 150:
            desc = desc[:150] + "..."
        result += f"\n  Description: {desc}"
    
    # Add interfaces if present
    if item.get("interfaces"):
        result += f"\n  Implements: {', '.join(i['name'] for i in item['interfaces'])}"
    
    # For INPUT_OBJECT types, use inputFields instead of fields
    if item["kind"] == "INPUT_OBJECT" and item.get("inputFields"):
        result += "\n  Input Fields:"
        fields_to_show = item["inputFields"][:MAX_FIELDS_TO_SHOW]
        for field in fields_to_show:
            result += f"\n{format_field(field)}"
        if len(item["inputFields"]) > MAX_FIELDS_TO_SHOW:
            result += f"\n  ... and {len(item['inputFields']) - MAX_FIELDS_TO_SHOW} more input fields"
    # For regular object types, use fields
    elif item.get("fields"):
        result += "\n  Fields:"
        fields_to_show = item["fields"][:MAX_FIELDS_TO_SHOW]
        for field in fields_to_show:
            result += f"\n{format_field(field)}"
        if len(item["fields"]) > MAX_FIELDS_TO_SHOW:
            result += f"\n  ... and {len(item['fields']) - MAX_FIELDS_TO_SHOW} more fields"
    
    return result


def format_graphql_operation(query: dict) -> str:
    """Format GraphQL operation (query/mutation)."""
    result = f"{query['name']}"
    
    if query.get("description"):
        desc = query["description"].replace("\n", " ")
        if len(desc) > 100:
            desc = desc[:100] + "..."
        result += f"\n  Description: {desc}"
    
    # Add arguments if present
    if query.get("args"):
        result += "\n  Arguments:"
        for arg in query["args"]:
            result += f"\n    {format_arg(arg)}"
    
    # Add return type
    result += f"\n  Returns: {format_type(query['type'])}"
    
    return result


def filter_and_sort_items(items: list, search_term: str, max_items: int) -> dict:
    """Filter, sort, and truncate schema items."""
    # Filter items based on search term
    filtered = [
        item for item in items
        if search_term in item.get("name", "").lower()
    ]
    
    # Sort filtered items by name length (shorter names first)
    filtered.sort(key=lambda x: len(x.get("name", "")))
    
    # Return truncation info and limited items
    return {
        "was_truncated": len(filtered) > max_items,
        "items": filtered[:max_items],
    }


async def introspect_graphql_schema(
    params: IntrospectGraphQLParams,
    schemas: list[Schema],
) -> dict:
    """
    Introspect and return the portion of the Shopify GraphQL schema.
    
    Args:
        params: Introspection parameters
        schemas: Available schemas
        
    Returns:
        Introspection results
    """
    try:
        # Get the schema based on API and version
        schema = await get_schema(params.api, params.version, schemas)
        
        # Load the schema content
        schema_content = await load_schema_content(schema)
        
        # Parse the schema content
        schema_json = json.loads(schema_content)
        
        # If a query is provided, filter the schema
        response_text = ""
        
        if params.query.strip():
            # Normalize search term
            normalized_query = params.query.strip()
            if normalized_query.endswith("s"):
                normalized_query = normalized_query[:-1]
            normalized_query = normalized_query.replace(" ", "")
            
            print(f"[introspect-graphql-schema] Filtering schema with query: {params.query} (normalized: {normalized_query})")
            
            search_term = normalized_query.lower()
            
            # Process types
            types_result = {"was_truncated": False, "items": []}
            matching_queries = []
            matching_mutations = []
            
            if schema_json.get("data", {}).get("__schema", {}).get("types"):
                types = schema_json["data"]["__schema"]["types"]
                
                # Process types
                types_result = filter_and_sort_items(types, search_term, MAX_RESULTS)
                
                # Find Query and Mutation types
                query_type = next((t for t in types if t["name"] == "QueryRoot"), None)
                mutation_type = next((t for t in types if t["name"] == "Mutation"), None)
                
                # Process queries if available
                if query_type and query_type.get("fields") and (
                    "all" in params.filter or "queries" in params.filter
                ):
                    queries_result = filter_and_sort_items(
                        query_type["fields"], search_term, MAX_RESULTS
                    )
                    matching_queries = queries_result["items"]
                
                # Process mutations if available
                if mutation_type and mutation_type.get("fields") and (
                    "all" in params.filter or "mutations" in params.filter
                ):
                    mutations_result = filter_and_sort_items(
                        mutation_type["fields"], search_term, MAX_RESULTS
                    )
                    matching_mutations = mutations_result["items"]
            
            # Build response text
            if "all" in params.filter or "types" in params.filter:
                response_text += "## Matching GraphQL Types:\n"
                if types_result["was_truncated"]:
                    response_text += "(Results limited to 10 items. Refine your search for more specific results.)\n\n"
                
                if types_result["items"]:
                    response_text += "\n\n".join(
                        format_schema_type(t) for t in types_result["items"]
                    ) + "\n\n"
                else:
                    response_text += "No matching types found.\n\n"
            
            # Add queries section
            if "all" in params.filter or "queries" in params.filter:
                response_text += "## Matching GraphQL Queries:\n"
                if len(matching_queries) == MAX_RESULTS:
                    response_text += "(Results limited to 10 items. Refine your search for more specific results.)\n\n"
                
                if matching_queries:
                    response_text += "\n\n".join(
                        format_graphql_operation(q) for q in matching_queries
                    ) + "\n\n"
                else:
                    response_text += "No matching queries found.\n\n"
            
            # Add mutations section
            if "all" in params.filter or "mutations" in params.filter:
                response_text += "## Matching GraphQL Mutations:\n"
                if len(matching_mutations) == MAX_RESULTS:
                    response_text += "(Results limited to 10 items. Refine your search for more specific results.)\n\n"
                
                if matching_mutations:
                    response_text += "\n\n".join(
                        format_graphql_operation(m) for m in matching_mutations
                    )
                else:
                    response_text += "No matching mutations found."
        
        else:
            response_text = "Please provide a search query to filter schema elements."
        
        await record_usage(
            "introspect_graphql_schema",
            params.model_dump(by_alias=True),
            response_text,
        )
        
        return {
            "content": [{
                "type": "text",
                "text": response_text,
            }],
            "isError": False,
        }
        
    except Exception as error:
        error_msg = f"Error processing Shopify GraphQL schema: {error}"
        print(f"[introspect-graphql-schema] {error_msg}")
        
        return {
            "content": [{
                "type": "text",
                "text": error_msg,
            }],
            "isError": True,
        }