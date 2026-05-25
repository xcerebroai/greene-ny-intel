# Greene NY — AAR ↔ parcel_master matcher join — punch-list

Date: 2026-05-25
Framework: v5.4.0 (commit 0dd4b07)
County-side runner: `runs/greene_ny/build/run_greene_pipeline.py`

## Stage boundary discipline — honored

- AAR `tax_foreclosure_auction` is the **sole PRIMARY EVENT SOURCE**. Every
  raw_event carries `source_id=tax_foreclosure_auction`,
  `source_role=PRIMARY_EVENT_SOURCE`.
- parcel_master is **ENRICHMENT ONLY**. It is never passed as a §17 document;
  no raw_event originates from it.
- `parties=[]` is passed through to §17 for every AAR raw_event — AAR does
  not name an owner per lot. §17 routes all 50 leads to `REVIEW_REQUIRED`
  with `review_reason: owner_not_on_document` and a placeholder owner
  (`tax_foreclosure_notice against unidentified party`). That routing is
  **preserved verbatim** — never relabeled as §17-resolved. The dashboard
  row carries `display_owner_section17_raw` so the §17 placeholder is
  always visible alongside the enriched owner.
- Owner attaches **downstream** as enrichment via a county-side projection
  that performs the PRINT_KEY join (the operator-named authoritative key).
  Every row records `owner_source=parcel_master` (or `unresolved`),
  `enrichment_source=parcel_master` (or `none`), and
  `row_enrichment_join_method` (`print_key` here).

## Counts

| metric | value |
|---|---|
| AAR lots ingested | 50 |
| parcel_master rows (full Greene roll) | 38,418 |
| **Tax Map # → PRINT_KEY join** | **50 hit / 0 miss** |
| raw_events with parcel_id resolved (SWIS_SBL_ID) | **50 of 50** |
| matched_leads | 50 |
| scored_leads | 50 |
| **§20 verdict** | **`DEPLOY_OK`** |
| **owner attached from parcel_master** | **50 of 50** (`owner_source: parcel_master`) |
| §17-resolved owner (from AAR doc itself) | 0 (correct — AAR exposes no owner) |
| still REVIEW_REQUIRED (§17 honest) | 50 (correct — owner not on document) |
| **row-level ENRICHED** | **50** (downstream PRINT_KEY join) |
| seam-level ENRICHED | 0 (see "Framework coupling" below) |
| build_label | `SOURCE_LIMITED` |
| framework gate suite | PASS 4/4 + v5.4.0 contract tests |

No stop conditions fired: no crash, no `DEPLOY_BLOCKED`.

## Why a county-side runner (not `build_leads.py`)

The monolith's `foreclosure_notices` translator emits signals **without an
`address` field**, so the monolith's address-based matcher cannot bridge AAR
signals to parcel_master rows. The natural join is **Tax Map # →
PRINT_KEY** (operator-authoritative). Doing that join county-side and
driving the v5.4.0 staged engine's public API
(`run_pipeline_staged.run_staged_pipeline`) directly resolves parcel_id
at the raw_event seam — no scaffold edit.

## Framework coupling observed (not patched — honest workaround)

`scaffold/pipeline/leads_base_writer.py:218` sets
`key_parcel_id = parcel_id if parcel_resolution_status == "RESOLVED" else None`,
and lines 210–213 set `parcel_resolution_status = REVIEW_REQUIRED` whenever
`debtor_resolution_status == REVIEW_REQUIRED`. So even when the raw_event's
`property_refs.parcel_id` is set to a real SWIS_SBL_ID, the §18 aggregation
key has `parcel_id=null` once §17 routes REVIEW_REQUIRED → the scoring seam
gets `primary_parcel_id=None` → the `enrichment_provider` is never called →
`scored_lead.enrichment_status = UNENRICHED`.

This appears to contradict §13.14's stated decoupling of
`parcel_resolution_status` from `enrichment_status`, but it is the framework
shipped behavior. Per operator rules ("do not modify universal framework
files unless a true framework defect blocks the run"), I did **not** patch
`scaffold/` — the seam path is preserved as-is. The county-side runner
attaches the parcel_master enrichment in the dashboard projection
post-`run_staged_pipeline`, recording two breakdowns side-by-side:
`enrichment_breakdown` (row-level, ENRICHED=50) and
`seam_enrichment_breakdown` (seam-level, ENRICHED=0).

Recommended framework conversation (out of scope for this build): land the
§13.14 decoupling at the leads_base_writer / aggregator boundary so the
seam can attach enrichment via `parcel_id` independently of §17 owner
resolution. Until then, county-side post-process is the clean workaround.

## Unmatched lots → punch-list

**None.** All 50 AAR Tax Maps joined cleanly to a PRINT_KEY in the full
38,418-record Greene parcel_master roll.

## Notable carry-overs (from prior turns)

1. AAR Greene auction is seasonal — `auctionId=6892` is Oct-2025 historical;
   the 2026 auction has not yet published. Adapter discovery mode returns
   zero today; pull via `--auction-id` when next live.
2. `data/raw/parcel_master.jsonl` is now the **full Greene county roll**
   (38,418 records) — the Phase 2 bounded pull (3,000) is superseded.
3. Score tiers/patterns still uniform — single-source single-doc-type
   intake. Diversity emerges when clerk + court primaries (Cloudflare-gated)
   come online via operator-seeded session.
4. `dashboard/dashboard.js` is the legacy v5.1.2 reader; the v5.4.0 staged
   payload now adds `display_owner_source`, `row_enrichment_status`,
   `tax_map`, `event_source`/`owner_source`/`enrichment_source` per row,
   plus payload-level `seam_enrichment_breakdown` and
   `enrichment_join_method_counts`. Renderer customization is Phase 5 work.

## Files produced

- `runs/greene_ny/build/run_greene_pipeline.py` (county-side runner).
- `data/dashboard.json` (v5.4.0 staged payload, county-side projection).
- `data/production/*.json` (matched_leads, scored_leads, evidence_ledger,
  *_leads_base.json, source_heartbeat).
- `dashboard/data/*.json` (deploy mirror).
- `runs/greene_ny/build/punch_list_matcher_join_2026-05-25.md` (this file).
