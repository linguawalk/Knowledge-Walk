"""Check split routing, publication isolation, media and article navigation."""
import importlib.util
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import build_split_preview as split


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.urls=[]; self.ids=set(); self.robots=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        self.urls.extend(a[k] for k in ['href','src'] if a.get(k))
        if a.get('id'): self.ids.add(a['id'])
        if tag=='meta' and a.get('name')=='robots' and 'noindex' in a.get('content',''):self.robots=True


class SplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy=split.read_json(ROOT/'config/proposals/net-kr-taxonomy.json')
        cls.rows=split.read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
        cls.originals={s['id']:s for s in split.load_stories()}
        cls.sites={}
        cls.pages={}
        for domain in ['net','kr']:
            categories,stories=split.prepare(domain,cls.taxonomy,cls.rows,cls.originals)
            site=split.SplitSite(domain,categories,stories,cls.taxonomy)
            cls.sites[domain]=site
            for name,body in site.render().items():
                cls.pages[Path(domain)/name]=body

    def test_disjoint_complete_publication(self):
        ids=[s['id'] for site in self.sites.values() for s in site.stories]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(set(ids),{s['id'] for s in self.originals.values() if split.publishable(s)})
        for site in self.sites.values():
            for story in site.stories:
                self.assertEqual(story['body'],self.originals[story['id']]['body'])
                self.assertEqual(story['sources'],self.originals[story['id']]['sources'])

    def test_saved_flags_cannot_publish_unapproved_story(self):
        import copy
        originals=copy.deepcopy(self.originals)
        sample=next(s for s in self.sites['net'].stories)
        originals[sample['id']]['status']='draft'
        _,stories=split.prepare('net',self.taxonomy,self.rows,originals)
        self.assertNotIn(sample['id'],{s['id'] for s in stories})

    def test_other_country_navigation_waits_for_publication_approval(self):
        import copy
        rows = copy.deepcopy(self.rows)
        originals = copy.deepcopy(self.originals)
        sample = self.sites['net'].stories[0]
        row = next(r for r in rows if r['id'] == sample['id'])
        row.update(region='아시아대양주', country_group='기타 국가', country='검토전용국가')
        # A saved published flag must not create an unpublished country's menu or sitemap entry.
        originals[sample['id']]['status'] = 'review'
        categories, _ = split.prepare('net', self.taxonomy, rows, originals)
        self.assertNotIn('검토전용국가', categories[0]['children'])
        originals[sample['id']]['status'] = 'approved'
        categories, _ = split.prepare('net', self.taxonomy, rows, originals)
        self.assertIn('검토전용국가', categories[0]['children'])

    def test_every_page_noindex_and_links_resolve(self):
        for name,body in self.pages.items():
            if name.suffix!='.html':continue
            p=Links();p.feed(body)
            self.assertTrue(p.robots,name)
            for url in p.urls:
                parts=urlsplit(url)
                if parts.scheme or parts.netloc:continue
                target=(split.DEST/name.parent/unquote(parts.path)).resolve()
                if not parts.path: target=(split.DEST/name).resolve()
                self.assertTrue(target.is_relative_to(ROOT),url)
                self.assertTrue(target.exists(),(name,url))
                if parts.fragment and target.suffix=='.html':
                    targetbody=target.read_text();tp=Links();tp.feed(targetbody)
                    self.assertIn(unquote(parts.fragment),tp.ids,(name,url))

    def test_article_numbered_toc_and_images(self):
        for domain,site in self.sites.items():
            for story in site.stories:
                body=self.pages[Path(domain)/site.story_path(story)]
                headings=sum(bool(b.get('heading')) for b in story['body'])
                self.assertEqual(body.count('class="toc-number"'),headings)
                self.assertEqual(body.count('class="section-number"'),headings)
                self.assertIn('aria-label="소제목 바로가기"',body)
                self.assertTrue((split.DEST/domain/site.image_path(story)).is_file())

    def test_country_labels_and_shared_other_buckets(self):
        net=self.sites['net']
        self.assertIn('기타 국가',self.pages[Path('net')/'categories/europe/index.html'])
        country=self.pages[Path('net')/'categories/europe/이탈리아/index.html']
        for label in self.taxonomy['country_content_labels']:self.assertIn(label,country)
        import copy
        categories=copy.deepcopy(net.categories)
        categories[0]['children'].append('검사전용빈국가')
        empty_site=split.SplitSite('net',categories,net.stories,self.taxonomy)
        empty_site.category(categories[0],'검사전용빈국가')
        empty=empty_site.files['categories/asia-oceania/검사전용빈국가/index.html']
        self.assertIn('아직 공개된 이야기가 없습니다.',empty)
        self.assertNotIn('8개 분야, 43개',self.pages[Path('kr/library.html')])


if __name__=='__main__': unittest.main()
