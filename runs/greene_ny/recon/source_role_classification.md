# Phase 0.E — Source Role Classification — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Method: knowledge_base/protocols/01_county_recon.md §01.10, applying the
§13 Lead Origination Contract role definitions.

---

## clerk_land_records

    source_role             PRIMARY_LEAD_SOURCE
    rationale               County Clerk recorded instruments are officially-
                            recorded distress / encumbrance / transfer / legal-
                            status events: lis pendens, mechanic's liens, federal
                            and state tax liens, judgment dockets, and
                            executor's / administrator's / sheriff's deeds. Each
                            is a discrete dated recorded event.
    section_13_reference    §13.2 — clerk/recorder records, liens, lis pendens,
                            recorded judgments, estate deeds.

## supreme_court_foreclosure

    source_role             PRIMARY_LEAD_SOURCE
    rationale               Supreme Court mortgage-foreclosure actions and RPTL
                            Article 11 in-rem tax-foreclosure petitions are
                            court-filed distress events. NYSCEF exposes the
                            docket, lis pendens, notice of sale, judgment of
                            foreclosure and surplus-money proceedings.
    section_13_reference    §13.2 — court events, foreclosure filings, lis
                            pendens, surplus.

## surrogate_court_probate

    source_role             PRIMARY_LEAD_SOURCE
    rationale               Surrogate's Court probate and administration
                            proceedings are court-filed legal-status events that
                            originate estate leads (decedent owner, fiduciary
                            appointed, heirs).
    section_13_reference    §13.2 — probate and estate records.

## webcivil_supreme

    source_role             SUPPORTING_LEAD_SOURCE
    rationale               Confirms case status, parties, disposition and
                            appearance dates for Supreme Court cases. It adds
                            event detail to leads originated from
                            supreme_court_foreclosure / clerk records; it exposes
                            no document images and originates no lead on its own.
    section_13_reference    §13 — supporting event source.

## tax_foreclosure

    source_role             PRIMARY_LEAD_SOURCE
    rationale               The Treasurer's Annual Petition & Notice of
                            Foreclosure is the official list of parcels in RPTL
                            Article 11 in-rem tax foreclosure — a dated tax-
                            distress event per parcel.
    section_13_reference    §13.2 — tax delinquency, tax-lien foreclosure.

## tax_foreclosure_auction

    source_role             SUPPORTING_LEAD_SOURCE
    rationale               The AAR / NYSauctions catalog is the post-foreclosure
                            disposition of county-owned tax-foreclosed parcels.
                            It confirms and adds sale detail to tax_foreclosure
                            leads (former owner of record, surplus context) but
                            the lead originates from the tax-foreclosure petition.
    section_13_reference    §13 — supporting event source; §13.2 tax sale.

## parcel_master

    source_role             ENRICHMENT_SOURCE
    rationale               Assessment, owner of record, inventory, valuation and
                            comparable sales describe the STATE of a property —
                            what it is, not a distress event. Attaches to leads;
                            never originates one.
    section_13_reference    §13.3 — parcel / assessor / valuation data.

## gis_parcels

    source_role             ENRICHMENT_SOURCE
    rationale               Tax-parcel geometry, municipal boundaries, flood/
                            wetland layers — spatial enrichment only.
    section_13_reference    §13.3 — GIS / parcel data.

---

## Rejected sources

    sheriff_sales_portal    REJECTED_SOURCE — no Greene County Sheriff online
                            sheriff-sale list exists; foreclosure-sale events are
                            captured via supreme_court_foreclosure.
    greene.sdgnys.com       REJECTED_SOURCE — legacy SDG Image Mate parcel portal
                            superseded by parcel_master (GAR PROS). Redundant.
    third-party aggregators REJECTED_SOURCE — foreclosure.com, taxliens.com,
                            sheriffsales.net, NETROnline, etc. are resellers, not
                            the official record authority (§01.6 / §01.10).
