---
name: evidence-context
description: Standardize extraction of full ticket context, Jira metadata, Confluence/doc links, and GitHub development evidence by orchestrating Jira, Confluence, and GitHub MCP servers. Handles Epic-to-Story hierarchy resolution.
user-invocable: true
---
# Evidence & Context Extractor

## Purpose

Create a consistent evidence, documentation, and metadata snapshot per Jira issue by orchestrating cross-platform discovery via MCP servers. This skill acts purely as a data-gathering engine to feed downstream test plan generators.

## Input

- Single Jira issue key (Iteratively called per story by Orchestrator)
- Target Environment URLs (passed from Orchestrator)
- Optional depth (`issue-only`, `issue-and-linked`, `issue-linked-and-subtasks`)

## Token Efficiency Rules

- Use a two-pass strategy: classify with minimal fields first, then enrich only for in-scope UI stories.
- Avoid requesting large text blobs unless required for AC mapping or conflict resolution.
- Return normalized summaries (ids/keys/status/links) instead of raw payload dumps.
- Jira-first mode is default. Confluence and direct in-scope GitHub lookups are trigger-gated, with one exception: linked-`Done` clone/relates lineage GitHub key search is always-on.

## Trigger-Gated Enrichment Policy (Mandatory)

For each in-scope UI story, compute these boolean triggers from minimal Jira pass data:

- `TRG-AC`: AC is partial, vague, or ambiguous.
- `TRG-BRAND`: story indicates cross-brand behavior/variance.
- `TRG-RISK`: story maps to auth continuity, undo/delete integrity, or known regression clusters.
- `TRG-REL`: release confidence explicitly requires code-level evidence.

Behavior:

- If no triggers fire: keep Jira-first path, skip Confluence and direct in-scope-key GitHub retrieval, but still execute linked-`Done` clone/relates lineage GitHub key search when present.
- If any trigger fires: allow Confluence/GitHub enrichment under the rules below.

## Output Contract

For each processed issue (Epic or Child), return one standardized JSON block containing:

1. **Metadata & Context**
   - `EPIC_KEY`: Primary Jira Key
   - `TARGET_URLS`: Target Environment URLs
   - `EPIC_SUMMARY`: Summary / Title
   - `EPIC_STATUS`: Current status
   - `EPIC_CREATED_BY`: Formatted creator string
   - `COMPONENT`: Exact Jira component names
2. **Hierarchy Map (If Epic)**
   - **Child Issues Resolved**: Categorized UI-testable vs. non-UI-testable keys.
   - **Story-only scope default**: include a child issue in scope only if its issue type is `Story`. Exclude every non-Story type (Bug, Task, Sub-task, Initiative, Spike, etc.) by default, and list them separately as out-of-scope.
3. **Documentation Links**
   - Extracted general documentation URLs (e.g., Confluence, Figma, external wikis) with BDD-filtered content summaries.
4. **Development Evidence Snapshot**
   - **Status**: `Available` | `Unavailable`
   - **PR/Commit Links**: Grouped by child key.
   - **Fallback Sources**: Key comments or attachments.

## Mandatory MCP Orchestration Workflow

1. **Jira Fetch (`atlassian-jira-dc` MCP):**
   - Pass 1 (minimal): call Jira MCP with targeted fields for scope decisions (`expand="names,schema"`): `summary,description,issuelinks,parent,status,issuetype,creator,components`.
   - Pass 2 (enrichment): request `comment,attachment` only for UI-testable in-scope stories or when AC ambiguity requires it.
   - Resolve remote issue links (`remotelink` endpoint) in addition to text body links to ensure full documentation discovery.
   - If resolving an Epic, discover child stories from `issuelinks` first (primary). Then run Epic Link/agile epic membership lookup as a secondary backstop (JQL `"Epic Link" = <EPIC_KEY>` or `/epic/{EPIC_KEY}/issue`) and add any missing stories. De-duplicate the union so children found by one source are not duplicated.

2. **Doc Extraction (Confluence MCP & General Links):**
   - Scan descriptions first, then comments/remote links only if needed for missing AC context.
   - Execute Confluence MCP lookup only for trigger-matched stories and only when a recognized Confluence URL is detected.
   - **BDD Filter Rules:** Extract only sections matching "Requirements", "Acceptance Criteria", or explicit "Given/When/Then" specifications. Discard historical revision logs and author notes.

3. **GitHub Fetch & BDD Extraction (`@modelcontextprotocol/server-github` MCP):**
   - **NEVER call `jira_getIssueDevelopmentInfo`** — the Jira instance is linked to a self-hosted Bitbucket (`git.mytheresa.com`) that returns `unauthorized`. It does not expose GitHub data. Skip it entirely and go directly to GitHub MCP.
   - Perform repository-scoped search using the Jira story key across PR titles and metadata only for trigger-matched stories; fetch body/comment detail only when required to map ambiguous AC.
   - Clone/relates lineage exception (always-on): when the in-scope story clones or relates to a linked `Done` story, run a GitHub key search on that linked key and attach inherited PR/commit evidence to the in-scope story.
   - **Smart BDD Extraction & Filtering Rules:**
     - *Ignore Bots:* Strip automated CI/CD comments (Jenkins, Dependabot, SonarQube, GitHub Actions).
     - *Target BDD Context:* Extract *only* PR Title, main summary, and sections labeled "How to Test", "Testing Notes", "Impact", or explicit state-change steps. Retain comments containing feature flag toggles or testing workarounds.
     - *Strip Raw Code:* Exclude all raw code diffs, patch files, JSON bodies, and stack traces.

3b. **Jira-Link Evidence Fallback (Mandatory before marking unavailable):**
   - For each in-scope UI story, scan Jira `description`, `comments`, `issuelinks`, and remote links for GitHub PR/commit URLs or commit SHA references.
   - Treat these URLs/references as valid development evidence even when direct GitHub MCP search by Jira key returns no hits.
   - Capture matched links under the story's development evidence list with source type (`jira-description`, `jira-comment`, `jira-remotelink`, `jira-issuelink`).

4. **Status Determination:**
   - Mark `Available` if explicit PR/commit evidence was found via GitHub MCP **or** via Jira-link evidence fallback.
   - If no triggers fire for a story, keep Jira-first mode, rely on Jira-link evidence, and still include any linked-`Done` lineage GitHub evidence.
   - If any trigger fires and GitHub MCP lookup fails (tool/server/auth/transient error), continue with Jira-link fallback and record outcome in the existing evidence format.
   - Mark `Unavailable` only after all required checks are performed and no PR/commit evidence is found:
       - Trigger-matched stories: in-scope-key GitHub search, linked-`Done` lineage GitHub search (when applicable), and Jira-link fallback.
       - Non-trigger stories: linked-`Done` lineage GitHub search (when applicable) and Jira-link fallback.

## Deterministic Rules

- **Never check Bitbucket for development evidence.** Do not call `jira_getIssueDevelopmentInfo` or query `git.mytheresa.com` (self-hosted Bitbucket/Stash) — it returns `unauthorized` and exposes no usable data. Always use the GitHub MCP server (plus the Jira-link evidence fallback) as the sole source of PR/commit evidence.
- AC remains the primary source of truth for scenario intent. Dev evidence enriches but never overrides AC intent.
- Story-only scope default: an epic's child issue enters scope only if its issue type is `Story`; all other types are excluded unless the Orchestrator explicitly overrides this.
- Process strictly one story per execution call to guarantee maximum token efficiency.