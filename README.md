# Porter UAT

Lightweight toolkit for generating simplified manual UAT test plans for **Net-a-Porter** and **Mr Porter** from Jira Epic evidence — no test management licence required.

A hardened GitHub Copilot agent reads Epics and linked stories directly from Jira via MCP, extracts Acceptance Criteria, and produces:

- A **Business Checklist** (xlsx) ready to hand to a Business User
- A **Coverage Matrix** for AC-to-test traceability
- A **Exploratory Scenarios** sheet for evidence-backed observations

---

## Prerequisites

| Requirement                 | Notes                             |
| --------------------------- | --------------------------------- |
| Python 3.9+                 | For xlsx generation               |
| GitHub Copilot (Agent mode) | Requires access to this repo      |
| Atlassian MCP configured    | See setup below                   |
| Jira Data Center access     | Read access to the target project |

---

## Setup

### 1. Clone

```sh
git clone https://github.com/your-org/porter-uat.git
cd porter-uat
```

### 2. Python dependencies

Create and activate a repository virtual environment (required on macOS due to PEP 668):

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r .github/scripts/requirements.txt
```

### 3. Atlassian MCP tokens

Store Jira and Confluence tokens in the MCP packages' default per-user files (outside the repo):

```sh
~/.atlassian-dc-mcp/jira.env
~/.atlassian-dc-mcp/confluence.env
```

Example:

```sh
# jira.env
JIRA_API_TOKEN=your-jira-token

# confluence.env
CONFLUENCE_API_TOKEN=your-confluence-token
```

### 4. GitHub MCP token

Store your GitHub personal access token (PAT) for the MCP package:

```sh
~/.github-mcp/github.env
```

Example:

```sh
# github.env
GITHUB_TOKEN=your-github-pat
```

The token is used to extract PR/commit evidence for development traceability.

---

## Generating a Test Plan

### Batch Mode (Multiple Epics)

Queue Epics in `epics_queue.txt` (one key per line), then run the batch processor:

```sh
cat > epics_queue.txt << EOF
G2-19278
G2-19500
G2-20100
EOF

python3 auto_copilot.py
```

The batch processor will:
- Open VS Code with Copilot Chat
- Automatically feed each Epic to the agent
- Wait for workbook generation on disk
- Track successes in `epics_processed.txt` and failures in `epics_failed.txt`
- Handle timeouts, context resets, and graceful shutdown (Ctrl+C or move mouse to top-left corner)

**Instructions:**
1. Focus Copilot Chat input box before starting
2. Move mouse to top-left corner at any time to safely abort (restores in-flight Epic to queue)

### Single Epic (Manual / Debugging)

For one-off generation or debugging:

1. Open a fresh Copilot chat thread (or type `/clear`)
2. Paste the following prompt, replacing `<EPIC_KEY>` with your target:

```
Read .github/prompts/uat-test-plan-template.md and strictly follow the Mandatory Orchestration Workflow for Epic '<EPIC_KEY>'. 
Generate the payload at /tmp/data_payload_<EPIC_KEY>.json and execute the python generator script.
Final chat output must include only Status, Workbook (when generated), Payload, and Reason (failure only).
```

3. Wait for workbook generation (`uat-test-plans/<EPIC_KEY>-<slug>.xlsx`)
4. Type `/clear` before processing another Epic

---

## Troubleshooting

### Copilot terminal asks for approval during batch runs

If Copilot pauses on helper commands (for example `jq` over local chat resource JSON files, or Python/openpyxl generator commands), add command-line auto-approve rules to your VS Code user settings under `chat.tools.terminal.autoApprove`.

Example rule:

```json
"chat.tools.terminal.autoApprove": {
   "python3": true,
   "jq": true,
   "/^jq '\\.data\\.issues \\| length' \"\/Users\/jordi\\.sans\/Library Application Support\/Code\/User\/workspaceStorage\/[^\"]+\/GitHub\\.copilot-chat\/chat-session-resources\/[^\"]+\/[^\"]+\/content\\.json\"$/": {
      "approve": true,
      "matchCommandLine": true
   },
   "/^python3 -c \"import openpyxl([; ].*)?\"$/": {
      "approve": true,
      "matchCommandLine": true
   },
   "/^python3 \/Users\/jordi\\.sans\/porter-uat\/.github\/scripts\/generate-test-plan-xlsx\\.py --validate \/tmp\/data_payload_[A-Z0-9-]+\\.json$/": {
      "approve": true,
      "matchCommandLine": true
   }
}
```

Notes:
- Keep regex rules narrow and read-only to avoid over-broad approval bypass.
- If a new rule does not apply immediately, run `Developer: Reload Window` once.

---

## Output Structure

```
uat-test-plans/
└── <EPIC_KEY>-<slug>.xlsx            # Business checklist workbook

uat-test-plans/source/
└── <EPIC_KEY>/
   └── data_payload_<EPIC_KEY>.json  # Persisted payload for XLSX regeneration
```

Intermediate chunk files are temporary by default and are cleaned from `/tmp`.

Artifact behavior is controlled by environment variables:
- `PERSIST_JSON_ARTIFACTS=1` (default): persist payload JSON files under `uat-test-plans/source/<EPIC_KEY>/`
- `PERSIST_CHUNK_ARTIFACTS=0` (default): do not persist chunk JSON files

### Workbook sheets

| Sheet                    | Purpose                                                                      |
| ------------------------ | ---------------------------------------------------------------------------- |
| Overview                 | Epic metadata, scope, dev evidence, gaps                                     |
| Checklist                | Business UAT checklist — Result and Notes columns blank for tester           |
| Coverage Matrix          | AC-to-check traceability with Inconsistencies field                         |
| Exploratory Scenarios    | Evidence-backed non-AC observations and design notes                         |

---

## How It Works

### Workflow Architecture

1. **Epic Map & Categorization:** Agent invokes `evidence-context` skill to extract Epic metadata and categorize child stories (UI-testable vs. backend-only).

2. **Chunked Evidence Gathering (Map-Reduce):** 
   - Groups UI-testable stories into batches (6-8 per chunk)
   - Iteratively invokes `evidence-context` per story with minimal field retrieval
   - Writes intermediate state to `/tmp/chunk_<EPIC_KEY>_<batch_id>.json` files to prevent context overflow

3. **Plan Synthesis & Payload Generation:** 
   - `test-plan-generator` skill reads all chunks and synthesizes final JSON payload
   - Payload written to `/tmp/data_payload_<EPIC_KEY>.json`

4. **Validation & XLSX Generation:**
   - Runs `generate-test-plan-xlsx.py --validate` for quick-fail preflight checks
   - On pass, runs `generate-test-plan-xlsx.py` to generate final workbook
   - Cleanup phase persists payload JSON to `uat-test-plans/source/<EPIC_KEY>/` (default)
   - Chunk files are cleaned from `/tmp` unless `PERSIST_CHUNK_ARTIFACTS=1`

### Data Flow

```
Jira Epic (via MCP)
    │
    ├── Metadata: creator, status, components
    │
    ├── Linked Stories (UI-testable only)
    │   └─→ AC + Comments → Chunked Evidence Files → Coverage Matrix rows → Checklist checks
   │
   ├── Persisted Payloads (for regeneration)
   │   └─→ uat-test-plans/source/<EPIC_KEY>/data_payload_<EPIC_KEY>.json
    │
    ├── Development Evidence (GitHub PRs via MCP)
    │   └─→ Availability status (Available / Unavailable)
    │
    └── Comments / Attachments
        └─→ Exploratory observations (Sheet 4)
```

### Key Rules

- Backend-only stories (no UI-reproducible AC) are **excluded** from scope
- Brand coverage (NAP/MRP) is noted as scope context — no separate repeat checks
- Result and Notes columns are always left blank for tester input
- Confluence is only queried when Epic has explicit doc links
- Token efficiency enforced: minimal initial retrieval, selective deep-dives only

---

## File Structure

| File / Folder                     | Purpose                                           |
| --------------------------------- | ------------------------------------------------- |
| `auto_copilot.py`                 | Batch processor — automation loop, queue mgmt    |
| `.github/prompts/uat-test-plan-template.md` | Mandatory orchestration workflow for agents |
| `.github/scripts/generate-test-plan-xlsx.py` | XLSX generator with enforced formatting rules |
| `.github/scripts/requirements.txt` | Python dependencies (openpyxl, pyautogui, etc.)  |
| `epics_queue.txt`                 | Queue of Epic keys (one per line) for batch mode |
| `epics_processed.txt`             | Log of successfully generated Epics              |
| `epics_failed.txt`                | Log of timeouts/failures for manual review       |

---

## Contributing

To change output format or checklist rules:

1. **Generator Script:** `.github/scripts/generate-test-plan-xlsx.py` — Update sheet structure, column definitions, and styling
2. **Template Workflow:** `.github/prompts/uat-test-plan-template.md` — Update the Mandatory Orchestration Workflow if skill invocation or payload structure changes
3. **Test Generation:** Generate a test plan and validate output structure

Keep the template and script in sync. The script header documents all enforced rules.
