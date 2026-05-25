# Greene County NY — Missed-Source Audit

Date: 2026-05-25
Framework: v5.4.0
Scope: county-side recon only. No adapters built. No framework files
touched. No leads fabricated.

Audit lanes 1–9 per operator brief. Companion JSON artifacts in this
folder:
- `aar_archive.json`           AAR catalog enumeration
- `treasurer_archive.json`     Treasurer petition PDFs + portal back-end
- `tcs_deep.json`              Total Collection Solution deep verification
- `legal_notices_sweep.json`   newspaper-of-record + Column re-recon
- `municipal_sweep.json`       BAS / InfoTax / per-town code/lien sweep

## Headline

**635 is NOT the full accessible universe.** 635 is what the **current
adapters** pull: 584 from one year of the Treasurer petition (2025) +
50 from one AAR auction (auctionId=6892) + 1 from a misconfigured
Column query. The audit identified at least **four stdlib-reachable
PRIMARY event sources** that the current build does not exploit, plus
multiple historical-year backfills against the two sources that are
already wired.

The lower bound on the next-pull addressable universe is roughly:

| Source | Net-new leads available now |
|---|---|
| TCS `status=Delinquent` bills (Treasurer back-end) | **~2,084** currently delinquent |
| TCS `status=Unpaid` bills (current cycle, not yet delinquent) | **~85** |
| Column adapter filter fix (`Greene County` not `Greene`) | **+34** (35 vs current 1) over 90 d |
| AAR auctionId=3738 (Greene 2022 tax-foreclosure auction, 80 lots) | **+80** historical disposition records |
| Treasurer petition prior years (2019, 2020, 2022 — text-layer, no OCR) | **~727** historical petition parcels |

That is **~3,010 additional addressable records** of varying recency,
without any operator cookie unlock and without defeating any
Cloudflare wall.

---

## A. Sources already built (3 PRIMARY + 1 ENRICHMENT)

| source_id | role | last run | leads | distress type |
|---|---|---|---|---|
| `tax_foreclosure_petition`  | PRIMARY_EVENT | 2025 petition PDF (OCR) | 584 | tax_foreclosure_notice |
| `tax_foreclosure_auction`   | PRIMARY_EVENT | AAR auctionId=6892 (Oct 2025) | 50 | tax_foreclosure_notice |
| `legal_notices_column`      | PRIMARY_EVENT | 90-d Column pull, filter=`Greene` | 1  | notice_of_sale |
| `parcel_master`             | ENRICHMENT    | NYS GIS ArcGIS (38 418 parcels) | 0 | (never originates) |

## B. Gated sources + exact blocker (instruction: do not spend time defeating)

| source_id | host | actionable-step blocker | unlock |
|---|---|---|---|
| `clerk_land_records` | searchiqs.com/nygre | Cloudflare Managed Challenge on `btnGuestLogin` click (cType=managed, no widget iframe, no auto-resolve in 40 s polls cold or warmed) | Operator-supplied `cf_clearance` + ASP.NET `IQSCustomerID`/`IQSAuthToken` session cookies (manual HAR capture from a solved guest session works), OR a browser-capable CI worker with operator-interactive Turnstile solve, OR a paid SearchIQS subscription |
| `supreme_court_foreclosure` | iapps.courts.state.ny.us/nyscef | Managed Challenge on Case Search submit | `cf_clearance` + iApps `JSESSIONID` from a solved session |
| `surrogate_court_probate` | iapps.courts.state.ny.us/nyscef (TAB=name, court=Surrogate) | same managed challenge, same servlet | same as Supreme |
| `webcivil_supreme` | iapps.courts.state.ny.us/webcivil/FCASSearch | Managed Challenge on POST + any second nav | same `cf_clearance` |
| `websurrogate` | websurrogates.nycourts.gov/Search/Cases | Managed Challenge on /Search/Cases | same `cf_clearance` |

Empirical proof + per-source form spec at
`runs/greene_ny/recon/stealth_recon_2026-05-25.md` +
`runs/greene_ny/recon/stealth_probe/*.json`.

## C. Non-gated sources NOT yet built (the headline misses)

### C1. Total Collection Solution (TCS) — `https://ny-greenecounty.totalcollectionsolution.com/`

**Classification: PRIMARY_EVENT_SOURCE — confirmed.**

This is the Greene County Treasurer's back-end (Systems East vendor).
Public credentials are *published by the county* on the Treasurer's
own site for guest tax lookup: `org=greenecounty`, `user=public@greene`,
`pass=public`. Verified working 2026-05-25.

Post-login endpoints (read-only under public account):

| endpoint | rows | content |
|---|---|---|
| `POST /bill/listXml` `status=0`  | 85       | currently UNPAID bills (this cycle, not yet delinquent) |
| `POST /bill/listXml` `status=3`  | **2 084** | currently DELINQUENT bills |
| `POST /bill/listXml` `status=7`  | 80 608  | historical RELEVIED bills (re-levy onto tax bill) |
| `POST /bill/listXml` `status=8`  | 0       | TAX_SALE status (empty in this snapshot) |
| `GET  /entity/listXml`            | 44 897 | all parcels (SBL, priorPrintKey, owner, location) |
| `GET  /address/listXml`           | 65 588 | mailing addresses keyed by entity |
| `GET  /bill/show/id/{N}`          | per-row | adds Address 1, Owner 2, Date Delinquent, Orig Amount, Is Arrears |

Fields per delinquent bill: entity (SBL), bill_number, bill_date,
status, owner1, bill_type, base / interest / penalty / paid / due,
plus mailing address + delinquency date via the detail endpoint.

**Why it's PRIMARY, not enrichment:** the status filter ORIGINATES
leads — you query `status=3` and get a list of parcels you didn't
previously know were delinquent. No parcel-pre-selection required.
That is the definition of a primary event source under §13.

**Caveats (will block "ship it tomorrow"):**

1. `robots.txt` on the TCS subdomain says `User-agent: *  Disallow: /`.
   The underlying data is public under NY RPTL §1500 et seq., but the
   platform ToS explicitly disallows crawling, and the public account
   is intended for interactive single-bill lookup.
2. `landsale/listXml` (in-rem foreclosure-sale records) returns 165
   rows but `saleAmount` is masked to $0.00 and only 2 batches are
   exposed; the current in-rem queue is not surfaced.
3. No CAPTCHA, no rate-limit headers, but a defensible rollout would
   cap at ≤1 rps, set an identifying User-Agent, and limit to
   `status=0` + `status=3` (≈2 170 records, defensible as
   directed-lookup).
4. The cleanest legal path is a FOIL request to the Treasurer for
   the same data export — same record set, no ToS risk. The TCS
   endpoint then becomes the daily-refresh path against an
   operator-explicit go-ahead.

**Operator decision required** before this adapter is built. **This
is the single biggest miss in the audit.** ~2 084 net-new
tax-delinquency event records sit one operator approval away.

### C2. Column adapter — one-character filter fix

**Classification: existing PRIMARY_EVENT_SOURCE, undersampling by ~35×.**

Current adapter (`scrapers/legal_notices_column.py`) passes
`county:["Greene"]` to the Column eNotice search API. That value:

- Matches **76 Kingston Daily Freeman notices** tagged `county="Greene"`
  (service-area metadata on an Ulster paper) — **0 of which are about
  Greene property.** The downstream "Greene-property attachment"
  regex filters them all out → 1 survivor today.
- **Does not match** the Catskill Daily Mail notices, which Column
  tags as `county="Greene County"` (with the word "County").

Switching the filter token to `"Greene County"` returns
**35 distress notices in a 90-day window**:

- 30 Foreclosure Sale notices
- 4 Summons (= lis pendens proxies)
- 1 Estate (Probate) Filing

That's a **35× yield jump from a one-string config fix**, plus net-new
distress doc types (lis pendens + probate) that the build does not
currently carry.

Column's `noticetype` field (`Foreclosure Sale` / `Summons` /
`Estate (Probate) Filings`) is reliable; the adapter currently regexes
the body text and would be cleaner reading the structured field.

### C3. AAR — auctionId=3738 (Greene 2022 tax-foreclosure auction)

**Classification: existing PRIMARY_EVENT_SOURCE, historical backfill.**

AAR has run **two** Greene County tax-foreclosure auctions ever:

| auctionId | date | lots | status |
|---|---|---|---|
| 3738 | 2022-10-12 | **80** | CLOSED — full lot HTML still accessible, final bids visible |
| 6892 | 2025-10-29 | 51 | CLOSED — current build target |

The 2022 catalog is unchanged from when it ran (HTML preserved
indefinitely) and is callable today via
`https://aarauctions.com/servlet/Search.do?auctionId=3738`. Same
per-lot fields as 6892: lot #, address, municipality, Tax Map #,
School District, Full Market Value, county/town/school tax due,
**final high bid + winning bidder username**.

Recency caveat: 2022 dispositions are 4 years old. Those parcels
either (a) closed in operator hands long since (no longer leads), or
(b) reverted / were re-listed. Useful as historical context + win-rate
calibration rather than fresh-distress origination.

### C4. Treasurer petition PDFs — prior years 2019 / 2020 / 2022 (text-layer)

**Classification: existing PRIMARY_EVENT_SOURCE, historical backfill,
no OCR required.**

Greene published an annual RPTL Article 11 petition every year
2015–2025 (skipping 2014-and-earlier; 2021 rolled into 2022 post-
COVID; 2024 rolled into 2025; no 2026 yet). The 2019, 2020, and 2022
PDFs **have a text layer** — the current OCR-pipeline adapter can be
re-pointed to those URLs and parse them without `tesseract`.

| year | source | text layer? | parcels |
|---|---|---|---|
| 2025 (live) | greenecountyny.gov/wp-content/uploads/2025/04/...Forclosure.pdf | NO (OCR) | 584 (in build) |
| 2023        | greenecountyny.gov/wp-content/uploads/2025/01/...Schedule-A.pdf | NO (OCR) | ~? |
| **2022**    | (Wayback) greenegovernment.com/.../2022/05/...-4.21.2022.pdf | **YES** | ~337 |
| **2020**    | (Wayback) greenegovernment.com/.../2020/02/...-2.20.2020.pdf | **YES** | ~282 |
| **2019**    | (Wayback) greenegovernment.com/.../2019/04/...-Foreclosure.pdf | **YES** | ~108 |
| 2018 / 2017 / 2016 / 2015 | (Wayback only) | NO (OCR) | unknown |

Same Schedule A schema as 2025 (parcel ID, tax year, owner, original
tax, interest + penalty, total due, grouped by SWIS). Text-layer
years parse straight via `pdftotext`. Wayback availability is a
mild fragility — operator may want to mirror the PDFs locally.

Recency caveat: 2019–2022 petitions show parcels that ROLLED through
the 2022 / 2025 dispositions. Useful for stacked-distress signal
(parcel on multiple petitions = persistent delinquency) rather than
fresh origination.

## D. Sources rejected (with reasons)

| source | reason |
|---|---|
| `nyspublicnotices.com` / `publicnoticesny.com` | unreachable / appears defunct; NY ecosystem consolidated onto Column |
| `mypublicnotices.com` | timeouts; not the NY primary venue |
| NYNPA (`nynpa.com`) | brochureware — no notices feed |
| `catskillnewspapers.com` | DNS unresolvable, HTTP 526 |
| `greenvillepioneer.com` | HTTP 526 |
| `hudsonvalley360.com` / `dailygazette.com` | display layer over Column — same upstream, no new data |
| BAS Gov town tax portals (Athens, Cairo, Catskill, Coxsackie, Durham, Greenville, Hunter, Lexington, New Baltimore, Windham, Village of Catskill) | bill-lookup + payment only; no public delinquent list; no arrears flag — **ENRICHMENT**, not event |
| InfoTax Online school portals (Catskill, Coxsackie-Athens, Hunter-Tannersville, WAJ) | school-tax bill-lookup only; JS-required ASP.NET; **ENRICHMENT** |
| `prosgar.com` (GAR Associates assessment) | assessment data only; no delinquency column — **ENRICHMENT** |
| Greene County code-enforcement / demolition / condemnation | no county-level dept; town determinations live in unstructured board minutes; no crawlable list anywhere — **NOT_FOUND** (would require FOIL per town) |
| Greene municipal-lien (utility re-levy) | re-levy goes onto tax bill (already captured by TCS); raw water/sewer delinquency lists not online — **NOT_PUBLISHED_ONLINE** |
| `pacer_ndny` (bankruptcy) | paid + operator credentials required — out of scope per operator decision |
| Divorce | DRL §235 — confidential by statute |

## E. Sources that can produce MORE leads right now (stdlib, no operator unlock)

Ranked by impact:

1. **Column filter fix** (existing adapter, one-string change):
   - +34 lead notices in 90 d window vs current 1
   - adds **lis_pendens** + **probate** distress doc types
   - **immediate yield: ~34 fresh distress records**
2. **AAR auctionId=3738 backfill** (existing adapter accepts `--auction-id`):
   - +80 lots (4-year-old disposition records)
   - matures the historical stack-depth signal
3. **Petition prior years 2019 / 2020 / 2022** (existing adapter, alternate URLs, text-layer parse):
   - +~727 historical petition parcels
   - matures the recurring-delinquency stack-depth signal
4. **TCS daily delinquency pull** (NEW adapter — needs operator
   sign-off on robots.txt / ToS):
   - **+~2 084 currently-delinquent parcels** (status=3)
   - +85 currently-unpaid bills (status=0)
   - net-new live-distress origination, daily refresh-able

If items 1–3 ship and item 4 gets operator approval, the lead
universe expands from 635 to approximately **3 645** addressable
records, with **four distress doc types** instead of two.

## F. Sources that need cookie seed

| source_id | seed | what unlocks |
|---|---|---|
| `clerk_land_records` (SearchIQS) | `cf_clearance` + `ASP.NET_SessionId` + `IQSCustomerID` from a manually-solved guest session | recorded liens, lis pendens, deeds (executor / administrator / tax), federal/state/mechanic tax liens, judgments |
| `supreme_court_foreclosure` (NYSCEF) | `cf_clearance` + iApps `JSESSIONID` | Mortgage Foreclosure case filings, RPAPL judgments, lis pendens |
| `surrogate_court_probate` (NYSCEF Surrogate court-type) | same cookies | probate, administration, affidavit-of-heirship |
| `webcivil_supreme` | `cf_clearance` | docketed Supreme civil cases (party-name sweep over canonical foreclosure plaintiffs) |
| `websurrogate` | `cf_clearance` | searchable Surrogate case index |

A single solved-browser HAR + the cookies extracted unlocks all five
(they share Cloudflare's per-cookie clearance scope at the `*.nycourts.gov`
+ `searchiqs.com` zones).

## G. Sources that are enrichment-only

| source | what it enriches | join key |
|---|---|---|
| `parcel_master` (NYS GIS ArcGIS) | owner, mailing addr, assessed value, school dist, property class | PRINT_KEY / parcel_id (already wired) |
| `prosgar.com` (Greene PROS) | same set, per-parcel UI | per-parcel only |
| BAS Gov town portals (11 Greene towns + Village of Catskill) | current-cycle town tax bill, prior-year payments | per-parcel after lookup |
| InfoTax Online (4 school districts) | school-tax bill | per-parcel after lookup |
| `tentative_assessment_roll` (operator-supplied bulk) | annual roll snapshot | SWIS+SBL |

## H. Recommended next adapter after AAR

In strict execution-cost order (lowest friction first):

1. **`legal_notices_column` filter fix** — 1-line change in
   `scrapers/legal_notices_column.py`:
   - replace `PUBLISHING_COUNTIES = ["Greene"]` with `["Greene County"]`
   - prefer reading Column's `noticetype` field rather than re-regexing
     the body text
   - prefer matching `county` field as substring (Column comma-joins
     service-area counties: e.g. `"Albany County, Greene County"` for
     Ravena News-Herald)
   - net: +34 distress records + adds lis_pendens + probate doc types
2. **`tax_foreclosure_auction` historical pull** — invoke with
   `--auction-id 3738` in addition to the seasonal-discovery pass
   (the seasonal-zero preservation patch already lets both data sets
   coexist on disk)
3. **`tax_foreclosure_petition` historical pull** — point the same
   adapter at the Wayback 2019 / 2020 / 2022 URLs (text-layer parse via
   `pdftotext`, no `tesseract` round-trip needed for those years)
4. **New adapter: `treasurer_tcs_delinquent`** — TCS portal pull.
   **Operator approval gate before code is written.** Specifically
   confirm:
   - that scraping the published public-account TCS data is acceptable
     to the operator and county (robots.txt says no; the data is
     statutorily public; the cleanest path is a parallel FOIL or
     written treasurer go-ahead)
   - the cadence (daily? weekly?)
   - whether to limit to `status=0` + `status=3` (~2 170 rows) or also
     include `status=7` relevied (~80 608)

## I. Is 635 the full accessible universe?

**No.** **635 is the current AAR + 2025-petition + mis-filtered-Column
lane only.**

With zero operator action beyond approving the work:
- **+34 leads** from the Column filter fix (1-string change to an
  existing adapter)
- **+80 leads** from AAR auctionId=3738 backfill
- **+727 leads** from petition prior-year backfill (text-layer years)

With operator sign-off on TCS scraping (or a parallel FOIL request to
the Treasurer):
- **+2 084 currently-delinquent leads** from TCS `status=3`
- **+85 currently-unpaid** from TCS `status=0`

With operator cf_clearance cookie:
- recorded clerk liens / lis pendens / deeds (SearchIQS)
- NYSCEF foreclosure docket
- NYSCEF probate (Surrogate)
- WebCivil Supreme docket

**Greene is NOT complete.** The "primary-source build" commit
(b65b1c3) was honest about being SOURCE_LIMITED; this audit has now
identified the specific sources to address next.

---

GREENE MISSED SOURCE AUDIT COMPLETE
