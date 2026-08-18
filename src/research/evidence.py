"""
Evidence collection and management module.

Manages evidence URLs and documentation sources for research claims.
Ensures all claims are backed by official sources where possible.
"""

import re
from typing import Dict, List, Optional


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
    
    Returns:
        True if URL is valid (starts with http:// or https://)
    """
    if not url:
        return False
    return bool(re.match(r"^https?://", url))


def validate_evidence(evidence: Dict[str, str]) -> bool:
    """
    Validate evidence record structure.
    
    Args:
        evidence: Evidence dict with keys: claim, url, source_type
    
    Returns:
        True if evidence record is valid
    """
    required_keys = {"claim", "url", "source_type"}
    if not all(key in evidence for key in required_keys):
        return False
    
    if not validate_url(evidence.get("url", "")):
        return False
    
    if not evidence.get("claim", "").strip():
        return False
    
    return True


def classify_source_type(url: str) -> str:
    """
    Classify evidence source type based on URL.
    
    Args:
        url: Evidence URL
    
    Returns:
        Source type: official_docs, official_api_docs, official_auth_docs,
                     official_pricing, official_github, third_party, etc.
    """
    if not url:
        return "unknown"
    
    url_lower = url.lower()
    
    # Official docs
    if "/docs/" in url_lower or "/documentation/" in url_lower:
        if "api" in url_lower:
            return "official_api_docs"
        elif "auth" in url_lower:
            return "official_auth_docs"
        elif "pricing" in url_lower or "plans" in url_lower:
            return "official_pricing"
        else:
            return "official_docs"
    
    # Official pricing
    if "/pricing" in url_lower or "/plans" in url_lower or "/products" in url_lower:
        return "official_pricing"
    
    # Official API docs
    if "/api" in url_lower or "api.github.com" in url_lower:
        return "official_api_docs"
    
    # Official auth
    if "/oauth" in url_lower or "/auth" in url_lower or "/authentication" in url_lower:
        return "official_auth_docs"
    
    # Official GitHub
    if "github.com" in url_lower:
        return "official_github"
    
    # Official MCP
    if "mcp" in url_lower or "model-context-protocol" in url_lower:
        return "official_mcp"
    
    # Default to third party for non-official sources
    if "developer." not in url_lower and ".com/" in url_lower:
        return "third_party"
    
    return "official_docs"


def score_evidence_quality(evidence_list: List[Dict[str, str]]) -> float:
    """
    Score the quality of evidence backing a claim.
    
    Factors:
    - Count of evidence sources
    - Presence of official sources
    - Presence of API documentation
    - Presence of authentication documentation
    
    Args:
        evidence_list: List of evidence records
    
    Returns:
        Score between 0 and 1
    """
    if not evidence_list:
        return 0.0
    
    score = 0.0
    
    # Base score from count
    count_score = min(len(evidence_list) / 3, 0.3)
    score += count_score
    
    # Official source score
    official_count = sum(
        1 for e in evidence_list
        if e.get("source_type", "").startswith("official")
    )
    if official_count > 0:
        score += 0.4
    
    # API documentation score
    api_docs = sum(
        1 for e in evidence_list
        if "api" in e.get("source_type", "").lower()
    )
    if api_docs > 0:
        score += 0.2
    
    # Authentication documentation score
    auth_docs = sum(
        1 for e in evidence_list
        if "auth" in e.get("source_type", "").lower()
    )
    if auth_docs > 0:
        score += 0.1
    
    return min(score, 1.0)


def merge_evidence_lists(
    existing: List[Dict[str, str]],
    new: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Merge two evidence lists, removing duplicates and keeping highest quality.
    
    Args:
        existing: Current evidence list
        new: New evidence to add
    
    Returns:
        Merged and deduplicated evidence list
    """
    if not existing:
        return new
    if not new:
        return existing
    
    # Keep existing URLs to avoid duplicates
    existing_urls = {e.get("url") for e in existing}
    
    merged = list(existing)
    for evidence in new:
        if evidence.get("url") not in existing_urls:
            merged.append(evidence)
    
    return merged


def get_official_sources(evidence_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filter evidence to only official sources.
    
    Args:
        evidence_list: Full evidence list
    
    Returns:
        Filtered list containing only official sources
    """
    return [
        e for e in evidence_list
        if e.get("source_type", "").startswith("official")
    ]


def evidence_supports_claim(evidence_list: List[Dict[str, str]], claim_keyword: str) -> bool:
    """
    Check if evidence list contains sources supporting a specific claim type.
    
    Args:
        evidence_list: List of evidence records
        claim_keyword: Keyword to search for in claims (e.g., "OAuth", "REST")
    
    Returns:
        True if any evidence mentions the keyword in its claim
    """
    return any(
        claim_keyword.lower() in e.get("claim", "").lower()
        for e in evidence_list
    )
