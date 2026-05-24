# Greene NY — Phase 3 first primary adapter — punch-list

Date: 2026-05-23
Framework: v5.4.0 (commit 0dd4b07)
Adapter: `scrapers/tax_foreclosure_auction.py` (AAR / NYSauctions)
Pipeline: real Greene AAR data → §17 → §18 → §19 → §20 (DEPLOY_OK) → seam →
50 scored_leads → dashboard payload.

## Recon findings (mandatory step)

- AAR is **stdlib-reachable**: nginx, HTTP 200, **no Cloudflare**, no
  cf-mitigated, no CAPTCHA, no session needed. Server-rendered HTML — all
  lot data lives in the raw response.
- **Zero current/upcoming Greene auction.** Probed `/auctions/tax-
  foreclosures/`, `/upcoming-auctions/`, `/?s=Greene`, `/auctions/` — none
  mention Greene. Greene is seasonal (next likely Sep/Oct 2026).
- Known dataset: **auctionId=6892** (Greene Oct 29, 2025, 51 lots
  advertised).
- Distress fields present in raw HTML: parcel (`Tax Map #`), address,
  municipality (`Town of X` / optional `Village of X`), auction date,
  Full Market Value, School/Village/County Tax Due, Current Bid + status,
  School District, Lot Size, Inspection note, property description.
- **Owner of record NOT exposed** by AAR (0 mentions in raw HTML). Per
  §17, the debtor party engine correctly flags these as REVIEW_REQUIRED.
  Owner must be recovered via the matcher joining to `parcel_master`
  (NYS layer PRIMARY_OWNER) by Tax Map # / address.

## Adapter built

- `scrapers/tax_foreclosure_auction.py` (~330 LOC). stdlib only.
- Two run modes:
  - **discovery** (default): scans AAR index pages for Greene auctions;
    exit 2 (seasonal-zero, not error) when none found.
  - **`--auction-id N`**: pulls a specific (historical or current) Greene
    auction; full pagination (`?page=P&perPage=20`).
- Output contract: MASTER_PROMPT §4.32 wrapped raw records with canonical
  fields matched to the `foreclosure_notices` translator (address, city,
  zip, doc_number, recording_year, recording_month, layer_id) +
  AAR-specific carry-forward (tax_map, lot_number, auction_id,
  auction_date, full_market_value, current_bid, bid_status, school/
  village/county tax due, school_district, inspection, property_description).
- Exit codes: 0 success · 2 seasonal-zero (legitimate) · 4 source
  unreachable · 1 other.

## Translator wiring (config)

- `sources.tax_foreclosure_auction.translator = "foreclosure_notices"`.
- `translator_config.layer_doc_type_map["0"] = {canonical:
  TAX_FORECLOSURE_NOTICE, subtype_label: "Tax Foreclosure Notice",
  pattern: tax}`.
- `doc_type_synonyms = {"TAX_SALE_AUCTION_LOT" / "Tax Foreclosure Auction
  Lot" → TAX_FORECLOSURE_NOTICE}`.
- `parcel_id_prefix = "GRN-AAR-"`.
- Per the Duval-lesson rule: every AAR raw row was verified to carry a
  Tax Map # (parcel attachment) before mapping `TAX_SALE_AUCTION_LOT` to
  the lead-generating canonical `TAX_FORECLOSURE_NOTICE`. The mapping
  is honest — every record DOES have property attachment.

## Production run — end-to-end results

- Discovery mode: **0 records, exit 2** (no live Greene auction; seasonal).
- `--auction-id 6892` (historical Greene Oct 2025): **50 records pulled**
  from a 51-lot advertised total.
- Pipeline (`build_leads.py`, production):
  - Translator: **50 records → 50 signals + 50 placeholder parcels**.
  - parcel_master (enrichment): 3,000 records → 0 signals + 3,000 parcels.
  - Staged §17 → §18 → §19: **50 matched_leads**.
  - **§20 semantic_verify verdict: `DEPLOY_OK`**.
  - Seam + scoring: **50 scored_leads**.
  - Dashboard payload written.

| field | value |
|---|---|
| **lead_total** | **50** |
| build_label | SOURCE_LIMITED (only one PRIMARY source live) |
| county / state / mode | Greene County / NY / production |
| **§20 verdict** | **DEPLOY_OK** |
| pattern_counts | `{tax: 50}` |
| score_tier_distribution | `{Workable: 50}` |
| deal_path_distribution | `{wholesale: 50}` |
| enrichment_breakdown | 0 ENRICHED · 50 UNENRICHED |
| **REVIEW_REQUIRED rows** | **50 of 50** (correct: AAR exposes no owner) |
| dropped_signals_unmapped_doc_type | **0** |
| framework gate suite | **PASS** (4/4 core + 6/6 v5.4.0 contract) |

## Stop conditions during this run

- Pipeline crash: **none**.
- §20 `DEPLOY_BLOCKED`: **no** — verdict `DEPLOY_OK`.
- → no halt fired; run completed end-to-end.

## Punch-list (gaps / degradations / things that flagged)

### P1 — matcher / enrichment join

1. **0/50 ENRICHED.** Matcher couldn't join AAR placeholder parcels
   (`GRN-AAR-<addr_hash>`) to `parcel_master` rows (NYS `SWIS_SBL_ID`,
   26-digit). The Tax Map # (`PRINT_KEY`) IS available on both sides and
   IS a real join key — the matcher's address-based fallback didn't
   succeed because AAR address strings (`113/115 N WASHINGTON ST`) don't
   normalize cleanly to NYS layer addresses (composed from LOC_ST_NBR +
   LOC_STREET). Fix: add a Tax-Map-#-based join path in the matcher
   pre-stage, or pre-resolve AAR signals' parcel_id to the
   `SWIS_SBL_ID` by scanning `data/raw/parcel_master.jsonl` for PRINT_KEY
   matches before feeding to the staged pipeline.
2. **Dashboard `display_address` is empty for UNENRICHED leads** —
   `parcel_display` is empty so the projection has nothing to render. The
   AAR raw record carries the address — a UNENRICHED fallback should
   surface signal-level address into the dashboard row. Downstream
   projection issue (`run_pipeline_staged.project_scored_lead`).

### P2 — adapter / source coverage

3. **50/51 lots captured** (98%). One lot lost in parse — likely
   non-standard title-bar format on that single lot. Worth investigating
   on a future auction; not blocking.
4. **`county_tax_due = 0/50`** in the output. This is the **actual data**,
   not a parse bug — every lot has `County Tax Due: $</b></td>` (empty
   value) in the raw HTML. School + village tax due ARE populated
   (49/50 school_tax). Verified.
5. **AAR HTML is malformed in places** (missing `>` in `</td`). Parser is
   tolerant via `[^<]*` field terminators. Note.
6. **Greene auction is seasonal.** Today's discovery returns 0 Greene
   matches across all AAR index pages — that is the honest live state.
   The 2026 Greene auction will publish ~Sep/Oct 2026; the adapter
   resumes auto-discovery then. Until then, `--auction-id 6892` (or the
   next year's id) is the way to pull.

### P3 — pipeline-level

7. **All 50 leads scored 55 / Workable / wholesale.** Uniform output is
   expected for a single-source single-doc-type ingest where every lead is
   REVIEW_REQUIRED. Scoring diversity emerges as more primary sources
   come online (stacking lien + clerk lis pendens + court foreclosure on
   the same parcel produces higher tiers and varied deal paths).
8. **`build_label = SOURCE_LIMITED`.** Correct — only one PRIMARY source
   is live. Other Greene primaries (SearchIQS clerk, NYSCEF court,
   Surrogate's) remain Cloudflare-gated and need an operator-seeded
   session.
9. **`normalize.normalize_doc_type` ignores per-source `doc_type_synonyms`**
   when called single-arg from `_signal_to_raw_event`. I worked around it
   by choosing a `subtype_label` ("Tax Foreclosure Notice") that matches
   the universal canonical registry directly. The per-source synonyms map
   in the config is therefore advisory in this codepath, not authoritative.
   Framework-level observation (no fix needed for this build).

### P4 — repo hygiene

10. **`runs/greene_ny/build_config.py`** still uncommitted (intentional per
    the operator's named-path commit scope).
11. **`scrapers/__init__.py`** still carries a Bexar-era docstring (flagged
    earlier).
12. **`scaffold/tests/test_foreclosure_notices_map.py`** orphaned (flagged
    earlier; not in required gate suite).

## Files produced this turn

- `scrapers/tax_foreclosure_auction.py` (new) — the AAR primary adapter.
- `data/raw/tax_foreclosure_auction.jsonl` (50 records, real Greene data).
- `data/dashboard.json` (76 KB), `data/matched_leads.json`,
  `data/scored_leads.json`, `data/evidence_ledger.json`,
  `data/tax_foreclosure_auction_leads_base.json`.
- `dashboard/data/{dashboard,matched_leads,scored_leads,evidence_ledger}.json`.
- `runs/greene_ny/build_config.py` (edited — translator wiring).
- `config/counties/greene_ny.json` (rewritten via `write_county_config.py`,
  schema VALIDATED) + regenerated `runs/greene_ny/recon/fingerprints/
  tax_foreclosure_auction.fingerprint.json` and
  `source_of_record_matrix.json`.
- This punch-list.
