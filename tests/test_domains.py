"""Real domain ownership, independent assets and old-link preservation."""
import json
import pathlib
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from unittest.mock import patch
from urllib.parse import unquote,urlsplit
from zipfile import ZipFile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_domains as domains


class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        self.urls.extend(a[k] for k in ['href','src'] if a.get(k))
        if a.get('id'):self.ids.add(a['id'])


class DomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=domains.build()
        cls.net=ROOT/'_site';cls.kr=cls.net/'knowledge'
        cls.originals={s['id']:s for s in domains.load_stories()}

    def test_shared_search_catalogs_are_complete_and_identical(self):
        net={s['id'] for s in domains.read_json(self.net/'search-index.json')}
        kr={s['id'] for s in domains.read_json(self.kr/'search-index.json')}
        self.assertEqual(net,kr)
        self.assertEqual(net,{s['id'] for s in self.originals.values() if domains.publishable(s)})
        self.assertIn('venice-winged-lion',net);self.assertIn('ford-moving-assembly',kr)

    def test_subject_view_has_correct_net_canonicals_and_internal_assets(self):
        for path in self.kr.rglob('*.html'):
            text=path.read_text();self.assertNotIn('개편 미리보기',text)
            relative=path.relative_to(self.kr).as_posix()
            expected='https://knowledgewalk.net/knowledge/'+relative
            if relative.startswith('stories/'):
                rows=domains.read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
                row=next(r for r in rows if r['id']==path.parent.name)
                expected=domains.canonical_story_url({'id':row['id'],'placement':row},domains.read_json(ROOT/'config/deployment.json'))
            self.assertIn('rel="canonical" href="'+expected+'"',text)
            parser=Links();parser.feed(text)
            for url in parser.urls:
                u=urlsplit(url)
                if u.scheme or u.netloc:continue
                target=(path.parent/unquote(u.path)).resolve() if u.path else path.resolve()
                self.assertTrue(target.is_relative_to(self.net),url)
                self.assertTrue(target.is_file(),(path,url))
                if u.fragment and target.suffix=='.html':
                    other=Links();other.feed(target.read_text());self.assertIn(unquote(u.fragment),other.ids,(path,url))
        self.assertFalse((self.kr/'CNAME').exists())
        self.assertFalse((ROOT/'_kr-site').exists())

    def test_old_kr_article_links_now_render_full_shared_body(self):
        for sid in self.result['kr_included']:
            page=(self.net/'stories'/sid/'index.html').read_text()
            self.assertIn('<article class="reading-page">',page)
            self.assertNotIn('location.replace',page)
            self.assertTrue((self.net/'knowledge/stories'/sid/'index.html').is_file())
            original=self.originals[sid]
            self.assertEqual(page.count('class="section-number"'),sum(bool(b.get('heading')) for b in original['body']))
        self.assertIn('https://knowledgewalk.net/stories/venice-winged-lion/index.html', (self.net/'stories/venice-winged-lion/index.html').read_text())

    def test_country_and_music_share_one_article_and_canonical(self):
        sid='fur-elise-title-and-theme'
        self.assertIn(sid,(self.kr/'categories/arts/음악/index.html').read_text())
        self.assertIn(sid,(self.net/'categories/europe/독일/index.html').read_text())
        for output in [self.net,self.kr,self.net/'knowledge']:
            page=(output/'stories'/sid/'index.html').read_text()
            self.assertEqual(page.count('rel="canonical"'),1)
            self.assertIn('rel="canonical" href="https://knowledgewalk.net/stories/'+sid+'/index.html"',page)
            self.assertIn('국가와 분야로 읽기',page)
        crc='crc-checksum-detecting-changed-data'
        self.assertIn(crc,(self.net/'categories/common/index.html').read_text())
        for path in self.net.glob('categories/*/*/index.html'):
            if path.relative_to(self.net).parts[1] in ['asia-oceania','europe','americas','middle-east-africa']:self.assertNotIn('data-story-id="'+crc+'"',path.read_text())

    def test_secondary_subject_membership_and_canonical_sitemap(self):
        sid='penny-post-1840-price-prepayment-and-letters'
        for path in ['categories/history-cities/역사와-제도/index.html','categories/ideas/기록과-지식-전달/index.html']:
            page=(self.kr/path).read_text()
            self.assertEqual(page.count('data-story-id="'+sid+'"'),1)
        index=domains.read_json(self.kr/'search-index.json')
        self.assertEqual(set(next(s for s in index if s['id']==sid)['categories']),{'history','ideas'})
        self.assertFalse((self.net/'knowledge/media').exists())
        sitemap=(self.net/'sitemap.xml').read_text()
        self.assertIn('https://knowledgewalk.net/stories/fur-elise-title-and-theme/index.html',sitemap)
        self.assertNotIn('https://knowledgewalk.net/knowledge/stories/fur-elise-title-and-theme/index.html',sitemap)
        self.assertIn('https://knowledgewalk.net/stories/crc-checksum-detecting-changed-data/index.html',sitemap)
        self.assertNotIn('https://knowledgewalk.net/knowledge/stories/',sitemap)

    def test_legacy_shelf_addresses_remain_readable_but_leave_sitemap(self):
        old='categories/history-cities/역사와-제도/index.html'
        page=(self.kr/old).read_text()
        self.assertIn('data-story-id="penny-post-1840-price-prepayment-and-letters"',page)
        self.assertIn('noindex,follow',page)
        self.assertNotIn('https://knowledgewalk.net/knowledge/'+old,(self.net/'sitemap.xml').read_text())

    def test_no_unapproved_story_in_either_site(self):
        for s in self.originals.values():
            if domains.publishable(s):continue
            for output in [self.net,self.kr]:
                self.assertFalse((output/'stories'/s['id']/'index.html').exists())
                for suffix in ['.jpg','.png','.webp']:
                    self.assertFalse((output/'media'/(s['id']+suffix)).exists())

    def test_single_domain_ignores_legacy_external_domain_flag(self):
        cfg=domains.read_json(ROOT/'config/deployment.json');cfg['kr_live']=True
        taxonomy=domains.read_json(ROOT/'config/proposals/net-kr-taxonomy.json')
        rows=domains.read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
        cats,stories=domains.prepare('net',taxonomy,rows,self.originals)
        site=domains.DomainSite('net',cats,stories,taxonomy,cfg);site.home()
        self.assertIn('href="https://knowledgewalk.net/knowledge/"',site.files['index.html'])
        self.assertNotIn('https://knowledgewalk.kr/',site.files['index.html'])
        self.assertNotIn('개편 미리보기',site.files['index.html'])

    def test_single_domain_keeps_general_story_canonical_on_net(self):
        cfg=domains.read_json(ROOT/'config/deployment.json');cfg['kr_live']=True
        tax=domains.read_json(ROOT/'config/proposals/net-kr-taxonomy.json')
        rows=domains.read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
        for domain in ['net','kr']:
            cats,stories=domains.prepare(domain,tax,rows,self.originals)
            site=domains.DomainSite(domain,cats,stories,tax,cfg)
            story=next(s for s in stories if s['id']=='crc-checksum-detecting-changed-data')
            site.story(story)
            page=site.files[site.story_path(story)]
            self.assertIn('rel="canonical" href="https://knowledgewalk.net/stories/'+story['id']+'/index.html"',page)

    def test_single_domain_has_no_external_kr_links_or_upload_artifact(self):
        for path in self.net.rglob('*.html'):
            parser=Links();parser.feed(path.read_text())
            self.assertFalse(any(url.startswith('https://knowledgewalk.kr/') for url in parser.urls),path)
        self.assertFalse((ROOT/'.github/workflows/hostinger-kr.yml').exists())
        self.assertNotIn('Save independent kr site',(ROOT/'.github/workflows/pages.yml').read_text())

    def test_hostinger_zip_puts_site_at_archive_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);folder=root/'_kr-site';folder.mkdir();(folder/'index.html').write_text('ready');(folder/'.htaccess').write_text('DirectoryIndex index.html')
            with patch.object(domains,'ROOT',root):target=domains.package_kr()
            with ZipFile(target) as archive:self.assertEqual(set(archive.namelist()),{'index.html','.htaccess'})

if __name__=='__main__':unittest.main()
