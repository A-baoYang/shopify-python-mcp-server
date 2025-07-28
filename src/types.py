"""Type definitions for Shopify MCP Server."""
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ValidationResult(str, Enum):
    """Validation result status."""
    SUCCESS = "success"
    FAILED = "failed"


class ValidationResponse(BaseModel):
    """Response from validation operations."""
    result: ValidationResult
    result_detail: str = Field(
        description="Explanation of the validation result"
    )


class Schema(BaseModel):
    """GraphQL Schema information."""
    api: str
    id: str
    version: str
    url: str


class API(BaseModel):
    """API information."""
    name: str
    description: str
    schemas: List[Schema] = []


class GraphQLSchemasResponse(BaseModel):
    """Response from GraphQL schemas endpoint."""
    latest_version: str
    apis: List[API]


class GettingStartedAPI(BaseModel):
    """Getting started API information."""
    name: str
    description: str


class SearchDocsParams(BaseModel):
    """Parameters for search_docs_chunks tool."""
    conversation_id: str = Field(
        alias="conversationId",
        description="🔗 REQUIRED: conversationId from learn_shopify_api tool"
    )
    prompt: str = Field(description="The search query for Shopify documentation")
    max_num_results: Optional[int] = Field(
        None,
        description="Maximum number of results to return from the search"
    )


class FetchDocsParams(BaseModel):
    """Parameters for fetch_full_docs tool."""
    conversation_id: str = Field(
        alias="conversationId",
        description="🔗 REQUIRED: conversationId from learn_shopify_api tool"
    )
    paths: List[str] = Field(
        description="The paths to the full documentation pages to read"
    )


class IntrospectGraphQLParams(BaseModel):
    """Parameters for introspect_graphql_schema tool."""
    conversation_id: str = Field(
        alias="conversationId",
        description="🔗 REQUIRED: conversationId from learn_shopify_api tool"
    )
    query: str = Field(
        description="Search term to filter schema elements by name"
    )
    filter: List[Literal["all", "types", "queries", "mutations"]] = Field(
        default=["all"],
        description="Filter results to show specific sections"
    )
    api: str = Field(default="admin", description="The API to introspect")
    version: Optional[str] = Field(None, description="The version of the API")


class ValidateGraphQLParams(BaseModel):
    """Parameters for validate_graphql_codeblocks tool."""
    conversation_id: str = Field(
        alias="conversationId",
        description="🔗 REQUIRED: conversationId from learn_shopify_api tool"
    )
    api: str = Field(default="admin", description="The GraphQL API to validate against")
    version: Optional[str] = Field(None, description="The version of the API")
    codeblocks: List[str] = Field(
        description="Array of GraphQL code blocks to validate"
    )


class LearnShopifyAPIParams(BaseModel):
    """Parameters for learn_shopify_api tool."""
    api: str = Field(description="The Shopify API you are building for")
    conversation_id: Optional[str] = Field(
        None,
        alias="conversationId",
        description="Optional existing conversation UUID"
    )