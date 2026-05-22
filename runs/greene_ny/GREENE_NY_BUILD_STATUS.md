# GREENE COUNTY, NY — BUILD STATUS

Framework: Xcerebro County Intelligence Harness v5.3.1
County: Greene County, New York · slug `greene_ny` · FIPS 36039
Status date: 2026-05-21 (updated after the primary-event-source re-recon)
Overall state: **PARTIAL_BUILD_READY** — Phase 3 buildable; no longer halted.

> Filed under `runs/greene_ny/` (not the repo root): repo-root markdown is
> scanned by the county-agnostic regression gate. County build artifacts live
> under `runs/<slug>/` per §02.13.

---

## Headline

The earlier Phase 3 "blocked" halt was based on an **incomplete Source-of-Record
Matrix** — original Phase 0 recon probed only SearchIQS and NYSCEF, both
Cloudflare-walled, and stopped. A re-recon on 2026-05-21 (operator-directed)
probed the full primary-event-source set and **found a stdlib-reachable primary
event source**: the AAR / NYSauctions tax-foreclosure auction. The §16 matrix
has been corrected; `county_build_status` is now **PARTIAL_BUILD_READY**.

Phase 3 is **buildable now** against the tax-foreclosure auction. The county
clerk and court sources remain access-constrained (Cloudflare challenge) but are
**session-required, not dead** — buildable via an operator-seeded session.

## Phase status

| Phase | Description | Status |
|---|---|---|
| 0 | County source recon + onboarding gate | ✅ COMPLETE (re-reconned 2026-05-21) |
| 1 | Synthetic data harness | ✅ COMPLETE — 110/0 under v5.3.1 |
| 2 | First adapter — `parcel_master` (ENRICHMENT FOUNDATION) | ✅ COMPLETE — 0 leads (correct) |
| 3 | First primary event source (lead origination) | ▶ READY — target: `tax_foreclosure_auction` |
| 4–8 | Matcher, dashboard, verification, refresh, summary | ⏸ not started |

## Corrected §16 matrix (2026-05-21 re-recon)

- `county_build_status`: **PARTIAL_BUILD_READY** · `build_verdict`:
  **READY_WITH_BLOCKERS**.
- 27-lead-type sweep: 2 `LIVE_SOURCE_FOUND` · 1 `LIVE_SOURCE_FOUND_LIMITED_
  COVERAGE` · 15 `SOURCE_FOUND_CAPTCHA` · 1 `SOURCE_FOUND_PAID` · 1
  `NEEDS_OPERATOR_REVIEW` · 4 `SOURCE_NOT_FOUND` · 3 `NOT_APPLICABLE_IN_STATE`.
- Detail: `runs/greene_ny/recon/RECON_REOPEN_2026-05-21.md`,
  `source_of_record_matrix.{json,md}`, `source_coverage_map.md`.

### Stdlib-reachable PRIMARY event sources (buildable now)

1. **`tax_foreclosure_auction`** (AAR / NYSauctions) — `mvp_required`.
   Server-rendered tax-foreclosure auction; confirmed Greene auction 6892
   (51 lots). **Phase 3 first-lead-source target.**
2. `tax_foreclosure` (Treasurer annual in-rem petition) — `high_value`.
   Stdlib-reachable but a scanned PDF (OCR).

### Session-required PRIMARY sources (operator-seeded session / stealth browser)

`clerk_land_records` (SearchIQS), `supreme_court_foreclosure`,
`surrogate_court_probate`, `webcivil_supreme` — all behind a Cloudflare
interactive challenge. Free public portals; buildable via an operator-seeded
session (`cf_clearance` + cookies) — approved §02.9 / §4.14 strategy.
`legal_notices_column` — Next.js SPA, reachability unconfirmed.

### Enrichment (never originates a lead — §13)

`parcel_master` (NYS ArcGIS — built Phase 2), `gis_parcels`,
`prosgar_assessment` (probed: assessment only, no delinquency data),
`tentative_assessment_roll` (operator-supplied bulk roll, not yet in repo).

## Resume point

Phase 3 — build the `tax_foreclosure_auction` adapter against the
stdlib-reachable AAR auction (RPTL Article 11 in-rem tax-foreclosure
disposition — a primary distress event that originates Tax Sale / Tax Lien
Foreclosure lead rows). Then Phase 4 (matcher) → Phase 8. The clerk/court
sources join the build once an operator-seeded session is provided.

## Open items

- `runs/greene_ny/build_config.py` carries uncommitted edits — kept uncommitted
  per the operator's explicit named-path commit scope.
- The earlier `runs/greene_ny/build/halt_log.md` + `escalations/phase3_*` record
  the superseded halt; retained as audit history.
- `scaffold/tests/test_foreclosure_notices_map.py` is orphaned by the Bexar
  scraper deletion (not in the required gate suite; framework-team item).
