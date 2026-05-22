# Source-of-Record Matrix — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.1
Generated: 2026-05-19 · **Corrected: 2026-05-21 (primary-event-source re-recon —
see RECON_REOPEN_2026-05-21.md)**
County build status: **PARTIAL_BUILD_READY**
Machine-readable form: source_of_record_matrix.json (schema-validated).

Human-readable summary of the 27-lead-type canonical sweep (§16.B). Access was
empirically probed 2026-05-21.

---

## Lead type sweep (27 canonical types)

    1.  Foreclosure ............... SOURCE_FOUND_CAPTCHA
        supreme_court_foreclosure (NYSCEF) — verified, Cloudflare-gated;
        seeded-session buildable. Column legal notices = alt published path.
    2.  Trustee Sale ............. NOT_APPLICABLE_IN_STATE  (NY is judicial)
    3.  Notice of Trustee Sale ... NOT_APPLICABLE_IN_STATE
    4.  Notice of Substitute
        Trustee Sale ............ NOT_APPLICABLE_IN_STATE
    5.  Sheriff Sale ............. SOURCE_FOUND_CAPTCHA
        Referee sale inside the Supreme Court case (NYSCEF) + Column notices.
    6.  Tax Lien Foreclosure ..... LIVE_SOURCE_FOUND
        tax_foreclosure_auction (AAR) — server-rendered, STDLIB-REACHABLE.
    7.  Tax Sale ................. LIVE_SOURCE_FOUND
        tax_foreclosure_auction (AAR auctionId=6892, 51 lots). BUILD TARGET.
    8.  Tax Sale Certificate ..... SOURCE_NOT_FOUND  (Greene uses in-rem)
    9.  Tax Delinquency .......... LIVE_SOURCE_FOUND_LIMITED_COVERAGE
        tax_foreclosure — Treasurer annual petition PDF (stdlib, OCR). ProsGar
        + tentative roll probed → ENRICHMENT only (no arrears column).
    10. Lis Pendens .............. SOURCE_FOUND_CAPTCHA
        clerk_land_records (SearchIQS) — verified live, Cloudflare-gated.
    11. Civil Judgment ........... SOURCE_FOUND_CAPTCHA   (clerk / WebCivil)
    12. Abstract of Judgment ..... SOURCE_FOUND_CAPTCHA   (clerk)
    13. Mechanic Lien ............ SOURCE_FOUND_CAPTCHA   (clerk)
    14. Construction Lien ........ SOURCE_FOUND_CAPTCHA   (clerk)
    15. Federal Tax Lien ......... SOURCE_FOUND_CAPTCHA   (clerk)
    16. State Tax Lien ........... SOURCE_FOUND_CAPTCHA   (clerk — TAX WARRANTS)
    17. Probate .................. SOURCE_FOUND_CAPTCHA   (Surrogate / NYSCEF)
    18. Affidavit of Heirship .... SOURCE_FOUND_CAPTCHA   (Surrogate / NYSCEF)
    19. Executor Deed ............ SOURCE_FOUND_CAPTCHA   (clerk)
    20. Administrator Deed ....... SOURCE_FOUND_CAPTCHA   (clerk)
    21. Code Lien ................ SOURCE_FOUND_CAPTCHA   (clerk — recorded liens)
    22. Demolition ............... SOURCE_NOT_FOUND       (per-town only)
    23. Condemnation ............. SOURCE_NOT_FOUND       (per-town only)
    24. Eviction ................. SOURCE_NOT_FOUND       (town justice courts)
    25. Divorce .................. NEEDS_OPERATOR_REVIEW  (DRL §235 confidential)
    26. Bankruptcy ............... SOURCE_FOUND_PAID      (PACER NDNY)
    27. Surplus .................. SOURCE_FOUND_CAPTCHA   (NYSCEF + AAR overage)

---

## Tally

    LIVE_SOURCE_FOUND ..................... 2   (Tax Lien Foreclosure, Tax Sale)
    LIVE_SOURCE_FOUND_LIMITED_COVERAGE .... 1   (Tax Delinquency)
    SOURCE_FOUND_CAPTCHA ................. 15   (clerk + court — seeded-session)
    SOURCE_FOUND_PAID ..................... 1   (Bankruptcy)
    NEEDS_OPERATOR_REVIEW ................. 1   (Divorce)
    SOURCE_NOT_FOUND ...................... 4
    NOT_APPLICABLE_IN_STATE ............... 3
    -----------------------------------------
    Total ................................ 27

## Source roles

    PRIMARY_EVENT_SOURCE   tax_foreclosure_auction (AAR) · tax_foreclosure
                           (Treasurer petition) · clerk_land_records ·
                           supreme_court_foreclosure · surrogate_court_probate ·
                           legal_notices_column · pacer_ndny
    SUPPORTING_EVENT_SRC   webcivil_supreme
    ENRICHMENT_SOURCE      parcel_master (NYS ArcGIS) · gis_parcels ·
                           prosgar_assessment · tentative_assessment_roll

## Stdlib-reachable now (buildable without browser tooling)

    tax_foreclosure_auction  PRIMARY   server-rendered  -> Phase 3 build target
    tax_foreclosure          PRIMARY   PDF (OCR)
    parcel_master            ENRICH    ArcGIS API (built — Phase 2)
    gis_parcels              ENRICH    ArcGIS API
    prosgar_assessment       ENRICH    server-rendered ASP.NET

## Session-required (operator-seeded session / stealth browser)

    clerk_land_records, supreme_court_foreclosure, surrogate_court_probate,
    webcivil_supreme — all behind a Cloudflare interactive challenge.
    legal_notices_column — Next.js SPA; reachability unconfirmed.
