"""Greene County, NY — Treasurer Annual Petition & Notice of Foreclosure adapter
(PRIMARY EVENT SOURCE; RPTL Article 11 in-rem tax-foreclosure proceeding).

Source : Greene County Treasurer
URL    : https://greenecountyny.gov/departments/treasurer/ — links the
         Annual Petition PDF, e.g.
         /wp-content/uploads/2025/04/2025-Petition-and-Notice-of-Forclosure.pdf
Format : scanned image PDF (CCITT fax), 29 pages for 2025. The petition is a
         court filing (Greene County Court, Index No. captioned on page 1)
         that lists every parcel under in-rem tax foreclosure with owner,
         address, SBL, tax years, and amounts owed. This is the PRE-AUCTION
         distress event — different (and earlier in the lifecycle) from the
         AAR auction-disposition records.

Pipeline (stdlib + pdftoppm + tesseract, both required to be on PATH):
  PDF  → pdftoppm -png -r 200      → page-N.png (per page)
       → tesseract --psm 6         → page-N.txt (per page)
       → concat                     → petition_full.txt
       → regex per parcel row       → wrapped §4.32 raw records

Row shape we OCR (verified against the 2025 petition):
    <SBL> <YEAR> County/Town <OWNER NAME>, <ADDRESS> $<face> $<gross> $<int> $<total>

Multiple years per SBL collapse into ONE event record (the in-rem petition
is one event per parcel; the year-by-year amounts add up to total owed).

Stage boundary: this is a PRIMARY EVENT SOURCE per §13.2 (court-filed tax
distress event with property attachment). The Duval-lesson rule is honored:
every emitted row carries a Tax Map # (SBL) — the join key to NYS
parcel_master enrichment. AAR remains a separate primary source for the
auction-disposition stage.

Output (§4.32): data/raw/tax_foreclosure_petition.jsonl, one wrapped record
per parcel-petition entry.

Exit codes: 0 success · 2 no parcels parsed (OCR yielded nothing) · 4
source unreachable · 1 other.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "tax_foreclosure_petition"
DEFAULT_PETITION_URL = (
    "https://greenecountyny.gov/wp-content/uploads/2025/04/"
    "2025-Petition-and-Notice-of-Forclosure.pdf"
)
USER_AGENT = "xcerebro-greene-ny-treasurer-petition/0.1"

# Parse the per-parcel OCR row. SBLs in the 2025 petition take forms like
# "58.00-4-38" or "58.00-5-10.1". OCR can drop or substitute punctuation;
# the regex tolerates extra/missing spaces and the leading "_" that
# tesseract sometimes emits between columns.
_ROW = re.compile(
    r"""^
    \s*
    (?P<sbl>\d{1,3}(?:\.\d+)?-\d+(?:\.\d+)?-\d+(?:\.\d+)?)   # SBL/PRINT_KEY
    \s+
    (?P<year>\d{4})                                          # tax year
    \s+
    (?P<fund>(?:County(?:/Town|/Vill|/Sch)?|Town|Village|School|Special)
        [A-Za-z/]*)                                          # fund label
    [\s_—\-]+
    (?P<rest>.+?)                                            # owner + addr + amounts
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)
_AMOUNT = re.compile(r"\$[\s]?[\d,]+(?:\.\d{2})?")


def _now_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


def _money_to_float(s: str | None):
    if not s:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- download

def download_petition(url: str, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        dst.write_bytes(resp.read())
    return dst


# ---------------------------------------------------------- OCR pipeline

def render_and_ocr(pdf: Path, workdir: Path) -> Path:
    """pdftoppm → PNG per page → tesseract → TXT per page → concat.
    Returns the full-text concatenation path."""
    workdir.mkdir(parents=True, exist_ok=True)
    prefix = workdir / "p"

    # Render: only if no PNGs yet
    if not list(workdir.glob("p-*.png")):
        subprocess.run(
            ["pdftoppm", "-png", "-r", "200", str(pdf), str(prefix)],
            check=True,
        )
    # OCR each page
    for png in sorted(workdir.glob("p-*.png")):
        txt = png.with_suffix(".txt")
        if txt.exists() and txt.stat().st_size > 0:
            continue
        subprocess.run(
            ["tesseract", str(png), str(png.with_suffix("")),
             "--psm", "6", "-l", "eng"],
            check=True, stderr=subprocess.DEVNULL,
        )
    # Concat
    full = workdir / "petition_full.txt"
    pages = sorted(workdir.glob("p-*.txt"))
    full.write_text(
        "".join(p.read_text(encoding="utf-8", errors="replace")
                for p in pages),
        encoding="utf-8",
    )
    return full


# ---------------------------------------------------------------- parse

def parse_row(line: str) -> dict | None:
    m = _ROW.match(line)
    if not m:
        return None
    sbl = m.group("sbl").strip()
    year = int(m.group("year"))
    fund = m.group("fund").strip()
    rest = m.group("rest").strip()
    # Pull amounts from the right.
    amounts = _AMOUNT.findall(rest)
    if not amounts:
        return None
    # Strip amounts off the right
    left = _AMOUNT.split(rest)[0].rstrip(" $")
    # Owner + address — split at the LAST comma; OCR can also produce a
    # second comma if owner has co-owners ("Argenziano Richard, Linda
    # Argenziano-Curcio"). Take the last comma that's followed by digits
    # OR by an address-keyword.
    addr = ""; owner = left
    addr_match = re.search(
        r",\s+(\d+[\w\s\.\-/]+|"
        r"P\.?O\.?\s*Box\s+\d+|"
        r"[A-Z][a-zA-Z]+\s+(?:Rd|Road|St|Street|Ave|Avenue|Ln|Lane|"
        r"Dr|Drive|Hwy|Highway|Way|Ct|Court|Cir|Circle|Blvd|Boulevard|"
        r"Pl|Place|Tr|Trail|Loop|Ter|Terrace|Pkwy|Parkway|Trace|Trk|"
        r"Route|Rt|Square|Sq|Knoll|Park|Pass))",
        left,
    )
    if addr_match:
        owner = left[:addr_match.start()].rstrip(", ")
        addr = left[addr_match.start() + 1:].lstrip().strip()
    # Total = last $ amount on the row
    total = _money_to_float(amounts[-1])
    face = _money_to_float(amounts[0]) if amounts else None
    return {
        "sbl": sbl, "year": year, "fund": fund,
        "owner_raw": owner, "address_raw": addr,
        "face_amount": face, "total_amount": total,
    }


def parse_full_text(text: str) -> list[dict]:
    rows: list[dict] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        r = parse_row(line)
        if r:
            rows.append(r)
    return rows


# ------------------------------------------------- collapse to one per SBL

def collapse_by_sbl(rows: list[dict]) -> list[dict]:
    """Multi-year rows on the same SBL → one record per parcel; aggregate
    tax_years, sum total_amount, retain first-seen owner+address."""
    by_sbl: dict = {}
    for r in rows:
        key = r["sbl"]
        if key not in by_sbl:
            by_sbl[key] = {
                "sbl": key, "owner_name": r["owner_raw"],
                "address": r["address_raw"], "tax_years": [],
                "fund_breakdown": [], "total_owed": 0.0,
                "face_total": 0.0,
            }
        rec = by_sbl[key]
        if r["year"] not in rec["tax_years"]:
            rec["tax_years"].append(r["year"])
        rec["fund_breakdown"].append({
            "year": r["year"], "fund": r["fund"],
            "face": r["face_amount"], "total": r["total_amount"],
        })
        if r["total_amount"]:
            rec["total_owed"] += r["total_amount"]
        if r["face_amount"]:
            rec["face_total"] += r["face_amount"]
        # Prefer the non-empty owner / address
        if not rec["owner_name"] and r["owner_raw"]:
            rec["owner_name"] = r["owner_raw"]
        if not rec["address"] and r["address_raw"]:
            rec["address"] = r["address_raw"]
    # Sort tax_years asc per record
    for rec in by_sbl.values():
        rec["tax_years"].sort()
    return list(by_sbl.values())


# ---------------------------------------------------------------- emit

def to_wrapped(rec: dict, *, source_url: str, fetched_at: str,
               recorded_date: str) -> dict:
    sbl = rec["sbl"]
    return {
        "raw_record_id": f"{SOURCE_ID}:{sbl}",
        "source_id": SOURCE_ID,
        "source_url": source_url,
        "source_fetched_at": fetched_at,
        "parser_confidence": 75,   # OCR — moderate confidence
        "raw_payload": {
            "tax_map": sbl,
            "owner_name_raw": rec["owner_name"],
            "address_raw": rec["address"],
            "tax_years": rec["tax_years"],
            "fund_breakdown": rec["fund_breakdown"],
            "total_owed": round(rec["total_owed"], 2) if rec["total_owed"] else None,
            "face_total": round(rec["face_total"], 2) if rec["face_total"] else None,
            "raw_doc_type": "TAX_FORECLOSURE_PETITION",
            "instrument_number": f"TX-PETITION-{sbl}",
            "recorded_date": recorded_date,
        },
    }


# ---------------------------------------------------------------- main

def run(*, output_path: Path | None = None, petition_url: str = DEFAULT_PETITION_URL,
        petition_year: int = 2025) -> dict:
    output_path = (output_path
                   or REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl")
    workdir = REPO_ROOT / "data" / "raw" / "_workdir"
    workdir.mkdir(parents=True, exist_ok=True)
    pdf = workdir / "petition.pdf"
    if not pdf.exists() or pdf.stat().st_size < 1000:
        download_petition(petition_url, pdf)
    full_text = render_and_ocr(pdf, workdir)
    rows = parse_full_text(full_text.read_text(encoding="utf-8", errors="replace"))
    parcels = collapse_by_sbl(rows)

    fetched_at = _now_iso()
    # Petition filed early in the petition_year; we don't have the exact
    # date on every page, but the petition is officially captioned/filed
    # in 02-Feb of the petition year (RPTL Art. 11 timeline).
    recorded_date = f"{petition_year}-02-27"
    wrapped = [
        to_wrapped(p, source_url=petition_url, fetched_at=fetched_at,
                   recorded_date=recorded_date)
        for p in parcels if p["sbl"]
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in wrapped:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(output_path)

    by_year = {}
    for p in parcels:
        for y in p["tax_years"]:
            by_year[y] = by_year.get(y, 0) + 1

    return {
        "source_id": SOURCE_ID, "petition_url": petition_url,
        "petition_year": petition_year, "ocr_lines": len(rows),
        "parcels": len(parcels), "records_written": len(wrapped),
        "year_distribution": dict(sorted(by_year.items())),
        "output_path": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pull + OCR + parse the Greene County Treasurer's "
                    "Annual Petition & Notice of Foreclosure (PRIMARY tax-"
                    "foreclosure event source)."
    )
    parser.add_argument("--out", default=None)
    parser.add_argument("--petition-url", default=DEFAULT_PETITION_URL)
    parser.add_argument("--petition-year", type=int, default=2025)
    args = parser.parse_args()
    try:
        stats = run(
            output_path=Path(args.out) if args.out else None,
            petition_url=args.petition_url, petition_year=args.petition_year,
        )
    except urllib.error.URLError as e:
        print(json.dumps({"status": "BLOCKED", "error": str(e)},
                         indent=2), file=sys.stderr)
        return 4
    print(json.dumps(stats, indent=2))
    return 0 if stats["records_written"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
