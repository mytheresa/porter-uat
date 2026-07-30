# Porter UAT

Lightweight toolkit for generating simplified manual UAT test plans for **Net-a-Porter** and **Mr Porter** from Jira Epic evidence — no test management licence required.

An AI agent (GitHub Copilot) reads the Epic and linked stories directly from Jira via MCP, extracts Acceptance Criteria, and produces:

- A **Simplified Business Checklist** (xlsx) ready to hand to a business tester
- A **Canonical Coverage Matrix** (markdown) for traceability
- A **Simplified Flows** narrative (markdown)

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.9+ | For xlsx generation |
| GitHub Copilot (Agent mode) | Requires access to this repo |
| Atlassian MCP configured | See setup below |
| Jira Data Center access | Read access to the target project |

---

## Setup

### 1. Clone

```sh
git clone https://github.com/your-org/porter-uat.git
cd porter-uat
```

### 2. Python dependencies

```sh
python3 -m venv /tmp/xlsx-venv
/tmp/xlsx-venv/bin/pip install -r .github/scripts/requirements.txt
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

---

## Generating a Test Plan

1. Open this repo in VS Code with GitHub Copilot Agent mode enabled.
2. Open Copilot Chat and attach the prompt template:

```
@workspace Use .github/prompts/atlassian-mcp-test-plan-template.md
Generate test plan for https://jira.mytheresa.com/browse/<EPIC_KEY>
```

3. The agent will:
   - Read the Epic and linked stories from Jira
   - Extract GitHub development evidence (PRs/commits)
   - Build the canonical coverage matrix
   - Generate the simplified checklist
   - Produce and save all output files to `uat-test-plans/<EPIC_KEY>/`

---

## Output Structure

```
uat-test-plans/
└── <EPIC_KEY>/
    ├── <slug>.simplified-flows.md       # Narrative checklist with steps
    ├── <slug>.coverage-matrix.md        # Canonical traceability matrix
    └── <slug>.simplified-flows.xlsx     # Business checklist workbook
```

### Workbook sheets

| Sheet | Purpose |
|---|---|
| Checklist | 8-column business checklist — Result and Notes left blank for tester |
| Overview | Epic metadata, scope, dev evidence, gaps |
| Coverage Matrix | AC-to-check traceability (no Status column — tracking is done in Checklist) |
| Exploratory and Design Obs | Evidence-backed non-AC observations |

---

## How It Works

```
Jira Epic
    │
    ├── Linked Stories (UI-testable only)
    │       └── Acceptance Criteria → Coverage Matrix rows → Checklist checks
    │
    ├── Development Evidence (GitHub PRs via MCP)
    │       └── Evidence Availability: Available / Evidence Unavailable
    │
    └── Comments / Attachments
            └── Exploratory observations (Sheet 4)
```

Key rules enforced automatically:

- Backend-only stories (no UI-reproducible AC) are **excluded** from scope and listed separately
- Brand coverage (NAP/MRP) is a scope note — no separate "repeat on MRP" check
- Result and Notes columns are always blank
- Confluence is only read when the Epic has explicit doc links

---

## Skills Reference

| Skill | File | Purpose |
|---|---|---|
| atlassian-test-plans | `.github/skills/atlassian-test-plans/SKILL.md` | Orchestrates plan generation |
| atlassian-development-evidence-github | `.github/skills/atlassian-development-evidence-github/SKILL.md` | Extracts GitHub PR/commit evidence |

---

## XLSX Script

The canonical xlsx generator lives at `.github/scripts/generate-test-plan-xlsx.py`.

The agent fills in the `── AGENT: FILL ──` sections with Epic-specific data and runs:

```sh
/tmp/xlsx-venv/bin/python3 .github/scripts/generate-test-plan-xlsx.py
```

The script enforces all formatting rules (styling, column structure, auto-fit) and cannot be overridden without updating the skill.

---

## Contributing

To change output format or checklist rules, update **both**:
1. `.github/skills/atlassian-test-plans/SKILL.md` — agent behaviour
2. `.github/scripts/generate-test-plan-xlsx.py` — xlsx output rules

Keep them in sync. The script header lists all enforced rules.
