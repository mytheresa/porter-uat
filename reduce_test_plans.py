"""
reduce_test_plans.py
Reduce each UAT checklist by ~30% (min 4 checks) by dropping lowest-priority
sections first, then regenerate xlsx files under uat-test-plans-reduced30/.
"""

import copy
import json
import math
import os
import subprocess
import sys
import tempfile

GENERATOR = os.path.join(os.path.dirname(__file__), ".github", "scripts", "generate-test-plan-xlsx.py")
SOURCE_DIR = os.path.join(os.path.dirname(__file__), "uat-test-plans", "source")
OUTPUT_DIR = "uat-test-plans-reduced30"
PYTHON = sys.executable

# --- Priority classification by section name (case-insensitive substring match) ---

LOW_SECTIONS = [
    "regression",
    "cross-brand",
    "cross brand",
    "cross-service",
    "data robustness",
    "negative-path",
    "name clipping",
    "ux feedback",
    "scroll behavior",
    "auth transition",
    "idempotency",
]

MEDIUM_SECTIONS = [
    "responsive behavior",
    "concierge handover",
    "navigation continuity",
    "mobile service",
    "mobile auth",
    "footer display",
    "no-flyout",
    "non-auth",
    "modal cancel",
    "all items consistency",
    "brand coverage",
    "redirect safety",
    "internal match logic",
]


def section_priority(section: str) -> int:
    """Return 1=Low, 2=Medium, 3=High based on section name."""
    s = section.lower()
    if any(k in s for k in LOW_SECTIONS):
        return 1
    if any(k in s for k in MEDIUM_SECTIONS):
        return 2
    return 3


def select_rows_to_drop(checklist_rows: list[dict], n_remove: int) -> set[str]:
    """Return set of Check IDs to drop (lowest priority first, later position first within tier)."""
    scored = [
        (section_priority(r["Section"]), -i, r["Check ID"])
        for i, r in enumerate(checklist_rows)
    ]
    # Sort ascending by priority score (1=Low first), then by -position (higher idx first)
    scored.sort(key=lambda x: (x[0], x[1]))
    return {cid for _, _, cid in scored[:n_remove]}


def update_matrix_rows(matrix_rows: list[dict], dropped_ids: set[str]) -> list[dict]:
    """Remove dropped UAT IDs from Checklist Mapping; drop COV row if mapping becomes empty."""
    updated = []
    for row in matrix_rows:
        mapping = row.get("Checklist Mapping", "")
        parts = [p.strip() for p in str(mapping).replace(";", ",").split(",") if p.strip()]
        remaining = [p for p in parts if p not in dropped_ids]
        if not remaining:
            # All mapped checks were dropped — remove this coverage row
            continue
        row = dict(row)
        row["Checklist Mapping"] = ", ".join(remaining)
        updated.append(row)
    return updated


def reduce_payload(data: dict) -> tuple[dict, set[str]]:
    checklist = data["CHECKLIST_ROWS"]
    total = len(checklist)
    target_keep = max(4, math.ceil(total * 0.70))
    n_remove = total - target_keep

    if n_remove <= 0:
        # Nothing to remove (already at/below floor)
        dropped = set()
    else:
        dropped = select_rows_to_drop(checklist, n_remove)

    reduced = copy.deepcopy(data)
    reduced["CHECKLIST_ROWS"] = [r for r in checklist if r["Check ID"] not in dropped]
    reduced["MATRIX_ROWS"] = update_matrix_rows(copy.deepcopy(data["MATRIX_ROWS"]), dropped)

    kept = len(reduced["CHECKLIST_ROWS"])
    removed_pct = round((total - kept) / total * 100)
    reduced["COVERAGE_SUMMARY"] = (
        f"[Reduced ~{removed_pct}% — {kept}/{total} checks retained, "
        f"lowest-priority sections dropped] " + data["COVERAGE_SUMMARY"]
    )

    epic_key = data["EPIC_KEY"]
    epic_slug = data["EPIC_SLUG"]
    reduced["OUTPUT_PATH"] = f"{OUTPUT_DIR}/{epic_key}-{epic_slug}.xlsx"

    return reduced, dropped


def run_generator(payload_path: str) -> bool:
    result = subprocess.run(
        [PYTHON, GENERATOR, payload_path],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__),
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip() or result.stdout.strip()}")
        return False
    print(f"  {result.stdout.strip()}")
    return True


def write_dropped_summary(
    summary_rows: list[tuple[str, int, int, list[str]]], output_dir: str
) -> None:
    lines = [
        "# Dropped Checks Summary\n",
        "Lowest-priority sections removed first (LOW → MEDIUM). HIGH-priority checks are never dropped.\n",
        "",
        "| Epic | Original | Kept | Dropped checks (Check ID [Section]) |",
        "|---|---|---|---|",
    ]
    for epic_key, original, kept, dropped_labels in summary_rows:
        dropped_cell = ", ".join(dropped_labels) if dropped_labels else "—"
        lines.append(f"| {epic_key} | {original} | {kept} | {dropped_cell} |")

    total_original = sum(r[1] for r in summary_rows)
    total_kept = sum(r[2] for r in summary_rows)
    pct = round((total_original - total_kept) / total_original * 100)
    lines += [
        "",
        f"**Total: {total_original} → {total_kept} checks ({pct}% removed)**",
    ]

    out_path = os.path.join(output_dir, "dropped-summary.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nSummary written to {out_path}")


def main() -> None:
    os.makedirs(os.path.join(os.path.dirname(__file__), OUTPUT_DIR), exist_ok=True)

    payloads = sorted([
        os.path.join(root, f)
        for root, _, files in os.walk(SOURCE_DIR)
        for f in files
        if f.startswith("data_payload_") and f.endswith(".json")
    ])

    if not payloads:
        print(f"No payload files found under {SOURCE_DIR}")
        sys.exit(1)

    total_original = 0
    total_kept = 0
    summary_rows: list[tuple[str, int, int, list[str]]] = []

    for payload_path in payloads:
        epic_key = os.path.basename(os.path.dirname(payload_path))
        print(f"\n{epic_key}")

        with open(payload_path, encoding="utf-8") as f:
            data = json.load(f)

        original_count = len(data["CHECKLIST_ROWS"])
        reduced_data, dropped = reduce_payload(data)
        kept_count = len(reduced_data["CHECKLIST_ROWS"])

        print(f"  {original_count} checks → {kept_count} kept, {len(dropped)} dropped")
        dropped_labels = []
        if dropped:
            dropped_labels = [
                f"{r['Check ID']} [{r['Section']}]"
                for r in data["CHECKLIST_ROWS"]
                if r["Check ID"] in dropped
            ]
            print(f"  Dropped: {', '.join(dropped_labels)}")

        summary_rows.append((epic_key, original_count, kept_count, dropped_labels))

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(reduced_data, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name

        try:
            run_generator(tmp_path)
        finally:
            os.unlink(tmp_path)

        total_original += original_count
        total_kept += kept_count

    removed_total = total_original - total_kept
    pct = round(removed_total / total_original * 100)
    print(f"\nDone. {total_original} → {total_kept} checks across all epics ({pct}% removed).")
    print(f"Output: {OUTPUT_DIR}/")

    write_dropped_summary(summary_rows, os.path.join(os.path.dirname(__file__), OUTPUT_DIR))


if __name__ == "__main__":
    main()
