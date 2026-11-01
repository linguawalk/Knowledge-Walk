#!/usr/bin/env python3
"""Build additive, noindex previews; never change production pages or DNS."""
import copy
import json
import posixpath
import re
from pathlib import Path
from build_site import ROOT, Site, esc, load_stories, publishable, read_json, require, validate

DEST = ROOT / 'collections/site-redesign'
REGION_IDS = ['asia-oceania', 'europe', 'americas', 'middle-east-africa']
TOPIC_IDS = ['industry', 'digital', 'finance', 'science', 'everyday-inventions', 'ideas']
INTRO = {
    '아시아대양주': '오랜 문명과 오늘의 생활 사이, 익숙하면서도 새로운 이야기를 만납니다.',
    '유럽': '광장의 조각부터 소설과 음악까지, 장소에 남은 이야기를 따라갑니다.',
    '아메리카': '도시와 사람, 전승과 변화가 만나는 대륙을 읽습니다.',
    '중동아프리카': '고대 도시와 교역로, 다양한 공동체의 삶을 만납니다.',
    '기업과 산업': '작은 아이디어는 어떻게 공장과 가게, 새로운 산업이 되었을까요?',
    '컴퓨터와 디지털': '화면 뒤에 쌓인 발명과 선택을, 사람의 이야기로 읽습니다.',
    '돈과 금융': '동전과 은행, 시장과 신용이 만들어진 역사를 따라갑니다.',
    '과학과 발견': '당연해 보이던 세상을 바꾼 질문과 관찰을 만납니다.',
    '생활을 바꾼 물건과 기술': '식탁과 집, 이동과 놀이를 바꾼 작은 발명을 살펴봅니다.',
    '생각과 지식': '사람은 어떻게 질문하고, 보고, 기록하고, 함께 배웠을까요?',
}


def prepare(domain, taxonomy, placements, originals):
    rows = [r for r in placements if r['proposed_domain'] == 'knowledgewalk.' + domain]
    required = set(originals)
    require({r['id'] for r in placements} == required, 'Placement coverage differs from canonical stories')
    require(len({r['id'] for r in placements}) == len(placements), 'Duplicate placements')
    categories = []
    definitions = taxonomy['net' if domain == 'net' else 'kr']
    ids = REGION_IDS if domain == 'net' else TOPIC_IDS
    lookup = {}
    for cid, (title, children) in zip(ids, definitions.items()):
        children = list(children)
        if domain == 'net':
            children += sorted({r['country'] for r in rows if r['region'] == title and r['country_group'] == '기타 국가'})
            children += ['지역에 걸친 이야기']
        categories.append(dict(id=cid, title=title, label=title, intro=INTRO[title], children=children))
        lookup[title] = cid
    mapped = []
    for row in rows:
        original = originals[row['id']]
        # Approval is always evaluated from current canonical data, never from a saved plan flag.
        if not publishable(original):
            continue
        story = copy.deepcopy(original)
        story['category'] = lookup[row['region'] if domain == 'net' else row['topic']]
        story['subcategory'] = (row['country'] or '지역에 걸친 이야기') if domain == 'net' else row['subtopic']
        story['placement'] = row
        mapped.append(story)
    return categories, mapped


class SplitSite(Site):
    def __init__(self, domain, categories, stories, taxonomy):
        super().__init__(categories, stories)
        self.domain = domain
        self.taxonomy = taxonomy
        self.brand_label = '국가와 이야기' if domain == 'net' else '발견과 지식'

    def link(self, page, target):
        # Resolve against a fixed virtual root, independent of the shell cwd.
        base = '/collections/site-redesign/' + self.domain + '/'
        return esc(posixpath.relpath(posixpath.normpath(base + target),
                                    posixpath.normpath(base + str(Path(page).parent))))

    def image_path(self, story):
        # Reuse published media without duplicating hundreds of megabytes in this repository.
        return '../../../' + super().image_path(story)

    def layout(self, page, title, description, body, active=None, article=False):
        super().layout(page, title, description, body, active, article)
        markup = self.files[page]
        other = 'kr' if self.domain == 'net' else 'net'
        other_name = '발견과 지식' if other == 'kr' else '국가와 이야기'
        switch = self.link(page, '../' + other + '/index.html')
        hub = self.link(page, '../index.html')
        banner = (f'<div class="preview-banner split-banner"><span>개편 미리보기 · knowledgewalk.{self.domain}</span>'
                  f'<a href="{switch}">{other_name} 미리보기 ↗</a><a href="{hub}">두 사이트 안내</a></div>')
        markup = markup.replace('<head>', '<head><meta name="robots" content="noindex,nofollow">', 1)
        markup = markup.replace('<body>', f'<body class="split-{self.domain}">{banner}', 1)
        markup = markup.replace('</head>', f'<link rel="stylesheet" href="{self.link(page, "site-assets/split.css")}"></head>', 1)
        markup = markup.replace('분야 보기', '메뉴 보기').replace('aria-label="주요 분야"', 'aria-label="주요 메뉴"')
        markup = markup.replace('Knowledge<span>Walk</span><i', f'Knowledge<span>Walk</span><small class="brand-section">{self.brand_label}</small><i')
        if self.domain == 'net':
            for c in self.categories:
                extras = [ch for ch in c['children'] if ch not in self.taxonomy['net'][c['title']] and ch != '지역에 걸친 이야기']
                for child in extras:
                    # Extra-country pages remain accessible through the regional hub, not a sprawling top menu.
                    markup = markup.replace(f'<li><a href="{self.link(page, self.category_path(c["id"], child))}">{esc(child)}</a></li>', '')
                if extras:
                    needle = f'<li><a href="{self.link(page, self.category_path(c["id"], "지역에 걸친 이야기"))}">'
                    extra = f'<li><a href="{self.link(page, self.category_path(c["id"]))}#other-countries">기타 국가</a></li>'
                    markup = markup.replace(needle, extra + needle)
            markup = markup.replace('분야 둘러보기', '지역 둘러보기')
        self.files[page] = markup

    def card(self, page, story):
        result = super().card(page, story)
        if self.domain == 'net':
            label = esc(story['placement']['topic'])
            result = result.replace('</span></p>', f' · {label}</span></p>', 1)
        return result

    def feature(self, page, story):
        return (f'<a class="feature-story" href="{self.link(page, self.story_path(story))}">'
                f'<div class="feature-image">{self.image(page, story, True)}</div>'
                f'<div class="feature-caption"><div><p class="eyebrow">{esc(story["subcategory"])}</p>'
                f'<h2>{esc(story["title"])}</h2></div><span class="round-arrow" aria-hidden="true">↗</span></div></a>')

    def home(self):
        page = 'index.html'
        is_net = self.domain == 'net'
        heading = '한 국가를 만나면,<br>이야기가 시작됩니다.' if is_net else '세상을 바꾼 발견,<br>그 시작을 읽습니다.'
        description = ('도시의 광장, 오래된 작품, 일상에 남은 풍습.<br>국가를 따라 걷고, 이야기로 조금 더 가까워집니다.' if is_net else
                       '기업과 컴퓨터, 돈과 과학, 매일 쓰는 물건까지.<br>오늘의 세상이 만들어진 과정을 이야기로 만납니다.')
        candidates = ['venice-winged-lion', 'mona-lisa-looking-guide'] if is_net else ['ford-moving-assembly', 'lloyds-coffeehouse-shipping-news']
        feature_story = next((s for sid in candidates for s in self.stories if s['id'] == sid), self.stories[0])
        fields = ''
        for n, c in enumerate(self.categories, 1):
            subset = [s for s in self.stories if s['category'] == c['id']]
            names = self.taxonomy['net'][c['title']] if is_net else c['children']
            fields += (f'<a class="field-card" href="{self.link(page, self.category_path(c["id"]))}">'
                       f'<div class="field-top"><span>{n:02d}</span><span aria-hidden="true">↗</span></div>'
                       f'<h3>{esc(c["title"])}</h3><p class="field-label">{esc(" · ".join(names))}</p>'
                       f'<p>{esc(c["intro"])}</p><span class="field-meta">{len(subset)}편의 이야기</span></a>')
        # Mix categories instead of allowing the first category to occupy the whole homepage.
        shelves = []
        for n in range(3):
            for c in self.categories:
                subset = [s for s in self.stories if s['category'] == c['id'] and s != feature_story]
                if len(subset) > n:
                    shelves.append(subset[n])
        storycards = ''.join(self.card(page, s) for s in shelves[:9])
        jump_name = '지역과 국가 둘러보기' if is_net else '궁금한 주제 둘러보기'
        body = f'''<section class="container hero"><div class="hero-copy"><p class="eyebrow">KNOWLEDGEWALK · {self.brand_label}</p><h1>{heading}</h1><p class="hero-description">{description}</p><a class="button" href="#fields">{jump_name} ↓</a><p class="hero-note">편안하게 읽고, 세상을 조금 더 깊이.</p></div>{self.feature(page, feature_story)}</section>
<div class="intro-strip"><div class="container"><span>{len(self.stories)}편의 이야기</span><p>읽는 즐거움에, 믿을 만한 근거를 더합니다.</p><span aria-hidden="true">✳</span></div></div>
<section id="fields" class="container fields-section"><div class="section-heading"><div><p class="eyebrow">FOLLOW YOUR CURIOSITY</p><h2>{jump_name}</h2></div></div><div class="field-grid split-fields">{fields}</div><div class="library-shortcuts"><a class="button" href="library.html">전체 이야기 서가 ↗</a><a class="text-link" href="reading.html">내 읽기 목록 ↗</a></div></section>
<section class="container story-shelf"><div class="section-heading"><div><p class="eyebrow">A LITTLE FURTHER</p><h2>오늘, 이 이야기부터</h2></div><a class="text-link" href="search.html">모든 이야기 ↗</a></div><div class="story-grid">{storycards}</div></section>'''
        self.layout(page, self.brand_label, re.sub('<[^>]+>', ' ', description), body)

    def category(self, category, child=None):
        if self.domain == 'kr':
            return super().category(category, child)
        cid = category['id']
        page = self.category_path(cid, child)
        subset = [s for s in self.stories if s['category'] == cid and (child is None or s['subcategory'] == child)]
        title = child or category['title']
        crumb = f'<a href="{self.link(page, "index.html")}">처음</a> / <a href="{self.link(page, self.category_path(cid))}">{esc(category["title"])}</a>'
        top = f'<nav class="breadcrumbs" aria-label="현재 위치">{crumb}</nav><header class="page-heading"><p class="eyebrow">국가와 이야기</p><h1>{esc(title)}</h1><p>{esc(category["intro"]) if child is None else "역사와 도시, 작품과 일상에서 이곳의 이야기를 만납니다."}</p></header>'
        if child is None:
            mains = self.taxonomy['net'][category['title']]
            extras = [ch for ch in category['children'] if ch not in mains and ch != '지역에 걸친 이야기']
            def country_cards(children):
                result = ''
                for c in children:
                    count = sum(s['subcategory'] == c for s in subset)
                    result += f'<a class="country-tile" href="{self.link(page, self.category_path(cid,c))}"><h3>{esc(c)}</h3><span>{str(count)+"편" if count else "이야기 준비 중"} ↗</span></a>'
                return '<div class="country-grid">'+result+'</div>'
            top += '<h2 class="shelf-title">국가를 골라 읽기</h2>'+country_cards(mains)
            top += '<section id="other-countries"><h2 class="shelf-title">기타 국가</h2>'+country_cards(extras)+'</section>'
            top += '<h2 class="shelf-title">지역에 걸친 이야기</h2>'+country_cards(['지역에 걸친 이야기'])
        else:
            if child == '지역에 걸친 이야기':
                top += '<p class="context-note">여러 국가와 공동체가 공유하는 전승과 생활 이야기입니다. 오늘의 국경이 문화의 범위를 정하지는 않습니다.</p>'
            else:
                top += '<p class="context-note">국가 이름은 이야기를 찾기 위한 길잡이입니다. 과거의 문명과 공동체가 오늘의 국경과 꼭 일치하지는 않습니다.</p>'
            labels = self.taxonomy['country_content_labels']
            top += '<nav class="chips country-filters" aria-label="이야기 종류">'+''.join(f'<a class="chip" href="#label-{n}">{esc(label)} <span>{sum(s["placement"]["topic"]==label for s in subset)}</span></a>' for n,label in enumerate(labels))+'</nav>'
            for n, label in enumerate(labels):
                selected = [s for s in subset if s['placement']['topic'] == label]
                listing = '<div class="story-grid">'+''.join(self.card(page,s) for s in selected)+'</div>' if selected else '<p class="topic-empty">아직 공개된 이야기가 없습니다.</p>'
                top += f'<section id="label-{n}" class="country-section"><h2 class="shelf-title">{label}</h2>{listing}</section>'
        if child is None:
            top += f'<h2 class="shelf-title">이 지역의 이야기 · {len(subset)}편</h2><div class="story-grid">'+''.join(self.card(page,s) for s in subset)+'</div>'
        self.layout(page, title, category['intro'], '<section class="container category-page">'+top+'</section>',cid)

    def library(self):
        super().library()
        old = f'8개 분야, 43개 소주제에서 한 편씩 골라 읽어 보세요. 현재 이 화면에는 {len(self.stories)}편이 있습니다.'
        new = f'{"지역과 국가" if self.domain == "net" else "주제와 소주제"}별로 정리한 {len(self.stories)}편의 이야기입니다.'
        self.files['library.html'] = self.files['library.html'].replace(old,new).replace('소주제별 서가','전체 이야기 서가')

    def render(self):
        # Collection manifests refer to the old combined taxonomy, so they are not republished here.
        self.home()
        for c in self.categories:
            self.category(c)
            for child in c['children']:
                self.category(c,child)
        for s in self.stories:
            self.story(s)
        self.search()
        self.library()
        self.reading()
        return self.files


def build():
    taxonomy = read_json(ROOT/'config/proposals/net-kr-taxonomy.json')
    placements = read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
    originals = load_stories()
    validate(read_json(ROOT/'config/categories.json'),originals)
    originals = {s['id']:s for s in originals}
    counts = {}
    for domain in ['net','kr']:
        categories, stories = prepare(domain,taxonomy,placements,originals)
        site = SplitSite(domain,categories,stories,taxonomy)
        files = site.render()
        destination = DEST/domain
        for name, content in files.items():
            path = destination/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8')
        assetdir = destination/'site-assets'
        assetdir.mkdir(exist_ok=True)
        for source in (ROOT/'site').iterdir():
            if source.is_file():
                (assetdir/source.name).write_bytes(source.read_bytes())
        (assetdir/'split.css').write_text((ROOT/'tools/templates/split-preview.css').read_text())
        for s in site.stories:
            require((destination/site.image_path(s)).is_file(),f'Missing published image: {s["id"]}')
        counts[domain] = {'stories':len(stories),'html_pages':sum(name.endswith('.html') for name in files)}
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'index.html').write_text('''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>KnowledgeWalk 개편 미리보기</title><style>body{margin:0;background:#faf8f3;color:#203b30;font-family:system-ui,sans-serif;line-height:1.9}main{max-width:850px;margin:8vh auto;padding:24px}h1{font-size:clamp(30px,5vw,48px);line-height:1.4}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin:35px 0}a.card{display:block;border:1px solid #c7cbbc;border-radius:12px;padding:28px;color:inherit;text-decoration:none;background:#fff}a.card:hover{border-color:#203b30}a{color:inherit}small{color:#59675d}h2{margin-top:0}</style></head><body><main><small>KNOWLEDGEWALK · 개편 미리보기</small><h1>국가를 따라 걷고,<br>발견의 이야기를 읽습니다.</h1><p>하나의 KnowledgeWalk, 두 가지 읽는 길을 준비했습니다.<br>현재 홈페이지와 도메인 연결은 그대로 유지됩니다.</p><section><a class="card" href="net/index.html"><h2>국가와 이야기 ↗</h2><p>knowledgewalk.net</p><p>아시아대양주 · 유럽 · 아메리카 · 중동아프리카<br>국가별 역사·도시·문화·생활 이야기</p></a><a class="card" href="kr/index.html"><h2>발견과 지식 ↗</h2><p>knowledgewalk.kr</p><p>기업 · 컴퓨터 · 금융 · 과학<br>생활을 바꾼 발명과 생각의 역사</p></a></section><p>이미 게시 승인을 받은 글만 담았습니다. 이미지, 출처, 번호 소제목과 옆 바로가기, 읽음 표시를 함께 확인하실 수 있습니다.</p><small>현재는 두 화면 모두 net 안의 미리보기 주소입니다. kr 도메인은 아직 전환하지 않았습니다. 미리보기의 읽음 표시와 현재 홈페이지의 읽음 표시는 같은 브라우저에서 공유됩니다.</small><p><a href="../../index.html">현재 홈페이지로 돌아가기 ↗</a></p></main></body></html>''')
    print(json.dumps(counts,ensure_ascii=False,indent=2))
    return counts


if __name__ == '__main__':
    build()
