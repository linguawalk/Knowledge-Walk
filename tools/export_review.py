#!/usr/bin/env python3
"""Export the actual site manuscripts to readable GitHub review documents."""
import os
from pathlib import Path

from build_site import ROOT, read_json, validate


def main():
    categories = read_json(ROOT / "config/categories.json")
    stories = [read_json(p) for p in sorted((ROOT / "content/stories").glob("*.json"))]
    cmap = validate(categories, stories)
    positions = {category["id"]: i for i, category in enumerate(categories)}
    stories.sort(key=lambda s: (positions[s["category"]], s["id"]))
    destination = ROOT / "docs/review"
    destination.mkdir(parents=True, exist_ok=True)
    index = ["# KnowledgeWalk — 분야별 시범 이야기", "",
             "각 제목을 누르면 글과 삽화를 함께 볼 수 있습니다. 모든 원고는 출처 원문 대조가 끝나지 않은 **검토용 초안**입니다. 사이트 게시 승인을 받은 원고가 아닙니다.", "",
             "| 분야 | 세부 분류 | 이야기 |", "|---|---|---|"]
    for story in stories:
        name = f"{story['id']}.md"
        image = os.path.relpath(ROOT / story["image"]["file"], destination).replace(os.sep, "/")
        draft = [f"# {story['title']}", "", f"*{story['subtitle']}*", "",
                 f"{cmap[story['category']]['title']} · {story['subcategory']}", "",
                 "> 편집 검토용 초안 · 출처 원문 대조 미완료 · 미게시", "",
                 f"![{story['image']['alt']}]({image})", "", f"*{story['image']['credit']}*", ""]
        for block in story["body"]:
            if block.get("heading"):
                draft += [f"## {block['heading']}", ""]
            for paragraph in block["paragraphs"]:
                draft += [paragraph, ""]
        draft += ["---", "", "[시범 이야기 목록으로](README.md)", ""]
        (destination / name).write_text("\n".join(draft), encoding="utf-8")
        index.append(f"| {cmap[story['category']]['title']} | {story['subcategory']} | [{story['title']}]({name}) |")
    index += ["", "새로운 사진 대신 AI 설명용 삽화를 사용했습니다. 삽화는 실제 유물·제품·장소를 정확하게 재현한 자료가 아닙니다.", "",
              "제작·게시 주기는 미정이며, 운영 사이트와 도메인은 변경하지 않았습니다.", ""]
    (destination / "README.md").write_text("\n".join(index), encoding="utf-8")
    print(f"Exported {len(stories)} review manuscripts with relative image links.")


if __name__ == "__main__":
    main()
