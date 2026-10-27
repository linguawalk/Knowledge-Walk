#!/usr/bin/env python3
"""Export manuscripts to a category/subcategory GitHub reading library."""
import os
from pathlib import Path

from build_site import ROOT, read_json, validate, source_ok, review_notice, load_stories, slug, publishable


def review_path(story):
    return Path(story['category']) / slug(story['subcategory']) / f"{story['id']}.md"


def state(story):
    if publishable(story):
        return "자료 대조·공개 게시 승인 완료"
    return "자료 대조 완료 · 게시 승인 대기" if story['source_review'] == 'verified' else "출처 추가 확인 중"


def main():
    categories = read_json(ROOT / 'config/categories.json')
    stories = load_stories()
    cmap = validate(categories, stories)
    positions = {category['id']: i for i, category in enumerate(categories)}
    stories.sort(key=lambda s: (positions[s['category']], s['id']))
    destination = ROOT / 'docs/review'
    destination.mkdir(parents=True, exist_ok=True)
    index = ['# KnowledgeWalk — 이야기 서가', '',
             '분야를 고른 다음 소주제로 들어가면 글과 이미지를 함께 읽을 수 있습니다. 기존 21편을 분야별 폴더로 옮겼으며 원고 내용은 유지했습니다.', '',
             f'**{sum(publishable(s) for s in stories)}편은 자료 대조와 공개 게시 승인을 마쳤으며, {sum(not publishable(s) for s in stories)}편은 추가 확인 중입니다. 실제 웹 게시는 별도의 배포 상태를 따릅니다.**', '',
             '[홈페이지 확인 안내](../homepage-review.md) · [최근 추가한 12편](batch-20261027-more.md)', '',
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
            draft += [f"[이미지 출처와 소장품 안내]({story['image']['source_url']}) · {story['image']['license']}", '']
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
        draft += ['---', '', '[같은 소주제의 이야기](README.md) · [전체 서가](../../README.md)', '']
        target.write_text('\n'.join(draft), encoding='utf-8')
    by_id = {story['id']: story for story in stories}
    for path in sorted((ROOT / 'content/batches').glob('*.json')):
        batch = read_json(path)
        ids = batch['story_ids']
        if len(ids) != len(set(ids)) or any(sid not in by_id for sid in ids):
            raise ValueError(f'Invalid story IDs in {path.name}')
        lines = [f"# {batch['title']}", '',
                 '제목을 누르면 **이미지·본문·확인한 근거자료**를 함께 볼 수 있습니다. 편집 검토용 원고입니다.', '',
                 '| 분야 · 세부 분류 | 이야기 | 이미지 |', '|---|---|---|']
        for sid in ids:
            story = by_id[sid]
            kind = 'AI 설명용 삽화' if story['image']['type'] == 'ai_illustration' else '박물관 제공 소장품 사진'
            lines.append(f"| {cmap[story['category']]['title']} · {story['subcategory']} | [{story['title']}]({review_path(story).as_posix()}) | {kind} |")
        lines += ['', '[분야별 이야기 서가](README.md) · [43개 소주제 현황](../topic-coverage.md)', '']
        (destination / f'batch-{path.stem}.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Exported {len(stories)} manuscripts into 8 categories / 43 topic folders.')


if __name__ == '__main__':
    main()
