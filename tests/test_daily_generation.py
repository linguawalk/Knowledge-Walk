"""Offline checks for review isolation, source provenance, cost caps and restarts.

All generated text/URLs here are synthetic fixtures in temporary directories.
No AI API request is performed by this test module.
"""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from tools import daily_generation as daily

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_URL = 'https://www.gogung.go.kr/test-fixture-not-a-real-source'


def draft_fixture():
    paragraph = '이 문단은 테스트 전용으로 만든 합성 원고다. 실제 역사나 유물에 관한 설명이 아니며, 임시 폴더의 게시 차단과 검토 상태를 확인하기 위한 문장으로만 사용한다. '
    return dict(title='동그란 우편함의 푸른 손잡이', subtitle='실제 콘텐츠가 아닌 시험용 부제', summary='합성 시험 원고',
                image_prompt='Synthetic test image, no real image API call',
                body=[dict(heading=None if i == 0 else f'시험 구간 {i}', paragraphs=[paragraph*2, paragraph*2]) for i in range(4)],
                sources=[dict(title='Test fixture only — not an actual source', url=FIXTURE_URL, claim='Synthetic fixture claim', excerpt='test fixture only')],
                status='approved', publication_ready=True, approved_by='malicious model field')


class FakeClient:
    calls = []
    fail_images = False

    def __init__(self, key, config, state, checkpoint):
        self.state, self.checkpoint = state, checkpoint

    def json(self, system, prompt, schema, search=False, **kwargs):
        self.calls.append('json')
        self.state['api_calls'] += 1; self.checkpoint()
        trace = dict(search_performed=search, source_urls=[daily.canonical(FIXTURE_URL)] if search else [])
        if 'topics' in schema['properties']:
            return dict(topics=[dict(id='blue-mailbox', title='동그란 우편함의 푸른 손잡이', question='합성 질문', category='history', subcategory='Korea')]), trace
        if 'decision' in schema['properties']:
            return dict(decision='ready_for_editor', notes=[]), trace
        return draft_fixture(), trace

    def image(self, prompt, target):
        self.calls.append('image')
        self.state['api_calls'] += 1; self.state['image_requests'] += 1; self.checkpoint()
        if self.fail_images:
            raise daily.GenerationError('Synthetic image failure')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/'content/images/horn-bow-missing-string.jpg', target)
        return dict(width=265, height=176)


class DailyGenerationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'config/prompts').mkdir(parents=True)
        shutil.copyfile(ROOT/'config/categories.json', self.root/'config/categories.json')
        (self.root/'config/prompts/daily-editor.md').write_text('Synthetic test prompt')
        self.config = daily.read_json(ROOT/'config/daily-generation.json')
        self.config.update(enabled=True, daily_count=1, reserve_topics=0, max_consecutive_failures=1)
        FakeClient.calls = []; FakeClient.fail_images = False

    def run_fixture(self):
        return daily.run('2026-10-28', self.config, self.root, FakeClient)

    def test_model_cannot_approve_or_publish_its_own_draft(self):
        result = self.run_fixture()
        self.assertEqual(result['status'], 'complete')
        stories = daily.load_stories(self.root)
        self.assertEqual(len(stories), 1)
        story = stories[0]
        self.assertEqual(story['status'], 'draft')
        self.assertFalse(story['publication_ready'])
        self.assertEqual(story['source_review'], 'pending')
        self.assertIsNone(story['approved_by'])
        self.assertTrue(all(s['verified'] is False for s in story['sources']))
        from tools.build_site import Site
        categories = daily.read_json(self.root/'config/categories.json')
        self.assertEqual(json.loads(Site(categories, stories).render()['search-index.json']), [])

    def test_rerun_complete_batch_does_not_make_more_paid_calls(self):
        self.run_fixture(); before = list(FakeClient.calls)
        result = self.run_fixture()
        self.assertEqual(result['status'], 'already_complete')
        self.assertEqual(FakeClient.calls, before)
        self.assertEqual(len(daily.load_stories(self.root)), 1)

    def test_image_failure_is_partial_and_retry_reuses_researched_text(self):
        FakeClient.fail_images = True
        result = self.run_fixture()
        self.assertEqual(result['complete'], 0)
        self.assertEqual(result['status'], 'partial')
        self.assertFalse(list((self.root/'content/stories').rglob('*.json')))
        calls = list(FakeClient.calls)
        FakeClient.fail_images = False
        result = self.run_fixture()
        self.assertEqual(result['complete'], 1)
        self.assertEqual(FakeClient.calls[len(calls):], ['image'])

    def test_crash_after_file_writes_recovers_without_regeneration(self):
        self.run_fixture()
        state_path = self.root/'content/generation_runs/2026-10-28.json'
        state = daily.read_json(state_path)
        sid = state['completed'].pop()
        state['pending'][sid] = dict(draft=draft_fixture())
        daily.save(state_path, state)
        before = list(FakeClient.calls)
        result = self.run_fixture()
        self.assertEqual(result['status'], 'already_complete')
        self.assertEqual(FakeClient.calls, before)

    def test_untrusted_and_untraced_sources_are_rejected(self):
        for url in ['http://www.gogung.go.kr/a', 'https://localhost/a', 'https://github.com/impostor/repo',
                    'https://www.gogung.go.kr/another-unseen-page']:
            with self.subTest(url=url):
                draft = draft_fixture(); draft['sources'][0]['url'] = url
                with self.assertRaises(daily.GenerationError):
                    daily.validate_draft(draft, dict(search_performed=True, source_urls=[daily.canonical(FIXTURE_URL)]), self.config)

    def test_no_search_trace_is_not_source_verification(self):
        response = dict(status='completed', output=[dict(type='message', content=[dict(type='output_text', text='{}')])])
        with self.assertRaises(daily.GenerationError):
            daily.response_content(response, require_search=True)
        with self.assertRaises(daily.GenerationError):
            daily.response_content(dict(status='incomplete', output=[]))

    def test_request_limit_is_checked_before_network_and_key_is_not_logged(self):
        state = dict(api_calls=128, image_requests=0)
        client = daily.OpenAIClient('TEST-SECRET-DO-NOT-LOG', self.config, state, lambda: None)
        with patch.object(daily, 'urlopen') as network:
            with self.assertRaises(daily.GenerationError): client.post('responses', {})
            network.assert_not_called()
        state['api_calls'] = 0
        with patch.object(daily, 'urlopen', side_effect=HTTPError('https://api.openai.com/v1/responses',403,'Denied',{},None)):
            with self.assertRaises(daily.GenerationError) as error:client.post('responses', {})
            self.assertNotIn('TEST-SECRET', str(error.exception))
            self.assertEqual(state['api_calls'], 1)

    def test_duplicate_and_unsafe_topics_are_rejected(self):
        categories = daily.read_json(self.root/'config/categories.json')
        topic = dict(id='topic', title='어떤 물건의 작은 손잡이', question='질문', category='history', subcategory='Korea')
        with self.assertRaises(daily.GenerationError):daily.validate_topic(topic, categories, [topic['title']], set())
        topic['id'] = '../../escape'
        with self.assertRaises(daily.GenerationError):daily.validate_topic(topic, categories, [], set())

    def test_missing_key_never_sends_a_request(self):
        with patch.object(daily, 'urlopen') as network:
            with self.assertRaises(daily.GenerationError):daily.OpenAIClient(None, self.config, {}, lambda: None)
            network.assert_not_called()

    def test_remote_checkpoint_failure_keeps_work_and_stops_requests(self):
        def failed_checkpoint():
            raise OSError('Synthetic remote checkpoint failure')
        with self.assertRaises(OSError):
            daily.run('2026-10-28', self.config, self.root, FakeClient, on_checkpoint=failed_checkpoint)
        state = daily.read_json(self.root/'content/generation_runs/2026-10-28.json')
        self.assertEqual(len(state['completed']), 1)
        calls = list(FakeClient.calls)
        self.assertEqual(self.run_fixture()['status'], 'already_complete')
        self.assertEqual(FakeClient.calls, calls)

    def test_remote_checkpoint_cannot_write_main(self):
        with patch.object(daily.subprocess, 'check_output', side_effect=['main\n', 'https://github.com/linguawalk/Knowledge-Walk.git\n']):
            with patch.object(daily.subprocess, 'run') as command:
                with self.assertRaises(OSError):daily.persist_review_checkpoint()
                command.assert_not_called()

    def test_failed_search_call_cannot_be_used_as_provenance(self):
        response = dict(status='completed', output=[dict(type='web_search_call', status='failed', action={'sources':[{'url':FIXTURE_URL}]}),
                         dict(type='message', content=[dict(type='output_text',text='{}',annotations=[{'type':'url_citation','url':FIXTURE_URL}])])])
        with self.assertRaises(daily.GenerationError):daily.response_content(response, require_search=True)

    def test_disabled_generation_cannot_call_the_client(self):
        config = {**self.config, 'enabled': False}
        with patch.object(daily, 'OpenAIClient') as client:
            with self.assertRaises(daily.GenerationError):
                daily.run('2026-10-28', config, self.root, client)
            client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
