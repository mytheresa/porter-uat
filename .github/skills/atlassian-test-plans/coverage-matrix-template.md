# Coverage Matrix Template

Use this table as the canonical source before producing the simplified checklist.

| Coverage ID | Jira Source | AC Ref | Capability / Requirement | Priority | Checklist Mapping | AC Fidelity | Evidence Notes | Evidence Availability | Case Type |
|---|---|---|---|---|---|---|---|---|---|
| EPICKEY_TC01 | G2-00000 | AC1 | Requirement text from Jira | Medium | CHK-01 | Exact | PR #N merged in repo (url) | Available | AC |
| EPICKEY_TC02 | G2-00000 | AC2 | Requirement text from Jira | Medium | CHK-02 | Exact | PR #N merged in repo (url) | Available | AC |

## Validation Rules

- Each row must have a non-empty Checklist Mapping.
- Mapping references must point to existing checklist items.
- If one checklist item covers multiple matrix rows, list all IDs in Checklist Mapping.
- If a Jira story has no manually reproducible UI behavior, exclude it and log exclusion reason under "Stories excluded (non-UI-testable)" in the Overview.
- No Status column — execution tracking is done in the Checklist sheet (Result column).
