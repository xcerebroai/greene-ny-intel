# GREENE COUNTY, NY — BUILD STATUS

Framework: Xcerebro County Intelligence Harness v5.3.1
County: Greene County, New York · slug `greene_ny` · FIPS 36039
Status date: 2026-05-21
Overall state: **HALTED at Phase 3** — temporary infrastructure hold.

> Filed under `runs/greene_ny/` (not the repo root): repo-root markdown is
> scanned by the county-agnostic regression gate, which forbids county/state
> names in universal-scope files. County build artifacts live under
> `runs/<slug>/` per §02.13.

---

## Headline

Greene County is **buildable** — Phase 0 recon proved verified primary event
sources exist (`build_verdict: READY_TO_BUILD`). Phases 0, 1, and 2 are
complete. The build is **halted at Phase 3** because every Greene County
primary event source sits behind a **Cloudflare interactive challenge** that
the current execution environment cannot pass. This is an **infrastructure
hold, not a final delivery** — Phases 0–2 carry over unchanged; the build
resumes at Phase 3 on browser-capable infrastructure.

Greene County currently has **zero leads**. No dashboard has been built, and
none is valid until lead rows originate from a primary event source (§4.11
No False Dashboard / §13 Lead Origination Contract).

---

## Phase status

| Phase | Description | Status |
|---|---|---|
| 0 | County source recon + onboarding gate | ✅ COMPLETE |
| 1 | Synthetic data harness | ✅ COMPLETE |
| 2 | First adapter — `parcel_master` (ENRICHMENT FOUNDATION) | ✅ COMPLETE |
| 3 | First primary event source (lead origination) | ⛔ BLOCKED |
| 4–8 | Matcher, dashboard, verification, refresh, summary | ⏸ not started |

### Phase 0 — COMPLETE
`config/counties/greene_ny.json` written + schema-validated; `build_verdict
READY_TO_BUILD`; P0 gate PASS. 8 verified sources; 27-lead-type Source-of-Record
Matrix; 16 recon artifacts in `runs/greene_ny/recon/`. REVIEW_GATE_1 APPROVED.

### Phase 1 — COMPLETE
Synthetic harness `verify_synthetic_harness.py` passes 110/0 under v5.3.1. (The
earlier v5.3.0 `build_leads.py` hardcoded-config halt was resolved by the
v5.3.1 `_auto_discover_county_config` fix.) REVIEW_GATE_2 APPROVED.

### Phase 2 — COMPLETE (enrichment foundation only)
`scrapers/parcel_master.py` ingests the NYS GIS Clearinghouse
`NYS_Tax_Parcels_Public` ArcGIS layer (Greene = 38,418 parcels; open REST API).
Fixture test 19/19; live 3,000-parcel pull verified. **This is an ENRICHMENT
source — it produced 0 lead rows / 0 signals, which is correct: enrichment
cannot originate leads (§13).** It supplies owner/valuation context only.
REVIEW_GATE_3 APPROVED. Report: `runs/greene_ny/build/phase2_parcel_master.md`.

### Phase 3 — BLOCKED
First primary event source = County Clerk land records (`clerk_land_records`,
SearchIQS). **Blocked by a Cloudflare interactive challenge.**

---

## Phase 3 blocker — specifics

Empirically confirmed 2026-05-21 with a standard browser User-Agent (curl):

    searchiqs.com/nygre/             -> HTTP 403  server: cloudflare
    searchiqs.com/nygre/Login.aspx   -> HTTP 403  cf-mitigated: challenge
                                        "Just a moment..." JS-challenge page
    iapps.courts.state.ny.us/nyscef/CaseSearch  -> HTTP 403  (same Cloudflare gate)
    iapps.courts.state.ny.us/webcivil/FCASMain  -> HTTP 403  (same Cloudflare gate)

Both the County Clerk portal and the alternate primary (NYS courts) are behind
the identical Cloudflare `cf-mitigated: challenge`. No documented API exists for
any of them (recon §01.23). Access status: **`BLOCKED`** (§01.9). Blocker class:
**HARD BLOCKER** (§01.13) — a Cloudflare interactive challenge, not a simple
user-agent or cookie gate.

The current execution environment provides only non-browser HTTP clients
(`urllib`, `curl`, `WebFetch`) — none can pass a Cloudflare challenge. Per
operator directive, §01.17, and §02.9, no workaround was attempted and no
records were fabricated. Halting is the designed, correct outcome.

Detail + operator-decision form:
`runs/greene_ny/build/escalations/phase3_primary_event_source_blocked.md`.

---

## Exact infrastructure required to resume

Phase 3 resumes on **browser-capable infrastructure**. Approved framework
access strategies (FRAMEWORK_VERSION.json locked rules), in recommended order:

1. **Operator-seeded session** — operator solves the Cloudflare challenge +
   SearchIQS guest login once in a real browser, exports the `cf_clearance` +
   ASP.NET session cookies; the framework replays them. Cheapest path for an
   immediate Phase 3 proof. `cf_clearance` expires in hours, so daily refresh
   needs periodic re-seeding or option 2.
2. **Stealth-browser worker** — headless Chromium with stealth/undetected
   tooling (Playwright + stealth, `nodriver`, undetected-chromedriver) on
   infrastructure that can run a real browser; possibly + a residential proxy
   if Cloudflare IP-reputation-gates the host. This is the durable path for a
   daily-refresh product.
3. **Operator-assisted manual pull / standing records delivery** from the
   Greene County Clerk (non-automated last resort).

None of these is available in the current sandboxed environment.

---

## What carries over (no rework on resume)

- `config/counties/greene_ny.json` — verified, schema-valid (Phase 0).
- `runs/greene_ny/recon/` — full recon dossier + Source-of-Record Matrix.
- `runs/greene_ny/gates/REVIEW_GATE_1..3.signoff.json` — operator approvals.
- `scrapers/parcel_master.py` + `runs/greene_ny/build/` — Phase 2 enrichment
  adapter, fixture, test, report.
- Synthetic harness (Phase 1) — green under v5.3.1.

## Resume point

Build resumes at **Phase 3** — build the `clerk_land_records` adapter against
the (now reachable) SearchIQS portal, originate the first primary-event lead
rows, then continue Phase 4 (matcher + review queue) → Phase 8.

## Open items (non-blocking, for resume)

- `runs/greene_ny/build_config.py` carries an uncommitted Phase 2 edit (the
  `parcel_master` block update that generated the committed config). Kept
  uncommitted per the operator's explicit named-path commit scope — operator
  may commit or discard it.
- Deleting the Bexar leftover `scrapers/foreclosure_notices_map.py` orphaned
  the framework test `scaffold/tests/test_foreclosure_notices_map.py`. That
  test is NOT in the required gate suite (`run_all.py` still passes 4/4); the
  framework team may retire the orphan in a future patch. Not modified here —
  `scaffold/` is universal framework code, out of scope for a county build.
- `scrapers/__init__.py` still carries a Bexar-era docstring; not a scraper
  and not in any commit scope given — flagged for a future cleanup.
