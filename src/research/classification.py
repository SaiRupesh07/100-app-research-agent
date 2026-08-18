"""
Research classification module.

Classifies apps into categories (buildability, access model, etc.) based on
extracted research data. This demonstrates the decision rules that transform
raw research into structured classifications.
"""

from typing import Any, Dict, List, Optional


def classify_buildability(
    api_available: bool,
    api_breadth: str,
    self_serve: bool,
    auth_methods: List[str],
    access_model: str,
    main_blocker: Optional[str] = None,
) -> str:
    """
    Classify buildability of an app based on research findings.

    Decision rules:
    - "Buildable now": public API exists, self-serve credentials,
      sufficient API surface, and no major access friction.
    - "Buildable with friction": API exists but has access friction.
    - "Gated / Not Practical": partnership required, no API,
      or severe restrictions.
    """

    # Normalize values defensively.
    access_model = access_model or ""
    api_breadth = api_breadth or ""
    auth_methods = auth_methods or []

    # ---------------------------------------------------------
    # GATED CHECK — highest priority
    # ---------------------------------------------------------

    if main_blocker in {
        "Partner approval",
        "Contact sales",
        "Private beta",
        "Partner/Contact sales",
    }:
        return "Gated / Not Practical"

    access_lower = access_model.lower()

    if (
        "contact sales" in access_lower
        or "partner" in access_lower
        or "private beta" in access_lower
    ):
        return "Gated / Not Practical"

    if not api_available or api_breadth == "No Public API":
        return "Gated / Not Practical"

    # ---------------------------------------------------------
    # BUILDABLE NOW CHECK
    # ---------------------------------------------------------

    if (
        api_available
        and self_serve is True
        and bool(auth_methods)
        and api_breadth in {"Broad", "Moderate"}
        and "paid" not in access_lower
        and "admin" not in access_lower
    ):
        return "Buildable now"

    # ---------------------------------------------------------
    # BUILDABLE WITH FRICTION
    # ---------------------------------------------------------

    if api_available and bool(auth_methods):
        return "Buildable with friction"

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    return "Gated / Not Practical"


def classify_confidence(
    evidence_count: int,
    evidence_quality: List[str],
) -> str:
    """
    Classify confidence level based on evidence quality and quantity.

    Decision rules:
    - "High": Multiple official sources clearly support the claim.
    - "Medium": Some official documentation or partial evidence.
    - "Low": Mostly third-party sources or weak evidence.
    - "Unknown": Insufficient evidence.
    """

    if evidence_count <= 0:
        return "Unknown"

    evidence_quality = evidence_quality or []

    # Count official sources.
    official_count = sum(
        1
        for quality in evidence_quality
        if "official" in str(quality).lower()
    )

    if evidence_count >= 2 and official_count >= 2:
        return "High"

    if evidence_count >= 1 and official_count >= 1:
        return "Medium"

    if evidence_count >= 2:
        return "Medium"

    return "Low"


def classify_access_model(
    self_serve: bool,
    free_or_trial: bool,
    paid_plan_required: bool,
    admin_approval_required: bool,
    partner_or_contact_sales: bool,
) -> str:
    """
    Classify access model based on access requirements.

    Valid output values:

    - Self-serve Free
    - Self-serve Paid
    - Admin Approval
    - Partner / Contact Sales
    - Private Beta
    - Unknown
    """

    # Highest-friction conditions first.

    if partner_or_contact_sales:
        return "Partner / Contact Sales"

    if admin_approval_required:
        return "Admin Approval"

    if not self_serve:
        return "Unknown"

    if free_or_trial:
        return "Self-serve Free"

    if paid_plan_required:
        return "Self-serve Paid"

    # If access is self-serve but pricing information is unclear,
    # use the closest supported classification.
    return "Self-serve Paid"


def identify_main_blocker(
    api_available: bool,
    api_breadth: str,
    self_serve: bool,
    partner_or_contact_sales: bool,
    admin_approval_required: bool,
    paid_plan_required: bool,
    evidence: List[Dict[str, str]],
) -> Optional[str]:
    """
    Identify the main blocker to buildability, if any.

    Returns:
        Main blocker description or None.
    """

    blockers = []

    evidence = evidence or []

    # ---------------------------------------------------------
    # API blockers
    # ---------------------------------------------------------

    if not api_available:
        blockers.append(("No public API", 10))

    if api_breadth == "No Public API":
        blockers.append(("No public API", 10))

    if api_breadth in {"Very Narrow", "Narrow"}:
        blockers.append(("Limited API surface", 5))

    # ---------------------------------------------------------
    # Access blockers
    # ---------------------------------------------------------

    if partner_or_contact_sales:
        blockers.append(("Partner/Contact sales", 10))

    if admin_approval_required:
        blockers.append(("Admin approval required", 7))

    if paid_plan_required:
        has_free_evidence = any(
            "free" in str(item).lower()
            for item in evidence
        )

        if not has_free_evidence:
            blockers.append(("Paid plan required", 6))

    if not self_serve:
        blockers.append(("Not self-serve", 7))

    # ---------------------------------------------------------
    # Return highest-priority blocker
    # ---------------------------------------------------------

    if not blockers:
        return None

    blockers.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return blockers[0][0]


def generate_buildability_reason(
    buildability: str,
    api_available: bool,
    api_breadth: str,
    self_serve: bool,
    auth_methods: List[str],
    access_model: str,
    main_blocker: Optional[str],
) -> str:
    """
    Generate a human-readable explanation for the buildability
    classification.
    """

    auth_methods = auth_methods or []
    access_model = access_model or ""
    api_breadth = api_breadth or "Unknown"

    # ---------------------------------------------------------
    # BUILDABLE NOW
    # ---------------------------------------------------------

    if buildability == "Buildable now":

        auth_text = (
            ", ".join(auth_methods)
            if auth_methods
            else "documented"
        )

        return (
            f"Public {api_breadth.lower()} API with "
            f"{auth_text} authentication. "
            f"Self-serve access via {access_model}."
        )

    # ---------------------------------------------------------
    # BUILDABLE WITH FRICTION
    # ---------------------------------------------------------

    if buildability == "Buildable with friction":

        reasons = []

        if not self_serve:
            reasons.append(
                "access approval required"
            )

        if "paid" in access_model.lower():
            reasons.append(
                "paid plan may be needed"
            )

        if "admin" in access_model.lower():
            reasons.append(
                "admin approval may be required"
            )

        if api_breadth in {
            "Narrow",
            "Very Narrow",
        }:
            reasons.append(
                "limited API surface"
            )

        reason_text = (
            ", ".join(reasons)
            if reasons
            else "various friction points"
        )

        return (
            f"API available ({api_breadth.lower()}) "
            f"but {reason_text}."
        )

    # ---------------------------------------------------------
    # GATED / NOT PRACTICAL
    # ---------------------------------------------------------

    if main_blocker:
        return f"Gated: {main_blocker}."

    if not api_available:
        return "No meaningful public API available."

    return (
        "Significant barriers to integration "
        "(partnership, complex approval, or "
        "unclear documentation)."
    )