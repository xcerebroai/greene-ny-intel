# API Discovery Report — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Method: knowledge_base/protocols/01_county_recon.md §01.23 (v5.3.0 Gap 2).
For every candidate source, documented APIs were searched before settling on
HTML scraping. Search locations per §01.23: <domain>/api, /api/swagger,
/swagger, /docs, /api-docs, Postman public collections, GitHub, vendor docs.

---

## Summary

    Documented API found: YES — for the GIS / parcel enrichment layer.
    No documented public API exists for the primary lead sources (county clerk
    land records, NYSCEF court records, the tax-foreclosure petition, or the
    auction catalog). Those are vendor / court servlet portals consumed via
    their form interfaces; Build Mode uses HTML / headless-browser adapters.

---

## gis_parcels — ArcGIS REST API — FOUND

    api_url                 https://gis.gcgovny.com/arcgis/rest/services
    api_type                ArcGIS
    documentation_url       https://gis.gcgovny.com/arcgis/rest/services (Esri
                            REST self-describing services directory)
    auth_required           false
    rate_limited            true (standard ArcGIS Server throttling expected)
    source_role             ENRICHMENT_SOURCE
    notes                   Public Esri ArcGIS Server. Folders: AGOL, Hosted,
                            Utilities. Services include 2025_WebMap (MapServer),
                            Greene_2020 (MapServer), AddressPoints_StreetSegment_
                            Composite (GeocodeServer). The tax-parcel layer is
                            served from this server (GIS maintains the RPTS parcel
                            geodatabase). Query via /MapServer/<id>/query.

## NYS GIS Clearinghouse parcel data — ArcGIS Hub API — FOUND

    api_url                 https://data.gis.ny.gov (ArcGIS Hub — Greene County
                            Parcel Data dataset
                            343d7dcba75c4f78b811e861939aa6e1_0)
    api_type                ArcGIS
    documentation_url       https://data.gis.ny.gov/datasets/greene-county-parcel-data
    auth_required           false
    rate_limited            true
    source_role             ENRICHMENT_SOURCE
    notes                   Statewide NYS ITS GIS Program Office parcel program.
                            Greene County parcel polygons + assessment attributes
                            available as a bulk download and via an ArcGIS Feature
                            Service. This is the lowest-friction enrichment path
                            (FULL_COUNTY_BULK).

---

## Search log — per source

    clerk_land_records (searchiqs.com)
        Searched: /api, /swagger, /docs, /api-docs on searchiqs.com; "SearchIQS
        api" / "Info Quick Solutions api" web + GitHub. Found: NO documented
        public API. SearchIQS is an ASP.NET form portal; access is via the
        guest-session search form. Build Mode uses a headless-browser adapter.

    supreme_court_foreclosure / surrogate_court_probate / webcivil_supreme
        (iapps.courts.state.ny.us)
        Searched: /api, /swagger, /docs on iapps.courts.state.ny.us; "NYSCEF api"
        / "NY courts iApps api" web + GitHub; NY OCA developer docs. Found: NO
        documented public API. NYSCEF/WebCivil are public servlet applications
        with form search and free document download, but no published REST/JSON
        API. Build Mode uses headless-browser adapters against the form surface.

    tax_foreclosure (greenecountyny.gov)
        Searched: greenecountyny.gov for /api, JSON endpoints; WordPress REST
        (/wp-json) exists but only serves CMS content, not the foreclosure list.
        Found: NO data API. The petition is a single annual scanned PDF; Build
        Mode ingests it via PDF download + OCR.

    tax_foreclosure_auction (aarauctions.com / nysauctions.com)
        Searched: /api, /docs on aarauctions.com; "AAR auctions api" /
        "nysauctions api" web + GitHub. Found: NO documented public API. Catalog
        is browsed via /servlet/Search.do?auctionId=<id>. Build Mode uses an
        HTML adapter during the seasonal auction window.

    parcel_master (greenecounty.prosgar.com)
        Searched: /api, /swagger, /docs on prosgar.com; "GAR Associates PROS api"
        / "prosgar api" web + GitHub. Found: NO documented public API for the
        PROS portal itself. However, the same parcel/assessment data is available
        through the NYS GIS Clearinghouse ArcGIS API (above) — recon recommends
        the Clearinghouse API as the parcel-master ingest path.
