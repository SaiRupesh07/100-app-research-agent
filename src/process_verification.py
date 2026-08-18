#!/usr/bin/env python3
"""
Process completed human verification results.

Reads:
    data/human_review_template.json

Writes:
    data/verification_results.json
    data/accuracy_report.json

The script does NOT fabricate human verification.
Only records whose human_result is:
    correct
    incorrect
    ambiguous

are treated as completed.

Usage:
    python scripts/process_verification.py
    python scripts/process_verification.py --allow-pending
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))

from config import (
    HUMAN_REVIEW_TEMPLATE_PATH,
    VERIFICATION_RESULTS_PATH,
    ACCURACY_REPORT_PATH,
    FIRST_PASS_RESEARCH_PATH,
    save_research_output,
)


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


VALID_RESULTS = {
    "correct",
    "incorrect",
    "ambiguous",
}


# ---------------------------------------------------------
# Utility functions
# ---------------------------------------------------------

def load_json(path: Path) -> Any:
    """Load JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: Path) -> None:
    """Save JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


def load_review_template() -> List[Dict[str, Any]]:
    """Load the human review template."""

    if not HUMAN_REVIEW_TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Human review template not found: "
            f"{HUMAN_REVIEW_TEMPLATE_PATH}"
        )

    data = load_json(HUMAN_REVIEW_TEMPLATE_PATH)

    if isinstance(data, dict):
        records = data.get("template", [])
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError(
            "human_review_template.json must contain "
            "a JSON object or list."
        )

    if not isinstance(records, list):
        raise ValueError(
            "The 'template' field must contain a list."
        )

    return records


def get_completed_records(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return only completed human verification records."""

    return [
        record
        for record in records
        if record.get("human_result") in VALID_RESULTS
    ]


def calculate_accuracy(
    verification_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate accuracy from completed human reviews.

    Ambiguous records receive 0.5 credit.
    """

    if not verification_results:
        return {
            "total_checks": 0,
            "correct": 0,
            "incorrect": 0,
            "ambiguous": 0,
            "accuracy_percent": 0.0,
            "status": "no_completed_reviews",
        }

    correct = sum(
        1
        for r in verification_results
        if r.get("human_result") == "correct"
    )

    incorrect = sum(
        1
        for r in verification_results
        if r.get("human_result") == "incorrect"
    )

    ambiguous = sum(
        1
        for r in verification_results
        if r.get("human_result") == "ambiguous"
    )

    total = len(verification_results)

    accuracy = (
        (correct + ambiguous * 0.5) / total * 100
        if total
        else 0.0
    )

    return {
        "total_checks": total,
        "correct": correct,
        "incorrect": incorrect,
        "ambiguous": ambiguous,
        "accuracy_percent": round(accuracy, 1),
        "status": "complete",
    }


def compare_agent_and_human(
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Produce field-level verification statistics.
    """

    completed = get_completed_records(records)

    field_stats: Dict[str, Dict[str, int]] = {}

    for record in completed:
        field = record.get("field", "unknown")

        if field not in field_stats:
            field_stats[field] = {
                "total": 0,
                "correct": 0,
                "incorrect": 0,
                "ambiguous": 0,
            }

        field_stats[field]["total"] += 1

        result = record.get("human_result")

        if result in VALID_RESULTS:
            field_stats[field][result] += 1

    return field_stats


# ---------------------------------------------------------
# Main processing
# ---------------------------------------------------------

def process_verification(
    allow_pending: bool = False,
) -> int:
    """
    Process human verification.

    Important:
    This function NEVER marks pending records as correct.
    """

    logger.info("=" * 70)
    logger.info("PROCESS HUMAN VERIFICATION")
    logger.info("=" * 70)

    records = load_review_template()

    total = len(records)

    pending = sum(
        1
        for r in records
        if r.get("human_result") == "pending"
    )

    completed = get_completed_records(records)

    logger.info(f"Total review records: {total}")
    logger.info(f"Completed reviews: {len(completed)}")
    logger.info(f"Pending reviews: {pending}")

    # -----------------------------------------------------
    # Safety check
    # -----------------------------------------------------

    if pending > 0 and not allow_pending:
        logger.warning(
            f"{pending} human reviews are still pending."
        )

        logger.warning(
            "No final accuracy report will be generated "
            "until the completed reviews are processed."
        )

        logger.info(
            "Complete the human reviews and run this script again."
        )

        return 0

    # -----------------------------------------------------
    # Process completed records
    # -----------------------------------------------------

    verification_results = []

    for record in completed:
        verification_results.append(
            {
                "app_id": record.get("app_id"),
                "app_name": record.get("app_name"),
                "field": record.get("field"),
                "agent_value": record.get("agent_value"),
                "official_source": record.get("official_source"),
                "human_result": record.get("human_result"),
                "human_verified_value": record.get(
                    "human_verified_value"
                ),
                "human_notes": record.get("human_notes", ""),
                "verification_date": record.get(
                    "verification_date"
                ),
                "verifier_name": record.get(
                    "verifier_name"
                ),
            }
        )

    # -----------------------------------------------------
    # Accuracy
    # -----------------------------------------------------

    accuracy = calculate_accuracy(
        verification_results
    )

    field_stats = compare_agent_and_human(records)

    # -----------------------------------------------------
    # Verification results
    # -----------------------------------------------------

    verification_output = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_template_records": total,
            "completed_records": len(completed),
            "pending_records": pending,
            "description": (
                "Human verification results. "
                "Only completed human reviews are included."
            ),
        },
        "results": verification_results,
    }

    save_json(
        verification_output,
        VERIFICATION_RESULTS_PATH,
    )

    logger.info(
        f"Verification results saved to: "
        f"{VERIFICATION_RESULTS_PATH}"
    )

    # -----------------------------------------------------
    # Accuracy report
    # -----------------------------------------------------

    report = {
        "status": (
            "complete"
            if completed
            else "pending"
        ),
        "generated": datetime.now().isoformat(),
        "summary": {
            "total_template_records": total,
            "completed_reviews": len(completed),
            "pending_reviews": pending,
        },
        "accuracy": accuracy,
        "field_statistics": field_stats,
    }

    save_json(
        report,
        ACCURACY_REPORT_PATH,
    )

    logger.info(
        f"Accuracy report saved to: "
        f"{ACCURACY_REPORT_PATH}"
    )

    # -----------------------------------------------------
    # Console summary
    # -----------------------------------------------------

    logger.info("")
    logger.info("=" * 70)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 70)

    logger.info(f"Total records: {total}")
    logger.info(f"Completed: {len(completed)}")
    logger.info(f"Pending: {pending}")

    if completed:
        logger.info(
            f"Correct: {accuracy['correct']}"
        )
        logger.info(
            f"Incorrect: {accuracy['incorrect']}"
        )
        logger.info(
            f"Ambiguous: {accuracy['ambiguous']}"
        )
        logger.info(
            f"Accuracy: "
            f"{accuracy['accuracy_percent']}%"
        )
    else:
        logger.info(
            "Accuracy: Not available yet — "
            "no human reviews completed."
        )

    logger.info("=" * 70)

    return 0


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def main() -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(
        description="Process human verification results."
    )

    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help=(
            "Write reports even when some reviews "
            "are still pending."
        ),
    )

    args = parser.parse_args()

    try:
        return process_verification(
            allow_pending=args.allow_pending
        )

    except Exception as exc:
        logger.error(
            f"Verification processing failed: {exc}",
            exc_info=True,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())