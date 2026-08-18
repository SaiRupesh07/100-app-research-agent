import json
import re
from pathlib import Path

DATASET_PATH = Path(__file__).parent.parent / "data" / "final_dataset.json"

def validate():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors = []
    warnings = []

    # 1. Exactly 100 records
    if len(data) != 100:
        errors.append(f"Expected 100 records, got {len(data)}")
    else:
        print(f"✅ Records count: {len(data)}")

    # 2. Unique IDs
    ids = [r["id"] for r in data]
    if len(set(ids)) != len(ids):
        errors.append("Duplicate IDs found")
    else:
        print("✅ All IDs unique")

    # 3. Unique app names
    names = [r["app_name"] for r in data]
    if len(set(names)) != len(names):
        errors.append("Duplicate app names found")
    else:
        print("✅ All app names unique")

    # 4. Required fields and types
    required_fields = [
        "id", "app_name", "category", "description", "auth_methods",
        "credential_model", "self_serve", "access_model", "access_notes",
        "api_types", "api_breadth", "api_notes", "mcp_available",
        "mcp_type", "mcp_url", "buildability", "main_blocker",
        "buildability_reason", "evidence", "confidence",
        "research_status", "last_checked", "human_verified",
        "verification_status", "verification_notes"
    ]
    for i, record in enumerate(data):
        for field in required_fields:
            if field not in record:
                errors.append(f"Record {i+1} missing field '{field}'")
        # Check types
        if not isinstance(record.get("auth_methods"), list):
            errors.append(f"Record {i+1}: auth_methods must be a list")
        if not isinstance(record.get("api_types"), list):
            errors.append(f"Record {i+1}: api_types must be a list")
        if record.get("self_serve") not in [True, False, None]:
            errors.append(f"Record {i+1}: self_serve must be boolean or null")
        if not isinstance(record.get("evidence"), list):
            errors.append(f"Record {i+1}: evidence must be a list")
        # Evidence structure
        for ev in record.get("evidence", []):
            if "claim" not in ev or "url" not in ev or "source_type" not in ev:
                errors.append(f"Record {i+1}: evidence entry missing required fields")
            # URL format
            if not re.match(r'^https?://', ev.get("url", "")):
                errors.append(f"Record {i+1}: evidence URL invalid: {ev.get('url')}")

    # 5. Valid enums
    valid_buildability = {"Buildable now", "Buildable with friction", "Gated / Not Practical"}
    valid_confidence = {"High", "Medium", "Low", "Unknown"}
    valid_research_status = {"success", "failed", "unknown"}  # you can extend
    valid_verification_status = {None, "correct", "partial", "wrong", "unverifiable"}

    for i, r in enumerate(data):
        if r.get("buildability") not in valid_buildability:
            errors.append(f"Record {i+1}: invalid buildability '{r.get('buildability')}'")
        if r.get("confidence") not in valid_confidence:
            errors.append(f"Record {i+1}: invalid confidence '{r.get('confidence')}'")
        if r.get("research_status") not in valid_research_status:
            errors.append(f"Record {i+1}: invalid research_status '{r.get('research_status')}'")
        if r.get("verification_status") not in valid_verification_status:
            errors.append(f"Record {i+1}: invalid verification_status '{r.get('verification_status')}'")

    # 6. If human_verified is true, verification_status must be set
    for i, r in enumerate(data):
        if r.get("human_verified") is True and r.get("verification_status") is None:
            warnings.append(f"Record {i+1}: human_verified is true but verification_status is null")
        if r.get("human_verified") is False and r.get("verification_status") is not None:
            warnings.append(f"Record {i+1}: human_verified is false but verification_status is set")

    # 7. Check categories (should match the 10 categories used)
    categories = set(r["category"] for r in data)
    expected_categories = {
        "CRM and Sales", "Support and Helpdesk", "Communications and Messaging",
        "Marketing, Ads, Email and Social", "Ecommerce", "Data, SEO and Scraping",
        "Developer, Infra and Data Platforms", "Productivity and Project Management",
        "Finance and Fintech", "AI, Research and Media-Native"
    }
    if categories != expected_categories:
        diff = categories.symmetric_difference(expected_categories)
        warnings.append(f"Category mismatch: {diff}")

    # Print summary
    print("\n" + "="*50)
    if errors:
        print("❌ Validation FAILED")
        for e in errors:
            print(f"  Error: {e}")
    else:
        print("✅ All structural checks passed.")
    if warnings:
        print("⚠️ Warnings:")
        for w in warnings:
            print(f"  Warning: {w}")
    print("="*50)

if __name__ == "__main__":
    validate()