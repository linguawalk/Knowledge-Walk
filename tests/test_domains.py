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
        cls.net=ROOT/'_site';cls.kr=ROOT/'_kr-site'
        cls.originals={s['id']:s for s in domains.load_stories()}

    def test_search_ownership_is_complete_and_disjoint(self):
        net={s['id'] for s in domains.read_json(self.net/'search-index.json')}
        kr={s['id'] for s in domains.read_json(self.kr/'search-index.json')}
        self.assertFalse(net&kr)
        self.assertEqual(net|kr,{s['id'] for s in self.originals.values() if domains.publishable(s)})
        self.assertIn('venice-winged-lion',net);self.assertIn('ford-moving-assembly',kr)

    def test_kr_is_self_contained_and_has_correct_canonicals(self):
        for path in self.kr.rglob('*.html'):
            text=path.read_text();self.assertNotIn('개편 미리보기',text)
            self.assertIn('https://knowledgewalk.kr/'+path.relative_to(self.kr).as_posix(),text)
            parser=Links();parser.feed(text)
            for url in parser.urls:
                u=urlsplit(url)
                if u.scheme or u.netloc:continue
                target=(path.parent/unquote(u.path)).resolve() if u.path else path.resolve()
                self.assertTrue(target.is_relative_to(self.kr),url)
                self.assertTrue(target.is_file(),(path,url))
                if u.fragment and target.suffix=='.html':
                    other=Links();other.feed(target.read_text());self.assertIn(unquote(u.fragment),other.ids,(path,url))
        self.assertFalse((self.kr/'CNAME').exists())
        self.assertIn('DirectoryIndex index.html', (self.kr/'.htaccess').read_text())

    def test_old_kr_article_links_preserve_fragment_and_have_readable_fallback(self):
        for sid in self.result['kr_included']:
            page=(self.net/'stories'/sid/'index.html').read_text()
            self.assertIn('location.search+location.hash',page)
            self.assertIn('../../knowledge/stories/'+sid+'/index.html',page)
            self.assertIn('<a href=',page)
            self.assertTrue((self.net/'knowledge/stories'/sid/'index.html').is_file())
        self.assertIn('https://knowledgewalk.net/stories/venice-winged-lion/index.html', (self.net/'stories/venice-winged-lion/index.html').read_text())

    def test_no_unapproved_story_in_either_site(self):
        for s in self.originals.values():
            if domains.publishable(s):continue
            for output in [self.net,self.kr]:
                self.assertFalse((output/'stories'/s['id']/'index.html').exists())
                for suffix in ['.jpg','.png','.webp']:
                    self.assertFalse((output/'media'/(s['id']+suffix)).exists())

    def test_kr_live_setting_switches_to_real_domain_without_touching_dns(self):
        cfg=domains.read_json(ROOT/'config/deployment.json');cfg['kr_live']=True
        taxonomy=domains.read_json(ROOT/'config/proposals/net-kr-taxonomy.json')
        rows=domains.read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
        cats,stories=domains.prepare('net',taxonomy,rows,self.originals)
        site=domains.DomainSite('net',cats,stories,taxonomy,cfg);site.home()
        self.assertIn('href="https://knowledgewalk.kr/"',site.files['index.html'])
        self.assertNotIn('개편 미리보기',site.files['index.html'])

    def test_hostinger_zip_puts_site_at_archive_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);folder=root/'_kr-site';folder.mkdir();(folder/'index.html').write_text('ready');(folder/'.htaccess').write_text('DirectoryIndex index.html')
            with patch.object(domains,'ROOT',root):target=domains.package_kr()
            with ZipFile(target) as archive:self.assertEqual(set(archive.namelist()),{'index.html','.htaccess'})

if __name__=='__main__':unittest.main()
