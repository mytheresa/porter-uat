# Coverage Matrix — G2-19278 PLP | Colour Linking

**Epic:** [G2-19278 PLP | Colour linking](https://jira.mytheresa.com/browse/G2-19278)
**Generated:** 2026-07-30
**Brands in scope:** Net-a-Porter (NAP) · Mr Porter (MRP)
**Environments:** https://acceptance.net-a-porter.com/en-de · https://acceptance.mrporter.com/en-de

---

## Stories in Scope (UI-testable)

| Jira Key | Summary | Status | UI-Testability |
|----------|---------|--------|----------------|
| G2-18440 | FE: PLP \| Colour swatches | Closed | Fully UI-testable |
| G2-18439 | BE: PLP API \| Colour linking | Closed | Mixed — BE pipeline items excluded; observable outcome (swatch data in PLP response) covered by G2-18440 checks |

## Stories Excluded (Non-UI-testable)

| Jira Key | Summary | Status | Reason for Exclusion |
|----------|---------|--------|----------------------|
| G2-17553 | BE: Tapir \| Indexing \| Export colour linking data to Mink | Closed | Pure backend data transfer; no observable UI outcome |

---

## Canonical Coverage Matrix

| Coverage ID | Jira Source | AC Ref | Capability / Requirement | Priority | Checklist Mapping | AC Fidelity | Evidence Notes | Evidence Availability | Case Type |
|-------------|------------|--------|--------------------------|----------|-------------------|-------------|----------------|----------------------|-----------|
| G2-19278_TC01 | G2-18440 | AC1 | Colour swatches displayed below product tile on PLP | High | CK-01 | Exact | PR #429 [atelier](https://github.com/mytheresa/atelier/pull/429) MERGED | Available | AC |
| G2-19278_TC02 | G2-18440 | AC2 | Selecting a swatch swaps main product image, updates PLP URL and visually highlights selected swatch | High | CK-02 | Exact | PR #429 [atelier](https://github.com/mytheresa/atelier/pull/429) MERGED | Available | AC |
| G2-19278_TC03 | G2-18440 | AC3 | Maximum 4 swatches shown on tile; (+) indicator displayed when more colours exist | High | CK-03 | Exact | PR #429 [atelier](https://github.com/mytheresa/atelier/pull/429) MERGED | Available | AC |
| G2-19278_TC04 | G2-18440 | AC4 | Hovering over (+) restores the cover / main product image | Medium | CK-04 | Exact | PR #429 [atelier](https://github.com/mytheresa/atelier/pull/429) MERGED | Available | AC |
| G2-19278_TC05 | G2-18440 | AC5 | Clicking (+) navigates user to the cover / default colour PDP | Medium | CK-05 | Exact | PR #429 [atelier](https://github.com/mytheresa/atelier/pull/429) MERGED | Available | AC |
| G2-19278_TC06 | G2-18440 | AC6 | Out of stock colour variants remain visible as swatches on PLP (no suppression) | Medium | CK-06 | Exact | PR #429 [atelier](https://github.com/mytheresa/atelier/pull/429) MERGED; bug G2-20786 noted in comments | Available | AC |
| G2-19278_TC07 | G2-18440 | AC7 | Deep link: each swatch click navigates to that colour's correct PDP URL | High | CK-07 | Exact | PR #429 [atelier](https://github.com/mytheresa/atelier/pull/429) MERGED | Available | AC |
| G2-19278_TC08 | G2-19278 (Epic) · G2-18440 | Epic AC1 + AC Scope | Colour swatches feature fully functional on both NAP and MRP brands | High | CK-08 | Exact | Epic AC states both NAP and MRP; G2-18440 explicitly scoped to both brands | Evidence Unavailable (Epic-level GitHub) | AC |

---

## Development Evidence Summary

| Jira Key | GitHub Evidence Status | PRs / Branches |
|----------|------------------------|----------------|
| G2-19278 | Evidence Unavailable | No PRs/commits returned at Epic level |
| G2-18440 | Available | PR #429 `[G2-18440] PLP color swatches` in `atelier` — MERGED 2026-03-12 |
| G2-18439 | Available | PRs #2417, #2419 in `hyena` (MERGED); PRs #45, #46, #47, #48, #49 in `mink` (MERGED) |
| G2-17553 | Not checked (excluded) | — |
