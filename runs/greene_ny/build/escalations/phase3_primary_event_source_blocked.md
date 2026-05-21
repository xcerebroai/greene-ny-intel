# ESCALATION — Phase 3 primary event source blocked (Cloudflare)

County: Greene County, New York (slug `greene_ny`)
Framework: Xcerebro County Intelligence Harness v5.3.1
Phase: 3 — First primary event source (lead origination)
Escalation type: §02.10 build-mode escalation / §02.9 clean halt
Date: 2026-05-21

---

## Context

Phase 3 targets the first **primary event source** for Greene County — the
County Clerk land records portal (`clerk_land_records`, SearchIQS) — the P0
source of recorded distress instruments (lis pendens, mechanic's/tax/judgment
liens, estate deeds) that originate lead rows per §13.

The adapter was attempted against the live source. Recon had flagged SearchIQS
and NYSCEF as bot-gated; per operator instruction the blocker was confirmed
empirically rather than assumed.

## Empirical evidence (2026-05-21)

Probed with a standard browser User-Agent over HTTPS (curl):

    https://www.searchiqs.com/nygre/            -> HTTP 403
    https://www.searchiqs.com/nygre/Login.aspx  -> HTTP 403
        server: cloudflare
        cf-mitigated: challenge
        body: "<title>Just a moment...</title>" interstitial; CSP loads
              https://challenges.cloudflare.com  (Cloudflare JS/Turnstile
              interactive challenge)

The same gate covers every Greene County primary event source — the alternate
primary (NYS courts) was probed for completeness:

    https://iapps.courts.state.ny.us/nyscef/CaseSearch   -> HTTP 403
    https://iapps.courts.state.ny.us/webcivil/FCASMain   -> HTTP 403
        server: cloudflare ; cf-mitigated: challenge ; same interstitial

`searchiqs.com/robots.txt` returns HTTP 200, but that is not the records data —
the record search pages themselves are challenge-gated.

Documented-API discovery (recon §01.23, `api_discovery_report.md`) previously
found **no** public API for SearchIQS or the NYS court portals; they are
consumed only through their interactive web surfaces.

## Classification

- Access status: **`BLOCKED`** (§01.9 / §16.F) — Cloudflare interactive
  challenge / anti-bot. Not `OPEN_PUBLIC`, not `SEARCH_ONLY_PUBLIC`.
- Blocker class: **HARD BLOCKER** (§01.13) — a Cloudflare challenge is not
  auto-resolvable; it is not a simple user-agent gate or cookie requirement.
- Buildability: every Greene County PRIMARY EVENT SOURCE (clerk + courts) is
  behind this gate. With current tooling, **zero primary-event lead rows can
  be produced** → no valid lead dashboard is buildable yet.

## Why no workaround was attempted

Per operator directive, §01.17, and §02.9: recon/build does not solve CAPTCHAs
or interactive challenges, does not fabricate records, and does not stand up a
false dashboard from enrichment. A Cloudflare `cf-mitigated: challenge` cannot
be passed by `urllib` / `curl` / `WebFetch` — the only HTTP tooling this
execution environment provides. Halting is the correct, designed outcome.

## Exact infrastructure required to resume

Phase 3 resumes on **browser-capable infrastructure**. Approved framework
access strategies (FRAMEWORK_VERSION.json locked rules — `stealth_browser_
allowed`, `seeded_session_allowed`, `operator_seeded_session_allowed`,
`residential_proxy_allowed`, `captcha_solver_allowed`, `operator_credentialed_
login_allowed` are all `true`). In recommended order:

1. **Operator-seeded session (cheapest, cleanest).** Operator solves the
   Cloudflare challenge + SearchIQS guest login once in a real browser and
   exports the `cf_clearance` cookie + the ASP.NET session cookies; the
   framework replays them. Caveat: `cf_clearance` is IP+UA-bound and expires
   in ~30 min–few hours, so a daily-refresh product needs either periodic
   re-seeding or option 2.
2. **Stealth-browser worker.** A headless Chromium with stealth/undetected
   tooling (e.g. Playwright + stealth, `nodriver`, or undetected-chromedriver),
   on infrastructure that can run a real browser. Plain headless Chromium often
   still fails `cf-mitigated: challenge`; stealth is the operative requirement.
   A residential proxy may additionally be needed if Cloudflare IP-reputation-
   gates the datacenter IP range.
3. **Operator-assisted manual pull / standing records delivery** from the
   Greene County Clerk's office (last-resort, non-automated channel).

None of options 1–3 are available in the current sandboxed execution
environment, which exposes only non-browser HTTP clients.

## Recommended action

Stand up a stealth-browser-capable worker (option 2) for the daily-refresh
product, or supply an operator-seeded `cf_clearance` + session (option 1) for
an immediate Phase 3 proof. Phases 0–2 carry over unchanged; the build resumes
at Phase 3.

## Operator decision

    [ ] Provide a stealth-browser-capable execution environment — resume Phase 3.
    [ ] Provide an operator-seeded SearchIQS session (cf_clearance + cookies).
    [ ] Authorize operator-assisted manual pull / standing records delivery.
    [ ] Other / hold.

    Operator: ______________________   Date: ______________
