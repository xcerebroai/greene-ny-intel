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
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _today_utc() -> date:
    """The 'refresh date' for the NEW/last-30 tags. UTC so the dashboard
    is deterministic regardless of where it's viewed from."""
    return datetime.now(timezone.utc).date()


def _parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _recency_tags(primary_event_date: str | None,
                  refresh_date: date) -> dict:
    """Compute is_new + days_since_event + last_30_days for a record.

    NEW = the county's recorded/filed date equals this refresh's date
    (not the scrape date). Last-30 = recorded/filed in the past 30 days.
    Future-dated events (e.g. a notice with sale_date > today) are NOT
    last-30 by recorded date — those are surfaced by the foreclosure
    sale-window filter instead.
    """
    d = _parse_iso_date(primary_event_date)
    if d is None:
        return {"is_new": False, "days_since_event": None,
                "last_30_days": False}
    delta = (refresh_date - d).days
    return {
        "is_new": delta == 0,
        "days_since_event": delta,
        "last_30_days": 0 <= delta <= 30,
    }

DOC_RE = re.compile(r"AAR-(\d+)-(\d+)")
ENTITY_RX = re.compile(
    r"\b(LLC|L\.L\.C|INC\.?|INCORPORATED|CORP\.?|CORPORATION|LTD\.?|LP|"
    r"COMPANY|CO\.?(?:\s|$)|BANK|ASSOCIATION|CHURCH|COMMISSION|AUTHORITY|"
    r"DISTRICT|COUNTY OF|COUNT(?:Y)? OF|TOWN OF|VILLAGE OF|CITY OF|"
    r"DEPARTMENT|HOLDINGS|GROUP|PARTNERS|REALTY|MGMT|MANAGEMENT|"
    r"PROPERTIES|HOMES|ESTATES|REAL\s+ESTATE|ENTERPRISES|VENTURES|"
    r"PARTNERSHIP|FUND|CAPITAL|EQUITIES|DEVELOPERS|BUILDERS|"
    r"CONSTRUCTION|FARMS|OUTFITTERS|LODGE|HOTEL|MOTEL|RESORT|"
    r"CLUB|RESTAURANT|FOUNDATION|INSTITUTE)\b",
    re.IGNORECASE,
)
TRUST_RX = re.compile(
    r"\b(TRUST(?:EE)?|REVOCABLE|IRREVOCABLE|FAMILY TRUST|LIVING TRUST|"
    r"REV TR|IRREV TR)\b",
    re.IGNORECASE,
)
# Genuine probate signal: "ESTATE OF X" / "EST OF X" / "X ESTATE" /
# "(DECD)" / "HEIRS OF" / "DECEASED". Bare "Estate" in a company name
# is handled separately — the ENTITY_RX checks fire first.
ESTATE_RX = re.compile(
    r"\b(EST(?:ATE)?\s+OF\s+|HEIRS?\s+OF\s+|"
    r"\(?DECEASED\)?|\(?DEC[CD']D?\)?|"  # (DECD), DECEASED, DEC'D, DECD
    r"\bESTATE\s*$|"                     # "Smith John ESTATE" at end
    r"\bESTATE\s*[,;])",                 # "Smith John ESTATE, Smith Mary"
    re.IGNORECASE,
)
# Life estate is a LIVING-tenant arrangement, not probate. Owner is alive.
LIFE_ESTATE_RX = re.compile(
    r"\b(LIFE\s+EST(?:ATE)?|LIFE-?ESTATE|L\.?\s?E\.?\b|"
    r"LIFE\s+TENANT|REMAINDERMAN|REMAINDER\s+INTEREST)\b",
    re.IGNORECASE,
)


def classify_owner_type(name: str) -> str:
    """Order matters: LIFE ESTATE is checked before ENTITY/ESTATE because
    it's neither — it's a living life-tenant arrangement. ENTITY then
    wins over ESTATE so that "Smith Realty Estates LLC" classifies as
    ENTITY (subdivision-name pattern), not as a probate-flavored ESTATE.
    Genuine probate ("ESTATE OF JOHN SMITH", "Smith John (DECD)") only
    matches ESTATE_RX after the entity check has failed.
    """
    s = (name or "").strip()
    if not s:
        return "UNKNOWN"
    low = s.lower()
    if "unidentified" in low or "unknown" in low or "review_required" in low:
        return "UNKNOWN"
    if LIFE_ESTATE_RX.search(s):
        return "LIFE_ESTATE"          # living life-tenant — NOT probate
    if ENTITY_RX.search(s):
        return "ENTITY"               # subdivision/company names win
    if TRUST_RX.search(s):
        return "TRUST"
    if ESTATE_RX.search(s):
        return "ESTATE"               # genuine probate (deceased individual)
    return "INDIVIDUAL"


def parse_address(full: str) -> tuple[str, str, str]:
    """Split 'street, city, state' (Greene's display_address format)."""
    parts = [p.strip() for p in (full or "").split(",") if p.strip()]
    street = parts[0] if len(parts) >= 1 else ""
    city = parts[1] if len(parts) >= 2 else ""
    state = parts[2] if len(parts) >= 3 else "NY"
    return street, city, state


def to_elpaso_record(scored: dict, refresh_date: date) -> dict:
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

    # Per-canonical signal_type so the dashboard's distress-signal
    # checkbox list resolves to one box PER distress flavor (tax
    # foreclosure / foreclosure NOS / lis pendens / probate /
    # mechanic's lien) instead of collapsing everything to a single
    # "foreclosure_notice" key. Each canonical also carries a `chip_class`
    # tag the renderer uses to pick CSS color.
    src = scored.get("event_source") or "unknown"

    canonicals = list(scored.get("canonical_doc_types") or [])
    if not canonicals:
        canonicals = (scored.get("doc_type_normalization") or {}).get(
            "canonical_doc_types") or []
    canonical0 = (canonicals[0] if canonicals else "").lower()

    # canonical → (signal_type, signal_label, doc_type_raw, chip_class)
    # chip_class ∈ {foreclosure, estate, tax_lien} — used by app.js for
    # chip color + by urgencyTier for whether to factor a future sale_date.
    CANONICAL_MAP: dict = {
        "tax_foreclosure_notice": (
            "tax_foreclosure_notice",
            "Tax Foreclosure",
            "TAX_FORECLOSURE_NOTICE",
            "foreclosure"),
        "notice_of_sale": (
            "notice_of_sale",
            "Foreclosure Notice of Sale",
            "NOTICE_OF_SALE",
            "foreclosure"),
        "final_judgment_of_foreclosure": (
            "final_judgment_of_foreclosure",
            "Final Judgment of Foreclosure",
            "FINAL_JUDGMENT_OF_FORECLOSURE",
            "foreclosure"),
        "lis_pendens": (
            "lis_pendens",
            "Lis Pendens / Foreclosure Summons",
            "LIS_PENDENS",
            "foreclosure"),
        "mechanics_lien": (
            "mechanics_lien",
            "Mechanic's Lien",
            "MECHANICS_LIEN",
            "foreclosure"),
        "letters_testamentary": (
            "letters_testamentary",
            "Probate — Letters Testamentary",
            "LETTERS_TESTAMENTARY",
            "estate"),
        "letters_of_administration": (
            "letters_of_administration",
            "Probate — Letters of Administration",
            "LETTERS_OF_ADMINISTRATION",
            "estate"),
        "estate_notice": (
            "estate_notice",
            "Probate — Estate Notice",
            "ESTATE_NOTICE",
            "estate"),
    }

    # Per-source label refinement (only for tax_foreclosure_notice,
    # where the SAME canonical comes from 3 different sources and the
    # operator wants the source distinguished in the label).
    SOURCE_LABEL_REFINE: dict = {
        ("tax_foreclosure_notice", "tax_foreclosure_petition"):
            ("Tax Foreclosure — In-Rem Petition", "TAX_FORECLOSURE_PETITION"),
        ("tax_foreclosure_notice", "tax_foreclosure_auction"):
            ("Tax Foreclosure — Auction", "TAX_SALE_AUCTION_LOT"),
        ("tax_foreclosure_notice", "legal_notices_column"):
            ("Tax Foreclosure — Public Notice", "COLUMN_TAX_FORECLOSURE_NOTICE"),
    }

    if canonical0 in CANONICAL_MAP:
        sig_type, label, doc_raw, chip_class = CANONICAL_MAP[canonical0]
        refine = SOURCE_LABEL_REFINE.get((canonical0, src))
        if refine:
            label, doc_raw = refine
    else:
        # Fallback for unmapped types — preserve as-is, classify as
        # foreclosure chip-class by default.
        sig_type = canonical0 or "distress_event"
        label = "Distress Event"
        doc_raw = (canonical0 or "UNKNOWN").upper()
        chip_class = "foreclosure"

    src_id = src

    # source_urls per source
    if src == "tax_foreclosure_auction" and auction_id:
        urls = [f"https://aarauctions.com/servlet/Search.do?auctionId={auction_id}"]
    elif src == "tax_foreclosure_petition":
        urls = ["https://greenecountyny.gov/departments/treasurer/"]
    else:
        urls = []

    stack_depth = int(scored.get("stack_depth") or 0)
    # Source URLs (aarauctions, greenecountyny.gov, column.us, etc.) are
    # internal evidence pointers — they belong in the evidence ledger
    # and the CSV export, NOT in the client-facing UI payload. The
    # renderer omits them from the lead-board signal entry.
    signals = [{
        "signal_type": sig_type,
        "signal_label": label,
        "signal_confidence": "HIGH",
        "chip_class": chip_class,
        "count": max(1, stack_depth),
        "instrument_numbers": [doc_num] if doc_num else [],
        "doc_type_raw": doc_raw,
        "recorded_date": sale_date,
        "sale_date": sale_date,
    }]

    is_review = (scored.get("display_lead_status") == "REVIEW_REQUIRED")
    enr_status = scored.get("row_enrichment_status") or "UNENRICHED"
    parcel_resolved = bool(scored.get("primary_parcel_id"))

    recency = _recency_tags(sale_date, refresh_date)
    # Historical = primary event date is more than 365 days old. The
    # default sort de-prioritizes historical leads; they remain
    # visible (stack_depth signal is preserved) but rank below current.
    is_historical = (recency["days_since_event"] is not None
                     and recency["days_since_event"] > 365)

    return {
        "lead_id": lead_id,
        "parcel_resolution_status": "RESOLVED" if parcel_resolved else "UNRESOLVED",
        "parcel_id": scored.get("primary_parcel_id") or "",
        "tax_map": scored.get("tax_map") or "",
        # Greene-appropriate enrichment provenance. EPCAD (El Paso
        # Central Appraisal District) was a hold-over from the El Paso
        # renderer port — irrelevant to NY. The field name is now
        # `parcel_master_enrichment_status` (the NYS GIS parcel layer);
        # `enrichment_status` stays as an unqualified alias.
        "parcel_master_enrichment_status": enr_status,
        "enrichment_status": enr_status,
        "filer_entity": "",
        "owner_name": owner or "Unknown",
        "owner_type": owner_type,
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
        "signal_types": [sig_type],
        "signal_chip_class": chip_class,
        "signal_count": max(1, stack_depth),
        "stack_depth": stack_depth,
        "latest_event_date": sale_date,
        # Recency tagging (UI-3). Pipeline-frozen against refresh_date,
        # not the viewer's wall clock — same NEW set for every operator.
        "recorded_date": sale_date,
        "is_new": recency["is_new"],
        "days_since_event": recency["days_since_event"],
        "last_30_days": recency["last_30_days"],
        # Historical = primary event > 365 days old. Visible by default;
        # the renderer pushes them below current/recent in default sort.
        "is_historical": is_historical,
        "review_required": is_review,
        # review_reason is intentionally NOT carried into the client
        # payload — it contains internal-pipeline commentary
        # ("§17 routing", "owner_not_on_document", source IDs) that
        # belongs in the evidence ledger, not the lead board.
    }


_OWNER_NORMALIZE_PUNCT = re.compile(r"[,/\-\.&;%\(\)\"']+")
_OWNER_BOILERPLATE = re.compile(
    r"\b(estate\s+of\s+|heirs?\s+of\s+|"
    r"lately\s+domiciled\s+at.*$|"
    r"\-?\s*estate\b|"
    r"\(decd?\)|\(deceased\)|"
    r"%\s*[a-z\s]+$|"   # "% Hugh Sterritt" attention-of suffix
    r"executr?ix?|"
    r"attn?:?\s+|"
    r"\bett?\s+al\b|"
    r"\betal\b)",
    re.IGNORECASE,
)


def _normalize_owner(name: str) -> str:
    """Owner-name canonical form for dedupe — strip boilerplate ('Estate
    of', 'lately domiciled at...', '% trustee', '(DECD)'), collapse
    whitespace, lowercase. Two raw strings that name the same person
    should collapse to the same normalized form even if one is
    'Smith John Estate' and the other is 'Estate of John Smith'."""
    s = (name or "").lower()
    s = _OWNER_BOILERPLATE.sub(" ", s)
    s = _OWNER_NORMALIZE_PUNCT.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Sort name tokens so "smith john" and "john smith" hash equally
    toks = sorted(t for t in s.split() if len(t) >= 2)
    return " ".join(toks)


_GENERIC_OWNER = re.compile(
    r"^(unknown|unidentified.*|review.required.*)$",
    re.IGNORECASE,
)


def _dedupe_records(records: list[dict]) -> tuple[list[dict], int]:
    """Collapse rows that name the SAME identified owner against the SAME
    parcel-or-address with the SAME signal_type. Rows without a strong
    identity anchor (anonymous "Unknown" Column notices, missing
    parcel_id AND missing property_full_address) are NEVER collapsed —
    each anonymous notice is treated as a distinct lead.

    Keeps the most-recent recorded_date; preserves the higher
    signal_count + stack_depth across the merged pair.
    """
    by_key: dict = {}
    order: list = []
    raw_owner_norm = lambda s: _normalize_owner(s or "")
    for r in records:
        owner_raw = (r.get("owner_name") or "").strip()
        owner_n = raw_owner_norm(owner_raw)
        is_generic = (not owner_n) or _GENERIC_OWNER.search(owner_raw.lower())
        parcel = (r.get("parcel_id") or "").strip().lower()
        address = (r.get("property_full_address") or "").strip().lower()
        sig_type = (r.get("signal_types") or ["?"])[0]
        # Strong identity = real owner AND (parcel_id OR street address).
        # Anonymous notices with no parcel/address keep ALL copies.
        if not is_generic and (parcel or address):
            key = (owner_n, parcel or address, sig_type)
        elif not is_generic and owner_n and len(owner_n) >= 12:
            # Named owner but no parcel anchor — only collapse if the
            # owner-name token-set is reasonably specific (≥ 12 chars
            # after normalization) so e.g. "John Smith" doesn't merge
            # two unrelated probate notices.
            key = (owner_n, "", sig_type)
        else:
            order.append(r)
            continue
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = r
            order.append(r)
            continue
        # Choose the canonical row by most-recent recorded_date.
        new_date = r.get("recorded_date") or ""
        old_date = existing.get("recorded_date") or ""
        keep, drop = (r, existing) if new_date > old_date else (existing, r)
        keep["signal_count"] = max(
            keep.get("signal_count") or 1,
            drop.get("signal_count") or 1,
        )
        keep["stack_depth"] = max(
            keep.get("stack_depth") or 0,
            drop.get("stack_depth") or 0,
        )
        if keep is r:
            for i, x in enumerate(order):
                if x is existing:
                    order[i] = r
                    break
            by_key[key] = r
    dropped = len(records) - len(order)
    return order, dropped


def main() -> int:
    src = REPO_ROOT / "data" / "dashboard.json"
    payload = json.loads(src.read_text(encoding="utf-8"))

    refresh_date = _today_utc()
    refresh_iso = refresh_date.isoformat()
    records_raw = [to_elpaso_record(s, refresh_date)
                   for s in payload.get("records", [])]
    records, dupes_dropped = _dedupe_records(records_raw)
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

    new_today = sum(1 for r in records if r["is_new"])
    last_30 = sum(1 for r in records if r["last_30_days"])
    historical = sum(1 for r in records if r.get("is_historical"))
    current_cycle = len(records) - historical
    estate_count = sum(1 for r in records if r["owner_type"] == "ESTATE")
    life_estate_count = sum(1 for r in records if r["owner_type"] == "LIFE_ESTATE")

    # Client-facing payload — strictly operator-visible stats. Internal
    # build commentary (build_label, build_label_reason — the
    # SOURCE_LIMITED / stealth / Cloudflare / cf_clearance / recon-path
    # prose) is intentionally OMITTED. So are owner_source_policy /
    # owner_source_counts / enrichment_join_method_counts /
    # semantic_verdict / sources_active — all internal-pipeline labels.
    out = {
        "generated_at": payload.get("generated_at"),
        "refresh_date": refresh_iso,
        "county": payload.get("county"),
        "state": payload.get("state"),
        "lead_total": len(records),
        "actionable_leads": actionable,
        "review_required": review,
        "new_today_count": new_today,
        "last_30_days_count": last_30,
        "current_cycle_count": current_cycle,
        "historical_count": historical,
        "estate_count": estate_count,
        "life_estate_count": life_estate_count,
        "parcel_master_enrichment_resolved": enriched,
        "parcel_master_enrichment_unresolved": unenriched,
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
        for t in ("INDIVIDUAL", "ENTITY", "ESTATE", "LIFE_ESTATE",
                  "TRUST", "UNKNOWN")
    }
    oos = sum(1 for r in records if r["out_of_state_owner_flag"])
    abs_ = sum(1 for r in records if r["absentee_owner_flag"])
    sig_type_counts: dict = {}
    for r in records:
        for t in (r.get("signal_types") or []):
            sig_type_counts[t] = sig_type_counts.get(t, 0) + 1
    print(f"records (after dedupe): {len(records)}  "
          f"duplicates collapsed: {dupes_dropped}")
    print(f"actionable: {actionable}  review: {review}")
    print(f"enriched: {enriched}  unenriched: {unenriched}")
    print(f"owner_types: {owner_type_counts}")
    print(f"out_of_state: {oos}  absentee: {abs_}")
    print(f"signal_type breakdown: {sig_type_counts}")
    print(f"current_cycle: {current_cycle}  historical: {historical}")
    print(f"refresh_date: {refresh_iso}  "
          f"NEW (filed today): {new_today}  "
          f"last 30 days: {last_30}")
    print(f"wrote {target_dir/'data.js'} + {target_dir/'data.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
