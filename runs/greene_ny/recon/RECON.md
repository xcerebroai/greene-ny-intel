# RECON.md — Greene County, New York

Framework: Xcerebro County Intelligence Harness v5.3.0
County: Greene County, New York · slug `greene_ny` · FIPS 36039
Phase: Phase 0 (County Source Recon and Onboarding Gate) — Recon Mode
Generated: 2026-05-19

This is the Phase 0 recon document required by `MASTER_PROMPT.md` §6. The
authoritative machine-readable output is `config/counties/greene_ny.json`. The
v5.3.0 Source-of-Record Matrix and the eight county-recon protocol artifacts
live under `runs/greene_ny/recon/`. This file is the operator-facing index.

---

## Verdict

**`build_verdict`: READY_TO_BUILD** — P0 GATE PASS.

Four verified PRIMARY lead sources are publicly accessible without operator
escalation; three are daily-refresh distress feeds. Enrichment is available. No
primary source is blocked, so Phase 0.5 (Auto-Resolve) was not triggered.

## County facts

- State legal framework: New York — **judicial foreclosure** (`state_rule_family`
  = `NY_judicial_foreclosure`). No non-judicial trustee sales.
- County seat: Catskill. 14 towns; 5 incorporated villages.
- Tax enforcement: County Treasurer, RPTL Article 11 **in-rem** tax foreclosure
  (no tax-lien-certificate sales).
- Two county web domains observed: `greenecountyny.gov` (current/official) and
  `greenegovernment.com` (legacy). GIS on `gcgovny.com`.

## Source map

| source_id | category / subtype | official_status | lead_value | access_pattern | grade | priority | build_priority | role |
|---|---|---|---|---|---|---|---|---|
| clerk_land_records | lead / clerk_recordings | OFFICIAL_VENDOR_PORTAL | LEAD_GENERATING | spa_with_api | A | P0 | mvp_required | PRIMARY |
| supreme_court_foreclosure | lead / court_civil | OFFICIAL_COURT | LEAD_GENERATING | static_html | A | P0 | mvp_required | PRIMARY |
| surrogate_court_probate | lead / court_probate | OFFICIAL_COURT | LEAD_GENERATING | static_html | A | P0 | high_value | PRIMARY |
| webcivil_supreme | lead / court_civil | OFFICIAL_COURT | LEAD_GENERATING | static_html | A | P0 | high_value | SUPPORTING |
| tax_foreclosure | lead / tax_delinquency | OFFICIAL_COUNTY | LEAD_GENERATING | static_html | A | P1 | high_value | PRIMARY |
| tax_foreclosure_auction | lead / tax_delinquency | OFFICIAL_VENDOR_PORTAL | LEAD_GENERATING | static_html | C | P1 | optional | SUPPORTING |
| parcel_master | enrichment / parcel_master | OFFICIAL_VENDOR_PORTAL | ENRICHMENT | spa_with_api | E | P2 | enrichment | ENRICHMENT |
| gis_parcels | enrichment / gis_parcels | OFFICIAL_COUNTY | ENRICHMENT | open_api | E | P2 | enrichment | ENRICHMENT |

### Source URLs

- **clerk_land_records** — Greene County Clerk land/official records via
  SearchIQS (Info Quick Solutions): https://www.searchiqs.com/nygre/ — verified
  from https://greenecountyny.gov/departments/county-clerk/ . Free guest search;
  $5/document print fee (non-commercial). Records: deeds, mortgages, mechanic /
  federal tax / state tax / welfare liens, judgments, lis pendens, UCC.
- **supreme_court_foreclosure** — NYS Supreme Court, Greene County, mortgage
  foreclosure + RPTL Art. 11 tax-foreclosure petitions via NYSCEF:
  https://iapps.courts.state.ny.us/nyscef/CaseSearch . Public, no login, free
  PDFs. Greene Supreme Court mandatory e-filing since 2020-10-21.
- **surrogate_court_probate** — Greene County Surrogate's Court probate via
  NYSCEF: https://iapps.courts.state.ny.us/nyscef/CaseSearch . Mandatory
  e-filing since 2021-02-16.
- **webcivil_supreme** — WebCivil Supreme statewide civil case search:
  https://iapps.courts.state.ny.us/webcivil/FCASMain . Supporting — case status
  / disposition; no document images.
- **tax_foreclosure** — Greene County Treasurer Annual Petition & Notice of
  Foreclosure: https://greenecountyny.gov/departments/treasurer/ (2025 PDF:
  /wp-content/uploads/2025/04/2025-Petition-and-Notice-of-Forclosure.pdf —
  scanned image, OCR required).
- **tax_foreclosure_auction** — Greene County tax-foreclosure auction via
  Absolute Auctions & Realty / NYSauctions.com:
  https://aarauctions.com/auctions/tax-foreclosures/ .
- **parcel_master** — Greene County RPTS property data, GAR Associates PROS:
  https://greenecounty.prosgar.com/ — verified from
  https://greenecountyny.gov/departments/rpts/ .
- **gis_parcels** — Greene County GIS ArcGIS REST:
  https://gis.gcgovny.com/arcgis/rest/services ; statewide bulk parcel data via
  the NYS GIS Clearinghouse (https://data.gis.ny.gov).

## Lead-type sweep (27 canonical types)

14 buildable (live / limited-coverage); 4 not found (Tax Sale Certificate,
Demolition, Condemnation, Eviction); 3 not applicable in NY (Trustee Sale,
Notice of Trustee Sale, Notice of Substitute Trustee Sale); 1 paid (Bankruptcy /
PACER); 1 operator review (Divorce — confidential under DRL §235). Full table:
`runs/greene_ny/recon/source_of_record_matrix.md`.

## P0 gate

**GATE PASS.** Daily-refresh distress sources unblocked: `supreme_court_
foreclosure` (NYSCEF, OPEN_PUBLIC), `clerk_land_records` (SearchIQS,
SEARCH_ONLY_PUBLIC), `surrogate_court_probate` (NYSCEF, OPEN_PUBLIC).

## Blocked sources

None. The HTTP 403 responses from SearchIQS and the NYS iApps portals are
automated-fetch bot-gating — a Build-Mode scrape-adapter concern (headless
browser), not a Phase-0 access blocker. Human guest/public access is
unobstructed.

## Open questions for the operator

1. SearchIQS guest mode — free document-image viewing or index search only?
   (Conservatively classified SEARCH_ONLY_PUBLIC; buildable either way.)
2. Is bankruptcy (PACER, NDNY) in scope? It is the only paid source.
3. County Clerk modern (post-2004) lis pendens index coverage — to confirm.
4. Verbatim SearchIQS / NYSCEF document-type code lists — to capture in Build
   Mode and populate each source's `doc_type_synonyms`.
5. `parcel_master` canonical field mapping — choose GAR PROS vs NYS GIS
   Clearinghouse as the ingest path and populate the `fields` map.

## Recon artifacts

`runs/greene_ny/recon/` — `source_discovery.md`, `source_verification.md`,
`portal_fingerprints.md`, `access_classification.md`,
`source_role_classification.md`, `document_type_discovery.md`,
`build_eligibility_handoff.md`, `recon_summary.md`,
`source_of_record_matrix.{json,md}`, `source_coverage_map.md`,
`api_discovery_report.md`, `operator_verified_sources.yml`,
`build_eligibility_report.md`, `fingerprints/<source_id>.fingerprint.json` (×8).
