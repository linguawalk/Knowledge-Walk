#!/usr/bin/env python3
"""Report drafted topics and suggest underrepresented areas; never generates or publishes."""
try:
    from .build_site import ROOT, read_json, validate, publishable, load_stories
except ImportError:
    from build_site import ROOT, read_json, validate, publishable, load_stories


def coverage(categories, stories):
    rows = []
    active = [s for s in stories if s["status"] != "rejected"]
    for category in categories:
        for child in category["children"]:
            subset = [s for s in active if s["category"] == category["id"] and s["subcategory"] == child]
            rows.append({"category": category["id"], "title": category["title"], "subcategory": child,
                         "count": len(subset), "source_checked": sum(s["source_review"] == "verified" for s in subset),
                         "approved": sum(publishable(s) for s in subset)})
    return rows


def main():
    categories = read_json(ROOT / "config/categories.json")
    stories = load_stories()
    validate(categories, stories)
    rows = coverage(categories, stories)
    occupied = sum(row["count"] > 0 for row in rows)
    category_totals = {c["id"]: sum(r["count"] for r in rows if r["category"] == c["id"]) for c in categories}
    # Stable order is an inspection queue, not a requirement to write these first.
    candidates = sorted([row for row in rows if row["count"] == 0], key=lambda row: category_totals[row["category"]])
    lines = ["# 세부 주제 제작 현황", "", f"전체 {len(rows)}개 세부 주제 중 원고가 있는 곳은 {occupied}개입니다. 원고 수는 미게시 초안과 검토 중 원고를 포함하며, 실제 공개된 글 수를 뜻하지 않습니다.", "",
             "| 분야 | 세부 주제 | 원고 | 자료 대조 완료 | 공개 승인 |", "|---|---|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['title']} | {row['subcategory']} | {row['count']} | {row['source_checked']} | {row['approved']} |")
    lines += ["", "## 먼저 살펴볼 빈 주제", "", "아래는 원고가 적은 분야의 빈 주제를 먼저 보여주는 조사 대기 목록입니다. 자료의 신뢰성과 이야기의 재미를 확인한 뒤 실제 소재를 정하며, 이 순서대로 무조건 집필하지 않습니다.", ""]
    lines += [f"- {row['title']} → {row['subcategory']}" for row in candidates[:8]]
    lines += ["", "분류 수를 채우려고 같은 소재를 여러 분야에 반복 사용하지 않습니다. 소재·중심 질문의 중복 여부는 편집 단계에서 별도 확인합니다. 제작 주기와 공개 일정은 아직 정하지 않았습니다.", ""]
    (ROOT / "docs/topic-coverage.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Coverage: {occupied}/{len(rows)} subcategories, {sum(row['count'] for row in rows)} manuscripts; no jobs scheduled.")


if __name__ == "__main__":
    main()
