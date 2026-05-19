# Build Eligibility Report — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Per MASTER_PROMPT.md §4.35 and knowledge_base/architecture/16_source_of_
record_matrix.md §16.A. Derived from source_of_record_matrix.json.

---

## County build status

    READY_TO_BUILD

## Build mode classification (if approved)

    FULL_BUILD — county_build_status is READY_TO_BUILD and the primary event
    sources required for the core distress pipeline (clerk land records, Supreme
    Court foreclosure, Surrogate's Court probate) are all LIVE_SOURCE_FOUND and
    accessible. Build all live sources concurrently per the §02 build-mode
    protocol; the tax-foreclosure source is P1 (annual cadence) and is built
    alongside as a high-value secondary distress feed.

## P0 gate

    GATE PASS. At least one P0 daily-refresh distress source is unblocked and
    pulling fresh distress events:
        - supreme_court_foreclosure (NYSCEF) — OPEN_PUBLIC, daily.
        - clerk_land_records (SearchIQS) — SEARCH_ONLY_PUBLIC, daily.
        - surrogate_court_probate (NYSCEF) — OPEN_PUBLIC, daily.

## Lead-type coverage summary

    Buildable now (live / limited-coverage) ......... 14 lead types
    Not found (no online county source) .............  4 lead types
    Not applicable in New York .......................  3 lead types
    Operator review / paid ...........................  2 lead types
    (Sweep total per §16.B: 27)

## Required recon artifacts — present

    [x] runs/greene_ny/recon/source_of_record_matrix.json   (schema-validated)
    [x] runs/greene_ny/recon/source_of_record_matrix.md
    [x] runs/greene_ny/recon/source_coverage_map.md
    [x] runs/greene_ny/recon/api_discovery_report.md
    [x] runs/greene_ny/recon/operator_verified_sources.yml
    [x] runs/greene_ny/recon/fingerprints/<source_id>.fingerprint.json  (8 files)
    [x] runs/greene_ny/recon/build_eligibility_report.md  (this file)
    [x] runs/greene_ny/recon/source_discovery.md
    [x] runs/greene_ny/recon/source_verification.md
    [x] runs/greene_ny/recon/portal_fingerprints.md
    [x] runs/greene_ny/recon/access_classification.md
    [x] runs/greene_ny/recon/source_role_classification.md
    [x] runs/greene_ny/recon/document_type_discovery.md
    [x] runs/greene_ny/recon/build_eligibility_handoff.md
    [x] runs/greene_ny/recon/recon_summary.md

## v5.3.0 mandatory recon sub-steps

    Lead type sweep (§01.21) ................ DONE — all 27 types classified.
    PDF / sample document inspection (§01.22)  PARTIAL — the 2025 tax-foreclosure
        Petition & Notice of Foreclosure was fetched and inspected (result:
        scanned CCITT-fax image PDF, OCR required). Individual clerk instruments
        and NYSCEF case PDFs were NOT extracted — recon is metadata-only
        (§01.17) and those portals bot-gate automated fetch; document-level
        field capture is scheduled for Build Mode Phase 0.F follow-up. Recorded
        honestly as open questions on the affected sources.
    Documented API discovery (§01.23) ....... DONE — see api_discovery_report.md.
        Found: ArcGIS REST (county GIS + NYS GIS Clearinghouse). None for the
        primary lead portals.
    Bulk-data availability (§01.24) ......... DONE — clerk/court = BATCH_QUERY;
        tax foreclosure = FULL_COUNTY_BULK (annual petition); enrichment =
        FULL_COUNTY_BULK (NYS GIS Clearinghouse). No PER_RECORD_ONLY source.

## Verdict

    build_verdict: READY_TO_BUILD
    Phase 0.5 (Auto-Resolve Blockers): NOT TRIGGERED — no blocked / low-
    confidence primary source.
    Build Mode is authorized once the operator approves at the Build Mode
    Approval Gate (MASTER_PROMPT §4.15).
