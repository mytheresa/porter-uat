# UAT Reducer V2 Batch Summary

Deterministic reducer with matrix-join scoring and hard constraint:
- Preserve at least one checklist check per AC Ref.

## Batch KPI

- Epics processed: 23
- Checks: 241 -> 201 (40 removed, 16.6% removed)
- AC coverage retained: 235/235 (100.0%)
- High-priority AC coverage retained: 149/149 (100.0%)
- Target reduction hit exactly: 14/23 epics

## Per-Epic KPI

| Epic | Checks (orig->kept) | Removed % | AC coverage % | High AC coverage % | Target hit | Priority reliability (before->after) |
|---|---:|---:|---:|---:|---|---|
| G2-15883 | 8->7 | 12% | 100.0% | 100.0% | No (guardrail constrained) | 90 (Good) -> 90 (Good) |
| G2-16011 | 8->6 | 25% | 100.0% | 100.0% | Yes | 20 (High skew) -> 20 (High skew) |
| G2-16144 | 10->7 | 30% | 100.0% | 100.0% | Yes | 60 (Moderate skew) -> 62 (Moderate skew) |
| G2-16151 | 6->5 | 17% | 100.0% | 100.0% | Yes | 20 (High skew) -> 20 (High skew) |
| G2-16176 | 10->8 | 20% | 100.0% | 100.0% | No (guardrail constrained) | 62 (Moderate skew) -> 62 (Moderate skew) |
| G2-16248 | 11->8 | 27% | 100.0% | 100.0% | Yes | 73 (Good) -> 73 (Good) |
| G2-16257 | 10->7 | 30% | 100.0% | 100.0% | Yes | 55 (Moderate skew) -> 55 (Moderate skew) |
| G2-16258 | 10->10 | 0% | 100.0% | 100.0% | No (guardrail constrained) | 69 (Moderate skew) -> 69 (Moderate skew) |
| G2-16283 | 8->7 | 12% | 100.0% | 100.0% | No (guardrail constrained) | 70 (Good) -> 70 (Good) |
| G2-16314 | 9->7 | 22% | 100.0% | 100.0% | Yes | 51 (Moderate skew) -> 51 (Moderate skew) |
| G2-16316 | 10->10 | 0% | 100.0% | 100.0% | No (guardrail constrained) | 48 (Moderate skew) -> 48 (Moderate skew) |
| G2-16396 | 16->12 | 25% | 100.0% | 100.0% | Yes | 77 (Good) -> 67 (Moderate skew) |
| G2-16474 | 10->7 | 30% | 100.0% | 100.0% | Yes | 50 (Moderate skew) -> 50 (Moderate skew) |
| G2-16477 | 12->10 | 17% | 100.0% | 100.0% | No (guardrail constrained) | 76 (Good) -> 76 (Good) |
| G2-16480 | 10->7 | 30% | 100.0% | 100.0% | Yes | 48 (Moderate skew) -> 48 (Moderate skew) |
| G2-16639 | 4->4 | 0% | 100.0% | 100.0% | Yes | 80 (Good) -> 80 (Good) |
| G2-17317 | 10->10 | 0% | 100.0% | 100.0% | No (guardrail constrained) | 64 (Moderate skew) -> 64 (Moderate skew) |
| G2-17387 | 9->7 | 22% | 100.0% | 100.0% | Yes | 67 (Moderate skew) -> 67 (Moderate skew) |
| G2-17473 | 10->7 | 30% | 100.0% | 100.0% | Yes | 56 (Moderate skew) -> 63 (Moderate skew) |
| G2-17475 | 6->6 | 0% | 100.0% | 100.0% | No (guardrail constrained) | 20 (High skew) -> 20 (High skew) |
| G2-17566 | 11->8 | 27% | 100.0% | 100.0% | Yes | 52 (Moderate skew) -> 53 (Moderate skew) |

## Dropped Checks

| Epic | Dropped checks (Check ID [Section]) |
|---|---|
| G2-15883 | UAT-003 [Client Detail Visibility] |
| G2-16011 | UAT-005 [Access & Roles], UAT-008 [Concierge Handover] |
| G2-16144 | UAT-004 [Language Selection], UAT-006 [Search], UAT-008 [Suggested Country] |
| G2-16151 | UAT-004 [Stock & Sizes] |
| G2-16176 | UAT-005 [Search & Meganav], UAT-006 [Responsive Behavior] |
| G2-16248 | UAT-001 [Desktop Main Navigation], UAT-003 [Flyout Templates], UAT-008 [Cross-Brand Variants] |
| G2-16257 | UAT-002 [Search Results], UAT-003 [Filters], UAT-006 [Redirect Safety] |
| G2-16258 | — |
| G2-16283 | UAT-002 [Color Switching] |
| G2-16314 | UAT-006 [Non-auth Feature Reuse], UAT-009 [Negative-path Sampling] |
| G2-16316 | — |
| G2-16396 | UAT-004 [Wishlist Navigation], UAT-006 [All Items Query & Rendering], UAT-007 [Auth Continuity], UAT-011 [Default Wishlist Guardrails] |
| G2-16474 | UAT-005 [Validation], UAT-006 [Free Shipping], UAT-008 [Regional Pricing] |
| G2-16477 | UAT-009 [Trimming and Input Hygiene], UAT-011 [Cross-Brand/Desktop-Mobile] |
| G2-16480 | UAT-005 [Cart State Lifecycle], UAT-009 [Checkout Summary Reflection], UAT-010 [Device and Performance] |
| G2-16639 | — |
| G2-17317 | — |
| G2-17387 | UAT-002 [Reservation Card Presence], UAT-008 [No-Data UX] |
| G2-17473 | UAT-004 [Address Update], UAT-005 [Address Deletion], UAT-007 [Data Completeness] |
| G2-17475 | — |
| G2-17566 | UAT-002 [Checkout Login], UAT-003 [Checkout Login], UAT-004 [Checkout Login] |

## Incremental Run 2026-08-07 11:39:24

### Batch KPI

- Epics processed: 2
- Checks: 43 -> 41 (2 removed, 4.7% removed)
- AC coverage retained: 42/42 (100.0%)
- High-priority AC coverage retained: 8/8 (100.0%)
- Target reduction hit exactly: 1/2 epics

### Per-Epic KPI

| Epic | Checks (orig->kept) | Removed % | AC coverage % | High AC coverage % | Target hit | Priority reliability (before->after) |
|---|---:|---:|---:|---:|---|---|
| G2-16977 | 34->34 | 0% | 100.0% | 100.0% | No (guardrail constrained) | 20 (High skew) -> 20 (High skew) |
| G2-16979 | 9->7 | 22% | 100.0% | 100.0% | Yes | 20 (High skew) -> 20 (High skew) |

### Dropped Checks

| Epic | Dropped checks (Check ID [Section]) |
|---|---|
| G2-16977 | — |
| G2-16979 | CHK-005 [Impersonation Session], CHK-007 [Account And Checkout Continuity] |
