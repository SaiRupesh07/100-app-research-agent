"""
Configuration and constants for the research pipeline.

The project follows this data flow:

    data/apps.json
        ↓
    Research Agent
        ↓
    data/first_pass_research.json
        ↓
    Verification sample
        ↓
    Human review
        ↓
    Final dataset / case study
"""

import json
from pathlib import Path
from typing import Any


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent

# Data directory
DATA_DIR = PROJECT_ROOT / "data"

# ------------------------------------------------------------
# Research input
# ------------------------------------------------------------

# IMPORTANT:
# This file contains ONLY the 100-app research input:
# id, app_name, category.
#
# It must NOT contain research conclusions.
APP_LIST_PATH = DATA_DIR / "apps.json"

# ------------------------------------------------------------
# Research outputs
# ------------------------------------------------------------

FIRST_PASS_RESEARCH_PATH = DATA_DIR / "first_pass_research.json"

# Final verified dataset
FINAL_DATASET_PATH = DATA_DIR / "final_dataset.json"

# ------------------------------------------------------------
# Verification outputs
# ------------------------------------------------------------

VERIFICATION_SAMPLE_PATH = DATA_DIR / "verification_sample.json"

HUMAN_REVIEW_TEMPLATE_PATH = DATA_DIR / "human_review_template.json"

VERIFICATION_RESULTS_PATH = DATA_DIR / "verification_results.json"

ACCURACY_REPORT_PATH = DATA_DIR / "accuracy_report.json"

VERIFICATION_REPORT_PATH = DATA_DIR / "verification_report.md"

# ------------------------------------------------------------
# Optional research cache
# ------------------------------------------------------------

CACHE_DIR = DATA_DIR / "cache"

# ------------------------------------------------------------
# Scripts
# ------------------------------------------------------------

SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# ------------------------------------------------------------
# Documentation
# ------------------------------------------------------------

DOCS_DIR = PROJECT_ROOT / "docs"

# ------------------------------------------------------------
# Case study
# ------------------------------------------------------------

CASE_STUDY_DIR = PROJECT_ROOT / "case-study"

CASE_STUDY_OUTPUT = CASE_STUDY_DIR / "index.html"


# ============================================================
# RESEARCH SETTINGS
# ============================================================

# HTTP request settings for official documentation research.

REQUEST_TIMEOUT_SECONDS = 20

MAX_RETRIES = 2

REQUEST_DELAY_SECONDS = 0.5

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; 100-App-Research-Agent/1.0; "
    "+https://github.com/)"
)


# Maximum number of source pages to retain per app.

MAX_SOURCES_PER_APP = 5


# Preferred source hierarchy.
#
# Sources higher in the list should generally be preferred
# when multiple sources support the same claim.

SOURCE_PRIORITY = [
    "official_docs",
    "official_api_docs",
    "official_auth_docs",
    "official_pricing",
    "official_mcp",
    "official_github",
    "third_party",
    "inferred",
]


# Only these source types should normally support
# high-confidence factual claims.

HIGH_CONFIDENCE_SOURCE_TYPES = {
    "official_docs",
    "official_api_docs",
    "official_auth_docs",
    "official_pricing",
    "official_mcp",
    "official_github",
}


# ============================================================
# CLASSIFICATION CONSTANTS
# ============================================================

# Valid buildability classifications.

BUILDABILITY_CATEGORIES = {
    "Buildable now": (
        "Public API, usable authentication, self-serve credentials, "
        "and sufficient API surface."
    ),
    "Buildable with friction": (
        "Requires paid plan, OAuth approval, admin approval, "
        "limited scopes, or other meaningful setup friction."
    ),
    "Gated / Not Practical": (
        "Requires partnership, sales contact, private access, "
        "or has no meaningful public API."
    ),
}


# Valid confidence levels.

CONFIDENCE_LEVELS = {
    "High": "Official documentation clearly supports the claim.",
    "Medium": "Partial official information or some ambiguity.",
    "Low": "Third-party sources or incomplete evidence.",
    "Unknown": "No reliable evidence found.",
}


# Valid research status.

RESEARCH_STATUS_VALUES = {
    "success",
    "failed",
    "unknown",
    "partial",
}


# ============================================================
# VERIFICATION CONSTANTS
# ============================================================

# IMPORTANT:
# Use the same vocabulary everywhere in the verification pipeline.

VERIFICATION_STATUS_VALUES = {
    "pending",
    "correct",
    "incorrect",
    "ambiguous",
}


# ============================================================
# ACCESS MODEL
# ============================================================

ACCESS_MODELS = {
    "Self-serve Free",
    "Self-serve Paid",
    "Admin Approval",
    "Partner / Contact Sales",
    "Private Beta",
    "Unknown",
}


# Credential models.

CREDENTIAL_MODELS = {
    "self-serve",
    "gated",
    "partner",
    "unknown",
}


# ============================================================
# API CLASSIFICATION
# ============================================================

API_BREADTH_VALUES = {
    "Broad",
    "Moderate",
    "Narrow",
    "Very Narrow",
    "No Public API",
    "Unknown",
}


# ============================================================
# EXPECTED CATEGORIES
# ============================================================

CATEGORIES = {
    "CRM and Sales",
    "Support and Helpdesk",
    "Communications and Messaging",
    "Marketing, Ads, Email and Social",
    "Ecommerce",
    "Data, SEO and Scraping",
    "Developer, Infra and Data Platforms",
    "Productivity and Project Management",
    "Finance and Fintech",
    "AI, Research and Media-Native",
}


# ============================================================
# AUTHENTICATION METHODS
# ============================================================

AUTH_METHODS = {
    "OAuth2",
    "OAuth 2.0",
    "API Key",
    "JWT",
    "Basic Auth",
    "Bearer Token",
    "Token",
    "SDK",
    "Session/Cookie",
    "Webhook",
    "mTLS",
    "Personal Access Token",
}


# ============================================================
# API TYPES
# ============================================================

API_TYPES = {
    "REST",
    "GraphQL",
    "SOAP",
    "SDK",
    "CLI",
    "Webhook",
    "gRPC",
    "WebSocket",
}


# ============================================================
# COMMON BLOCKERS
# ============================================================

COMMON_BLOCKERS = {
    "Partner approval",
    "Paid plan",
    "Admin approval",
    "Limited/Restricted API",
    "Unclear documentation",
    "Private beta",
    "Contact sales",
    "No public API",
    "OAuth complexity",
    "Rate limiting",
    "Regional restrictions",
}


# ============================================================
# VERIFICATION SAMPLE CONFIGURATION
# ============================================================

# 10 categories × 2 apps = 20-app verification sample.

VERIFICATION_SAMPLE_SIZE = 20

APPS_PER_CATEGORY_IN_SAMPLE = 2


# ============================================================
# RESEARCH INPUT LOADING
# ============================================================

def load_app_list() -> list[dict[str, Any]]:
    """
    Load the minimal research input list.

    apps.json should contain only:
        - id
        - app_name
        - category

    It must not be used to store research conclusions.
    """

    if not APP_LIST_PATH.exists():
        raise FileNotFoundError(
            f"Research input file not found: {APP_LIST_PATH}"
        )

    with open(APP_LIST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected {APP_LIST_PATH} to contain a JSON list."
        )

    return data


# ============================================================
# FINAL DATASET LOADING
# ============================================================

def load_final_dataset() -> list[dict[str, Any]]:
    """
    Load the final verified dataset.

    IMPORTANT:
    This is an OUTPUT/reference dataset and should not be used
    as the input to the first-pass research process.
    """

    if not FINAL_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Final dataset not found: {FINAL_DATASET_PATH}"
        )

    with open(FINAL_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected {FINAL_DATASET_PATH} to contain a JSON list."
        )

    return data


# ============================================================
# BACKWARD-COMPATIBLE APP LIST HELPER
# ============================================================

def get_app_list_from_dataset() -> list[dict[str, Any]]:
    """
    Return the minimal app list.

    Preferred behavior:
        Load from data/apps.json.

    If apps.json does not exist yet, fall back to extracting
    id/app_name/category from final_dataset.json.

    The fallback exists only for migration/backward compatibility.
    """

    if APP_LIST_PATH.exists():
        return load_app_list()

    data = load_final_dataset()

    return [
        {
            "id": record["id"],
            "app_name": record["app_name"],
            "category": record["category"],
        }
        for record in data
    ]


# ============================================================
# OUTPUT HELPERS
# ============================================================

def save_research_output(
    data: dict[str, Any],
    path: Path,
) -> None:
    """
    Save structured research output to JSON.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# CACHE HELPERS
# ============================================================

def ensure_cache_dir() -> Path:
    """
    Create and return the research cache directory.
    """

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return CACHE_DIR