"""Checks for publication isolation, content validation and generated navigation."""
import copy
import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_site", ROOT / "tools/build_site.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.images = []
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.links.extend(attrs[k] for k in ("href", "src") if attrs.get(k))
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "img":
            self.images.append(attrs)
        if tag == "meta" and attrs.get("name") == "robots" and "noindex" in attrs.get("content", ""):
            self.noindex = True


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.categories = builder.read_json(ROOT / "config/categories.json")
        cls.story = builder.read_json(ROOT / "content/stories/cities/europe/venice-winged-lion.json")
        builder.build(preview=True)
        builder.build()

    def approved_fixture(self):
        story = copy.deepcopy(self.story)
        story.update(status="approved", publication_ready=True, source_review="verified",
                     approved_by="test fixture only", approved_at="2026-10-27",
                     sources=[{"title": "Test reference", "url": "https://example.org/reference",
                               "checked_at": "2026-10-27", "verified": True}])
        return story

    def test_category_transcription(self):
        self.assertEqual(len(self.categories), 8)
        self.assertEqual(sum(len(c["children"]) for c in self.categories), 43)
        self.assertIn("America", self.categories[0]["children"])
        self.assertIn("Americas", self.categories[1]["children"])

    def test_production_has_no_draft_text_media_or_editorial_files(self):
        output = ROOT / "_site"
        stories = builder.load_stories()
        approved = [s for s in stories if builder.publishable(s)]
        pending = [s for s in stories if not builder.publishable(s)]
        index = builder.read_json(output / "search-index.json")
        self.assertEqual({s['id'] for s in index}, {s['id'] for s in approved})
        for story in approved:
            self.assertTrue((output / f"stories/{story['id']}/index.html").is_file())
        for story in pending:
            self.assertFalse((output / f"stories/{story['id']}/index.html").exists())
            self.assertFalse((output / f"media/{story['id']}.jpg").exists())
        for path in output.rglob("*"):
            if path.is_file():
                self.assertNotIn("drafts", path.parts)
                self.assertNotIn("editorial", path.name)
                if path.suffix in (".html", ".json"):
                    for story in pending:
                        self.assertNotIn(story["title"], path.read_text())

    def test_legacy_pages_excludes_every_non_public_root_entry(self):
        self.assertFalse((ROOT / '.nojekyll').exists(), 'Root publication requires Jekyll exclusions')
        excluded = set(builder.read_json(ROOT / '_config.yml')['exclude'])
        output = ROOT / '_site'
        allowed = {p.relative_to(output).parts[0] for p in output.rglob('*') if p.is_file()}
        for path in ROOT.iterdir():
            if path.name not in allowed | {'_config.yml', 'CNAME'}:
                self.assertIn(path.name, excluded, f'Non-public root entry must be excluded: {path}')
        for path in output.rglob('*'):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (ROOT / path.relative_to(output)).read_bytes())

    def test_preview_is_marked_noindex_and_includes_story(self):
        output = ROOT / "_preview"
        for path in output.rglob("*.html"):
            parser = Links()
            parser.feed(path.read_text())
            self.assertTrue(parser.noindex, str(path))
        self.assertEqual(len(builder.read_json(output / "search-index.json")),
                         len(list((ROOT / "content/stories").rglob("*.json"))))
        self.assertTrue((output / "media/venice-winged-lion.jpg").exists())

    def test_revoking_a_story_rebuilds_clean_output(self):
        for directory in (ROOT / "_site", ROOT / "_preview"):
            (directory / "stale.txt").write_text("must not survive")
        builder.build()
        builder.build(preview=True)
        self.assertFalse((ROOT / "_site/stale.txt").exists())
        self.assertFalse((ROOT / "_preview/stale.txt").exists())

    def test_incomplete_approval_fails_instead_of_publishing(self):
        for key, value in [("source_review", "pending"), ("publication_ready", False),
                           ("sources", []), ("approved_by", None), ("approved_at", "bad-date")]:
            with self.subTest(key=key):
                story = self.approved_fixture()
                story[key] = value
                with self.assertRaises(ValueError):
                    builder.validate(self.categories, [story])

    def test_unverified_or_unsafe_source_is_rejected(self):
        for changes in ({"verified": False}, {"url": "javascript:alert(1)"}, {"checked_at": "yesterday"}):
            story = self.approved_fixture()
            story["sources"][0].update(changes)
            with self.assertRaises(ValueError):
                builder.validate(self.categories, [story])

    def test_approved_story_appears_in_public_pages_and_search(self):
        story = self.approved_fixture()
        builder.validate(self.categories, [story])
        files = builder.Site(self.categories, [story]).render()
        self.assertIn("stories/venice-winged-lion/index.html", files)
        self.assertIn(story["title"], files["index.html"])
        self.assertIn(story["title"], files["categories/cities/europe/index.html"])
        self.assertEqual(len(json.loads(files["search-index.json"])), 1)

    def test_invalid_category_id_and_image_paths_fail(self):
        for changes in ({"id": "../../escape"}, {"subcategory": "Not a subcategory"},
                        {"image": {**self.story["image"], "file": "/etc/passwd"}}):
            with self.subTest(changes=changes):
                story = {**self.story, **changes}
                with self.assertRaises(ValueError):
                    builder.validate(self.categories, [story])

    def test_story_url_does_not_change_with_category(self):
        site = builder.Site(self.categories, [self.story], preview=True)
        moved = {**self.story, "category": "culture", "subcategory": "Art"}
        builder.validate(self.categories, [moved])
        self.assertEqual(site.story_path(self.story), site.story_path(moved))

    def test_nested_manuscripts_keep_the_same_ids_and_categories(self):
        stories = builder.load_stories()
        self.assertEqual(len(stories), len(builder.story_files()))
        self.assertGreater(len(stories), 0)
        builder.validate(self.categories, stories)
        for story in stories:
            path = ROOT / 'content/stories' / story['category'] / builder.slug(story['subcategory']) / (story['id'] + '.json')
            self.assertTrue(path.is_file())

    def test_library_lists_each_story_once_and_all_topic_folders(self):
        stories = builder.load_stories()
        files = builder.Site(self.categories, stories, preview=True).render()
        links = Links()
        links.feed(files['library.html'])
        for story in stories:
            self.assertEqual(links.links.count(f"stories/{story['id']}/index.html"), 1)
        for category in self.categories:
            for child in category['children']:
                self.assertIn(f"categories/{category['id']}/{builder.slug(child)}/index.html", links.links)
        public = builder.Site(self.categories, stories).render()
        self.assertEqual(len(json.loads(public['search-index.json'])), sum(builder.publishable(s) for s in stories))
        for story in stories:
            if not builder.publishable(story):
                self.assertNotIn(story['title'], public['library.html'])
                self.assertNotIn(story['title'], public['reading.html'])

    def test_featured_draft_cannot_displace_approved_story(self):
        draft = {**self.story, "featured": True, "status": "review", "publication_ready": False,
                 "approved_by": None, "approved_at": None}
        approved = self.approved_fixture()
        approved.update(id="approved-fixture", title="A verified fixture", featured=False)
        builder.validate(self.categories, [draft, approved])
        site = builder.Site(self.categories, [draft, approved])
        files = site.render()
        self.assertEqual([s["id"] for s in site.stories], ["approved-fixture"])
        self.assertNotIn(draft["title"], files["index.html"])
        self.assertIn(approved["title"], files["index.html"])

    def test_checked_sources_do_not_grant_publication_approval(self):
        story = self.approved_fixture()
        story.update(status="review", publication_ready=False, approved_by=None, approved_at=None)
        builder.validate(self.categories, [story])
        self.assertFalse(builder.publishable(story))
        files = builder.Site(self.categories, [story], preview=True).render()
        page = files["stories/venice-winged-lion/index.html"]
        self.assertIn("자료 대조를 마친", page)
        self.assertIn("공개 게시 승인은 아직", page)
        self.assertNotIn("게시 전 출처 확인이 남아", page)
        self.assertNotIn("stories/venice-winged-lion/index.html", builder.Site(self.categories, [story]).render())

    def test_verified_flag_requires_actual_checked_source_records(self):
        story = self.approved_fixture()
        story.update(status="review", publication_ready=False, approved_by=None, approved_at=None, sources=[])
        with self.assertRaises(ValueError):
            builder.validate(self.categories, [story])
        story["sources"] = [{"title": "Candidate", "url": "https://example.org/", "verified": False}]
        with self.assertRaises(ValueError):
            builder.validate(self.categories, [story])

    def test_topic_coverage_distinguishes_review_from_public_approval(self):
        from tools.topic_coverage import coverage
        draft = {**self.story, "id": "draft-fixture", "status": "draft", "source_review": "pending"}
        checked = self.approved_fixture()
        checked.update(id="review-fixture", status="review", publication_ready=False, approved_by=None, approved_at=None)
        approved = self.approved_fixture()
        approved["id"] = "approved-fixture"
        rejected = {**draft, "id": "rejected-fixture", "status": "rejected"}
        categories = [{"id": "cities", "title": "Cities", "children": ["Europe", "Asia"]}]
        rows = coverage(categories, [draft, checked, approved, rejected])
        self.assertEqual(rows[0]["count"], 3)
        self.assertEqual(rows[0]["source_checked"], 2)
        self.assertEqual(rows[0]["approved"], 1)
        self.assertEqual(rows[1]["count"], 0)

    def test_text_is_escaped(self):
        story = copy.deepcopy(self.story)
        story["body"][0]["paragraphs"].append('<script>alert("not HTML")</script>')
        files = builder.Site(self.categories, [story], preview=True).render()
        page = files["stories/venice-winged-lion/index.html"]
        self.assertNotIn('<script>alert', page)
        self.assertIn('&lt;script&gt;', page)

    def test_all_local_links_images_and_fragments_resolve(self):
        for mode in ("_site", "_preview"):
            output = ROOT / mode
            for page in output.rglob("*.html"):
                parsed = Links()
                parsed.feed(page.read_text())
                for image in parsed.images:
                    self.assertTrue(image.get("alt"))
                for href in parsed.links:
                    url = urlsplit(href)
                    if url.scheme or url.netloc:
                        continue
                    target = ((output / unquote(url.path).lstrip("/")) if url.path.startswith("/")
                              else (page.parent / unquote(url.path)) if url.path else page)
                    target = target.resolve()
                    self.assertTrue(target.is_relative_to(output.resolve()), (page, href))
                    self.assertTrue(target.is_file(), (page, href))
                    if url.fragment:
                        linked = Links()
                        linked.feed(target.read_text())
                        self.assertIn(unquote(url.fragment), linked.ids, (page, href))


if __name__ == "__main__":
    unittest.main()
