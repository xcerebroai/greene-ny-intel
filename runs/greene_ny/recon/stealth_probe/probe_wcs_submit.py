"""Confirm WebCivil Supreme submit works without reCAPTCHA — and capture the
result table shape so the adapter can parse it."""
from __future__ import annotations
import json, time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

OUT_DIR = Path(__file__).resolve().parent
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

GREENE_SUPREME = "38"
GREENE_COUNTY  = "37"


def new_browser(p):
    browser = p.chromium.launch(headless=True,
        args=["--disable-blink-features=AutomationControlled"])
    ctx = browser.new_context(user_agent=USER_AGENT,
        viewport={"width": 1400, "height": 900}, locale="en-US")
    page = ctx.new_page()
    Stealth().apply_stealth_sync(page)
    return browser, ctx, page


def settle(page, ms=10000, extra=2500):
    try: page.wait_for_load_state("networkidle", timeout=ms)
    except Exception: pass
    page.wait_for_timeout(extra)


def attempt(plaintiff_last: str, year: str = "2025") -> dict:
    out = {"plaintiff": plaintiff_last, "year": year}
    with sync_playwright() as p:
        browser, ctx, page = new_browser(p)
        try:
            page.goto("https://iapps.courts.state.ny.us/webcivil/FCASSearch?param=P",
                      wait_until="domcontentloaded", timeout=45000)
            settle(page)
            # Fill plaintiff
            page.fill("input[name=txtPlaintiffLname]", plaintiff_last)
            # Select Greene Supreme + Greene County in the multi-select
            page.evaluate("""(vals) => {
                const sel = document.querySelector('select[name=cboCourt]');
                if (!sel) return;
                for (const opt of sel.options) opt.selected = vals.includes(opt.value);
                sel.dispatchEvent(new Event('change', {bubbles:true}));
            }""", [GREENE_SUPREME, GREENE_COUNTY])
            # Year of filing
            try:
                page.select_option("select[name=cboYearOfFiling]", year)
            except Exception:
                pass
            # Status = all
            try: page.locator("input[name=rbStatus][value=all]").first.check()
            except Exception: pass
            # Represents = AllRoles
            try: page.locator("input[name=rdRepresents][value=AllRoles]").first.check()
            except Exception: pass
            # Submit
            page.locator("input[name=btnFindCase]").first.click()
            settle(page, ms=18000, extra=4000)
            out["url"] = page.url
            out["title"] = page.title()
            html = page.content()
            out["html_len"] = len(html)
            # Detect challenge
            out["challenge"] = ("just a moment" in (page.title() or '').lower() or
                                "turnstile" in html.lower() or
                                "cf-challenge" in html.lower())
            # Look for recaptcha challenge dialog
            out["recaptcha_dialog_count"] = page.locator("iframe[src*='recaptcha'][title*='challenge']").count()
            # Detect "Validation failed" / error msg
            err_text = ""
            for sel in [".errMsg",".error","#errorMsg",".errorMessage"]:
                try:
                    e = page.locator(sel)
                    if e.count() > 0:
                        err_text += "[" + sel + "]" + (e.first.inner_text(timeout=2000) or "") + "; "
                except Exception:
                    pass
            out["error_text"] = err_text[:500]
            # Parse table
            tbl = page.evaluate("""() => Array.from(document.querySelectorAll('table')).map(t => ({
                rows: t.querySelectorAll('tr').length,
                headers: Array.from(t.querySelectorAll('thead th, tr:first-child th, tr:first-child td')).map(c=>(c.innerText||'').trim()).slice(0,15),
                sampleRows: Array.from(t.querySelectorAll('tbody tr, tr')).slice(0,5).map(r => Array.from(r.querySelectorAll('td,th')).map(c => (c.innerText||'').trim()).slice(0,15))
            })).filter(t=>t.rows>0)""")
            out["tables"] = tbl
            # Look for pagination / total-found banner
            try:
                body_text = page.locator("body").inner_text(timeout=5000)
            except Exception:
                body_text = ""
            out["body_head"] = body_text[:2500].replace('\n',' | ')
            fname = f"wcs_submit_{plaintiff_last.replace(' ','_')}_{year}.html"
            (OUT_DIR / fname).write_text(html, encoding="utf-8")
            out["html_file"] = fname
            try: page.screenshot(path=str(OUT_DIR / fname.replace('.html','.png')))
            except Exception: pass
        except Exception as exc:
            out["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            browser.close()
    return out


def main():
    # Try a few well-known foreclosure plaintiffs to confirm submit works
    queries = [
        ("BANK", "2025"),
        ("WELLS FARGO", "2025"),
        ("US BANK", "2025"),
        ("FREEDOM MORTGAGE", "2025"),
    ]
    results = []
    for last, yr in queries:
        print(f"[wcs] {last} year={yr} ...", flush=True)
        r = attempt(last, yr)
        print(f"   url={r.get('url')}  challenge={r.get('challenge')}  rows-in-largest-table={(max((t['rows'] for t in r.get('tables') or [{'rows':0}]), default=0))}  error_text={r.get('error_text')[:120]!r}",
              flush=True)
        results.append(r)
        time.sleep(1.5)
    (OUT_DIR / "wcs_submit.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print("\nWrote", OUT_DIR / "wcs_submit.json")


if __name__ == "__main__":
    main()
