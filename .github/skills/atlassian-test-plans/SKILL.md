
`openpyxlopenpyxl`
---
name: atlassian-test-plans
description: Create one simplified manual UAT checklist per Jira Epic using only Atlassian MCP evidence, with a mandatory canonical coverage matrix, strict traceability checks, and a separate exploratory/design observations sheet.
user-invocable: true
---
# Atlassian Test Plan Simplified Output

Compatibility note:

- Legacy identifier: atlassian-test-plan-triple-output

## Purpose

Generate one simplified manual plan per Epic while preserving full traceability to a canonical coverage matrix.

Required output set:

1. Simplified checklist (quick validation)
2. Canonical coverage matrix
3. Exploratory/design observations (separate, evidence-backed)

The matrix remains the source of truth and the checklist must map to it with no gaps.

Default prompt template

- `.github/prompts/atlassian-mcp-uat-triple-business-template.md`

## Source Rules

Use only explicit Atlassian MCP evidence linked to the Epic:

- Epic metadata and description
- Linked issues (stories/tasks/bugs/subtasks)
- Acceptance Criteria (primary source of truth)
- Development evidence (PR/commit/branch/build data when exposed)
- Linked docs/design references (Confluence/official docs)

Do not invent flows, environments, or expected behavior.

UI-testability gate (mandatory before including any story/task):

- Before adding a story to scope, check whether its AC can be reproduced manually by a person on the UI.
- If ALL AC items are backend-only (API contracts, data pipeline, indexing, infrastructure) with no observable UI outcome: **exclude the story entirely** from checklist, matrix, and "Stories in scope". List it under "Stories excluded (non-UI-testable)" in the Overview instead.
- If a story has MIXED AC (some UI, some BE): include only the UI-reproducible AC items; note the excluded BE items as out of scope.

AC-first policy:

- AC drives required scenarios.
- Additional evidence-backed scenarios are allowed as `Exploratory` only.
- Exploratory scenarios must not change AC intent.

Deterministic fallbacks:

- Missing explicit PR/Commit in MCP => `Evidence Unavailable`

## Inputs Required

- Jira Epic key(s)
- Target audience (default: Business)
- In-scope environment(s)/brand(s)
- Severity taxonomy
- Coverage ID strategy (preserve existing IDs; else `EPICKEY_TCxx`)
- Output root: `uat-test-plans`
- Per-Epic folder: `uat-test-plans/<EPIC_KEY>/`

## Team Defaults

- Batch processing: enabled
- Output mode: Markdown + XLSX (mandatory)
- Scope: UI-manual scenarios
- AC/design handling: merged
- Output order: Matrix, Simplified Checklist

## Output Contract (Per Epic)

Create all files under `uat-test-plans/<EPIC_KEY>/`.

Markdown files:

1. `epic-slug.simplified-flows.md`
2. `epic-slug.coverage-matrix.md`

Workbook files (mandatory):

1. `epic-slug.simplified-flows.xlsx`

Workbook sheet contract:

1. `Checklist`
2. `Overview`
3. `Coverage Matrix`
4. `Exploratory and Design Observations`

Checklist column order:

1. `Check ID`
2. `Section`
3. `Check`
4. `How to Verify`
5. `Pass Criteria`
6. `Result`
7. `Notes`

## Canonical Coverage Matrix

Build first, then reuse in all plans.

Required columns:

- Coverage ID
- Jira Source
- Acceptance Criteria Ref
- Capability / Requirement
- Priority
- Checklist Mapping
- AC Fidelity (Exact / Partial / Missing)
- Evidence Notes
- Evidence Availability (Available / Evidence Unavailable)
- Case Type (AC / Exploratory)

Consistency checks:

- Every matrix row appears in the checklist
- No orphan checklist scenarios
- The checklist cannot drop matrix rows
- Exploratory rows must include explicit evidence reference(s)
- Exploratory/design observations are listed in a separate section and Sheet 4
- Exploratory/design observations do not replace AC matrix rows

## Plan Requirements

Simplified checklist must include:

- Timeboxed checklist
- One line per matrix row or explicit merged-ID row
- Success goal per checklist item/group
- Failure goal per checklist item/group
- Pass criteria in plain language
- Minimal execution notes
- Traceability line
- Separate "Exploratory and Design Observations" section for non-AC checks

## Orchestration Gates (Mandatory)

Required skill invocation:

- `atlassian-development-evidence-github`

Preflight:

- One Jira Epic read must succeed before generation (mandatory).
- Confluence read is conditional: only execute if the Epic or any linked issue contains an explicit Confluence doc link. Skip silently if none found — do not block generation.

If invocation or preflight fails:

- Stop generation
- Return failure reason(s)

Invocation compliance report format:

- Required Skill: name
- Invocation Status: Invoked / Not Invoked
- Evidence: tool call or step reference

## Process

1. Run preflight (Jira + Confluence)
2. Gather Epic and linked issue evidence
3. Invoke `atlassian-development-evidence-github` for linked issues
4. Extract AC and explicit requirements
5. Build canonical matrix
6. Generate the simplified checklist only
7. Validate parity, AC coverage, and evidence statuses
8. Return in order:

- invocation compliance report
- canonical coverage matrix
- Simplified checklist
- parity summary
- gaps/inconsistencies remarks

## Gap/Consistency Remarks

Use these tags:

- `GAP`
- `INCONSISTENCY`
- `DOC_DRIFT`
- `EVIDENCE_UNAVAILABLE`

Each remark must include:

- Source key/link
- Impacted Coverage ID(s)
- Why it is a gap/inconsistency
- Clarification question

## Token-Efficient Execution Profile

- Prefer targeted Jira fields:
  - Epic: `summary,description,status,issuetype,issuelinks,creator`
  - Linked issues: `summary,description,status,issuetype,issuelinks,subtasks,comment,attachment,creator`
- Resolve Epic-link and Development/devstatus fields semantically from Jira `names` and `schema`.
- Use `fields=["*all"]` only when targeted fields are insufficient
- Query direct Epic children first; expand second-order links only when AC/dependencies require it
- Confluence mode: `bodyMode=text`, `maxBodyChars` 1500-3000
- Keep evidence notes compact (key + link), no raw payload dumps
- Avoid duplicate retrieval of the same issue/doc in one run

## XLSX Generation

Use the canonical script at `.github/scripts/generate-test-plan-xlsx.py`.

Runtime setup (always use virtualenv):

```
python3 -m venv /tmp/xlsx-venv
/tmp/xlsx-venv/bin/pip install openpyxl -q
/tmp/xlsx-venv/bin/python3 .github/scripts/generate-test-plan-xlsx.py
```

Agent workflow:

1. Read the script — fill in all sections marked `── AGENT: FILL ──` with Epic-specific data.
2. Do not modify helper functions or styling constants.
3. Run via virtualenv to produce the xlsx.
4. Output path: `uat-test-plans/<EPIC_KEY>/<slug>.simplified-flows.xlsx`

## Non-Negotiables

- Manual reproducibility
- Numbered steps + bullet expected results
- No non-Atlassian assumptions
- Coverage parity between matrix and the checklist
- Do not create a separate brand coverage check. Brand scope is a scope note in Overview only.
- Exclude backend-only stories with no UI-reproducible AC from checklist and matrix scope.
