"""Optional real-browser checks; needs Playwright Python and Chromium.

Run after both build modes. Starts temporary loopback servers and closes them.
Does not publish a preview or contact external services.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(directory)))
    Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def check():
    preview, base = serve(ROOT / "_preview")
    production, public = serve(ROOT / "_site")
    shots = ROOT / "docs/previews"
    shots.mkdir(exist_ok=True, parents=True)
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            context = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            def visit(path):
                response = page.goto(base + path, wait_until="networkidle")
                assert response.status == 200, path
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), path
            visit("/index.html")
            assert page.locator(".field-card").count() == 8
            assert page.locator(".nav-group li a").count() == 51
            assert page.locator(".feature-image img").evaluate("img => img.complete && img.naturalWidth > 0")
            page.screenshot(path=str(shots / "home-desktop.png"), full_page=True)
            page.locator(".nav-group summary").nth(1).click()
            assert page.locator(".nav-group").nth(1).get_attribute("open") is not None
            page.keyboard.press("Escape")
            assert page.locator(".nav-group[open]").count() == 0
            visit("/categories/cities/europe/index.html")
            assert page.locator(".story-card").count() == 1
            page.locator(".story-card a").click()
            page.wait_for_load_state("networkidle")
            assert "/stories/venice-winged-lion/" in page.url
            assert page.locator(".prose h2").count() == 3
            assert page.locator(".article-image img").evaluate("img => img.naturalWidth > 0")
            assert "실제 조각상" in page.locator("figcaption").inner_text()
            page.screenshot(path=str(shots / "story-desktop.png"), full_page=True)
            page.locator(".article-toc a").last.click()
            page.wait_for_timeout(500)
            assert "#part-3" in page.url
            visit("/search.html?q=베네치아")
            page.wait_for_function("document.querySelector('#search-status').textContent.includes('찾았습니다')")
            assert page.locator("#search-results .story-card").count() == 1
            page.locator("#query").fill("기념품")
            assert page.locator("#search-results .story-card").count() == 1
            page.locator("#category-filter").select_option("history")
            assert page.locator("#search-empty").is_visible()
            page.locator("#reset-search").click()
            assert page.locator("#search-results .story-card").count() == 1
            page.locator("#query").fill('<img src=x onerror=alert(1)>')
            assert page.locator("#search-empty").is_visible()
            assert page.locator("img[onerror]").count() == 0
            visit("/categories/history/korea/index.html")
            assert page.locator(".empty-state").is_visible()
            assert page.locator(".story-card").count() == 0
            mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
            m = mobile.new_page()
            m.on("pageerror", lambda error: errors.append(str(error)))
            m.goto(base + "/index.html", wait_until="networkidle")
            assert m.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert not m.locator(".main-nav").is_visible()
            m.screenshot(path=str(shots / "home-mobile.png"), full_page=True)
            m.locator(".menu-button").click()
            assert m.locator(".main-nav").is_visible()
            m.locator(".nav-group summary").nth(1).click()
            m.locator(".nav-group").nth(1).get_by_role("link", name="Europe", exact=True).click()
            m.wait_for_load_state("networkidle")
            assert "/cities/europe/" in m.url
            m.locator(".story-card a").click()
            m.wait_for_load_state("networkidle")
            assert m.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert m.locator(".article-image img").evaluate("img => img.naturalWidth > 0")
            m.screenshot(path=str(shots / "story-mobile.png"), full_page=True)
            # Site remains readable without JavaScript.
            plain = browser.new_context(java_script_enabled=False, viewport={"width": 390, "height": 844})
            n = plain.new_page()
            n.goto(base + "/index.html")
            assert n.locator(".main-nav").is_visible()
            n.goto(base + "/stories/venice-winged-lion/index.html")
            assert n.locator(".prose p").count() > 10
            page.goto(public + "/index.html", wait_until="networkidle")
            assert page.locator(".preview-banner").count() == 0
            assert page.locator(".feature-story").count() == 0
            assert page.locator(".feature-empty").is_visible()
            assert not json.loads(page.request.get(public + "/search-index.json").text())
            assert page.request.get(public + "/stories/venice-winged-lion/index.html").status == 404
            browser.close()
        assert not errors, errors
        print("PASS: desktop/mobile navigation, Korean full-text search, filters/reset, images, reading anchors, empty categories, no-JS reading and production draft exclusion.")
        print("Saved 4 screenshots under docs/previews/. No browser JavaScript errors.")
    finally:
        for server in (preview, production):
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    check()
