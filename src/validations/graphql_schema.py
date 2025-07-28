"""GraphQL schema validation."""
import json

from graphql import build_client_schema, parse, validate

from ..tools.graphql_introspection import get_schema, load_schema_content
from ..types import Schema, ValidationResponse, ValidationResult


async def validate_graphql_operation(
    graphql_code: str,
    api: str,
    version: str,
    schemas: list[Schema],
) -> ValidationResponse:
    """
    Validate a GraphQL operation against the specified schema.
    
    Args:
        graphql_code: The raw GraphQL operation code
        api: The name of the API
        version: The version of the schema
        schemas: Available schemas
        
    Returns:
        ValidationResponse indicating the status
    """
    try:
        trimmed_code = graphql_code.strip()
        if not trimmed_code:
            return ValidationResponse(
                result=ValidationResult.FAILED,
                result_detail="No GraphQL operation found in the provided code.",
            )
        
        # Get the schema
        schema_obj = await get_schema(api, version, schemas)
        schema_content = await load_schema_content(schema_obj)
        schema_json = json.loads(schema_content)
        schema = build_client_schema(schema_json["data"])
        
        # Parse the GraphQL document
        try:
            document = parse(trimmed_code)
        except Exception as parse_error:
            return ValidationResponse(
                result=ValidationResult.FAILED,
                result_detail=f"GraphQL syntax error: {parse_error}",
            )
        
        # Validate against schema
        validation_errors = validate(schema, document)
        if validation_errors:
            error_messages = "; ".join(str(e) for e in validation_errors)
            return ValidationResponse(
                result=ValidationResult.FAILED,
                result_detail=f"GraphQL validation errors: {error_messages}",
            )
        
        # Get operation type
        operation_type = "operation"
        if document.definitions:
            first_def = document.definitions[0]
            if hasattr(first_def, "operation"):
                operation_type = first_def.operation.value
        
        return ValidationResponse(
            result=ValidationResult.SUCCESS,
            result_detail=f"Successfully validated GraphQL {operation_type} against schema.",
        )
        
    except Exception as error:
        return ValidationResponse(
            result=ValidationResult.FAILED,
            result_detail=f"Validation error: {error}",
        )