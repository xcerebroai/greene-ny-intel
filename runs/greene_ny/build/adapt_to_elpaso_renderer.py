#!/usr/bin/env python3
"""Transform Greene NY v5.4.0 staged dashboard payload → El Paso renderer shape.

The El Paso operator lead-board renderer (`dashboard/app.js`) reads
`window.LEADS = {county, state, build_label, lead_total, records:[...]}`
where each record has fields like `owner_name`, `owner_type`,
`property_full_address`, `signals:[{signal_type, signal_label, sale_date,
source_urls, instrument_numbers, ...}]`, etc.

This county-side adapter reads `data/dashboard.json` (Greene's v5.4.0
staged payload — 50 real AAR tax-foreclosure leads, all PRINT_KEY-joined
to parcel_master with `owner_source=parcel_master`) and emits:

  dashboard/data.js    -> `window.LEADS = {...};` (script-loaded)
  dashboard/data.json  -> same payload, JSON-only

No scaffold/ or knowledge_base/ edits. Only the dashboard/ files this
runner writes are county-side artifacts. Source of truth remains
`data/dashboard.json` (output of `runs/greene_ny/build/run_greene_pipeline.py`).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

DOC_RE = re.compile(r"AAR-(\d+)-(\d+)")
ENTITY_RX = re.compile(
    r"\b(LLC|L\.L\.C|INC\.?|INCORPORATED|CORP\.?|CORPORATION|LTD\.?|LP|"
    r"COMPANY|CO\.?(?:\s|$)|BANK|ASSOCIATION|CHURCH|COMMISSION|AUTHORITY|"
    r"DISTRICT|COUNTY OF|COUNT(?:Y)? OF|TOWN OF|VILLAGE OF|CITY OF|"
    r"DEPARTMENT|HOLDINGS|GROUP|PARTNERS|REALTY|MGMT|MANAGEMENT)\b",
    re.IGNORECASE,
)
TRUST_RX = re.compile(
    r"\b(TRUST(?:EE)?|REVOCABLE|IRREVOCABLE|FAMILY TRUST|LIVING TRUST|"
    r"REV TR|IRREV TR)\b",
    re.IGNORECASE,
)
ESTATE_RX = re.compile(
    r"\b(EST(?:ATE)? OF|HEIRS? OF|DECEASED|DECD|DEC\'D)\b",
    re.IGNORECASE,
)


def classify_owner_type(name: str) -> str:
    s = (name or "").strip()
    if not s:
        return "UNKNOWN"
    low = s.lower()
    if "unidentified" in low or "unknown" in low or "review_required" in low:
        return "UNKNOWN"
    if ESTATE_RX.search(s):
        return "ESTATE"
    if TRUST_RX.search(s):
        return "TRUST"
    if ENTITY_RX.search(s):
        return "ENTITY"
    return "INDIVIDUAL"


def parse_address(full: str) -> tuple[str, str, str]:
    """Split 'street, city, state' (Greene's display_address format)."""
    parts = [p.strip() for p in (full or "").split(",") if p.strip()]
    street = parts[0] if len(parts) >= 1 else ""
    city = parts[1] if len(parts) >= 2 else ""
    state = parts[2] if len(parts) >= 3 else "NY"
    return street, city, state


def to_elpaso_record(scored: dict) -> dict:
    lead_id = scored.get("lead_id") or ""
    m = DOC_RE.search(lead_id)
    auction_id = m.group(1) if m else ""
    lot_num = m.group(2) if m else ""
    doc_num = f"AAR-{auction_id}-{lot_num}" if m else ""

    owner = (scored.get("display_owner") or "").strip()
    owner_type = classify_owner_type(owner)

    property_full = (scored.get("display_address") or "").strip()
    p_street, p_city, p_state = parse_address(property_full)

    m_city = (scored.get("display_owner_mailing_city") or "").strip()
    m_state = (scored.get("display_owner_mailing_state") or "").strip()
    m_zip = (scored.get("display_owner_mailing_zip") or "").strip()
    m_addr = (scored.get("display_owner_mailing_address") or "").strip()
    mailing_full = ", ".join(p for p in (m_addr, m_city, m_state, m_zip) if p)

    out_of_state = bool(m_state and m_state.upper() not in ("NY", ""))
    absentee = bool(m_city and p_city and m_city.upper() != p_city.upper())

    # Sale / event date — Greene's primary_event_date from staged pipeline
    # falls back to AAR auction_date encoded in the doc_number's auctionId.
    sale_date = scored.get("primary_event_date") or ""

    # Signal: tax-foreclosure-auction lot. We use signal_type
    # `foreclosure_notice` (matching El Paso's renderer's exact string) so
    # the existing urgency tier / sale-window filter / fcl chip class fire
    # for these leads. signal_label preserves the precise distress type so
    # operators see "Tax Foreclosure — Sale ..." in the chip.
    sources = []
    if auction_id:
        sources = [f"https://aarauctions.com/servlet/Search.do?auctionId={auction_id}"]

    signals = [{
        "signal_type": "foreclosure_notice",
        "signal_label": "Tax Foreclosure Auction",
        "signal_confidence": "HIGH",
        "source_id": "tax_foreclosure_auction",
        "count": 1,
        "source_urls": sources,
        "evidence_ids": list(scored.get("evidence_ids") or []),
        "instrument_numbers": [doc_num] if doc_num else [],
        "doc_type_raw": "TAX_SALE_AUCTION_LOT",
        "recorded_date": sale_date,
        "sale_date": sale_date,
    }]

    is_review = (scored.get("display_lead_status") == "REVIEW_REQUIRED")
    enr_status = scored.get("row_enrichment_status") or "UNENRICHED"
    parcel_resolved = bool(scored.get("primary_parcel_id"))

    return {
        "lead_id": lead_id,
        "parcel_resolution_status": "RESOLVED" if parcel_resolved else "UNRESOLVED",
        "parcel_id": scored.get("primary_parcel_id") or "",
        "tax_map": scored.get("tax_map") or "",
        # El Paso's renderer reads epcad_enrichment_status only for the
        # top-level count; we provide a Greene-friendly alias too.
        "epcad_enrichment_status": enr_status,
        "enrichment_status": enr_status,
        # AAR doesn't expose a filer; §17 placeholder is preserved on the
        # source row but not surfaced as a filer in this projection.
        "filer_entity": "",
        # owner — comes from parcel_master via the PRINT_KEY join; per-row
        # provenance is visible via owner_source.
        "owner_name": owner or "Unknown",
        "owner_type": owner_type,
        "owner_source": scored.get("owner_source") or "unresolved",
        "owner_source_section17_raw": scored.get("display_owner_section17_raw")
                                       or "",
        "property_full_address": property_full,
        "property_street": p_street,
        "property_city": p_city,
        "property_state": p_state,
        "property_zip": "",
        "mailing_full_address": mailing_full,
        "mailing_city": m_city,
        "mailing_state": m_state,
        "mailing_zip": m_zip,
        "assessed_value": scored.get("display_assessed_value"),
        "appraised_value": None,
        "homestead": None,
        "absentee_owner_flag": absentee,
        "out_of_state_owner_flag": out_of_state,
        "legal_description": "",
        "signals": signals,
        "signal_types": ["foreclosure_notice"],
        "source_urls": sources,
        "latest_event_date": sale_date,
        "review_required": is_review,
        "review_reason": (
            "owner_not_on_document — AAR exposes no owner per lot; "
            "owner attached downstream from parcel_master."
        ) if is_review else "",
    }


def main() -> int:
    src = REPO_ROOT / "data" / "dashboard.json"
    payload = json.loads(src.read_text(encoding="utf-8"))

    records = [to_elpaso_record(s) for s in payload.get("records", [])]
    # actionable = operator-workable: owner known (from any source) AND
    # parcel resolved. The §17 REVIEW_REQUIRED routing is a separate quality
    # flag (preserved in `review_required` per row) — it indicates owner
    # attribution provenance ("owner came from enrichment, not the source
    # document"), NOT that the lead is unworkable.
    def _workable(r: dict) -> bool:
        owner_ok = bool(r.get("owner_name")) and r["owner_type"] != "UNKNOWN"
        parcel_ok = r.get("parcel_resolution_status") == "RESOLVED"
        return owner_ok and parcel_ok
    actionable = sum(1 for r in records if _workable(r))
    review = sum(1 for r in records if r["review_required"])
    enriched = sum(1 for r in records if r["enrichment_status"] == "ENRICHED")
    unenriched = sum(1 for r in records if r["enrichment_status"] == "UNENRICHED")

    out = {
        "generated_at": payload.get("generated_at"),
        "county": payload.get("county"),
        "state": payload.get("state"),
        "build_label": payload.get("build_label"),
        "build_label_reason": payload.get("build_label_reason", ""),
        "semantic_verdict": payload.get("semantic_verdict"),
        "sources_active": ["tax_foreclosure_auction"],
        "lead_total": len(records),
        "actionable_leads": actionable,
        "review_required": review,
        # El Paso-style enrichment count names + Greene-friendly aliases
        "epcad_enrichment_resolved": enriched,
        "epcad_enrichment_unresolved": unenriched,
        "parcel_master_enrichment_resolved": enriched,
        "parcel_master_enrichment_unresolved": unenriched,
        # provenance breakdowns from the staged payload, surfaced for ops:
        "owner_source_counts": payload.get("owner_source_counts", {}),
        "enrichment_join_method_counts": payload.get(
            "enrichment_join_method_counts", {}),
        "owner_source_policy": payload.get("owner_source_policy", ""),
        "records": records,
    }

    target_dir = REPO_ROOT / "dashboard"
    (target_dir / "data.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # window.LEADS = {...}; — the script-tag form El Paso uses.
    (target_dir / "data.js").write_text(
        "window.LEADS = " + json.dumps(out, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )

    owner_type_counts = {
        t: sum(1 for r in records if r["owner_type"] == t)
        for t in ("INDIVIDUAL", "ENTITY", "ESTATE", "TRUST", "UNKNOWN")
    }
    oos = sum(1 for r in records if r["out_of_state_owner_flag"])
    abs_ = sum(1 for r in records if r["absentee_owner_flag"])
    print(f"records: {len(records)}")
    print(f"actionable: {actionable}  review: {review}")
    print(f"enriched: {enriched}  unenriched: {unenriched}")
    print(f"owner_types: {owner_type_counts}")
    print(f"out_of_state: {oos}  absentee: {abs_}")
    print(f"wrote {target_dir/'data.js'} + {target_dir/'data.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
