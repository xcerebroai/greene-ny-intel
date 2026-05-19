# Phase 0.D — Access Classification — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Method: knowledge_base/protocols/01_county_recon.md §01.9. Canonical enum
values only. No forbidden action was taken (§01.17) — no accounts created, no
payments, no CAPTCHA solved, no records scraped.

---

## clerk_land_records

    access_classification   SEARCH_ONLY_PUBLIC
    evidence                 Greene County Clerk page states records are "available
                             online for your 24/7 convenience ... log on as a
                             guest" and that public viewing/searching is free as a
                             guest; a $5/document fee applies only to PRINTED
                             copies for non-commercial users. Search metadata is
                             therefore free; document images are fee-gated.
    notes                    Document images are not required to originate leads
                             from index metadata, so SEARCH_ONLY_PUBLIC is
                             buildable without escalation. Automated HTTPS fetch
                             returned HTTP 403 — a scrape-difficulty/technical
                             concern recorded in the fingerprint, NOT an access-
                             tier blocker; a human guest is unobstructed.

## supreme_court_foreclosure

    access_classification   OPEN_PUBLIC
    evidence                 NYSCEF is "a publicly accessible website where filings
                             can be downloaded for free, and you do not need a
                             login." Case search by index number or party name;
                             e-filed Greene County Supreme Court cases (mandatory
                             since 2020-10-21) expose full dockets and PDF
                             documents at no charge.
    notes                    Automated fetch of iApps endpoints returned HTTP 403
                             (bot gating) — technical scrape concern, not an
                             access blocker.

## surrogate_court_probate

    access_classification   OPEN_PUBLIC
    evidence                 Same NYSCEF public-access surface as Supreme Court.
                             Greene County Surrogate's Court mandatory e-filing
                             since 2021-02-16; e-filed estate proceedings are
                             publicly searchable with free document downloads.
    notes                    Some estate-proceeding documents may be restricted
                             per Surrogate's Court rules; the case index and core
                             filings are public.

## webcivil_supreme

    access_classification   OPEN_PUBLIC
    evidence                 "You can search for cases as a public user and do NOT
                             have to login." Covers active + disposed civil
                             Supreme Court cases statewide including Greene.
    notes                    Displays case status/parties/appearances only — no
                             document images. Automated fetch returned HTTP 403
                             (bot gating); human access is login-free.

## tax_foreclosure

    access_classification   OPEN_PUBLIC
    evidence                 The Annual Petition & Notice of Foreclosure is a PDF
                             published openly on the Treasurer's page
                             (greenecountyny.gov/wp-content/uploads/2025/04/
                             2025-Petition-and-Notice-of-Forclosure.pdf). Fetch
                             succeeded with no login or payment.
    notes                    The PDF is a SCANNED image (CCITT fax, ~2.7 MB, no
                             text layer) — OCR required to extract parcel rows.
                             Recorded as an extraction constraint, not an access
                             blocker.

## tax_foreclosure_auction

    access_classification   OPEN_PUBLIC
    evidence                 AAR / NYSauctions.com auction catalogs are publicly
                             browsable (servlet/Search.do?auctionId=...). Bidder
                             registration is required only to BID, not to view the
                             catalog and lot details.
    notes                    Seasonal — the Greene County catalog is published
                             only during the annual auction window.

## parcel_master

    access_classification   OPEN_PUBLIC
    evidence                 GAR PROS portal (greenecounty.prosgar.com) — public
                             property search with no login requirement observed;
                             exposes assessment, inventory, owner of record,
                             comparable sales, deed/map references.
    notes                    Enrichment source. NYS GIS Clearinghouse provides the
                             same parcel/assessment attributes as bulk download.

## gis_parcels

    access_classification   OPEN_PUBLIC
    evidence                 Public ArcGIS REST services directory at
                             gis.gcgovny.com/arcgis/rest/services responded with a
                             services listing; ArcGIS query endpoints are open.
                             NYS GIS Clearinghouse Greene County parcel data is a
                             public download.
    notes                    Enrichment source.
