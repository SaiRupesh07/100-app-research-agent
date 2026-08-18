"""
Verification utilities for the 100-app research pipeline.

Responsibilities:
1. Create a deterministic verification sample.
2. Create human-review records.
3. Preserve actual official evidence URLs where available.
4. Track pending/correct/incorrect/ambiguous human reviews.
5. Calculate verification accuracy.
6. Generate an auditable accuracy report.

Important:
- Human verification is NEVER fabricated.
- New verification records always start as "pending".
- Pending records are excluded from accuracy calculations.
- Accuracy is calculated only from actual human-review results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from config import (
    APPS_PER_CATEGORY_IN_SAMPLE,
    VERIFICATION_SAMPLE_SIZE,
    VERIFICATION_STATUS_VALUES,
)


# ============================================================
# VERIFICATION SAMPLE
# ============================================================

def create_verification_sample(
    apps: List[Dict[str, Any]],
    sample_size: int = VERIFICATION_SAMPLE_SIZE,
    apps_per_category: int = APPS_PER_CATEGORY_IN_SAMPLE,
) -> List[Dict[str, Any]]:
    """
    Create a deterministic representative verification sample.

    Default:
        2 apps per category
        10 categories
        = 20 apps

    The same dataset produces the same sample.
    """

    if not apps:
        return []

    categories: Dict[str, List[Dict[str, Any]]] = {}

    for app in apps:
        category = app.get("category", "Unknown")
        categories.setdefault(category, []).append(app)

    sample: List[Dict[str, Any]] = []

    for category in sorted(categories.keys()):
        category_apps = categories[category]

        for app in category_apps[:apps_per_category]:
            sample.append(app)

            if len(sample) >= sample_size:
                return sample

    return sample[:sample_size]


# ============================================================
# EVIDENCE HELPERS
# ============================================================

def _get_evidence_urls(
    app: Dict[str, Any],
    preferred_types: Optional[List[str]] = None,
) -> List[str]:
    """
    Extract unique evidence URLs from an app.

    If preferred_types is supplied, only those source types
    are considered.
    """

    evidence = app.get("evidence", []) or []

    urls: List[str] = []

    for item in evidence:
        if not isinstance(item, dict):
            continue

        source_type = str(item.get("source_type", ""))
        url = item.get("url")

        if not url:
            continue

        if preferred_types and source_type not in preferred_types:
            continue

        if url not in urls:
            urls.append(url)

    return urls


def _select_source_for_field(
    app: Dict[str, Any],
    field: str,
) -> Optional[str]:
    """
    Select the most relevant official evidence URL for a field.
    """

    priorities = {
        "auth_methods": [
            "official_auth_docs",
            "official_api_docs",
            "official_docs",
        ],
        "api_breadth": [
            "official_api_docs",
            "official_docs",
            "official_github",
        ],
        "access_model": [
            "official_pricing",
            "official_auth_docs",
            "official_docs",
        ],
        "buildability": [
            "official_api_docs",
            "official_auth_docs",
            "official_pricing",
            "official_docs",
            "official_mcp",
            "official_github",
        ],
        "mcp_available": [
            "official_mcp",
            "official_docs",
            "official_github",
        ],
    }

    preferred_types = priorities.get(field, [])

    urls = _get_evidence_urls(app, preferred_types)

    if urls:
        return urls[0]

    # Fallback to any available evidence.
    urls = _get_evidence_urls(app)

    if urls:
        return urls[0]

    return None


# ============================================================
# VERIFICATION RECORD
# ============================================================

def create_verification_record(
    app: Optional[Dict[str, Any]] = None,
    field: str = "",
    agent_value: Any = None,
    official_source: Optional[str] = None,
    app_id: Any = None,
    app_name: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create one human-review verification record.

    Supports both the existing app-based calling style and the
    keyword arguments used by scripts/verify_sample.py.

    Human verification always starts as "pending".
    No human verification result is fabricated.
    """

    # Support the existing app=app calling style.
    if app is None:
        app = {
            "id": app_id,
            "app_name": app_name,
            "category": category,
        }
    else:
        # Do not overwrite values already present in the app record.
        if app_id is not None and app.get("id") is None:
            app["id"] = app_id
        if app_name is not None and app.get("app_name") is None:
            app["app_name"] = app_name
        if category is not None and app.get("category") is None:
            app["category"] = category

    # Use the app's researched value unless explicitly supplied.
    if agent_value is None and field:
        agent_value = app.get(field)

    # Older verify_sample.py versions can pass placeholder text
    # instead of a real URL. In that case, use actual evidence.
    if not official_source or not str(official_source).strip().lower().startswith(
        ("http://", "https://")
    ):
        official_source = _select_source_for_field(app, field)

    return {
        "app_id": app.get("id"),
        "app_name": app.get("app_name"),
        "category": app.get("category"),
        "field": field,
        "agent_value": agent_value,
        "official_source": official_source,
        "human_result": "pending",
        "human_verified_value": None,
        "human_notes": "",
        "verification_date": None,
        "verifier_name": None,
    }


# ============================================================
# HUMAN REVIEW TEMPLATE
# ============================================================

def create_human_review_template(
    verification_sample: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a complete human-review template.

    Four fields are checked for every sampled app:
        - auth_methods
        - access_model
        - api_breadth
        - buildability

    MCP is checked only when MCP is available or MCP evidence
    exists for that app.
    """

    records: List[Dict[str, Any]] = []

    fields = [
        "auth_methods",
        "access_model",
        "api_breadth",
        "buildability",
    ]

    for app in verification_sample:

        for field in fields:
            records.append(
                create_verification_record(
                    app=app,
                    field=field,
                )
            )

        mcp_evidence = _get_evidence_urls(
            app,
            ["official_mcp"],
        )

        if app.get("mcp_available") or mcp_evidence:
            records.append(
                create_verification_record(
                    app=app,
                    field="mcp_available",
                )
            )

    return {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_apps": len(verification_sample),
            "total_checks": len(records),
            "description": (
                "Human review template generated from "
                "first-pass research. All human verification "
                "fields start as pending."
            ),
            "instructions": [
                "For each record, open the official_source URL.",
                "Compare agent_value with official documentation.",
                (
                    "Set human_result to correct, incorrect, "
                    "ambiguous, or pending."
                ),
                (
                    "If incorrect, provide human_verified_value "
                    "with the corrected value."
                ),
                "Add human_notes explaining the decision.",
                (
                    "Set verification_date and verifier_name "
                    "when the check is completed."
                ),
                (
                    "Do not mark a record correct without "
                    "checking the official source."
                ),
            ],
        },
        "template": records,
    }


# ============================================================
# VALUE COMPARISON
# ============================================================

def compare_values(
    agent_value: Any,
    verified_value: Any,
) -> str:
    """
    Compare an agent value with a human-verified value.

    Returns:
        correct
        incorrect
        ambiguous
    """

    if verified_value is None:
        return "ambiguous"

    # Lists such as auth_methods.
    if isinstance(agent_value, list) and isinstance(
        verified_value,
        list,
    ):
        agent_set = {
            str(value).strip().lower()
            for value in agent_value
        }

        verified_set = {
            str(value).strip().lower()
            for value in verified_value
        }

        if agent_set == verified_set:
            return "correct"

        return "incorrect"

    # Boolean fields such as mcp_available.
    if isinstance(agent_value, bool) and isinstance(
        verified_value,
        bool,
    ):
        return (
            "correct"
            if agent_value == verified_value
            else "incorrect"
        )

    agent_normalized = str(agent_value).strip().lower()
    verified_normalized = str(
        verified_value
    ).strip().lower()

    if agent_normalized == verified_normalized:
        return "correct"

    return "incorrect"


# ============================================================
# PROCESS VERIFICATION RESULTS
# ============================================================

def process_verification_results(
    review_template: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate and process a human-review template.

    Pending records remain pending.

    This function does not create human decisions.
    """

    records = review_template.get("template", [])

    processed: List[Dict[str, Any]] = []

    valid_statuses = {
        "correct",
        "incorrect",
        "ambiguous",
        "pending",
        "partial",
        "wrong",
        "unverifiable",
    }

    for record in records:

        result = record.get(
            "human_result",
            "pending",
        )

        if result not in valid_statuses:
            raise ValueError(
                f"Invalid human_result '{result}' for "
                f"{record.get('app_name')} / "
                f"{record.get('field')}"
            )

        processed.append(dict(record))

    completed = [
        record
        for record in processed
        if record.get("human_result")
        in {
            "correct",
            "incorrect",
            "ambiguous",
        }
    ]

    pending = [
        record
        for record in processed
        if record.get("human_result") == "pending"
    ]

    return {
        "metadata": {
            "processed_at": datetime.now().isoformat(),
            "total_checks": len(processed),
            "completed_checks": len(completed),
            "pending_checks": len(pending),
        },
        "records": processed,
    }


# ============================================================
# ACCURACY
# ============================================================

def calculate_accuracy(
    verification_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate accuracy from human verification results.

    IMPORTANT:

    Pending records are excluded from the denominator.

    Ambiguous records receive 0.5 credit.

    Example:

        8 correct
        1 incorrect
        1 ambiguous

        Accuracy =
        (8 + 0.5) / 10 * 100
        = 85%

    If there are no completed reviews, accuracy is None.
    """

    if not verification_results:
        return {
            "total_checks": 0,
            "evaluated_checks": 0,
            "pending": 0,
            "correct": 0,
            "incorrect": 0,
            "ambiguous": 0,
            "accuracy_percent": None,
            "status": "no_data",
        }

    correct = sum(
        1
        for record in verification_results
        if record.get("human_result") == "correct"
    )

    incorrect = sum(
        1
        for record in verification_results
        if record.get("human_result") == "incorrect"
    )

    ambiguous = sum(
        1
        for record in verification_results
        if record.get("human_result") == "ambiguous"
    )

    pending = sum(
        1
        for record in verification_results
        if record.get("human_result") == "pending"
    )

    evaluated = (
        correct
        + incorrect
        + ambiguous
    )

    if evaluated == 0:
        accuracy_percent = None
    else:
        accuracy_percent = (
            (
                correct
                + ambiguous * 0.5
            )
            / evaluated
            * 100
        )

    if evaluated == 0:
        status = "pending"
    elif pending > 0:
        status = "partial"
    else:
        status = "complete"

    return {
        "total_checks": len(verification_results),
        "evaluated_checks": evaluated,
        "pending": pending,
        "correct": correct,
        "incorrect": incorrect,
        "ambiguous": ambiguous,
        "accuracy_percent": (
            round(accuracy_percent, 1)
            if accuracy_percent is not None
            else None
        ),
        "status": status,
    }


# ============================================================
# ACCURACY REPORT
# ============================================================

def generate_accuracy_report(
    first_pass_results: List[Dict[str, Any]],
    verification_results: Optional[
        List[Dict[str, Any]]
    ] = None,
) -> Dict[str, Any]:
    """
    Generate an auditable accuracy report.

    Compatibility:
        The first_pass_results argument is retained because
        the existing project scripts pass it.

    IMPORTANT:
        first_pass_results are NOT treated as human verification.

        Therefore we do NOT calculate fake "first-pass accuracy"
        by looking for human_result fields in first-pass records.

    Actual accuracy comes only from human verification results.
    """

    if not verification_results:
        return {
            "status": "pending",
            "message": (
                "Human verification has not yet been completed."
            ),
            "first_pass": {
                "total_apps": len(first_pass_results),
                "accuracy_percent": None,
                "status": "not_applicable",
            },
            "verification": calculate_accuracy([]),
            "improvement_percent": None,
            "timestamp": datetime.now().isoformat(),
            "methodology": {
                "human_verification_required": True,
                "pending_excluded_from_accuracy": True,
                "ambiguous_weight": 0.5,
            },
        }

    verification_accuracy = calculate_accuracy(
        verification_results
    )

    return {
        "status": verification_accuracy["status"],
        "first_pass": {
            "total_apps": len(first_pass_results),
            "accuracy_percent": None,
            "status": "not_applicable",
            "note": (
                "First-pass records do not contain human "
                "verification labels, so first-pass accuracy "
                "is not fabricated."
            ),
        },
        "verification": verification_accuracy,
        "improvement_percent": None,
        "timestamp": datetime.now().isoformat(),
        "methodology": {
            "human_verification_required": True,
            "pending_excluded_from_accuracy": True,
            "ambiguous_weight": 0.5,
        },
    }