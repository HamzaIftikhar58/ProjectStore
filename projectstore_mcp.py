#!/usr/bin/env python3
"""
ProjectStore MCP Server
Connects Antigravity IDE to ProjectStore (on cPanel or locally).
Provides catalog auditing, SEO optimization, technical specifications management,
and safe product description editing.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

import httpx
try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

# Initialize MCP Server
mcp = MCPServer("ProjectStoreMCP")

# Configuration
API_URL = os.environ.get("PROJECTSTORE_API_URL", "").rstrip("/")
API_TOKEN = os.environ.get("PROJECTSTORE_API_TOKEN") or os.environ.get("PROJECTSTORE_MCP_TOKEN", "")
TIMEOUT_SECONDS = float(os.environ.get("PROJECTSTORE_TIMEOUT", "30.0"))


def _dispatch_remote(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute action via remote/local HTTP API."""
    url = f"{API_URL}/api/store-mcp/"
    headers = {
        "X-ProjectStore-Token": API_TOKEN,
        "Content-Type": "application/json"
    }
    body = {"action": action, **payload}
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = client.post(url, json=body, headers=headers)
            if resp.status_code == 403:
                return {
                    "status": "error",
                    "message": f"403 Forbidden: Invalid PROJECTSTORE_API_TOKEN. Check token in mcp_config.json and .env."
                }
            if resp.status_code == 404:
                return {
                    "status": "error",
                    "message": f"404 Not Found: '{url}' was not found. Ensure Django route is deployed."
                }
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        return {
            "status": "error",
            "message": f"Could not connect to {API_URL}. If running locally, ensure 'python manage.py runserver' is active, or unset PROJECTSTORE_API_URL to use direct local ORM mode."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"HTTP request failed: {str(e)}"
        }


def _dispatch_local(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute action directly via Django ORM."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ProjectStore.settings")
    import django
    django.setup()
    from Store import mcp_views
    from django.test import RequestFactory

    rf = RequestFactory()
    body = {"action": action, **payload}
    import json
    req = rf.post(
        "/api/store-mcp/",
        data=json.dumps(body),
        content_type="application/json",
        HTTP_X_PROJECTSTORE_TOKEN=API_TOKEN
    )
    response = mcp_views.mcp_endpoint(req)
    return json.loads(response.content.decode("utf-8"))


def call_api(action: str, **kwargs) -> Dict[str, Any]:
    """Route call either to remote HTTP endpoint or local Django ORM."""
    if API_URL:
        return _dispatch_remote(action, kwargs)
    else:
        return _dispatch_local(action, kwargs)


# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool()
def projectstore_health() -> Dict[str, Any]:
    """
    Check connectivity to the ProjectStore database/API and return catalog summary counts.
    Returns:
        Total products, active products, categories, specifications, and variants count.
    """
    res = call_api("health_check")
    mode = f"Remote HTTP ({API_URL})" if API_URL else "Local Direct Django ORM"
    return {"mode": mode, **res}


@mcp.tool()
def projectstore_audit_catalog(category_slug: str = "", limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Audit the ProjectStore product catalog for quality, completeness, and SEO issues.
    Flags:
        - Missing or thin descriptions (< 40 words)
        - Missing short descriptions
        - Missing image alt_text
        - Missing technical specifications
        - Missing package contents (package_includes)
        - Missing meta_description / meta_keywords
        - Active products with 0 stock
    Returns:
        Average health score (0-100%), issue breakdown summary, and a prioritized list of products sorted by lowest health score first.
    """
    return call_api("audit_catalog", category_slug=category_slug, limit=limit, offset=offset)


@mcp.tool()
def projectstore_list_products(
    query: str = "",
    category_slug: str = "",
    is_active: Optional[bool] = None,
    is_project: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Search and filter products in the catalog.
    Args:
        query: Search term for product name or SKU.
        category_slug: Filter by category slug.
        is_active: Filter by active status (True/False/None).
        is_project: Filter by project flag (True for DIY projects, False for retail products).
        limit: Number of products to return (max 100).
        offset: Pagination offset.
    """
    return call_api(
        "list_products",
        query=query,
        category_slug=category_slug,
        is_active=is_active,
        is_project=is_project,
        limit=limit,
        offset=offset
    )


@mcp.tool()
def projectstore_get_product(identifier: str) -> Dict[str, Any]:
    """
    Retrieve full details for a single product by ID, SKU, or slug.
    Returns:
        Complete fields, category, pricing, description, specifications, features,
        variants, gallery images, related products, and health score.
    """
    return call_api("get_product", identifier=identifier)


@mcp.tool()
def projectstore_update_product(
    identifier: str,
    name: Optional[str] = None,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
    meta_description: Optional[str] = None,
    meta_keywords: Optional[str] = None,
    alt_text: Optional[str] = None,
    package_includes: Optional[str] = None,
    guarantee_text: Optional[str] = None,
    youtube_video_url: Optional[str] = None,
    price: Optional[float] = None,
    discount_percentage: Optional[int] = None,
    stock: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_project: Optional[bool] = None,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Safely update a product's content, SEO, pricing, or inventory.
    IMPORTANT: Defaults to dry_run=True so you can preview the before/after diff first.
    Set dry_run=False to commit the changes to the database.
    Args:
        identifier: Product ID, SKU, or slug.
        name: Updated product title.
        short_description: Concise 1-2 sentence overview.
        description: Full detailed HTML/text description.
        meta_description: SEO meta description (recommended <= 160 characters).
        meta_keywords: Comma-separated SEO keywords.
        alt_text: Accessible and SEO-friendly image alt text.
        package_includes: Items in box (one per line, e.g. '1x ESP32 Board\\n1x USB Cable').
        guarantee_text: Custom warranty or quality callout.
        youtube_video_url: Embed/video link.
        price: Base price.
        discount_percentage: Discount percentage (0-100).
        stock: Inventory count.
        is_active: Product visibility on site.
        is_project: Distinguishes DIY engineering project vs ready product.
        dry_run: If True, calculates and returns the diff without saving.
    """
    updates = {}
    if name is not None:
        updates["name"] = name
    if short_description is not None:
        updates["short_description"] = short_description
    if description is not None:
        updates["description"] = description
    if meta_description is not None:
        updates["meta_description"] = meta_description
    if meta_keywords is not None:
        updates["meta_keywords"] = meta_keywords
    if alt_text is not None:
        updates["alt_text"] = alt_text
    if package_includes is not None:
        updates["package_includes"] = package_includes
    if guarantee_text is not None:
        updates["guarantee_text"] = guarantee_text
    if youtube_video_url is not None:
        updates["youtube_video_url"] = youtube_video_url
    if price is not None:
        updates["price"] = price
    if discount_percentage is not None:
        updates["discount_percentage"] = discount_percentage
    if stock is not None:
        updates["stock"] = stock
    if is_active is not None:
        updates["is_active"] = is_active
    if is_project is not None:
        updates["is_project"] = is_project

    return call_api("update_product", identifier=identifier, updates=updates, dry_run=dry_run)


@mcp.tool()
def projectstore_set_specifications(
    identifier: str,
    specifications: List[Dict[str, str]],
    mode: str = "merge",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Add, update, or replace technical specifications (ProductSpecification) for a product.
    Args:
        identifier: Product ID, SKU, or slug.
        specifications: List of dictionaries with 'key' and 'value', e.g.:
            [{"key": "Operating Voltage", "value": "3.3V - 5V"}, {"key": "Microcontroller", "value": "ESP32-WROOM-32"}]
        mode: 'merge' (default, updates matching keys and adds new ones) or 'replace' (clears existing specs and sets these).
        dry_run: If True, previews changes without writing to database.
    """
    return call_api("update_specifications", identifier=identifier, specifications=specifications, mode=mode, dry_run=dry_run)


@mcp.tool()
def projectstore_set_features(
    identifier: str,
    features: List[Dict[str, str]],
    mode: str = "merge",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Add, update, or replace feature highlights (ProductFeature) for a product.
    Args:
        identifier: Product ID, SKU, or slug.
        features: List of dictionaries with 'title' and 'feature', e.g.:
            [{"title": "Dual Core Processing", "feature": "Dual Tensilica LX6 cores clocked up to 240MHz."}]
        mode: 'merge' or 'replace'.
        dry_run: If True, previews changes without writing to database.
    """
    return call_api("update_features", identifier=identifier, features=features, mode=mode, dry_run=dry_run)


if __name__ == "__main__":
    # Run server via FastMCP stdio transport
    mcp.run()
