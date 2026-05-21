# Phase 2 Build Report — First Adapter: parcel_master

County: Greene County, New York (slug `greene_ny`)
Framework: Xcerebro County Intelligence Harness v5.3.1
Phase: 2 — First Adapter (enrichment source, validates the matching layer)
Date: 2026-05-21

---

## Enrichment foundation only — NOT a lead source

This adapter is an **ENRICHMENT** source (`source_role: ENRICHMENT_SOURCE`,
`source_priority: P2`). Per the §13 Lead Origination Contract, enrichment
**cannot originate a lead row** — parcel / assessor / valuation data describes
what a property *is*, not a recorded distress *event*.

Phase 2 built an enrichment **foundation**. It produced **zero lead rows** and
**zero signals**: the translator run on the 3,000-parcel pull returned 3,000
parcels and **0 signals** — the correct, expected result for an enrichment
source.

Greene County therefore has **zero leads** at the end of Phase 2. No dashboard
is valid or complete from this output — a dashboard whose rows are enrichment
records is a No False Dashboard violation (§4.11 / §13.7). Lead rows must
originate from a verified **primary event source** (clerk recordings, court
filings, tax-foreclosure events). Producing those is Phase 3 onward; this
adapter only supplies owner / valuation context that *attaches to* leads once
a primary source has created them.

---

## What was built

`scrapers/parcel_master.py` — a Greene County parcel-master adapter that
ingests the **NYS GIS Clearinghouse** statewide public tax-parcel layer. It
**replaces** the Bexar County BCAD scraper that shipped in `scrapers/` as a
harness-extraction leftover (county-scoped file, correctly replaced per the
§4.31 universality contract).

## Source — NYS GIS Clearinghouse (operator-directed ingest)

Per the operator's REVIEW_GATE_1 answer (e), the parcel-master ingest is the
NYS GIS Clearinghouse full-county bulk layer, not the GAR PROS per-parcel web
portal:

- Service: `https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/FeatureServer`
- Layer: **1** (`NYS_Tax_Parcels_Public`). Layer 0 is only the county-footprint
  layer and is not used.
- Coverage: Greene County is one of the 36 counties that opted into NYS public
  sharing. `WHERE COUNTY_NAME='Greene'` → **38,418 parcels** (verified
  2026-05-21).
- Access: open ArcGIS REST query API — no login, no key, no CAPTCHA. This is
  an `open_api` source; **no browser-automation / SPA / hidden-API blocker was
  encountered**, so the §02.9 halt / escalation path was not needed.
- Refresh: annual (NYS publishes 2024–2025 roll data).

## Field mapping (derived from the documented 74-field schema)

The operator directed that the field map be derived from the bulk layer's
documented schema, not pre-assumed. The layer's 74-field schema was inspected
live; `scrapers/parcel_master.py` normalizes source fields → framework-
canonical `raw_payload` names (the §4.32 Path 1 contract — scraper normalizes,
translator stays protocol-agnostic, so **no `field_map` is required**):

    NYS layer field            framework-canonical raw_payload field
    -----------------------    -------------------------------------
    SWIS_SBL_ID                parcel_id          (county-unique key)
    PARCEL_ADDR / LOC_*        address            (uppercase situs)
    PRIMARY_OWNER (+ADD_OWNER) owner_name
    MAIL_ADDR / PO_BOX         owner_mailing_address
    MAIL_CITY / STATE / ZIP    owner_mailing_city / _state / _zip
    MUNI_NAME                  city               (situs town)
    LOC_ZIP                    zip
    TOTAL_AV                   assessed_value
    LAND_AV                    land_value
    TOTAL_AV - LAND_AV         improvement_value  (derived)
    YR_BLT                     year_built
    PROP_CLASS                 property_use
    ACRES / CALC_ACRES         acres

## Output contract

Writes `data/raw/parcel_master.jsonl` in the MASTER_PROMPT §4.32 wrapped
raw-record shape (`raw_record_id`, `source_id`, `source_url`,
`source_fetched_at`, `parser_confidence`, `raw_payload`). `source_url` is a
real per-record NYS query deep-link.

## Verification

- **Fixture test** — `runs/greene_ny/build/test_parcel_master.py` runs the
  scraper against a captured 25-parcel live response
  (`runs/greene_ny/build/fixtures/parcel_master/greene_sample_25.json`) with no
  network: **19/19 PASS**. Asserts the §4.32 wrapped shape, canonical
  `raw_payload` field names, spot-checked normalization (parcel_id, uppercased
  situs, owner name, co-owner fold-in, int coercion, out-of-state mailing,
  missing-year handling), and that the universal `parcel_master` translator
  consumes the output.
- **Live bounded pull** — `python3 scrapers/parcel_master.py --max-features
  3000` pulled 3,000 real Greene parcels in 38.9 s, exercising live fetch +
  3-page pagination. (The full 38,418-parcel county roll is the production
  refresh — run with no `--max-features`.)
- **Translator validation (matching-layer contract)** — feeding the 3,000
  records through `translate_parcel_master` yields 3,000 parcels and **0
  signals** (correct: enrichment sources never originate leads). 358 of the
  3,000 carry an out-of-state owner mailing address — a genuine absentee-owner
  enrichment signal for downstream scoring.
- **Framework gate suite** — `scaffold/tests/run_all.py` PASS 4/4. The new
  scraper's county-specific strings are confined to `scrapers/` (exempt from
  the county-agnostic regression scanner per §4.31.1).
- **County config** — `config/counties/greene_ny.json` `parcel_master` block
  updated (real URL, `translator: parcel_master`, `official_status:
  OFFICIAL_STATE`, ArcGIS fingerprint); re-written via `write_county_config.py`,
  schema VALIDATED.

## Known limitations

- The NYS public layer carries no exemption columns — the canonical
  `exempt_homestead / over_65 / disabled / veteran` flags are not populated. If
  exemption data is needed, a per-town assessment-roll ingest is a future
  enhancement.
- The Phase 2 proof pull is bounded to 3,000 parcels; the production refresh
  pulls the full county roll.
- Parcel↔signal join is exercised at the translator boundary here; full matcher
  integration against real lead signals is Phase 4.

## REVIEW_GATE_3 readiness

Per MASTER_PROMPT §6, REVIEW_GATE_3 reviews: first adapter produces normalized
output ✅; fixtures pass ✅ (19/19); sample records reviewed against the live
source ✅. Phase 3 (first lead-source adapter) cannot start without operator
sign-off.

## Files

- `scrapers/parcel_master.py` — Greene/NYS parcel-master adapter (replaces Bexar).
- `data/raw/parcel_master.jsonl` — 3,000 normalized parcels (Phase 2 artifact).
- `runs/greene_ny/build/test_parcel_master.py` — fixture test (19/19).
- `runs/greene_ny/build/fixtures/parcel_master/greene_sample_25.json` — live fixture.
- `config/counties/greene_ny.json` — `parcel_master` source block updated.
