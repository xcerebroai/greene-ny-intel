"""Phase 0+1 stealth probe — SearchIQS (Greene clerk) and NYSCEF (Supreme + Surrogate).

Drives chromium via playwright_stealth (same approach that broke Smith TX
publicsearch.us in the prior session). For each gated source we:
  1. Navigate to the landing URL.
  2. Wait for `networkidle` and an extra settle.
  3. Snapshot title + URL + HTML to disk.
  4. Detect Cloudflare Turnstile / challenge markers.
  5. If a search surface is reachable, attempt one query and snapshot the
     result endpoint (so the adapter can call it directly).

Output: runs/greene_ny/recon/stealth_probe/<source>.{html,png,meta.json}
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

OUT_DIR = Path(__file__).resolve().parent
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

CF_MARKERS = [
    "challenges.cloudflare.com",
    "cf-challenge",
    "Just a moment",
    "Checking your browser",
    "Verifying you are human",
    "turnstile",
    "cf_chl_",
]

SOURCES = [
    {
        "id": "searchiqs_landing",
        "url": "https://www.searchiqs.com/nygre/LoginA.aspx",
        "note": "Greene County clerk land-records login (guest mode link from county clerk site)",
    },
    {
        "id": "searchiqs_root",
        "url": "https://www.searchiqs.com/nygre/",
        "note": "Greene County clerk land-records root (county code path)",
    },
    {
        "id": "nyscef_search",
        "url": "https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name",
        "note": "NYSCEF case search — county/court selector (Supreme + Surrogate)",
    },
    {
        "id": "nyscef_root",
        "url": "https://iapps.courts.state.ny.us/nyscef/",
        "note": "NYSCEF landing",
    },
    {
        "id": "webcivil",
        "url": "https://iapps.courts.state.ny.us/webcivil/ecourtsMain",
        "note": "WebCivil Supreme entry",
    },
]


def detect_blockers(html: str, title: str) -> dict:
    lower = html.lower()
    hits = []
    for m in CF_MARKERS:
        if m.lower() in lower or m.lower() in (title or "").lower():
            hits.append(m)
    return {
        "cf_markers": hits,
        "looks_blocked": bool(hits),
    }


def probe(p, src: dict) -> dict:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1400, "height": 900},
        locale="en-US",
    )
    page = ctx.new_page()
    Stealth().apply_stealth_sync(page)
    meta = {
        "id": src["id"],
        "url": src["url"],
        "note": src["note"],
    }
    try:
        resp = page.goto(src["url"], timeout=45000, wait_until="domcontentloaded")
        meta["http_status"] = resp.status if resp else None
        meta["final_url"] = page.url
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception as e:
            meta["networkidle_error"] = str(e)
        page.wait_for_timeout(3500)
        title = page.title()
        html = page.content()
        meta["title"] = title
        meta["html_length"] = len(html)
        meta["blockers"] = detect_blockers(html, title)
        # Visible text snippet to characterize the page
        try:
            body_text = page.locator("body").inner_text(timeout=5000)
        except Exception:
            body_text = ""
        meta["text_head"] = body_text[:1200]

        # Snapshot
        html_path = OUT_DIR / f"{src['id']}.html"
        html_path.write_text(html, encoding="utf-8")
        png_path = OUT_DIR / f"{src['id']}.png"
        try:
            page.screenshot(path=str(png_path), full_page=False)
            meta["screenshot"] = png_path.name
        except Exception as e:
            meta["screenshot_error"] = str(e)
        meta["html_file"] = html_path.name

        # Capture form surfaces (helps build adapters)
        forms = page.evaluate("""() => {
            const out = [];
            for (const f of document.querySelectorAll('form')) {
                const inputs = [];
                for (const inp of f.querySelectorAll('input, select, textarea, button')) {
                    inputs.push({tag: inp.tagName.toLowerCase(),
                                 name: inp.name || '',
                                 id: inp.id || '',
                                 type: inp.type || '',
                                 value: inp.value || ''});
                }
                out.push({action: f.action || '', method: (f.method||'').toLowerCase(), id: f.id || '', name: f.name || '', inputs: inputs});
            }
            return out;
        }""")
        meta["forms"] = forms

        # Capture top-level links
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a[href]')).slice(0,40).map(a => ({href: a.href, text: (a.innerText||'').trim().slice(0,80)}))""")
        meta["links_sample"] = links
    finally:
        browser.close()
    return meta


def main():
    results = []
    with sync_playwright() as p:
        for src in SOURCES:
            print(f"[probe] {src['id']} -> {src['url']}", flush=True)
            try:
                m = probe(p, src)
            except Exception as exc:
                m = {"id": src["id"], "url": src["url"], "error": f"{type(exc).__name__}: {exc}"}
            print(f"  http={m.get('http_status')} title={m.get('title','')!r}  blocked={m.get('blockers',{}).get('looks_blocked')}", flush=True)
            results.append(m)
            time.sleep(1.5)
    (OUT_DIR / "probe_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {OUT_DIR / 'probe_results.json'}")


if __name__ == "__main__":
    main()
