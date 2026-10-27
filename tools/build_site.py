#!/usr/bin/env python3
"""Dependency-free static site builder. No uploads, deployments, or AI API calls."""
import argparse
import html
import json
import math
import os
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def esc(value):
    return html.escape(str(value), quote=True)


def slug(value):
    return value.lower().replace(" ", "-")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, name):
    require(isinstance(value, str) and bool(value.strip()), f"Missing text: {name}")
    return value


def source_ok(source):
    if not isinstance(source, dict):
        return False
    parsed = urlsplit(str(source.get("url", "")))
    try:
        date.fromisoformat(source.get("checked_at", ""))
    except (ValueError, TypeError):
        return False
    return (parsed.scheme == "https" and bool(parsed.hostname)
            and not parsed.username and not parsed.password
            and isinstance(source.get("title"), str) and bool(source["title"].strip())
            and source.get("verified") is True)


def publishable(story):
    return (story.get("status") == "approved"
            and story.get("publication_ready") is True
            and story.get("source_review") == "verified"
            and bool(story.get("approved_by")) and bool(story.get("approved_at"))
            and bool(story.get("sources")) and all(source_ok(s) for s in story["sources"]))


def review_notice(story):
    if story.get("source_review") == "verified":
        return "자료 대조를 마친 검토용 이야기입니다. 공개 게시 승인은 아직 받지 않았습니다."
    return "편집 검토용 이야기입니다. 게시 전 출처 확인이 남아 있습니다."


def validate(categories, stories, root=ROOT):
    require(isinstance(categories, list) and categories, "No categories")
    category_map = {}
    for category in categories:
        cid = text(category.get("id"), "category id")
        require(ID.fullmatch(cid) and cid not in category_map, "Invalid/duplicate category id")
        for key in ("title", "label", "intro"):
            text(category.get(key), key)
        children = category.get("children")
        require(isinstance(children, list) and children, f"No subcategories: {cid}")
        for child in children:
            text(child, "subcategory")
            require(ID.fullmatch(slug(child)), "Invalid subcategory slug")
        require(len({slug(c) for c in children}) == len(children), "Duplicate subcategory")
        category_map[cid] = category
    seen = set()
    for story in stories:
        sid = text(story.get("id"), "story id")
        require(ID.fullmatch(sid) and sid not in seen, "Invalid/duplicate story id")
        seen.add(sid)
        for key in ("title", "subtitle", "summary"):
            text(story.get(key), key)
        require(type(story.get("featured", False)) is bool, "featured must be boolean")
        cid = story.get("category")
        require(cid in category_map, f"Unknown category: {sid}")
        require(story.get("subcategory") in category_map[cid]["children"], f"Unknown subcategory: {sid}")
        require(story.get("status") in ("draft", "review", "approved", "rejected"), "Invalid status")
        require(type(story.get("publication_ready")) is bool, "publication_ready must be boolean")
        require(story.get("source_review") in ("pending", "verified"), "Invalid source_review")
        require(isinstance(story.get("sources"), list), "sources must be an array")
        for entry in story["sources"]:
            require(isinstance(entry, dict), "Invalid source record")
            if "supports" in entry:
                require(isinstance(entry["supports"], list) and entry["supports"], "Source supports must be a nonempty list")
                for claim in entry["supports"]:
                    text(claim, "source support")
        if story["source_review"] == "verified":
            require(bool(story["sources"]) and all(source_ok(s) for s in story["sources"]),
                    f"Verified source review needs checked references: {sid}")
        image = story.get("image")
        require(isinstance(image, dict), f"Image missing: {sid}")
        for key in ("file", "alt", "credit"):
            text(image.get(key), f"image {key}")
        require(image.get("type") in ("ai_illustration", "photo", "artwork"), "Invalid image type")
        for dimension in ("width", "height"):
            if dimension in image:
                require(type(image[dimension]) is int and image[dimension] > 0, "Image dimensions must be positive integers")
        image_path = (root / image["file"]).resolve()
        require(image_path.is_relative_to(root.resolve()) and image_path.is_file(), f"Unsafe/missing image: {sid}")
        require(image_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"), "Unsupported image format")
        if image["type"] != "ai_illustration":
            require(bool(image.get("source_url")) and bool(image.get("license")), "Photo/artwork needs source and license")
            require(urlsplit(image["source_url"]).scheme == "https", "Image source must use HTTPS")
        body = story.get("body")
        require(isinstance(body, list) and body, f"Body missing: {sid}")
        for block in body:
            require(isinstance(block, dict), "Invalid body block")
            if block.get("heading") is not None:
                text(block["heading"], "heading")
            require(isinstance(block.get("paragraphs"), list) and block["paragraphs"], "Empty section")
            for paragraph in block["paragraphs"]:
                text(paragraph, "paragraph")
        if story["status"] == "approved" or story["publication_ready"]:
            require(publishable(story), f"Incomplete publication approval or sources: {sid}")
            try:
                date.fromisoformat(story["approved_at"])
            except (ValueError, TypeError):
                raise ValueError(f"approved_at must be YYYY-MM-DD: {sid}") from None
    return category_map


class Site:
    def __init__(self, categories, stories, preview=False):
        self.categories = categories
        self.category_map = {c["id"]: c for c in categories}
        self.preview = preview
        self.stories = [s for s in stories if s["status"] != "rejected" and (preview or publishable(s))]
        positions = {category["id"]: i for i, category in enumerate(categories)}
        self.stories.sort(key=lambda s: (not s.get("featured", False), positions[s["category"]], s["id"]))
        self.files = {}

    def link(self, page, target):
        return esc(os.path.relpath(target, str(Path(page).parent)).replace(os.sep, "/"))

    def category_path(self, cid, child=None):
        return f"categories/{cid}/" + (f"{slug(child)}/" if child else "") + "index.html"

    def story_path(self, story):
        return f"stories/{story['id']}/index.html"

    def image_path(self, story):
        return f"media/{story['id']}{Path(story['image']['file']).suffix.lower()}"

    def minutes(self, story):
        return max(1, math.ceil(sum(len(p) for b in story["body"] for p in b["paragraphs"]) / 500))

    def image(self, page, story, eager=False):
        image = story["image"]
        css = ' class="artwork-image"' if image["type"] == "artwork" else ""
        return (f'<img{css} src="{self.link(page, self.image_path(story))}" alt="{esc(image["alt"])}" '
                f'width="{image.get("width", 1536)}" height="{image.get("height", 1024)}" loading="{"eager" if eager else "lazy"}" decoding="async">')

    def layout(self, page, title, description, body, active=None, article=False):
        link = lambda target: self.link(page, target)
        nav = ""
        for c in self.categories:
            children = "".join(f'<li><a href="{link(self.category_path(c["id"], sub))}">{esc(sub)}</a></li>' for sub in c["children"])
            nav += (f'<details class="nav-group{" active" if active == c["id"] else ""}">'
                    f'<summary>{esc(c["title"])}<span aria-hidden="true">⌄</span></summary><ul>'
                    f'<li><a href="{link(self.category_path(c["id"]))}">전체 이야기 <span aria-hidden="true">↗</span></a></li>{children}</ul></details>')
        preview_banner = '<div class="preview-banner">검토용 화면 · 미게시 원고가 포함되어 있습니다</div>' if self.preview else ""
        robots = '<meta name="robots" content="noindex,nofollow">' if self.preview or page == "404.html" else ""
        progress = '<div class="reading-progress" aria-hidden="true"><span></span></div>' if article else ""
        self.files[page] = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · KnowledgeWalk</title><meta name="description" content="{esc(description)}">{robots}
<meta name="theme-color" content="#faf8f3"><link rel="icon" href="{link('site-assets/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{link('site-assets/site.css')}"><script src="{link('site-assets/site.js')}" defer></script></head>
<body>{preview_banner}<a class="skip-link" href="#main">본문으로 건너뛰기</a>{progress}
<header class="site-header"><div class="header-inner"><a class="brand" href="{link('index.html')}" aria-label="KnowledgeWalk 첫 화면">Knowledge<span>Walk</span><i aria-hidden="true">✳</i></a>
<button class="menu-button" aria-expanded="false" aria-controls="main-nav" hidden>분야 보기 <span aria-hidden="true">＋</span></button>
<nav id="main-nav" class="main-nav" aria-label="주요 분야">{nav}</nav>
<a class="search-link" href="{link('search.html')}" aria-label="이야기 검색"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg><span>검색</span></a></div></header>
<main id="main" tabindex="-1">{body}</main>
<footer class="site-footer"><div class="footer-inner"><a class="brand" href="{link('index.html')}">Knowledge<span>Walk</span></a><p>궁금한 마음으로, 세상을 한 걸음 더.</p><a href="{link('index.html')}#fields">분야 둘러보기 <span aria-hidden="true">↗</span></a><small>© 2026 KnowledgeWalk</small></div></footer>
</body></html>'''

    def card(self, page, story):
        category = self.category_map[story["category"]]
        return (f'<article class="story-card"><a href="{self.link(page, self.story_path(story))}">'
                f'<div class="card-image">{self.image(page, story)}</div>'
                f'<div class="card-copy"><p class="eyebrow">{esc(category["title"])} <span> / {esc(story["subcategory"])}</span></p>'
                f'<h2>{esc(story["title"])}</h2><p>{esc(story["summary"])}</p>'
                f'<span class="text-link">이야기 읽기 <span aria-hidden="true">↗</span></span></div></a></article>')

    def home(self):
        page = "index.html"
        if self.stories:
            s = self.stories[0]
            feature = (f'<a class="feature-story" href="{self.link(page, self.story_path(s))}">'
                       f'<div class="feature-image">{self.image(page, s, True)}<span class="image-label">ILLUSTRATED STORY</span></div>'
                       f'<div class="feature-caption"><div><p class="eyebrow">{esc(self.category_map[s["category"]]["title"])} · {esc(s["subcategory"])}</p>'
                       f'<h2>{esc(s["title"])}</h2></div><span class="round-arrow" aria-hidden="true">↗</span></div></a>')
        else:
            feature = '<div class="feature-empty"><span aria-hidden="true">✳</span><p>작은 궁금증 하나가<br>새로운 이야기의 시작.</p><small>곧 첫 이야기를 만나보세요.</small></div>'
        fields = ""
        for n, c in enumerate(self.categories, 1):
            count = sum(s["category"] == c["id"] for s in self.stories)
            fields += (f'<a class="field-card field-{c["id"]}" href="{self.link(page, self.category_path(c["id"]))}">'
                       f'<div class="field-top"><span>0{n}</span><span aria-hidden="true">↗</span></div>'
                       f'<h3>{esc(c["title"])}</h3><p class="field-label">{esc(c["label"])}</p><p>{esc(c["intro"])}</p>'
                       f'<span class="field-meta">{str(count) + "개의 이야기" if count else "이야기를 준비하고 있어요"}</span></a>')
        stories = "".join(self.card(page, s) for s in self.stories[:9])
        shelf = f'<section class="container story-shelf"><div class="section-heading"><div><p class="eyebrow">STORIES TO WANDER INTO</p><h2>그냥 지나치기 아까운 이야기</h2></div><a class="text-link" href="search.html">모든 이야기 <span aria-hidden="true">↗</span></a></div><div class="story-grid">{stories}</div></section>' if len(self.stories) > 1 else ""
        body = f'''<section class="container hero"><div class="hero-copy"><p class="eyebrow"><span class="little-star" aria-hidden="true">✳</span> 발견하는 즐거움, KnowledgeWalk</p>
<h1>알고 나면,<br>조금 다르게<br>보이는 것들<span class="title-dot">.</span></h1>
<p class="hero-description">도시의 사자 한 마리부터 매일 쓰는 물건까지.<br>익숙한 세상에 숨은, 작지만 재미있는 사연을 만납니다.</p>
<a class="button" href="#fields">궁금한 분야 둘러보기 <span aria-hidden="true">↓</span></a><p class="hero-note">잠깐 읽고, 오래 바라보는 이야기.</p></div>{feature}</section>
<div class="intro-strip"><div class="container"><span>역사에서 과학까지</span><p>어려운 설명 대신, 한 편의 이야기로.</p><span aria-hidden="true">✳</span></div></div>
<section id="fields" class="container fields-section"><div class="section-heading"><div><p class="eyebrow">EIGHT WAYS TO EXPLORE</p><h2>오늘은 어떤 이야기가 궁금하세요?</h2></div><p>마음이 가는 곳에서 시작하세요.</p></div><div class="field-grid">{fields}</div></section>{shelf}
<section class="container closing-note"><span aria-hidden="true">✳</span><p>새로운 곳을 가지 않아도,<br>새로운 이야기는 만날 수 있으니까.</p></section>'''
        self.layout(page, "익숙한 세상의 작은 발견", "역사, 도시, 문화, 생활부터 과학까지. 가볍게 읽고 즐기는 이야기, KnowledgeWalk.", body)

    def category(self, category, child=None):
        cid = category["id"]
        page = self.category_path(cid, child)
        subset = [s for s in self.stories if s["category"] == cid and (child is None or s["subcategory"] == child)]
        chips = f'<a class="chip{" selected" if child is None else ""}" {"aria-current=page" if child is None else ""} href="{self.link(page, self.category_path(cid))}">전체</a>'
        for name in category["children"]:
            chips += f'<a class="chip{" selected" if name == child else ""}" {"aria-current=page" if name == child else ""} href="{self.link(page, self.category_path(cid, name))}">{esc(name)}</a>'
        listing = '<div class="story-grid">' + "".join(self.card(page, s) for s in subset) + '</div>' if subset else '<div class="empty-state"><span aria-hidden="true">✳</span><h2>다음 이야기를 준비하고 있어요.</h2><p>이곳에서 만나고 싶은 작은 궁금증을 모으고 있습니다.</p><a class="text-link" href="' + self.link(page, "index.html") + '#fields">다른 분야 둘러보기 ↗</a></div>'
        crumb = f'<a href="{self.link(page, "index.html")}">처음</a><span aria-hidden="true">/</span><a href="{self.link(page, self.category_path(cid))}">{esc(category["title"])}</a>'
        if child:
            crumb += f'<span aria-hidden="true">/</span><span>{esc(child)}</span>'
        title = child or category["title"]
        body = f'<section class="container category-page"><nav class="breadcrumbs" aria-label="현재 위치">{crumb}</nav><header class="page-heading"><p class="eyebrow">{esc(category["title"])} · {esc(category["label"])}</p><h1>{esc(title)}</h1><p>{esc(category["intro"])}</p></header><nav class="chips" aria-label="세부 분야">{chips}</nav><p class="result-label">{len(subset)}개의 이야기</p>{listing}</section>'
        self.layout(page, title, category["intro"], body, cid)

    def story(self, story):
        page = self.story_path(story)
        category = self.category_map[story["category"]]
        crumb = (f'<a href="{self.link(page, "index.html")}">처음</a><span aria-hidden="true">/</span>'
                 f'<a href="{self.link(page, self.category_path(category["id"]))}">{esc(category["title"])}</a><span aria-hidden="true">/</span>'
                 f'<a href="{self.link(page, self.category_path(category["id"], story["subcategory"]))}">{esc(story["subcategory"])}</a>')
        contents = ""
        prose = ""
        for index, block in enumerate(story["body"]):
            if block.get("heading"):
                contents += f'<li><a href="#part-{index}">{esc(block["heading"])}</a></li>'
                prose += f'<h2 id="part-{index}">{esc(block["heading"])}</h2>'
            prose += "".join(f'<p>{esc(p)}</p>' for p in block["paragraphs"])
        notice = f'<p class="draft-notice">{esc(review_notice(story))}</p>' if not publishable(story) else ""
        sources = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])} ↗</a><span class="source-date">확인일 {esc(s["checked_at"])}</span><p>{esc(" · ".join(s.get("supports", [])))}</p></li>' for s in story["sources"] if source_ok(s))
        sources = f'<details class="sources"><summary>이야기의 바탕이 된 자료</summary><ul>{sources}</ul></details>' if sources else '<p class="source-pending">출처 확인 중 · 확인이 끝나면 참고 자료를 안내합니다.</p>'
        img = story["image"]
        image_source = f' <a href="{esc(img["source_url"])}" rel="noopener noreferrer">이미지 출처</a> · {esc(img["license"])}' if img["type"] != "ai_illustration" else ""
        figure_class = " artwork-figure" if img["type"] == "artwork" else ""
        if img["type"] == "artwork":
            image_source += f' · <a href="{self.link(page, self.image_path(story))}">이미지 크게 보기</a>'
        body = f'''<article class="reading-page"><div class="container"><nav class="breadcrumbs" aria-label="현재 위치">{crumb}</nav></div>
<header class="article-heading"><p class="eyebrow">{esc(category['title'])} · {esc(story['subcategory'])}</p><h1>{esc(story['title'])}</h1><p class="article-subtitle">{esc(story['subtitle'])}</p><p class="reading-meta">약 {self.minutes(story)}분의 작은 발견</p>{notice}</header>
<figure class="article-image container{figure_class}">{self.image(page, story, True)}<figcaption>{esc(img['credit'])}{image_source}</figcaption></figure>
<div class="reading-layout"><aside class="article-toc"><details open><summary>이야기 속으로</summary><ol>{contents}</ol></details></aside>
<div class="prose">{prose}<div class="story-end" aria-hidden="true">✳</div>{sources}<a class="back-link" href="{self.link(page, self.category_path(category['id'], story['subcategory']))}">← {esc(story['subcategory'])}의 다른 이야기</a></div></div></article>'''
        self.layout(page, story["title"], story["summary"], body, category["id"], article=True)

    def search(self):
        page = "search.html"
        options = "".join(f'<option value="{esc(c["id"])}">{esc(c["title"])}</option>' for c in self.categories)
        body = f'''<section class="container search-page"><header class="page-heading"><p class="eyebrow">FOLLOW YOUR CURIOSITY</p><h1>어떤 이야기를 찾으세요?</h1><p>도시 이름, 물건, 작은 궁금증을 입력해 보세요.</p></header>
<form class="search-form" role="search" action="search.html" data-index="search-index.json"><label for="query">검색어</label><div class="search-row"><input id="query" name="q" type="search" placeholder="예: 베네치아, 사자, 책" autocomplete="off"><button class="button" type="submit">검색</button></div><label for="category-filter">분야 선택</label><select id="category-filter" name="category"><option value="">모든 분야</option>{options}</select></form>
<noscript><p>검색은 자바스크립트가 필요합니다. 아래 전체 이야기 목록에서 골라 읽으실 수 있습니다.</p></noscript>
<p id="search-status" class="result-label" role="status" aria-live="polite">전체 {len(self.stories)}개의 이야기</p><div id="search-results" class="story-grid">{"".join(self.card(page, s) for s in self.stories)}</div><div id="search-empty" class="empty-state" hidden><h2>아직 찾는 이야기가 없어요.</h2><p>다른 단어로 찾아보거나, 분야를 바꿔 보세요.</p><button class="button" type="button" id="reset-search">전체 이야기 보기</button></div></section>'''
        self.layout(page, "이야기 검색", "궁금한 단어로 KnowledgeWalk의 이야기를 찾아보세요.", body)
        index = []
        for s in self.stories:
            index.append({"id": s["id"], "title": s["title"], "summary": s["summary"], "category": s["category"],
                          "category_title": self.category_map[s["category"]]["title"], "subcategory": s["subcategory"],
                          "url": self.story_path(s), "image": self.image_path(s), "alt": s["image"]["alt"],
                          "text": " ".join([s["title"], s["subtitle"], s["summary"], s["subcategory"], self.category_map[s["category"]]["label"]] + [p for b in s["body"] for p in b["paragraphs"]])})
        self.files["search-index.json"] = json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n"

    def render(self):
        self.home()
        for category in self.categories:
            self.category(category)
            for child in category["children"]:
                self.category(category, child)
        for story in self.stories:
            self.story(story)
        self.search()
        self.layout("404.html", "길을 잠깐 벗어났네요", "찾으시는 페이지가 없습니다.", '<section class="container empty-state"><p class="eyebrow">404</p><h1>길을 잠깐 벗어났네요.</h1><p>다른 이야기에서 다시 시작해 볼까요?</p><a class="button" href="/index.html">첫 화면으로</a></section>')
        return self.files


def build(preview=False, sync_root=False, categories_path=None, stories_dir=None):
    categories = read_json(categories_path or ROOT / "config/categories.json")
    story_files = sorted((stories_dir or ROOT / "content/stories").glob("*.json"))
    stories = [read_json(path) for path in story_files]
    validate(categories, stories)
    require(not (preview and sync_root), "Preview cannot overwrite the root site")
    site = Site(categories, stories, preview)
    files = site.render()
    destination = ROOT / ("_preview" if preview else "_site")
    # Only these disposable build directories are replaced. Never clean the checkout.
    with tempfile.TemporaryDirectory(prefix="knowledgewalk-") as tmp:
        staged = Path(tmp)
        for name, content in files.items():
            path = staged / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        shutil.copytree(ROOT / "site", staged / "site-assets")
        for story in site.stories:
            target = staged / site.image_path(story)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / story["image"]["file"], target)
        if destination.is_symlink():
            raise ValueError("Build directory must not be a symlink")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(staged, destination)
    if sync_root:
        # Root HTML is a checked-in convenience copy, not the deploy artifact.
        # Deploy ONLY _site, otherwise repository drafts would be downloadable.
        # A root sync is additive: existing archives and unrelated files survive.
        for source in destination.rglob("*"):
            if source.is_file():
                target = ROOT / source.relative_to(destination)
                require(target.resolve().is_relative_to(ROOT), "Unsafe root output path")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
    return {"mode": "preview" if preview else "production", "pages": len([n for n in files if n.endswith('.html')]),
            "included": [s["id"] for s in site.stories], "excluded": len(stories) - len(site.stories), "output": str(destination)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Include drafts in a noindex review build")
    parser.add_argument("--sync-root", action="store_true", help="Also refresh checked-in production HTML")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.preview, args.sync_root), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
