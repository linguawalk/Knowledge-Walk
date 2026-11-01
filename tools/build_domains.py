#!/usr/bin/env python3
"""Build independent net/kr sites and preserve existing net article links."""
import argparse
import json
import posixpath
import shutil
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED
from build_site import ROOT, Site, esc, load_stories, publishable, read_json, require, validate
from build_split_preview import SplitSite, prepare


class DomainSite(SplitSite):
    def __init__(self, domain, categories, stories, taxonomy, settings, bridge=False):
        super().__init__(domain,categories,stories,taxonomy)
        self.settings=settings
        self.bridge=bridge

    def link(self,page,target):
        if urlsplit(target).scheme:
            return esc(target)
        # Virtual deep root avoids cwd-dependent relpaths while allowing preview-shared helpers.
        base='/website/site/'
        return esc(posixpath.relpath(posixpath.normpath(base+target),posixpath.normpath(base+str(Path(page).parent))))

    def image_path(self,story):
        return Site.image_path(self,story)

    def home(self):
        super().home()
        batches=self.active_batches()
        if batches:
            batch,members=batches[0]
            link=f'<a class="text-link" href="collections/{esc(batch["id"])}/index.html">최근 추가한 이야기 {len(members)}편 ↗</a>'
            self.files['index.html']=self.files['index.html'].replace('<div class="library-shortcuts">','<div class="library-shortcuts">'+link,1)

    def search(self):
        super().search()
        if self.domain == "kr":
            self.files["search.html"] = self.files["search.html"].replace("예: 베네치아, 사자, 책", "예: 컴퓨터, 은행, 별")

    def render(self):
        super().render()
        self.collection_pages()
        return self.files

    def layout(self,page,title,description,body,active=None,article=False):
        import re
        super().layout(page,title,description,body,active,article)
        text=self.files[page]
        text=re.sub(r'<div class="preview-banner split-banner">.*?</div>','',text,count=1,flags=re.S)
        text=text.replace('<meta name="robots" content="noindex,nofollow">','')
        if page == '404.html':
            text=text.replace('</head>','<meta name="robots" content="noindex,follow"></head>',1)
        canonical='https://knowledgewalk.'+self.domain+'/'+page
        if self.bridge:canonical='https://knowledgewalk.net/'+self.settings['temporary_kr_path']+'/'+page
        text=text.replace('</head>',f'<link rel="canonical" href="{esc(canonical)}"></head>',1)
        other='https://knowledgewalk.net/' if self.domain=='kr' else ('https://knowledgewalk.kr/' if self.settings['kr_live'] else self.link(page,self.settings['temporary_kr_path']+'/index.html'))
        label='국가와 이야기' if self.domain=='kr' else '발견과 지식'
        switch=f'<a class="site-switch" href="{other}">{label} ↗</a>'
        text=text.replace('<button class="menu-button"',switch+'<button class="menu-button"',1)
        text=text.replace('<small>© 2026 KnowledgeWalk</small>',switch+'<small>© 2026 KnowledgeWalk</small>')
        self.files[page]=text


def redirect_page(title,target,canonical):
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>{esc(title)} · KnowledgeWalk</title><link rel="canonical" href="{esc(canonical)}"><meta http-equiv="refresh" content="0;url={esc(target)}"></head><body><p>이 이야기의 새 페이지로 이동합니다.</p><a href="{esc(target)}">{esc(title)} 읽기</a><script>location.replace({json.dumps(target)}+location.search+location.hash);</script></body></html>'''


def write_site(destination,files,site):
    require(destination in [ROOT/'_site',ROOT/'_kr-site'] or destination.is_relative_to(ROOT/'_site'),'Unexpected build destination')
    destination.mkdir(parents=True,exist_ok=True)
    for name,content in files.items():
        path=destination/name
        require(path.resolve().is_relative_to(destination.resolve()),'Unsafe output path')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
    shutil.copytree(ROOT/'site',destination/'site-assets',dirs_exist_ok=True)
    css=(ROOT/'tools/templates/split-preview.css').read_text()+ '\n.site-switch{font-size:12px;white-space:nowrap;text-decoration:underline;text-underline-offset:4px}.header-inner>.site-switch{margin-left:15px}@media(max-width:1150px){.header-inner>.site-switch{display:none}}\n'
    (destination/'site-assets/split.css').write_text(css)
    for story in site.stories:
        target=destination/site.image_path(story);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/story['image']['file'],target)


def build(sync_root=False):
    settings=read_json(ROOT/'config/deployment.json')
    require(settings['mode']=='split','Split mode is not active')
    require(settings['temporary_kr_path']=='knowledge','Unexpected temporary route')
    taxonomy=read_json(ROOT/'config/proposals/net-kr-taxonomy.json')
    rows=read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
    stories=load_stories();legacy_categories=read_json(ROOT/'config/categories.json');validate(legacy_categories,stories)
    originals={s['id']:s for s in stories};sites={};files={}
    for domain in ['net','kr']:
        categories,mapped=prepare(domain,taxonomy,rows,originals)
        sites[domain]=DomainSite(domain,categories,mapped,taxonomy,settings)
        files[domain]=sites[domain].render()
        sites[domain].layout('404.html','찾는 이야기가 보이지 않아요','다른 이야기에서 다시 시작해 보세요.','<section class="container empty-state"><h1>찾는 이야기가 보이지 않아요.</h1><a href="index.html">첫 화면으로 ↗</a></section>')
        files[domain]=sites[domain].files
        files[domain]['sitemap.xml']='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>https://knowledgewalk.'+domain+'/'+name+'</loc></url>' for name in files[domain] if name.endswith('.html') and name!='404.html')+'</urlset>'
        files[domain]['robots.txt']='User-agent: *\nAllow: /\nSitemap: https://knowledgewalk.'+domain+'/sitemap.xml\n'
    netids={s['id'] for s in sites['net'].stories};krids={s['id'] for s in sites['kr'].stories}
    require(not netids&krids,'Overlapping domain ownership')
    require(netids|krids=={s['id'] for s in stories if publishable(s)},'Missing approved stories')
    def target(story):
        if story['id'] in netids:return Site.story_path(sites['net'],story)
        return ('https://knowledgewalk.kr/' if settings['kr_live'] else 'knowledge/')+Site.story_path(sites['kr'],story)
    for s in sites['kr'].stories:
        path=Site.story_path(sites['kr'],s);dest=target(s)
        rel=dest if dest.startswith('https:') else posixpath.relpath(dest,str(Path(path).parent))
        canonical=dest if dest.startswith('https:') else 'https://knowledgewalk.net/'+dest
        files['net'][path]=redirect_page(s['title'],rel,canonical)
    class LegacySite(Site):
        def story_path(self,story):return target(story)
        def image_path(self,story):
            path=Site.image_path(self,story)
            return path if story['id'] in netids else ('https://knowledgewalk.kr/' if settings['kr_live'] else 'knowledge/')+path
        def link(self,page,target):return esc(target) if target.startswith('https:') else super().link(page,target)
        def layout(self,page,title,description,body,active=None,article=False):
            sites['net'].layout(page,title,description,body,None,article)
            self.files[page]=sites['net'].files[page]
    legacy=LegacySite(legacy_categories,stories)
    for c in legacy_categories:
        legacy.category(c)
        for ch in c['children']:legacy.category(c,ch)
    legacy.collection_pages()
    files['net'].update(legacy.files)
    # Independently staged artifacts: only disposable generated directories are replaced.
    for folder in [ROOT/'_site',ROOT/'_kr-site']:
        require(not folder.is_symlink(),'Output directory cannot be a symlink')
        if folder.exists():shutil.rmtree(folder)
    write_site(ROOT/'_site',files['net'],sites['net']);write_site(ROOT/'_kr-site',files['kr'],sites['kr'])
    if not settings['kr_live']:
        kr=sites['kr'];bridge=DomainSite('kr',kr.categories,kr.stories,taxonomy,settings,bridge=True)
        write_site(ROOT/'_site/knowledge',bridge.render(),bridge)
    # Keep old preview URLs functional; their media refer to the original net root.
    for s in sites['kr'].stories:
        path=ROOT/'_site'/Site.image_path(sites['kr'],s);path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/s['image']['file'],path)
    (ROOT/'_kr-site/.htaccess').write_text('DirectoryIndex index.html index.php\nErrorDocument 404 /404.html\n')
    (ROOT/'_kr-site/knowledgewalk-deployment.json').write_text(json.dumps({'site':'knowledgewalk.kr','stories':len(krids),'ids':sorted(krids)},ensure_ascii=False))
    if sync_root:
        for source in (ROOT/'_site').rglob('*'):
            if source.is_file():
                dest=ROOT/source.relative_to(ROOT/'_site');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        allowed={p.relative_to(ROOT/'_site').parts[0] for p in (ROOT/'_site').rglob('*') if p.is_file()}
        # Existing approved, noindex previews stay public; private source files remain excluded.
        allowed.add('collections')
        excluded=sorted(p.name+('/*' if p.is_dir() else '') for p in ROOT.iterdir() if p.name not in allowed|{'_config.yml','CNAME'})
        (ROOT/'_config.yml').write_text(json.dumps({'exclude':excluded},indent=2)+'\n')
    return dict(mode='split',pages=sum(1 for p in (ROOT/'_site').rglob('*.html')),included=sorted(netids|krids),net_included=sorted(netids),kr_included=sorted(krids),excluded=len(stories)-len(netids|krids),output=str(ROOT/'_site'),kr_output=str(ROOT/'_kr-site'),kr_live=settings['kr_live'])


def package_kr():
    folder=ROOT/'downloads';folder.mkdir(exist_ok=True);target=folder/'knowledgewalk-kr-site.zip'
    with ZipFile(target,'w',ZIP_DEFLATED) as archive:
        for p in sorted((ROOT/'_kr-site').rglob('*')):
            if p.is_file():archive.write(p,p.relative_to(ROOT/'_kr-site'))
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--sync-root',action='store_true');parser.add_argument('--package-kr',action='store_true');args=parser.parse_args()
    print(json.dumps(build(args.sync_root),ensure_ascii=False,indent=2))
    if args.package_kr:print(package_kr())
