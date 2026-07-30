---
name: atlassian-development-evidence-github
description: Standardize extraction of Development-section evidence for Jira issues, including PR/commit discovery and deterministic fallback markers when GitHub evidence cannot be expanded.
user-invocable: true
---

# Atlassian Development Evidence via GitHub Links

## Purpose

Create a consistent evidence snapshot per Jira issue for Development context used by test plan generation.

Primary goal:
- Capture explicit PR/commit evidence when exposed by Jira MCP
- Fall back deterministically when Development data is missing or inaccessible

## Input

- Jira issue key(s)
- Optional depth:
  - `issue-only`
  - `issue-and-linked`
  - `issue-linked-and-subtasks`

## Output Contract

For each processed issue, return one evidence block with:

- Issue Key
- Development Evidence Status:
  - `Available`
  - `Evidence Unavailable`
- PR Links (if any)
- Commit Links/Hashes (if any)
- Fallback Evidence Sources Used:
  - comments
  - linked tickets
  - attachments
  - documentation links
- Notes and Gaps

Additionally return invocation metadata:

- Skill Invocation Status: Invoked / Failed
- Failure Reason (if failed)

## Mandatory Workflow

1. Read Jira issue via MCP with targeted fields first and `expand="names,schema"`; fall back to `fields=["*all"]` only if targeted fields are insufficient for Development evidence detection.
2. Resolve field semantics from `names` and `schema` (do not assume fixed custom field IDs):
  - Epic link field by name/type (Epic Link relationship)
  - Development/devstatus field by plugin/type/name patterns
3. Inspect resolved fields and payload for explicit Development evidence (PRs/commits/branches/build links).
4. **Always call `getIssueDevelopmentInfo` with `applicationType: "github"`** — never default to `stash` or `bitbucket`. This codebase uses GitHub. If no GitHub data is returned, fall back to `githube` (GitHub Enterprise) before marking Evidence Unavailable.
5. If explicit Development evidence exists:
  - mark status `Available`
  - collect references as-is
6. If explicit Development evidence is not exposed by MCP after GitHub check:
  - mark status `Evidence Unavailable`
  - continue using fallback sources:
    - issue comments
    - linked issues
    - attachments
    - linked documentation

Execution defaults for token efficiency:

- Prefer targeted Jira fields when possible: `summary,description,issuelinks,subtasks,comment,attachment,status,issuetype,priority,creator`
- Resolve Epic-link and Development/devstatus fields semantically from `names`/`schema` after retrieval.
- Use `fields=["*all"]` only when targeted fields are insufficient for Development evidence detection
- Process direct linked issues first; recurse only when the current issue AC/dependency text explicitly references deeper links
- Keep output evidence blocks concise (status + counts + URLs), no raw payload dumps

## Deterministic Rules

- Never drop a referenced evidence link just because it cannot be expanded.
- Always preserve source URLs in output.
- Never infer PR/commit details not explicitly present in MCP-accessible sources.
- Use `Evidence Unavailable` only when PR/commit data is expected but not exposed.

## Usage with Simplified Test Plan Skill

When generating plans:

1. Run this evidence skill for Epic-linked issues first.
2. Attach evidence outputs to the shared coverage matrix rows.
3. Carry forward statuses into:
  - Evidence Availability
4. Emit remarks for unresolved evidence statuses.

## Non-Negotiables

- AC remains primary source of truth for scenario intent
- Development evidence enriches scenarios, never overrides AC intent
- Deterministic markers must be present for missing/inaccessible evidence
- Invocation failure must be surfaced to the user by the orchestrator before plan generation continues
