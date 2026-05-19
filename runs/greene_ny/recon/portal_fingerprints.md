# Phase 0.C — Portal Fingerprints — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Method: knowledge_base/protocols/01_county_recon.md §01.8. One entry per
VERIFIED_OFFICIAL source. Machine-readable copies in recon/fingerprints/.

---

## clerk_land_records

    name                   Greene County Clerk — Land Records (SearchIQS)
    vendor                  Info Quick Solutions (IQS / SearchIQS)
    detection_heuristics    Host searchiqs.com; county code path /nygre/;
                            ASP.NET .aspx pages (Login.aspx); "log on as a guest"
                            guest-session model documented by county clerk
    architecture            Server-rendered ASP.NET web application with
                            session/viewstate; results pages are server HTML
    search_interface        Form-based POST search; name-indexed
    result_url_pattern      /nygre/ (session-bound .aspx result pages)
    detail_url_pattern      Document detail .aspx pages (session-bound)
    scrape_difficulty       HIGH — automated HTTPS fetch returned HTTP 403
                            (user-agent / bot gating); guest session + viewstate
                            handling required. Human guest access is unobstructed.

## supreme_court_foreclosure

    name                    NYS Supreme Court — Greene County — foreclosure (NYSCEF)
    vendor                  NYS Unified Court System (in-house — NYSCEF / iApps)
    detection_heuristics    Host iapps.courts.state.ny.us; path /nyscef/;
                            JSP servlet application
    architecture            Server-rendered servlet/JSP application
    search_interface        Form-based search — index number, party name, county,
                            court type, case type
    result_url_pattern      /nyscef/CaseSearch result + DocumentList views
    detail_url_pattern      /nyscef/ViewDocument — filed documents downloadable as
                            free PDFs
    scrape_difficulty       MEDIUM-HIGH — automated fetch of /webcivil endpoints
                            returned HTTP 403 (bot gating); public human access is
                            login-free. Headless browser + pacing expected.

## surrogate_court_probate

    name                    Greene County Surrogate's Court — probate (NYSCEF)
    vendor                  NYS Unified Court System (NYSCEF / iApps)
    detection_heuristics    Host iapps.courts.state.ny.us; /nyscef/; court-type
                            selector includes Surrogate's Court
    architecture            Server-rendered servlet/JSP application
    search_interface        Form-based search — same NYSCEF surface, court type =
                            Surrogate's Court, county = Greene
    result_url_pattern      /nyscef/CaseSearch
    detail_url_pattern      /nyscef/ViewDocument
    scrape_difficulty       MEDIUM-HIGH — same NYSCEF surface and bot gating as
                            supreme_court_foreclosure.

## webcivil_supreme

    name                    WebCivil Supreme — statewide civil case search
    vendor                  NYS Unified Court System (iApps / WebCivil)
    detection_heuristics    Host iapps.courts.state.ny.us; path /webcivil/FCASMain
    architecture            Server-rendered servlet/JSP application
    search_interface        Form-based — index number, party name, attorney/firm,
                            judge; county filter
    result_url_pattern      /webcivil/ case-list pages
    detail_url_pattern      /webcivil/ case-detail pages (status, parties,
                            appearances; no document images)
    scrape_difficulty       MEDIUM-HIGH — automated fetch returned HTTP 403; public
                            human access is login-free.

## tax_foreclosure

    name                    Greene County Treasurer — Petition & Notice of
                            Foreclosure
    vendor                  WordPress (greenecountyny.gov) — county-hosted
    detection_heuristics    /wp-content/uploads/ PDF path; WordPress county site
    architecture            Static PDF published on a WordPress page
    search_interface        None — single annual PDF document, no search
    result_url_pattern      /wp-content/uploads/<year>/<month>/<year>-Petition-and-
                            Notice-of-Forclosure.pdf
    detail_url_pattern      n/a (single document)
    scrape_difficulty       MEDIUM — PDF fetch succeeds, but the 2025 petition is a
                            SCANNED, CCITT-fax-encoded image PDF (~2.7 MB) with no
                            text layer. OCR is required to extract parcel rows.

## tax_foreclosure_auction

    name                    Greene County tax-foreclosure auction (AAR / nysauctions)
    vendor                  Absolute Auctions & Realty (aarauctions.com /
                            nysauctions.com)
    detection_heuristics    Host aarauctions.com; servlet path /servlet/Search.do
                            with auctionId query param; "NYSAUCTIONS.COM" branding
    architecture            Server-rendered auction-catalog web application
    search_interface        Auction catalog browse by auctionId; lot listing pages
    result_url_pattern      /servlet/Search.do?auctionId=<id>
    detail_url_pattern      Per-lot catalog pages; downloadable internet bidding
                            packet PDF
    scrape_difficulty       LOW-MEDIUM — public catalog pages; auction is seasonal
                            (annual), so the catalog only exists during the auction
                            window.

## parcel_master

    name                    Greene County RPTS property data (GAR Associates PROS)
    vendor                  GAR Associates — PROS (Property Record Online System)
    detection_heuristics    Host prosgar.com; county subdomain greenecounty.;
                            "Quick Property Search" / "Advanced Property Search" /
                            "Related Parcel Records Search" UI strings
    architecture            Web application (assessment-data portal)
    search_interface        Property search by location/owner/parcel; advanced
                            search; related-parcel search
    result_url_pattern      greenecounty.prosgar.com/ search result pages
    detail_url_pattern      Per-parcel assessment / inventory / sales pages
    scrape_difficulty       MEDIUM — public, no login; web-app session handling
                            expected. Statewide bulk parcel data via NYS GIS
                            Clearinghouse is the lower-friction enrichment path.

## gis_parcels

    name                    Greene County GIS — tax parcel layer (ArcGIS)
    vendor                  Esri ArcGIS Server (county-hosted, gcgovny.com)
    detection_heuristics    Host gis.gcgovny.com; ArcGIS REST directory at
                            /arcgis/rest/services (folders: AGOL, Hosted,
                            Utilities; services include 2025_WebMap MapServer,
                            Greene_2020, AddressPoints geocoder)
    architecture            ArcGIS Server REST + JS web-map viewer (greenewebmap)
    search_interface        ArcGIS REST query API (/query endpoints)
    result_url_pattern      /arcgis/rest/services/<folder>/<service>/MapServer/<id>/query
    detail_url_pattern      Feature attributes via REST query
    scrape_difficulty       LOW — open ArcGIS REST API; JSON query responses.
