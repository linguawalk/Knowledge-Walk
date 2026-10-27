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
    index += ["", "새로운 사진 대신 AI 설명용 삽화를 사용했습니다. 삽화는 실제 유물·제품·장소를 정확하게 재현한 자료가 아닙니다.", "",
              "제작·게시 주기는 미정이며, 운영 사이트와 도메인은 변경하지 않았습니다.", ""]
    (destination / "README.md").write_text("\n".join(index), encoding="utf-8")
    print(f"Exported {len(stories)} review manuscripts with relative image links.")


if __name__ == "__main__":
    main()
