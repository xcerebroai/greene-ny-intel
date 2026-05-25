"""Headless smoke test of dashboard/index.html with the live data.

Spawns a tiny static HTTP server, loads the dashboard in headless
chromium, and exercises:
  - Default landing render → row-count text + visible <div class='lead'> count
  - Click distress-signal 'lis_pendens' checkbox → confirm visible count drops
  - Click owner ESTATE → confirm count drops
  - Click 'Last 30 days' preset → confirm count matches payload's
    last_30_days_count
  - Click 'All records (default)' preset → resets to full count
  - 'Reset all filters' button → same

Requires playwright (already in .venv per prior phases).
"""
from __future__ import annotations
import http.server, socketserver, threading, time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
PORT = 8742


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **kw): pass


def serve():
    import os
    os.chdir(str(ROOT / "dashboard"))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Quiet) as srv:
        srv.serve_forever()


def main():
    th = threading.Thread(target=serve, daemon=True)
    th.start()
    time.sleep(0.6)
    failures = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page()
        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="networkidle", timeout=30000)
        page.wait_for_selector('[data-ready="1"]', timeout=15000)
        # 1) row count text
        row_text = page.locator("#rowCount").inner_text().strip()
        print(f"[1] Default row count text: {row_text!r}")
        # 2) visible .lead rows (windowed at PAGE=60)
        lead_n = page.locator(".lead").count()
        print(f"[1] Visible .lead nodes (windowed): {lead_n}")
        if "1,210" not in row_text and "1210" not in row_text:
            failures.append(f"Default row text missing 1,210: {row_text!r}")

        # 3) Click lis_pendens checkbox
        cbx = page.locator('input[data-sig="lis_pendens"]')
        if cbx.count() == 0:
            failures.append("lis_pendens checkbox not found")
        else:
            cbx.check()
            page.wait_for_timeout(250)
            row_text2 = page.locator("#rowCount").inner_text().strip()
            print(f"[2] After lis_pendens check: {row_text2}")
            if "4" not in row_text2.split(" of ")[0]:
                failures.append(f"lis_pendens click: expected 4, got {row_text2!r}")
            cbx.uncheck(); page.wait_for_timeout(150)

        # 4) Click owner_type ESTATE
        own = page.locator('input[data-own="ESTATE"]')
        if own.count() == 0:
            failures.append("ESTATE owner checkbox not found")
        else:
            own.check(); page.wait_for_timeout(250)
            row_text3 = page.locator("#rowCount").inner_text().strip()
            print(f"[3] After ESTATE check: {row_text3}")
            if "23" not in row_text3.split(" of ")[0]:
                failures.append(f"ESTATE click: expected 23, got {row_text3!r}")
            own.uncheck(); page.wait_for_timeout(150)

        # 5) Click 'Last 30 days' preset
        last30 = page.locator(".preset", has_text="Last 30 days")
        if last30.count() == 0:
            failures.append("'Last 30 days' preset button not found")
        else:
            last30.click(); page.wait_for_timeout(250)
            row_text4 = page.locator("#rowCount").inner_text().strip()
            print(f"[4] After Last-30-days preset: {row_text4}")
            if "18" not in row_text4.split(" of ")[0]:
                failures.append(f"Last 30 days: expected 18, got {row_text4!r}")

        # 6) Click 'All records (default)' preset → reset
        allp = page.locator(".preset", has_text="All records")
        if allp.count() == 0:
            failures.append("'All records' preset button not found")
        else:
            allp.click(); page.wait_for_timeout(250)
            row_text5 = page.locator("#rowCount").inner_text().strip()
            print(f"[5] After All-records reset: {row_text5}")
            if "1,210" not in row_text5 and "1210" not in row_text5:
                failures.append(f"All-records reset: expected 1,210, got {row_text5!r}")

        # 7) Reset button
        reset = page.locator("#resetBtn")
        reset.click(); page.wait_for_timeout(250)
        row_text6 = page.locator("#rowCount").inner_text().strip()
        print(f"[6] After Reset button: {row_text6}")
        if "1,210" not in row_text6 and "1210" not in row_text6:
            failures.append(f"Reset: expected 1,210, got {row_text6!r}")

        # 8) EPCAD must not appear anywhere on the page
        html = page.content()
        if "EPCAD" in html.upper():
            failures.append("'EPCAD' literal string found in rendered HTML")
        else:
            print("[7] no EPCAD reference in rendered HTML ✓")

        # 9) Top-of-list default sort should NOT lead with ESTATE
        if page.locator(".lead").count() > 0:
            first_otype = page.locator(".lead").first.locator(".otype").inner_text().strip()
            print(f"[8] First-row owner_type after reset: {first_otype}")
            if first_otype == "ESTATE":
                failures.append("Default sort leads with ESTATE row")
        b.close()
    if failures:
        print("\nFAILURES:")
        for f in failures: print(f"  - {f}")
        raise SystemExit(1)
    print("\nALL SMOKE CHECKS PASSED")


if __name__ == "__main__":
    main()
