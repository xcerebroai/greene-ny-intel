# Build Eligibility Gate Handoff — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Method: knowledge_base/protocols/01_county_recon.md §01.15 / §01.16.

---

## Counts

    VERIFIED_OFFICIAL sources ............... 8
    By role:
        PRIMARY_LEAD_SOURCE ................. 4  (clerk_land_records,
                                               supreme_court_foreclosure,
                                               surrogate_court_probate,
                                               tax_foreclosure)
        SUPPORTING_LEAD_SOURCE .............. 2  (webcivil_supreme,
                                               tax_foreclosure_auction)
        ENRICHMENT_SOURCE .................. 2  (parcel_master, gis_parcels)
    By access classification:
        OPEN_PUBLIC ........................ 7
        SEARCH_ONLY_PUBLIC ................. 1  (clerk_land_records)
        blocked / login / paid / captcha ... 0

## Accessible primary sources

    4 of 4 PRIMARY_LEAD_SOURCE entries are accessible without operator
    escalation (OPEN_PUBLIC or SEARCH_ONLY_PUBLIC):

        clerk_land_records          SEARCH_ONLY_PUBLIC  (free guest search;
                                    document print fee only — buildable)
        supreme_court_foreclosure   OPEN_PUBLIC
        surrogate_court_probate     OPEN_PUBLIC
        tax_foreclosure             OPEN_PUBLIC (annual PDF; OCR required)

## Accessible primary document / lead types

    From the §16 lead-type sweep, the following originate from accessible
    primary sources and are buildable now:

        Foreclosure, Sheriff Sale (referee), Lis Pendens, Surplus
            <- supreme_court_foreclosure (NYSCEF)
        Probate, Affidavit of Heirship
            <- surrogate_court_probate (NYSCEF)
        Mechanic / Construction Lien, Federal Tax Lien, State Tax Lien,
        Abstract of Judgment, Civil Judgment, Executor Deed,
        Administrator Deed, Code Lien (recorded)
            <- clerk_land_records (SearchIQS)
        Tax Lien Foreclosure, Tax Delinquency, Tax Sale
            <- tax_foreclosure / tax_foreclosure_auction (annual cadence, P1)

## Blockers by type

    Technical blockers ....... 0  (the HTTP 403 responses on SearchIQS / iApps
                                  are automated-fetch bot-gating — a Build-Mode
                                  scrape-adapter concern, resolved with a
                                  headless browser; NOT a Phase-0 access
                                  blocker, since human guest/public access is
                                  unobstructed)
    Permission blockers ...... 0 for the buildable lead set. (Bankruptcy/PACER
                                  is paid, but bankruptcy is not required and is
                                  routed to operator review.)
    Hard blockers ............ 0
    Unknown blockers ......... 0

    Because no required P0 primary source carries verification_confidence LOW
    or source_role BLOCKED_SOURCE and no source has a non-empty blocker_type,
    Phase 0.5 (Auto-Resolve Blockers) was NOT triggered (MASTER_PROMPT §4.29.2).

## Recommended provisional verdict

    READY_TO_BUILD

    Justification: at least one verified primary lead source is fully accessible
    without operator escalation (in fact four are), each with at least one
    accessible primary document/lead type, and enrichment (parcel master, GIS)
    is available. No critical blocker prevents Phase 1+ work. This satisfies the
    §01.16 / §4.10 definition of READY_TO_BUILD.

## Justification trail

    clerk_land_records — VERIFIED_OFFICIAL (vendor portal linked from the County
        Clerk's official page) -> PRIMARY_LEAD_SOURCE -> SEARCH_ONLY_PUBLIC ->
        contributes the lien family, lis pendens, judgment dockets, estate deeds.
        P0. Buildable.
    supreme_court_foreclosure — VERIFIED_OFFICIAL (NYS court system) ->
        PRIMARY_LEAD_SOURCE -> OPEN_PUBLIC -> contributes foreclosure, sheriff/
        referee sale, lis pendens, surplus, RPTL Art.11 petitions. P0. Buildable.
    surrogate_court_probate — VERIFIED_OFFICIAL (NYS court system) ->
        PRIMARY_LEAD_SOURCE -> OPEN_PUBLIC -> contributes probate / estate. P0.
        Buildable.
    webcivil_supreme — VERIFIED_OFFICIAL -> SUPPORTING_LEAD_SOURCE -> OPEN_PUBLIC
        -> case-status / lifecycle confirmation. Does not originate leads.
    tax_foreclosure — VERIFIED_OFFICIAL (County Treasurer) ->
        PRIMARY_LEAD_SOURCE -> OPEN_PUBLIC -> contributes tax-foreclosure / tax-
        delinquency. P1 (annual). Buildable with OCR.
    tax_foreclosure_auction — VERIFIED_OFFICIAL (county-contracted auctioneer) ->
        SUPPORTING_LEAD_SOURCE -> OPEN_PUBLIC -> confirms tax-lead disposition.
    parcel_master — VERIFIED_OFFICIAL (RPTS partner portal) -> ENRICHMENT_SOURCE
        -> OPEN_PUBLIC -> attaches owner / valuation context.
    gis_parcels — VERIFIED_OFFICIAL (county GIS) -> ENRICHMENT_SOURCE ->
        OPEN_PUBLIC -> attaches parcel geometry.

    No source's classification depended on a forbidden action (§01.17). The
    HTTP 403 responses were observed passively during automated fetch and are
    documented as scrape-difficulty, not as access denial.

## Recommended operator next actions

    1. Approve entry to Build Mode (FULL_BUILD) — see build_eligibility_report.md.
    2. Decide whether bankruptcy (PACER) is in scope; if so, supply PACER
       credentials (it is the only paid lead source and is optional).
    3. Confirm the three clerk open questions during Build Mode Phase 0.F
       follow-up: SearchIQS guest-mode document-view scope, verbatim doc-type
       code list, and modern (post-2004) lis pendens index coverage.
