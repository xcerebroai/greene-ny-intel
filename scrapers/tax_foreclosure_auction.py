"""Greene County, NY — AAR tax-foreclosure auction adapter (PRIMARY EVENT SOURCE).

Source : Absolute Auctions & Realty / NYSauctions.com
Portal : https://aarauctions.com/auctions/tax-foreclosures/
         https://aarauctions.com/servlet/Search.do?auctionId=<N>
Role   : PRIMARY_LEAD_SOURCE / PRIMARY_EVENT_SOURCE (§13.2). The annual
         RPTL Article 11 in-rem tax-foreclosure DISPOSITION event for
         Greene County. Lead rows ORIGINATE here.

Access (recon-confirmed 2026-05-23)
-----------------------------------
nginx + WordPress + a Java servlet catalog at /servlet/Search.do.
HTTP 200, no Cloudflare, no cf-mitigated, no CAPTCHA, no session.
Server-rendered HTML — all lot data lives in the raw response, not
JS-injected. Stdlib-reachable end-to-end (urllib + re).

Greene auctions are SEASONAL. The known dataset is auctionId=6892
(Oct 29, 2025, 51 lots). The 2026 Greene auction has not yet been
published — discovery on /auctions/tax-foreclosures/ + /upcoming-
auctions/ + /?s=Greene returns ZERO Greene matches today. The default
mode therefore emits zero rows and exits 2 (seasonal-zero, not an
error). Pass --auction-id N to pull a specific (historical or current)
Greene auction.

Lot HTML shape (per recon)
--------------------------
Each lot title bar:
    #<N> – <address>, [Village of X,] Town of Y
followed by a card carrying:
    Current Bid: $... [Closed | Active]
    <property description>
    Tax Map #: <SBL>
    Lot Size: <acres> Acre
    School District: <CSD>
    Full Market Value: $<value>
    Inspection: <note>
    School Tax Due: $<amt>
    Village Tax Due: $<amt>
    County Tax Due: $<amt>

**AAR does NOT expose owner-of-record per lot.** Owner is recovered
downstream by the matcher joining the AAR record (by Tax Map # / address)
to the parcel_master enrichment layer (NYS_Tax_Parcels_Public PRIMARY_OWNER).

Output contract (MASTER_PROMPT §4.32)
-------------------------------------
data/raw/tax_foreclosure_auction.jsonl — one wrapped record per lot.

    {
      "raw_record_id":      "tax_foreclosure_auction:AAR-<auctionId>-<lot>",
      "source_id":          "tax_foreclosure_auction",
      "source_url":         "https://aarauctions.com/servlet/Search.do?auctionId=<N>",
      "source_fetched_at":  "<ISO-8601 UTC Z>",
      "parser_confidence":  90,
      "raw_payload": {
          # canonical field names consumed by the foreclosure_notices
          # translator (no field_map needed):
          "address":          "<situs, uppercase, address portion only>",
          "city":             "<TOWN_NAME uppercase, 'Town of ' stripped>",
          "zip":              "",                # AAR does not expose ZIP
          "doc_number":       "AAR-<auctionId>-<lot>",
          "recording_year":   <int>,             # auction year
          "recording_month":  <int>,             # auction month
          "layer_id":         0,                 # → layer_doc_type_map["0"]
          # AAR-specific reference fields the translator carries forward:
          "raw_doc_type":     "TAX_SALE_AUCTION_LOT",
          "tax_map":          "<SBL>",
          "lot_number":       <int>,
          "auction_id":       <int>,
          "auction_date":     "YYYY-MM-DD",
          "village":          "<VILLAGE or empty>",
          "full_market_value":<int or None>,
          "current_bid":      <int or None>,
          "bid_status":       "<Closed | Active | Pending | "">",
          "school_district":  "<CSD>",
          "lot_size":         "<acres string>",
          "school_tax_due":   <float or None>,
          "village_tax_due":  <float or None>,
          "county_tax_due":   <float or None>,
          "inspection":       "<note>",
          "property_description": "<bldg-type, sqft, BR/BA>"
      }
    }

Exit codes
----------
    0  success — N rows written
    2  no Greene auction discovered (seasonal-zero, not an error)
    4  source unreachable / non-200
    1  other parse/IO error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ID = "tax_foreclosure_auction"
BASE = "https://aarauctions.com"
SEARCH = BASE + "/servlet/Search.do"
INDEX_URLS = (
    BASE + "/auctions/tax-foreclosures/",
    BASE + "/upcoming-auctions/",
    BASE + "/?s=Greene",
    BASE + "/auctions/",
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_PER_PAGE = 20
DEFAULT_TIMEOUT = 30
MAX_PAGES = 50  # hard ceiling

_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"],
    start=1,
)}


# ------------------------------------------------------------------ HTTP --

def _fetch(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise urllib.error.HTTPError(
                url, resp.status, "non-200", resp.headers, None
            )
        return resp.read().decode("utf-8", errors="replace")


def _now_iso() -> str:
    return (datetime.now(timezone.utc).isoformat(timespec="seconds")
            .replace("+00:00", "Z"))


# ---------------------------------------------------------- discovery ----

_AUCTION_LINK_RE = re.compile(
    r'href="[^"]*auctionId=(\d+)[^"]*"[^>]*>([^<]{0,200})', re.IGNORECASE
)


def discover_greene_auctions() -> list[dict]:
    """Scan AAR index pages for Greene County auctions.

    Returns a list of {"auction_id": int, "link_text": str, "source_url": str}
    for every auctionId whose surrounding link text mentions Greene (case
    insensitive). Seasonal-zero is the expected result outside the auction
    window — caller treats an empty list as 'no live Greene auction'.
    """
    seen: dict = {}
    for url in INDEX_URLS:
        try:
            html = _fetch(url)
        except Exception:
            continue
        for m in _AUCTION_LINK_RE.finditer(html):
            aid, label = int(m.group(1)), m.group(2)
            # Look in a window around the link for "Greene"
            ctx = html[max(0, m.start() - 400): m.end() + 400]
            if re.search(r"\bgreene\b", ctx, re.IGNORECASE):
                if aid not in seen:
                    seen[aid] = {
                        "auction_id": aid,
                        "link_text": re.sub(r"\s+", " ", label).strip(),
                        "source_url": url,
                    }
    return list(seen.values())


# ---------------------------------------------------------- HTML parse ---

_TITLE_RE = re.compile(
    # title bar: #N – address, [Village of X,] Town of Y    (& Village/City variants)
    r'#(\d+)\s*(?:&#8211;|–|-)\s*([^<]+?)(?=<|More\s+Info)',
    re.IGNORECASE,
)
_TAXMAP_RE = re.compile(
    # Tax Map # uses the standard bold-label pattern. The terminator is
    # the next `<` (handles malformed AAR markup that drops `</td>`).
    r'<b>\s*Tax\s*Map\s*#\s*:\s*</b>\s*([^<]+)',
    re.IGNORECASE,
)
# Two field-label patterns are in play:
#   A — `<b>Label:</b> value</td>`           (Full Market Value, Lot Size,
#                                              School District, Inspection)
#   B — `<b>Label: $</b>VALUE</td>`          (School / Village / County
#                                              Tax Due — the `:` and `$`
#                                              live INSIDE the bold)
# This template tolerates both: optional `:`/`$` either side of `</b>`,
# and terminator `[^<]*` instead of `</td>` (some cells drop the `>`).
_BOLD_RE_TPL = (
    r'<b>\s*{label}\s*:?\s*\$?\s*</b>\s*\$?\s*([^<]*)'
)
# Current Bid uses a separate <strong>+<span> pattern.
_CURRENT_BID_RE = re.compile(
    r'Current\s*Bid\s*:?\s*</?\s*strong\s*>\s*(?:<span[^>]*>\s*)?'
    r'<strong>\s*\$([0-9,]+)',
    re.IGNORECASE,
)
_BID_STATUS_RE = re.compile(
    r'>\s*(Closed|Sold|Active|Pending|Open|Withdrawn|Canceled)\s*<',
    re.IGNORECASE,
)
_DATE_HEADER_RE = re.compile(
    r"((?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s*(\d{4}))"
)
_TOTAL_LOTS_RE = re.compile(
    r"All\s*Items\s*\((\d+)\)", re.IGNORECASE
)


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s)


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _parse_money(s: str) -> Optional[int]:
    if not s:
        return None
    m = re.search(r"([0-9][0-9,]*)(?:\.\d+)?", s)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _parse_money_float(s: str) -> Optional[float]:
    if not s:
        return None
    m = re.search(r"([0-9][0-9,]*(?:\.\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _parse_field(html_window: str, label: str) -> str:
    m = re.search(_BOLD_RE_TPL.format(label=re.escape(label)),
                  html_window, re.IGNORECASE)
    return _norm_ws(m.group(1)) if m else ""


def _split_address_municipality(title_tail: str) -> tuple[str, str, str]:
    """Parse '113/115 N Washington St, Village of Athens, Town of Athens'
    → (address, town, village).  Returns uppercase strings; missing → ""."""
    parts = [p.strip() for p in re.split(r",", title_tail) if p.strip()]
    if not parts:
        return "", "", ""
    address = parts[0]
    town = ""
    village = ""
    for p in parts[1:]:
        pu = p.upper()
        if pu.startswith("TOWN OF "):
            town = pu[len("TOWN OF "):].strip()
        elif pu.startswith("VILLAGE OF "):
            village = pu[len("VILLAGE OF "):].strip()
        elif pu.startswith("CITY OF "):
            town = town or pu[len("CITY OF "):].strip()
    return _norm_ws(address).upper(), town, village


def _extract_auction_date(html: str) -> Optional[date]:
    m = _DATE_HEADER_RE.search(html)
    if not m:
        return None
    month_name, day, year = m.group(1).split()[0], m.group(2), m.group(3)
    mi = _MONTHS.get(month_name)
    if not mi:
        return None
    try:
        return date(int(year), mi, int(day.rstrip(",")))
    except ValueError:
        return None


def _split_into_lot_blocks(html: str) -> list[tuple[int, str, str]]:
    """Slice the page HTML at title-bar boundaries. AAR repeats each lot's
    title bar (summary + detail), so a lot's block must run from its FIRST
    occurrence to the FIRST occurrence of the NEXT lot number — not to the
    next regex match (that would clip the block before its Tax Map card).
    Returns list of (lot_number, title_tail, block_html)."""
    matches = list(_TITLE_RE.finditer(html))
    if not matches:
        return []
    seen: dict = {}
    order: list = []
    for m in matches:
        lot = int(m.group(1))
        if lot not in seen:
            seen[lot] = (m.start(), _norm_ws(m.group(2)))
            order.append(lot)
    out: list = []
    for i, lot in enumerate(order):
        start, title_tail = seen[lot]
        end = seen[order[i + 1]][0] if i + 1 < len(order) else len(html)
        out.append((lot, title_tail, html[start:end]))
    return out


def parse_auction_page(html: str, *, auction_id: int,
                       auction_date: Optional[date]) -> list[dict]:
    """Parse one auctionId page into per-lot raw_payload dicts (canonical
    fields). Lots that lack a Tax Map # are skipped (page non-lot blocks)."""
    out: list = []
    for lot, title_tail, block in _split_into_lot_blocks(html):
        tm_match = _TAXMAP_RE.search(block)
        if not tm_match:
            continue
        tax_map = _norm_ws(tm_match.group(1))
        address, town, village = _split_address_municipality(title_tail)
        if not address:
            continue
        full_market = _parse_money(_parse_field(block, "Full Market Value"))
        school_district = _parse_field(block, "School District")
        lot_size = _parse_field(block, "Lot Size")
        inspection = _parse_field(block, "Inspection")
        school_tax = _parse_money_float(_parse_field(block, "School Tax Due"))
        village_tax = _parse_money_float(_parse_field(block, "Village Tax Due"))
        county_tax = _parse_money_float(_parse_field(block, "County Tax Due"))

        bid_match = _CURRENT_BID_RE.search(block)
        current_bid = _parse_money(bid_match.group(1)) if bid_match else None
        # Status (`Closed` / `Active` / `Sold` …) lives in its own tag near
        # the bid amount. Look from the bid match forward in the block.
        status_window = block[bid_match.end():] if bid_match else ""
        status_match = _BID_STATUS_RE.search(status_window[:600])
        bid_status = status_match.group(1) if status_match else ""

        # Property description = text between Current Bid line and Tax Map.
        desc = ""
        cb_end = bid_match.end() if bid_match else 0
        tm_start = tm_match.start()
        if cb_end and tm_start > cb_end:
            desc_raw = _strip_tags(block[cb_end:tm_start])
            desc_raw = re.sub(r"More\s+Details|More\s+Info\s*/?\s*Bid|"
                              r"Track\s+Item|Bid\s+Now", " ", desc_raw,
                              flags=re.IGNORECASE)
            desc = _norm_ws(desc_raw)[:400]

        ad = auction_date
        payload = {
            # canonical foreclosure_notices fields
            "address": address,
            "city": town,           # accepted_municipalities check key
            "zip": "",
            "doc_number": f"AAR-{auction_id}-{lot}",
            "recording_year": ad.year if ad else None,
            "recording_month": ad.month if ad else None,
            "layer_id": 0,
            # AAR-specific (carry-forward)
            "raw_doc_type": "TAX_SALE_AUCTION_LOT",
            "tax_map": tax_map,
            "lot_number": lot,
            "auction_id": auction_id,
            "auction_date": ad.isoformat() if ad else None,
            "village": village,
            "full_market_value": full_market,
            "current_bid": current_bid,
            "bid_status": bid_status,
            "school_district": school_district,
            "lot_size": lot_size,
            "school_tax_due": school_tax,
            "village_tax_due": village_tax,
            "county_tax_due": county_tax,
            "inspection": inspection,
            "property_description": desc,
        }
        out.append(payload)
    return out


# ---------------------------------------------------------------- run ----

def pull_auction(auction_id: int, *, per_page: int = DEFAULT_PER_PAGE,
                 fetch_fn=None) -> dict:
    """Pull every page of one auctionId. Returns
        {"auction_id", "auction_date", "total_lots_advertised", "lots": [..]}.
    `fetch_fn` is injectable for offline tests (URL → HTML string)."""
    fetch = fetch_fn or _fetch
    page = 1
    lots_total: list = []
    auction_date: Optional[date] = None
    advertised_total: Optional[int] = None
    url_first = ""
    while page <= MAX_PAGES:
        url = (f"{SEARCH}?auctionId={auction_id}"
               f"&page={page}&perPage={per_page}&orderBy=")
        html = fetch(url)
        if page == 1:
            url_first = url
            auction_date = _extract_auction_date(html)
            tot = _TOTAL_LOTS_RE.search(html)
            advertised_total = int(tot.group(1)) if tot else None
        page_lots = parse_auction_page(
            html, auction_id=auction_id, auction_date=auction_date
        )
        if not page_lots:
            break
        lots_total.extend(page_lots)
        # Stop early if we've matched the advertised total.
        if advertised_total and len(lots_total) >= advertised_total:
            break
        page += 1
    return {
        "auction_id": auction_id,
        "auction_date": auction_date.isoformat() if auction_date else None,
        "total_lots_advertised": advertised_total,
        "lots": lots_total,
        "first_page_url": url_first,
    }


def _wrap(payload: dict, *, source_url: str, fetched_at: str) -> dict:
    return {
        "raw_record_id": f"{SOURCE_ID}:{payload['doc_number']}",
        "source_id": SOURCE_ID,
        "source_url": source_url,
        "source_fetched_at": fetched_at,
        "parser_confidence": 90,
        "raw_payload": payload,
    }


def _read_existing_jsonl(path: Path) -> list[dict]:
    """Read an existing wrapped-JSONL file. Tolerates missing file / blank lines."""
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def run(*, output_path: Optional[Path] = None,
        auction_id: Optional[int] = None,
        append: bool = False,
        fetch_fn=None) -> dict:
    """Pull a Greene County AAR tax-foreclosure auction and write the
    wrapped JSONL. If auction_id is None, run discovery first; if discovery
    finds nothing, write an empty JSONL and return stats with
    ``seasonal_zero=True``.

    When ``append=True``, existing rows in ``output_path`` are merged with
    the new pull. Dedupe key is ``raw_record_id`` (auctionId+lot — stable
    across pulls). The merge order is existing-then-new, so a re-pull of
    the same auctionId refreshes its rows (newer entries overwrite older
    ones in the dedupe dict).
    """
    output_path = (output_path
                   or REPO_ROOT / "data" / "raw" / f"{SOURCE_ID}.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stats: dict = {
        "source_id": SOURCE_ID, "portal": BASE,
        "output_path": str(output_path),
        "append": append,
    }

    if auction_id is None:
        discovered = discover_greene_auctions()
        stats["discovery"] = discovered
        if not discovered:
            # Seasonal-zero. Greene auctions run annually; outside that
            # window discovery returns nothing. PRESERVE any existing
            # historical JSONL on disk — the daily-refresh CI needs the
            # last good Greene auction to survive between seasons.
            preserved = (output_path.exists()
                         and output_path.read_text(encoding="utf-8").strip())
            if not preserved:
                output_path.write_text("", encoding="utf-8")
            stats.update({
                "seasonal_zero": True,
                "records_written": 0,
                "preserved_existing": bool(preserved),
                "message": "No live or upcoming Greene auction discovered "
                           "across AAR index pages. Greene auctions are "
                           "seasonal (next likely Sep/Oct). Existing "
                           "JSONL preserved." if preserved else
                           "No live or upcoming Greene auction discovered "
                           "across AAR index pages. Greene auctions are "
                           "seasonal (next likely Sep/Oct).",
            })
            return stats
        auction_id = discovered[0]["auction_id"]

    fetched_at = _now_iso()
    pulled = pull_auction(auction_id, fetch_fn=fetch_fn)
    new_rows = [_wrap(p, source_url=pulled["first_page_url"],
                      fetched_at=fetched_at)
                for p in pulled["lots"]]

    if append:
        existing = _read_existing_jsonl(output_path)
        merged: dict = {}
        for r in existing:
            rid = r.get("raw_record_id")
            if rid:
                merged[rid] = r
        for r in new_rows:
            rid = r.get("raw_record_id")
            if rid:
                merged[rid] = r
        rows = list(merged.values())
        stats["existing_rows_before_merge"] = len(existing)
        stats["new_rows_pulled"] = len(new_rows)
    else:
        rows = new_rows

    tmp = output_path.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(output_path)

    stats.update({
        "auction_id": auction_id,
        "auction_date": pulled["auction_date"],
        "total_lots_advertised": pulled["total_lots_advertised"],
        "records_written": len(rows),
        "first_page_url": pulled["first_page_url"],
        "seasonal_zero": False,
    })
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pull Greene County, NY AAR tax-foreclosure auction lots."
    )
    parser.add_argument("--out", default=None,
                        help="Output JSONL. Default: "
                             "data/raw/tax_foreclosure_auction.jsonl")
    parser.add_argument("--auction-id", type=int, default=None,
                        help="AAR auctionId. If omitted, the adapter "
                             "discovers Greene auctions from AAR index "
                             "pages; absent → seasonal-zero, exit 2.")
    parser.add_argument("--append", action="store_true",
                        help="Merge new pull with existing JSONL (dedupe "
                             "by raw_record_id). Use for historical "
                             "backfill across multiple auctionIds.")
    args = parser.parse_args()
    try:
        stats = run(output_path=Path(args.out) if args.out else None,
                    auction_id=args.auction_id,
                    append=args.append)
    except urllib.error.URLError as exc:
        print(json.dumps({"source_id": SOURCE_ID, "status": "BLOCKED",
                          "error": str(exc)}, indent=2), file=sys.stderr)
        return 4
    print(json.dumps(stats, indent=2))
    if stats.get("seasonal_zero"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
