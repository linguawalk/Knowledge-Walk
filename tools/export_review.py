#!/usr/bin/env python3
"""Export manuscripts to a category/subcategory GitHub reading library."""
import os
from pathlib import Path
from urllib.parse import quote, urlsplit

from build_site import ROOT, read_json, validate, source_ok, review_notice, load_stories, slug, publishable


def review_path(story):
    return Path(story['category']) / slug(story['subcategory']) / f"{story['id']}.md"


def state(story):
    if publishable(story):
        return "자료 대조·공개 게시 승인 완료"
    return "자료 대조 완료 · 게시 승인 대기" if story['source_review'] == 'verified' else "출처 추가 확인 중"


def export_daily_queue(destination):
    runs = [read_json(p) for p in sorted((ROOT / 'content/generation_runs').glob('*.json'), reverse=True)]
    lines = ['# KnowledgeWalk — 아침 검토함', '',
             '자동 제작 계획은 2026-10-28 사용자 요청으로 철회되었습니다. 앞으로는 요청 시 제작하며, 확인 전 홈페이지에 게시하지 않습니다.', '',
             '이 검토함은 GitHub 저장소 안의 자료이며, 비공개 보관함을 뜻하지는 않습니다.', '']
    if not runs:
        lines += ['자동 생성 결과가 없습니다. 예약 실행은 제거되어 있습니다.', '']
    else:
        lines += ['| 제작일 | 완료 / 목표 | 상태 | 읽기 |', '|---|---:|---|---|']
        for run in runs:
            day, count = run['date'], len(run['completed'])
            label = '목표 수량 완료' if count == run['target'] else '일부 완료 · 점검 필요'
            link = f'[글과 이미지 보기](batch-daily-{day}.md)' if count else '완료된 원고 없음'
            lines.append(f"| {day} | {count} / {run['target']} | {label} | {link} |")
    lines += ['', '출처 후보와 AI 감수 기록은 편집 보조 자료입니다. 원문 대조와 사용자 공개 승인은 별도이며, AI가 승인 표시를 채우지 않습니다.', '',
              '[전체 분야별 서가](README.md) · [자동 제작 방식과 연결 안내](../daily-generation.md)', '']
    (destination / 'daily-queue.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    categories = read_json(ROOT / 'config/categories.json')
    stories = load_stories()
    cmap = validate(categories, stories)
    positions = {category['id']: i for i, category in enumerate(categories)}
    stories.sort(key=lambda s: (positions[s['category']], s['id']))
    destination = ROOT / 'docs/review'
    destination.mkdir(parents=True, exist_ok=True)
    index = ['# KnowledgeWalk — 이야기 서가', '',
             f'분야를 고른 다음 소주제로 들어가면 전체 {len(stories)}편의 글과 이미지를 함께 읽을 수 있습니다.', '',
             f'**공개 승인 {sum(publishable(s) for s in stories)}편 / 자료 대조 완료·편집 검토 {sum(s["source_review"] == "verified" and not publishable(s) for s in stories)}편 / 출처 추가 확인 {sum(s["source_review"] != "verified" for s in stories)}편.** 실제 웹 게시는 별도의 배포 상태를 따릅니다.', '',
             '[아침 검토함](daily-queue.md) · [홈페이지 확인 안내](../homepage-review.md) · [새 이야기 10편](batch-20261031-ten-folklore-myths-and-marvels.md)', '',
             '| 분야 | 이야기 | 소주제 수 |', '|---|---:|---:|']
    for category in categories:
        cid = category['id']
        subset = [s for s in stories if s['category'] == cid]
        index.append(f"| [{category['title']} · {category['label']}]({cid}/README.md) | {len(subset)}편 | {len(category['children'])}개 |")
        category_index = [f"# {category['title']} · {category['label']}", '', category['intro'], '',
                          '[전체 서가로](../README.md)', '', '| 소주제 | 이야기 |', '|---|---:|']
        for child in category['children']:
            child_slug = slug(child)
            folder = destination / cid / child_slug
            folder.mkdir(parents=True, exist_ok=True)
            members = [s for s in subset if s['subcategory'] == child]
            category_index.append(f'| [{child}]({child_slug}/README.md) | {len(members)}편 |')
            child_index = [f"# {category['title']} → {child}", '',
                           '[분야 목록](../README.md) · [전체 서가](../../README.md)', '']
            if members:
                child_index += ['| 이야기 | 확인 상태 |', '|---|---|']
                child_index += [f"| [{s['title']}]({s['id']}.md) | {state(s)} |" for s in members]
            else:
                child_index += ['이 소주제의 이야기는 아직 준비 중입니다.']
            (folder / 'README.md').write_text('\n'.join(child_index) + '\n', encoding='utf-8')
        (destination / cid / 'README.md').write_text('\n'.join(category_index) + '\n', encoding='utf-8')
    index += ['', '홈페이지에서는 ‘읽음으로 표시’와 ‘내 읽기 목록’을 사용할 수 있습니다. GitHub 폴더의 확인 상태는 출처·편집 상태이며 개인의 읽기 기록을 뜻하지 않습니다.', '',
              '[43개 소주제 제작 현황](../topic-coverage.md)', '']
    (destination / 'README.md').write_text('\n'.join(index), encoding='utf-8')
    for story in stories:
        target = destination / review_path(story)
        image = os.path.relpath(ROOT / story['image']['file'], target.parent).replace(os.sep, '/')
        draft = [f"# {story['title']}", '', f"*{story['subtitle']}*", '',
                 f"{cmap[story['category']]['title']} · {story['subcategory']}", '',
                 f"> {review_notice(story)}", '',
                 f"![{story['image']['alt']}]({image})", '', f"*{story['image']['credit']}*", '']
        if story['image']['type'] != 'ai_illustration':
            draft += [f"[이미지 출처·제작 근거]({story['image']['source_url']}) · {story['image']['license']}", '']
        for block in story['body']:
            if block.get('heading'):
                draft += [f"## {block['heading']}", '']
            for paragraph in block['paragraphs']:
                draft += [paragraph, '']
        checked = [s for s in story['sources'] if source_ok(s)]
        if checked:
            draft += ['## 이야기의 바탕이 된 자료', '']
            for entry in checked:
                draft += [f"- [{entry['title']}]({entry['url']}) · 확인일 {entry['checked_at']}"]
                if entry.get('supports'):
                    draft += [f"  - 확인 내용: {' / '.join(entry['supports'])}"]
            draft += ['']
        if story['source_review'] != 'verified':
            draft += ['아직 대조하지 못한 내용이 남아 있습니다. 위 자료가 모든 문장의 확인 완료를 뜻하지는 않습니다.', '']
            candidates = [s for s in story['sources'] if not source_ok(s) and urlsplit(str(s.get('url', ''))).scheme == 'https']
            if candidates:
                draft += ['## 검토할 참고 자료 후보', '', '아래는 원문 대조 전 후보입니다. 사실 확인 완료를 뜻하지 않습니다.', '']
                for entry in candidates:
                    title = str(entry.get('title', '참고 자료')).replace('[', '\\[').replace(']', '\\]').replace('<', '&lt;').replace('>', '&gt;').replace('\n', ' ')
                    url = quote(entry['url'], safe=':/?&=%#@,+;-_~.!$*')
                    draft += [f'- [{title}]({url})']
                draft += ['']
        draft += ['---', '', '[같은 소주제의 이야기](README.md) · [전체 서가](../../README.md)', '']
        target.write_text('\n'.join(draft), encoding='utf-8')
    by_id = {story['id']: story for story in stories}
    for path in sorted((ROOT / 'content/batches').glob('*.json')):
        batch = read_json(path)
        ids = batch['story_ids']
        if len(ids) != len(set(ids)) or any(sid not in by_id for sid in ids):
            raise ValueError(f'Invalid story IDs in {path.name}')
        lines = [f"# {batch['title']}", '',
                 '제목을 누르면 **이미지·본문·근거자료 및 확인 상태**를 함께 볼 수 있습니다. 실제 웹 게시 여부는 각 원고의 승인·배포 상태를 따릅니다.', '',
                 '| 분야 · 세부 분류 | 이야기 | 이미지 |', '|---|---|---|']
        for sid in ids:
            story = by_id[sid]
            kind = story['image'].get('label') or ('AI 설명용 삽화' if story['image']['type'] == 'ai_illustration' else '박물관 제공 소장품 사진')
            lines.append(f"| {cmap[story['category']]['title']} · {story['subcategory']} | [{story['title']}]({review_path(story).as_posix()}) | {kind} |")
        lines += ['', '[분야별 이야기 서가](README.md) · [43개 소주제 현황](../topic-coverage.md)', '']
        (destination / f'batch-{path.stem}.md').write_text('\n'.join(lines), encoding='utf-8')
    export_daily_queue(destination)
    print(f'Exported {len(stories)} manuscripts into 8 categories / 43 topic folders.')


if __name__ == '__main__':
    main()
