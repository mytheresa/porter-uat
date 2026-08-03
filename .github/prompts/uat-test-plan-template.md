# Unified Business UAT Queue Processor Template

## 🛠️ Execution Runbook

### Automated Execution (Batch Mode)
Run `python3 auto_copilot.py` from your terminal. The script automatically pops Epics from `epics_queue.txt`, triggers Copilot for each target Epic key, waits for workbook creation on disk, and manages `/clear` context resets between runs.

### Manual Execution (Single Epic / Debugging)
To process or debug a single Epic manually:
1. Open a fresh Copilot chat thread (or type `/clear`).
2. Paste the following prompt, replacing `<EPIC_KEY>` with your target Jira key:
   > "Run .github/prompts/uat-test-plan-template.md for Epic '<EPIC_KEY>' and generate /tmp/data_payload_<EPIC_KEY>.json before executing the Python generator script."
3. Wait for the agent to finish generating `uat-test-plans/<EPIC_KEY>-<slug>.xlsx`.
4. Type `/clear` before processing another Epic.

---

## Role

Act as a business user of an e-commerce website validating functionality on target environments (e.g., brand acceptance sites).

## Goal

Generate a reproducible UAT test plan iteratively starting from an Epic key and linked user stories for business quick-checks.

## Evidence Policy

- Primary source of truth: Epic/Story Acceptance Criteria and user-story description.
- Secondary evidence allowed: Jira comments, PR/commit evidence, and linked docs.
- Use secondary evidence only to clarify test paths/expected outcomes; do not let it override AC intent.
- If secondary evidence conflicts with AC, keep AC as canonical and report the conflict under gaps/inconsistencies.
- Development evidence must be considered `Available` when PR/commit links are found either directly via GitHub MCP or indirectly via Jira story metadata (description, comments, issuelinks, or remote links).
- Trigger-driven enrichment policy: Jira-first by default. Pull Confluence/GitHub only when at least one trigger fires for a story.

## Token Efficiency Rules

- Keep tool calls retrieval-first and minimal: request only fields required for decisions and mapping.
- Use two-pass retrieval: (1) minimal metadata/AC to classify scope, (2) fetch comments/docs/PR detail only for in-scope UI stories.
- Do not render large raw tool payloads in chat; summarize and write structured artifacts to `/tmp` files.
- Keep final chat output compact while preserving the required 5-section order.
- Do not call GitHub MCP for every UI story by default. Call it only for trigger-matched stories.

## Checklist Depth Rule (Future Runs)

- Generate a balanced `CHECKLIST_ROWS` set that does not miss critical business steps and does not over-compress distinct validations.
- Target **8–12 checks** for typical Epics; allow up to **15 checks** only when complexity/risk justifies it.
- Cover the critical business outcomes expressed by AC and risk context, but avoid forcing a fixed checklist template when a flow is not applicable.
- Keep checklist wording business-facing and environment-agnostic (no brand-name wording, no API/code-level steps).

## Inputs

- **Target Epic Key:** Explicit Epic key provided in prompt payload
- **Target Environment URLs:** `<TARGET_URLS>` (e.g., `https://acceptance.net-a-porter.com/en-de`, `https://acceptance.mrporter.com/en-de`)
- **Output Root Folder:** `uat-test-plans/`

## Mandatory Orchestration Workflow

You must execute the following workflow in exact order for **ONE Epic only**. Do not attempt to loop multiple Epics in a single chat session. Stop and report failure if any step fails. **Execute every step autonomously without asking the user for confirmation, approval, or clarification at any intermediate point. Never offer optional next steps mid-run. Proceed directly to the final output.**

1. **Queue Context:** Process the explicit Epic key supplied in the prompt. Do not attempt to read or modify `epics_queue.txt`.
2. **Preflight & Epic Map:** Invoke the `evidence-context` skill against the parent Epic ONLY to extract metadata (`creator`, `status`, `components`) and map the child story hierarchy. Categorize and separate all non-UI stories (e.g., backend-only logic, database migrations) into an exclusion array.
3. **Chunked Iterative Evidence Gathering (Map-Reduce):** 
   - Group UI-testable child stories into manageable batches (maximum **5 stories per chunk**).
   - For *each* child story in a chunk, invoke `evidence-context` individually with minimal retrieval first.
    - Classify trigger flags per story using this exact set:
       - `TRG-AC`: AC is partial, vague, or ambiguous.
       - `TRG-BRAND`: story touches cross-brand behavior/variance.
       - `TRG-RISK`: story maps to auth continuity, undo/delete integrity, or known regression clusters.
       - `TRG-REL`: release confidence explicitly requires code-level evidence.
    - Jira-first default path (no triggers): use Jira metadata/AC and lightweight Jira link scanning only; skip Confluence/GitHub retrieval.
    - Triggered path (any trigger true):
       - Pull Confluence only when recognized Confluence links are present and needed for ambiguity resolution.
       - Attempt GitHub MCP lookup for PR/commit evidence.
       - If GitHub fails or returns no hits, continue with Jira-link fallback and record outcome in existing evidence format.
    - Do not mark evidence unavailable for triggered stories until both GitHub and Jira-link fallback checks are completed.
   - Aggregate story evidence chunk-by-chunk into intermediate state files (`/tmp/chunk_<EPIC_KEY>_<batch_id>.json`) to prevent context window overflow.
4. **Plan Generation:** Invoke the `test-plan-generator` skill, pointing it to the chunked data files. The skill synthesizes the chunks into the final JSON payload at `/tmp/data_payload_<EPIC_KEY>.json`. Before running the generator, always ensure the venv and dependencies are ready using: `source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate && pip install openpyxl -q)`. Then execute `python3 $(pwd)/.github/scripts/generate-test-plan-xlsx.py --validate /tmp/data_payload_<EPIC_KEY>.json` for preflight quick-fail checks, and then `python3 $(pwd)/.github/scripts/generate-test-plan-xlsx.py /tmp/data_payload_<EPIC_KEY>.json` to generate the workbook. Halt and report if any of these commands fail.
5. **Final Assembly & Rendering:** Once plan generation completes:
   - Verify that the target Excel file exists at `uat-test-plans/<EPIC_KEY>-<slug>.xlsx`.
    - You MUST return the final chat response in this exact order and in compact form:
     1. Invocation Compliance Report (listing tools called and status).
     2. Preflight status (pass/fail based on evidence gathering).
     3. A 3-bullet executive summary of UAT coverage, including confirmation and the link to the saved XLSX file (`uat-test-plans/<EPIC_KEY>-<slug>.xlsx`).
     4. Coverage parity summary.
     5. Gaps and inconsistencies remarks.
    - Compactness limits: keep each section to concise bullets/tables only; avoid narrative paragraphs and avoid repeating raw tool data.
   - Dev evidence reporting rule: in the Invocation Compliance Report, include one short line with evidence-source basis (for example: `GitHub MCP`, `Jira comment GitHub URL`, `Jira remote link`).
   - Include a trigger summary line in the Invocation Compliance Report: `triggered stories`, `GitHub lookups executed`, `Confluence lookups executed`.
   - **CRITICAL INSTRUCTION:** Halt completely after output rendering.