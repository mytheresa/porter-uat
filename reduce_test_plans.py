"""
reduce_test_plans.py (Reducer V2)

Deterministically reduce each UAT checklist by target ratio while preserving hard
coverage constraints derived from MATRIX_ROWS joins.
"""

import copy
import json
import math
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from typing import Any

GENERATOR = os.path.join(os.path.dirname(__file__), ".github", "scripts", "generate-test-plan-xlsx.py")
SOURCE_DIR = os.path.join(os.path.dirname(__file__), "uat-test-plans", "source")
OUTPUT_DIR = "uat-test-plans-reduced30"
PYTHON = sys.executable

TARGET_KEEP_RATIO = 0.70
MIN_CHECKS_KEPT = 4

PRIORITY_WEIGHT = {"High": 100, "Medium": 65, "Low": 35}
FIDELITY_WEIGHT = {"Full": 35, "Partial": 22, "Inferred": 10}
EVIDENCE_WEIGHT = {"Available": 0, "Unavailable": 8}

CASE_TYPE_BONUS = {
    "functional": 8,
    "regression": 20,
    "integration": 16,
    "compatibility": 12,
    "resilience": 12,
    "dependency": 10,
    "ux": 6,
    "usability": 6,
}

CORE_CASE_TYPES = {"functional", "regression", "integration"}
PRIORITY_LEVELS = ["High", "Medium", "Low"]


def parse_mapping_ids(mapping_value: Any) -> list[str]:
    return [part.strip() for part in str(mapping_value or "").replace(";", ",").split(",") if part.strip()]


def normalize_checklist_row(row: Any, idx: int) -> dict[str, str]:
    if isinstance(row, dict):
        check_id = str(row.get("Check ID", "")).strip()
        section = str(row.get("Section", "")).strip()
        if not check_id:
            raise ValueError(f"CHECKLIST_ROWS row {idx} has empty Check ID")
        return {"Check ID": check_id, "Section": section}

    if isinstance(row, list):
        if not row:
            raise ValueError(f"CHECKLIST_ROWS row {idx} is empty")
        check_id = str(row[0]).strip()
        section = str(row[2]).strip() if len(row) > 2 else ""
        if not check_id:
            raise ValueError(f"CHECKLIST_ROWS row {idx} has empty Check ID")
        return {"Check ID": check_id, "Section": section}

    raise ValueError(f"CHECKLIST_ROWS row {idx} must be dict or list")


def normalize_matrix_row(row: Any, idx: int) -> dict[str, str]:
    if isinstance(row, dict):
        ac_ref = str(row.get("AC Ref", "")).strip()
        mapping = str(row.get("Checklist Mapping", "")).strip()
        priority = str(row.get("Priority", "")).strip()
        fidelity = str(row.get("AC Fidelity", "")).strip()
        evidence = str(row.get("Evidence Availability", "")).strip()
        case_type = str(row.get("Case Type", "")).strip()
        if not ac_ref:
            raise ValueError(f"MATRIX_ROWS row {idx} has empty AC Ref")
        if not mapping:
            raise ValueError(f"MATRIX_ROWS row {idx} has empty Checklist Mapping")
        return {
            "AC Ref": ac_ref,
            "Checklist Mapping": mapping,
            "Priority": priority,
            "AC Fidelity": fidelity,
            "Evidence Availability": evidence,
            "Case Type": case_type,
        }

    if isinstance(row, list):
        if len(row) < 10:
            raise ValueError(f"MATRIX_ROWS row {idx} has insufficient columns")
        return {
            "AC Ref": str(row[2]).strip(),
            "Checklist Mapping": str(row[5]).strip(),
            "Priority": str(row[4]).strip(),
            "AC Fidelity": str(row[6]).strip(),
            "Evidence Availability": str(row[8]).strip(),
            "Case Type": str(row[9]).strip(),
        }

    raise ValueError(f"MATRIX_ROWS row {idx} must be dict or list")


def score_matrix_row(row: dict[str, str]) -> int:
    priority_score = PRIORITY_WEIGHT.get(row.get("Priority", ""), 0)
    fidelity_score = FIDELITY_WEIGHT.get(row.get("AC Fidelity", ""), 0)
    evidence_score = EVIDENCE_WEIGHT.get(row.get("Evidence Availability", ""), 0)
    case_score = CASE_TYPE_BONUS.get(row.get("Case Type", "").strip().lower(), 0)
    return priority_score + fidelity_score + evidence_score + case_score


def update_matrix_rows(matrix_rows: list[Any], dropped_ids: set[str]) -> list[Any]:
    """Remove dropped check IDs from Checklist Mapping; drop matrix rows with empty mapping."""
    updated: list[Any] = []
    for row in matrix_rows:
        if isinstance(row, dict):
            mapping = row.get("Checklist Mapping", "")
            parts = parse_mapping_ids(mapping)
            remaining = [p for p in parts if p not in dropped_ids]
            if not remaining:
                continue
            new_row = dict(row)
            new_row["Checklist Mapping"] = ", ".join(remaining)
            updated.append(new_row)
            continue

        if isinstance(row, list):
            parts = parse_mapping_ids(row[5] if len(row) > 5 else "")
            remaining = [p for p in parts if p not in dropped_ids]
            if not remaining:
                continue
            new_row = list(row)
            while len(new_row) <= 5:
                new_row.append("")
            new_row[5] = ", ".join(remaining)
            updated.append(new_row)
            continue

        # Keep unexpected row types untouched so upstream validation catches shape issues.
        updated.append(row)

    return updated


def priority_counter(matrix_rows: list[Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for idx, row in enumerate(matrix_rows, start=1):
        m = normalize_matrix_row(row, idx)
        pr = m.get("Priority", "")
        if pr in PRIORITY_LEVELS:
            counts[pr] += 1
    return counts


def priority_reliability_kpi(counts: Counter[str]) -> tuple[int, str]:
    total = sum(counts.values())
    if total == 0:
        return 0, "No data"

    levels_present = sum(1 for level in PRIORITY_LEVELS if counts.get(level, 0) > 0)
    diversity = levels_present / len(PRIORITY_LEVELS)
    high_share = counts.get("High", 0) / total
    balance = max(0.0, 1.0 - abs(high_share - 0.5) / 0.5)
    score = round((0.6 * diversity + 0.4 * balance) * 100)

    if score >= 70:
        band = "Good"
    elif score >= 45:
        band = "Moderate skew"
    else:
        band = "High skew"

    return score, band


def reduce_payload_v2(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    checklist_rows_raw = data.get("CHECKLIST_ROWS", [])
    matrix_rows_raw = data.get("MATRIX_ROWS", [])

    checklist_meta = [normalize_checklist_row(r, i) for i, r in enumerate(checklist_rows_raw, start=1)]
    matrix_meta = [normalize_matrix_row(r, i) for i, r in enumerate(matrix_rows_raw, start=1)]

    check_order: dict[str, int] = {}
    for idx, row in enumerate(checklist_meta):
        check_order[row["Check ID"]] = idx

    all_check_ids = [r["Check ID"] for r in checklist_meta]
    check_id_set = set(all_check_ids)

    check_to_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    check_to_acrefs: dict[str, set[str]] = defaultdict(set)
    check_to_case_types: dict[str, set[str]] = defaultdict(set)
    ac_to_checks: dict[str, set[str]] = defaultdict(set)
    ac_priority_rank: dict[str, int] = {}
    ac_priority_label: dict[str, str] = {}
    case_type_to_checks: dict[str, set[str]] = defaultdict(set)

    for mrow in matrix_meta:
        ac_ref = mrow["AC Ref"]
        mapped_ids = [cid for cid in parse_mapping_ids(mrow["Checklist Mapping"]) if cid in check_id_set]
        if not mapped_ids:
            continue

        pr_label = mrow.get("Priority", "")
        pr_rank = PRIORITY_WEIGHT.get(pr_label, 0)
        if pr_rank > ac_priority_rank.get(ac_ref, -1):
            ac_priority_rank[ac_ref] = pr_rank
            ac_priority_label[ac_ref] = pr_label

        case_type = mrow.get("Case Type", "").strip().lower()

        for cid in mapped_ids:
            check_to_rows[cid].append(mrow)
            check_to_acrefs[cid].add(ac_ref)
            ac_to_checks[ac_ref].add(cid)
            if case_type:
                check_to_case_types[cid].add(case_type)
                case_type_to_checks[case_type].add(cid)

    check_scores: dict[str, int] = {}
    for cid in all_check_ids:
        linked_rows = check_to_rows.get(cid, [])
        if not linked_rows:
            check_scores[cid] = 0
            continue

        row_scores = [score_matrix_row(r) for r in linked_rows]
        max_row = max(row_scores)
        avg_row = sum(row_scores) / len(row_scores)

        linked_ac = check_to_acrefs.get(cid, set())
        unique_ac_count = sum(1 for ac in linked_ac if len(ac_to_checks.get(ac, set())) == 1)
        high_ac_count = sum(1 for ac in linked_ac if ac_priority_label.get(ac) == "High")
        case_diversity = len(check_to_case_types.get(cid, set()))

        score = int(round(max_row + (0.35 * avg_row) + (30 * unique_ac_count) + (10 * high_ac_count) + (4 * case_diversity)))
        check_scores[cid] = score

    total_checks = len(all_check_ids)
    target_keep = max(MIN_CHECKS_KEPT, math.ceil(total_checks * TARGET_KEEP_RATIO))

    required_ac_refs = set(ac_to_checks.keys())
    required_core_case_types = {
        ct for ct in CORE_CASE_TYPES if ct in case_type_to_checks and case_type_to_checks[ct]
    }

    kept: set[str] = set(all_check_ids)
    dropped: set[str] = set()

    # Deterministic order: lower score dropped first, then later checklist position first.
    candidates = sorted(all_check_ids, key=lambda cid: (check_scores.get(cid, 0), -check_order[cid], cid))

    def can_drop(cid: str, kept_now: set[str]) -> bool:
        if len(kept_now) - 1 < target_keep:
            return False

        kept_after = kept_now - {cid}

        # Hard constraint 1: every AC Ref retains at least one mapped checklist check.
        for ac_ref in check_to_acrefs.get(cid, set()):
            mapped = ac_to_checks.get(ac_ref, set())
            if mapped and not (mapped & kept_after):
                return False

        # Hard constraint 2: keep at least one check for each core case family present.
        for case_type in required_core_case_types:
            if not (case_type_to_checks.get(case_type, set()) & kept_after):
                return False

        return True

    for cid in candidates:
        if len(kept) <= target_keep:
            break
        if can_drop(cid, kept):
            kept.remove(cid)
            dropped.add(cid)

    reduced = copy.deepcopy(data)
    reduced["CHECKLIST_ROWS"] = [
        row for row, meta in zip(checklist_rows_raw, checklist_meta) if meta["Check ID"] in kept
    ]
    reduced["MATRIX_ROWS"] = update_matrix_rows(copy.deepcopy(matrix_rows_raw), dropped)

    kept_count = len(reduced["CHECKLIST_ROWS"])
    removed_pct = round(((total_checks - kept_count) / total_checks) * 100) if total_checks else 0

    reduced["COVERAGE_SUMMARY"] = (
        f"[Reduced V2 ~{removed_pct}% — {kept_count}/{total_checks} checks retained; "
        f"AC and core-case coverage guardrails enforced] " + str(data.get("COVERAGE_SUMMARY", ""))
    )

    epic_key = str(data.get("EPIC_KEY", "EPIC-KEY"))
    epic_slug = str(data.get("EPIC_SLUG", ""))
    reduced["OUTPUT_PATH"] = f"{OUTPUT_DIR}/{epic_key}-{epic_slug}.xlsx"

    ac_before = required_ac_refs
    ac_after = set()
    high_before = {ac for ac, pr in ac_priority_label.items() if pr == "High"}
    high_after = set()

    for i, mrow in enumerate(reduced["MATRIX_ROWS"], start=1):
        nr = normalize_matrix_row(mrow, i)
        ac_ref = nr["AC Ref"]
        mapped_ids = parse_mapping_ids(nr["Checklist Mapping"])
        if mapped_ids:
            ac_after.add(ac_ref)
            if ac_ref in high_before:
                high_after.add(ac_ref)

    ac_coverage_pct = round((len(ac_after) / len(ac_before)) * 100, 1) if ac_before else 100.0
    high_coverage_pct = round((len(high_after) / len(high_before)) * 100, 1) if high_before else 100.0

    before_prio = priority_counter(matrix_rows_raw)
    after_prio = priority_counter(reduced["MATRIX_ROWS"])
    before_rel_score, before_rel_band = priority_reliability_kpi(before_prio)
    after_rel_score, after_rel_band = priority_reliability_kpi(after_prio)

    target_remove = max(0, total_checks - target_keep)
    actual_remove = len(dropped)

    dropped_labels = [
        f"{meta['Check ID']} [{meta['Section'] or 'N/A'}]"
        for meta in checklist_meta
        if meta["Check ID"] in dropped
    ]

    kpi = {
        "epic_key": epic_key,
        "original_checks": total_checks,
        "kept_checks": kept_count,
        "dropped_checks": actual_remove,
        "removed_pct": removed_pct,
        "target_remove": target_remove,
        "target_hit": actual_remove == target_remove,
        "ac_before": len(ac_before),
        "ac_after": len(ac_after),
        "ac_coverage_pct": ac_coverage_pct,
        "high_ac_before": len(high_before),
        "high_ac_after": len(high_after),
        "high_ac_coverage_pct": high_coverage_pct,
        "matrix_before": len(matrix_rows_raw),
        "matrix_after": len(reduced["MATRIX_ROWS"]),
        "core_case_constraints": ", ".join(sorted(required_core_case_types)) if required_core_case_types else "none",
        "priority_before": dict(before_prio),
        "priority_after": dict(after_prio),
        "priority_reliability_before": f"{before_rel_score} ({before_rel_band})",
        "priority_reliability_after": f"{after_rel_score} ({after_rel_band})",
        "dropped_labels": dropped_labels,
    }

    return reduced, kpi


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


def write_batch_summary(kpis: list[dict[str, Any]], output_dir: str) -> None:
    total_original = sum(int(k["original_checks"]) for k in kpis)
    total_kept = sum(int(k["kept_checks"]) for k in kpis)
    removed_total = total_original - total_kept
    removed_pct = round((removed_total / total_original) * 100, 1) if total_original else 0.0

    total_ac_before = sum(int(k["ac_before"]) for k in kpis)
    total_ac_after = sum(int(k["ac_after"]) for k in kpis)
    total_high_before = sum(int(k["high_ac_before"]) for k in kpis)
    total_high_after = sum(int(k["high_ac_after"]) for k in kpis)

    ac_cov_batch = round((total_ac_after / total_ac_before) * 100, 1) if total_ac_before else 100.0
    high_cov_batch = round((total_high_after / total_high_before) * 100, 1) if total_high_before else 100.0

    target_hit_count = sum(1 for k in kpis if k["target_hit"])

    lines = [
        "# UAT Reducer V2 Batch Summary",
        "",
        "Deterministic reducer with matrix-join scoring and hard constraints:",
        "- Preserve at least one checklist check per AC Ref.",
        "- Preserve at least one checklist check for each core case type present (functional/regression/integration).",
        "",
        "## Batch KPI",
        "",
        f"- Epics processed: {len(kpis)}",
        f"- Checks: {total_original} -> {total_kept} ({removed_total} removed, {removed_pct}% removed)",
        f"- AC coverage retained: {total_ac_after}/{total_ac_before} ({ac_cov_batch}%)",
        f"- High-priority AC coverage retained: {total_high_after}/{total_high_before} ({high_cov_batch}%)",
        f"- Target reduction hit exactly: {target_hit_count}/{len(kpis)} epics",
        "",
        "## Per-Epic KPI",
        "",
        "| Epic | Checks (orig->kept) | Removed % | AC coverage % | High AC coverage % | Target hit | Priority reliability (before->after) |",
        "|---|---:|---:|---:|---:|---|---|",
    ]

    for k in sorted(kpis, key=lambda row: str(row["epic_key"])):
        lines.append(
            "| {epic} | {orig}->{kept} | {removed}% | {ac_cov}% | {high_cov}% | {hit} | {prio_before} -> {prio_after} |".format(
                epic=k["epic_key"],
                orig=k["original_checks"],
                kept=k["kept_checks"],
                removed=k["removed_pct"],
                ac_cov=k["ac_coverage_pct"],
                high_cov=k["high_ac_coverage_pct"],
                hit="Yes" if k["target_hit"] else "No (guardrail constrained)",
                prio_before=k["priority_reliability_before"],
                prio_after=k["priority_reliability_after"],
            )
        )

    lines += [
        "",
        "## Dropped Checks",
        "",
        "| Epic | Core case guardrails | Dropped checks (Check ID [Section]) |",
        "|---|---|---|",
    ]

    for k in sorted(kpis, key=lambda row: str(row["epic_key"])):
        dropped_cell = ", ".join(k["dropped_labels"]) if k["dropped_labels"] else "—"
        lines.append(f"| {k['epic_key']} | {k['core_case_constraints']} | {dropped_cell} |")

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

    all_kpis: list[dict[str, Any]] = []

    for payload_path in payloads:
        epic_key = os.path.basename(os.path.dirname(payload_path))
        print(f"\n{epic_key}")

        with open(payload_path, encoding="utf-8") as f:
            data = json.load(f)

        try:
            reduced_data, kpi = reduce_payload_v2(data)
        except ValueError as e:
            print(f"  ERROR: {e}")
            continue

        print(
            f"  {kpi['original_checks']} checks -> {kpi['kept_checks']} kept, "
            f"{kpi['dropped_checks']} dropped ({kpi['removed_pct']}%)"
        )
        print(
            f"  AC coverage: {kpi['ac_after']}/{kpi['ac_before']} ({kpi['ac_coverage_pct']}%), "
            f"High AC: {kpi['high_ac_after']}/{kpi['high_ac_before']} ({kpi['high_ac_coverage_pct']}%)"
        )
        print(
            "  Priority reliability: "
            f"{kpi['priority_reliability_before']} -> {kpi['priority_reliability_after']}"
        )
        if kpi["dropped_labels"]:
            print(f"  Dropped: {', '.join(kpi['dropped_labels'])}")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(reduced_data, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name

        try:
            run_generator(tmp_path)
        finally:
            os.unlink(tmp_path)

        all_kpis.append(kpi)

    if not all_kpis:
        print("\nNo epic was reduced successfully.")
        sys.exit(1)

    total_original = sum(int(k["original_checks"]) for k in all_kpis)
    total_kept = sum(int(k["kept_checks"]) for k in all_kpis)
    removed_total = total_original - total_kept
    removed_pct = round((removed_total / total_original) * 100, 1) if total_original else 0.0

    print(f"\nDone. {total_original} -> {total_kept} checks across all epics ({removed_pct}% removed).")
    print(f"Output: {OUTPUT_DIR}/")

    write_batch_summary(all_kpis, os.path.join(os.path.dirname(__file__), OUTPUT_DIR))


if __name__ == "__main__":
    main()
