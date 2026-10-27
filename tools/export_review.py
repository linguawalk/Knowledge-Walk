#!/usr/bin/env python3
"""Export the actual site manuscripts to readable GitHub review documents."""
import os
from pathlib import Path

from build_site import ROOT, read_json, validate, source_ok, review_notice


def main():
    categories = read_json(ROOT / "config/categories.json")
    stories = [read_json(p) for p in sorted((ROOT / "content/stories").glob("*.json"))]
    cmap = validate(categories, stories)
    positions = {category["id"]: i for i, category in enumerate(categories)}
    stories.sort(key=lambda s: (positions[s["category"]], s["id"]))
    destination = ROOT / "docs/review"
    destination.mkdir(parents=True, exist_ok=True)
    index = ["# KnowledgeWalk — 분야별 시범 이야기", "",
             "각 제목을 누르면 글과 삽화, 확인한 참고 자료를 함께 볼 수 있습니다. **모든 원고는 편집 검토용이며 공개 게시 승인은 받지 않았습니다.** 자료 대조 상태는 아래 표에서 구분합니다.", "",
             "| 분야 | 세부 분류 | 이야기 | 자료 대조 |", "|---|---|---|---|"]
    for story in stories:
        name = f"{story['id']}.md"
        image = os.path.relpath(ROOT / story["image"]["file"], destination).replace(os.sep, "/")
        draft = [f"# {story['title']}", "", f"*{story['subtitle']}*", "",
                 f"{cmap[story['category']]['title']} · {story['subcategory']}", "",
                 f"> {review_notice(story)}", "",
                 f"![{story['image']['alt']}]({image})", "", f"*{story['image']['credit']}*", ""]
        if story["image"]["type"] != "ai_illustration":
            draft += [f"[이미지 출처와 소장품 안내]({story['image']['source_url']}) · {story['image']['license']}", ""]
        for block in story["body"]:
            if block.get("heading"):
                draft += [f"## {block['heading']}", ""]
            for paragraph in block["paragraphs"]:
                draft += [paragraph, ""]
        checked = [s for s in story["sources"] if source_ok(s)]
        if checked:
            draft += ["## 이야기의 바탕이 된 자료", ""]
            for entry in checked:
                draft += [f"- [{entry['title']}]({entry['url']}) · 확인일 {entry['checked_at']}"]
                if entry.get("supports"):
                    draft += [f"  - 확인 내용: {' / '.join(entry['supports'])}"]
            draft += [""]
        if story["source_review"] != "verified":
            draft += ["아직 대조하지 못한 내용이 남아 있습니다. 위 자료가 모든 문장의 확인 완료를 뜻하지는 않습니다.", ""]
        draft += ["---", "", "[시범 이야기 목록으로](README.md)", ""]
        (destination / name).write_text("\n".join(draft), encoding="utf-8")
        state = "완료 · 게시 승인 대기" if story["source_review"] == "verified" else "확인 중"
        index.append(f"| {cmap[story['category']]['title']} | {story['subcategory']} | [{story['title']}]({name}) | {state} |")
    index += ["", "AI 설명용 삽화와 출처·이용 조건을 확인한 소장품 이미지를 사용합니다. 각 글에서 종류와 출처를 구분합니다. AI 삽화는 실제 유물·제품·장소를 정확하게 재현한 자료가 아닙니다.", "",
              "제작·게시 주기는 미정이며, 운영 사이트와 도메인은 변경하지 않았습니다.", ""]
    (destination / "README.md").write_text("\n".join(index), encoding="utf-8")
    # Keep each delivery's reading list reproducible from its story IDs.
    by_id = {story["id"]: story for story in stories}
    for path in sorted((ROOT / "content/batches").glob("*.json")):
        batch = read_json(path)
        ids = batch["story_ids"]
        if len(ids) != len(set(ids)) or any(sid not in by_id for sid in ids):
            raise ValueError(f"Invalid story IDs in {path.name}")
        lines = [f"# {batch['title']}", "",
                 "제목을 누르면 **이미지·본문·확인한 근거자료**를 함께 볼 수 있습니다. 편집 검토용 원고이며 운영 사이트에는 아직 게시하지 않았습니다.", "",
                 "| 분야 · 세부 분류 | 이야기 | 이미지 |", "|---|---|---|"]
        for sid in ids:
            story = by_id[sid]
            kind = "AI 설명용 삽화" if story["image"]["type"] == "ai_illustration" else "박물관 제공 소장품 사진"
            lines.append(f"| {cmap[story['category']]['title']} · {story['subcategory']} | [{story['title']}]({sid}.md) | {kind} |")
        lines += ["", "실제 사진과 AI 삽화는 각 글에서 구분합니다. 박물관 사진은 공개된 크기로 제공하며, 일부 사진은 작습니다. AI 삽화는 정확한 역사 재현 자료가 아닙니다.", "",
                  "[전체 이야기 목록](README.md) · [43개 세부 주제 현황](../topic-coverage.md)", ""]
        (destination / f"batch-{path.stem}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Exported {len(stories)} review manuscripts with relative image links.")


if __name__ == "__main__":
    main()
