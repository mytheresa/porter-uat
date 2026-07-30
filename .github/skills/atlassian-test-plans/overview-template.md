# Standard Overview Template

Use this overview block at the top of the simplified plan for consistency.

## Overview

- Epic: <EPIC_KEY> - <EPIC_TITLE>
- Objective: Validate manually reproducible UI behavior explicitly documented in Jira and linked artifacts.
- Audience: Business quick-check
- Scope boundaries:
  - Included: matrix-linked UI scenarios from documented AC/requirements
  - Excluded: undocumented assumptions, non-reproducible checks, automation-only checks
- Environments/Brands: <DOCUMENTED_SCOPE_ONLY>
- Evidence policy: Each major scenario should capture at least one URL/screenshot/note when practical.

## Coverage Matrix Policy

- Build matrix first, then generate the simplified checklist from matrix.
- Keep one-to-one coverage parity between matrix rows and checklist items.
- Any excluded Jira item must include a documented exclusion reason.
