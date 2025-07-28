"""Settings for Shopify MCP Server."""
import os
from pathlib import Path

# Base URLs
SHOPIFY_DEV_BASE_URL = (
    "https://shopify-dev.myshopify.io/"
    if os.getenv("DEV") == "true"
    else "https://shopify.dev/"
)

# Feature flags
POLARIS_UNIFIED_ENABLED = os.getenv("POLARIS_UNIFIED") in ["true", "1"]
LIQUID_MCP_ENABLED = os.getenv("LIQUID_MCP") in ["true", "1"]
OPT_OUT_INSTRUMENTATION = os.getenv("OPT_OUT_INSTRUMENTATION") == "true"

# Paths
BASE_DIR = Path(__file__).parent.parent
SCHEMAS_CACHE_DIR = BASE_DIR / "data"

# Package info
PACKAGE_VERSION = "1.0.0"
SERVER_NAME = "shopify-mcp-server"