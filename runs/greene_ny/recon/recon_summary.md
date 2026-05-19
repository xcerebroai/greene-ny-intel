# Recon Summary — Greene County, New York

County: Greene County, New York (slug greene_ny)
Framework version: v5.3.0
Generated: 2026-05-19
Operator-facing executive summary. Detail: build_eligibility_handoff.md and
source_of_record_matrix.json.

---

## Build Eligibility Gate verdict

    READY_TO_BUILD

## What this county can produce

Greene County, NY publishes its core real-estate distress events online and
free to the public. Recon verified eight official sources and walked all 27
canonical lead types. The county can produce a real, daily-refreshed lead
board today.

- **Mortgage foreclosure** — New York is a judicial-foreclosure state.
  Foreclosure actions are filed in the Supreme Court and, because Greene County
  Supreme Court has had mandatory e-filing since October 2020, the full docket
  and PDF documents are public and free on NYSCEF. This is a P0 daily source.
- **County Clerk land records** — Deeds, mortgages, the full lien family
  (mechanic's, federal tax, state tax, judgment), and lis pendens are searchable
  free as a guest on the County Clerk's SearchIQS portal. P0 daily source.
- **Probate / estate** — Surrogate's Court probate and administration
  proceedings are public on NYSCEF (mandatory e-filing since February 2021).
- **Tax foreclosure** — The County Treasurer enforces delinquent taxes via an
  RPTL Article 11 in-rem foreclosure and publishes an annual Petition & Notice
  of Foreclosure; foreclosed parcels are sold at an annual online auction. This
  is a P1 (annual-cadence) distress feed.
- **Enrichment** — Parcel/assessment data (GAR PROS portal) and GIS parcel
  geometry (county ArcGIS + the statewide NYS GIS Clearinghouse, available as a
  full-county bulk download) are open and free.

## What is NOT available

- **Sheriff sale calendar** — NY foreclosure sales are referee's sales noticed
  inside the Supreme Court case; the Sheriff publishes no standalone online sale
  list. Sale events are captured through the court source instead.
- **Code enforcement, demolition, condemnation** — run by each of the 14 towns
  individually; no county-wide portal. Recorded code/municipal liens still
  surface in clerk land records.
- **Eviction** — filed in town/village Justice Courts with no public online
  docket.
- **Divorce** — NY matrimonial records are confidential by statute.
- **Bankruptcy** — federal; available only via PACER (paid). Optional, routed
  to operator review.

## Why this verdict

Four verified PRIMARY lead sources are publicly accessible without operator
escalation, three of them daily-refresh distress feeds — the P0 gate passes
comfortably. Enrichment is available. No primary source is blocked, so the
auto-resolve phase (Phase 0.5) was not needed. The build will be a FULL_BUILD.

## Recommended next action

Approve entry to Build Mode. The core distress pipeline — foreclosure, clerk
liens/lis pendens, and probate — is buildable immediately; tax foreclosure
follows as an annual secondary feed. Decide separately whether bankruptcy
(PACER, paid) is in scope.

## Open questions for the operator

1. SearchIQS guest mode — does it allow free document-image VIEWING, or only
   index search? Recon classified conservatively as SEARCH_ONLY_PUBLIC; either
   way the source is buildable.
2. Is bankruptcy (PACER, Northern District of NY) in scope? It is the only paid
   source; if yes, PACER credentials are required.
3. Confirm the County Clerk's modern (post-2004) lis pendens index coverage —
   the clerk's published note references a separate 1924-2004 LP index.
