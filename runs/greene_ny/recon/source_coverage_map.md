# Source Coverage Map — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.1
Generated: 2026-05-19 · **Corrected: 2026-05-21 (primary-event-source re-recon)**
Companion to source_of_record_matrix.json (§16.D).

---

## Live sources (accessible / buildable now — stdlib-reachable)

    tax_foreclosure_auction   PRIMARY  P1  OPEN_PUBLIC   server-rendered (AAR)
    tax_foreclosure           PRIMARY  P1  OPEN_PUBLIC   PDF publication (OCR)
    parcel_master             ENRICH   P2  OPEN_PUBLIC   ArcGIS API (built P2)
    gis_parcels               ENRICH   P2  OPEN_PUBLIC   ArcGIS API
    prosgar_assessment        ENRICH   P2  OPEN_PUBLIC   ASP.NET assessment form

## Blocked / session-required sources (Cloudflare interactive challenge)

    clerk_land_records        PRIMARY  P0  CAPTCHA_PROTECTED  SearchIQS
    supreme_court_foreclosure PRIMARY  P0  CAPTCHA_PROTECTED  NYSCEF
    surrogate_court_probate   PRIMARY  P0  CAPTCHA_PROTECTED  NYSCEF
    webcivil_supreme          SUPPORT  P0  CAPTCHA_PROTECTED  WebCivil

    These are NOT dead ends. Each is a free public portal reachable in a
    browser; buildable via an operator-seeded session (cf_clearance + session
    cookies) or a stealth browser — approved §02.9 / §4.14 access strategies.

## Limited-coverage sources

    tax_foreclosure        Annual petition only; scanned PDF (OCR required);
                           the AAR auction is the cleaner primary tax path.
    legal_notices_column   Next.js SPA; backend API host (api.column.us)
                           responds but the search endpoint is undiscovered —
                           stdlib-reachability UNCONFIRMED, needs API discovery
                           or browser tooling.

## Lead types with NO source found

    Tax Sale Certificate   Greene enforces via RPTL Art. 11 in-rem foreclosure.
    Demolition             Per-town building/code offices; no county portal.
    Condemnation           Per-town building/code offices; no county portal.
    Eviction               Town/village justice courts; no online docket.

## Operator review / decision required

    Divorce                NY matrimonial records confidential (DRL §235).
    Bankruptcy             PACER (NDNY) — paid; operator credentials required.
    legal_notices_column   Operator decision: invest in Column API discovery
                           or browser tooling, or rely on court/clerk sources.

## Per-record-only coverage constraints (§16.G)

    None. The tax-foreclosure auction and treasurer petition are full-county
    bulk; the enrichment parcel layer is FULL_COUNTY_BULK.

## Not applicable in New York

    Trustee Sale, Notice of Trustee Sale, Notice of Substitute Trustee Sale —
    New York is a judicial-foreclosure state.
