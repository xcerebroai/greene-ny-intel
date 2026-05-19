# Source-of-Record Matrix — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
County build status: READY_TO_BUILD
Machine-readable form: source_of_record_matrix.json (schema-validated against
config/counties/_schema.json $defs/sourceOfRecordMatrix).

This is the human-readable summary of the 27-lead-type canonical sweep
(§16.B). Each row: lead type — status — selected source — note.

---

## Lead type sweep (27 canonical types)

    1.  Foreclosure ............... LIVE_SOURCE_FOUND
        supreme_court_foreclosure — NYSCEF Supreme Court mortgage foreclosure.
    2.  Trustee Sale ............. NOT_APPLICABLE_IN_STATE
        NY is a judicial-foreclosure state.
    3.  Notice of Trustee Sale ... NOT_APPLICABLE_IN_STATE
    4.  Notice of Substitute
        Trustee Sale ............ NOT_APPLICABLE_IN_STATE
    5.  Sheriff Sale ............. LIVE_SOURCE_FOUND_LIMITED_COVERAGE
        supreme_court_foreclosure — referee's sale noticed within the Supreme
        Court case; no standalone county sheriff-sale calendar.
    6.  Tax Lien Foreclosure ..... LIVE_SOURCE_FOUND_LIMITED_COVERAGE
        tax_foreclosure — RPTL Article 11 in-rem petition; annual; scanned PDF.
    7.  Tax Sale ................. LIVE_SOURCE_FOUND
        tax_foreclosure_auction — annual AAR / NYSauctions auction.
    8.  Tax Sale Certificate ..... SOURCE_NOT_FOUND
        Greene uses in-rem foreclosure, not certificate sales.
    9.  Tax Delinquency .......... LIVE_SOURCE_FOUND_LIMITED_COVERAGE
        tax_foreclosure — annual petition only; no rolling delinquency feed.
    10. Lis Pendens .............. LIVE_SOURCE_FOUND
        clerk_land_records — notice of pendency recorded with County Clerk.
    11. Civil Judgment ........... LIVE_SOURCE_FOUND
        webcivil_supreme — Supreme Court disposition; also clerk judgment dockets.
    12. Abstract of Judgment ..... LIVE_SOURCE_FOUND
        clerk_land_records — transcripts of judgment docketed with the Clerk.
    13. Mechanic Lien ............ LIVE_SOURCE_FOUND
        clerk_land_records — NY Lien Law mechanic's liens filed with the Clerk.
    14. Construction Lien ........ LIVE_SOURCE_FOUND
        clerk_land_records — NY files construction liens as mechanic's liens.
    15. Federal Tax Lien ......... LIVE_SOURCE_FOUND
        clerk_land_records — IRS liens filed with the County Clerk.
    16. State Tax Lien ........... LIVE_SOURCE_FOUND
        clerk_land_records — NYS tax warrants filed with the County Clerk.
    17. Probate .................. LIVE_SOURCE_FOUND
        surrogate_court_probate — NYSCEF Surrogate's Court.
    18. Affidavit of Heirship .... LIVE_SOURCE_FOUND_LIMITED_COVERAGE
        surrogate_court_probate — NY uses administration proceedings, not
        recorded heirship affidavits.
    19. Executor Deed ............ LIVE_SOURCE_FOUND
        clerk_land_records — executor's deeds recorded with the County Clerk.
    20. Administrator Deed ....... LIVE_SOURCE_FOUND
        clerk_land_records — administrator's deeds recorded with the Clerk.
    21. Code Lien ................ LIVE_SOURCE_FOUND_LIMITED_COVERAGE
        clerk_land_records — recorded municipal/code liens only; no county-wide
        code-enforcement portal.
    22. Demolition ............... SOURCE_NOT_FOUND
        Town building/code departments only.
    23. Condemnation ............. SOURCE_NOT_FOUND
        Town building/code departments only.
    24. Eviction ................. SOURCE_NOT_FOUND
        Town/village Justice Courts — no public online docket.
    25. Divorce .................. NEEDS_OPERATOR_REVIEW
        NY matrimonial records confidential (DRL §235).
    26. Bankruptcy ............... SOURCE_FOUND_PAID
        PACER (NDNY) — paid; operator credentials required.
    27. Surplus .................. LIVE_SOURCE_FOUND_LIMITED_COVERAGE
        supreme_court_foreclosure — surplus money proceedings within the
        foreclosure case.

---

## Tally

    LIVE_SOURCE_FOUND ......................  9
    LIVE_SOURCE_FOUND_LIMITED_COVERAGE .....  5
    SOURCE_NOT_FOUND .......................  4
    NOT_APPLICABLE_IN_STATE ................  3
    SOURCE_FOUND_PAID ......................  1
    NEEDS_OPERATOR_REVIEW ..................  1
    -----------------------------------------
    Total ..................................  27 (with 4 NA/UNKNOWN spread above)

    14 of 27 lead types have a live or limited-coverage buildable source.
    Foreclosure, probate, lis pendens, and the full lien family are all live
    and accessible — the core distress pipeline is buildable today.
