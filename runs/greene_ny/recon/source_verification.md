# Phase 0.B — Official Source Verification — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Method: knowledge_base/protocols/01_county_recon.md §01.7 — four verification
layers. Rule: pass Layer 1 OR (Layer 2 AND Layer 3), AND pass Layer 4 →
VERIFIED_OFFICIAL.

---

## clerk_land_records

    name                   Greene County Clerk — Land/Official Records (SearchIQS)
    official_url           https://www.searchiqs.com/nygre/
    layers_passed          Layer 2 (vendor portal — IQS/SearchIQS), Layer 3
                           (linked from greenecountyny.gov/departments/county-clerk/),
                           Layer 4 (Greene County Clerk is the NY recording
                           authority for land records)
    verification_status    VERIFIED_OFFICIAL
    notes                  The County Clerk's own page directs the public to
                           "www.searchiqs.com/nygre and log on as a guest." Vendor
                           is Info Quick Solutions (IQS). The official-site inbound
                           link is the proof of official status (§01.7 Layer 2/3).

## supreme_court_foreclosure

    name                   NYS Supreme Court — Greene County — foreclosure (NYSCEF)
    official_url           https://iapps.courts.state.ny.us/nyscef/CaseSearch
    layers_passed          Layer 1 (courts.state.ny.us — NYS government domain),
                           Layer 4 (Supreme Court is the NY court of jurisdiction
                           for mortgage foreclosure and RPTL Art. 11 tax foreclosure)
    verification_status    VERIFIED_OFFICIAL
    notes                  NYSCEF is the official NYS Unified Court System e-filing
                           and public case-search system. Greene County Supreme
                           Court has mandatory e-filing effective 2020-10-21.

## surrogate_court_probate

    name                   Greene County Surrogate's Court — probate (NYSCEF)
    official_url           https://iapps.courts.state.ny.us/nyscef/CaseSearch
    layers_passed          Layer 1 (courts.state.ny.us), Layer 4 (Surrogate's
                           Court is the NY court of jurisdiction for probate /
                           estate administration)
    verification_status    VERIFIED_OFFICIAL
    notes                  Greene County Surrogate's Court mandatory e-filing
                           effective 2021-02-16. Estate proceedings filed since
                           then are in NYSCEF.

## webcivil_supreme

    name                   WebCivil Supreme — statewide civil case search
    official_url           https://iapps.courts.state.ny.us/webcivil/FCASMain
    layers_passed          Layer 1 (courts.state.ny.us), Layer 4 (NYS Unified
                           Court System)
    verification_status    VERIFIED_OFFICIAL
    notes                  Covers active + disposed civil Supreme Court cases for
                           all 62 counties including Greene. Supporting role —
                           confirms case status / parties; does not expose
                           document images.

## tax_foreclosure

    name                   Greene County Treasurer — Annual Petition & Notice of
                           Foreclosure
    official_url           https://greenecountyny.gov/departments/treasurer/
    layers_passed          Layer 1 (greenecountyny.gov — county government domain),
                           Layer 4 (County Treasurer is the RPTL Article 11
                           enforcing officer for delinquent taxes)
    verification_status    VERIFIED_OFFICIAL
    notes                  Treasurer page publishes the "Annual Petition & Notice
                           of Foreclosure (2025)". The petition itself is filed in
                           NY Supreme Court as an in-rem proceeding.

## tax_foreclosure_auction

    name                   Greene County tax-foreclosure auction (Absolute
                           Auctions & Realty / NYSauctions.com)
    official_url           https://aarauctions.com/auctions/tax-foreclosures/
    layers_passed          Layer 2 (auction vendor), Layer 3 (county news posts on
                           greenecountyny.gov and town sites announce and link this
                           vendor's Greene County auctions), Layer 4 (the auction
                           disposes county-owned RPTL Art. 11 tax-foreclosed parcels)
    verification_status    VERIFIED_OFFICIAL
    notes                  County-contracted auctioneer. Auction catalog is the
                           post-foreclosure disposition list; supporting role.

## parcel_master

    name                   Greene County RPTS property data (GAR Associates PROS)
    official_url           https://greenecounty.prosgar.com/
    layers_passed          Layer 2 (assessment-data vendor — GAR Associates),
                           Layer 3 (linked from greenecountyny.gov/departments/rpts/
                           as the official "partner website"), Layer 4 (Real
                           Property Tax Service is the county assessment authority)
    verification_status    VERIFIED_OFFICIAL
    notes                  Enrichment source. RPTS page text: "Property
                           assessments, inventory, maps and assessment roll
                           information can be found on our partner website."

## gis_parcels

    name                   Greene County GIS — tax parcel layer (ArcGIS)
    official_url           https://gis.gcgovny.com/greenewebmap/
    layers_passed          Layer 1 (gcgovny.com — Greene County government GIS
                           subdomain), Layer 3 (linked from RPTS page), Layer 4
                           (Greene County GIS Department maintains the tax-parcel
                           geodatabase for RPTS)
    verification_status    VERIFIED_OFFICIAL
    notes                  Enrichment source. Public ArcGIS REST services
                           directory confirmed at gis.gcgovny.com/arcgis/rest/
                           services. Statewide bulk parcel data also published via
                           the NYS GIS Clearinghouse.

---

## Excluded / not verified

    sheriff_sales          NOT_RECORDS_AUTHORITY for an online sale list — no
                           Greene County Sheriff online sheriff-sale calendar
                           exists. Foreclosure-sale events are captured inside the
                           Supreme Court case file (supreme_court_foreclosure).
    aggregator sites       REJECTED — foreclosure.com, taxliens.com, sheriffsales.net,
                           NETROnline, propertychecker, countyoffice.org are
                           third-party resellers, excluded per §01.6.
    greene.sdgnys.com      Legacy SDG Image Mate parcel portal. Still resolves but
                           superseded — RPTS now directs the public to the GAR PROS
                           portal. Recorded as historical, not a selected source.
