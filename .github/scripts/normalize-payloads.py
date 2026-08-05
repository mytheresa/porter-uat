import glob
import json
import os
from typing import Any


def normalize_evidence_availability(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text == "available":
        return "Available"
    if "unavailable" in text:
        return "Unavailable"
    # Defensive default to explicit unavailable when value is empty/unknown.
    return "Unavailable"


def normalize_payload(path: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    epic_created_by = str(data.get("EPIC_CREATED_BY", "")).strip()
    epic_key = str(data.get("EPIC_KEY", "")).strip()
    epic_slug = str(data.get("EPIC_SLUG", "")).strip()

    checklist_rows = data.get("CHECKLIST_ROWS", [])
    for row in checklist_rows:
        if isinstance(row, dict):
            if row.get("Contact") != epic_created_by:
                row["Contact"] = epic_created_by
                changed = True

    matrix_rows = data.get("MATRIX_ROWS", [])
    for row in matrix_rows:
        if isinstance(row, dict):
            normalized = normalize_evidence_availability(row.get("Evidence Availability"))
            if row.get("Evidence Availability") != normalized:
                row["Evidence Availability"] = normalized
                changed = True

    if epic_key and epic_slug:
        canonical_output_path = f"uat-test-plans/{epic_key}-{epic_slug}.xlsx"
        if data.get("OUTPUT_PATH") != canonical_output_path:
            data["OUTPUT_PATH"] = canonical_output_path
            changed = True

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    return changed


def main() -> None:
    patterns = [
        "uat-test-plans/source/*/data_payload_*.json",
        "uat-test-plans/source/startup/data_payload_*.json",
    ]

    paths = sorted({p for pattern in patterns for p in glob.glob(pattern) if os.path.isfile(p)})

    changed_count = 0
    for path in paths:
        if normalize_payload(path):
            changed_count += 1
            print(f"UPDATED {path}")
        else:
            print(f"UNCHANGED {path}")

    print(f"TOTAL {len(paths)} payloads scanned; {changed_count} updated.")


if __name__ == "__main__":
    main()
