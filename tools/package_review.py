#!/usr/bin/env python3
"""Bundle a locally readable review website. Does not upload or deploy."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from build_site import ROOT, build


def main():
    build(preview=True)
    folder = ROOT / 'downloads'
    folder.mkdir(exist_ok=True)
    target = folder / 'knowledgewalk-homepage-review.zip'
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / '_preview').rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT / '_preview'))
        archive.writestr('사용안내.txt', '''KnowledgeWalk 홈페이지 검토본

1. 압축파일을 폴더에 모두 풀어 주세요.
2. index.html을 더블클릭해 브라우저로 열어 주세요.
3. 첫 화면의 ‘소주제별 전체 서가’에서 분야 → 소주제 → 글을 선택합니다.
4. 다 읽은 글에서는 ‘읽음으로 표시’를 누르고 ‘내 읽기 목록’에서 모아 봅니다.

이미지와 검색 자료가 함께 들어 있어 인터넷 없이도 읽을 수 있습니다.
읽기 기록은 같은 브라우저의 로컬 저장소에만 남습니다.
파일로 직접 여는 경우 브라우저 설정에 따라 기록이 유지되지 않거나 파일별로 나뉠 수 있습니다.
실제 웹주소에서의 읽기 기록도 다른 기기나 브라우저와 공유되지 않습니다.
저장이 불가능한 경우 안내를 표시하고 글 읽기는 계속 지원합니다.
읽음 표시는 공개 게시 승인과 별도입니다.

이것은 미게시 원고 21편을 담은 검토용 사본입니다.
출처 추가 확인 중인 3편은 해당 글에 상태를 표시했습니다.
운영 사이트 knowledgewalk.net은 이 작업으로 변경되지 않았습니다.
''')
    print(f'Created {target.relative_to(ROOT)} ({target.stat().st_size:,} bytes). No deployment.')


if __name__ == '__main__':
    main()
