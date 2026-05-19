# Phase 0.A — Source Discovery — Greene County, New York

County: Greene County, New York
Slug: greene_ny
Framework version: v5.3.0
Generated: 2026-05-19
Method: web search + page fetch, per knowledge_base/protocols/01_county_recon.md §01.6

This file records candidate official sources discovered for Greene County, NY.
One entry per source. Aggregator / reseller sites (NETROnline, foreclosure.com,
taxliens.com, propertychecker, countyoffice.org, etc.) were seen in search
results and are explicitly excluded — they are reseller layers over official
data, not the record authority (§01.6).

---

## clerk_land_records

    name                   Greene County Clerk — Land/Official Records (SearchIQS)
    official_url           https://www.searchiqs.com/nygre/
    page_title             Greene County, NY — SearchIQS online records
    gov_or_aggregator      government (official county-clerk vendor portal)
    records_covered        Deeds, mortgages, liens (federal, mechanic, state tax,
                           welfare), judgments and court records, lis pendens,
                           UCC filings, military discharges, divorce records
    discovered_via_query   "Greene County New York county clerk official records"
                           — confirmed via greenecountyny.gov/departments/county-clerk/
                           which states "go to www.searchiqs.com/nygre and log on
                           as a guest."

## supreme_court_foreclosure

    name                   NYS Supreme Court — Greene County — mortgage foreclosure
                           (NYSCEF e-filing + case search)
    official_url           https://iapps.courts.state.ny.us/nyscef/CaseSearch
    page_title             NYSCEF Case Search — New York State Courts
    gov_or_aggregator      government (NYS Unified Court System)
    records_covered        Mortgage foreclosure actions, lis pendens / notice of
                           pendency, civil judgments, notices of sale, surplus
                           money proceedings, RPTL Article 11 tax-foreclosure
                           petitions filed in Supreme Court
    discovered_via_query   "Greene County NY Supreme Court foreclosure case search
                           NYSCEF eCourts" — Greene County Supreme Court mandatory
                           e-filing since 2020-10-21.

## surrogate_court_probate

    name                   Greene County Surrogate's Court — probate / administration
                           (NYSCEF e-filing)
    official_url           https://iapps.courts.state.ny.us/nyscef/CaseSearch
    page_title             NYSCEF Case Search — New York State Courts
    gov_or_aggregator      government (NYS Unified Court System — Surrogate's Court)
    records_covered        Probate proceedings, administration proceedings,
                           miscellaneous estate proceedings
    discovered_via_query   "Greene County NY Surrogate's Court probate estate
                           records" — Greene County Surrogate's Court mandatory
                           e-filing since 2021-02-16.

## webcivil_supreme

    name                   WebCivil Supreme — statewide civil Supreme Court case
                           search (covers Greene County)
    official_url           https://iapps.courts.state.ny.us/webcivil/FCASMain
    page_title             Web Civil Supreme Court Case Search
    gov_or_aggregator      government (NYS Unified Court System)
    records_covered        Active and disposed civil Supreme Court cases for all
                           62 NY counties, including Greene; case status, parties,
                           appearance calendars, disposition
    discovered_via_query   "Greene County NY Supreme Court foreclosure case search
                           NYSCEF eCourts"

## tax_foreclosure

    name                   Greene County Treasurer — Annual Petition & Notice of
                           Foreclosure (in-rem tax foreclosure list)
    official_url           https://greenecountyny.gov/departments/treasurer/
    page_title             Treasurer | Greene County, New York
    gov_or_aggregator      government (Greene County Treasurer)
    records_covered        Annual RPTL Article 11 in-rem tax-foreclosure petition
                           listing delinquent parcels subject to foreclosure;
                           2025 petition PDF published 2025-02-27
    discovered_via_query   "Greene County New York treasurer delinquent taxes
                           in-rem foreclosure" — sample doc:
                           greenecountyny.gov/wp-content/uploads/2025/04/
                           2025-Petition-and-Notice-of-Forclosure.pdf

## tax_foreclosure_auction

    name                   Greene County tax-foreclosure real estate auction
                           (Absolute Auctions & Realty / NYSauctions.com)
    official_url           https://aarauctions.com/auctions/tax-foreclosures/
    page_title             Tax Foreclosures — NYSAUCTIONS.COM
    gov_or_aggregator      government-contracted vendor (county auctioneer)
    records_covered        Catalog of county-owned tax-foreclosed parcels offered
                           at the annual online auction; lots, owner-of-record,
                           photos, internet bidding packet
    discovered_via_query   "Greene County NY tax foreclosed real estate online
                           auction nysauctions.com 2025" — confirmed by county
                           news posts and town announcements citing this vendor.

## parcel_master

    name                   Greene County Real Property Tax Service — property data
                           (GAR Associates PROS portal)
    official_url           https://greenecounty.prosgar.com/
    page_title             Greene County Property Assessment Portal (GAR PROS)
    gov_or_aggregator      government-contracted vendor (RPTS "partner website")
    records_covered        Parcel assessment, property inventory, owner of record
                           (current + past), comparable sales, deed/map references,
                           tax maps
    discovered_via_query   "Greene County New York Real Property Tax Service Image
                           Mate parcel search" — RPTS page greenecountyny.gov/
                           departments/rpts/ links this as the official partner
                           portal. (Legacy SDG Image Mate at greene.sdgnys.com
                           still resolves but RPTS now directs the public to PROS.)

## gis_parcels

    name                   Greene County GIS — tax parcel layer (ArcGIS) + NYS GIS
                           Clearinghouse Greene County parcel data
    official_url           https://gis.gcgovny.com/greenewebmap/
    page_title             Greene County Web Map
    gov_or_aggregator      government (Greene County GIS Department)
    records_covered        Tax parcel boundaries, municipal boundaries, fire/school
                           districts, wetlands, flood zones; ArcGIS REST services
                           directory at gis.gcgovny.com/arcgis/rest/services;
                           statewide bulk parcel data via NYS GIS Clearinghouse
                           (data.gis.ny.gov)
    discovered_via_query   "Greene County New York Real Property Tax Service Image
                           Mate parcel search"

---

## Categories searched and NOT found as buildable county-level online sources

    sheriff_sales          NY is a judicial-foreclosure state. Foreclosure sales
                           are referee's sales noticed inside the Supreme Court
                           case (NYSCEF) and advertised in newspapers. The Greene
                           County Sheriff Civil Division performs sheriff sales
                           but publishes NO online sale list/calendar
                           (greenecountyny.gov/departments/sheriff/civil-division/
                           confirmed: only a one-line mention, no schedule).
    code_enforcement       No county-wide code-enforcement portal. Code
                           enforcement, demolition, and condemnation are run by
                           each of the 14 towns individually. Out of scope for a
                           county-wide build per domain/02_signals_and_sources.md.
    eviction               NY evictions are filed in town/village Justice Courts
                           and City Courts; no public online docket exists for
                           these courts countywide.
    bankruptcy             Federal — U.S. Bankruptcy Court, Northern District of
                           NY. Available only via PACER (paid).
    records_center         greenecountyny.gov/departments/county-clerk/
                           greene-county-records-center/ — internal inactive-
                           records storage; explicitly states it does NOT provide
                           public access. Not a source.
