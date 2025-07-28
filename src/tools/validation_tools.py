"""Validation tools for Shopify MCP Server."""
from ..types import ValidateGraphQLParams, ValidationResponse, ValidationResult
from ..utils.instrumentation import record_usage
from ..validations import has_failed_validation
from ..validations.graphql_schema import validate_graphql_operation


def format_validation_result(
    results: list[ValidationResponse],
    item_name: str = "Items",
) -> str:
    """
    Format validation results into readable markdown.
    
    Args:
        results: List of validation responses
        item_name: Name of items being validated
        
    Returns:
        Formatted markdown string
    """
    response_text = "## Validation Summary\n\n"
    response_text += f"**Overall Status:** {'✅ VALID' if not has_failed_validation(results) else '❌ INVALID'}\n"
    response_text += f"**Total {item_name}:** {len(results)}\n\n"
    
    response_text += "## Detailed Results\n\n"
    for index, check in enumerate(results):
        status_icon = "✅" if check.result == ValidationResult.SUCCESS else "❌"
        response_text += f"### {item_name[:-1]} {index + 1}\n"
        response_text += f"**Status:** {status_icon} {check.result.value.upper()}\n"
        response_text += f"**Details:** {check.result_detail}\n\n"
    
    return response_text


async def validate_graphql_codeblocks(
    params: ValidateGraphQLParams,
    schemas: list,
) -> dict:
    """
    Validate GraphQL code blocks against schema.
    
    Args:
        params: Validation parameters
        schemas: Available schemas
        
    Returns:
        Validation results
    """
    # Validate all code blocks in parallel
    import asyncio
    validation_responses = await asyncio.gather(*[
        validate_graphql_operation(
            codeblock,
            params.api,
            params.version,
            schemas,
        )
        for codeblock in params.codeblocks
    ])
    
    await record_usage(
        "validate_graphql_codeblocks",
        params.model_dump(by_alias=True),
        [r.model_dump() for r in validation_responses],
    )
    
    # Format the response
    response_text = format_validation_result(
        validation_responses,
        "Code Blocks",
    )
    
    return {
        "content": [{
            "type": "text",
            "text": response_text,
        }],
        "isError": has_failed_validation(validation_responses),
    }