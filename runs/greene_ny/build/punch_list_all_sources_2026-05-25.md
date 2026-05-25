# Greene NY — full primary-source build punch-list

Date: 2026-05-25
Framework: v5.4.0 (commit 0dd4b07)
Runner: `runs/greene_ny/build/run_greene_pipeline.py`

## Sources probed + outcomes

| Source | URL | Tech | Outcome | Records |
|---|---|---|---|---|
| AAR tax-foreclosure auction | aarauctions.com/servlet/Search.do | nginx + Java servlet, server-rendered HTML | **BUILT** (stdlib) | 50 (historical auctionId=6892) |
| Treasurer Annual Petition | greenecountyny.gov / scanned PDF | scanned image PDF → pdftoppm + tesseract OCR | **BUILT** (stdlib + OCR) | 584 parcels (RPTL Art. 11 in-rem petition; tax years 2014–2023) |
| Column legal notices | newyork.column.us → Firebase Cloud Functions | `POST /api/search/public-notices` JSON | **BUILT** (stdlib) | 1 (after tightening filter to require `COUNTY OF GREENE` mention; 4 false positives from Lexington-as-defendant text rejected) |
| SearchIQS clerk land records | searchiqs.com/nygre | Cloudflare **Turnstile** (interactive) | **PUNCH-LIST** — plain headless Playwright passes the *landing* page but the "Search Records as Guest" click triggers Turnstile which does not auto-resolve under headless. Verified 2026-05-25. Needs stealth tooling (playwright-stealth / undetected) or operator-seeded `cf_clearance`. |
| NYSCEF Supreme + Surrogate | iapps.courts.state.ny.us/nyscef | Cloudflare challenge | **PUNCH-LIST** — same Cloudflare wall (`cf-mitigated: challenge`, "Performing security verification"). Verified 2026-05-25. Same stealth/seeded-session requirement. |
| WebCivil Supreme | iapps.courts.state.ny.us/webcivil | Cloudflare challenge | **PUNCH-LIST** — same. |
| NYS Tax Warrant Notice System | www8.tax.ny.gov/TWNS | down / connection reset | **PUNCH-LIST** — service unreachable. Recheck periodically. |
| PACER bankruptcy NDNY | pacer.uscourts.gov | Paid subscription | **OUT OF SCOPE** per prior operator decision. |
| Greene County Sheriff sale list | greenecountyny.gov/departments/sheriff | none online | **NOT FOUND** — NY foreclosure sales are referee sales noticed in the Supreme Court case (NYSCEF, Cloudflare). |
| Per-town code enforcement | per-town | per-town only | **NOT FOUND** — Greene has 14 towns; no county-wide portal. |
| Town/village justice courts (eviction) | per-town | none online | **NOT FOUND** — no public online docket. |

## End-to-end pipeline result

- raw_events: 635 (AAR 50 + Treasurer 584 + Column 1)
- parcel_id resolved: 619 (97% PRINT_KEY join coverage)
- matched_leads: 635
- scored_leads: 635
- **§20 verdict: `DEPLOY_OK`**
- enrichment_breakdown (row-level via PRINT_KEY join): **619 ENRICHED / 16 UNENRICHED**
- owner_source: 582 from §17 (event-document parties — Treasurer + Column) · 51 from parcel_master (AAR auction rows + 1 Column row where §17 couldn't resolve)
- pattern_counts: foreclosure=1 · tax=634
- owner_type distribution: 475 INDIVIDUAL · 138 ENTITY · 12 ESTATE · 8 TRUST · 2 UNKNOWN
- 111 out-of-state owners · 505 absentee
- framework gate suite: PASS

## Distress types now on the board

| signal_label | source | count |
|---|---|---|
| Tax Foreclosure — In-Rem Petition | tax_foreclosure_petition | 584 |
| Tax Foreclosure — Auction | tax_foreclosure_auction | 50 |
| Foreclosure Notice of Sale | legal_notices_column | 1 |

When SearchIQS / NYSCEF unblock, lis pendens, mechanic lien, federal/state
tax lien, judgment lien, executor/administrator deeds, probate, and surplus
filings will land alongside.

## Stage-boundary discipline — audited

- parcel_master never originates a lead. It's enrichment only, attached
  downstream via PRINT_KEY (619/635 rows) or parcel_id (rest).
- AAR auction rows: `parties=[]` (HONEST — AAR exposes no owner per lot);
  §17 routes REVIEW_REQUIRED; owner attaches from parcel_master via
  `owner_source=parcel_master`.
- Treasurer petition rows: `parties=[{name: <owner from Schedule A>,
  name_type: "DF", raw_role: "taxpayer_named_in_rem_petition"}]`. The
  petition IS the event document; the owner is a named defendant in the
  in-rem proceeding. §17 reads it as event-document party.
- Column notice rows: `parties` extracted from notice text (defendant/
  plaintiff regex). The notice IS the event document.

## Renderer

`dashboard/` continues to use the El Paso renderer (`index.html`,
`styles.css`, `app.js`) with `data.js` regenerated from the multi-source
dashboard payload. Three signal-label facets appear in the left "Distress
signal" filter. Owner-type filter shows 5 classes. Out-of-state and
absentee filters work.

## Punch-list summary

1. SearchIQS — Cloudflare Turnstile. Needs stealth-Playwright or operator-
   seeded session. Adds: lis pendens + all lien types + executor /
   administrator deeds + judgment dockets (8+ lead types).
2. NYSCEF Supreme + Surrogate + WebCivil — same Cloudflare wall. Adds:
   judicial mortgage foreclosure cases + probate + civil judgments + sale
   notices + surplus.
3. NYS TWNS — unreachable. Adds: state tax warrants (would dedup with clerk-
   filed state tax liens).
4. PACER — paid. Out of scope.
5. Per-town code enforcement / town justice court eviction — no centralized
   source.
6. AAR auction is seasonal — next live Greene auction Sep/Oct 2026.
