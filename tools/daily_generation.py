#!/usr/bin/env python3
"""Prepare researched, illustrated drafts. Never approves, merges or publishes."""
import argparse
import base64
from datetime import date, datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

try:
    from .build_site import ROOT, ID, load_stories, read_json, slug, validate
except ImportError:
    from build_site import ROOT, ID, load_stories, read_json, slug, validate


class GenerationError(RuntimeError):
    pass


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def obj(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


def array(item, minimum=1, maximum=8):
    return dict(type='array', items=item, minItems=minimum, maxItems=maximum)


STRING = {'type': 'string'}
TOPIC = obj(dict(id=STRING, category=STRING, subcategory=STRING, title=STRING, question=STRING))
SOURCE = obj(dict(title=STRING, url=STRING, claim=STRING, excerpt=STRING))
DRAFT = obj(dict(title=STRING, subtitle=STRING, summary=STRING,
                 body=array(obj(dict(heading={'type': ['string', 'null']}, paragraphs=array(STRING, 2, 5))), 4, 4),
                 sources=array(SOURCE, 1, 4), image_prompt=STRING))
AUDIT = obj(dict(decision={'type': 'string', 'enum': ['ready_for_editor', 'revise', 'reject']},
                 notes=array(STRING, 0, 8)))


def trusted_url(url, config):
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or '').lower()
        if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port not in (None, 443):
            return False
        if not any(host == domain or host.endswith('.' + domain) for domain in config['trusted_domains']):
            return False
        if host in ('github.com', 'raw.githubusercontent.com'):
            if parsed.path.strip('/').split('/')[0] not in config['trusted_github_owners']:
                return False
        return True
    except (ValueError, TypeError):
        return False


def canonical(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip('/'), parts.query, ''))


def grams(text):
    text = re.sub(r'[^0-9a-z가-힣]', '', text.lower())
    return {text[i:i+3] for i in range(max(0, len(text)-2))}


def duplicate(title, existing):
    left = grams(title)
    return any(left and right and len(left & right) / len(left | right) >= .62
               for right in (grams(t) for t in existing))


def response_content(response, require_search=False):
    if response.get('status') != 'completed':
        raise GenerationError('AI response was incomplete; not saved as a complete story')
    texts, urls, searched = [], set(), False
    for item in response.get('output', []):
        if item.get('type') == 'web_search_call' and item.get('status') == 'completed':
            searched = True
            for source in item.get('action', {}).get('sources', []):
                if source.get('url'):
                    urls.add(canonical(source['url']))
        for block in item.get('content', []):
            if block.get('type') == 'output_text':
                texts.append(block['text'])
            for annotation in block.get('annotations', []):
                if annotation.get('type') == 'url_citation' and annotation.get('url'):
                    urls.add(canonical(annotation['url']))
    if require_search and (not searched or not urls):
        raise GenerationError('No actual web-search source trace; citations cannot be accepted')
    try:
        payload = json.loads(''.join(texts))
    except (ValueError, TypeError):
        raise GenerationError('Invalid structured AI response') from None
    return payload, dict(response_id=response.get('id'), model=response.get('model'),
                         usage=response.get('usage'), search_performed=searched, source_urls=sorted(urls))


class OpenAIClient:
    def __init__(self, key, config, state, checkpoint):
        if not key:
            raise GenerationError('OPENAI_API_KEY is not configured; no paid request was sent')
        self.key, self.config, self.state, self.checkpoint = key, config, state, checkpoint

    def post(self, endpoint, payload):
        for attempt in range(3):
            if self.state['api_calls'] >= self.config['max_api_calls_per_day']:
                raise GenerationError('Daily request limit reached')
            if endpoint == 'images/generations':
                if self.state['image_requests'] >= self.config['max_image_requests_per_day']:
                    raise GenerationError('Daily image-request limit reached')
                self.state['image_requests'] += 1
            self.state['api_calls'] += 1
            self.checkpoint()
            request = Request('https://api.openai.com/v1/' + endpoint,
                              data=json.dumps(payload).encode(),
                              headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
            try:
                with urlopen(request, timeout=180) as response:
                    return json.load(response)
            except HTTPError as error:
                if error.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise GenerationError(f'AI service HTTP {error.code}; credentials and response body omitted') from None
            except (URLError, TimeoutError, ValueError):
                raise GenerationError('AI service network/response error; no credential details logged') from None
        raise GenerationError('Request could not complete')

    def json(self, system, prompt, schema, search=False, max_tokens=None):
        payload = dict(model=self.config['text_model'],
                       input=[dict(role='system', content=system), dict(role='user', content=prompt)],
                       max_output_tokens=max_tokens or self.config['max_output_tokens'],
                       text={'format': {'type': 'json_schema', 'name': 'knowledgewalk', 'strict': True, 'schema': schema}},
                       store=False)
        if search:
            payload.update(tools=[{'type': 'web_search', 'filters': {'allowed_domains': self.config['trusted_domains']}}],
                           max_tool_calls=self.config['max_web_calls_per_response'],
                           include=['web_search_call.action.sources'])
        return response_content(self.post('responses', payload), require_search=search)

    def image(self, prompt, target):
        from PIL import Image
        data = self.post('images/generations', dict(model=self.config['image_model'], prompt=prompt,
                         size=self.config['image_size'], quality=self.config['image_quality'], n=1,
                         output_format='jpeg', output_compression=85))
        try:
            raw = base64.b64decode(data['data'][0]['b64_json'], validate=True)
            if len(raw) > 25_000_000:
                raise ValueError('Image too large')
            image = Image.open(io.BytesIO(raw))
            if image.width * image.height > 16_000_000:
                raise ValueError('Image dimensions too large')
            image.load()
            image = image.convert('RGB')
            image.thumbnail((1280, 1280))
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=82, optimize=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix('.tmp')
            temporary.write_bytes(buffer.getvalue())
            temporary.replace(target)
            return dict(width=image.width, height=image.height)
        except (KeyError, IndexError, ValueError, OSError):
            raise GenerationError('Image missing or invalid; draft not counted as complete') from None


def validate_topic(topic, categories, known_titles, known_ids):
    if not isinstance(topic, dict) or not ID.fullmatch(str(topic.get('id', ''))):
        raise GenerationError('Invalid topic ID')
    category = next((c for c in categories if c['id'] == topic.get('category')), None)
    if not category or topic.get('subcategory') not in category['children']:
        raise GenerationError('Topic is outside the 43 approved subcategories')
    if not all(isinstance(topic.get(k), str) and topic[k].strip() for k in ('title', 'question')):
        raise GenerationError('Empty topic title/question')
    if topic['id'] in known_ids or duplicate(topic['title'], known_titles):
        raise GenerationError('Duplicate topic')


def validate_draft(draft, trace, config):
    if not isinstance(draft, dict):
        raise GenerationError('Draft is not an object')
    for name in ('title', 'subtitle', 'summary', 'image_prompt'):
        if not isinstance(draft.get(name), str) or not draft[name].strip() or len(draft[name]) > 2500:
            raise GenerationError('Invalid draft text')
        if name != 'image_prompt' and any(token in draft[name] for token in ('<', '>', '![', '](')):
            raise GenerationError('Draft title/summary must be plain text')
    body = draft.get('body', [])
    if not isinstance(body, list) or len(body) != 4:
        raise GenerationError('Draft requires introduction and three sections')
    paragraphs = []
    for index, block in enumerate(body):
        if not isinstance(block, dict) or not isinstance(block.get('paragraphs'), list) or not 2 <= len(block['paragraphs']) <= 5:
            raise GenerationError('Invalid body paragraphs')
        if index and (not isinstance(block.get('heading'), str) or not block['heading'].strip()):
            raise GenerationError('Missing section heading')
        if not index and block.get('heading') is not None:
            raise GenerationError('Introduction must have no heading')
        for text in block['paragraphs']:
            if not isinstance(text, str) or not text.strip() or any(token in text for token in ('<', '>', '![', '](')):
                raise GenerationError('Body must be plain, nonempty paragraph text')
            paragraphs.append(text)
    if not 850 <= sum(len(p) for p in paragraphs) <= 1900:
        raise GenerationError('Draft length is outside editorial bounds')
    sources = draft.get('sources', [])
    traced = set(trace.get('source_urls', []))
    if not trace.get('search_performed') or not 1 <= len(sources) <= 4:
        raise GenerationError('Research sources are missing')
    for source in sources:
        if (not isinstance(source, dict) or not trusted_url(source.get('url'), config)
                or canonical(source['url']) not in traced):
            raise GenerationError('Reference is untrusted or not in actual search results')
        if not all(isinstance(source.get(k), str) and source[k].strip() for k in ('title', 'claim', 'excerpt')):
            raise GenerationError('Reference support is missing')
        if len(source['excerpt'].split()) > 25 or len(source['excerpt']) > 160:
            raise GenerationError('Source quotation exceeds editorial limit')


def run(day, config, root=ROOT, client_factory=OpenAIClient, on_checkpoint=None):
    if config.get('enabled') is not True:
        raise GenerationError('Automatic generation is disabled; no paid request was sent')
    if date.fromisoformat(day).isoformat() != day:
        raise GenerationError('Invalid batch date')
    target = config['daily_count']
    if type(target) is not int or not 1 <= target <= 30 or config['publication_policy'] != 'draft_only_human_approval_required':
        raise GenerationError('Unsafe generation/publication configuration')
    state_path = root / 'content/generation_runs' / (day + '.json')
    state = read_json(state_path) if state_path.exists() else dict(date=day, target=target, api_calls=0, image_requests=0, topics=[], completed=[], pending={}, errors=[])
    if state['target'] != target:
        raise GenerationError('Cannot change the size of an existing daily batch')
    if len(state['completed']) != len(set(state['completed'])) or len(state['completed']) > target:
        raise GenerationError('Invalid completed-story count; manual state recovery is required')
    checkpoint = lambda: save(state_path, state)
    categories = read_json(root / 'config/categories.json')
    existing = load_stories(root)
    validate(categories, existing, root)
    existing_by_id = {s['id']: s for s in existing}
    if any(sid not in existing_by_id for sid in state['completed']):
        raise GenerationError('Completed batch state has a missing manuscript; recovery is required')
    # Recover a completed story if the runner stopped after writing its files
    # but before checkpointing the batch list. Never regenerate/charge for it.
    for sid, work in list(state['pending'].items()):
        prior = existing_by_id.get(sid)
        evidence = root / 'docs/research/daily' / day / (sid + '.json')
        if (prior and evidence.exists() and prior['title'] == work['draft']['title']
                and prior['body'] == work['draft']['body'] and prior['status'] == 'draft'
                and not prior['publication_ready'] and not prior['approved_by']):
            state['completed'].append(sid)
            del state['pending'][sid]
            checkpoint()
    if state['completed']:
        save(root / 'content/batches' / f'daily-{day}.json', dict(id=f'daily-{day}', title=f'{day} 아침 이야기 · 검토용', story_ids=state['completed']))
    if len(state['completed']) >= target:
        state['status'] = 'complete'
        checkpoint()
        return dict(status='already_complete', complete=len(state['completed']), target=target, api_calls=state['api_calls'])
    existing.sort(key=lambda s: (s.get('generated_at', ''), s['id']))
    known_titles, known_ids = [s['title'] for s in existing], {s['id'] for s in existing}
    prompt = (root / 'config/prompts/daily-editor.md').read_text()
    client = client_factory(os.environ.get('OPENAI_API_KEY'), config, state, checkpoint)
    if not state['topics']:
        count = target + config['reserve_topics']
        plan, trace = client.json(prompt, json.dumps(dict(task='Plan distinct story topics, using underfilled fields first. Return JSON.',
                            categories=categories, count=count,
                            counts={c['id']: sum(s['category'] == c['id'] for s in existing) for c in categories},
                            recent_titles=known_titles[-300:]), ensure_ascii=False), obj({'topics': array(TOPIC, count, count)}),
                                  max_tokens=config['max_planning_output_tokens'])
        if not isinstance(plan.get('topics'), list) or len(plan['topics']) != count:
            raise GenerationError('Planner did not return the required topic count')
        state['topics'], state['planning_trace'] = plan['topics'], trace
        checkpoint()
    failures = 0
    for topic in state['topics']:
        if len(state['completed']) >= target:
            break
        short_id = topic.get('id', '') if isinstance(topic, dict) else ''
        sid = f'daily-{day}-{short_id}'
        if sid in state['completed']:
            continue
        try:
            validate_topic(topic, categories, known_titles, set())
            if sid in known_ids:
                raise GenerationError('Existing story ID conflicts with unfinished batch state')
            if sid in state['pending']:
                work = state['pending'][sid]
                draft, trace, audit = work['draft'], work['trace'], work['audit']
            else:
                draft, trace = client.json(prompt, json.dumps(dict(task='Research with web_search and write an original Korean story. Return JSON.',
                       topic=topic, body_characters='1000–1500', existing_titles=known_titles[-200:]), ensure_ascii=False), DRAFT, search=True)
                validate_draft(draft, trace, config)
                if duplicate(draft['title'], known_titles):
                    raise GenerationError('Draft repeats an existing title/question')
                audit, audit_trace = client.json(prompt + '\n독립 감수자 역할이다. 지어낸 원인, 연도, 과장, 근거와 다른 내용을 원문 검색으로 확인한다. 아직 최종 사실 검증이나 사용자 승인을 하지 않는다.',
                        json.dumps(dict(task='Independently research and audit this draft. Reject weak sources or unsupported core claims. Return JSON.',
                                       draft=draft, previous_titles=known_titles[-200:]), ensure_ascii=False), AUDIT, search=True)
                if audit.get('decision') != 'ready_for_editor':
                    raise GenerationError('Independent AI check requests revision; not counted as a finished draft')
                work = dict(draft=draft, trace=trace, audit=audit, audit_trace=audit_trace)
                state['pending'][sid] = work
                checkpoint()
            validate_draft(draft, trace, config)
            image_path = Path('content/illustrations') / (sid + '.jpg')
            dimensions = client.image('Landscape 3:2, warm ivory watercolor and colored pencil editorial illustration for adult readers. No text, logos or watermark. Conceptual illustration, not evidence or an exact reconstruction. ' + draft['image_prompt'], root / image_path)
            story = dict(id=sid, title=draft['title'], subtitle=draft['subtitle'], summary=draft['summary'],
                         category=topic['category'], subcategory=topic['subcategory'], status='draft',
                         publication_ready=False, source_review='pending', approved_by=None, approved_at=None,
                         sources=[dict(title=s['title'], url=s['url'], verified=False, supports=[s['claim']]) for s in draft['sources']],
                         image=dict(file=image_path.as_posix(), type='ai_illustration', alt=draft['summary'],
                                    credit='KnowledgeWalk 자동 제작 · AI 설명용 삽화. 실제 모습의 정확한 재현이나 사실 검증 자료가 아닙니다.', **dimensions),
                         body=draft['body'], generated_at=day)
            validate(categories, [story], root)
            save(root / 'content/stories' / story['category'] / slug(story['subcategory']) / (sid + '.json'), story)
            evidence = dict(id=sid, date=day, research=trace, automated_editorial_check=audit,
                            audit_trace=work['audit_trace'], source_candidates=draft['sources'],
                            source_review='pending', human_approval=False,
                            image_sha256=hashlib.sha256((root/image_path).read_bytes()).hexdigest())
            save(root / 'docs/research/daily' / day / (sid + '.json'), evidence)
            state['completed'].append(sid)
            del state['pending'][sid]
            known_titles.append(story['title']); known_ids.add(sid)
            failures = 0
            state['status'] = 'complete' if len(state['completed']) == target else 'partial'
            checkpoint()
            save(root / 'content/batches' / f'daily-{day}.json', dict(id=f'daily-{day}', title=f'{day} 아침 이야기 · 검토용', story_ids=state['completed']))
            if on_checkpoint:
                on_checkpoint()
        except (GenerationError, KeyError, ValueError, TypeError) as error:
            state['errors'].append(dict(topic_id=short_id, reason=str(error)[:220]))
            state['status'] = 'partial' if state['completed'] else 'failed'
            checkpoint()
            if on_checkpoint:
                on_checkpoint()
            failures += 1
            if failures >= config['max_consecutive_failures'] or state['api_calls'] >= config['max_api_calls_per_day']:
                break
    return dict(status='complete' if len(state['completed']) == target else 'partial', complete=len(state['completed']),
                target=target, api_calls=state['api_calls'], image_requests=state['image_requests'])


def persist_review_checkpoint():
    """Save each completed/failed item remotely before incurring more API cost."""
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, text=True).strip()
    if branch != 'drafts/review-queue' or remote.rstrip('/').removesuffix('.git') != 'https://github.com/linguawalk/Knowledge-Walk':
        raise OSError('Remote checkpoints are allowed only on the authorized review branch')
    commands = [[sys.executable, 'tools/export_review.py'],
                ['git', 'add', '--', 'content/stories', 'content/illustrations', 'content/batches',
                 'content/generation_runs', 'docs/review', 'docs/research']]
    try:
        for command in commands:
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
        changed = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode
        if changed == 1:
            subprocess.run(['git', 'commit', '-m', 'Checkpoint daily drafts for human review'], cwd=ROOT, check=True, capture_output=True)
        elif changed != 0:
            raise OSError('Cannot inspect the review checkpoint')
        subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/drafts/review-queue'], cwd=ROOT, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise OSError('Review checkpoint failed; stopped before further paid requests') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', type=lambda value: date.fromisoformat(value).isoformat(),
                        default=datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat())
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--checkpoint-git', action='store_true', help='Persist each item to the review branch only')
    parser.add_argument('--summary-file', type=Path)
    args = parser.parse_args()
    config = read_json(ROOT / 'config/daily-generation.json')
    summary = dict(date=args.date, timezone=config['timezone'], target=config['daily_count'], enabled=config['enabled'],
                   api_key_configured=bool(os.environ.get('OPENAI_API_KEY')), automatic_publication=False)
    code = 0
    if args.dry_run or not config['enabled']:
        summary.update(status='configuration_check_only', generated=0)
    else:
        try:
            summary.update(run(args.date, config, on_checkpoint=persist_review_checkpoint if args.checkpoint_git else None))
            code = 0 if summary['status'] in ('complete', 'already_complete') else 1
        except (GenerationError, ValueError, KeyError, OSError) as error:
            state_file = ROOT / 'content/generation_runs' / (args.date + '.json')
            completed = len(read_json(state_file).get('completed', [])) if state_file.exists() else 0
            summary.update(status='blocked', reason=str(error)[:220], complete=completed, generated=completed)
            code = 1
    if args.summary_file:
        save(args.summary_file, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
