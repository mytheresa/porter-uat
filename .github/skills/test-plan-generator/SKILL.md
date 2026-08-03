---
name: test-plan-generator
description: Process context evidence, Confluence docs, and pre-filtered Jira metadata into a structured JSON payload silently, and execute generate-test-plan-xlsx.py using an absolute script path to produce the final Excel file.
user-invocable: true
---
# Test Plans Generator & Python Bridge

## Purpose

Acts as the data transformation bridge between evidence extraction and the deterministic workbook script. It converts Acceptance Criteria (AC), metadata, docs, and PR evidence into a strict JSON payload consumed by `$(pwd)/.github/scripts/generate-test-plan-xlsx.py`.

## Evidence Priority Policy

- Primary source of truth: Epic/Story Acceptance Criteria and user-story description.
- Secondary evidence allowed: Jira comments, PRs/commits, and linked docs (Confluence/Figma/external docs).
- Secondary evidence may refine or clarify reproduction steps and expected outcomes, but must never contradict or override AC intent.
- If secondary evidence conflicts with AC, keep AC as canonical and record the conflict in gaps/inconsistencies.

## Input

- Array of chunked JSON story objects (or paths to `/tmp/chunk_<EPIC_KEY>_*.json` files) generated via the chunked Map-Reduce orchestrator workflow.

## Mandatory Workflow

1. **Scenario & Checklist Synthesizer:**

   - Ingest all batched story chunks for the Epic.
   - Parse UI-testable story AC first, then enrich with Confluence BDD notes, comments, and PR evidence as secondary context.
   - Map PRs/comments/test notes directly to AC scenarios as supporting evidence only.
   - Formulate atomic verification checks for `CHECKLIST_ROWS` and map parity to `MATRIX_ROWS`.
   - **Checklist Leanness Rule (mandatory):** `CHECKLIST_ROWS` must cover only the highest-priority business user journeys. Target **8–12 checks** (hard cap: 15 for the most complex Epics). The full checklist must be executable in **15–30 minutes** by a business user. Collapse all of the following into a single check per user journey: device variants (desktop/mobile), cancel/close modal behaviour, and success-notification timing. Exclude entirely: brand-specific references (do not mention NAP, MRP, or any brand name — the UAT is run against one target environment at a time as defined by `TARGET_URLS`), Safari-specific rendering, raw localisation string checks, isolated cancel/X behaviour, developer-level or API-level verification, and any negative/boundary case already captured in `MATRIX_ROWS`. Move those concerns to `MATRIX_ROWS` `Inconsistencies` or `EXPLORATORY_ROWS` instead.
2. **Silent JSON Payload Generation (`/tmp/data_payload_<EPIC_KEY>.json`):**

   - Consolidate all transformed chunk rows into a single flat JSON file saved directly to disk at `/tmp/data_payload_<EPIC_KEY>.json`.
   - **Strict Token Rule:** Do NOT stream or render the JSON content in chat prose or tool call outputs. Write silently to file system.
3. **Workbook Execution:**

    - Ensure the venv and dependencies are ready before running any Python command:
       ```bash
       source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate && pip install openpyxl -q)
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
