"""Greene County, NY — Column legal-notices adapter (PRIMARY EVENT SOURCE).

Column (column.us / newyork.column.us) is the public-notice publishing
network used by NY newspapers for statutory legal notices: mortgage
foreclosure sale notices, sheriff sales, tax sales, estate/probate
notices, lis pendens, etc.

API (recon, 2026-05-25):
  POST https://us-central1-enotice-production.cloudfunctions.net/api/search/public-notices
  Content-Type: application/json
  Body: {"search":"<keyword>", "allFilters":[{"publishedtimestamp":{"from":<ms>,"to":<ms>}},
         {"state":["New York"]}, {"county":["Greene"]}],
         "noneFilters":[], "sort":[{"publishedtimestamp":"desc"}],
         "pageSize":N, "isDemo":false}
  Headers: content-type:application/json; origin/referer:newyork.column.us

Important caveat — Column's `county` field is the PUBLISHING-county
(the county of the newspaper that printed the notice), NOT the
property's county. A Greene-property foreclosure can be advertised in
a regional paper based in Ulster, Albany, or Columbia. This adapter
queries SEVERAL likely publishing counties and filters on TEXT
CONTENT for Greene-property markers (Greene town names appearing in
the notice body) before emitting a record.

Per the Duval-lesson rule, every emitted row must show property
attachment in the raw text. Notices that mention Greene only as a
publisher but have no Greene-property reference are filtered out.

Stage boundary: this is a PRIMARY EVENT SOURCE per §13.2 — each
distress notice (foreclosure sale, sheriff sale, tax sale, lis pendens,
estate, probate, lien) is a recorded distress event. NYS parcel_master
remains ENRICHMENT, never originates a lead.

Output (§4.32): data/raw/legal_notices_column.jsonl.

Exit codes: 0 records found · 2 no records (no live Greene-property
notices in the window — legitimate-zero, not error) · 4 source
unreachable · 1 other.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "legal_notices_column"
API_URL = ("https://us-central1-enotice-production.cloudfunctions.net/"
           "api/search/public-notices")
USER_AGENT = "xcerebro-greene-ny-column/0.1"

# Counties whose newspapers publish Greene-relevant notices.
PUBLISHING_COUNTIES = [
    "Greene", "Albany", "Ulster", "Columbia", "Delaware", "Schoharie",
    "Rensselaer", "Schenectady",
]

# Greene County town / village names — checked case-insensitively in the
# notice body to confirm property attachment.
GREENE_PLACES = [
    "Ashland", "Athens", "Cairo", "Catskill", "Coxsackie", "Durham",
    "Greenville", "Halcott", "Hunter", "Jewett", "Lexington",
    "New Baltimore", "Prattsville", "Windham", "Tannersville",
    "Leeds", "Palenville", "Round Top", "Cornwallville", "East Durham",
    "Freehold", "Haines Falls", "West Coxsackie", "Cementon", "Earlton",
    "Climax", "Surprise", "Acra", "Oak Hill", "Medusa", "Purling",
    "Hensonville", "Maplecrest", "Elka Park", "South Cairo",
]

# Distress keywords by canonical type. Each notice gets classified by the
# first matching pattern. Duval-lesson: only emit lead-generating canonical
# types when the text demonstrates property attachment (address / SBL /
# tax map / parcel id / legal description).
DISTRESS_PATTERNS = [
    ("NOTICE_OF_SALE", re.compile(
        r"\bNOTICE\s+OF\s+SALE\b|\bSHERIFF[' ]?S?\s+SALE\b|"
        r"\bMORTGAGE\s+FORECLOSURE\s+SALE\b|\bREFEREE[' ]?S?\s+SALE\b",
        re.IGNORECASE)),
    ("LIS_PENDENS", re.compile(
        r"\bLIS\s+PENDENS\b|\bNOTICE\s+OF\s+PENDENCY\b",
        re.IGNORECASE)),
    ("TAX_FORECLOSURE_NOTICE", re.compile(
        r"\bTAX\s+(?:LIEN|SALE|FORECLOSURE)\b|\bIN\s+REM\s+TAX\b",
        re.IGNORECASE)),
    ("FINAL_JUDGMENT_OF_FORECLOSURE", re.compile(
        r"\bFINAL\s+JUDGMENT\s+OF\s+FORECLOSURE\b|"
        r"\bJUDGMENT\s+OF\s+FORECLOSURE\s+AND\s+SALE\b",
        re.IGNORECASE)),
    ("LETTERS_TESTAMENTARY", re.compile(
        r"\bLETTERS\s+TESTAMENTARY\b|\bGRANT\s+OF\s+PROBATE\b",
        re.IGNORECASE)),
    ("LETTERS_OF_ADMINISTRATION", re.compile(
        r"\bLETTERS\s+OF\s+ADMINISTRATION\b", re.IGNORECASE)),
    ("ESTATE_NOTICE", re.compile(
        r"\bSURROGATE[' ]?S?\s+COURT\b|\bESTATE\s+OF\b|"
        r"\bCREDITOR\s+CLAIMS\b|\bNOTICE\s+TO\s+CREDITORS\b",
        re.IGNORECASE)),
    ("MECHANICS_LIEN", re.compile(
        r"\bMECHANIC[' ]?S?\s+LIEN\b", re.IGNORECASE)),
]

# Filter junk: LLC formations, business registrations, election notices —
# these are NOT distress and should not be emitted.
NON_DISTRESS = re.compile(
    r"\bNOTICE\s+OF\s+FORMATION\b|\bARTICLES\s+OF\s+ORGANIZATION\b|"
    r"\bSECRETARY\s+OF\s+STATE\s+OF\s+NEW\s+YORK\b|"
    r"\bASSUMED\s+NAME\b|\bD/B/A\b|"
    r"\bPUBLIC\s+HEARING\b|\bMEETING\s+NOTICE\b|\bELECTION\s+NOTICE\b",
    re.IGNORECASE,
)

# Property-attachment markers — a notice must show at least one of these
# to count as having "property attachment" per the Duval-lesson rule.
PROPERTY_RX = re.compile(
    r"\b\d+\s+[A-Z][a-zA-Z\.\s]+(?:Rd|Road|St|Street|Ave|Avenue|Ln|Lane|"
    r"Dr|Drive|Hwy|Highway|Way|Ct|Court|Blvd|Boulevard|Pl|Place|"
    r"Route|Rt|Pkwy|Parkway|Tr|Trail|Loop|Ter|Terrace|Cir|Circle|"
    r"Sq|Square|Knoll|Park|Pass)\b",
    re.IGNORECASE,
)
TAX_MAP_RX = re.compile(
    r"\bSection\s*\d+|Block\s*\d+|Lot\s*\d+|"
    r"\b\d{1,3}\.\d+-\d+(?:-\d+(?:\.\d+)?)?\b|\bSBL[#:\s]\s*[\d\.\-]+",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _search(*, keyword: str, publishing_county: str, days_back: int,
            page_size: int) -> list[dict]:
    now_ms = int(time.time() * 1000)
    body = {
        "search": keyword,
        "allFilters": [
            {"publishedtimestamp": {
                "from": now_ms - days_back * 86400 * 1000, "to": now_ms,
            }},
            {"state": ["New York"]},
            {"county": [publishing_county]},
        ],
        "noneFilters": [],
        "sort": [{"publishedtimestamp": "desc"}],
        "pageSize": page_size,
        "isDemo": False,
    }
    req = urllib.request.Request(
        API_URL, method="POST",
        headers={
            "content-type": "application/json",
            "user-agent": USER_AGENT,
            "origin": "https://newyork.column.us",
            "referer": "https://newyork.column.us/",
        },
        data=json.dumps(body).encode("utf-8"),
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read()).get("results", [])


def _classify(text: str) -> tuple[str | None, str]:
    """Return (canonical_doc_type, signal_label) or (None,'') if non-distress."""
    if NON_DISTRESS.search(text):
        return None, ""
    for canonical, rx in DISTRESS_PATTERNS:
        if rx.search(text):
            label = canonical.replace("_", " ").title()
            return canonical, label
    return None, ""


def _greene_property(text: str) -> tuple[bool, list[str]]:
    """Does the notice mention a Greene-county PROPERTY (not just an
    incidentally-shared word like a town name as a defendant)?

    Greene town names appear in unrelated notices as personal names or
    defendant names (e.g. "Lexington" in a Saratoga foreclosure). The
    only reliable property-attachment markers are:
      • Explicit county text: "COUNTY OF GREENE" / "GREENE COUNTY" /
        "GREENE, NEW YORK" / "GREENE, NY".
      • Town name preceded by 'TOWN/VILLAGE/CITY OF' (explicit municipal
        qualifier).
    A bare town name alone is NOT sufficient evidence."""
    matched: list[str] = []
    upper = text.upper()
    if re.search(r"\b(?:COUNTY\s+OF\s+GREENE|GREENE\s+COUNTY|"
                 r"GREENE,?\s+(?:NEW\s+YORK|NY)\b)", upper):
        matched.append("greene_county_named")
    for town in GREENE_PLACES:
        if re.search(r"\b(?:TOWN\s+OF|VILLAGE\s+OF|CITY\s+OF)\s+"
                     + re.escape(town).upper() + r"\b", upper):
            matched.append(f"town_of:{town}")
            break
    return bool(matched), matched


def _property_attachment(text: str) -> tuple[bool, str]:
    """Confirms a parcel attachment via street address or tax-map ref."""
    m = PROPERTY_RX.search(text)
    if m:
        return True, "street_address"
    m = TAX_MAP_RX.search(text)
    if m:
        return True, "tax_map_ref"
    return False, ""


def _wrap(notice: dict, canonical: str, signal_label: str,
          greene_markers: list[str], property_evidence: str,
          fetched_at: str) -> dict:
    nid = notice.get("id") or ""
    return {
        "raw_record_id": f"{SOURCE_ID}:{nid}",
        "source_id": SOURCE_ID,
        "source_url": notice.get("pdfurl") or f"https://newyork.column.us/?id={nid}",
        "source_fetched_at": fetched_at,
        "parser_confidence": 80,
        "raw_payload": {
            "raw_doc_type": canonical,
            "canonical_doc_type_hint": canonical,
            "signal_label": signal_label,
            "instrument_number": nid,
            "recorded_date": datetime.fromtimestamp(
                (notice.get("publishedtimestamp") or 0) / 1000,
                tz=timezone.utc,
            ).date().isoformat() if notice.get("publishedtimestamp") else "",
            "newspaper_name": notice.get("newspapername") or "",
            "publishing_county": notice.get("county") or "",
            "publishing_state": notice.get("state") or "",
            "notice_type": notice.get("noticetype") or "",
            "text": (notice.get("text") or "")[:4000],
            "pdf_url": notice.get("pdfurl") or "",
            "greene_attachment_markers": greene_markers,
            "property_attachment_evidence": property_evidence,
            "filer": notice.get("filer") or "",
        },
    }


def run(*, output_path: Path | None = None, days_back: int = 90,
        page_size: int = 100) -> dict:
    output_path = (output_path
                   or REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fetched_at = _now_iso()

    seen_ids: set = set()
    kept: list[dict] = []
    probed = 0
    by_cty: dict = {}
    skipped: dict = {
        "non_distress": 0,
        "no_greene_attachment": 0,
        "no_property_evidence": 0,
        "duplicate": 0,
    }
    # Two-pass: per publishing county, several distress keywords
    keywords = ["foreclosure", "mortgage", "sheriff sale", "tax sale",
                "lis pendens", "estate", "probate"]
    for pcty in PUBLISHING_COUNTIES:
        per_cty = 0
        for kw in keywords:
            try:
                results = _search(keyword=kw, publishing_county=pcty,
                                  days_back=days_back, page_size=page_size)
            except Exception as e:
                print(f"  search err pcty={pcty} kw={kw}: {e}",
                      file=sys.stderr)
                continue
            probed += len(results)
            for n in results:
                nid = n.get("id")
                if not nid or nid in seen_ids:
                    skipped["duplicate"] += 1
                    continue
                seen_ids.add(nid)
                text = n.get("text") or ""
                ok_greene, markers = _greene_property(text)
                if not ok_greene:
                    skipped["no_greene_attachment"] += 1
                    continue
                canonical, label = _classify(text)
                if not canonical:
                    skipped["non_distress"] += 1
                    continue
                ok_prop, prop_evidence = _property_attachment(text)
                if not ok_prop:
                    skipped["no_property_evidence"] += 1
                    continue
                kept.append(_wrap(n, canonical, label, markers, prop_evidence,
                                  fetched_at))
                per_cty += 1
        by_cty[pcty] = per_cty
    # Write
    tmp = output_path.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(output_path)
    return {
        "source_id": SOURCE_ID, "api_url": API_URL,
        "days_back": days_back, "probed_results": probed,
        "records_written": len(kept), "by_publishing_county": by_cty,
        "skipped_breakdown": skipped, "output_path": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pull Greene-property distress notices from Column."
    )
    parser.add_argument("--out", default=None)
    parser.add_argument("--days-back", type=int, default=90)
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    try:
        stats = run(
            output_path=Path(args.out) if args.out else None,
            days_back=args.days_back, page_size=args.page_size,
        )
    except urllib.error.URLError as e:
        print(json.dumps({"status": "BLOCKED", "error": str(e)},
                         indent=2), file=sys.stderr)
        return 4
    print(json.dumps(stats, indent=2))
    return 0 if stats["records_written"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
