# Unified Business UAT Queue Processor Template

## Fast Rules

- Act as a business user of an ecommerce website.
- AC is canonical; secondary evidence only clarifies.
- Story-only scope: `evidence-context` resolves epic children from Jira Epic Link plus `issuelinks`, but only child issues whose type is `Story` are in scope; consume that scoping and do not re-derive it here.
- Default to Jira-only. Pull Confluence/GitHub only when a trigger fires.
- Clone/relates lineage: when an in-scope story clones or relates to a `Done` story, follow that link and run a GitHub key search on the linked key to recover implementation evidence.
- Quick wins: if the epic has no UI-testable stories, or the workbook already exists, stop early with the minimal result.
- Use two passes: classify first, enrich only when needed.
- Missing-AC rule: if explicit AC are absent, produce only 2-4 exploratory checks and do not invent end-to-end UAT flows.
- Final chat output: status + artifact paths only, except in batch mode when explicitly instructed to skip final rendering.

## Mandatory Orchestration Workflow

Execute exactly one Epic key. Stop on failure. No prompts.

1. Queue Context
   - Process the explicit Epic key from the prompt.
   - Do not read or modify `epics_queue.txt`.

2. Preflight And Epic Map
  - Invoke `evidence-context` for the parent Epic only.
  - Capture creator, status, components, and child stories from `evidence-context`'s merged Epic Link + `issuelinks` discovery.
  - Rely on `evidence-context`'s Story-only scoping (non-Story types excluded by default).
  - Mark backend-only, migration, and evaluation stories as excluded.
  - If the Epic returns zero child stories, treat the epic as having no story scope and clearly note in the XLSX that no stories were found.

3. Chunked Evidence Gathering (Map-Reduce)
   - Group UI-testable stories in batches of **6-8**.
   - For each child story, run `evidence-context` with minimal retrieval first.
   - Classify triggers using only:
     - `TRG-AC`: AC partial/vague/ambiguous.
     - `TRG-BRAND`: cross-brand behavior variance.
     - `TRG-RISK`: auth continuity, undo/delete integrity, known regression clusters.
     - `TRG-REL`: release confidence needs code-level evidence.
  - No trigger: use Jira metadata/AC + Jira-link scan; run linked-`Done` lineage GitHub key search when applicable.
   - Trigger: pull Confluence only when linked and useful; then try GitHub, then Jira-link fallback.
   - Clone/relates lineage (always, even with no trigger): if the story clones or relates to a `Done` story, follow that link, pull the linked story's AC/completion marks, and run a GitHub key search on the linked key (e.g. `"<LINKED_KEY>" is:pr`). Attribute any PR/commit evidence found to the in-scope story as inherited implementation evidence.
  - Do not mark evidence unavailable until required checks complete: trigger stories check in-scope key + linked-`Done` (when applicable) + Jira-link fallback; non-trigger stories check linked-`Done` (when applicable) + Jira-link fallback.
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