"""
Confidence scoring module.

Scores research confidence based on evidence quality and quantity.
Higher confidence reflects stronger evidence backing the research findings.
"""

from typing import Dict, List

from src.research.evidence import score_evidence_quality


def score_confidence_for_field(
    field_name: str,
    evidence_list: List[Dict[str, str]],
    field_value: any,
) -> str:
    """
    Score confidence for a specific research field.
    
    Confidence depends on:
    - Evidence quality (official vs third-party)
    - Evidence quantity
    - Whether the field value is supported by evidence
    - Whether the field is directly or indirectly verified
    
    Args:
        field_name: Name of the field being scored
        evidence_list: List of evidence supporting the field
        field_value: The actual value of the field
    
    Returns:
        Confidence level: "High", "Medium", "Low", or "Unknown"
    """
    if not evidence_list or field_value is None:
        return "Unknown"
    
    # Score evidence quality
    quality_score = score_evidence_quality(evidence_list)
    
    # High confidence: strong evidence from official sources
    if quality_score >= 0.7:
        return "High"
    
    # Medium confidence: decent evidence or some official sources
    if quality_score >= 0.4:
        return "Medium"
    
    # Low confidence: weak evidence
    if quality_score >= 0.1:
        return "Low"
    
    # Unknown: no meaningful evidence
    return "Unknown"


def score_overall_confidence(app_research: Dict[str, any]) -> str:
    """
    Score overall confidence for a complete app research record.
    
    This considers the quality and coverage of evidence across all fields:
    - Authentication documentation
    - API documentation
    - Access model documentation
    - Pricing/access documentation
    - MCP documentation
    
    Args:
        app_research: Complete app research record
    
    Returns:
        Overall confidence level: "High", "Medium", "Low", or "Unknown"
    """
    evidence = app_research.get("evidence", [])
    
    if not evidence:
        return "Unknown"
    
    # Calculate evidence quality
    quality_score = score_evidence_quality(evidence)
    
    # Count how many major aspects are covered
    evidence_claims = [e.get("claim", "").lower() for e in evidence]
    
    covered_aspects = 0
    if any("auth" in claim or "oauth" in claim for claim in evidence_claims):
        covered_aspects += 1
    if any("api" in claim for claim in evidence_claims):
        covered_aspects += 1
    if any("access" in claim or "plan" in claim for claim in evidence_claims):
        covered_aspects += 1
    if any("pricing" in claim or "free" in claim for claim in evidence_claims):
        covered_aspects += 1
    
    # Score based on quality and coverage
    coverage_score = covered_aspects / 4  # 4 major aspects
    combined_score = (quality_score * 0.6) + (coverage_score * 0.4)
    
    if combined_score >= 0.7:
        return "High"
    elif combined_score >= 0.4:
        return "Medium"
    elif combined_score >= 0.1:
        return "Low"
    else:
        return "Unknown"


def explain_confidence(confidence_level: str, evidence_list: List[Dict[str, str]]) -> str:
    """
    Generate human-readable explanation for confidence level.
    
    Args:
        confidence_level: Confidence level string
        evidence_list: Supporting evidence
    
    Returns:
        Human-readable explanation
    """
    if not evidence_list:
        return "No evidence found."
    
    official_count = sum(
        1 for e in evidence_list
        if e.get("source_type", "").startswith("official")
    )
    total_count = len(evidence_list)
    
    if confidence_level == "High":
        return f"Strong evidence from {official_count} official sources ({total_count} total)."
    elif confidence_level == "Medium":
        return f"Partial documentation or mixed sources ({official_count} official, {total_count} total)."
    elif confidence_level == "Low":
        return f"Weak evidence, mostly third-party sources ({total_count} sources)."
    else:
        return "Insufficient evidence found."
