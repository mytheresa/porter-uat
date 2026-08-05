---
name: test-plan-generator
description: Process context evidence, Confluence docs, and pre-filtered Jira metadata into a structured JSON payload silently, and execute generate-test-plan-xlsx.py using an absolute script path to produce the final Excel file.
user-invocable: true
---
# Test Plans Generator & Python Bridge

## Purpose

Bridge evidence extraction to the workbook script. Convert AC, metadata, docs, and PR evidence into the JSON payload consumed by `$(pwd)/.github/scripts/generate-test-plan-xlsx.py`.

## Evidence Priority Policy

- Primary source of truth: Epic/Story Acceptance Criteria and user-story description.
- Secondary evidence allowed: Jira comments, PRs/commits, and linked docs (Confluence/Figma/external docs).
- Secondary evidence may refine or clarify reproduction steps and expected outcomes, but must never contradict or override AC intent.
- If secondary evidence conflicts with AC, keep AC as canonical and record the conflict in gaps/inconsistencies.
- Trigger-driven enrichment: Confluence/GitHub are optional per-story enrichments, not defaults.

## Quick Wins

- If the epic has no UI-testable stories, emit the minimal excluded-story payload and stop.
- If no trigger fires, stay Jira-only and skip Confluence/GitHub.
- If coverage is already obvious from AC, do not expand evidence just to fill space.

## Input

- Array of chunked JSON story objects (or paths to `/tmp/chunk_<EPIC_KEY>_*.json` files) generated via the chunked Map-Reduce orchestrator workflow.

## Mandatory Workflow

1. **Scenario & Checklist Synthesizer:**

   - Ingest all batched story chunks.
   - Parse UI-testable AC first; use docs/comments/PRs only as secondary context.
   - Keep Jira-first behavior for non-trigger stories.
   - Map PRs/comments/test notes to AC scenarios only as supporting evidence.
   - Build atomic checks for `CHECKLIST_ROWS` with parity to `MATRIX_ROWS`.
   - Aim for **8–12 checks**; allow up to **15** for high-risk Epics.
   - Keep wording business-facing and session-friendly; move technical diagnostics to `MATRIX_ROWS` or `EXPLORATORY_ROWS`.
2. **Silent JSON Payload Generation (`/tmp/data_payload_<EPIC_KEY>.json`):**

   - Consolidate all transformed chunk rows into a single flat JSON file saved directly to disk at `/tmp/data_payload_<EPIC_KEY>.json`.
   - **Strict Token Rule:** Do NOT stream or render the JSON content in chat prose or tool call outputs. Write silently to file system.
3. **Workbook Execution:**

    - Ensure the workspace venv already exists and has dependencies installed before running any Python command:
       ```bash
       source .venv/bin/activate 2>/dev/null || { echo 'Missing .venv; create it once during setup, then rerun.'; exit 1; }
       python3 -c "import openpyxl,sys; print('NON_INTERACTIVE_OK', sys.executable)"
       ```
    - Execute preflight validation first (quick fail on bad payload):
       ```bash
       python3 $(pwd)/.github/scripts/generate-test-plan-xlsx.py --validate /tmp/data_payload_<EPIC_KEY>.json
       ```
    - If preflight passes, execute the Python generator script passing the specific payload argument:
     ```bash
     python3 $(pwd)/.github/scripts/generate-test-plan-xlsx.py /tmp/data_payload_<EPIC_KEY>.json
     ```

## JSON Payload Schema

The generated JSON file must contain these exact top-level keys for the Python script to consume:

### Overview Keys

- `EPIC_KEY`: Exact Jira Key
- `EPIC_SLUG`: Lowercase hyphenated slug
- `OUTPUT_PATH`: `uat-test-plans/{EPIC_KEY}-{EPIC_SLUG}.xlsx`
- `PLAN_TITLE`: `f"{EPIC_KEY} UAT — {Short Title}"`
- `GENERATED_DATE`: Current date in `YYYY-MM-DD`
- `EPIC_SUMMARY`: Summary string from Jira
- `EPIC_STATUS`: Exact Jira status string
- `EPIC_CREATED_BY`: Formatted creator string (used to populate the Checklist `Contact` column)
- `COMPONENT`: Jira component string (e.g., "Checkout", "N/A")
- `TARGET_URLS`: Environment URLs passed from context
- `TIMEBOX`: Estimated execution time
- `COVERAGE_SUMMARY`: Summary of total checks vs. stories
- `STORIES_IN_SCOPE`: Formatted list of UI-testable stories
- `STORIES_EXCLUDED`: Formatted list of non-UI-testable stories with justification
- `OUT_OF_SCOPE`: Non-UI items, third-party edge cases
- `DEV_EVIDENCE`: PR counts, branch status, or fallback source summary
- `GAPS_SUMMARY`: List of missing evidence or ambiguous AC items

### Data Rows (List of Objects)

Output JSON objects matching exact headers:

- `CHECKLIST_ROWS`: `Check ID`, `Contact`, `Section`, `Check`, `How to Verify`, `Pass Criteria`
  - **Pass Criteria formatting:** Use `\n` between sentences — one criterion per line. Do not use bullet symbols or dashes.
- `MATRIX_ROWS`: `Coverage ID`, `Jira Source`, `AC Ref`, `Capability`, `Priority`, `Checklist Mapping`, `AC Fidelity`, `Evidence Notes`, `Evidence Availability`, `Case Type`, `Inconsistencies`
- `EXPLORATORY_ROWS`: `Observation ID`, `Source Type`, `Jira Source`, `Summary`, `How to Validate`, `Expected Observation`, `Impact`, `Linked Coverage IDs`, `Evidence Notes`

## Non-Negotiables

- **Silent Payload Creation:** Write directly to disk at `/tmp/data_payload_<EPIC_KEY>.json`.
- **Matrix Parity:** Every UI-testable story AC must have at least one corresponding entry in `MATRIX_ROWS` and `CHECKLIST_ROWS`.
- **Strict Execution:** Execute `$(pwd)/.github/scripts/generate-test-plan-xlsx.py` with the explicit file path argument to produce the `.xlsx` file before responding.
- **Preflight Required:** Always run `--validate` against the payload before workbook generation and halt on any validation error.
