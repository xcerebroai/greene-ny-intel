"""Warmed-session attempt at WebCivil Supreme search submit.

Hypothesis: Cloudflare Managed Challenge fires on cold POSTs but accepts
already-cookied sessions that have browsed the eCourts site. Walk through
the site like a user, then submit.
"""
from __future__ import annotations
import json, time
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

OUT_DIR = Path(__file__).resolve().parent
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def settle(page, ms=10000, extra=2000):
    try: page.wait_for_load_state("networkidle", timeout=ms)
    except Exception: pass
    page.wait_for_timeout(extra)


def main():
    out = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
            args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(user_agent=USER_AGENT,
            viewport={"width": 1400, "height": 900}, locale="en-US",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
            })
        page = ctx.new_page()
        Stealth().apply_stealth_sync(page)
        try:
            # Walk 1: ecourts home
            page.goto("https://iapps.courts.state.ny.us/webcivil/ecourtsMain",
                      wait_until="domcontentloaded", timeout=45000)
            settle(page); time.sleep(2)
            out["step1_title"] = page.title()

            # Walk 2: FCASMain (WebCivil Supreme home)
            page.goto("https://iapps.courts.state.ny.us/webcivil/FCASMain",
                      wait_until="domcontentloaded", timeout=45000)
            settle(page); time.sleep(2)
            out["step2_title"] = page.title()

            # Walk 3: terms of use
            page.goto("https://iapps.courts.state.ny.us/webcivil/TermsOfUse",
                      wait_until="domcontentloaded", timeout=45000)
            settle(page); time.sleep(2)
            out["step3_title"] = page.title()

            # Walk 4: Party Search page
            page.goto("https://iapps.courts.state.ny.us/webcivil/FCASSearch?param=P",
                      wait_until="domcontentloaded", timeout=45000)
            settle(page); time.sleep(3)
            out["step4_title"] = page.title()
            # Some realistic mouse / scroll
            try:
                page.mouse.move(400, 200, steps=10); time.sleep(0.4)
                page.mouse.move(700, 500, steps=8);  time.sleep(0.4)
                page.evaluate("window.scrollBy(0, 200)"); time.sleep(0.6)
            except Exception:
                pass
            # Fill carefully with delays
            page.locator("input[name=txtPlaintiffLname]").first.click(timeout=5000); time.sleep(0.5)
            page.type("input[name=txtPlaintiffLname]", "WELLS FARGO", delay=80); time.sleep(0.5)
            # Court multi-select via JS
            page.evaluate("""(vals) => {
                const sel = document.querySelector('select[name=cboCourt]');
                for (const opt of sel.options) opt.selected = vals.includes(opt.value);
                sel.dispatchEvent(new Event('change', {bubbles:true}));
            }""", ["37","38"])
            time.sleep(0.5)
            page.select_option("select[name=cboYearOfFiling]", "2025"); time.sleep(0.5)
            page.locator("input[name=rbStatus][value=all]").first.check(); time.sleep(0.3)
            page.locator("input[name=rdRepresents][value=AllRoles]").first.check(); time.sleep(0.4)
            # Scroll to submit button, hover, click
            page.locator("input[name=btnFindCase]").first.scroll_into_view_if_needed()
            time.sleep(0.6)
            page.locator("input[name=btnFindCase]").first.hover()
            time.sleep(0.4)
            page.locator("input[name=btnFindCase]").first.click()
            settle(page, ms=25000, extra=5000)
            out["submit_title"] = page.title()
            out["submit_url"] = page.url
            html = page.content()
            out["submit_html_len"] = len(html)
            out["submit_challenge"] = "just a moment" in (out["submit_title"] or '').lower()
            # If challenge, wait longer
            if out["submit_challenge"]:
                print("  cf challenge fired — waiting 60s for auto-resolve ...")
                deadline = time.time() + 60
                iters = 0
                while time.time() < deadline:
                    iters += 1
                    page.wait_for_timeout(3000)
                    t = page.title()
                    if "just a moment" not in (t or '').lower():
                        out["resolved_after_wait"] = True
                        out["final_title"] = t
                        out["wait_iterations"] = iters
                        break
                else:
                    out["resolved_after_wait"] = False
                    out["wait_iterations"] = iters
                    out["final_title"] = page.title()
            (OUT_DIR / "wcs_warmed.html").write_text(page.content(), encoding="utf-8")
            try: page.screenshot(path=str(OUT_DIR / "wcs_warmed.png"))
            except Exception: pass
            # Try parse any tables that exist
            tbl = page.evaluate("""() => Array.from(document.querySelectorAll('table')).map(t => ({
                rows: t.querySelectorAll('tr').length,
                headers: Array.from(t.querySelectorAll('thead th, tr:first-child th, tr:first-child td')).map(c=>(c.innerText||'').trim()).slice(0,15),
                sampleRows: Array.from(t.querySelectorAll('tbody tr, tr')).slice(0,5).map(r => Array.from(r.querySelectorAll('td,th')).map(c => (c.innerText||'').trim()).slice(0,15))
            })).filter(t=>t.rows>0)""")
            out["tables"] = tbl
        except Exception as exc:
            out["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            browser.close()
    (OUT_DIR / "wcs_warmed.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k:v for k,v in out.items() if k != 'tables'}, indent=2, default=str)[:2000])
    print('tables headers:', [t.get('headers') for t in (out.get('tables') or [])])
    print('table rows:', [t.get('rows') for t in (out.get('tables') or [])])

if __name__ == "__main__":
    main()
