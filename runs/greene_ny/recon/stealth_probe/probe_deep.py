"""Phase 1 deep probe — drive each gated source past its first surface.

  1. SearchIQS: click "Search Records as Guest" / btnGuestLogin → snapshot
     the post-login search panel. Then attempt a recorded-date search and
     capture the result table.
  2. NYSCEF CaseSearch: select Greene + Real Property / Commercial-Foreclosure
     / Tax Certiorari case types, submit. Watch whether reCAPTCHA fires.
  3. WebCivil Supreme: try a county + case-type query.
  4. WebSurrogate: probe the surrogate-court statewide search.
"""
from __future__ import annotations
import json, re, time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

OUT_DIR = Path(__file__).resolve().parent
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def new_browser(p):
    browser = p.chromium.launch(headless=True,
        args=["--disable-blink-features=AutomationControlled"])
    ctx = browser.new_context(user_agent=USER_AGENT,
        viewport={"width": 1400, "height": 900}, locale="en-US")
    page = ctx.new_page()
    Stealth().apply_stealth_sync(page)
    return browser, ctx, page


def snapshot(page, name: str) -> dict:
    html_path = OUT_DIR / f"{name}.html"
    png_path = OUT_DIR / f"{name}.png"
    html = page.content()
    html_path.write_text(html, encoding="utf-8")
    try:
        page.screenshot(path=str(png_path), full_page=False)
    except Exception:
        pass
    try:
        text = page.locator("body").inner_text(timeout=4000)
    except Exception:
        text = ""
    return {
        "name": name,
        "url": page.url,
        "title": page.title(),
        "html_len": len(html),
        "text_head": text[:1500],
        "has_recaptcha_iframe": page.locator("iframe[src*='recaptcha']").count(),
        "has_turnstile": "turnstile" in html.lower() or "cf-challenge" in html.lower(),
    }


def safe_settle(page, ms=12000, extra=2500):
    try:
        page.wait_for_load_state("networkidle", timeout=ms)
    except Exception:
        pass
    page.wait_for_timeout(extra)


def probe_searchiqs(p) -> dict:
    browser, ctx, page = new_browser(p)
    out: dict = {"id": "searchiqs"}
    try:
        page.goto("https://www.searchiqs.com/nygre/", wait_until="domcontentloaded", timeout=45000)
        safe_settle(page)
        out["landing"] = snapshot(page, "iqs_01_landing")
        # Click Guest Login
        guest = page.locator("#btnGuestLogin")
        out["guest_btn_count"] = guest.count()
        if guest.count() > 0:
            guest.first.click()
            safe_settle(page)
            out["after_guest"] = snapshot(page, "iqs_02_after_guest")
            # Look for menu links, date picker, party search
            links = page.evaluate("""() => Array.from(document.querySelectorAll('a')).map(a => ({text: (a.innerText||'').trim(), href: a.href})).filter(o => o.text.length)""")
            out["after_guest_links"] = links[:60]
            # Detect document-type dropdown / date search
            selects = page.evaluate("""() => Array.from(document.querySelectorAll('select')).map(s => ({id: s.id, name: s.name, options: Array.from(s.options).slice(0,80).map(o => ({v: o.value, t: o.text}))}))""")
            out["after_guest_selects"] = selects
            inputs = page.evaluate("""() => Array.from(document.querySelectorAll('input, textarea, button')).map(i => ({tag: i.tagName.toLowerCase(), id: i.id, name: i.name, type: i.type, value: (i.value||'').slice(0,40)}))""")
            out["after_guest_inputs"] = inputs[:80]
            # Try clicking "Search Documents" / advanced if present
            for sel in ["a:has-text('Search')","a:has-text('Document')","a:has-text('Recorded')","a:has-text('Land')"]:
                try:
                    cands = page.locator(sel)
                    n = cands.count()
                    if n:
                        out.setdefault("nav_links_found", []).append({"sel": sel, "count": n, "first_text": cands.first.inner_text(timeout=2000)})
                except Exception:
                    pass
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def probe_nyscef_query(p) -> dict:
    browser, ctx, page = new_browser(p)
    out: dict = {"id": "nyscef_query"}
    try:
        page.goto("https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name",
                  wait_until="domcontentloaded", timeout=45000)
        safe_settle(page)
        out["initial"] = snapshot(page, "nyscef_01_initial")
        # Read out the county + case-type options
        opts = page.evaluate("""() => {
            const get = sel => { const el = document.querySelector(sel); return el ? Array.from(el.options).map(o => ({v:o.value, t:o.text})) : null; };
            return { county: get('select[name=txtCounty]'), caseType: get('select[name=txtCaseType]') };
        }""")
        out["select_options"] = opts
        # Pick Greene + party last name + Real-property / Foreclosure case type if present
        # Locate option values by text match (defensive)
        greene_v = next((o['v'] for o in (opts.get('county') or []) if 'Greene' in (o['t'] or '')), None)
        out["greene_option_value"] = greene_v
        if greene_v:
            page.select_option("select[name=txtCounty]", greene_v)
        # Wide date window: blank → all-time
        # Submit blank-name with a wildcard? NYSCEF requires party fields. Try a common surname.
        page.fill("input[name=txtPartyLastName]", "SMITH")
        # Wait for any recaptcha widget render
        page.wait_for_timeout(1500)
        out["pre_submit"] = snapshot(page, "nyscef_02_pre_submit")
        # Submit
        try:
            page.click("button:has-text('Search')", timeout=8000)
        except Exception as e:
            out["submit_error"] = f"click: {e}"
        safe_settle(page, ms=18000, extra=3500)
        out["post_submit"] = snapshot(page, "nyscef_03_post_submit")
        # Detect a result table
        tbl = page.evaluate("""() => {
            const tables = Array.from(document.querySelectorAll('table'));
            const out = [];
            for (const t of tables) {
                const headers = Array.from(t.querySelectorAll('thead th, tr:first-child th, tr:first-child td')).map(c => (c.innerText||'').trim());
                const bodyRows = t.querySelectorAll('tbody tr').length || Math.max(0, t.querySelectorAll('tr').length - 1);
                if (headers.length) out.push({headers, bodyRows});
            }
            return out;
        }""")
        out["tables"] = tbl
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def probe_websurrogate(p) -> dict:
    browser, ctx, page = new_browser(p)
    out: dict = {"id": "websurrogate"}
    try:
        page.goto("https://websurrogates.nycourts.gov/", wait_until="domcontentloaded", timeout=45000)
        safe_settle(page)
        out["initial"] = snapshot(page, "wsurr_01_initial")
        # Capture forms + links
        forms = page.evaluate("""() => Array.from(document.querySelectorAll('form')).map(f => ({action: f.action, method: f.method, inputs: Array.from(f.querySelectorAll('input,select,textarea,button')).map(i=>({tag:i.tagName.toLowerCase(), id:i.id, name:i.name, type:i.type}))}))""")
        out["forms"] = forms
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a')).slice(0,50).map(a=>({text:(a.innerText||'').trim().slice(0,80), href:a.href}))""")
        out["links"] = links
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def probe_webcivil_supreme(p) -> dict:
    browser, ctx, page = new_browser(p)
    out: dict = {"id": "webcivil_supreme"}
    try:
        page.goto("https://iapps.courts.state.ny.us/webcivil/FCASMain",
                  wait_until="domcontentloaded", timeout=45000)
        safe_settle(page)
        out["initial"] = snapshot(page, "wcs_01_initial")
        links = page.evaluate("""() => Array.from(document.querySelectorAll('a')).slice(0,50).map(a=>({text:(a.innerText||'').trim().slice(0,80), href:a.href}))""")
        out["links"] = links
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def main():
    results: dict = {}
    with sync_playwright() as p:
        print("[deep] searchiqs ...", flush=True)
        results["searchiqs"] = probe_searchiqs(p); time.sleep(1)
        print("[deep] nyscef_query ...", flush=True)
        results["nyscef_query"] = probe_nyscef_query(p); time.sleep(1)
        print("[deep] websurrogate ...", flush=True)
        results["websurrogate"] = probe_websurrogate(p); time.sleep(1)
        print("[deep] webcivil_supreme ...", flush=True)
        results["webcivil_supreme"] = probe_webcivil_supreme(p)
    (OUT_DIR / "probe_deep.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print("\nWrote", OUT_DIR / "probe_deep.json")


if __name__ == "__main__":
    main()
