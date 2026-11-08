"""Regional and subject navigation over one approved, canonical story catalog."""
import copy
import json
import re
from build_site import Site, esc, require, publishable, slug, read_json, ROOT

INTRO = {
    '유럽':'동·서·남·북·중부유럽의 국가와 이야기로 여행합니다.',
    '아시아':'동·서·남·동남·중앙아시아의 역사와 생활을 만납니다.',
    '아메리카':'북·중앙·남아메리카의 도시와 사람, 변화를 읽습니다.',
    '아프리카':'오래된 교역로와 도시, 다양한 공동체의 이야기를 읽습니다.',
    '대양주':'바다로 이어진 지역의 역사와 생활을 만납니다.',
    '역사':'국가와 권력, 전쟁과 외교, 법과 개혁의 시간을 따라갑니다.',
    '도시와 사회':'도시와 교통, 노동과 이주, 주거와 재난의 역사를 읽습니다.',
    '문화와 예술':'문학과 음악, 미술과 건축, 전승과 공연을 만납니다.',
    '경제·산업·금융':'화폐와 은행, 무역과 기업, 생산과 시장의 변화를 읽습니다.',
    '과학과 발견':'우주와 생명, 물질과 환경을 이해하게 된 과정을 살펴봅니다.',
    '기술과 디지털':'도구와 기계에서 컴퓨터와 인공지능까지 발명의 조건을 읽습니다.',
    '생각과 지식':'철학과 세계관, 배움과 기록, 책이 지식을 전하는 방식을 읽습니다.',
    '세계와 교류':'특정 국가에 한정되지 않는 발견과 지식, 생활의 이야기를 만납니다.',
}


def enabled(taxonomy):
    return taxonomy.get('version', 1) >= 2


def prepare(domain, taxonomy, placements, originals):
    require({r['id'] for r in placements} == set(originals), 'Placement coverage differs from canonical stories')
    require(len({r['id'] for r in placements}) == len(placements), 'Duplicate placements')
    rows = [r for r in placements if publishable(originals[r['id']])]
    for row in rows:
        require(row['primary_subject'] == row['kr_topics'][0], 'Primary subject must be the first subject')
        require(len({(t['topic'],t['subtopic']) for t in row['kr_topics']}) == len(row['kr_topics']), 'Duplicate subject membership')
        for t in row['kr_topics']:
            require(t['subtopic'] in taxonomy['kr'].get(t['topic'], []), 'Invalid subject classification')
        for geo in row['geographies']:
            require(geo['continent'] in taxonomy['geography'], 'Unknown continent')
            if geo.get('subregion'):
                require(geo['subregion'] in taxonomy['geography'][geo['continent']], 'Unknown subregion')
    categories = []
    if domain == 'net':
        for continent, cid in taxonomy['continent_ids'].items():
            countries = sorted({g['country'] for r in rows for g in r['geographies'] if g['continent']==continent and g.get('country')})
            if any(g['continent']==continent and not g.get('country') for r in rows for g in r['geographies']):
                countries.append('지역에 걸친 이야기')
            regions = list(taxonomy['geography'][continent]) if continent not in ['아프리카','대양주'] else []
            categories.append(dict(id=cid,title=continent,label=continent,intro=INTRO[continent],children=countries,regions=regions))
        label=taxonomy['world_label']
        categories.append(dict(id='common',title=label,label=label,intro=INTRO[label],children=[label],regions=[]))
    else:
        for title, children in taxonomy['kr'].items():
            active=[child for child in children if any({'topic':title,'subtopic':child} in r['kr_topics'] for r in rows)]
            categories.append(dict(id=taxonomy['topic_ids'][title],title=title,label=title,intro=INTRO[title],children=active))
    mapped=[]
    for row in rows:
        story=copy.deepcopy(originals[row['id']]);story['placement']=copy.deepcopy(row)
        if domain=='net':
            story['category']=taxonomy['continent_ids'][row['region']] if row.get('region') else 'common'
            story['subcategory']=row.get('country') or ('지역에 걸친 이야기' if row.get('region') else taxonomy['world_label'])
            cats=[taxonomy['continent_ids'][g['continent']] for g in row['geographies']]
            if story['category']=='common':cats.append('common')
            story['search_categories']=list(dict.fromkeys(cats))
        else:
            p=row['primary_subject'];story['category']=taxonomy['topic_ids'][p['topic']];story['subcategory']=p['subtopic']
            story['search_categories']=list(dict.fromkeys(taxonomy['topic_ids'][t['topic']] for t in row['kr_topics']))
        mapped.append(story)
    return categories,mapped


class Navigation:
    """Methods delegated to by SplitSite only for navigation version2."""
    def in_category(self, story, cid):
        row=story['placement']
        if self.domain=='kr':return any(self.taxonomy['topic_ids'][t['topic']]==cid for t in row['kr_topics'])
        if cid=='common':return story['category']=='common'
        return any(self.taxonomy['continent_ids'][g['continent']]==cid for g in row['geographies'])

    def menu(self,page,active):
        nav=''
        for c in self.categories:
            if c['id']=='common':
                nav+=f'<a class="nav-direct" href="{self.link(page,self.category_path(c["id"]))}">{esc(c["title"])}</a>'
                continue
            children=c.get('regions') or c['children']
            links=''.join(f'<li><a href="{self.link(page,self.category_path(c["id"],ch))}">{esc(ch)}</a></li>' for ch in children)
            nav+=(f'<details class="nav-group{" active" if active==c["id"] else ""}"><summary>{esc(c["title"])}<span aria-hidden="true">⌄</span></summary><ul>'
                  f'<li><a href="{self.link(page,self.category_path(c["id"]))}">전체 이야기 ↗</a></li>{links}</ul></details>')
        return nav

    def layout(self,page,title,description,body,active=None,article=False):
        Site.layout(self,page,title,description,body,active,article)
        markup=self.files[page]
        if article and self.domain=='net':
            story=next((s for s in self.stories if self.story_path(s)==page),None)
            row=story['placement'] if story else {}
            if row.get('region') and row.get('subregion'):
                cid=self.taxonomy['continent_ids'][row['region']]
                anchor=f'<a href="{self.link(page,self.category_path(cid))}">{esc(row["region"])}</a>'
                regional=f'<span aria-hidden="true">/</span><a href="{self.link(page,self.category_path(cid,row["subregion"]))}">{esc(row["subregion"])}</a>'
                markup=re.sub(r'(<nav class="breadcrumbs".*?</nav>)',lambda m:m.group(1).replace(anchor,anchor+regional,1),markup,count=1,flags=re.S)
        markup=re.sub(r'<nav id="main-nav".*?</nav>', '<nav id="main-nav" class="main-nav" aria-label="주요 메뉴">'+Navigation.menu(self,page,active)+'</nav>',markup,count=1,flags=re.S)
        markup=markup.replace('<head>','<head><meta name="robots" content="noindex,nofollow">',1)
        other='kr' if self.domain=='net' else 'net';label='지역별' if self.domain=='net' else '주제별'
        banner=f'<div class="preview-banner split-banner"><span>개편 미리보기 · {label}</span><a href="{self.link(page,"../"+other+"/index.html")}">다른 보기 ↗</a></div>'
        markup=markup.replace('<body>',f'<body class="split-{self.domain} navigation-v2">{banner}',1)
        markup=markup.replace('</head>',f'<link rel="stylesheet" href="{self.link(page,"site-assets/split.css")}"></head>',1)
        markup=markup.replace('분야 보기','메뉴 보기').replace('Knowledge<span>Walk</span><i',f'Knowledge<span>Walk</span><small class="brand-section">{"지역과 이야기" if self.domain=="net" else "발견과 지식"}</small><i')
        self.files[page]=markup

    def card(self,page,story):
        row=story['placement'];p=row['primary_subject']
        attrs={
            'data-catalog-text':' '.join([story['title'],story['summary'],row.get('country') or '',*[t['topic']+' '+t['subtopic'] for t in row['kr_topics']],*row.get('people',[])]),
            'data-catalog-topics':json.dumps(list(dict.fromkeys([v for t in row['kr_topics'] for v in [t['topic'],t['subtopic']]])),ensure_ascii=False),
            'data-catalog-facets':json.dumps(row.get('facets',[]),ensure_ascii=False),
            'data-catalog-countries':json.dumps(list(dict.fromkeys(g['country'] for g in row['geographies'] if g.get('country'))),ensure_ascii=False),
            'data-catalog-primary':p['topic'],'data-catalog-primary-subtopic':p['subtopic'],
        }
        result=Site.card(self,page,story)
        return result.replace('<article class="story-card"', '<article class="story-card" '+ ' '.join(k+'="'+esc(v)+'"' for k,v in attrs.items()),1)

    def catalog(self,page,stories,topics=None,facets=None,countries=False,scope=None):
        def select(name,label,options):
            return f'<label>{label}<select data-filter="{name}"><option value="">전체</option>'+''.join(f'<option value="{esc(x)}">{esc(x)}</option>' for x in options)+'</select></label>'
        controls=''
        if topics:controls+=select('topics','주제' if self.domain=='net' else '소주제',topics)
        if facets:
            present=[f for f in facets if any(f in s['placement'].get('facets',[]) for s in stories)]
            if present:controls+=select('facets','종류',present)
        if countries:
            names=sorted({g['country'] for s in stories for g in s['placement']['geographies'] if g.get('country')})
            if names:controls+=select('countries','국가',names)
        if scope:
            controls+=f'<label class="catalog-check"><input type="checkbox" data-primary-topic="{esc(scope[0])}" data-primary-subtopic="{esc(scope[1] or "")}">대표 분류만 보기</label>'
        cards=''.join(self.card(page,s) for s in stories)
        return (f'<section class="catalog" data-catalog><form class="catalog-controls" hidden><label>목록에서 찾기<input type="search" name="q" placeholder="제목·주제·인물 검색" autocomplete="off"></label>{controls}<button type="reset" class="chip">초기화</button></form>'
                f'<p class="catalog-status" role="status" aria-live="polite">{len(stories)}편의 이야기</p><div class="story-grid catalog-results">{cards}</div><p class="empty-state catalog-empty" hidden>조건에 맞는 이야기가 없습니다. 다른 조건으로 찾아보세요.</p></section>')

    def home(self):
        page='index.html';net=self.domain=='net'
        feature_id='venice-winged-lion' if net else 'ford-moving-assembly'
        feature=next((s for s in self.stories if s['id']==feature_id),self.stories[0])
        cards=''
        for n,c in enumerate(self.categories,1):
            selected=[s for s in self.stories if self.in_category(s,c['id'])]
            primary=sum(s['category']==c['id'] for s in self.stories)
            labels=c.get('regions') or c['children']
            counts=f'{len(selected)}편의 이야기' if net else (f'대표 {primary}편'+(f' · 관련 {len(selected)-primary}편' if len(selected)>primary else ''))
            cards+=(f'<a class="field-card" href="{self.link(page,self.category_path(c["id"]))}"><div class="field-top"><span>{n:02d}</span><span>↗</span></div><h3>{esc(c["title"])}</h3><p class="field-label">{esc(" · ".join(labels))}</p><p>{esc(c["intro"])}</p><span class="field-meta">{counts}</span></a>')
        picks=[]
        for c in self.categories:
            selected=[s for s in self.stories if s['category']==c['id'] and s['id']!=feature['id']]
            for s in selected[:2]:
                if s['id'] not in {p['id'] for p in picks}:picks.append(s)
        heading='지역을 따라,<br>이야기를 만납니다.' if net else '궁금한 주제로,<br>세상을 읽습니다.'
        description='다섯 대륙과 그 안의 지역, 국가를 따라<br>역사와 도시, 문화와 생활의 이야기를 만납니다.' if net else '역사와 사회에서 예술과 과학까지.<br>일곱 주제로 같은 이야기를 새롭게 발견합니다.'
        body=f'<section class="container hero"><div class="hero-copy"><p class="eyebrow">KNOWLEDGEWALK · {"지역과 이야기" if net else "발견과 지식"}</p><h1>{heading}</h1><p class="hero-description">{description}</p><a class="button" href="#fields">{"지역" if net else "주제"} 둘러보기 ↓</a></div>{self.feature(page,feature)}</section><div class="intro-strip"><div class="container"><span>{len(self.stories)}편의 이야기</span><p>한 글은 관련된 여러 지역과 주제에서 만날 수 있습니다.</p><span>✳</span></div></div><section id="fields" class="container fields-section"><div class="section-heading"><h2>{"지역과 국가로 읽기" if net else "일곱 주제로 읽기"}</h2></div><div class="field-grid split-fields">{cards}</div><div class="library-shortcuts"><a class="button" href="library.html">전체 이야기 서가 ↗</a><a class="text-link" href="reading.html">내 읽기 목록 ↗</a></div></section><section class="container story-shelf"><div class="section-heading"><h2>이 이야기부터</h2><a class="text-link" href="search.html">모든 이야기 ↗</a></div><div class="story-grid">'+''.join(self.card(page,s) for s in picks[:9])+'</div></section>'
        self.layout(page,'지역과 이야기' if net else '발견과 지식',re.sub('<[^>]+>',' ',description),body)

    def category(self,category,child=None):
        cid=category['id'];page=self.category_path(cid,child);title=child or category['title'];net=self.domain=='net';is_region=net and child in category.get('regions',[])
        if net:
            def matches(s):
                if cid=='common':return s['category']=='common'
                geos=[g for g in s['placement']['geographies'] if self.taxonomy['continent_ids'][g['continent']]==cid]
                if child is None:return bool(geos)
                if is_region:return any(g.get('subregion')==child for g in geos)
                if child=='지역에 걸친 이야기':return any(not g.get('country') for g in geos)
                return any(g.get('country')==child for g in geos)
            selected=[s for s in self.stories if matches(s)]
            if cid!='common':
                selected=[dict(s,category=cid,subcategory=(child if child and not is_region else next((g.get('country') or '지역에 걸친 이야기' for g in s['placement']['geographies'] if g['continent']==category['title'] and (not is_region or g.get('subregion')==child)),s['subcategory']))) for s in selected]
        else:
            selected=[]
            for s in self.stories:
                ts=[t for t in s['placement']['kr_topics'] if t['topic']==category['title'] and (child is None or t['subtopic']==child)]
                if ts:selected.append(dict(s,category=cid,subcategory=ts[0]['subtopic']))
        crumb=f'<a href="{self.link(page,"index.html")}">처음</a> / <a href="{self.link(page,self.category_path(cid))}">{esc(category["title"])}</a>'
        if net and child and not is_region and cid!='common':
            subregion=next((g.get('subregion') for s in selected for g in s['placement']['geographies'] if g.get('country')==child and g['continent']==category['title']),None)
            if subregion:crumb+=f' / <a href="{self.link(page,self.category_path(cid,subregion))}">{esc(subregion)}</a>'
        count=f'{len(selected)}편의 이야기'
        if not net:
            primary=sum(s['placement']['primary_subject']['topic']==category['title'] and (child is None or s['placement']['primary_subject']['subtopic']==child) for s in selected)
            count=f'대표 {primary}편 · 관련 포함 {len(selected)}편' if len(selected)>primary else f'{primary}편의 이야기'
        intro={'문학':'소설·희곡·시와 서사, 산문과 작가의 이야기를 골라 읽습니다.','음악':'작곡가와 작품, 악기와 공연의 이야기를 만납니다.','미술':'회화·조각·공예·사진 속에 담긴 이야기와 표현을 살펴봅니다.','건축':'주거와 종교건축, 궁전과 공공건축의 공간을 읽습니다.'}.get(child,category['intro'])
        top=f'<nav class="breadcrumbs" aria-label="현재 위치">{crumb}</nav><header class="page-heading"><p class="eyebrow">{"지역과 이야기" if net else "발견과 지식"}</p><h1>{esc(title)}</h1><p>{esc(intro)}</p><p>{count}</p></header>'
        if net and cid!='common':
            if child is None and category.get('regions'):
                tiles=''
                for region in category['regions']:
                    n=sum(any(g['continent']==category['title'] and g.get('subregion')==region for g in s['placement']['geographies']) for s in selected)
                    tiles+=f'<a class="country-tile" href="{self.link(page,self.category_path(cid,region))}"><h2>{esc(region)}</h2><span>{str(n)+"편" if n else "이야기 준비 중"} ↗</span></a>'
                top+='<h2 class="shelf-title">지역으로 읽기</h2><div class="country-grid">'+tiles+'</div>'
            if child is None or is_region:
                names=sorted({g['country'] for s in selected for g in s['placement']['geographies'] if g['continent']==category['title'] and g.get('country') and (not is_region or g.get('subregion')==child)})
                tiles=''
                for country in names:
                    n=sum(any(g['continent']==category['title'] and g.get('country')==country for g in s['placement']['geographies']) for s in selected)
                    tiles+=f'<a class="country-tile" href="{self.link(page,self.category_path(cid,country))}"><h3>{esc(country)}</h3><span>{n}편 ↗</span></a>'
                if tiles:top+='<section id="other-countries"><h2 class="shelf-title">국가별 이야기</h2><div class="country-grid">'+tiles+'</div></section>'
            top+='<p class="context-note">지역과 국가는 이야기를 찾는 길잡이입니다. 과거의 공동체와 문화가 오늘의 국경과 꼭 일치하지는 않습니다.</p>'
            top+=''.join(f'<span id="label-{i}" class="legacy-anchor"></span>' for i in range(4))
        if not selected:top+='<p class="empty-state">아직 공개된 이야기가 없습니다. 다른 지역의 이야기를 먼저 만나보세요.</p>'
        else:
            topics=list(self.taxonomy['kr']) if net else category['children'] if child is None else None
            top+=Navigation.catalog(self,page,selected,topics=topics,facets=self.taxonomy.get('facets',{}).get(child),countries=net and (is_region or child is None),scope=None if net or primary==len(selected) else (category['title'],child))
        self.layout(page,title,category['intro'],'<section class="container category-page">'+top+'</section>',cid)

    def library(self):
        page='library.html'
        top=f'<header class="page-heading"><p class="eyebrow">EXPLORE THE CATALOG</p><h1>전체 이야기 서가</h1><p>{len(self.stories)}편을 한 번씩 담았습니다. 주제와 국가, 제목으로 좁혀 읽어 보세요.</p></header>'
        body=top+Navigation.catalog(self,page,self.stories,topics=list(self.taxonomy['kr']),countries=True)
        self.layout(page,'전체 이야기 서가','지역과 주제로 찾는 모든 이야기','<section class="container">'+body+'</section>')

    def search(self):
        Site.search(self)
        index=json.loads(self.files['search-index.json']);lookup={s['id']:s['placement'] for s in self.stories}
        for item in index:
            row=lookup[item['id']];item.update(primary_subject=row['primary_subject'],subjects=row['kr_topics'],geographies=row['geographies'],facets=row.get('facets',[]),people=row.get('people',[]))
            item['text']+=' '+' '.join([v for g in row['geographies'] for v in g.values() if v]+[v for t in row['kr_topics'] for v in t.values()]+row.get('facets',[])+row.get('people',[]))
        self.files['search-index.json']=json.dumps(index,ensure_ascii=False,separators=(',',':'))+'\n'
        self.files['search-index.js']='window.KNOWLEDGEWALK_SEARCH = '+json.dumps(index,ensure_ascii=True)+';\n'

    def legacy_pages(self):
        legacy=read_json(ROOT/'config/navigation-legacy-v1.json')['routes'][self.domain];lookup={s['id']:s for s in self.stories}
        for page,entry in legacy.items():
            if page in self.files:continue
            selected=[lookup[sid] for sid in entry['ids'] if sid in lookup]
            body=f'<section class="container"><header class="page-heading"><h1>{esc(entry["title"])} 이야기</h1><p>새로운 지역별·주제별 메뉴에서도 같은 글을 찾아보세요.</p><a href="{self.link(page,"library.html")}">전체 서가 ↗</a></header>'
            body+=Navigation.catalog(self,page,selected,topics=list(self.taxonomy['kr']))+'</section>'
            self.layout(page,entry['title'],'이전 목록의 이야기와 새로운 탐색 경로',body)
            self.files[page]=self.files[page].replace('</head>','<meta name="robots" content="noindex,follow"></head>',1)

    def render(self):
        self.home()
        for c in self.categories:
            self.category(c)
            for child in c['children']:self.category(c,child)
            for region in c.get('regions',[]):self.category(c,region)
        for story in self.stories:self.story(story)
        self.search();self.library();self.reading();Navigation.legacy_pages(self)
        return self.files
