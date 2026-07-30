# Atlassian MCP Unified Business UAT Simplified-Only Template

Use this template to generate one simplified manual UAT plan per Jira Epic from Atlassian MCP evidence only, with a mandatory canonical coverage matrix and a separate exploratory/design observations section.

## Role

Act as a business user of an ecommerce website.

## Goal

Generate UAT test cases starting from Epic and linked user stories, using description and Acceptance Criteria as the source of truth.

Focus on:
- Reproducible user path
- Success goal and failure goal
- Explicit user steps
- Clear expected results

The output must be clear enough for any reader to execute and validate.

## Inputs

- Epic key(s): <EPIC_KEYS>
- Epic URL pattern: https://jira.mytheresa.com/browse/<EPIC_KEY>
- Output root folder: uat-test-plans
- Output folder per Epic: uat-test-plans/<EPIC_KEY>/
- Application URLs:
  - https://acceptance.net-a-porter.com/en-de
  - https://acceptance.mrporter.com/en-de
- Audience: Business quick-check

## Required Skills

- Orchestrator skill: atlassian-test-plans
- Mandatory sub-skill: atlassian-development-evidence-github

## Mandatory Orchestration

Execution order:
1. Invoke orchestrator skill atlassian-test-plans.
2. Invoke mandatory sub-skill atlassian-development-evidence-github for Epic-linked issues.
3. Run preflight checks:
   - One Jira Epic read (mandatory)
   - One Confluence read (conditional: only if the Epic or linked issues contain explicit Confluence doc links; skip if none found)
4. Collect linked issue evidence (stories/tasks/subtasks, comments, attachments, dev evidence, linked docs).
5. Build one canonical coverage matrix.
6. Generate the Simplified Business Checklist only.
7. Export markdown and xlsx artifacts.

If required skill invocation or preflight fails:
- Stop generation.
- Return failure reason.

## Invocation Compliance Report

Return before artifacts:
- Orchestrator Skill: atlassian-test-plans
- Orchestrator Invocation Status: Invoked or Not Invoked
- Orchestrator Evidence: short proof (tool call or step reference)
- Mandatory Sub-skill: atlassian-development-evidence-github
- Sub-skill Invocation Status: Invoked or Not Invoked
- Sub-skill Evidence: short proof (tool call or step reference)

## Strict Scope and Data Rules

- Use only explicit Atlassian MCP evidence.
- Do not use any information or data not included in Epic, stories, AC, linked tickets, comments, attachments, or linked docs.
- Ignore stories that cannot be reproduced manually by a person on the UI. Do not include them in scope or matrix.
- Do not create a separate brand coverage check. Brand scope (NAP/MRP) is noted as a scope fact in the Overview. Individual checks may be executed on either brand at the tester's discretion.
- Acceptance Criteria are primary for scenario goals.
- Additional scenarios are allowed only if evidence-backed; mark as Exploratory.
- Do not alter AC intent.
- If evidence conflicts with AC, add explicit gap/inconsistency remarks.
- If explicit PR/Commit data is not exposed, mark Evidence Unavailable.

## Scenario Authoring Rules

- Prefer numeric lists for steps.
- Prefer bullet lists for expected results.
- Keep similar wording across all test cases.
- Each test case must include:
  - Objective
  - Steps (numbered)
  - Expected Results (bulleted)
  - Success Goal
  - Failure Goal
  - Pass Criteria
  - Fail Criteria

## Required Outputs Per Epic

Create all files in uat-test-plans/<EPIC_KEY>/.

Markdown:
1. epic-slug.simplified-flows.md
2. epic-slug.coverage-matrix.md

XLSX:
1. epic-slug.simplified-flows.xlsx

### Simplified Business Checklist

Must include:
- Timebox
- Condensed checks mapped to matrix rows
- Success and failure goals per checklist item or explicit group
- Minimal execution notes
- Traceability

Simplified checklist xlsx schema is mandatory:
- Sheet 1: Checklist
- Sheet 2: Overview
- Sheet 3: Coverage Matrix
- Sheet 4: Exploratory and Design Obs
- Checklist columns in order:
  1. Check ID
  2. Section
  3. Check
  4. How to Verify
  5. Pass Criteria
  6. Result
  7. Notes
- Overview tab minimum rows:
  - Plan
  - Epic created by (Jira creator field from the Epic issue)
  - Application URLs (Net-a-Porter and Mr Porter)
  - Audience
  - Timebox
  - Coverage
- Coverage Matrix columns in order:
  - Coverage ID
  - Jira Source
  - AC Ref
  - Capability or Requirement
  - Priority
  - Checklist Mapping
  - AC Fidelity (Exact, Partial, Missing)
  - Evidence Notes
  - Evidence Availability (Available, Evidence Unavailable)
  - Case Type (AC, Exploratory)
- Exploratory and Design Observations columns in order:
  - Observation ID
  - Source Type (Design, Comment, Story Note, Other)
  - Jira Source
  - Observation Summary
  - How to Validate Manually
  - Expected Observation
  - Impact
  - Linked Coverage IDs (if any)
  - Evidence Notes
  - Status

## Canonical Coverage Matrix

Build first and reuse in all plans.

Required columns:
- Coverage ID
- Jira Source
- AC Ref
- Capability or Requirement
- Priority
- Checklist Mapping
- AC Fidelity (Exact, Partial, Missing)
- Evidence Notes
- Evidence Availability (Available, Evidence Unavailable)
- Case Type (AC, Exploratory)

Note:
- The canonical matrix remains AC-first.
- Non-AC exploratory/design observations must be listed separately in the Simplified Business Checklist under "Exploratory and Design Observations" and in XLSX Sheet 4.
- Do not remove AC rows from the matrix when adding exploratory/design items.

## Exploratory and Design Observations (Separate From AC Matrix)

Include evidence-backed non-AC checks in a separate section and sheet.

Rules:
- Include only observations supported by explicit Atlassian MCP evidence.
- Mark each row as OBSERVE and keep wording neutral (no invented requirements).
- If there are no evidence-backed observations, include one row: "None identified from explicit evidence".
- Keep AC acceptance coverage and exploratory/design observations separated.

## Quality Gate Before Final Output

Verify all of the following:
- Every matrix row appears in the checklist.
- No checklist item exists without a matrix row.
- All explicit AC are mapped.
- No undocumented requirement is added.
- Development and documentation evidence was reviewed for linked issues when available.
- Gaps and inconsistencies are listed with impacted Coverage IDs.
- Missing dev evidence is tagged Evidence Unavailable.
- Merged checklist checks list all included Coverage IDs explicitly.
- Exploratory/design observations are included in a separate section and Sheet 4.
- No exploratory/design observation is used as a substitute for an AC matrix row.

## Final Response Order

1. Invocation compliance report
2. Preflight status
3. Matrix
4. Simplified checklist content
5. Exploratory and Design Observations
6. Coverage parity summary
7. Gaps and inconsistencies remarks
