# Unified Business UAT Queue Processor Template

## Fast Rules

- AC is canonical; secondary evidence only clarifies.
- Default to Jira-only. Pull Confluence/GitHub only when a trigger fires.
- Quick wins: if the epic has no UI-testable stories, or the workbook already exists, stop early with the minimal result.
- Use two passes: classify first, enrich only when needed.
- Final chat output: status + artifact paths only, except in batch mode when explicitly instructed to skip final rendering.

## Mandatory Orchestration Workflow

Execute exactly one Epic key. Stop on failure. No prompts.

1. Queue Context
   - Process the explicit Epic key from the prompt.
   - Do not read or modify `epics_queue.txt`.

2. Preflight And Epic Map
  - Invoke `evidence-context` for the parent Epic only.
  - Capture creator, status, components, and child stories.
  - Mark backend-only, migration, and evaluation stories as excluded.

3. Chunked Evidence Gathering (Map-Reduce)
   - Group UI-testable stories in batches of **6-8**.
   - For each child story, run `evidence-context` with minimal retrieval first.
   - Classify triggers using only:
     - `TRG-AC`: AC partial/vague/ambiguous.
     - `TRG-BRAND`: cross-brand behavior variance.
     - `TRG-RISK`: auth continuity, undo/delete integrity, known regression clusters.
     - `TRG-REL`: release confidence needs code-level evidence.
   - No trigger: use Jira metadata/AC + Jira-link scan only.
   - Trigger: pull Confluence only when linked and useful; then try GitHub, then Jira-link fallback.
   - Do not mark evidence unavailable until both GitHub and Jira-link fallback are checked.
   - Write intermediate chunk artifacts to `/tmp/chunk_<EPIC_KEY>_<batch_id>.json`.

4. Plan Generation
  - Invoke `test-plan-generator` using the chunk artifacts.
  - Use the existing workspace venv only:
     - `source .venv/bin/activate 2>/dev/null || { echo 'Missing .venv; create it once during setup, then rerun.'; exit 1; }`
     - `python3 -c "import openpyxl,sys; print('NON_INTERACTIVE_OK', sys.executable)"`
   - Validate payload:
     - `python3 $(pwd)/.github/scripts/generate-test-plan-xlsx.py --validate /tmp/data_payload_<EPIC_KEY>.json`
   - Generate workbook:
     - `python3 $(pwd)/.github/scripts/generate-test-plan-xlsx.py /tmp/data_payload_<EPIC_KEY>.json`
   - Halt and report failure if any command fails.

5. Final Assembly And Rendering
  - Verify workbook exists at `uat-test-plans/<EPIC_KEY>-<slug>.xlsx`.
  - Batch-mode exception: if the prompt explicitly says `Batch mode: do not render final chat output`, skip the return block below and halt after generator completion.
  - Return only:
     1. `Status: Success` or `Status: Failed`
     2. `Workbook: uat-test-plans/<EPIC_KEY>-<slug>.xlsx` (when generated)
     3. `Payload: /tmp/data_payload_<EPIC_KEY>.json`
     4. `Reason: <one-line failure reason>` (failure only)
   - Do not include invocation/compliance/coverage/gaps narrative sections unless explicitly requested.
   - Halt after rendering output.