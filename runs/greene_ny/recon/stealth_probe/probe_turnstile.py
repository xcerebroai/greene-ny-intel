"""Turnstile-aware probe.

Each gated source: load, then poll for Turnstile to auto-resolve. If a checkbox
challenge iframe is present, attempt a click. Wait up to N seconds. Report the
outcome honestly.

Outcomes per source:
  - auto_pass           — stealth bypassed; no Turnstile ever shown
  - turnstile_passed    — Turnstile resolved (with or without click)
  - turnstile_blocked   — Turnstile present and unresolved after wait
"""
from __future__ import annotations
import json, time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout
from playwright_stealth import Stealth

OUT_DIR = Path(__file__).resolve().parent
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def new_browser(p, headless=True):
    browser = p.chromium.launch(headless=headless,
        args=["--disable-blink-features=AutomationControlled"])
    ctx = browser.new_context(user_agent=USER_AGENT,
        viewport={"width": 1400, "height": 900}, locale="en-US")
    page = ctx.new_page()
    Stealth().apply_stealth_sync(page)
    return browser, ctx, page


def detect_state(page: Page) -> dict:
    title = (page.title() or "")
    html = page.content()
    lower = html.lower()
    is_challenge_title = "just a moment" in title.lower() or "verifying" in title.lower()
    has_turnstile_widget = ("turnstile" in lower or "challenges.cloudflare.com" in lower)
    cf_chl_input = page.locator("input[name='cf-turnstile-response']").count()
    cf_iframes = page.locator("iframe[src*='challenges.cloudflare.com']").count()
    return {
        "title": title,
        "url": page.url,
        "challenge_title": is_challenge_title,
        "has_turnstile_widget": has_turnstile_widget,
        "cf_iframes": cf_iframes,
        "cf_chl_input_count": cf_chl_input,
        "looks_blocked": is_challenge_title,
        "html_len": len(html),
    }


def wait_for_turnstile_resolve(page: Page, total_wait_s: int = 35) -> dict:
    """Poll for Turnstile to auto-resolve. If a checkbox iframe is reachable,
    click inside it. Return final state."""
    deadline = time.time() + total_wait_s
    clicked = False
    iterations = 0
    while time.time() < deadline:
        iterations += 1
        state = detect_state(page)
        if not state["challenge_title"]:
            state["resolved"] = True
            state["clicked"] = clicked
            state["iterations"] = iterations
            return state
        # Attempt one click on the challenge iframe checkbox
        if not clicked:
            try:
                fr = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
                # The checkbox often has role=checkbox or an input with label
                # Try click the iframe body center as fallback
                try:
                    fr.locator("input[type=checkbox]").first.click(timeout=2500)
                    clicked = True
                except Exception:
                    pass
                if not clicked:
                    try:
                        fr.locator("label").first.click(timeout=2500)
                        clicked = True
                    except Exception:
                        pass
            except Exception:
                pass
        page.wait_for_timeout(2000)
    state = detect_state(page)
    state["resolved"] = not state["challenge_title"]
    state["clicked"] = clicked
    state["iterations"] = iterations
    return state


SOURCES = [
    ("searchiqs_landing",
     "https://www.searchiqs.com/nygre/",
     None),
    ("searchiqs_guest_click",
     "https://www.searchiqs.com/nygre/",
     "click_guest"),
    ("nyscef_case_search",
     "https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name",
     None),
    ("nyscef_submit",
     "https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name",
     "submit_smith"),
    ("websurrogate_root",
     "https://websurrogates.nycourts.gov/",
     None),
    ("websurrogate_case_search",
     "https://websurrogates.nycourts.gov/Search/Cases",
     None),
    ("webcivil_supreme_index",
     "https://iapps.courts.state.ny.us/webcivil/FCASSearch?param=I",
     None),
    ("webcivil_supreme_party",
     "https://iapps.courts.state.ny.us/webcivil/FCASSearch?param=P",
     None),
]


def run_one(p, src_id: str, url: str, action: str | None) -> dict:
    out = {"id": src_id, "url": url, "action": action}
    browser, ctx, page = new_browser(p)
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        out["http_status"] = resp.status if resp else None
        # Brief settle
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(2500)
        # If turnstile fires, wait for it
        state1 = wait_for_turnstile_resolve(page, total_wait_s=30)
        out["initial_state"] = state1
        if action == "click_guest":
            try:
                page.locator("#btnGuestLogin").first.click(timeout=5000)
            except Exception as e:
                out["action_error"] = str(e)
            page.wait_for_timeout(3000)
            state2 = wait_for_turnstile_resolve(page, total_wait_s=40)
            out["post_action_state"] = state2
        elif action == "submit_smith":
            try:
                page.select_option("select[name=txtCounty]", "20")  # Greene
            except Exception as e:
                out["county_select_error"] = str(e)
            try:
                page.fill("input[name=txtPartyLastName]", "SMITH")
            except Exception:
                pass
            try:
                page.click("button:has-text('Search')", timeout=5000)
            except Exception as e:
                out["submit_error"] = str(e)
            page.wait_for_timeout(3000)
            state2 = wait_for_turnstile_resolve(page, total_wait_s=40)
            out["post_action_state"] = state2

        # Snapshot end state
        end_html = page.content()
        (OUT_DIR / f"ts_{src_id}.html").write_text(end_html, encoding="utf-8")
        try:
            page.screenshot(path=str(OUT_DIR / f"ts_{src_id}.png"), full_page=False)
        except Exception:
            pass
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        browser.close()
    return out


def main():
    results = []
    with sync_playwright() as p:
        for src_id, url, action in SOURCES:
            print(f"[ts-probe] {src_id} action={action} ...", flush=True)
            r = run_one(p, src_id, url, action)
            print(f"  initial: blocked={r.get('initial_state',{}).get('looks_blocked')} title={r.get('initial_state',{}).get('title')!r}", flush=True)
            if 'post_action_state' in r:
                ps = r['post_action_state']
                print(f"  post:    blocked={ps.get('looks_blocked')} resolved={ps.get('resolved')} clicked={ps.get('clicked')} url={ps.get('url')}", flush=True)
            results.append(r)
            time.sleep(1.0)
    (OUT_DIR / "turnstile_results.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {OUT_DIR / 'turnstile_results.json'}")


if __name__ == "__main__":
    main()
