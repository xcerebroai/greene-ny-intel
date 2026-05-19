#!/usr/bin/env python3
"""Phase 0 Step 4 builder for greene_ny.

Builds the populated county config dict in memory and writes it via
scaffold/ops/write_county_config.py (MASTER_PROMPT.md Section 4.28).
Also emits the standalone Source-of-Record Matrix JSON and per-source
portal fingerprint JSON artifacts under runs/greene_ny/recon/.
"""
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scaffold", "ops"))
from write_county_config import write_county_config  # noqa: E402

NOW = "2026-05-19T00:00:00Z"
FW = "v5.3.0"

# ---------------------------------------------------------------- sources ---

def src(**kw):
    """Build a source proof-packet block from the template defaults."""
    base = {
        "category": "lead", "subtype": "", "url": "", "access_pattern": "static_html",
        "official_status": "", "lead_value": "", "operator_override": False,
        "source_reliability_grade": "", "source_priority": "", "build_priority": "",
        "enabled": True, "paused_reason": "", "pause_until": "", "allowed_to_export": True,
        "source_freshness": "", "known_limitations": [], "last_verified_at": NOW,
        "auth_required": False, "rate_limit_rpm": None, "scraper_module": "",
        "fields": {}, "doc_type_synonyms": {}, "refresh_cadence": "daily", "ttl_days": 365,
        "blocked_unblock_paths": [], "notes": "", "verification_note": "",
        "open_questions": [], "verified_from_url": "", "verification_method": "",
        "official_entity": "", "portal_type": "", "records_available": [],
        "search_fields": [], "access_method": "", "public_access_status": "",
        "document_access_status": "", "source_role": "", "verification_confidence": "",
        "sample_record_path_confirmed": False, "sample_record_type": "",
        "sample_search_possible": False, "sample_document_view_possible": False,
        "blocker": "", "next_access_strategy": "", "blocker_type": "",
        "auto_resolve_status": "NOT_ATTEMPTED", "final_resolution_status": "",
        "auto_resolve_attempts": [], "lifecycle_status": "", "suppression_reason": "",
        "expected_refresh_cadence": "", "source_freshness_status": "UNKNOWN",
        "stale_after_hours": None, "last_successful_fetch_at": "",
        "last_attempted_fetch_at": "", "last_record_seen_at": "", "record_ttl_days": None,
        "expire_if_not_seen_runs": None, "stale_record_policy": "",
        "quarantine_status": "NOT_QUARANTINED", "quarantine_reason": "",
        "estimated_runtime_minutes": None, "estimated_cost_category": "FREE",
        "portal_fingerprint_id": "", "portal_family": "", "fingerprinted_at": NOW,
        "fingerprint_confidence": "", "fingerprint_summary": "",
        "recommended_adapter": "", "credentials_required_kind": "",
        "credentials_declared": False, "manual_upload_path": "",
        "manual_upload_received_at": "",
    }
    base.update(kw)
    return base


sources = {}

sources["clerk_land_records"] = src(
    category="lead", subtype="clerk_recordings",
    url="https://www.searchiqs.com/nygre/", access_pattern="spa_with_api",
    official_status="OFFICIAL_VENDOR_PORTAL", lead_value="LEAD_GENERATING",
    source_reliability_grade="A", source_priority="P0", build_priority="mvp_required",
    scraper_module="scrapers/clerk_land_records.py", refresh_cadence="daily",
    ttl_days=1095, source_freshness="DAILY", expected_refresh_cadence="DAILY",
    rate_limit_rpm=30,
    blocked_unblock_paths=["seeded_session", "captcha_solver"],
    portal_fingerprint_id="clerk_land_records", portal_family="IQS_SearchIQS",
    fingerprint_confidence="HIGH",
    fingerprint_summary="Info Quick Solutions (SearchIQS) ASP.NET land-records "
        "portal at searchiqs.com/nygre; guest-session search; automated fetch "
        "returned HTTP 403 (bot gating) — headless browser adapter required.",
    recommended_adapter="searchiqs_recordings (headless browser + guest session)",
    official_entity="Greene County Clerk",
    portal_type="county clerk land/official records search",
    records_available=["deeds", "mortgages", "federal_tax_liens", "mechanics_liens",
        "state_tax_liens", "welfare_liens", "judgments", "lis_pendens", "ucc",
        "military_discharges", "divorce_records"],
    search_fields=["party_name", "date_range", "document_type"],
    access_method="SEARCHABLE_PUBLIC_PORTAL",
    public_access_status="PUBLIC_SEARCH_DOCUMENTS_LOCKED",
    document_access_status="DOCUMENTS_PAID_SUBSCRIPTION_REQUIRED",
    source_role="PRIMARY_LEAD_SOURCE", verification_confidence="HIGH",
    sample_record_path_confirmed=True, sample_record_type="search_form",
    sample_search_possible=True, sample_document_view_possible=False,
    verified_from_url="https://greenecountyny.gov/departments/county-clerk/",
    verification_method="official_vendor_link",
    verification_note="Greene County Clerk page directs the public to "
        "searchiqs.com/nygre and to log on as a guest; guest search/view is free, "
        "$5/document print fee for non-commercial users. Official-site inbound "
        "link confirms official status. Automated HTTPS fetch returned HTTP 403 "
        "(user-agent gating) — a scrape-difficulty concern, not an access-tier "
        "blocker; a human guest is unobstructed.",
    known_limitations=["Automated fetch HTTP 403 — headless browser + guest "
        "session required for scraping", "Document images print-fee gated "
        "($5/doc non-commercial); index search is free",
        "County Clerk's published note references a Lis Pendens index covering "
        "1924-2004 separately — modern lis pendens coverage to be confirmed"],
    open_questions=["Confirm whether SearchIQS guest mode allows free document-"
        "image VIEWING or only index search (recon classified conservatively as "
        "SEARCH_ONLY).", "Capture the verbatim SearchIQS document-type code list "
        "and populate doc_type_synonyms during Build Mode.",
        "Confirm modern (post-2004) lis pendens / notice-of-pendency coverage in "
        "the main SearchIQS index."],
    stale_after_hours=48, stale_record_policy="KEEP_UNTIL_RELEASED",
    estimated_runtime_minutes=20,
    notes="PRIMARY P0 lead source — recorded liens, lis pendens, judgment "
        "dockets, estate deeds.",
)

_court_layers_note = ("NYSCEF is the NYS Unified Court System public e-filing "
    "system; no login required, filings download free as PDF.")

sources["supreme_court_foreclosure"] = src(
    category="lead", subtype="court_civil",
    url="https://iapps.courts.state.ny.us/nyscef/CaseSearch",
    access_pattern="static_html", official_status="OFFICIAL_COURT",
    lead_value="LEAD_GENERATING", source_reliability_grade="A",
    source_priority="P0", build_priority="mvp_required",
    scraper_module="scrapers/supreme_court_foreclosure.py", refresh_cadence="daily",
    ttl_days=1095, source_freshness="DAILY", expected_refresh_cadence="DAILY",
    rate_limit_rpm=20, blocked_unblock_paths=["seeded_session"],
    portal_fingerprint_id="supreme_court_foreclosure", portal_family="NYSCEF_iApps",
    fingerprint_confidence="HIGH",
    fingerprint_summary="NYS Unified Court System NYSCEF / iApps servlet portal; "
        "public case search + free PDF document download; automated fetch of "
        "iApps endpoints returned HTTP 403 (bot gating) — headless browser "
        "adapter expected.",
    recommended_adapter="nyscef_case_search (headless browser, county=Greene, "
        "court=Supreme, case type=mortgage foreclosure / RPTL Art.11)",
    official_entity="New York State Supreme Court, Greene County (NYS Unified "
        "Court System)",
    portal_type="court e-filing docket and case search",
    records_available=["mortgage_foreclosure_cases", "notice_of_pendency",
        "judgment_of_foreclosure_and_sale", "notice_of_sale",
        "referee_report_of_sale", "surplus_money_proceedings",
        "rptl_article_11_tax_foreclosure_petitions"],
    search_fields=["index_number", "party_name", "county", "court_type",
        "case_type", "filing_date_range"],
    access_method="SEARCHABLE_PUBLIC_PORTAL",
    public_access_status="FULL_PUBLIC_ACCESS",
    document_access_status="DOCUMENTS_PUBLIC",
    source_role="PRIMARY_LEAD_SOURCE", verification_confidence="HIGH",
    sample_record_path_confirmed=True, sample_record_type="docket_search_form",
    sample_search_possible=True, sample_document_view_possible=True,
    verified_from_url="https://iapps.courts.state.ny.us/nyscef/HomePage",
    verification_method="court_portal",
    verification_note="NYSCEF is the official NYS court e-filing system. Greene "
        "County Supreme Court has mandatory e-filing effective 2020-10-21, so "
        "post-2020 mortgage-foreclosure actions expose full dockets and PDF "
        "documents to the public at no charge. " + _court_layers_note,
    known_limitations=["Only e-filed cases are visible — cases filed before "
        "mandatory e-filing (2020-10-21) may not appear; acceptable for a "
        "fresh-distress product",
        "Automated fetch HTTP 403 — headless browser adapter required"],
    open_questions=["Capture verbatim NYSCEF case-type / document-type strings "
        "for Greene County foreclosure cases during Build Mode."],
    stale_after_hours=48, stale_record_policy="KEEP_UNTIL_RELEASED",
    estimated_runtime_minutes=25,
    notes="PRIMARY P0 lead source — judicial mortgage foreclosure + RPTL "
        "Article 11 in-rem tax-foreclosure petitions filed in Supreme Court.",
)

sources["surrogate_court_probate"] = src(
    category="lead", subtype="court_probate",
    url="https://iapps.courts.state.ny.us/nyscef/CaseSearch",
    access_pattern="static_html", official_status="OFFICIAL_COURT",
    lead_value="LEAD_GENERATING", source_reliability_grade="A",
    source_priority="P0", build_priority="high_value",
    scraper_module="scrapers/surrogate_court_probate.py", refresh_cadence="daily",
    ttl_days=1095, source_freshness="DAILY", expected_refresh_cadence="DAILY",
    rate_limit_rpm=20, blocked_unblock_paths=["seeded_session"],
    portal_fingerprint_id="surrogate_court_probate", portal_family="NYSCEF_iApps",
    fingerprint_confidence="HIGH",
    fingerprint_summary="NYSCEF / iApps; Surrogate's Court case search; public, "
        "free PDF documents; same bot-gating as the Supreme Court surface.",
    recommended_adapter="nyscef_case_search (headless browser, county=Greene, "
        "court=Surrogate's Court)",
    official_entity="Greene County Surrogate's Court (NYS Unified Court System)",
    portal_type="surrogate's court e-filing docket and case search",
    records_available=["probate_proceedings", "administration_proceedings",
        "letters_testamentary", "letters_of_administration",
        "miscellaneous_estate_proceedings"],
    search_fields=["index_number", "decedent_name", "county", "court_type",
        "filing_date_range"],
    access_method="SEARCHABLE_PUBLIC_PORTAL",
    public_access_status="FULL_PUBLIC_ACCESS",
    document_access_status="DOCUMENTS_PUBLIC",
    source_role="PRIMARY_LEAD_SOURCE", verification_confidence="HIGH",
    sample_record_path_confirmed=True, sample_record_type="docket_search_form",
    sample_search_possible=True, sample_document_view_possible=True,
    verified_from_url="https://iapps.courts.state.ny.us/nyscef/HomePage",
    verification_method="court_portal",
    verification_note="Greene County Surrogate's Court has mandatory e-filing "
        "effective 2021-02-16; estate proceedings filed since then are publicly "
        "searchable on NYSCEF with free document downloads.",
    known_limitations=["Only e-filed estate proceedings (post-2021-02-16) are "
        "visible", "Some estate documents may be access-restricted per "
        "Surrogate's Court rules; case index and core filings are public",
        "Automated fetch HTTP 403 — headless browser adapter required"],
    open_questions=["Confirm which Surrogate's Court document types are publicly "
        "viewable vs restricted for Greene County."],
    stale_after_hours=72, stale_record_policy="KEEP_UNTIL_RELEASED",
    estimated_runtime_minutes=20,
    notes="PRIMARY P0 lead source — probate / estate administration originates "
        "estate leads (decedent owner, fiduciary appointed).",
)

sources["webcivil_supreme"] = src(
    category="lead", subtype="court_civil",
    url="https://iapps.courts.state.ny.us/webcivil/FCASMain",
    access_pattern="static_html", official_status="OFFICIAL_COURT",
    lead_value="LEAD_GENERATING", source_reliability_grade="A",
    source_priority="P0", build_priority="high_value",
    scraper_module="scrapers/webcivil_supreme.py", refresh_cadence="daily",
    ttl_days=1095, source_freshness="DAILY", expected_refresh_cadence="DAILY",
    rate_limit_rpm=20, blocked_unblock_paths=["seeded_session"],
    portal_fingerprint_id="webcivil_supreme", portal_family="NYSCEF_iApps",
    fingerprint_confidence="HIGH",
    fingerprint_summary="NYS Unified Court System WebCivil Supreme; public "
        "statewide civil case search (active + disposed), no document images; "
        "automated fetch returned HTTP 403.",
    recommended_adapter="webcivil_supreme_search (headless browser, "
        "county=Greene)",
    official_entity="New York State Unified Court System (WebCivil Supreme)",
    portal_type="statewide civil supreme court case status search",
    records_available=["civil_case_status", "parties", "appearance_calendars",
        "case_disposition"],
    search_fields=["index_number", "party_name", "attorney_firm", "judge",
        "county"],
    access_method="SEARCHABLE_PUBLIC_PORTAL",
    public_access_status="PUBLIC_SEARCH_ONLY",
    document_access_status="DOCUMENTS_NOT_AVAILABLE",
    source_role="SUPPORTING_LEAD_SOURCE", verification_confidence="HIGH",
    sample_record_path_confirmed=True, sample_record_type="case_search_form",
    sample_search_possible=True, sample_document_view_possible=False,
    verified_from_url="https://iapps.courts.state.ny.us/webcivil/ecourtsMain",
    verification_method="court_portal",
    verification_note="WebCivil Supreme covers active + disposed civil Supreme "
        "Court cases for all 62 NY counties including Greene; public search, no "
        "login. Supporting role — confirms case status / disposition for "
        "foreclosure leads; exposes no document images.",
    known_limitations=["No document images — status/parties metadata only",
        "Automated fetch HTTP 403 — headless browser adapter required"],
    open_questions=[],
    stale_after_hours=72, stale_record_policy="KEEP_UNTIL_RELEASED",
    estimated_runtime_minutes=15,
    notes="SUPPORTING source — case-status / lifecycle confirmation for "
        "supreme_court_foreclosure leads (suppression of disposed cases).",
)

sources["tax_foreclosure"] = src(
    category="lead", subtype="tax_delinquency",
    url="https://greenecountyny.gov/departments/treasurer/",
    access_pattern="static_html", official_status="OFFICIAL_COUNTY",
    lead_value="LEAD_GENERATING", source_reliability_grade="A",
    source_priority="P1", build_priority="high_value",
    scraper_module="scrapers/tax_foreclosure.py", refresh_cadence="on_demand",
    ttl_days=400, source_freshness="ANNUAL", expected_refresh_cadence="MANUAL",
    rate_limit_rpm=None, blocked_unblock_paths=["manual_pull"],
    portal_fingerprint_id="tax_foreclosure", portal_family="custom_county",
    fingerprint_confidence="MEDIUM",
    fingerprint_summary="Annual 'Petition & Notice of Foreclosure' published as a "
        "PDF on the WordPress county Treasurer page. The 2025 petition is a "
        "scanned, CCITT-fax-encoded image PDF (~2.7 MB) with no text layer — "
        "OCR required.",
    recommended_adapter="pdf_ocr_static_list (download annual petition PDF, OCR, "
        "parse parcel rows)",
    official_entity="Greene County Treasurer",
    portal_type="annual in-rem tax-foreclosure petition (PDF publication)",
    records_available=["tax_foreclosure_petition", "delinquent_parcels"],
    search_fields=[],
    access_method="PDF_PUBLICATION",
    public_access_status="FULL_PUBLIC_ACCESS",
    document_access_status="DOCUMENTS_PUBLIC",
    source_role="PRIMARY_LEAD_SOURCE", verification_confidence="MEDIUM",
    sample_record_path_confirmed=True, sample_record_type="pdf_publication",
    sample_search_possible=False, sample_document_view_possible=True,
    verified_from_url="https://greenecountyny.gov/departments/treasurer/",
    verification_method="official_domain",
    verification_note="The County Treasurer enforces delinquent taxes under NY "
        "RPTL Article 11 and publishes the Annual Petition & Notice of "
        "Foreclosure on greenecountyny.gov. The 2025 petition PDF "
        "(/wp-content/uploads/2025/04/2025-Petition-and-Notice-of-Forclosure.pdf, "
        "published 2025-02-27) was fetched and inspected: it is a scanned image "
        "PDF requiring OCR. Confidence MEDIUM because the per-parcel field layout "
        "was not extractable without OCR during recon.",
    known_limitations=["Annual publication cadence only — no rolling/searchable "
        "delinquent-tax list is published online",
        "2025 petition PDF is scanned (CCITT fax) — OCR required to read SBL, "
        "owner, address, amount, redemption date",
        "Treasurer publishes only the annual petition, not interim delinquency"],
    open_questions=["Confirm the per-parcel field layout inside the petition PDF "
        "(SBL/parcel id, owner name, situs address, amount owed, redemption "
        "deadline, tax years) after OCR.",
        "Confirm publication month each year so the refresh harness can time the "
        "annual pull."],
    stale_after_hours=8760, stale_record_policy="EXPIRE_AFTER_TTL",
    record_ttl_days=400, estimated_runtime_minutes=10,
    estimated_cost_category="FREE",
    notes="PRIMARY tax-distress source — P1 (annual cadence). The official list "
        "of parcels in RPTL Article 11 in-rem tax foreclosure.",
)

sources["tax_foreclosure_auction"] = src(
    category="lead", subtype="tax_delinquency",
    url="https://aarauctions.com/auctions/tax-foreclosures/",
    access_pattern="static_html", official_status="OFFICIAL_VENDOR_PORTAL",
    lead_value="LEAD_GENERATING", source_reliability_grade="C",
    source_priority="P1", build_priority="optional",
    scraper_module="scrapers/tax_foreclosure_auction.py", refresh_cadence="on_demand",
    ttl_days=200, source_freshness="ANNUAL", expected_refresh_cadence="MANUAL",
    rate_limit_rpm=None, blocked_unblock_paths=[],
    portal_fingerprint_id="tax_foreclosure_auction", portal_family="custom_vendor",
    fingerprint_confidence="MEDIUM",
    fingerprint_summary="Absolute Auctions & Realty (aarauctions.com / "
        "nysauctions.com) auction-catalog web app; lots browsed via "
        "/servlet/Search.do?auctionId=<id>; seasonal — Greene catalog exists "
        "only during the annual auction window.",
    recommended_adapter="aar_auction_catalog (HTML, seasonal)",
    official_entity="Greene County Treasurer / Absolute Auctions & Realty",
    portal_type="annual tax-foreclosure real-estate auction catalog",
    records_available=["tax_foreclosed_parcel_lots", "former_owner_of_record",
        "auction_dates"],
    search_fields=["auction_id", "lot_number"],
    access_method="SEARCHABLE_PUBLIC_PORTAL",
    public_access_status="FULL_PUBLIC_ACCESS",
    document_access_status="DOCUMENTS_PUBLIC",
    source_role="SUPPORTING_LEAD_SOURCE", verification_confidence="MEDIUM",
    sample_record_path_confirmed=True, sample_record_type="auction_catalog",
    sample_search_possible=True, sample_document_view_possible=True,
    verified_from_url="https://greenecountyny.gov/departments/treasurer/",
    verification_method="official_vendor_link",
    verification_note="Greene County conducts its annual tax-foreclosure real "
        "estate auction online via Absolute Auctions & Realty (NYSauctions.com); "
        "county news posts and town announcements link this vendor. Catalog "
        "browsing is public; bidder registration is required only to bid. "
        "Supporting role — confirms disposition of tax_foreclosure leads and "
        "surfaces former owner-of-record / surplus context.",
    known_limitations=["Seasonal — catalog published only during the annual "
        "auction window", "Auction vendor is a mirror of county data (grade C)"],
    open_questions=["Confirm the lot-record field layout per auction during "
        "Build Mode."],
    stale_after_hours=8760, stale_record_policy="EXPIRE_AFTER_TTL",
    record_ttl_days=200, estimated_runtime_minutes=10,
    notes="SUPPORTING source — post-foreclosure disposition of tax-foreclosed "
        "parcels; confirms tax_foreclosure leads.",
)

sources["parcel_master"] = src(
    category="enrichment", subtype="parcel_master",
    url="https://greenecounty.prosgar.com/", access_pattern="spa_with_api",
    official_status="OFFICIAL_VENDOR_PORTAL", lead_value="ENRICHMENT",
    source_reliability_grade="E", source_priority="P2", build_priority="enrichment",
    scraper_module="scrapers/parcel_master.py", refresh_cadence="quarterly",
    ttl_days=400, source_freshness="ANNUAL", expected_refresh_cadence="MONTHLY",
    rate_limit_rpm=30, blocked_unblock_paths=[],
    portal_fingerprint_id="parcel_master", portal_family="GAR_PROS",
    fingerprint_confidence="HIGH",
    fingerprint_summary="GAR Associates PROS (Property Record Online System) "
        "assessment-data portal at greenecounty.prosgar.com; public property "
        "search, no login; quick/advanced/related-parcel search.",
    recommended_adapter="nys_clearinghouse_parcel_bulk (preferred — ArcGIS bulk) "
        "OR gar_pros_parcel (per-parcel web)",
    official_entity="Greene County Real Property Tax Service",
    portal_type="parcel assessment / property record portal",
    records_available=["parcel_assessment", "property_inventory",
        "owner_of_record", "comparable_sales", "deed_map_references", "tax_maps"],
    search_fields=["address", "owner_name", "parcel_id", "municipality"],
    access_method="SEARCHABLE_PUBLIC_PORTAL",
    public_access_status="FULL_PUBLIC_ACCESS",
    document_access_status="DOCUMENTS_PUBLIC",
    source_role="ENRICHMENT_SOURCE", verification_confidence="HIGH",
    sample_record_path_confirmed=True, sample_record_type="search_form",
    sample_search_possible=True, sample_document_view_possible=True,
    verified_from_url="https://greenecountyny.gov/departments/rpts/",
    verification_method="official_vendor_link",
    verification_note="RPTS page links greenecounty.prosgar.com as the official "
        "partner property-data portal. Enrichment only — assessment, owner of "
        "record, valuation, comparable sales. Equivalent bulk data is also "
        "available via the NYS GIS Clearinghouse (recommended ingest path).",
    known_limitations=["Enrichment only — never originates a lead",
        "Assessment data lags clerk recordings on ownership/transfer timing"],
    open_questions=["Confirm the canonical-field mapping (parcel_id, situs "
        "address, owner, assessed value) for the chosen ingest path — GAR PROS "
        "vs NYS Clearinghouse — during Build Mode; fields map left empty pending "
        "that decision."],
    stale_after_hours=2160, stale_record_policy="NEVER_EXPIRE",
    estimated_runtime_minutes=30,
    notes="ENRICHMENT (P2) — parcel/owner/valuation context attached to leads.",
)

sources["gis_parcels"] = src(
    category="enrichment", subtype="gis_parcels",
    url="https://gis.gcgovny.com/arcgis/rest/services", access_pattern="open_api",
    official_status="OFFICIAL_COUNTY", lead_value="ENRICHMENT",
    source_reliability_grade="E", source_priority="P2", build_priority="enrichment",
    scraper_module="scrapers/gis_parcels.py", refresh_cadence="quarterly",
    ttl_days=400, source_freshness="ANNUAL", expected_refresh_cadence="MONTHLY",
    rate_limit_rpm=60, blocked_unblock_paths=[],
    portal_fingerprint_id="gis_parcels", portal_family="ArcGIS",
    fingerprint_confidence="HIGH",
    fingerprint_summary="Esri ArcGIS Server at gis.gcgovny.com/arcgis/rest/"
        "services (folders AGOL, Hosted, Utilities); open REST query API; "
        "county GIS maintains the RPTS tax-parcel geodatabase.",
    recommended_adapter="arcgis_feature_query",
    official_entity="Greene County GIS Department",
    portal_type="ArcGIS REST parcel / map services",
    records_available=["tax_parcel_boundaries", "municipal_boundaries",
        "fire_school_districts", "wetlands", "flood_zones", "address_points"],
    search_fields=["parcel_id", "geometry", "address"],
    access_method="API_ENDPOINT",
    public_access_status="FULL_PUBLIC_ACCESS",
    document_access_status="DOCUMENTS_NOT_AVAILABLE",
    source_role="ENRICHMENT_SOURCE", verification_confidence="HIGH",
    sample_record_path_confirmed=True, sample_record_type="api_endpoint",
    sample_search_possible=True, sample_document_view_possible=False,
    verified_from_url="https://greenecountyny.gov/departments/rpts/",
    verification_method="official_domain",
    verification_note="Public ArcGIS REST services directory confirmed at "
        "gis.gcgovny.com/arcgis/rest/services. Enrichment — parcel geometry and "
        "spatial layers. Statewide bulk parcel data also published via the NYS "
        "GIS Clearinghouse (data.gis.ny.gov).",
    known_limitations=["Enrichment only", "Specific parcel layer id within the "
        "MapServer to be confirmed in Build Mode"],
    open_questions=["Identify the exact tax-parcel layer id in the ArcGIS "
        "MapServer during Build Mode."],
    stale_after_hours=2160, stale_record_policy="NEVER_EXPIRE",
    estimated_runtime_minutes=15,
    notes="ENRICHMENT (P2) — GIS parcel geometry / spatial context.",
)

# --------------------------------------------------------- SoR matrix -------

def vlayers(authority, relevance, access, extract, refresh):
    return {"authority": authority, "lead_type_relevance": relevance,
            "access": access, "extractability": extract,
            "refresh_provenance": refresh}


def cand(source_id, url, authority, role, access, bulk, layers,
         path=True, docview=False, fields=None, notes=""):
    return {
        "source_id": source_id, "official_url": url, "authority_type": authority,
        "source_role": role, "access_status": access, "bulk_availability": bulk,
        "verification_layers": layers, "sample_record_path_confirmed": path,
        "sample_document_view_possible": docview,
        "minimum_lead_fields_available": fields or [],
        "operator_verified": False, "notes": notes,
    }


PASS_A = "PASS"
CLERK_FIELDS = ["party_name", "recording_date", "document_type",
                "document_reference"]
COURT_FIELDS = ["party_name", "index_number", "filing_date", "case_type"]


def clerk_cand(relevance):
    return cand("clerk_land_records", "https://www.searchiqs.com/nygre/",
        "Greene County Clerk", "PRIMARY_EVENT_SOURCE", "SEARCH_ONLY_PUBLIC",
        "BATCH_QUERY",
        vlayers("PASS — official county clerk vendor portal (SearchIQS) linked "
                "from greenecountyny.gov",
                relevance,
                "PASS — free guest search; document print fee only",
                "PASS — name/date/doc-type index yields party, date, doc ref",
                "PASS — clerk recordings indexed continuously"),
        path=True, docview=False, fields=CLERK_FIELDS,
        notes="Automated fetch HTTP 403 — headless browser adapter required.")


def nyscef_sup_cand(relevance):
    return cand("supreme_court_foreclosure",
        "https://iapps.courts.state.ny.us/nyscef/CaseSearch",
        "NYS Supreme Court, Greene County", "PRIMARY_EVENT_SOURCE", "OPEN_PUBLIC",
        "BATCH_QUERY",
        vlayers("PASS — NYS Unified Court System (courts.state.ny.us)",
                relevance,
                "PASS — public, no login, free PDF document download",
                "PASS — docket exposes parties, index number, dates, documents",
                "PASS — e-filed continuously; Greene Supreme mandatory e-filing "
                "since 2020-10-21"),
        path=True, docview=True, fields=COURT_FIELDS,
        notes="Automated fetch HTTP 403 — headless browser adapter expected.")


def surrogate_cand(relevance):
    return cand("surrogate_court_probate",
        "https://iapps.courts.state.ny.us/nyscef/CaseSearch",
        "Greene County Surrogate's Court", "PRIMARY_EVENT_SOURCE", "OPEN_PUBLIC",
        "BATCH_QUERY",
        vlayers("PASS — NYS Unified Court System Surrogate's Court",
                relevance,
                "PASS — public NYSCEF access, free PDF downloads",
                "PASS — proceeding exposes decedent, fiduciary, dates",
                "PASS — Greene Surrogate mandatory e-filing since 2021-02-16"),
        path=True, docview=True, fields=["decedent_name", "index_number",
            "filing_date", "proceeding_type"],
        notes="Automated fetch HTTP 403 — headless browser adapter expected.")


def webcivil_cand(relevance, role="SUPPORTING_EVENT_SOURCE"):
    return cand("webcivil_supreme",
        "https://iapps.courts.state.ny.us/webcivil/FCASMain",
        "NYS Unified Court System", role, "OPEN_PUBLIC", "BATCH_QUERY",
        vlayers("PASS — NYS Unified Court System",
                relevance,
                "PASS — public search, no login",
                "PARTIAL — case status / parties only; no document images",
                "PASS — active + disposed civil cases statewide"),
        path=True, docview=False, fields=["party_name", "index_number",
            "case_status"],
        notes="Status-confirmation source; no document images.")


def taxfc_cand(relevance, role="PRIMARY_EVENT_SOURCE"):
    return cand("tax_foreclosure",
        "https://greenecountyny.gov/departments/treasurer/",
        "Greene County Treasurer", role, "OPEN_PUBLIC", "FULL_COUNTY_BULK",
        vlayers("PASS — Greene County Treasurer (greenecountyny.gov)",
                relevance,
                "PASS — annual petition PDF published openly, no login",
                "PARTIAL — 2025 petition is a scanned image PDF; OCR required",
                "PARTIAL — annual publication cadence only"),
        path=True, docview=True, fields=["parcel_sbl", "owner_name",
            "property_address", "amount_owed", "redemption_date"],
        notes="2025 Petition & Notice of Foreclosure inspected — scanned PDF, "
              "OCR required.")


def taxauction_cand(relevance):
    return cand("tax_foreclosure_auction",
        "https://aarauctions.com/auctions/tax-foreclosures/",
        "Greene County Treasurer / Absolute Auctions & Realty",
        "SUPPORTING_EVENT_SOURCE", "OPEN_PUBLIC", "FULL_COUNTY_BULK",
        vlayers("PASS — county-contracted auctioneer, linked from county news",
                relevance,
                "PASS — public catalog; registration only to bid",
                "PASS — lot records expose parcel, former owner, sale date",
                "PARTIAL — seasonal; catalog exists only during auction window"),
        path=True, docview=True, fields=["parcel_id", "former_owner",
            "auction_date", "lot_number"],
        notes="Seasonal auction catalog.")


PACER_CAND = cand("pacer_ndny", "https://pacer.uscourts.gov/",
    "U.S. Bankruptcy Court, Northern District of New York",
    "PRIMARY_EVENT_SOURCE", "PAID_SUBSCRIPTION_REQUIRED", "BATCH_QUERY",
    vlayers("PASS — federal bankruptcy court of jurisdiction",
            "PASS — federal bankruptcy petitions",
            "FAIL — PACER charges per-page access fees",
            "PASS — petitions expose debtor, filing date, chapter",
            "PASS — continuously updated"),
    path=True, docview=True,
    fields=["debtor_name", "case_number", "filing_date", "chapter"],
    notes="Federal — PACER access is paid; operator credentials required.")


def lt(name, applic, authorities, cands, selected, status, notes=""):
    return {"lead_type": name, "state_applicability": applic,
            "expected_authorities": authorities, "candidate_sources": cands,
            "selected_source_id": selected, "status": status,
            "coverage_notes": notes}


NA = "NOT_APPLICABLE_IN_STATE"
AP = "APPLICABLE"
lead_types = []

lead_types.append(lt("Foreclosure", AP,
    ["County Clerk", "Supreme Court"],
    [nyscef_sup_cand("PASS — mortgage foreclosure actions e-filed in Supreme "
        "Court"),
     clerk_cand("PASS — notice of pendency / lis pendens recorded with clerk")],
    "supreme_court_foreclosure", "LIVE_SOURCE_FOUND",
    "NY judicial foreclosure: actions filed in Supreme Court; full docket + "
    "documents on NYSCEF for Greene County (mandatory e-filing since 2020)."))

for tname in ["Trustee Sale", "Notice of Trustee Sale",
              "Notice of Substitute Trustee Sale"]:
    lead_types.append(lt(tname, NA, [], [], "", "NOT_APPLICABLE_IN_STATE",
        "New York is a judicial-foreclosure state; there are no trustee sales "
        "or substitute-trustee sale notices."))

lead_types.append(lt("Sheriff Sale", AP,
    ["Supreme Court", "Sheriff", "Referee"],
    [nyscef_sup_cand("PASS — notice of sale / referee sale filed within the "
        "Supreme Court foreclosure case")],
    "supreme_court_foreclosure", "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
    "NY foreclosure sales are referee's sales noticed inside the Supreme Court "
    "case; the Greene County Sheriff publishes no standalone online sheriff-sale "
    "calendar. Captured via NYSCEF Notice of Sale documents."))

lead_types.append(lt("Tax Lien Foreclosure", AP,
    ["County Treasurer", "Supreme Court"],
    [taxfc_cand("PASS — RPTL Article 11 in-rem tax-foreclosure petition"),
     nyscef_sup_cand("PASS — the tax-foreclosure petition is filed in Supreme "
        "Court")],
    "tax_foreclosure", "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
    "Greene County enforces delinquent taxes via RPTL Article 11 in-rem "
    "foreclosure. The Treasurer's annual Petition & Notice of Foreclosure is the "
    "list; annual cadence; 2025 petition is a scanned PDF (OCR required)."))

lead_types.append(lt("Tax Sale", AP,
    ["County Treasurer", "Auction vendor"],
    [taxauction_cand("PASS — annual tax-foreclosure auction of county-owned "
        "parcels")],
    "tax_foreclosure_auction", "LIVE_SOURCE_FOUND",
    "Tax-foreclosed parcels are sold at the annual online auction via Absolute "
    "Auctions & Realty (NYSauctions.com)."))

lead_types.append(lt("Tax Sale Certificate", AP,
    ["County Treasurer"], [], "", "SOURCE_NOT_FOUND",
    "Greene County enforces delinquent taxes through RPTL Article 11 in-rem "
    "foreclosure, not tax-lien-certificate sales; no certificate sale occurs."))

lead_types.append(lt("Tax Delinquency", AP,
    ["County Treasurer"],
    [taxfc_cand("PASS — delinquent parcels listed in the annual foreclosure "
        "petition")],
    "tax_foreclosure", "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
    "The Treasurer publishes no rolling/searchable delinquent-tax list online — "
    "only the annual Petition & Notice of Foreclosure. Tax-delinquency signal is "
    "therefore annual-cadence (P1)."))

lead_types.append(lt("Lis Pendens", AP,
    ["County Clerk", "Supreme Court"],
    [clerk_cand("PASS — notice of pendency recorded with the County Clerk"),
     nyscef_sup_cand("PASS — notice of pendency also filed in the Supreme Court "
        "case")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "Notices of pendency are recorded with the County Clerk (SearchIQS) and "
    "filed in the Supreme Court case. Note: clerk's published LP index covers "
    "1924-2004 separately — modern coverage to be confirmed in Build Mode."))

lead_types.append(lt("Civil Judgment", AP,
    ["Supreme Court", "County Clerk"],
    [webcivil_cand("PASS — disposed civil cases with money judgments",
        role="PRIMARY_EVENT_SOURCE"),
     clerk_cand("PASS — judgment transcripts docketed with the County Clerk")],
    "webcivil_supreme", "LIVE_SOURCE_FOUND",
    "Civil judgments are entered in Supreme Court (WebCivil shows disposition) "
    "and docketed with the County Clerk as judgment liens."))

lead_types.append(lt("Abstract of Judgment", AP,
    ["County Clerk"],
    [clerk_cand("PASS — transcripts of judgment docketed with the clerk create "
        "judgment liens")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "In NY a transcript of judgment docketed with the County Clerk creates a "
    "judgment lien on real property; visible in clerk judgment records."))

lead_types.append(lt("Mechanic Lien", AP,
    ["County Clerk"],
    [clerk_cand("PASS — mechanic's liens filed with the County Clerk")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "NY Lien Law mechanic's liens are filed with the County Clerk; the clerk's "
    "record list explicitly includes mechanic liens."))

lead_types.append(lt("Construction Lien", AP,
    ["County Clerk"],
    [clerk_cand("PASS — NY construction liens are filed as mechanic's liens "
        "with the County Clerk")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "New York uses the term 'mechanic's lien' (Lien Law Art. 2) for construction "
    "liens; same County Clerk filing."))

lead_types.append(lt("Federal Tax Lien", AP,
    ["County Clerk"],
    [clerk_cand("PASS — federal tax liens filed with the County Clerk")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "IRS federal tax liens are filed with the County Clerk; clerk record list "
    "includes federal liens."))

lead_types.append(lt("State Tax Lien", AP,
    ["County Clerk", "NYS Department of Taxation and Finance"],
    [clerk_cand("PASS — NYS tax warrants filed with the County Clerk")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "NYS tax warrants are filed with the County Clerk (clerk record list "
    "includes state tax liens). NYS also runs a statewide Tax Warrant Notice "
    "System as a secondary index."))

lead_types.append(lt("Probate", AP,
    ["Surrogate's Court"],
    [surrogate_cand("PASS — probate proceedings e-filed in Surrogate's Court")],
    "surrogate_court_probate", "LIVE_SOURCE_FOUND",
    "Greene County Surrogate's Court probate proceedings on NYSCEF (mandatory "
    "e-filing since 2021-02-16)."))

lead_types.append(lt("Affidavit of Heirship", AP,
    ["Surrogate's Court", "County Clerk"],
    [surrogate_cand("PASS — NY resolves intestate succession via Surrogate's "
        "Court administration proceedings")],
    "surrogate_court_probate", "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
    "NY resolves heirship through Surrogate's Court administration proceedings "
    "rather than recorded affidavits of heirship; heirship signal captured via "
    "Letters of Administration in Surrogate's Court."))

lead_types.append(lt("Executor Deed", AP,
    ["County Clerk"],
    [clerk_cand("PASS — executor's deeds recorded with the County Clerk")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "Estate deeds by an executor are recorded with the County Clerk land "
    "records."))

lead_types.append(lt("Administrator Deed", AP,
    ["County Clerk"],
    [clerk_cand("PASS — administrator's deeds recorded with the County Clerk")],
    "clerk_land_records", "LIVE_SOURCE_FOUND",
    "Estate deeds by an administrator are recorded with the County Clerk land "
    "records."))

lead_types.append(lt("Code Lien", AP,
    ["Town code-enforcement offices", "County Clerk"],
    [clerk_cand("PARTIAL — municipal/code liens appear in clerk records when a "
        "town records them")],
    "clerk_land_records", "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
    "Greene County's 14 towns each run their own code enforcement; there is no "
    "county-wide portal. Recorded municipal/code liens are visible in clerk land "
    "records, but un-recorded code activity is not captured."))

for tname in ["Demolition", "Condemnation"]:
    lead_types.append(lt(tname, AP,
        ["Town code-enforcement / building departments"], [], "",
        "SOURCE_NOT_FOUND",
        "Handled by individual town building/code-enforcement offices; no "
        "county-wide online source. Per domain/02_signals_and_sources.md, "
        "municipal code enforcement is out of scope for a county-wide build."))

lead_types.append(lt("Eviction", AP,
    ["Town/Village Justice Courts", "City Courts"], [], "", "SOURCE_NOT_FOUND",
    "NY evictions are filed in town/village Justice Courts and City Courts, "
    "which publish no public online docket countywide; not buildable."))

lead_types.append(lt("Divorce", AP,
    ["Supreme Court"],
    [webcivil_cand("PARTIAL — matrimonial case existence may show in WebCivil "
        "but documents are confidential", role="SUPPORTING_EVENT_SOURCE")],
    "", "NEEDS_OPERATOR_REVIEW",
    "NY matrimonial records are confidential by statute (DRL §235); divorce "
    "filings are not a publicly extractable lead source. The real-property "
    "signal surfaces instead as recorded deeds in clerk records."))

lead_types.append(lt("Bankruptcy", AP,
    ["U.S. Bankruptcy Court, NDNY"], [PACER_CAND], "pacer_ndny",
    "SOURCE_FOUND_PAID",
    "Federal bankruptcy filings are available only via PACER, which charges "
    "access fees; operator credentials required to build."))

lead_types.append(lt("Surplus", AP,
    ["Supreme Court"],
    [nyscef_sup_cand("PASS — surplus money proceedings filed within the Supreme "
        "Court foreclosure case")],
    "supreme_court_foreclosure", "LIVE_SOURCE_FOUND_LIMITED_COVERAGE",
    "Foreclosure-sale surplus money proceedings are post-sale filings within "
    "the Supreme Court foreclosure case file on NYSCEF."))

sor_matrix = {
    "county_slug": "greene_ny", "county_name": "Greene County", "state": "NY",
    "framework_version": FW, "generated_at": "2026-05-19T00:00:00Z",
    "county_build_status": "READY_TO_BUILD", "lead_types": lead_types,
}

coverage_map = {
    "live_sources": ["clerk_land_records", "supreme_court_foreclosure",
        "surrogate_court_probate", "webcivil_supreme", "tax_foreclosure",
        "tax_foreclosure_auction", "parcel_master", "gis_parcels"],
    "blocked_sources": [],
    "limited_coverage_sources": ["tax_foreclosure", "tax_foreclosure_auction"],
    "not_found_lead_types": ["Tax Sale Certificate", "Demolition",
        "Condemnation", "Eviction"],
    "operator_review_required": ["Divorce", "Bankruptcy"],
}

api_discovery = {
    "searched": [
        "searchiqs.com/{api,swagger,docs,api-docs}; SearchIQS/IQS api (web,GitHub)",
        "iapps.courts.state.ny.us/{api,swagger,docs}; NYSCEF/WebCivil api (web,GitHub)",
        "greenecountyny.gov {api, /wp-json}",
        "aarauctions.com/{api,docs}; AAR/nysauctions api (web,GitHub)",
        "prosgar.com/{api,swagger,docs}; GAR Associates PROS api (web,GitHub)",
        "gis.gcgovny.com/arcgis/rest/services (ArcGIS REST directory)",
        "data.gis.ny.gov NYS GIS Clearinghouse (ArcGIS Hub)",
    ],
    "found": [
        {"api_url": "https://gis.gcgovny.com/arcgis/rest/services",
         "api_type": "ArcGIS",
         "documentation_url": "https://gis.gcgovny.com/arcgis/rest/services",
         "auth_required": False, "rate_limited": True,
         "source_role": "ENRICHMENT_SOURCE",
         "notes": "Public Greene County Esri ArcGIS Server; tax-parcel layer "
                  "served here; query via /MapServer/<id>/query."},
        {"api_url": "https://data.gis.ny.gov",
         "api_type": "ArcGIS",
         "documentation_url": "https://data.gis.ny.gov/datasets/"
                              "greene-county-parcel-data",
         "auth_required": False, "rate_limited": True,
         "source_role": "ENRICHMENT_SOURCE",
         "notes": "NYS GIS Clearinghouse — Greene County parcel polygons + "
                  "assessment attributes as bulk download / ArcGIS Feature "
                  "Service. Recommended parcel-master ingest path."},
    ],
    "search_notes": "No documented public API exists for the primary lead "
        "sources (county clerk SearchIQS, NYSCEF/WebCivil court portals, the "
        "tax-foreclosure petition PDF, or the AAR auction catalog) — those are "
        "consumed via form/HTML adapters. Documented APIs exist only for the GIS "
        "/ parcel enrichment layer (ArcGIS).",
}

enrichment_index_strategy = {
    "bulk_index_available": True,
    "bulk_index_source": "NYS GIS Clearinghouse — Greene County Parcel Data "
        "(ArcGIS); county ArcGIS server gis.gcgovny.com",
    "per_record_query_required": False,
    "per_record_query_cost_estimate": "n/a — full-county bulk parcel data is "
        "freely available",
    "recommended_strategy": "Ingest the NYS GIS Clearinghouse Greene County "
        "parcel layer (FULL_COUNTY_BULK, ArcGIS) as the enrichment index; use "
        "GAR PROS for per-parcel verification/spot-checks. Enrichment never "
        "originates a lead — it attaches to clerk/court/tax leads only.",
    "deferred_to_version": None,
}

# --------------------------------------------------------------- config -----

config = {
    "county_id": "greene_ny",
    "county_name": "Greene County",
    "state": "NY",
    "subject_state_full": "New York",
    "fips_code": "36039",
    "timezone": "America/New_York",
    "operator_market_priority": "exploratory",
    "state_rule_family": "NY_judicial_foreclosure",
    "geography": {
        "municipalities": [
            {"name": "Ashland", "code": "ASH"},
            {"name": "Athens", "code": "ATH"},
            {"name": "Cairo", "code": "CAI"},
            {"name": "Catskill", "code": "CAT"},
            {"name": "Coxsackie", "code": "COX"},
            {"name": "Durham", "code": "DUR"},
            {"name": "Greenville", "code": "GRV"},
            {"name": "Halcott", "code": "HAL"},
            {"name": "Hunter", "code": "HUN"},
            {"name": "Jewett", "code": "JEW"},
            {"name": "Lexington", "code": "LEX"},
            {"name": "New Baltimore", "code": "NBA"},
            {"name": "Prattsville", "code": "PRA"},
            {"name": "Windham", "code": "WIN"},
            {"name": "Tannersville", "code": "TAN"},
        ],
        "accepted_municipalities": [
            {"name": n, "kind": "incorporated"} for n in
            ["ASHLAND", "ATHENS", "CAIRO", "CATSKILL", "COXSACKIE", "DURHAM",
             "GREENVILLE", "HALCOTT", "HUNTER", "JEWETT", "LEXINGTON",
             "NEW BALTIMORE", "PRATTSVILLE", "WINDHAM", "TANNERSVILLE"]
        ] + [
            {"name": n, "kind": "unincorporated_community"} for n in
            ["LEEDS", "PALENVILLE", "ROUND TOP", "CORNWALLVILLE", "EAST DURHAM",
             "FREEHOLD", "HAINES FALLS", "WEST COXSACKIE", "CEMENTON", "EARLTON",
             "CLIMAX", "SURPRISE", "ACRA", "OAK HILL", "MEDUSA", "PURLING",
             "HENSONVILLE", "MAPLECREST", "ELKA PARK", "SOUTH CAIRO"]
        ],
        "cross_county_policy": {
            "unknown_city_action": "flag_for_review",
            "neighboring_county_municipalities": [
                "Albany County", "Columbia County", "Ulster County",
                "Delaware County", "Schoharie County"],
        },
        "sale_date_rule": {
            "rule_name": "scheduled_by_court",
            "statute_reference": "NY RPAPL Article 13 (judicial mortgage "
                "foreclosure — referee's sale scheduled by the court); NY RPTL "
                "Article 11 (in-rem tax foreclosure).",
        },
        "parcel_id_format": "^[0-9A-Za-z .\\-]+$",
        "parcel_id_normalization": "preserve-sbl",
        "address_format_notes": "NY tax parcels are identified by Section-Block-"
            "Lot (SBL) / print key. Properties sit within 14 towns (5 with "
            "incorporated villages); county seat is Catskill.",
    },
    "sources": sources,
    "scoring_overrides": {
        "match_confidence_floor": 80,
        "review_queue_ratio_alert_threshold": 0.5,
        "high_equity_assessed_to_sale_ratio": 2.0,
        "long_term_owned_years": 15,
        "senior_owner_proxy_years": 25,
        "favorable_loan_era_start": "2020-01-01",
        "favorable_loan_era_end": "2022-06-30",
    },
    "storage": {
        "mode": "STATIC_JSON_MODE", "supabase_enabled": False,
        "dashboard_payload": "data/leads.json", "retain_raw_records_days": 30,
        "retain_source_runs_days": 365,
    },
    "dashboard": {
        "title": "Greene County, NY — Lead Intelligence",
        "subtitle": "Daily-refreshed real estate distress signals",
        "primary_color": "#0F172A", "accent_color": "#3B82F6",
        "default_view": "all_leads",
        "precanned_views": [
            {"id": "foreclosure_active",
             "label": "Active foreclosure cases",
             "filter": "pattern:foreclosure"},
            {"id": "probate_estate",
             "label": "Probate / estate leads",
             "filter": "pattern:estate"},
            {"id": "tax_distress",
             "label": "Tax-foreclosure parcels",
             "filter": "pattern:tax"},
            {"id": "recorded_liens",
             "label": "Recorded liens (mechanic / tax / judgment)",
             "filter": "pattern:lien"},
        ],
        "view_modes": ["CLIENT_VIEW", "OPERATOR_VIEW"],
        "build_label": "", "build_label_reason": "",
    },
    "deployment": {
        "github_org": "xcerebroai", "github_repo": "greene-ny-intel",
        "live_url": "", "scheduled_task_name": "", "watchdog_task_name": "",
        "scheduler_runtime_class": "", "scheduler_test_fired_at": "",
        "production_verification_status": "", "production_verification_at": "",
        "last_known_good_commit": "", "last_known_good_dashboard_at": "",
    },
    "build_verdict": "READY_TO_BUILD",
    "build_verdict_reason": "Multiple verified PRIMARY_LEAD_SOURCE entries are "
        "publicly accessible without operator escalation: the Greene County "
        "Clerk land records (SearchIQS, SEARCH_ONLY_PUBLIC) and NYS Supreme "
        "Court mortgage-foreclosure dockets (NYSCEF, OPEN_PUBLIC) are both "
        "daily-refresh distress sources, satisfying the P0 gate. Surrogate's "
        "Court probate (NYSCEF) adds estate leads. Enrichment (parcel master, "
        "GIS) is available. No primary P0 source is blocked, so Phase 0.5 was "
        "not required. Tax foreclosure is P1 (annual). Build Mode is authorized "
        "pending operator approval.",
    "build_verdict_at": NOW,
    "auto_resolve_status": "NOT_ATTEMPTED",
    "final_resolution_status": "",
    "operator_override_audit": [],
    "source_of_record_matrix": sor_matrix,
    "source_coverage_map": coverage_map,
    "api_discovery": api_discovery,
    "enrichment_index_strategy": enrichment_index_strategy,
}

# ------------------------------------------------------------- write --------

target = os.path.join(REPO, "config", "counties", "greene_ny.json")
schema = os.path.join(REPO, "config", "counties", "_schema.json")
result = write_county_config(config, target, schema_path=schema, overwrite=True)
print(result.summary())

# Standalone SoR matrix artifact
recon = os.path.join(REPO, "runs", "greene_ny", "recon")
with open(os.path.join(recon, "source_of_record_matrix.json"), "w",
          encoding="utf-8") as fh:
    json.dump(sor_matrix, fh, indent=2)
print("wrote source_of_record_matrix.json")

# Per-source portal fingerprints
fp_dir = os.path.join(recon, "fingerprints")
for sid, s in sources.items():
    fp = {
        "source_id": sid, "county_slug": "greene_ny", "framework_version": FW,
        "fingerprinted_at": NOW, "url": s["url"],
        "portal_family": s["portal_family"], "access_pattern": s["access_pattern"],
        "access_method": s["access_method"],
        "fingerprint_confidence": s["fingerprint_confidence"],
        "fingerprint_summary": s["fingerprint_summary"],
        "recommended_adapter": s["recommended_adapter"],
        "records_available": s["records_available"],
        "search_fields": s["search_fields"],
        "known_limitations": s["known_limitations"],
    }
    with open(os.path.join(fp_dir, sid + ".fingerprint.json"), "w",
              encoding="utf-8") as fh:
        json.dump(fp, fh, indent=2)
print("wrote %d fingerprint files" % len(sources))

if not result.is_ok():
    raise SystemExit(1)
