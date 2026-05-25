"""Headless verification that the build-status banner is gone + no
internal commentary leaks into the rendered HTML."""
from __future__ import annotations
import http.server, socketserver, threading, time, re, os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
PORT = 8743


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **kw): pass


def serve():
    os.chdir(str(ROOT / "dashboard"))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Quiet) as srv:
        srv.serve_forever()


def main():
    threading.Thread(target=serve, daemon=True).start()
    time.sleep(0.6)

    BLOCKED = [
        "PARTIAL LEAD BOARD", "PARTIAL_BUILD", "SOURCE_LIMITED",
        "Cloudflare", "cf_clearance", "cf_chl", "cf-mitigated",
        "stealth", "staged pipeline", "playwright",
        "recon", "NYSCEF", "SearchIQS", "WebCivil", "WebSurrogate",
        "CAPTCHA", "Managed Challenge",
        "build_label_reason",
        "aarauctions", "greenecountyny.gov", "column.us",
        "EPCAD",
        # Internal pipeline labels
        "§17", "section_17", "PRIMARY_EVENT_SOURCE", "DEPLOY_OK",
    ]

    failures = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        page.goto(f"http://127.0.0.1:{PORT}/index.html",
                  wait_until="networkidle", timeout=30000)
        page.wait_for_selector('[data-ready="1"]', timeout=15000)

        # 1) Banner element must be present (kept for data-load errors)
        #    but hidden on a healthy load.
        banner = page.locator("#banner")
        hidden = banner.evaluate("(el) => el.hidden || el.hasAttribute('hidden')")
        text = banner.inner_text().strip()
        print(f"[1] banner.hidden={hidden}  banner.text={text!r}")
        if not hidden:
            failures.append("banner is visible on healthy load")
        if text:
            failures.append(f"banner has rendered text: {text!r}")

        # 2) Full rendered HTML must contain none of the blocked strings
        html = page.content()
        # The script tag for data.js is inline — exclude its content from the
        # check by reading only what the browser computed as TEXT.
        body_text = page.locator("body").inner_text(timeout=5000)
        # Detail panels are not opened — open one to expand the worst-case
        # rendered text surface, then re-grab body text.
        if page.locator(".lead").count() > 0:
            page.locator(".lead").first.click()
            page.wait_for_timeout(250)
            body_text = page.locator("body").inner_text(timeout=5000)
        print(f"[2] body_text length: {len(body_text)} chars  "
              f".lead nodes: {page.locator('.lead').count()}")

        for token in BLOCKED:
            if token.lower() in body_text.lower():
                snippet_idx = body_text.lower().find(token.lower())
                snippet = body_text[max(0, snippet_idx - 30): snippet_idx + 80]
                failures.append(f"blocked token {token!r} found near: {snippet!r}")

        # 3) topStats must NOT contain SOURCE_LIMITED-flavored copy
        topstats = page.locator("#topStats").inner_text()
        print(f"[3] topStats: {topstats!r}")
        if any(t.lower() in topstats.lower() for t in
               ["partial", "source_limited", "cloudflare", "stealth"]):
            failures.append(f"topStats contains internal label: {topstats!r}")

        # 4) Confirm dashboard still renders normally
        rc = page.locator("#rowCount").inner_text().strip()
        print(f"[4] rowCount: {rc!r}")
        if "1,210" not in rc and "1210" not in rc:
            failures.append(f"unexpected rowCount: {rc!r}")

        b.close()

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        raise SystemExit(1)
    print("\nALL BANNER + COMMENTARY CHECKS PASSED")


if __name__ == "__main__":
    main()
