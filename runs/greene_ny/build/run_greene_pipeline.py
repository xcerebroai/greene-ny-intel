#!/usr/bin/env python3
"""Greene NY — county-side runner of the v5.4.0 staged pipeline.

Drives `scaffold.pipeline.run_pipeline_staged.run_staged_pipeline` (the
public v5.4.0 staged-engine API) with PRINT_KEY-pre-resolved raw events
from all configured primary event sources, plus a parcel_master-backed
enrichment lookup in the dashboard projection.

Sources ingested (PRIMARY event sources only):
  1. tax_foreclosure_auction   AAR / NYSauctions tax-foreclosure
                                auction (post-disposition event)
  2. tax_foreclosure_petition  Treasurer Annual Petition & Notice of
                                Foreclosure (RPTL Art. 11 in-rem court
                                filing; pre-auction). OCR-parsed.
  3. legal_notices_column      Column legal notices (newspaper-
                                published sale / probate / lien notices
                                — filtered to Greene-property only).

Stage boundary discipline (HARD RULES — honored, audited):
- AAR + Treasurer + Column are PRIMARY EVENT SOURCES. Each emits
  raw_events with source_role=PRIMARY_EVENT_SOURCE.
- NYS parcel_master is ENRICHMENT ONLY. Never an event document.
  Never feeds §17. Attached downstream via parcel_id (PRINT_KEY join
  for AAR + Treasurer; address fallback elsewhere).
- §17 reads parties only from the EVENT document. AAR exposes no
  owner per lot → parties=[]. Treasurer + Column DO name owners /
  defendants — those parties are fed to §17 as event-document parties
  (not enrichment).
- Every dashboard row carries event_source / owner_source /
  enrichment_source.

Run: python3 runs/greene_ny/build/run_greene_pipeline.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scaffold.pipeline import run_pipeline_staged  # noqa: E402

OWNER_SOURCE_ENRICHMENT = "parcel_master"
ENRICHMENT_SOURCE = "parcel_master"


# ----------------------------------------------------------------- helpers ---

def _now_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _det_id(prefix: str, *parts) -> str:
    h = hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


def _load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip()]


# --------------------------------------------------- source → raw_event ---

def aar_to_raw_event(aar: dict, pm_by_pk: dict, fetched_at: str) -> dict:
    """AAR auction lot → raw_event. parties=[] (AAR exposes no owner)."""
    p = aar["raw_payload"]
    tax_map = (p.get("tax_map") or "").strip()
    pm = pm_by_pk.get(tax_map)
    parcel_id = pm["parcel_id"] if pm else None
    situs = ((pm.get("address") or "").upper() if pm
             else (p.get("address") or "").strip().upper())
    rid = _det_id("raw", "aar", aar.get("raw_record_id"), tax_map)
    amounts: list = []
    if p.get("full_market_value"):
        amounts.append({"role": "full_market_value",
                        "amount": p["full_market_value"], "currency": "USD"})
    if p.get("current_bid"):
        amounts.append({"role": "current_bid",
                        "amount": p["current_bid"], "currency": "USD"})
    return {
        "raw_event_id": rid,
        "source_id": "tax_foreclosure_auction",
        "source_role": "PRIMARY_EVENT_SOURCE",
        "canonical_doc_type": "tax_foreclosure_notice",
        "raw_doc_type": "TAX_SALE_AUCTION_LOT",
        "instrument_number": p.get("doc_number"),
        "recorded_date": p.get("auction_date"),
        "event_date": None,
        "source_url": aar.get("source_url"),
        "parties": [],
        "document_body_text": None,
        "property_refs": {
            "parcel_id": parcel_id, "situs_address": situs,
            "legal_description": None, "case_number": None,
        },
        "amounts": amounts,
        "evidence_ids": [_det_id("ev", rid)],
        "parser_name": "tax_foreclosure_auction",
        "parser_version": "1.0.0",
        "parser_confidence": aar.get("parser_confidence", 90),
        "captured_at": aar.get("source_fetched_at") or fetched_at,
    }


def petition_to_raw_event(pt: dict, pm_by_pk: dict, fetched_at: str) -> dict:
    """Treasurer petition row → raw_event. parties from Schedule A
    owner column (the petition IS the event document; the owner is a
    named defendant in the in-rem proceeding)."""
    p = pt["raw_payload"]
    sbl = (p.get("tax_map") or "").strip()
    pm = pm_by_pk.get(sbl)
    parcel_id = pm["parcel_id"] if pm else None
    # Prefer parcel_master canonical address; fall back to OCR address.
    situs = ((pm.get("address") or "").upper() if pm
             else (p.get("address_raw") or "").strip().upper())
    rid = _det_id("raw", "petition", sbl)
    parties: list = []
    owner_raw = (p.get("owner_name_raw") or "").strip()
    if owner_raw:
        # The Treasurer petition NAMES the owner as a defendant to the
        # in-rem proceeding — that IS an event-document party (§17).
        parties.append({
            "name": owner_raw, "name_type": "DF",
            "raw_role": "taxpayer_named_in_rem_petition",
        })
    amounts = []
    if p.get("total_owed"):
        amounts.append({"role": "total_tax_owed",
                        "amount": p["total_owed"], "currency": "USD"})
    if p.get("face_total"):
        amounts.append({"role": "face_tax_amount",
                        "amount": p["face_total"], "currency": "USD"})
    return {
        "raw_event_id": rid,
        "source_id": "tax_foreclosure_petition",
        "source_role": "PRIMARY_EVENT_SOURCE",
        "canonical_doc_type": "tax_foreclosure_notice",
        "raw_doc_type": "TAX_FORECLOSURE_PETITION",
        "instrument_number": p.get("instrument_number"),
        "recorded_date": p.get("recorded_date"),
        "event_date": None,
        "source_url": pt.get("source_url"),
        "parties": parties,
        "document_body_text": None,
        "property_refs": {
            "parcel_id": parcel_id, "situs_address": situs,
            "legal_description": None, "case_number": None,
        },
        "amounts": amounts,
        "evidence_ids": [_det_id("ev", rid)],
        "parser_name": "tax_foreclosure_petition",
        "parser_version": "1.0.0",
        "parser_confidence": pt.get("parser_confidence", 75),
        "captured_at": pt.get("source_fetched_at") or fetched_at,
    }


_COL_PARTY_DEF_RX = re.compile(
    r"(?:Plaintiff|Pltf\.?)[^,]*?(?:vs\.|against)\s*"
    r"([A-Z][A-Z\s,\.&'-]{2,80}?)(?:,\s*Defendant|,\s*Defen|\s+et\s*al|\s*,?\s*Defendant)",
    re.IGNORECASE | re.DOTALL,
)
_COL_PARTY_PLAINTIFF_RX = re.compile(
    r"\b([A-Z][A-Z0-9,\s\.&'-]{2,80}?),?\s*(?:Plaintiff|Pltf\.?)",
    re.IGNORECASE,
)


def _classify_canonical_from_column(p: dict) -> str:
    raw = (p.get("raw_doc_type") or "").upper()
    if raw in (
        "NOTICE_OF_SALE", "FINAL_JUDGMENT_OF_FORECLOSURE",
        "LIS_PENDENS", "TAX_FORECLOSURE_NOTICE", "MECHANICS_LIEN",
        "LETTERS_TESTAMENTARY", "LETTERS_OF_ADMINISTRATION",
    ):
        return raw.lower()
    if raw == "ESTATE_NOTICE":
        return "letters_of_administration"
    return "notice_of_sale"


def column_to_raw_event(c: dict, fetched_at: str) -> dict:
    p = c["raw_payload"]
    text = p.get("text") or ""
    canonical = _classify_canonical_from_column(p)
    raw_dt = p.get("raw_doc_type") or "COLUMN_NOTICE"
    rid = _det_id("raw", "column", p.get("instrument_number") or c.get("raw_record_id"))
    parties: list = []
    # Try to extract defendant from the notice text.
    md = _COL_PARTY_DEF_RX.search(text)
    if md:
        nm = re.sub(r"\s+", " ", md.group(1)).strip(" ,.")
        if nm and len(nm) > 2:
            parties.append({"name": nm, "name_type": "DF",
                            "raw_role": "defendant_named_in_notice"})
    mp = _COL_PARTY_PLAINTIFF_RX.search(text)
    if mp:
        nm = re.sub(r"\s+", " ", mp.group(1)).strip(" ,.")
        if nm and len(nm) > 2:
            parties.append({"name": nm, "name_type": "PL",
                            "raw_role": "plaintiff_named_in_notice"})
    # Property address from text — only as a hint; parcel_id stays None
    # (Column doesn't expose Tax Map # in the notice text reliably).
    addr_m = re.search(
        r"\b\d{1,5}\s+[A-Z][a-zA-Z\.\s]+(?:Rd|Road|St|Street|Ave|Avenue|"
        r"Ln|Lane|Dr|Drive|Hwy|Highway|Way|Ct|Court|Blvd|Boulevard|Pl|"
        r"Place|Route|Rt|Pkwy|Parkway|Tr|Trail|Loop|Ter|Terrace|Cir|"
        r"Circle|Sq|Square|Knoll|Park|Pass)\b", text)
    situs = addr_m.group(0).upper() if addr_m else ""
    return {
        "raw_event_id": rid,
        "source_id": "legal_notices_column",
        "source_role": "PRIMARY_EVENT_SOURCE",
        "canonical_doc_type": canonical,
        "raw_doc_type": raw_dt,
        "instrument_number": p.get("instrument_number"),
        "recorded_date": p.get("recorded_date"),
        "event_date": None,
        "source_url": c.get("source_url"),
        "parties": parties,
        "document_body_text": text[:3000],
        "property_refs": {
            "parcel_id": None, "situs_address": situs,
            "legal_description": None, "case_number": None,
        },
        "amounts": [],
        "evidence_ids": [_det_id("ev", rid)],
        "parser_name": "legal_notices_column",
        "parser_version": "1.0.0",
        "parser_confidence": c.get("parser_confidence", 80),
        "captured_at": c.get("source_fetched_at") or fetched_at,
    }


def evidence_entry(raw_event: dict, field: str) -> dict:
    grade_map = {
        "tax_foreclosure_auction": "C",
        "tax_foreclosure_petition": "A",
        "legal_notices_column": "B",
    }
    return {
        "evidence_id": raw_event["evidence_ids"][0],
        "record_id": raw_event["raw_event_id"],
        "field": field,
        "value": raw_event.get("instrument_number") or "",
        "status": "Confirmed",
        "source_id": raw_event["source_id"],
        "source_reliability_grade": grade_map.get(raw_event["source_id"], "C"),
        "source_url": raw_event.get("source_url") or "",
        "captured_at": raw_event["captured_at"],
    }


# --------------------------------------------------- enrichment_provider ---

def build_enrichment_provider(pm_by_parcel_id: dict):
    def provider(parcel_id: Optional[str]) -> Optional[dict]:
        if not parcel_id:
            return None
        pm = pm_by_parcel_id.get(parcel_id)
        if not pm:
            return None
        return {
            "situs_address": (pm.get("address") or "").upper(),
            "situs_city": pm.get("city") or "",
            "situs_state": "NY",
            "owner_name": pm.get("owner_name") or "",
            "owner_mailing_address": pm.get("owner_mailing_address") or "",
            "owner_mailing_city": pm.get("owner_mailing_city") or "",
            "owner_mailing_state": pm.get("owner_mailing_state") or "",
            "owner_mailing_zip": pm.get("owner_mailing_zip") or "",
            "assessed_value": pm.get("assessed_value"),
            "year_built": pm.get("year_built"),
            "property_use": pm.get("property_use") or "",
            "last_sale_price": None,
            "last_sale_date": None,
            "owner_source": OWNER_SOURCE_ENRICHMENT,
            "enrichment_source": ENRICHMENT_SOURCE,
        }
    return provider


# ------------------------------ county-side dashboard projection ---------

_S17_PLACEHOLDER_MARKERS = (
    "unidentified", "unknown", "review_required", "no party",
    "not named", "tax_foreclosure_notice against",
    "notice_of_sale against", "lis_pendens against",
)
_AAR_DOC_RX = re.compile(r"AAR-\d+-\d+")
# Petition lead_ids take two shapes depending on §17 routing:
#   • parties=[defendant] resolved → lead_id = 'lead_parcel_<SWIS_SBL_ID>'
#   • OCR-mangled owner → §17 REVIEW_REQUIRED → lead_id = 'lead_unresolved_<inst>'
#     where <inst> begins 'TX-PETITION-<SBL>'.
_TX_PETITION_RX = re.compile(r"TX-PETITION-[\d\.\-]+")


def _section17_resolved(owner_text: str) -> bool:
    o = (owner_text or "").strip().lower()
    if not o:
        return False
    return not any(m in o for m in _S17_PLACEHOLDER_MARKERS)


def _lookup_enrichment(scored: dict, *, aar_by_doc: dict,
                       petition_by_sbl: dict, pm_by_pk: dict,
                       pm_by_parcel_id: dict) -> tuple[dict, str]:
    """Resolve parcel_master enrichment for a scored_lead. Tries (in order):
       1. seam's primary_parcel_id (works for §17-resolved leads — e.g.
          Treasurer petition rows where parties=[defendant] resolved)
       2. lead_id → AAR doc_number → tax_map (AAR REVIEW_REQUIRED path)
       3. lead_id → TX-PETITION-<SBL> direct (petition REVIEW_REQUIRED path)
    Returns (parcel_master_record_or_empty, join_method)."""
    # 1
    pid = scored.get("primary_parcel_id")
    if pid and pid in pm_by_parcel_id:
        return pm_by_parcel_id[pid], "parcel_id"
    lid = scored.get("lead_id") or ""
    # 2
    m = _AAR_DOC_RX.search(lid)
    if m:
        aar = aar_by_doc.get(m.group(0))
        if aar:
            pm = pm_by_pk.get((aar["raw_payload"].get("tax_map") or "").strip())
            if pm:
                return pm, "print_key"
    # 3
    m = _TX_PETITION_RX.search(lid)
    if m:
        sbl = m.group(0).replace("TX-PETITION-", "")
        pm = pm_by_pk.get(sbl)
        if pm:
            return pm, "print_key"
    return {}, "none"


def _event_source_for(scored: dict) -> str:
    """Authoritative: the matched_lead carries source_ids per §18. The seam
    forwards them to the scored_lead. Use them directly."""
    srcs = scored.get("source_ids") or []
    if srcs:
        return srcs[0]
    # Fallback (should not be needed once source_ids is reliably present):
    lid = scored.get("lead_id") or ""
    if _AAR_DOC_RX.search(lid): return "tax_foreclosure_auction"
    if _TX_PETITION_RX.search(lid): return "tax_foreclosure_petition"
    return "unknown"


def project_lead(scored: dict, *, aar_by_doc: dict,
                 petition_by_sbl: dict, pm_by_pk: dict,
                 pm_by_parcel_id: dict) -> dict:
    seam_parcel = scored.get("parcel_display") or {}
    s17_owner = (scored.get("owner_name") or "").strip()
    s17_ok = _section17_resolved(s17_owner)

    pm_rec, join_method = _lookup_enrichment(
        scored, aar_by_doc=aar_by_doc, petition_by_sbl=petition_by_sbl,
        pm_by_pk=pm_by_pk, pm_by_parcel_id=pm_by_parcel_id,
    )

    pm_enrich: dict = {}
    if pm_rec:
        pm_enrich = {
            "situs_address": (pm_rec.get("address") or "").upper(),
            "situs_city": pm_rec.get("city") or "",
            "situs_state": "NY",
            "owner_name": pm_rec.get("owner_name") or "",
            "owner_mailing_address": pm_rec.get("owner_mailing_address") or "",
            "owner_mailing_city": pm_rec.get("owner_mailing_city") or "",
            "owner_mailing_state": pm_rec.get("owner_mailing_state") or "",
            "owner_mailing_zip": pm_rec.get("owner_mailing_zip") or "",
            "assessed_value": pm_rec.get("assessed_value"),
            "year_built": pm_rec.get("year_built"),
            "property_use": pm_rec.get("property_use") or "",
            "swis_sbl_id": pm_rec.get("parcel_id"),
            "tax_map": pm_rec.get("print_key"),
        }

    enriched_owner = (pm_enrich.get("owner_name")
                      or seam_parcel.get("owner_name") or "").strip()

    if s17_ok:
        display_owner = s17_owner
        owner_source = "section_17"
    elif enriched_owner:
        display_owner = enriched_owner
        owner_source = OWNER_SOURCE_ENRICHMENT
    else:
        display_owner = "Unknown"
        owner_source = "unresolved"

    enriched = bool(pm_enrich)
    situs = pm_enrich or seam_parcel
    event_source = _event_source_for(scored)
    canonical_dt = ""
    # patterns/display_patterns can carry the canonical hint per source
    return {
        "lead_id": scored["lead_id"],
        "scored_lead_id": scored["scored_lead_id"],
        "primary_parcel_id": pm_enrich.get("swis_sbl_id")
                             or scored.get("primary_parcel_id"),
        "tax_map": pm_enrich.get("tax_map"),
        "display_address": ", ".join(v for v in (
            situs.get("situs_address"), situs.get("situs_city"),
            situs.get("situs_state"),
        ) if v),
        "display_owner": display_owner,
        "display_owner_source": owner_source,
        "display_owner_section17_raw": s17_owner,
        "display_owner_mailing_address": situs.get("owner_mailing_address") or "",
        "display_owner_mailing_city": situs.get("owner_mailing_city") or "",
        "display_owner_mailing_state": situs.get("owner_mailing_state") or "",
        "display_owner_mailing_zip": situs.get("owner_mailing_zip") or "",
        "display_score": scored.get("score", 0),
        "display_tier": scored.get("tier") or "",
        "display_patterns": list(scored.get("display_patterns") or []),
        "display_pattern_set": list(scored.get("pattern_set") or []),
        "display_attributes": list(scored.get("attributes") or []),
        "display_deal_paths": [dp.get("path") for dp in scored.get("deal_paths", [])],
        "display_lead_status": scored.get("lead_status", "STACKED_LEAD"),
        "display_assessed_value": situs.get("assessed_value"),
        "display_year_built": situs.get("year_built"),
        "display_property_use": situs.get("property_use"),
        "stack_depth": scored.get("stack_depth", 0),
        "evidence_ids": list(scored.get("evidence_ids") or []),
        "primary_event_date": scored.get("primary_event_date"),
        "review_flags": list(scored.get("review_flags") or []),
        "seam_enrichment_status": scored.get("enrichment_status"),
        "row_enrichment_status": "ENRICHED" if enriched else "UNENRICHED",
        "row_enrichment_join_method": join_method,
        "event_source": event_source,
        "owner_source": owner_source,
        "enrichment_source": ENRICHMENT_SOURCE if enriched else "none",
    }


def build_payload(scored_leads: list, *, semantic_verdict: str, county: str,
                  state: str, build_label: str, build_label_reason: str,
                  aar_by_doc: dict, petition_by_sbl: dict,
                  pm_by_pk: dict, pm_by_parcel_id: dict,
                  per_source_counts: dict) -> dict:
    rows = [project_lead(s, aar_by_doc=aar_by_doc,
                         petition_by_sbl=petition_by_sbl,
                         pm_by_pk=pm_by_pk,
                         pm_by_parcel_id=pm_by_parcel_id)
            for s in scored_leads]
    pat = Counter(); attr = Counter(); sdd = Counter()
    sti = Counter(); dpd = Counter(); ev_src = Counter()
    for s, r in zip(scored_leads, rows):
        for p in s.get("display_patterns") or []: pat[p] += 1
        for a in s.get("attributes") or []: attr[a] += 1
        sdd[str(s.get("stack_depth", 0))] += 1
        sti[s.get("tier", "Archive")] += 1
        for dp in s.get("deal_paths") or []:
            dpd[dp.get("path") or ""] += 1
        ev_src[r["event_source"]] += 1
    return {
        "generated_at": _now_iso(),
        "build_label": build_label,
        "build_label_reason": build_label_reason,
        "mode": "production",
        "county": county, "state": state,
        "semantic_verdict": semantic_verdict,
        "lead_total": len(scored_leads),
        "event_source_counts": dict(ev_src),
        "per_source_raw_records": per_source_counts,
        "owner_source_policy": (
            "Owners attached downstream as enrichment from parcel_master via "
            "PRINT_KEY join. §17 keeps its honest owner-from-document routing "
            "(parties=[] on AAR rows; parties=[defendant] on Treasurer "
            "petition + Column notices). Owner is NEVER relabeled §17-resolved "
            "if §17 didn't resolve it from the source document."
        ),
        "enrichment_breakdown": {
            "ENRICHED": sum(1 for r in rows
                            if r["row_enrichment_status"] == "ENRICHED"),
            "UNENRICHED": sum(1 for r in rows
                              if r["row_enrichment_status"] == "UNENRICHED"),
        },
        "seam_enrichment_breakdown": {
            "ENRICHED": sum(1 for s in scored_leads
                            if s.get("enrichment_status") == "ENRICHED"),
            "UNENRICHED": sum(1 for s in scored_leads
                              if s.get("enrichment_status") == "UNENRICHED"),
        },
        "owner_source_counts": dict(Counter(r["owner_source"] for r in rows)),
        "enrichment_join_method_counts": dict(
            Counter(r["row_enrichment_join_method"] for r in rows)),
        "pattern_counts": dict(sorted(pat.items())),
        "attribute_counts": dict(sorted(attr.items())),
        "stack_depth_distribution": dict(sorted(sdd.items())),
        "score_tier_distribution": dict(sorted(sti.items())),
        "deal_path_distribution": dict(sorted(dpd.items())),
        "records": rows,
    }


# ----------------------------------------------------------------- main ----

def main() -> int:
    workdir = REPO_ROOT / "data" / "production"
    workdir.mkdir(parents=True, exist_ok=True)
    fetched_at = _now_iso()

    pm = _load_jsonl(REPO_ROOT / "data" / "raw" / "parcel_master.jsonl")
    pm_by_pk = {p["raw_payload"]["print_key"]: p["raw_payload"]
                for p in pm if p["raw_payload"].get("print_key")}
    pm_by_parcel_id = {p["raw_payload"]["parcel_id"]: p["raw_payload"]
                       for p in pm if p["raw_payload"].get("parcel_id")}
    print(f"parcel_master: {len(pm)} records (enrichment, never originates leads)")

    aar = _load_jsonl(REPO_ROOT / "data" / "raw"
                      / "tax_foreclosure_auction.jsonl")
    petition = _load_jsonl(REPO_ROOT / "data" / "raw"
                           / "tax_foreclosure_petition.jsonl")
    column = _load_jsonl(REPO_ROOT / "data" / "raw"
                         / "legal_notices_column.jsonl")
    print(f"AAR auction rows: {len(aar)}")
    print(f"Treasurer petition rows: {len(petition)}")
    print(f"Column notices: {len(column)}")

    raw_events: list = []
    evidence_entries: list = []
    raw_events.extend(aar_to_raw_event(r, pm_by_pk, fetched_at) for r in aar)
    raw_events.extend(petition_to_raw_event(r, pm_by_pk, fetched_at)
                      for r in petition)
    raw_events.extend(column_to_raw_event(r, fetched_at) for r in column)
    for r in raw_events:
        field = ("tax_foreclosure_event"
                 if r["canonical_doc_type"] == "tax_foreclosure_notice"
                 else r["canonical_doc_type"])
        evidence_entries.append(evidence_entry(r, field))
    parcel_resolved = sum(1 for r in raw_events
                          if r["property_refs"]["parcel_id"])
    print(f"raw_events: {len(raw_events)}  parcel_id resolved: {parcel_resolved}")
    per_source_counts = {
        "tax_foreclosure_auction": len(aar),
        "tax_foreclosure_petition": len(petition),
        "legal_notices_column": len(column),
    }

    enrichment_provider = build_enrichment_provider(pm_by_parcel_id)

    result = run_pipeline_staged.run_staged_pipeline(
        raw_events,
        evidence_entries=evidence_entries,
        signal_type_labels={
            "tax_foreclosure_notice": "Tax Foreclosure Notice",
            "notice_of_sale": "Foreclosure Notice of Sale",
            "lis_pendens": "Lis Pendens",
            "final_judgment_of_foreclosure": "Final Judgment of Foreclosure",
            "letters_testamentary": "Letters Testamentary",
            "letters_of_administration": "Letters of Administration",
            "mechanics_lien": "Mechanic's Lien",
        },
        workdir=workdir,
        as_of=date.today(),
        enrichment_provider=enrichment_provider,
        approve_needs_review=True,
    )

    print(f"matched_leads: {len(result['matched_leads'])}  "
          f"scored_leads: {len(result['scored_leads'])}  "
          f"§20 verdict: {result['semantic_verdict']}")

    aar_by_doc = {a["raw_payload"].get("doc_number"): a for a in aar
                  if a["raw_payload"].get("doc_number")}
    petition_by_sbl = {p["raw_payload"].get("tax_map"): p for p in petition
                       if p["raw_payload"].get("tax_map")}

    payload = build_payload(
        result["scored_leads"],
        semantic_verdict=result["semantic_verdict"],
        county="Greene County", state="NY",
        build_label="SOURCE_LIMITED",
        build_label_reason=(
            "Three primary event sources are live (AAR tax-foreclosure "
            "auction, Treasurer Annual Petition & Notice of Foreclosure "
            "PDF, Column legal notices). SearchIQS clerk + NYSCEF court "
            "primaries remain Cloudflare-Turnstile-gated — plain headless "
            "Playwright cannot pass; punch-listed for stealth tooling / "
            "operator-seeded session."
        ),
        aar_by_doc=aar_by_doc, petition_by_sbl=petition_by_sbl,
        pm_by_pk=pm_by_pk, pm_by_parcel_id=pm_by_parcel_id,
        per_source_counts=per_source_counts,
    )

    out_main = REPO_ROOT / "data" / "dashboard.json"
    payload_json = json.dumps(payload, indent=2, ensure_ascii=False)
    out_main.write_text(payload_json + "\n", encoding="utf-8")
    (workdir / "dashboard.json").write_text(payload_json + "\n",
                                            encoding="utf-8")
    deploy = REPO_ROOT / "dashboard" / "data"
    deploy.mkdir(parents=True, exist_ok=True)
    (deploy / "dashboard.json").write_text(payload_json + "\n",
                                           encoding="utf-8")
    for fname in ("matched_leads.json", "scored_leads.json",
                  "evidence_ledger.json"):
        src = workdir / fname
        if src.exists():
            (deploy / fname).write_text(src.read_text(encoding="utf-8"),
                                        encoding="utf-8")
            (REPO_ROOT / "data" / fname).write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8",
            )

    owner_attached = sum(1 for r in payload["records"]
                         if r["owner_source"] == OWNER_SOURCE_ENRICHMENT)
    s17_resolved = sum(1 for r in payload["records"]
                       if r["owner_source"] == "section_17")
    enr = payload["enrichment_breakdown"]["ENRICHED"]
    print()
    print(f"lead_total: {payload['lead_total']}")
    print(f"event_source_counts: {payload['event_source_counts']}")
    print(f"pattern_counts: {payload['pattern_counts']}")
    print(f"enrichment_breakdown: {payload['enrichment_breakdown']}")
    print(f"owner attached from parcel_master: {owner_attached}")
    print(f"owner from §17 (event-document): {s17_resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
