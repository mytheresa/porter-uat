"""
UAT Test Plan XLSX Generator
============================
Canonical script for generating simplified UAT test plan workbooks.

Usage (agent-invoked via virtualenv):
    python3 -m venv /tmp/xlsx-venv
    /tmp/xlsx-venv/bin/pip install openpyxl -q
    /tmp/xlsx-venv/bin/python3 .github/scripts/generate-test-plan-xlsx.py

Rules enforced by this script (do not change without updating the skill):
- Header row: dark blue fill, white bold font — data rows: plain white
- No alternating row colours
- Result and Notes columns always empty (left for tester)
- No Status column in Coverage Matrix
- No separate brand coverage check row
- Overview includes Epic created by (from Jira creator field), NOT a "Created by" generator row
- Stories excluded (non-UI-testable) row always present after Stories in scope
- Column widths and row heights auto-fit from content

Agent instructions:
  1. Fill in all sections marked  ── AGENT: FILL ──
  2. Do not change the helper functions or styling constants
  3. Run with /tmp/xlsx-venv/bin/python3
  4. Output path follows: uat-test-plans/<EPIC_KEY>/<slug>.simplified-flows.xlsx
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os

# ── Styling constants (do not modify) ────────────────────────────────────────
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT  = Font(bold=True, color="FFFFFF", size=10)
BODY_FONT    = Font(size=10)
WRAP         = Alignment(wrap_text=True, vertical="top")
CENTER       = Alignment(horizontal="center", vertical="top", wrap_text=True)
THIN         = Side(style="thin", color="B8B8B8")
BORDER       = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
LINE_HEIGHT  = 15  # points per line at size 10


def style_header(ws, row, cols):
    for col in range(1, cols + 1):
        c = ws.cell(row=row, column=col)
        c.fill = HEADER_FILL; c.font = HEADER_FONT
        c.alignment = CENTER; c.border = BORDER


def style_row(ws, row, cols):
    for col in range(1, cols + 1):
        c = ws.cell(row=row, column=col)
        c.font = BODY_FONT; c.alignment = WRAP; c.border = BORDER


def autofit(ws, min_col_width=8, max_col_width=60):
    """Auto-fit column widths and row heights from cell content."""
    col_widths = {}; row_lines = {}
    for row in ws.iter_rows():
        for cell in row:
            if not cell.value:
                continue
            lines = str(cell.value).split("\n")
            col = cell.column; r = cell.row
            longest = max(len(l) for l in lines)
            col_widths[col] = max(col_widths.get(col, min_col_width), longest)
            row_lines[r]    = max(row_lines.get(r, 1), len(lines))
    for col, w in col_widths.items():
        ws.column_dimensions[get_column_letter(col)].width = min(w + 2, max_col_width)
    for r, lines in row_lines.items():
        ws.row_dimensions[r].height = max(LINE_HEIGHT, lines * LINE_HEIGHT)


# ════════════════════════════════════════════════════════════════════════════
# ── AGENT: FILL — Epic metadata ──────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════
EPIC_KEY        = "G2-XXXXX"               # e.g. "G2-19278"
EPIC_SLUG       = "epic-slug"              # e.g. "plp-colour-linking"
PLAN_TITLE      = f"{EPIC_KEY} UAT — ..."  # e.g. "G2-19278 UAT — PLP Colour Swatches"
GENERATED_DATE  = "YYYY-MM-DD"
EPIC_SUMMARY    = f"{EPIC_KEY} — ..."      # e.g. "G2-19278 — PLP | Colour linking"
EPIC_STATUS     = "Done"                   # from Jira status field
EPIC_CREATED_BY = "Surname, Name || Affiliation (email@domain.com)"  # from Jira creator field
COMPONENT       = "..."                    # from Jira components field
TIMEBOX         = "~30-45 minutes"
COVERAGE_SUMMARY = "X checks (...)"
STORIES_IN_SCOPE = "G2-XXXXX (FE: ...), G2-YYYYY (BE: ...)"
STORIES_EXCLUDED = "G2-ZZZZZ (BE: ...) — reason why excluded (non-UI-testable AC)"
OUT_OF_SCOPE    = "..."
DEV_EVIDENCE    = "..."
GAPS_SUMMARY    = "GAP-01: ...; GAP-02: ..."

OUTPUT_PATH     = f"uat-test-plans/{EPIC_KEY}/{EPIC_SLUG}.simplified-flows.xlsx"


# ── AGENT: FILL — Sheet 1: Checklist rows ─────────────────────────────────────
# Format: (check_id, section, check, how_to_verify, pass_criteria, "", "")
# Result (col 6) and Notes (col 7) are ALWAYS empty strings — never pre-populate
CHECKLIST_ROWS = [
    # ("CHK-01", "Section Name", "Verify ...",
    #  "1. Step one.\n2. Step two.\n3. Step three.",
    #  "Pass criteria text.", "", ""),
]


# ── AGENT: FILL — Sheet 3: Coverage Matrix rows ───────────────────────────────
# Format: (coverage_id, jira_source, ac_ref, capability, priority,
#          checklist_mapping, ac_fidelity, evidence_notes, evidence_availability, case_type)
# No Status column.
MATRIX_ROWS = [
    # ("EPICKEY_TC01", "G2-XXXXX", "AC1", "Capability description", "Medium",
    #  "CHK-01", "Exact", "PR #N merged in repo (url)", "Available", "AC"),
]


# ── AGENT: FILL — Sheet 4: Exploratory observations ──────────────────────────
# Format: (obs_id, source_type, jira_source, summary, how_to_validate,
#          expected_observation, impact, linked_coverage_ids, evidence_notes, status)
# status is always "OBSERVE"
# If no observations: one row with ("OBS-01", "N/A", "N/A", "None identified from explicit evidence", ...)
EXPLORATORY_ROWS = [
    # ("OBS-01", "Comment", "G2-XXXXX", "Observation summary...",
    #  "How to validate manually...", "Expected result...", "Impact level...",
    #  "EPICKEY_TC01", "Evidence note...", "OBSERVE"),
]


# ════════════════════════════════════════════════════════════════════════════
# ── Workbook generation (do not modify below this line) ──────────────────────
# ════════════════════════════════════════════════════════════════════════════
wb = Workbook()

# Sheet 1: Checklist
ws1 = wb.worksheets[0]
ws1.title = "Checklist"
ws1.freeze_panes = "A2"
checklist_headers = ["Check ID", "Section", "Check", "How to Verify", "Pass Criteria", "Result", "Notes"]
for col, h in enumerate(checklist_headers, 1):
    ws1.cell(row=1, column=col, value=h)
style_header(ws1, 1, len(checklist_headers))
for r_idx, row_data in enumerate(CHECKLIST_ROWS, 2):
    for c_idx, val in enumerate(row_data, 1):
        ws1.cell(row=r_idx, column=c_idx, value=val)
    style_row(ws1, r_idx, len(checklist_headers))
autofit(ws1)

# Sheet 2: Overview
ws2 = wb.create_sheet("Overview")
overview_rows = [
    ("Plan",                               PLAN_TITLE),
    ("Generated",                          GENERATED_DATE),
    ("Epic",                               EPIC_SUMMARY),
    ("Epic Status",                        EPIC_STATUS),
    ("Epic created by",                    EPIC_CREATED_BY),
    ("Component",                          COMPONENT),
    ("Application URL — NAP",             "https://acceptance.net-a-porter.com/en-de"),
    ("Application URL — MRP",             "https://acceptance.mrporter.com/en-de"),
    ("Audience",                           "Business quick-check"),
    ("Timebox",                            TIMEBOX),
    ("Coverage",                           COVERAGE_SUMMARY),
    ("Stories in scope",                   STORIES_IN_SCOPE),
    ("Stories excluded (non-UI-testable)", STORIES_EXCLUDED),
    ("Out of scope",                       OUT_OF_SCOPE),
    ("Dev Evidence",                       DEV_EVIDENCE),
    ("Gaps",                               GAPS_SUMMARY),
]
for col, h in enumerate(["Field", "Value"], 1):
    ws2.cell(row=1, column=col, value=h)
style_header(ws2, 1, 2)
for r_idx, (field, val) in enumerate(overview_rows, 2):
    ws2.cell(row=r_idx, column=1, value=field)
    ws2.cell(row=r_idx, column=2, value=val)
    style_row(ws2, r_idx, 2)
autofit(ws2)

# Sheet 3: Coverage Matrix
ws3 = wb.create_sheet("Coverage Matrix")
ws3.freeze_panes = "A2"
matrix_headers = [
    "Coverage ID", "Jira Source", "AC Ref", "Capability / Requirement",
    "Priority", "Checklist Mapping",
    "AC Fidelity", "Evidence Notes", "Evidence Availability", "Case Type",
]
for col, h in enumerate(matrix_headers, 1):
    ws3.cell(row=1, column=col, value=h)
style_header(ws3, 1, len(matrix_headers))
for r_idx, row_data in enumerate(MATRIX_ROWS, 2):
    for c_idx, val in enumerate(row_data, 1):
        ws3.cell(row=r_idx, column=c_idx, value=val)
    style_row(ws3, r_idx, len(matrix_headers))
autofit(ws3)

# Sheet 4: Exploratory and Design Obs
ws4 = wb.create_sheet("Exploratory and Design Obs")
ws4.freeze_panes = "A2"
obs_headers = [
    "Observation ID", "Source Type", "Jira Source", "Observation Summary",
    "How to Validate Manually", "Expected Observation", "Impact",
    "Linked Coverage IDs", "Evidence Notes", "Status",
]
for col, h in enumerate(obs_headers, 1):
    ws4.cell(row=1, column=col, value=h)
style_header(ws4, 1, len(obs_headers))
for r_idx, row_data in enumerate(EXPLORATORY_ROWS, 2):
    for c_idx, val in enumerate(row_data, 1):
        ws4.cell(row=r_idx, column=c_idx, value=val)
    style_row(ws4, r_idx, len(obs_headers))
autofit(ws4)

# Save
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
wb.save(OUTPUT_PATH)
print(f"Saved: {OUTPUT_PATH}")
