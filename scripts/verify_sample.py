#!/usr/bin/env python3
"""
Create and process the human-verification sample.

The verification template is deliberately honest:
- It uses the existing 20-app sample.
- It pulls the researched app record from first_pass_research.json.
- It selects a real official evidence URL for each field whenever one exists.
- It never fabricates a human verification result.
- Every newly generated review starts with human_result="pending".

Usage:
    python scripts/verify_sample.py
    python scripts/verify_sample.py --process
    python scripts/verify_sample.py --quiet
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project paths.
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from config import (
    VERIFICATION_SAMPLE_PATH,
    HUMAN_REVIEW_TEMPLATE_PATH,
    VERIFICATION_RESULTS_PATH,
    FIRST_PASS_RESEARCH_PATH,
    save_research_output,
)

from research.verification import (
    create_verification_record,
    calculate_accuracy,
    generate_accuracy_report,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Evidence/source selection
# ---------------------------------------------------------------------------

FIELD_SOURCE_PRIORITY = {
    "auth_methods": [
        "official_auth_docs",
        "official_api_docs",
        "official_docs",
    ],
    "access_model": [
        "official_pricing",
        "official_auth_docs",
        "official_docs",
        "official_api_docs",
    ],
    "api_breadth": [
        "official_api_docs",
        "official_docs",
        "official_github",
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
        "official_api_docs",
        "official_github",
    ],
}


def _is_real_url(value: Any) -> bool:
    """Return True only for an actual HTTP(S) URL."""
    if not isinstance(value, str):
        return False
    value = value.strip().lower()
    return value.startswith("http://") or value.startswith("https://")


def select_official_source(
    app: Dict[str, Any],
    field: str,
) -> Optional[str]:
    """
    Select the best available official evidence URL for a field.

    Evidence is taken only from the research record. No URL is invented.
    """
    evidence = app.get("evidence", []) or []

    # Prefer field-specific source types.
    priorities = FIELD_SOURCE_PRIORITY.get(
        field,
        [
            "official_docs",
            "official_api_docs",
            "official_auth_docs",
            "official_pricing",
            "official_mcp",
            "official_github",
        ],
    )

    for source_type in priorities:
        for item in evidence:
            if not isinstance(item, dict):
                continue
            if item.get("source_type") == source_type and _is_real_url(
                item.get("url")
            ):
                return item["url"]

    # Fallback: any official source with a real URL.
    for item in evidence:
        if not isinstance(item, dict):
            continue
        source_type = str(item.get("source_type", "")).lower()
        if source_type.startswith("official") and _is_real_url(item.get("url")):
            return item["url"]

    return None


def select_source_claim(
    app: Dict[str, Any],
    field: str,
    source_url: Optional[str],
) -> Optional[str]:
    """Return the claim associated with the selected source URL."""
    if not source_url:
        return None

    for item in app.get("evidence", []) or []:
        if not isinstance(item, dict):
            continue
        if item.get("url") == source_url:
            claim = item.get("claim")
            if claim:
                return str(claim)

    return None


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_json(path: Path, default: Any) -> Any:
    """Safely load JSON from a project file."""
    if not path.exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_verification_sample() -> List[Dict[str, Any]]:
    """Load the 20-app verification sample."""
    data = load_json(VERIFICATION_SAMPLE_PATH, {})

    if not data:
        logger.error("Verification sample not found: %s", VERIFICATION_SAMPLE_PATH)
        logger.error("Run: python scripts/run_research.py")
        raise FileNotFoundError(str(VERIFICATION_SAMPLE_PATH))

    apps = data.get("apps", [])

    if not isinstance(apps, list):
        raise ValueError("verification_sample.json must contain an 'apps' list")

    return apps


def load_first_pass_index() -> Dict[str, Dict[str, Any]]:
    """
    Load first-pass research and index it by ID and app name.

    The verification sample may contain only a subset of the full research
    fields, so this index is the authoritative source for evidence URLs.
    """
    data = load_json(FIRST_PASS_RESEARCH_PATH, {})

    if not data:
        logger.error("First-pass research not found: %s", FIRST_PASS_RESEARCH_PATH)
        raise FileNotFoundError(str(FIRST_PASS_RESEARCH_PATH))

    apps = data.get("apps", [])

    if not isinstance(apps, list):
        raise ValueError("first_pass_research.json must contain an 'apps' list")

    index: Dict[str, Dict[str, Any]] = {}

    for app in apps:
        if not isinstance(app, dict):
            continue

        if app.get("id") is not None:
            index[f"id:{app['id']}"] = app

        if app.get("app_name"):
            index[f"name:{str(app['app_name']).strip().lower()}"] = app

    return index


def find_research_record(
    sample_app: Dict[str, Any],
    research_index: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Find the corresponding full first-pass research record."""
    app_id = sample_app.get("id")
    if app_id is not None:
        result = research_index.get(f"id:{app_id}")
        if result:
            return result

    app_name = sample_app.get("app_name")
    if app_name:
        result = research_index.get(
            f"name:{str(app_name).strip().lower()}"
        )
        if result:
            return result

    # If the sample already contains evidence, it can still be used.
    return sample_app


# ---------------------------------------------------------------------------
# Template generation
# ---------------------------------------------------------------------------

def create_human_review_template(
    apps: List[Dict[str, Any]],
    research_index: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Create verification records for the selected apps.

    Four fields are checked for every app:
      auth_methods
      access_model
      api_breadth
      buildability

    MCP is checked only where the agent reports MCP availability.
    """
    template: List[Dict[str, Any]] = []

    for sample_app in apps:
        app = find_research_record(sample_app, research_index)

        app_id = app.get("id", sample_app.get("id"))
        app_name = app.get("app_name", sample_app.get("app_name"))
        category = app.get("category", sample_app.get("category"))

        fields_to_verify = [
            "auth_methods",
            "access_model",
            "api_breadth",
            "buildability",
        ]

        if bool(app.get("mcp_available")):
            fields_to_verify.append("mcp_available")

        for field in fields_to_verify:
            agent_value = app.get(field)

            # Keep a clear True/False value for MCP.
            if field == "mcp_available":
                agent_value = bool(app.get("mcp_available"))

            official_source = select_official_source(app, field)
            source_claim = select_source_claim(
                app,
                field,
                official_source,
            )

            # Use the project's verification helper. It starts the record
            # as pending and does not fabricate human results.
            record = create_verification_record(
                app_id=app_id,
                app_name=app_name,
                category=category,
                field=field,
                agent_value=agent_value,
                official_source=official_source,
            )

            # Extra audit metadata is useful to the reviewer and harmless
            # to existing processing code.
            record["source_claim"] = source_claim

            if official_source is None:
                record["source_status"] = "missing_official_evidence"
            else:
                record["source_status"] = "official_source_found"

            template.append(record)

    return template


def validate_template_sources(
    template: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Validate source coverage without pretending that verification is done."""
    missing = sum(
        1 for record in template
        if not _is_real_url(record.get("official_source"))
    )

    official = sum(
        1 for record in template
        if record.get("source_status") == "official_source_found"
    )

    pending = sum(
        1 for record in template
        if record.get("human_result") == "pending"
    )

    return {
        "total": len(template),
        "official_sources": official,
        "missing_sources": missing,
        "pending": pending,
    }


def generate_template() -> Dict[str, Any]:
    """Generate and save the human review template."""
    logger.info("Loading verification sample...")
    apps = load_verification_sample()

    logger.info("Loading first-pass research...")
    research_index = load_first_pass_index()

    logger.info("Creating review template for %d apps...", len(apps))
    template = create_human_review_template(apps, research_index)

    stats = validate_template_sources(template)

    logger.info("Template contains %d verification records", stats["total"])
    logger.info(
        "Official source URLs: %d/%d",
        stats["official_sources"],
        stats["total"],
    )
    logger.info(
        "Missing official source URLs: %d",
        stats["missing_sources"],
    )
    logger.info("Pending human reviews: %d", stats["pending"])

    template_data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_apps": len(apps),
            "total_checks": len(template),
            "official_source_count": stats["official_sources"],
            "missing_source_count": stats["missing_sources"],
            "description": (
                "Human review template. Fill in human_result, "
                "human_verified_value, and human_notes for each record."
            ),
            "verification_status": "pending",
            "instructions": [
                "For each record, visit the official_source URL.",
                "Compare agent_value with the official documentation.",
                "Set human_result to: correct, incorrect, ambiguous, or pending.",
                "If incorrect, set human_verified_value to the correct value.",
                "Add human_notes explaining your decision.",
                "Set verification_date and verifier_name when complete.",
                "Do not mark a record correct without checking its source.",
                "The accuracy report is generated only from completed reviews.",
            ],
        },
        "template": template,
    }

    save_research_output(
        template_data,
        HUMAN_REVIEW_TEMPLATE_PATH,
    )

    logger.info("")
    logger.info("Human review template created!")
    logger.info("Location: %s", HUMAN_REVIEW_TEMPLATE_PATH)

    if stats["missing_sources"]:
        logger.warning(
            "%d records do not have a real official source URL.",
            stats["missing_sources"],
        )
        logger.warning(
            "Those records must remain pending until an official source is found."
        )

    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Review the official_source for each record.")
    logger.info("2. Compare agent_value with official documentation.")
    logger.info("3. Fill human_result, human_verified_value, and human_notes.")
    logger.info("4. Run: python scripts/verify_sample.py --process")

    return template_data


# ---------------------------------------------------------------------------
# Processing completed reviews
# ---------------------------------------------------------------------------

def load_completed_reviews() -> List[Dict[str, Any]]:
    """Load only reviews that have actually been completed."""
    if not HUMAN_REVIEW_TEMPLATE_PATH.exists():
        logger.error(
            "Review template not found: %s",
            HUMAN_REVIEW_TEMPLATE_PATH,
        )
        return []

    with open(HUMAN_REVIEW_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    template = data.get("template", [])

    valid_results = {"correct", "incorrect", "ambiguous"}

    return [
        record
        for record in template
        if record.get("human_result") in valid_results
    ]


def process_completed_reviews() -> None:
    """Process completed human reviews and generate accuracy report."""
    logger.info("Loading completed reviews...")
    reviews = load_completed_reviews()

    if not reviews:
        logger.warning("No completed reviews found.")
        logger.info(
            "Complete the human review template first: %s",
            HUMAN_REVIEW_TEMPLATE_PATH,
        )
        return

    logger.info("Found %d completed review records", len(reviews))

    accuracy = calculate_accuracy(reviews)

    logger.info("")
    logger.info("Accuracy Report:")
    logger.info("  Total checks: %d", accuracy["total_checks"])
    logger.info("  Correct: %d", accuracy["correct"])
    logger.info("  Incorrect: %d", accuracy["incorrect"])
    logger.info("  Ambiguous: %d", accuracy["ambiguous"])
    logger.info("  Accuracy: %.1f%%", accuracy["accuracy_percent"])

    report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "status": "verification_complete",
            "completed_checks": len(reviews),
        },
        "accuracy": accuracy,
        "results": reviews,
    }

    save_research_output(
        report,
        VERIFICATION_RESULTS_PATH,
    )

    logger.info(
        "Accuracy report saved: %s",
        VERIFICATION_RESULTS_PATH,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify research sample against official documentation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify_sample.py
  python scripts/verify_sample.py --process
  python scripts/verify_sample.py --quiet
        """,
    )

    parser.add_argument(
        "--process",
        action="store_true",
        help="Process completed reviews instead of creating the template",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress logging output",
    )

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    logger.info("=" * 70)
    logger.info("VERIFICATION PIPELINE")
    logger.info("=" * 70)

    try:
        if args.process:
            process_completed_reviews()
        else:
            generate_template()

        return 0

    except Exception as exc:
        logger.error("Verification failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())