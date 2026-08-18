"""
Research extraction module.

Extracts structured research fields (auth methods, API types, access model, etc.)
from application data. This demonstrates how raw research is converted to
structured format suitable for classification.
"""

from typing import Any, Dict, List


def extract_auth_methods(app_data: Dict[str, Any]) -> List[str]:
    """
    Extract authentication methods from app research.
    
    Args:
        app_data: Raw app data containing auth information
    
    Returns:
        List of authentication method strings (e.g., ["OAuth2", "API Key"])
    """
    # This represents extraction from official auth documentation
    auth = app_data.get("auth_methods", [])
    if isinstance(auth, list):
        return [method.strip() for method in auth if method]
    elif isinstance(auth, str):
        return [auth.strip()] if auth else []
    return []


def extract_api_types(app_data: Dict[str, Any]) -> List[str]:
    """
    Extract API types (REST, GraphQL, etc.) from app research.
    
    Args:
        app_data: Raw app data containing API information
    
    Returns:
        List of API type strings
    """
    # This represents extraction from official API documentation
    apis = app_data.get("api_types", [])
    if isinstance(apis, list):
        return [api.strip() for api in apis if api]
    elif isinstance(apis, str):
        return [apis.strip()] if apis else []
    return []


def extract_api_breadth(app_data: Dict[str, Any]) -> str:
    """
    Extract API breadth classification from app research.
    
    Breadth describes the scope of available API endpoints/actions.
    
    Args:
        app_data: Raw app data containing API breadth information
    
    Returns:
        Breadth classification: "Broad", "Moderate", "Narrow", "Very Narrow", "No Public API", "Unknown"
    """
    breadth = app_data.get("api_breadth", "Unknown")
    valid_values = {"Broad", "Moderate", "Narrow", "Very Narrow", "No Public API", "Unknown"}
    return breadth if breadth in valid_values else "Unknown"


def extract_mcp_info(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract MCP (Model Context Protocol) availability from app research.
    
    Args:
        app_data: Raw app data containing MCP information
    
    Returns:
        Dict with keys: available (bool), type (str), url (str or None)
    """
    return {
        "available": app_data.get("mcp_available", False),
        "type": app_data.get("mcp_type", "No MCP Found"),
        "url": app_data.get("mcp_url"),
    }


def extract_access_model(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract access model information from app research.
    
    Access model describes how a developer obtains credentials and API access.
    
    Args:
        app_data: Raw app data containing access information
    
    Returns:
        Dict with keys: model (str), self_serve (bool), notes (str)
    """
    return {
        "model": app_data.get("access_model", "Unknown"),
        "self_serve": app_data.get("self_serve", None),
        "free_or_trial": app_data.get("free_or_trial"),
        "paid_plan_required": app_data.get("paid_plan_required"),
        "admin_approval_required": app_data.get("admin_approval_required"),
        "partner_or_contact_sales": app_data.get("partner_or_contact_sales"),
        "notes": app_data.get("access_notes", ""),
    }


def extract_evidence(app_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract evidence URLs and supporting documentation from app research.
    
    Each evidence entry should have:
    - claim: What fact it supports
    - url: Direct link to official documentation
    - source_type: Type of source (official_docs, official_api_docs, etc.)
    
    Args:
        app_data: Raw app data containing evidence
    
    Returns:
        List of evidence dicts
    """
    evidence = app_data.get("evidence", [])
    if isinstance(evidence, list):
        return evidence
    return []


def extract_core_fields(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract core identification and description fields.
    
    Args:
        app_data: Raw app data
    
    Returns:
        Dict with core fields: id, app_name, category, description
    """
    return {
        "id": app_data.get("id"),
        "app_name": app_data.get("app_name", ""),
        "category": app_data.get("category", ""),
        "description": app_data.get("description", ""),
    }


def extract_all_fields(app_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all research fields from application data.
    
    This is the main extraction function that coordinates all field extraction.
    
    Args:
        app_data: Raw app data from research
    
    Returns:
        Fully extracted and structured research record
    """
    return {
        **extract_core_fields(app_data),
        "auth_methods": extract_auth_methods(app_data),
        "credential_model": app_data.get("credential_model", "unknown"),
        "access": extract_access_model(app_data),
        "api_types": extract_api_types(app_data),
        "api_breadth": extract_api_breadth(app_data),
        "api_notes": app_data.get("api_notes", ""),
        "mcp": extract_mcp_info(app_data),
        "evidence": extract_evidence(app_data),
    }
