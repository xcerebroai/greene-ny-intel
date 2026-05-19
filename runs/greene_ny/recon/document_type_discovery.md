# Phase 0.F — Document Type Discovery — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Method: knowledge_base/protocols/01_county_recon.md §01.12 — metadata-only
document-type discovery for accessible PRIMARY_LEAD_SOURCE / SUPPORTING_LEAD_
SOURCE entries. Canonical types cross-referenced to
knowledge_base/domain/canonical_doc_types.json.

This phase is metadata-only. No records were scraped (§01.17). Document-type
vocabularies below are the categories the portals expose, captured from portal
descriptions, the county clerk's published record list, and NY statutory
practice. Per-source verbatim doc-type code lists must be confirmed during
Build Mode Phase 0.F follow-up and recorded in each source's
doc_type_synonyms map.

---

## clerk_land_records

    source_name                              clerk_land_records
    document_type_taxonomy_field_name        Document Type (name-indexed land/
                                             official records index)
    total_types_observed                     Record families published by the
                                             Greene County Clerk: deeds;
                                             mortgages; liens (federal tax,
                                             mechanic's, state tax, welfare);
                                             judgments / court records; lis
                                             pendens; UCC; military discharges;
                                             divorce records.
    types_mapped_to_canonical_primary        LIS_PENDENS; MECHANICS_LIEN;
                                             CONSTRUCTION_LIEN (NY: filed as a
                                             mechanic's lien); FEDERAL_TAX_LIEN;
                                             STATE_TAX_LIEN; JUDGMENT_LIEN
                                             (docketed transcripts of judgment);
                                             EXECUTORS_DEED; ADMINISTRATORS_DEED;
                                             SHERIFF_DEED; QUITCLAIM_DEED;
                                             RELEASE_OF_LIEN / SATISFACTION_OF_
                                             MORTGAGE / RELEASE_OF_LIS_PENDENS
                                             (negative signals).
    types_mapped_to_canonical_enrichment     WARRANTY_DEED; BARGAIN_AND_SALE_DEED
                                             (the common NY arm's-length deed);
                                             MORTGAGE; ASSIGNMENT_OF_MORTGAGE;
                                             UCC_FINANCING_STATEMENT.
    types_unknown                            County-specific recorder doc-type
                                             codes/abbreviations are not yet
                                             confirmed — SearchIQS exposes a
                                             document-type filter whose exact code
                                             list must be captured in Build Mode.
    recommended_primary_doc_types_for_build  LIS_PENDENS, MECHANICS_LIEN,
                                             FEDERAL_TAX_LIEN, STATE_TAX_LIEN,
                                             JUDGMENT_LIEN, EXECUTORS_DEED,
                                             ADMINISTRATORS_DEED, SHERIFF_DEED.

## supreme_court_foreclosure

    source_name                              supreme_court_foreclosure
    document_type_taxonomy_field_name        Case Type / Filed Document type
                                             (NYSCEF docket)
    total_types_observed                     Case types: Real Property —
                                             Mortgage Foreclosure; Tax
                                             Certiorari; RPTL Art. 11 in-rem tax
                                             foreclosure. Filed-document types
                                             within a foreclosure case: Summons &
                                             Complaint, Notice of Pendency (lis
                                             pendens), Judgment of Foreclosure &
                                             Sale, Notice of Sale, Referee's
                                             Report of Sale, Surplus Money
                                             proceedings.
    types_mapped_to_canonical_primary        LIS_PENDENS; FINAL_JUDGMENT_OF_
                                             FORECLOSURE; NOTICE_OF_SALE;
                                             SHERIFF_SALE (referee's sale event);
                                             SHERIFF_SALE_SURPLUS; TAX_FORECLOSURE_
                                             NOTICE (RPTL Art. 11 petition).
    types_mapped_to_canonical_enrichment     n/a (court event source).
    types_unknown                            Exact NYSCEF case-type and document-
                                             type code strings to be captured in
                                             Build Mode.
    recommended_primary_doc_types_for_build  LIS_PENDENS, FINAL_JUDGMENT_OF_
                                             FORECLOSURE, NOTICE_OF_SALE,
                                             SHERIFF_SALE, SHERIFF_SALE_SURPLUS.

## surrogate_court_probate

    source_name                              surrogate_court_probate
    document_type_taxonomy_field_name        Proceeding Type (NYSCEF Surrogate's
                                             Court)
    total_types_observed                     Probate proceeding; Administration
                                             proceeding; miscellaneous estate
                                             proceedings. Filed documents:
                                             Petition for Probate / Letters,
                                             Letters Testamentary, Letters of
                                             Administration, decrees.
    types_mapped_to_canonical_primary        LETTERS_TESTAMENTARY; LETTERS_OF_
                                             ADMINISTRATION; DETERMINATION_OF_
                                             HEIRSHIP (estate lead-generating).
    types_mapped_to_canonical_enrichment     n/a (court event source).
    types_unknown                            Exact NYSCEF Surrogate proceeding-
                                             type strings to be captured in Build
                                             Mode.
    recommended_primary_doc_types_for_build  LETTERS_TESTAMENTARY, LETTERS_OF_
                                             ADMINISTRATION.

## webcivil_supreme

    source_name                              webcivil_supreme
    document_type_taxonomy_field_name        Case Type (WebCivil Supreme)
    total_types_observed                     Civil Supreme Court case types
                                             including foreclosure; case status
                                             (Active / Disposed) and disposition.
    types_mapped_to_canonical_primary        Supporting only — confirms case
                                             status for FINAL_JUDGMENT_OF_
                                             FORECLOSURE / LIS_PENDENS leads.
    types_mapped_to_canonical_enrichment     n/a.
    types_unknown                            n/a.
    recommended_primary_doc_types_for_build  None — supporting source; used to
                                             confirm lifecycle status.

## tax_foreclosure

    source_name                              tax_foreclosure
    document_type_taxonomy_field_name        Single document — Annual Petition &
                                             Notice of Foreclosure (no taxonomy)
    total_types_observed                     One canonical type — the in-rem tax-
                                             foreclosure petition listing
                                             delinquent parcels.
    types_mapped_to_canonical_primary        TAX_FORECLOSURE_NOTICE.
    types_mapped_to_canonical_enrichment     n/a.
    types_unknown                            Per-parcel field layout inside the
                                             petition — the 2025 PDF is a scanned
                                             image; OCR is required to read parcel
                                             ID (SBL), owner, address, amount and
                                             redemption date.
    recommended_primary_doc_types_for_build  TAX_FORECLOSURE_NOTICE.

## tax_foreclosure_auction

    source_name                              tax_foreclosure_auction
    document_type_taxonomy_field_name        Auction lot catalog (AAR / NYSauctions)
    total_types_observed                     Lot listings — tax-foreclosed
                                             parcels offered at the annual auction.
    types_mapped_to_canonical_primary        TAX_DEED (post-tax-foreclosure
                                             disposition) — supporting confirmation.
    types_mapped_to_canonical_enrichment     n/a.
    types_unknown                            Lot-record field layout per auction.
    recommended_primary_doc_types_for_build  None — supporting source; confirms
                                             disposition of tax_foreclosure leads.
