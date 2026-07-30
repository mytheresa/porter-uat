# Simplified UAT Checklist — G2-19278 PLP | Colour Linking

---

## Invocation Compliance Report

| Field | Value |
|-------|-------|
| Orchestrator Skill | atlassian-test-plans |
| Orchestrator Invocation Status | Invoked |
| Orchestrator Evidence | Skill SKILL.md read; Epic G2-19278 fetched via mcp_atlassian-jir_jira_getIssue; 3 linked stories fetched via JQL "Epic Link" = G2-19278 |
| Mandatory Sub-skill | atlassian-development-evidence-github |
| Sub-skill Invocation Status | Invoked |
| Sub-skill Evidence | getIssueDevelopmentInfo called with applicationType: "github" for G2-19278, G2-18440, G2-18439; fallback markers applied where no data returned |

---

## Preflight Status

| Check | Status | Notes |
|-------|--------|-------|
| Epic read (Jira MCP) | PASS | G2-19278 read successfully |
| Confluence read | SKIPPED | No explicit Confluence doc links found in Epic or linked issues |
| Linked issues collected | PASS | 3 stories found via Epic Link JQL |
| Development evidence | PASS | GitHub dev info checked for Epic + 2 stories; Epic-level Evidence Unavailable; story-level Available |
| UI-testability gate | PASS | 1 story fully in scope (G2-18440); 1 mixed (G2-18439, BE items excluded); 1 excluded (G2-17553) |

---

## Overview

| Field | Value |
|-------|-------|
| Plan | G2-19278 PLP \| Colour Linking — Simplified Business UAT |
| Epic created by | Kozlova, Nika \|\| External (ext.nkozlova) |
| Application URLs | https://acceptance.net-a-porter.com/en-de · https://acceptance.mrporter.com/en-de |
| Audience | Business quick-check |
| Timebox | ~60 minutes |
| Coverage | 8 AC-driven checks + 3 exploratory/design observations |

---

## Simplified Business Checklist

> **Timebox:** ~60 minutes total  
> **Environment:** Use acceptance.net-a-porter.com/en-de and acceptance.mrporter.com/en-de  
> **Prerequisites:** Use a product that has 2 or more colour-linked variants (multi-colour product on PLP). Find products using existing colour group data or ask the trading team for test SKUs.

---

### Section 1 — Swatch Display

**Success Goal:** Swatches are visible below product tiles on PLP for colour-linked products.  
**Failure Goal:** No swatches appear, or swatches appear on wrong products.

---

#### CK-01 · Colour swatches appear below product tile

**Coverage IDs:** G2-19278_TC01  
**Objective:** Verify that small interactive colour swatches are rendered below the product image tile on PLP.

**Steps:**
1. Navigate to a category or search results page on acceptance.net-a-porter.com/en-de.
2. Locate a product that has multiple colour variants (e.g., a bag or shoe available in several colours).
3. Observe the area below the product image tile.

**Expected Results:**
- Small swatch images are visible directly below the product tile.
- Swatches represent different colour variants of the product.
- Swatches are interactive (visually respond on hover/focus).

**Pass Criteria:** Swatches visible below the tile for a known multi-colour product.  
**Fail Criteria:** No swatches shown, or swatches appear on single-colour products only.

---

### Section 2 — Swatch Interaction

**Success Goal:** Interacting with swatches changes the product image, URL, and highlights the selection.  
**Failure Goal:** Image does not change, URL does not update, or no highlight applied.

---

#### CK-02 · Image swap, URL update and swatch highlight on selection

**Coverage IDs:** G2-19278_TC02  
**Objective:** Verify that clicking a swatch swaps the main product tile image, updates the page URL, and highlights the active swatch.

**Steps:**
1. On the PLP, find a product with multiple swatches.
2. Note the initial main product image and the current page URL.
3. Click a swatch that is different from the current/default colour.
4. Observe the product image, URL, and swatch visual state.

**Expected Results:**
- Main product image changes to the selected colour's image.
- Page URL updates to reflect the selected colour's product slug.
- The clicked swatch is visually distinguished (e.g., border, highlight, active state).
- Previously active swatch loses its highlight.

**Pass Criteria:** Image swaps, URL updates, and selected swatch is visually highlighted.  
**Fail Criteria:** Any of: image does not change, URL remains unchanged, or no visual highlight applied.

---

### Section 3 — Overflow Colours

**Success Goal:** When a product has more than 4 colour variants, a (+) indicator is shown and behaves correctly.  
**Failure Goal:** (+) is absent, or hover/click behaviour is incorrect.

---

#### CK-03 · Maximum 4 swatches; (+) indicator for overflow

**Coverage IDs:** G2-19278_TC03  
**Objective:** Confirm that at most 4 swatches are shown per tile and a (+) overflow indicator appears for additional colours.

**Steps:**
1. On the PLP, find a product known to have 5 or more colour variants.
2. Count the number of swatches displayed below the tile.
3. Check whether a (+) or overflow indicator is visible.

**Expected Results:**
- Exactly 4 swatches are displayed.
- A (+) indicator (or equivalent) is visible alongside the 4 swatches.
- No 5th or further swatch image is shown directly.

**Pass Criteria:** Max 4 swatches visible; (+) present for products with 5+ colours.  
**Fail Criteria:** More than 4 swatches shown, or (+) missing for products with overflow colours.

---

#### CK-04 · Hover (+) restores main/cover image

**Coverage IDs:** G2-19278_TC04  
**Objective:** Verify that hovering over (+) reverts the product tile image to the cover/main image.

**Steps:**
1. On a product tile with 5+ colour variants, click a swatch to change the image.
2. Move the cursor to hover over the (+) indicator.
3. Observe the product tile image.

**Expected Results:**
- The product tile image reverts to the cover/default colour image when hovering (+).
- No navigation occurs on hover alone.

**Pass Criteria:** Cover image displayed on (+) hover.  
**Fail Criteria:** Image does not revert, or unintended navigation occurs.

---

#### CK-05 · Click (+) navigates to cover PDP

**Coverage IDs:** G2-19278_TC05  
**Objective:** Confirm that clicking the (+) indicator navigates the user to the cover/default colour's PDP.

**Steps:**
1. On a product tile showing (+), click the (+) indicator.
2. Observe the resulting page.

**Expected Results:**
- Browser navigates to the PDP for the cover/default colour.
- The PDP URL matches the expected slug for the cover product.

**Pass Criteria:** Click on (+) lands on the cover colour PDP.  
**Fail Criteria:** Click on (+) leads to wrong PDP, error page, or no navigation.

---

### Section 4 — Stock Visibility

**Success Goal:** Out of stock colour swatches are visible on PLP.  
**Failure Goal:** Out of stock swatches are hidden or suppressed.

---

#### CK-06 · Out of stock colour swatches visible on PLP

**Coverage IDs:** G2-19278_TC06  
**Objective:** Confirm that colour variants that are out of stock still appear as swatches on the PLP.

**Steps:**
1. Identify a product that has at least one out of stock colour variant (coordinate with trading/QA for test data).
2. Navigate to a PLP where this product is listed.
3. Observe the swatch row.

**Expected Results:**
- The out of stock colour swatch is visible in the row below the tile.
- No swatch suppression occurs at PLP level.
- Any visual treatment for OOS is not expected at this stage (PLP scope only).

**Pass Criteria:** OOS colour swatch visible on PLP tile.  
**Fail Criteria:** OOS swatch hidden or removed from PLP tile.

---

### Section 5 — Deep Linking

**Success Goal:** Each swatch resolves to a correct colour-specific PDP URL.  
**Failure Goal:** Swatch links to wrong PDP, broken URL, or no navigation.

---

#### CK-07 · Deep link: swatch click navigates to correct colour PDP URL

**Coverage IDs:** G2-19278_TC07  
**Objective:** Verify that each individual swatch, when clicked, navigates directly to the correct PDP for that colour variant.

**Steps:**
1. On the PLP, select a product with multiple swatches.
2. Click each available swatch in turn.
3. Note the URL after each click (or copy the href before clicking).
4. Verify each URL corresponds to the expected product slug for that colour.

**Expected Results:**
- Each swatch generates a unique, valid URL for its respective colour variant.
- Clicking any swatch navigates to the correct colour's PDP.
- Back-navigation returns to the PLP.

**Pass Criteria:** Every clicked swatch resolves to its colour-specific PDP URL.  
**Fail Criteria:** Any swatch links to incorrect PDP, 404, or non-colour-specific URL.

---

### Section 6 — Dual Brand Coverage

**Success Goal:** Feature works identically on both NAP and MRP acceptance environments.  
**Failure Goal:** Feature missing or broken on one brand.

---

#### CK-08 · Colour swatches functional on both NAP and MRP

**Coverage IDs:** G2-19278_TC08  
**Objective:** Confirm the full colour swatch feature is deployed and functional on both Net-a-Porter and Mr Porter.

**Steps:**
1. Repeat checks CK-01 to CK-07 on acceptance.net-a-porter.com/en-de.
2. Repeat checks CK-01 to CK-07 on acceptance.mrporter.com/en-de.

**Expected Results:**
- Swatches visible, interactive, and deep-linked on NAP.
- Swatches visible, interactive, and deep-linked on MRP.
- Visual styling consistent with each brand's design language.

**Pass Criteria:** All swatch checks pass on both brands.  
**Fail Criteria:** Feature missing, broken, or not deployed on either brand.

---

## Exploratory and Design Observations

> These are non-AC observations backed by explicit Jira evidence. Do not substitute for AC checks above.

| Obs ID | Source Type | Jira Source | Observation Summary | How to Validate Manually | Expected Observation | Impact | Linked Coverage IDs | Evidence Notes | Status |
|--------|------------|------------|--------------------|--------------------------|--------------------|--------|--------------------|----|--------|
| OBS-01 | Comment | G2-18440 (comment 738669) | Bug G2-20786 was raised for some products' colour swatches fix; unclear if fully resolved | Identify products affected by the bug; check colour swatch display and interaction | Swatch display and interaction is consistent across all products; no product shows broken swatches | Medium — could affect checkout conversion | G2-19278_TC01, G2-19278_TC02 | G2-20786 referenced as fix; verify status of G2-20786 before sign-off | OBSERVE |
| OBS-02 | Story Note | G2-18439 (comment 734636) | A product should NOT appear in its own `alternativeColors` list; the backend was changed to exclude self-references | On PLP, verify that the displayed swatches do not include the current/cover product's own colour as a swatch in the overflow row | The cover product's own colour is either not shown as a duplicate swatch, or is shown correctly as the active/selected swatch | Low — data quality; affects user perception of colour count | G2-19278_TC03 | BE comment by ext.pjassu confirming behaviour; PR #2417 #2419 in hyena MERGED | OBSERVE |
| OBS-03 | Design | G2-18440 (description) | Figma designs provided for NAP and MRP; swatch layout and visual style should match brand designs | Compare rendered swatches on acceptance against Figma refs: [NAP](https://www.figma.com/design/AClD0sJnAeZlWbchDF8JHm/rds-nap-plp-template?node-id=2-5) · [MRP](https://www.figma.com/design/UDgQqNHggMzHOTqaBaZ37a/rds-mrp-plp-template?node-id=2-5) | Swatch size, spacing, highlight style, and (+) overflow indicator align with Figma designs for each brand | Medium — visual inconsistency may reduce brand confidence | G2-19278_TC01, G2-19278_TC08 | Figma links explicitly in G2-18440 description | OBSERVE |

---

## Coverage Parity Summary

| Matrix rows | 8 |
|---|---|
| Checklist checks | 8 (CK-01 to CK-08) |
| Every matrix row appears in checklist | YES |
| Every checklist item has a matrix row | YES |
| All explicit Epic/Story AC mapped | YES |
| Undocumented requirements added | NONE |
| Exploratory items in separate section | YES (3 observations) |

---

## Gaps and Inconsistencies

| Gap ID | Impacted Coverage IDs | Description |
|--------|----------------------|-------------|
| GAP-01 | G2-19278_TC08 | Epic-level GitHub development info returns no PRs/commits; evidence attributed to story-level PRs in atelier/mink/hyena |
| GAP-02 | G2-19278_TC06 | AC states OOS swatches are visible but notes "special treatment on PDP, not on PLP" — no explicit visual spec for OOS on PLP provided; out of scope item "Sold out visibility in Colour swatches - TBC" per G2-18440 Notes |
| GAP-03 | G2-19278_TC01–TC08 | G2-18439 Test Scenarios and G2-17553 Test Scenarios are both marked "TBC" — no formal test scenarios authored in linked stories; plan relies entirely on AC text |
| GAP-04 | OBS-01 | Bug G2-20786 is referenced but not linked to this Epic; its resolution status is unknown at time of plan generation — verify before UAT execution |
