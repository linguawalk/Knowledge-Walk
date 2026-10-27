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
    story_count = len(list((ROOT / "content/stories").rglob("*.json")))
    stories = [json.loads(path.read_text()) for path in sorted((ROOT / "content/stories").rglob("*.json"))]
    def capture(page, filename):
        # Full-page screenshots must also load images below the viewport.
        page.evaluate("""async () => {
          const images = [...document.images];
          images.forEach(image => { image.loading = 'eager'; });
          await Promise.all(images.map(image => image.decode()));
          if (images.some(image => !image.naturalWidth)) throw new Error('Image not loaded');
          if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
          window.scrollTo({top: 0, behavior: 'instant'});
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        }""")
        page.screenshot(path=str(shots / filename), full_page=True)
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
            capture(page, "home-desktop.png")
            visit("/library.html")
            assert page.locator(".library-category").count() == 8
            assert page.locator(".topic-folder").count() == 43
            assert page.locator("[data-story-id]").count() == story_count
            page.screenshot(path=str(shots / "library-desktop.png"), full_page=False)
            visit("/index.html")
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
            assert page.locator(".read-toggle").get_attribute("aria-pressed") == "false"
            page.locator(".read-toggle").click()
            page.reload(wait_until="networkidle")
            assert page.locator(".read-toggle").get_attribute("aria-pressed") == "true"
            capture(page, "story-desktop.png")
            page.locator(".article-toc a").last.click()
            page.wait_for_timeout(500)
            assert "#part-3" in page.url
            visit("/search.html?q=베네치아")
            page.wait_for_function("document.querySelector('#search-status').textContent.includes('찾았습니다')")
            assert page.locator("#search-results .story-card").count() == 1
            assert "읽음 ✓" in page.locator("#search-results .read-state").inner_text()
            page.locator("#query").fill("기념품")
            assert page.locator("#search-results .story-card").count() == 1
            page.locator("#category-filter").select_option("history")
            assert page.locator("#search-empty").is_visible()
            page.locator("#reset-search").click()
            assert page.locator("#search-results .story-card").count() == story_count
            page.locator("#query").fill('<img src=x onerror=alert(1)>')
            assert page.locator("#search-empty").is_visible()
            assert page.locator("img[onerror]").count() == 0
            visit("/categories/history/africa/index.html")
            assert page.locator(".empty-state").is_visible()
            assert page.locator(".story-card").count() == 0
            visit("/reading.html")
            assert f"읽음 1편" in page.locator("#reading-count").inner_text()
            page.locator("#reading-filter").select_option("read")
            assert page.locator(".story-card:visible").count() == 1
            page.screenshot(path=str(shots / "reading-desktop.png"), full_page=False)
            page.locator("#reading-filter").select_option("unread")
            assert page.locator(".story-card:visible").count() == story_count - 1
            # Canceling a mark updates an already-open list in another tab.
            other = context.new_page()
            other.goto(base + "/stories/venice-winged-lion/index.html", wait_until="networkidle")
            other.locator(".read-toggle").click()
            page.wait_for_function("document.querySelector('#reading-count').textContent.includes('읽음 0편')")
            assert page.locator(".story-card:visible").count() == story_count
            other.close()
            mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
            m = mobile.new_page()
            m.on("pageerror", lambda error: errors.append(str(error)))
            m.goto(base + "/index.html", wait_until="networkidle")
            assert m.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert not m.locator(".main-nav").is_visible()
            capture(m, "home-mobile.png")
            m.goto(base + "/library.html", wait_until="networkidle")
            assert m.locator(".topic-folder").count() == 43
            assert m.evaluate("document.documentElement.scrollWidth <= innerWidth")
            m.screenshot(path=str(shots / "library-mobile.png"), full_page=False)
            m.goto(base + "/index.html", wait_until="networkidle")
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
            capture(m, "story-mobile.png")
            for story in stories:
                for viewport in (page, m):
                    viewport.goto(base + "/stories/" + story["id"] + "/index.html", wait_until="networkidle")
                    assert viewport.locator("h1").inner_text() == story["title"]
                    assert viewport.locator(".article-image img").evaluate("img => img.complete && img.naturalWidth > 0")
                    assert viewport.locator(".draft-notice").is_visible()
                    assert viewport.evaluate("document.documentElement.scrollWidth <= innerWidth"), story["id"]
                    if story["source_review"] == "verified":
                        assert "자료 대조를 마친" in viewport.locator(".draft-notice").inner_text()
                        viewport.locator(".sources summary").click()
                        assert viewport.locator(".sources a").count() == len(story["sources"])
                        assert viewport.locator(".source-date").first.is_visible()
                    else:
                        assert "출처 확인이 남아" in viewport.locator(".draft-notice").inner_text()
                    if story["image"]["type"] == "artwork":
                        image = viewport.locator(".article-image img")
                        ratio = image.evaluate("img => ({display: img.getBoundingClientRect().width / img.getBoundingClientRect().height, natural: img.naturalWidth / img.naturalHeight})")
                        assert abs(ratio["display"] - ratio["natural"]) < 0.01, "Artwork aspect ratio changed"
                        assert story["image"]["license"] in viewport.locator("figcaption").inner_text()
                        assert viewport.locator("figcaption a").first.get_attribute("href") == story["image"]["source_url"]
                        if story["id"] in ("dokseodang-gathering", "bowl-sundial"):
                            prefix = "dokseodang" if story["id"] == "dokseodang-gathering" else "bowl-sundial"
                            capture(viewport, prefix + ("-desktop.png" if viewport is page else "-mobile.png"))
            # Site remains readable without JavaScript.
            blocked = browser.new_context(viewport={"width": 390, "height": 844})
            blocked.add_init_script("Object.defineProperty(window, 'localStorage', {get() { throw new Error('Storage disabled'); }});")
            b = blocked.new_page()
            b.on("pageerror", lambda error: errors.append(str(error)))
            b.goto(base + "/reading.html", wait_until="networkidle")
            assert b.locator(".storage-note").is_visible()
            assert b.locator(".story-card:visible").count() == story_count
            b.goto(base + "/stories/venice-winged-lion/index.html", wait_until="networkidle")
            assert b.locator(".read-toggle").is_disabled()
            blocked.close()
            # Bundled search data works without fetching a JSON file.
            # Managed Chromium blocks file://, so test the same assets over loopback.
            offline = browser.new_context()
            offline.add_init_script("window.fetch = () => { throw new Error('Fetch unavailable'); };")
            f = offline.new_page()
            f.on("pageerror", lambda error: errors.append(str(error)))
            f.goto(base + "/search.html?q=경회루", wait_until="networkidle")
            assert f.locator("#search-results .story-card").count() == 1
            assert f.locator("#query").is_enabled()
            f.locator(".story-card a").click()
            f.wait_for_load_state("networkidle")
            assert f.locator(".article-image img").evaluate("img => img.complete && img.naturalWidth > 0")
            offline.close()
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
        print(f"Checked {story_count} story pages on desktop and mobile; screenshots saved with all images loaded. No browser JavaScript errors.")
    finally:
        for server in (preview, production):
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    check()
