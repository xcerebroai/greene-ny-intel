"""
Greene County, NY — parcel-master adapter (ENRICHMENT source).

Pulls Greene County parcels from the NYS GIS Clearinghouse statewide
public tax-parcel layer:

    https://gisservices.its.ny.gov/arcgis/rest/services/
        NYS_Tax_Parcels_Public/FeatureServer/1

Layer 1 (`NYS_Tax_Parcels_Public`) carries the full 2024-2025 assessment
attribute set for the 36 NY counties that opted into public sharing.
Greene County is included — `WHERE COUNTY_NAME='Greene'` returns 38,418
parcels (verified 2026-05-21). Layer 0 of the same service is only the
county-footprint layer and is NOT used here.

This source is ENRICHMENT, not lead-generating (county config:
`source_role = ENRICHMENT_SOURCE`, `source_priority = P2`). It produces
parcel/owner/valuation context that the matcher joins onto leads
originated by primary clerk / court / tax sources. It never originates a
lead on its own.

Output contract
---------------
Writes `data/raw/parcel_master.jsonl`, one JSON line per parcel, in the
framework-canonical wrapped raw-record shape (MASTER_PROMPT §4.32). The
`raw_payload` carries framework-canonical lowercase field names, so the
universal `parcel_master` translator consumes it with NO `field_map` —
this scraper does the source->canonical normalization (the §4.32 Path 1
contract: scrapers normalize, translators stay protocol-agnostic).

NYS layer field  ->  framework-canonical raw_payload field
-----------------------------------------------------------
    SWIS_SBL_ID            -> parcel_id        (county-unique parcel key)
    PARCEL_ADDR            -> address          (situs; falls back to
                                                LOC_ST_NBR + LOC_STREET)
    PRIMARY_OWNER (+ADD_OWNER) -> owner_name
    MAIL_ADDR / PO_BOX     -> owner_mailing_address
    MAIL_CITY              -> owner_mailing_city
    MAIL_STATE             -> owner_mailing_state
    MAIL_ZIP               -> owner_mailing_zip
    MUNI_NAME              -> city             (situs town/municipality)
    LOC_ZIP                -> zip
    TOTAL_AV               -> assessed_value
    LAND_AV                -> land_value
    TOTAL_AV - LAND_AV     -> improvement_value (derived; None if either
                                                 missing)
    YR_BLT                 -> year_built
    PROP_CLASS             -> property_use
    ACRES (or CALC_ACRES)  -> acres

Reference-only extras carried in raw_payload (translator ignores them):
    print_key, sbl, swis, county_name, owner_type, add_owner,
    full_market_value, roll_year, used_as_desc.

Known limitation: the NYS public layer carries no exemption columns, so
the canonical `exempt_homestead / exempt_over_65 / exempt_disabled /
exempt_veteran` flags are NOT emitted (the translator treats their
absence as all-False). Exemption data, if needed, is a future per-town
assessment-roll ingest.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scaffold.scrapers._arcgis_featureserver import (  # noqa: E402
    ArcGISFeatureServer,
)

SOURCE_ID = "parcel_master"
SERVICE_URL = (
    "https://gisservices.its.ny.gov/arcgis/rest/services/"
    "NYS_Tax_Parcels_Public/FeatureServer"
)
LAYER_ID = 1
COUNTY_NAME = "Greene"
USER_AGENT = "xcerebro-greene-ny-parcel-master/0.1 (+private repo)"

OUT_FIELDS = (
    "OBJECTID,COUNTY_NAME,MUNI_NAME,SWIS,PARCEL_ADDR,PRINT_KEY,SBL,"
    "SWIS_SBL_ID,LOC_ST_NBR,LOC_STREET,LOC_UNIT,LOC_ZIP,PROP_CLASS,"
    "USED_AS_DESC,LAND_AV,TOTAL_AV,FULL_MARKET_VAL,YR_BLT,ACRES,"
    "CALC_ACRES,PRIMARY_OWNER,ADD_OWNER,OWNER_TYPE,MAIL_ADDR,PO_BOX,"
    "MAIL_CITY,MAIL_STATE,MAIL_ZIP,ROLL_YR"
)


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _s(value) -> str:
    """Coerce a value to a stripped string; None / 'NULL' -> ''."""
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.upper() == "NULL" else text


def _to_int(value):
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _situs_address(a: dict) -> str:
    """Situs address, uppercase canonical. PARCEL_ADDR first; else compose
    from the LOC_* parts."""
    addr = _s(a.get("PARCEL_ADDR"))
    if not addr:
        parts = [_s(a.get("LOC_ST_NBR")), _s(a.get("LOC_STREET")),
                 _s(a.get("LOC_UNIT"))]
        addr = " ".join(p for p in parts if p)
    return " ".join(addr.split()).upper()


def _owner_name(a: dict) -> str:
    primary = _s(a.get("PRIMARY_OWNER"))
    add = _s(a.get("ADD_OWNER"))
    if primary and add:
        return f"{primary} & {add}"
    return primary or add


def _mailing_address(a: dict) -> str:
    mail = _s(a.get("MAIL_ADDR"))
    if mail:
        return mail
    box = _s(a.get("PO_BOX"))
    return f"PO BOX {box}" if box else ""


def _parcel_id(a: dict) -> str:
    """County-unique parcel key. SWIS_SBL_ID is the layer's designed
    unique id; fall back to SWIS + PRINT_KEY."""
    pid = _s(a.get("SWIS_SBL_ID"))
    if pid:
        return pid
    swis, pk = _s(a.get("SWIS")), _s(a.get("PRINT_KEY"))
    return f"{swis}-{pk}" if swis and pk else (pk or swis)


def _improvement_value(total, land):
    t, l = _to_int(total), _to_int(land)
    if t is None or l is None or t < l:
        return None
    return t - l


def normalize_feature(feature: dict, *, fetched_at: str) -> dict:
    """Map one ArcGIS feature to a §4.32 wrapped raw record."""
    a = feature.get("attributes", {}) or {}
    oid = a.get("OBJECTID")
    parcel_id = _parcel_id(a)
    record_url = (
        f"{SERVICE_URL}/{LAYER_ID}/query?where=OBJECTID%3D{oid}"
        "&outFields=*&f=json"
    )
    payload = {
        # framework-canonical fields the parcel_master translator reads
        "parcel_id": parcel_id,
        "address": _situs_address(a),
        "owner_name": _owner_name(a),
        "owner_mailing_address": _mailing_address(a),
        "owner_mailing_city": _s(a.get("MAIL_CITY")),
        "owner_mailing_state": _s(a.get("MAIL_STATE")),
        "owner_mailing_zip": _s(a.get("MAIL_ZIP")),
        "city": _s(a.get("MUNI_NAME")),
        "zip": _s(a.get("LOC_ZIP")),
        "assessed_value": _to_int(a.get("TOTAL_AV")),
        "land_value": _to_int(a.get("LAND_AV")),
        "improvement_value": _improvement_value(a.get("TOTAL_AV"),
                                                a.get("LAND_AV")),
        "year_built": _to_int(a.get("YR_BLT")),
        "property_use": _s(a.get("PROP_CLASS")),
        "acres": _to_float(a.get("ACRES")) or _to_float(a.get("CALC_ACRES")),
        "legal_description": "",  # not exposed by the NYS public layer
        # reference-only extras (translator ignores unknown keys)
        "print_key": _s(a.get("PRINT_KEY")),
        "sbl": _s(a.get("SBL")),
        "swis": _s(a.get("SWIS")),
        "county_name": _s(a.get("COUNTY_NAME")),
        "owner_type": _s(a.get("OWNER_TYPE")),
        "add_owner": _s(a.get("ADD_OWNER")),
        "full_market_value": _to_int(a.get("FULL_MARKET_VAL")),
        "roll_year": _to_int(a.get("ROLL_YR")),
        "used_as_desc": _s(a.get("USED_AS_DESC")),
    }
    return {
        "raw_record_id": parcel_id or f"OID-{oid}",
        "source_id": SOURCE_ID,
        "source_url": record_url,
        "source_fetched_at": fetched_at,
        "parser_confidence": 95,
        "raw_payload": payload,
    }


def run(*, output_path: Path | None = None,
        max_features: int | None = None,
        muni: str | None = None,
        fetch_fn=None) -> dict:
    """Pull Greene County parcels and write the wrapped JSONL output.

    max_features caps the pull (for proving / testing); None pulls the
    full county roll. muni limits to one town (MUNI_NAME), also for
    bounded test pulls. fetch_fn is injectable for fixture-driven tests.
    """
    output_path = output_path or REPO_ROOT / "data" / "raw" / "parcel_master.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    where = f"COUNTY_NAME='{COUNTY_NAME}'"
    if muni:
        where += f" AND MUNI_NAME='{muni}'"

    server = ArcGISFeatureServer(SERVICE_URL, user_agent=USER_AGENT,
                                 fetch_fn=fetch_fn)
    fetched_at = _now_iso()

    stats = {
        "source_id": SOURCE_ID,
        "service_url": f"{SERVICE_URL}/{LAYER_ID}",
        "where": where,
        "output_path": str(output_path),
    }

    tmp = output_path.with_suffix(".jsonl.tmp")
    count = 0
    seen: set = set()
    with open(tmp, "w", encoding="utf-8") as fh:
        for feat in server.iter_features(
            layer_id=LAYER_ID,
            where=where,
            out_fields=OUT_FIELDS,
            return_geometry=False,
            max_features=max_features,
        ):
            rec = normalize_feature(feat, fetched_at=fetched_at)
            pid = rec["raw_record_id"]
            if pid in seen:
                continue
            seen.add(pid)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1
    tmp.replace(output_path)

    stats["records_written"] = count
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pull Greene County, NY parcel-master records from the "
                    "NYS GIS Clearinghouse public tax-parcel layer."
    )
    parser.add_argument("--out", default=None,
                        help="Output JSONL path. Default: data/raw/parcel_master.jsonl")
    parser.add_argument("--max-features", type=int, default=None,
                        help="Cap on records pulled (omit for the full county roll).")
    parser.add_argument("--muni", default=None,
                        help="Limit the pull to one town (MUNI_NAME).")
    args = parser.parse_args()

    stats = run(
        output_path=Path(args.out) if args.out else None,
        max_features=args.max_features,
        muni=args.muni,
    )
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
