# Source Coverage Map — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Companion to source_of_record_matrix.json (§16.D).

---

## Live sources (accessible, buildable without operator escalation)

    clerk_land_records          PRIMARY  P0  SEARCH_ONLY_PUBLIC  daily
    supreme_court_foreclosure   PRIMARY  P0  OPEN_PUBLIC         daily
    surrogate_court_probate     PRIMARY  P0  OPEN_PUBLIC         daily
    webcivil_supreme            SUPPORT  P0  OPEN_PUBLIC         daily
    tax_foreclosure             PRIMARY  P1  OPEN_PUBLIC         annual
    tax_foreclosure_auction     SUPPORT  P1  OPEN_PUBLIC         annual
    parcel_master               ENRICH   P2  OPEN_PUBLIC         quarterly
    gis_parcels                 ENRICH   P2  OPEN_PUBLIC         quarterly

## Blocked sources

    (none) — no source is at access status BLOCKED / CAPTCHA_PROTECTED /
    LOGIN_REQUIRED / PAID for the lead types selected to build.

## Limited-coverage sources

    tax_foreclosure             Annual publication cadence only; the 2025
                                Petition & Notice of Foreclosure PDF is a scanned
                                image (OCR required). Coverage is the annual
                                in-rem foreclosure list, not a rolling delinquency
                                feed — classified P1.
    tax_foreclosure_auction     Seasonal — catalog exists only during the annual
                                auction window.

## Per-record-only coverage constraints (§16.G)

    (none) — clerk and court sources support batch/date-range query; the
    enrichment parcel layer is available as FULL_COUNTY_BULK via the NYS GIS
    Clearinghouse. No source is PER_RECORD_ONLY.

## Lead types with NO source found

    Tax Sale Certificate        Greene County uses RPTL Article 11 in-rem
                                foreclosure, not tax-lien-certificate sales.
    Demolition                  Town building/code departments only; no
                                county-wide online source.
    Condemnation                Town building/code departments only; no
                                county-wide online source.
    Eviction                    Town/village Justice Courts and City Courts —
                                no public online docket countywide.

## Lead types requiring operator review

    Divorce                     NY matrimonial records are confidential by
                                statute (DRL §235); not a publicly extractable
                                lead source.
    Bankruptcy                  Federal — PACER (Northern District of NY) charges
                                access fees; operator must supply credentials to
                                build.

## Not applicable in New York

    Trustee Sale, Notice of Trustee Sale, Notice of Substitute Trustee Sale —
    New York is a judicial-foreclosure state; no non-judicial trustee sales.
