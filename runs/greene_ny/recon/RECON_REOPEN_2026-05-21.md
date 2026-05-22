# Recon Re-Open — Primary Event Source Sweep — Greene County, NY

Framework: Xcerebro County Intelligence Harness v5.3.1
County: Greene County, New York (slug `greene_ny`)
Date: 2026-05-21
Trigger: operator correction — the original Phase 0 recon under-probed the
tax-distress and legal-notice primary sources and the Phase 3 escalation was
based on an incomplete matrix. This re-recon supersedes the 2026-05-19
classifications for the sources below. All access classes were **empirically
probed** (curl, browser User-Agent), never assumed.

---

## Empirical probe results (2026-05-21)

    Source                  Probe result
    ----------------------  --------------------------------------------------
    AAR Auctions            HTTP 200, nginx + WordPress, /servlet/Search.do.
    (aarauctions.com)       auctionId=6892 = Greene County tax-foreclosure
                            auction, 51 lots, FULLY SERVER-RENDERED (lot data
                            in page HTML). STDLIB-REACHABLE. No Cloudflare.
    ProsGar                 HTTP 200, Microsoft-IIS / ASP.NET, server-rendered
    (greenecounty.          form. /PROSSearch/AdvancedSearchFilters probed —
     prosgar.com)           filters are owner/address/value/class/beds-baths
                            ONLY. NO delinquency / arrears / years-due / tax-
                            sale filter. STDLIB-REACHABLE but ENRICHMENT.
    Column legal notices    HTTP 200, Next.js SPA, Cloudflare-fronted (serves
    (newyork.column.us)     the app shell, NOT a challenge). Notice data via a
                            backend API; api.column.us host responds but no
                            documented search endpoint was found. Stdlib-
                            reachability UNCONFIRMED — needs API discovery or
                            browser tooling.
    SearchIQS               HTTP 403, server: cloudflare, cf-mitigated:
    (searchiqs.com/nygre)   challenge — Cloudflare interactive challenge. NOT
                            stdlib-reachable. Operator-confirmed live in a
                            public guest browser session → SESSION-REQUIRED,
                            not a dead blocker.
    NYSCEF / WebCivil       HTTP 403, server: cloudflare, cf-mitigated:
    (iapps.courts.state.    challenge — same Cloudflare wall. NOT stdlib-
     ny.us)                 reachable; buildable via operator-seeded session.
    Surrogate's Court       Online = NYSCEF (Cloudflare) + WebSurrogate
                            (websurrogates.nycourts.gov, account-gated). Same
                            NY-courts wall.
    Tentative roll PDF      Operator-supplied bulk RPS flat file
                            (1932_26T_Tentative-Roll-150P1-Greenville.pdf) —
                            NOT present in the repo as of this re-recon.

---

## Corrections applied to the §16 Source-of-Record Matrix

1. **AAR tax-foreclosure auction — SUPPORTING → PRIMARY_EVENT_SOURCE.** It is
   the RPTL Article 11 in-rem tax-foreclosure disposition event. Server-
   rendered, stdlib-reachable, OPEN_PUBLIC. Tax Sale and Tax Lien Foreclosure
   upgrade to `LIVE_SOURCE_FOUND`. This is the buildable Phase 3 target.
2. **SearchIQS clerk land records — reclassified from "BLOCKED" to
   SESSION-REQUIRED** (`access_status: CAPTCHA_PROTECTED`, per-lead-type status
   `SOURCE_FOUND_CAPTCHA`). It is a free public guest portal behind a Cloudflare
   challenge — buildable via an operator-seeded session (approved §02.9 / §4.14
   strategy), not a dead end. The earlier Phase 3 "blocked" escalation is
   superseded.
3. **NYSCEF / WebCivil / Surrogate's Court** — same: `SOURCE_FOUND_CAPTCHA`,
   buildable via operator-seeded session.
4. **Column legal notices — added** as a candidate PRIMARY_EVENT_SOURCE for
   Foreclosure / Sheriff Sale (published notices). `access_status: UNKNOWN` —
   SPA, stdlib-reachability unconfirmed.
5. **ProsGar — added and classified ENRICHMENT_SOURCE.** Empirically confirmed
   it carries NO delinquency/arrears data; it cannot originate a tax-distress
   lead (§13). It is an assessment portal, not a tax-sale platform.
6. **Tentative assessment roll — added as ENRICHMENT_SOURCE** (bulk owner/AV/
   exemption roll; no arrears column; operator-supplied, not yet in repo).

## Corrected verdict

- `source_of_record_matrix.county_build_status`: **PARTIAL_BUILD_READY**
- `build_verdict`: **READY_WITH_BLOCKERS**
- Lead-type sweep (27): 2 LIVE_SOURCE_FOUND · 1 LIVE_SOURCE_FOUND_LIMITED_COVERAGE
  · 15 SOURCE_FOUND_CAPTCHA · 1 SOURCE_FOUND_PAID · 1 NEEDS_OPERATOR_REVIEW ·
  4 SOURCE_NOT_FOUND · 3 NOT_APPLICABLE_IN_STATE.

## Buildable now (stdlib-reachable), ranked by build_priority

1. **`tax_foreclosure_auction`** (AAR / NYSauctions) — PRIMARY, `mvp_required`.
   Server-rendered, stdlib-reachable. **Phase 3 first-lead-source target.**
2. `tax_foreclosure` (Treasurer petition PDF) — PRIMARY, `high_value`. Stdlib-
   reachable but a scanned PDF (OCR).
3. `parcel_master` (NYS ArcGIS) — ENRICHMENT, built in Phase 2.
4. `gis_parcels`, `prosgar_assessment` — ENRICHMENT.

Session-required (not stdlib-reachable; need an operator-seeded session /
stealth browser): `clerk_land_records`, `supreme_court_foreclosure`,
`surrogate_court_probate`, `webcivil_supreme`. Unconfirmed: `legal_notices_column`.

Authoritative machine-readable matrix: `source_of_record_matrix.json` and the
`source_of_record_matrix` block of `config/counties/greene_ny.json`.
