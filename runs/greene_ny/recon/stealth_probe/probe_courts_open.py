"""Deep probe of the COURT surfaces that are stealth-reachable.

  - WebCivil Supreme — case search by county + case type. Supreme civil
    court data (foreclosure cases = "Mortgage Foreclosure" or "RPAPL"
    case types). https://iapps.courts.state.ny.us/webcivil/FCASSearch
  - WebSurrogate — surrogate court case search (probate). Statewide.
    https://websurrogates.nycourts.gov/

For each: characterize the search forms, list dropdown options (county,
case type), submit a test query and capture the result table.
"""
from __future__ import annotations
import json, time
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


def settle(page, ms=10000, extra=2500):
    try:
        page.wait_for_load_state("networkidle", timeout=ms)
    except Exception:
        pass
    page.wait_for_timeout(extra)


def capture_forms(page) -> list:
    return page.evaluate("""() => Array.from(document.querySelectorAll('form')).map(f => ({
        action: f.action, method: f.method, id: f.id, name: f.name,
        inputs: Array.from(f.querySelectorAll('input,select,textarea,button')).map(i => ({
            tag: i.tagName.toLowerCase(), id: i.id || '', name: i.name || '',
            type: i.type || '', value: (i.value||'').toString().slice(0,40)
        })),
        selectOptions: Array.from(f.querySelectorAll('select')).map(s => ({
            id: s.id, name: s.name,
            options: Array.from(s.options).slice(0,200).map(o => ({v: o.value, t: (o.text||'').trim()}))
        }))
    }))""")


def capture_tables(page) -> list:
    return page.evaluate("""() => Array.from(document.querySelectorAll('table')).map(t => ({
        rows: t.querySelectorAll('tr').length,
        headers: Array.from(t.querySelectorAll('thead th, tr:first-child th, tr:first-child td')).map(c=>(c.innerText||'').trim()).slice(0,20),
        firstRows: Array.from(t.querySelectorAll('tbody tr, tr')).slice(0, 6).map(r => Array.from(r.querySelectorAll('td,th')).map(c => (c.innerText||'').trim()).slice(0,12))
    })).filter(t => t.rows > 0)""")


# --- WebCivil Supreme ---

def probe_webcivil_supreme_index(p) -> dict:
    """Index Search = look up a specific case by Court + Index Number; not
    a bulk surface. We'll use it to confirm court list / county codes."""
    browser, ctx, page = new_browser(p)
    out = {"id": "webcivil_supreme_index"}
    try:
        page.goto("https://iapps.courts.state.ny.us/webcivil/FCASSearch?param=I",
                  wait_until="domcontentloaded", timeout=45000)
        settle(page)
        out["title"] = page.title()
        out["url"] = page.url
        out["forms"] = capture_forms(page)
        (OUT_DIR / "wcs_index.html").write_text(page.content(), encoding="utf-8")
        try: page.screenshot(path=str(OUT_DIR / "wcs_index.png"))
        except Exception: pass
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def probe_webcivil_supreme_party(p) -> dict:
    """Party Search — bulk-ish; submit a county+name query."""
    browser, ctx, page = new_browser(p)
    out = {"id": "webcivil_supreme_party"}
    try:
        page.goto("https://iapps.courts.state.ny.us/webcivil/FCASSearch?param=P",
                  wait_until="domcontentloaded", timeout=45000)
        settle(page)
        out["title_initial"] = page.title()
        out["forms_initial"] = capture_forms(page)
        (OUT_DIR / "wcs_party_initial.html").write_text(page.content(), encoding="utf-8")
        try: page.screenshot(path=str(OUT_DIR / "wcs_party_initial.png"))
        except Exception: pass
    except Exception as exc:
        out["error_initial"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def probe_webcivil_documents(p) -> dict:
    """Document Search — by index number + date range — confirms FCAS doc-image surface."""
    browser, ctx, page = new_browser(p)
    out = {"id": "webcivil_supreme_documents"}
    try:
        page.goto("https://iapps.courts.state.ny.us/webcivil/FCASDocumentSearch",
                  wait_until="domcontentloaded", timeout=45000)
        settle(page)
        out["title"] = page.title()
        out["url"] = page.url
        out["forms"] = capture_forms(page)
        (OUT_DIR / "wcs_documents.html").write_text(page.content(), encoding="utf-8")
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


# --- WebSurrogate ---

def probe_websurrogate(p) -> dict:
    browser, ctx, page = new_browser(p)
    out = {"id": "websurrogate"}
    try:
        page.goto("https://websurrogates.nycourts.gov/", wait_until="domcontentloaded", timeout=45000)
        settle(page)
        out["title_welcome"] = page.title()
        out["url_welcome"] = page.url
        # Click into search or "Continue" / "I agree"
        for sel in ["a:has-text('Search Cases')",
                    "a:has-text('Search')",
                    "button:has-text('Continue')",
                    "button:has-text('Accept')",
                    "input[value='Accept']",
                    "a:has-text('I Agree')",
                    "a:has-text('Agree')"]:
            try:
                cands = page.locator(sel)
                if cands.count() > 0:
                    out.setdefault("click_attempts", []).append({"sel": sel, "count": cands.count(), "text": cands.first.inner_text(timeout=2000)})
            except Exception:
                pass
        # Navigate to /Search/Cases — the case search surface
        try:
            page.goto("https://websurrogates.nycourts.gov/Search/Cases", wait_until="domcontentloaded", timeout=45000)
            settle(page)
        except Exception as e:
            out["search_nav_error"] = str(e)
        out["title_search"] = page.title()
        out["url_search"] = page.url
        out["forms_search"] = capture_forms(page)
        out["text_head"] = (page.locator('body').inner_text(timeout=4000) if True else '')[:2000]
        (OUT_DIR / "wsurr_search.html").write_text(page.content(), encoding="utf-8")
        try: page.screenshot(path=str(OUT_DIR / "wsurr_search.png"))
        except Exception: pass
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def main():
    results = {}
    with sync_playwright() as p:
        print("[courts] webcivil_supreme index ..."); results["wcs_index"] = probe_webcivil_supreme_index(p); time.sleep(0.8)
        print("[courts] webcivil_supreme party ..."); results["wcs_party"] = probe_webcivil_supreme_party(p); time.sleep(0.8)
        print("[courts] webcivil_supreme documents ..."); results["wcs_documents"] = probe_webcivil_documents(p); time.sleep(0.8)
        print("[courts] websurrogate ..."); results["websurrogate"] = probe_websurrogate(p)
    (OUT_DIR / "courts_open.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {OUT_DIR / 'courts_open.json'}")


if __name__ == "__main__":
    main()
