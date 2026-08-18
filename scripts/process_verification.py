#!/usr/bin/env python3

"""
Process human verification results.

Reads:
    data/human_review_template.json

Writes:
    data/verification_results.json
    data/accuracy_report.json

IMPORTANT:
This script never fabricates human verification.
Only records marked as:
    correct
    incorrect
    ambiguous

are considered completed.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))

from config import (
    HUMAN_REVIEW_TEMPLATE_PATH,
    VERIFICATION_RESULTS_PATH,
    ACCURACY_REPORT_PATH,
)


# ============================================================
# LOGGING
# ============================================================

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


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path) -> Any:
    """Load JSON from disk."""

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data: Any, path: Path) -> None:
    """Save JSON to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# LOAD TEMPLATE
# ============================================================

def load_review_template() -> List[Dict[str, Any]]:
    """Load human review records."""

    if not HUMAN_REVIEW_TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Review template not found: "
            f"{HUMAN_REVIEW_TEMPLATE_PATH}"
        )

    data = load_json(HUMAN_REVIEW_TEMPLATE_PATH)

    if isinstance(data, dict):
        records = data.get("template", [])
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError(
            "Invalid human_review_template.json format."
        )

    if not isinstance(records, list):
        raise ValueError(
            "'template' must contain a list."
        )

    return records


# ============================================================
# VERIFICATION HELPERS
# ============================================================

def get_pending_records(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return pending records."""

    return [
        record
        for record in records
        if record.get("human_result") == "pending"
    ]


def get_completed_records(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return completed verification records."""

    return [
        record
        for record in records
        if record.get("human_result") in VALID_RESULTS
    ]


# ============================================================
# ACCURACY
# ============================================================

def calculate_accuracy(
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate verification accuracy.

    Ambiguous = 0.5 credit.
    """

    if not records:
        return {
            "total_checks": 0,
            "correct": 0,
            "incorrect": 0,
            "ambiguous": 0,
            "accuracy_percent": 0.0,
            "status": "no_data",
        }

    correct = sum(
        1
        for record in records
        if record.get("human_result") == "correct"
    )

    incorrect = sum(
        1
        for record in records
        if record.get("human_result") == "incorrect"
    )

    ambiguous = sum(
        1
        for record in records
        if record.get("human_result") == "ambiguous"
    )

    total = len(records)

    accuracy = (
        (correct + ambiguous * 0.5)
        / total
        * 100
    )

    return {
        "total_checks": total,
        "correct": correct,
        "incorrect": incorrect,
        "ambiguous": ambiguous,
        "accuracy_percent": round(accuracy, 1),
        "status": "complete",
    }


# ============================================================
# FIELD STATISTICS
# ============================================================

def calculate_field_statistics(
    records: List[Dict[str, Any]],
) -> Dict[str, Dict[str, int]]:
    """Calculate verification statistics by field."""

    stats: Dict[str, Dict[str, int]] = {}

    for record in records:

        field = record.get(
            "field",
            "unknown",
        )

        if field not in stats:
            stats[field] = {
                "total": 0,
                "correct": 0,
                "incorrect": 0,
                "ambiguous": 0,
            }

        stats[field]["total"] += 1

        result = record.get("human_result")

        if result in {
            "correct",
            "incorrect",
            "ambiguous",
        }:
            stats[field][result] += 1

    return stats


# ============================================================
# MAIN PROCESSOR
# ============================================================

def process_verification() -> int:
    """Process human verification."""

    logger.info("=" * 70)
    logger.info("PROCESSING HUMAN VERIFICATION")
    logger.info("=" * 70)

    records = load_review_template()

    total = len(records)

    pending = get_pending_records(records)

    completed = get_completed_records(records)

    logger.info(
        f"Total verification records: {total}"
    )

    logger.info(
        f"Completed reviews: {len(completed)}"
    )

    logger.info(
        f"Pending reviews: {len(pending)}"
    )

    # --------------------------------------------------------
    # IMPORTANT SAFETY CHECK
    # --------------------------------------------------------

    if pending:

        logger.warning(
            f"{len(pending)} verification records "
            f"are still pending."
        )

        logger.warning(
            "Human verification has NOT been completed."
        )

        logger.info(
            "No final accuracy claim will be made."
        )

        # Save a status report so the pipeline has
        # a transparent state.

        report = {
            "status": "pending",
            "generated": datetime.now().isoformat(),

            "summary": {
                "total_records": total,
                "completed_reviews": len(completed),
                "pending_reviews": len(pending),
            },

            "accuracy": calculate_accuracy(
                completed
            ),

            "field_statistics":
                calculate_field_statistics(
                    completed
                ),

            "message": (
                "Human verification is still pending. "
                "Complete the review template before "
                "using the accuracy results."
            ),
        }

        save_json(
            report,
            ACCURACY_REPORT_PATH,
        )

        logger.info(
            f"Pending accuracy status saved to: "
            f"{ACCURACY_REPORT_PATH}"
        )

        return 0

    # --------------------------------------------------------
    # COMPLETED VERIFICATION
    # --------------------------------------------------------

    results = []

    for record in completed:

        results.append(
            {
                "app_id": record.get("app_id"),
                "app_name": record.get("app_name"),
                "field": record.get("field"),
                "agent_value": record.get(
                    "agent_value"
                ),
                "official_source": record.get(
                    "official_source"
                ),
                "human_result": record.get(
                    "human_result"
                ),
                "human_verified_value":
                    record.get(
                        "human_verified_value"
                    ),
                "human_notes": record.get(
                    "human_notes",
                    "",
                ),
                "verification_date":
                    record.get(
                        "verification_date"
                    ),
                "verifier_name":
                    record.get(
                        "verifier_name"
                    ),
            }
        )

    # --------------------------------------------------------
    # ACCURACY
    # --------------------------------------------------------

    accuracy = calculate_accuracy(
        completed
    )

    field_statistics = calculate_field_statistics(
        completed
    )

    # --------------------------------------------------------
    # SAVE VERIFICATION RESULTS
    # --------------------------------------------------------

    verification_output = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "total_records": total,
            "completed_records": len(completed),
            "description": (
                "Human verification results."
            ),
        },

        "results": results,
    }

    save_json(
        verification_output,
        VERIFICATION_RESULTS_PATH,
    )

    # --------------------------------------------------------
    # SAVE ACCURACY REPORT
    # --------------------------------------------------------

    accuracy_report = {
        "status": "complete",

        "generated": datetime.now().isoformat(),

        "summary": {
            "total_records": total,
            "completed_reviews": len(completed),
            "pending_reviews": 0,
        },

        "accuracy": accuracy,

        "field_statistics": field_statistics,
    }

    save_json(
        accuracy_report,
        ACCURACY_REPORT_PATH,
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    logger.info("")
    logger.info("=" * 70)
    logger.info("VERIFICATION COMPLETE")
    logger.info("=" * 70)

    logger.info(
        f"Total checks: {total}"
    )

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

    logger.info(
        f"Verification results: "
        f"{VERIFICATION_RESULTS_PATH}"
    )

    logger.info(
        f"Accuracy report: "
        f"{ACCURACY_REPORT_PATH}"
    )

    logger.info("=" * 70)

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

def main() -> int:

    try:
        return process_verification()

    except Exception as exc:

        logger.error(
            f"Processing failed: {exc}",
            exc_info=True,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())