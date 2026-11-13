"""The approved catalog keeps its addresses while geographic and subject routes change."""
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_site import load_stories,publishable,read_json
from build_split_preview import prepare,SplitSite


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tax=read_json(ROOT/'config/proposals/net-kr-taxonomy.json')
        cls.rows=read_json(ROOT/'config/proposals/net-kr-story-placement.json')['articles']
        cls.originals={s['id']:s for s in load_stories()}
        cls.sites={}
        for domain in ['net','kr']:
            cats,stories=prepare(domain,cls.tax,cls.rows,cls.originals)
            cls.sites[domain]=SplitSite(domain,cats,stories,cls.tax)

    def test_five_continents_and_thirteen_regional_routes(self):
        site=self.sites['net']
        self.assertEqual([c['title'] for c in site.categories[:-1]],['유럽','아시아','아메리카','아프리카','대양주'])
        self.assertEqual([len(c['regions']) for c in site.categories[:-1]],[5,5,3,0,0])
        mexico=next(r for r in self.rows if r['country']=='멕시코')
        self.assertEqual((mexico['region'],mexico['subregion']),('아메리카','북아메리카'))
        americas=site.category_map['americas'];site.category(americas,'중앙아메리카')
        central=[s for s in site.stories if any(
            g['continent']=='아메리카' and g.get('subregion')=='중앙아메리카'
            for g in s['placement']['geographies'])]
        page=site.files[site.category_path('americas','중앙아메리카')]
        for story in central:
            self.assertIn('data-story-id="'+story['id']+'"',page)
        # Keep the empty-region check independent of the growing approved catalog.
        empty=SplitSite('net',site.categories,[s for s in site.stories if s not in central],self.tax)
        empty.category(empty.category_map['americas'],'중앙아메리카')
        self.assertIn('아직 공개된 이야기가 없습니다',empty.files[empty.category_path('americas','중앙아메리카')])
        site.category(americas,'북아메리카')
        self.assertIn('멕시코',site.files[site.category_path('americas','북아메리카')])

    def test_new_menu_loads_versioned_assets_for_returning_readers(self):
        site=self.sites['net'];site.home();page=site.files['index.html']
        for asset in ['site.js','site.css','split.css']:
            self.assertIn('site-assets/'+asset+'?v=navigation-2',page)

    def test_subject_primary_counts_cover_each_story_once(self):
        site=self.sites['kr'];counts={c['id']:sum(s['category']==c['id'] for s in site.stories) for c in site.categories}
        self.assertEqual(len(counts),7)
        self.assertEqual(sum(counts.values()),len(site.stories))
        self.assertEqual({s['id'] for s in site.stories},{s['id'] for s in self.originals.values() if publishable(s)})
        for story in site.stories:
            self.assertEqual(story['placement']['primary_subject'],story['placement']['kr_topics'][0])

    def test_empty_subjects_do_not_appear_in_menu(self):
        tax=copy.deepcopy(self.tax);tax['kr']['문화와 예술'].append('검사전용빈주제')
        cats,_=prepare('kr',tax,self.rows,self.originals)
        self.assertNotIn('검사전용빈주제',next(c for c in cats if c['id']=='arts')['children'])

    def test_art_facets_are_genres_not_new_top_level_menus(self):
        site=self.sites['kr'];arts=site.category_map['arts'];site.category(arts,'문학')
        body=site.files[site.category_path('arts','문학')]
        for facet in ['소설','희곡','시와 서사']:self.assertIn('value="'+facet+'"',body)
        self.assertIn('data-catalog-primary',body)
        rows={r['id']:r for r in self.rows}
        self.assertEqual(rows['faust-first-part-gretchen-and-desire']['facets'],['희곡'])
        self.assertEqual(rows['diamond-sutra-868-print-and-gift']['primary_subject']['topic'],'생각과 지식')

    def test_scientists_are_classified_by_discovery_with_person_tags(self):
        site=self.sites['kr'];science=site.category_map['science']
        self.assertNotIn('과학자의 발견',science['children'])
        darwin=next(s for s in site.stories if s['id']=='darwin-life-of-observation')
        self.assertEqual(darwin['subcategory'],'생명과 의학')
        self.assertIn('다윈',darwin['placement']['people'])

    def test_cross_region_membership_does_not_duplicate_a_page(self):
        site=self.sites['net'];sid='constantinople-1453-walls-sea-and-new-capital'
        for cid,region in [('europe','동유럽'),('asia','서아시아')]:
            site.category(site.category_map[cid],region)
            page=site.files[site.category_path(cid,region)]
            self.assertEqual(page.count('data-story-id="'+sid+'"'),1)
        self.assertEqual(sum(s['id']==sid for s in site.stories),1)

    def test_legacy_collections_filter_unapproved_members(self):
        site=self.sites['kr'];site.render()
        legacy=read_json(ROOT/'config/navigation-legacy-v1.json')['routes']['kr']
        published={s['id'] for s in site.stories}
        path='categories/history-cities/역사와-제도/index.html'
        for sid in legacy[path]['ids']:
            self.assertEqual('data-story-id="'+sid+'"' in site.files[path],sid in published)
        self.assertIn('noindex,follow',site.files[path])


if __name__=='__main__':unittest.main()
