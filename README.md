# Shopify MCP Server - Python Implementation

This is a Python implementation of the Shopify MCP Server using FastMCP. It provides the same functionality as the original TypeScript version, helping developers interact with Shopify APIs through the Model Context Protocol.

Inspired by [shopify.dev mcp server](https://github.com/Shopify/dev-mcp/tree/main)

## Features

- **Admin GraphQL API** support with schema introspection and validation
- **Documentation search** across shopify.dev
- **GraphQL code validation** to prevent hallucinated fields
- **Conversation tracking** for usage analytics
- **Schema caching** for improved performance

## Installation

```bash
# Clone the repository
git clone https://github.com/A-baoYang/shopify-python-mcp-server
cd shopify-mcp-server

# Install dependencies using uv
uv pip install -r requirements.txt

# Or install with pip
pip install -r requirements.txt
```

## Usage

### Running the server

```bash
# Using uv
uv run python main.py

# Or with Python directly
python main.py
```

### Configuration for Claude Desktop or Cursor

Add the following to your MCP configuration:

```json
{
  "mcpServers": {
    "shopify-mcp-server": {
      "command": "python",
      "args": ["/path/to/shopify-mcp-server/main.py"]
    }
  }
}
```

With uv:

```json
{
  "mcpServers": {
    "shopify-mcp-server": {
      "command": "uv",
      "args": ["run", "python", "/path/to/shopify-mcp-server/main.py"]
    }
  }
}
```

### Environment Variables

- `OPT_OUT_INSTRUMENTATION`: Set to `"true"` to disable usage tracking
- `POLARIS_UNIFIED`: Set to `"true"` or `"1"` to enable Polaris support
- `LIQUID_MCP`: Set to `"true"` or `"1"` to enable Liquid support (experimental)
- `DEV`: Set to `"true"` to use development Shopify URL

## Available Tools

| Tool Name | Description |
|-----------|-------------|
| `learn_shopify_api` | **Start here first** - Teaches about Shopify APIs and generates required conversationId |
| `search_docs_chunks` | Search across shopify.dev documentation |
| `fetch_full_docs` | Retrieve complete documentation pages |
| `introspect_graphql_schema` | Explore GraphQL schemas to find types, queries, and mutations |
| `validate_graphql_codeblocks` | Validate GraphQL code against schema |

## Available Prompts

| Prompt Name | Description |
|-------------|-------------|
| `shopify_admin_graphql` | Help write GraphQL operations for the Shopify Admin API |

## Development

The project structure:

```
shopify-mcp-server/
--- main.py              # Main server entry point
--- src/
|   --- settings.py      # Configuration settings
|   --- types.py         # Type definitions
|   --- tools/           # Tool implementations
|   --- validations/     # Validation logic
|   --- utils/           # Utility functions
--- data/                # Schema cache directory
```
