"""
Phase 2 fixture test — Greene County parcel_master adapter.

Runs scrapers/parcel_master.py against a captured fixture of the live
NYS GIS Clearinghouse response (no network), and asserts:

  1. the scraper emits the MASTER_PROMPT §4.32 wrapped raw-record shape;
  2. raw_payload carries framework-canonical field names;
  3. source->canonical normalization is correct (spot-checked against
     known fixture values);
  4. the universal parcel_master translator consumes the output and
     produces framework parcel records (the matching-layer contract).

County-scoped Phase 2 build artifact — lives under runs/greene_ny/build/
per §02.13, not in scaffold/tests/ (which is universal).

Run:  python3 runs/greene_ny/build/test_parcel_master.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scrapers.parcel_master as pm  # noqa: E402
from scaffold.pipeline.translators.parcel_master import (  # noqa: E402
    translate_parcel_master,
)

FIXTURE = (REPO_ROOT / "runs" / "greene_ny" / "build" / "fixtures"
           / "parcel_master" / "greene_sample_25.json")

_passes: list = []
_fails: list = []


def check(label: str, ok: bool, detail: str = "") -> None:
    (_passes if ok else _fails).append((label, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}"
          + (f"  --  {detail}" if (detail and not ok) else ""))


def fixture_fetch_fn(fixture: dict):
    """Injectable fetch_fn: page 1 -> fixture; later pages -> empty."""
    def _fetch(url: str, params: dict) -> dict:
        if int(params.get("resultOffset", 0) or 0) == 0:
            return fixture
        return {"features": []}
    return _fetch


def main() -> int:
    if not FIXTURE.exists():
        print(f"[FAIL] fixture missing: {FIXTURE}")
        return 1
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected_n = len(fixture.get("features", []))

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "parcel_master.jsonl"
        stats = pm.run(output_path=out, fetch_fn=fixture_fetch_fn(fixture))
        records = [json.loads(ln) for ln in
                   out.read_text(encoding="utf-8").splitlines() if ln.strip()]

    print(f"scraper stats: {json.dumps(stats)}")

    # 1 — record count
    check(f"scraper wrote all {expected_n} fixture parcels",
          len(records) == expected_n,
          f"got {len(records)}")

    # 2 — §4.32 wrapped shape on every record
    wrap_keys = {"raw_record_id", "source_id", "source_url",
                 "source_fetched_at", "parser_confidence", "raw_payload"}
    shape_ok = all(wrap_keys.issubset(r) for r in records)
    check("every record has the §4.32 wrapped shape", shape_ok)
    check("source_id is 'parcel_master' on every record",
          all(r.get("source_id") == "parcel_master" for r in records))
    check("parser_confidence is an int on every record",
          all(isinstance(r.get("parser_confidence"), int) for r in records))
    check("source_url is a real NYS query deep-link",
          all("gisservices.its.ny.gov" in r.get("source_url", "")
              for r in records))

    # 3 — canonical raw_payload field names present
    canon = {"parcel_id", "address", "owner_name", "owner_mailing_address",
             "owner_mailing_city", "owner_mailing_state", "owner_mailing_zip",
             "city", "zip", "assessed_value", "land_value",
             "improvement_value", "year_built", "property_use", "acres",
             "legal_description"}
    payload_ok = all(canon.issubset(r["raw_payload"]) for r in records)
    check("raw_payload carries all canonical translator fields", payload_ok)

    # 3b — spot-check normalization against known fixture record 1
    by_oid = {f["attributes"]["OBJECTID"]: f for f in fixture["features"]}
    rec1 = next((r for r in records
                 if r["raw_payload"]["parcel_id"]
                 == pm._parcel_id(by_oid[835967]["attributes"])), None)
    check("fixture OBJECTID 835967 normalized", rec1 is not None)
    if rec1:
        p = rec1["raw_payload"]
        check("  parcel_id == SWIS_SBL_ID",
              p["parcel_id"] == "19200009200000040120000000", p["parcel_id"])
        check("  address uppercased situs",
              p["address"] == "OFF ROUTE 23", p["address"])
        check("  owner_name == PRIMARY_OWNER",
              p["owner_name"] == "Loh, Glenn", p["owner_name"])
        check("  situs city == MUNI_NAME",
              p["city"] == "Ashland", p["city"])
        check("  assessed_value coerced to int",
              p["assessed_value"] == 26000, repr(p["assessed_value"]))
        check("  out-of-state owner mailing preserved (NJ)",
              p["owner_mailing_state"] == "NJ", p["owner_mailing_state"])
        check("  missing YR_BLT -> year_built None",
              p["year_built"] is None, repr(p["year_built"]))

    # 3c — co-owner join (record 2 has ADD_OWNER)
    rec2 = next((r for r in records
                 if r["raw_payload"]["parcel_id"]
                 == pm._parcel_id(by_oid[835968]["attributes"])), None)
    if rec2:
        check("co-owner folded into owner_name",
              rec2["raw_payload"]["owner_name"] == "Kane, John & Kane, Monika",
              rec2["raw_payload"]["owner_name"])

    # 4 — universal translator consumes the output
    signals, parcels, meta = translate_parcel_master(
        records, {"county_id": "greene_ny"}, {"translator": "parcel_master"})
    check("translator emits zero signals (enrichment source)",
          signals == [], f"got {len(signals)}")
    check(f"translator emits {expected_n} parcels",
          len(parcels) == expected_n, f"got {len(parcels)}")
    if parcels:
        pk = parcels[0]
        check("translated parcel has parcel_id + owner_name + address",
              bool(pk.get("parcel_id")) and "owner_name" in pk
              and "address" in pk)
        check("translated parcel carries parcel_master_status",
              pk.get("parcel_master_status") == "matched_pending_join",
              pk.get("parcel_master_status"))

    print(f"\nPASS: {len(_passes)}  FAIL: {len(_fails)}")
    if _fails:
        print("Phase 2 parcel_master fixture test FAILED.")
        return 1
    print("Phase 2 parcel_master fixture test PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
