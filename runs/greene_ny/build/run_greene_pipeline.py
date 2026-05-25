#!/usr/bin/env python3
"""Greene NY — county-side runner of the v5.4.0 staged pipeline.

Drives `scaffold.pipeline.run_pipeline_staged.run_staged_pipeline` (the
public v5.4.0 staged-engine API) with PRINT_KEY-pre-resolved AAR raw
events and a parcel_master-backed enrichment_provider.

Why a county-side runner rather than `build_leads.py`?
-----------------------------------------------------
`build_leads.py`'s monolith calls `foreclosure_notices.translate(...)`
which emits signals WITHOUT an `address` field, so the downstream
address-based matcher in `build_leads.py` cannot bridge AAR signals to
parcel_master rows. The natural join is Tax Map # → PRINT_KEY (the
operator-named authoritative key on both sides). Doing that join
county-side, before the staged engine runs, lets the engine receive
raw_events with `property_refs.parcel_id` already resolved to the
NYS `SWIS_SBL_ID`. No scaffold edit required.

Stage boundary discipline (hard rules)
--------------------------------------
- AAR tax_foreclosure_auction is the SOLE PRIMARY EVENT SOURCE.
  Every raw_event carries source_id=tax_foreclosure_auction,
  source_role=PRIMARY_EVENT_SOURCE.
- parcel_master is ENRICHMENT ONLY. No parcel_master row ever appears
  as a raw_event. parcel_master is NOT passed to §17 as a document.
- `parties=[]` is passed through to §17 — AAR does not name an owner
  per lot. §17 stays HONEST: it routes these leads to REVIEW_REQUIRED
  with an "owner-unresolved" placeholder, and that routing is
  preserved.
- The owner attaches DOWNSTREAM via the `enrichment_provider`
  (the §13.14 / R3-iii enrichment seam). The dashboard projection
  records `owner_source = parcel_master` explicitly and preserves the
  §17-raw owner placeholder in `display_owner_section17_raw` for full
  transparency. Owner is NEVER relabeled as §17-resolved.

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

EVENT_SOURCE = "tax_foreclosure_auction"
OWNER_SOURCE = "parcel_master"
ENRICHMENT_SOURCE = "parcel_master"


# ----------------------------------------------------------------- helpers ---

def _now_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _det_id(prefix: str, *parts) -> str:
    h = hashlib.sha1("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


def _load_jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip()]


# ----------------------------------------------------- raw_event construction

def aar_to_raw_event(aar: dict, pm_by_pk: dict, fetched_at: str) -> dict:
    """Convert one AAR wrapped raw record into a v5.4.0 raw_event_record.
    PRINT_KEY join is the authoritative parcel-id resolution. parties is
    DELIBERATELY empty — AAR does not name an owner per lot. §17 will
    flag owner-unresolved per its contract; that is correct."""
    p = aar["raw_payload"]
    tax_map = (p.get("tax_map") or "").strip()
    pm = pm_by_pk.get(tax_map)

    # Authoritative parcel_id from parcel_master via PRINT_KEY scan.
    parcel_id = pm["parcel_id"] if pm else None

    # situs prefers the parcel_master canonical address (joined), falls
    # back to the AAR address (preserved verbatim for provenance).
    situs_address = (
        (pm.get("address") or "").strip().upper() if pm
        else (p.get("address") or "").strip().upper()
    )

    raw_event_id = _det_id("raw", aar.get("raw_record_id"), tax_map)
    amounts: list = []
    if p.get("full_market_value"):
        amounts.append({"role": "full_market_value",
                        "amount": p["full_market_value"], "currency": "USD"})
    if p.get("current_bid"):
        amounts.append({"role": "current_bid",
                        "amount": p["current_bid"], "currency": "USD"})

    return {
        "raw_event_id": raw_event_id,
        "source_id": EVENT_SOURCE,
        "source_role": "PRIMARY_EVENT_SOURCE",
        "canonical_doc_type": "tax_foreclosure_notice",
        "raw_doc_type": "TAX_SALE_AUCTION_LOT",
        "instrument_number": p.get("doc_number"),
        "recorded_date": p.get("auction_date"),
        "event_date": None,
        "source_url": aar.get("source_url"),
        "parties": [],     # AAR exposes no owner per lot — HONEST empty
        "document_body_text": None,
        "property_refs": {
            "parcel_id": parcel_id,
            "situs_address": situs_address,
            "legal_description": None,
            "case_number": None,
        },
        "amounts": amounts,
        "evidence_ids": [_det_id("ev", raw_event_id)],
        "parser_name": "tax_foreclosure_auction",
        "parser_version": "1.0.0",
        "parser_confidence": aar.get("parser_confidence", 90),
        "captured_at": aar.get("source_fetched_at") or fetched_at,
    }


def evidence_for_event(raw_event: dict) -> dict:
    return {
        "evidence_id": raw_event["evidence_ids"][0],
        "record_id": raw_event["raw_event_id"],
        "field": "tax_foreclosure_event",
        "value": raw_event.get("instrument_number") or "",
        "status": "Confirmed",
        "source_id": EVENT_SOURCE,
        "source_reliability_grade": "C",       # AAR = county-contracted vendor
        "source_url": raw_event.get("source_url") or "",
        "captured_at": raw_event["captured_at"],
    }


# --------------------------------------------------- enrichment_provider ----

def build_enrichment_provider(pm_by_parcel_id: dict):
    """parcel_id → parcel_display dict. The seam attaches this as
    `parcel_display` on the scored_lead and sets enrichment_status =
    ENRICHED. Returns None for unresolved parcel_id → UNENRICHED."""
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
            # Provenance carried IN the parcel_display block: every
            # enrichment value reaching the dashboard is labeled with its
            # origin, distinct from the §17 event-document attribution.
            "owner_source": OWNER_SOURCE,
            "enrichment_source": ENRICHMENT_SOURCE,
        }
    return provider


# ------------------------------------- county-side dashboard projection ----
# Mirrors run_pipeline_staged.project_scored_lead's contract and adds:
# explicit event/owner/enrichment source attribution; a display_owner that
# falls back to parcel_master when §17 is unresolved (with display_owner_
# source labeling it); §17's raw owner placeholder is preserved separately.

_S17_PLACEHOLDER_MARKERS = (
    "unidentified", "unknown", "tax_foreclosure", "review_required",
    "not named", "no party",
)


def _section17_resolved(owner_text: str) -> bool:
    o = (owner_text or "").strip().lower()
    if not o:
        return False
    return not any(m in o for m in _S17_PLACEHOLDER_MARKERS)


_LEAD_ID_DOC_RE = re.compile(r"AAR-\d+-\d+")


def project_lead(scored: dict, *, aar_by_doc: dict, pm_by_pk: dict) -> dict:
    """County-side projection. Attaches parcel_master enrichment via a
    downstream lookup (lead_id → AAR doc_number → tax_map → parcel_master)
    because the framework's §18 leads_base_writer zeros key_parcel_id when
    §17 routes REVIEW_REQUIRED (which IT correctly does, since AAR did not
    name the owner). The seam's enrichment_provider therefore can't be
    called via parcel_id; this projection attaches the enrichment AFTER
    the staged engine returns, with full provenance recorded per row."""
    seam_parcel = scored.get("parcel_display") or {}
    s17_owner = (scored.get("owner_name") or "").strip()
    s17_ok = _section17_resolved(s17_owner)

    # Downstream enrichment lookup: lead_id -> AAR doc_number -> tax_map ->
    # parcel_master. The Tax Map # is the authoritative join the operator named.
    pm_enrich: dict = {}
    join_method = ""
    m = _LEAD_ID_DOC_RE.search(scored.get("lead_id") or "")
    if m:
        aar = aar_by_doc.get(m.group(0))
        if aar:
            tax_map = (aar["raw_payload"].get("tax_map") or "").strip()
            pm_rec = pm_by_pk.get(tax_map) if tax_map else None
            if pm_rec:
                join_method = "print_key"
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
                    "tax_map": tax_map,
                }

    enriched_owner = (pm_enrich.get("owner_name") or seam_parcel.get("owner_name") or "").strip()

    # Display-owner provenance:
    #  - section_17: §17 actually resolved an owner FROM THE AAR DOCUMENT
    #  - parcel_master: §17 unresolved, enrichment supplied owner from the
    #    NYS parcel_master via the PRINT_KEY join (NOT a §17 resolution)
    #  - unresolved: neither source produced an owner
    if s17_ok:
        display_owner = s17_owner
        owner_source = "section_17"
    elif enriched_owner:
        display_owner = enriched_owner
        owner_source = OWNER_SOURCE
    else:
        display_owner = "Unknown"
        owner_source = "unresolved"

    enriched = bool(pm_enrich)
    situs = pm_enrich or seam_parcel
    return {
        "lead_id": scored["lead_id"],
        "scored_lead_id": scored["scored_lead_id"],
        # the operator-asked-for resolved parcel id (from the downstream join):
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
        # seam-level enrichment_status (UNENRICHED because §17→§18 zeroed
        # parcel_id in the aggregation key); the row IS enriched at the
        # dashboard level via the downstream PRINT_KEY join below.
        "seam_enrichment_status": scored.get("enrichment_status"),
        "row_enrichment_status": "ENRICHED" if enriched else "UNENRICHED",
        "row_enrichment_join_method": join_method or "none",
        # explicit attribution — operator-readable, per §13 + operator rules:
        "event_source": EVENT_SOURCE,
        "owner_source": owner_source,
        "enrichment_source": ENRICHMENT_SOURCE if enriched else "none",
    }


def build_payload(scored_leads: list, *, semantic_verdict: str, county: str,
                  state: str, build_label: str, build_label_reason: str,
                  aar_by_doc: dict, pm_by_pk: dict) -> dict:
    rows = [project_lead(s, aar_by_doc=aar_by_doc, pm_by_pk=pm_by_pk)
            for s in scored_leads]
    pat = Counter(); attr = Counter(); sdd = Counter()
    sti = Counter(); dpd = Counter()
    for s in scored_leads:
        for p in s.get("display_patterns") or []:
            pat[p] += 1
        for a in s.get("attributes") or []:
            attr[a] += 1
        sdd[str(s.get("stack_depth", 0))] += 1
        sti[s.get("tier", "Archive")] += 1
        for dp in s.get("deal_paths") or []:
            dpd[dp.get("path") or ""] += 1
    return {
        "generated_at": _now_iso(),
        "build_label": build_label,
        "build_label_reason": build_label_reason,
        "mode": "production",
        "county": county, "state": state,
        "semantic_verdict": semantic_verdict,
        "lead_total": len(scored_leads),
        "event_source": EVENT_SOURCE,
        "owner_source_policy": (
            f"Owner is ATTACHED downstream as enrichment from {OWNER_SOURCE} "
            "via the v5.4.0 seam (R3-iii / §13.14). §17 keeps its honest "
            "owner-unresolved routing when the AAR event document did not "
            "name the owner; that routing is NEVER relabeled. The dashboard "
            "row carries display_owner_source per lead so the provenance is "
            "always visible."
        ),
        "enrichment_breakdown": {
            # row-level enrichment from the downstream PRINT_KEY join — the
            # operator-meaningful count. Seam-level is reported separately.
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
    aar_path = REPO_ROOT / "data" / "raw" / "tax_foreclosure_auction.jsonl"
    pm_path = REPO_ROOT / "data" / "raw" / "parcel_master.jsonl"
    workdir = REPO_ROOT / "data" / "production"
    workdir.mkdir(parents=True, exist_ok=True)
    fetched_at = _now_iso()

    aar = _load_jsonl(aar_path)
    pm = _load_jsonl(pm_path)
    pm_by_pk = {p["raw_payload"]["print_key"]: p["raw_payload"]
                for p in pm if p["raw_payload"].get("print_key")}
    pm_by_parcel_id = {p["raw_payload"]["parcel_id"]: p["raw_payload"]
                       for p in pm if p["raw_payload"].get("parcel_id")}

    hits = [a for a in aar if a["raw_payload"].get("tax_map") in pm_by_pk]
    misses = [a for a in aar if a["raw_payload"].get("tax_map") not in pm_by_pk]
    print(f"AAR lots: {len(aar)}  parcel_master: {len(pm)}")
    print(f"PRINT_KEY join: {len(hits)} hit / {len(misses)} miss")

    raw_events = [aar_to_raw_event(a, pm_by_pk, fetched_at) for a in aar]
    evidence_entries = [evidence_for_event(r) for r in raw_events]
    parcel_id_resolved = sum(1 for r in raw_events
                             if r["property_refs"]["parcel_id"])
    print(f"raw_events: {len(raw_events)}  "
          f"parcel_id resolved: {parcel_id_resolved}")

    enrichment_provider = build_enrichment_provider(pm_by_parcel_id)

    result = run_pipeline_staged.run_staged_pipeline(
        raw_events,
        evidence_entries=evidence_entries,
        signal_type_labels={"tax_foreclosure_notice": "Tax Foreclosure Notice"},
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
    payload = build_payload(
        result["scored_leads"],
        semantic_verdict=result["semantic_verdict"],
        county="Greene County", state="NY",
        build_label="SOURCE_LIMITED",
        build_label_reason=(
            "Only one primary event source is live (AAR tax-foreclosure "
            "auction). Clerk + court primaries remain Cloudflare-gated "
            "and require an operator-seeded session to ingest."
        ),
        aar_by_doc=aar_by_doc, pm_by_pk=pm_by_pk,
    )

    # Write dashboard payload to canonical locations.
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
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )

    # Operator stats
    owner_attached = sum(1 for r in payload["records"]
                         if r["owner_source"] == OWNER_SOURCE)
    s17_resolved = sum(1 for r in payload["records"]
                       if r["owner_source"] == "section_17")
    still_rq = sum(1 for r in payload["records"]
                   if r["display_lead_status"] == "REVIEW_REQUIRED")
    enriched_count = payload["enrichment_breakdown"]["ENRICHED"]

    print()
    print(f"lead_total: {payload['lead_total']}")
    print(f"enrichment_breakdown: {payload['enrichment_breakdown']}")
    print(f"owner attached from parcel_master: {owner_attached}")
    print(f"owner from §17 (event-document): {s17_resolved}")
    print(f"still REVIEW_REQUIRED (§17 honest): {still_rq}")
    print(f"unmatched lots (no PRINT_KEY hit): {len(misses)}")
    for m in misses[:10]:
        print(f"  miss: {m['raw_payload'].get('doc_number')} "
              f"tax_map={m['raw_payload'].get('tax_map')!r}")
    print(f"\nwrote dashboard.json → {out_main}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
