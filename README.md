# KnowledgeWalk

익숙한 세상의 사물·장소·이름에 얽힌 작은 이야기를 읽는 사이트입니다. WordPress와 별도 데이터베이스 없이, 콘텐츠 파일에서 HTML을 생성합니다. 작업 범위는 `linguawalk/Knowledge-Walk` 한 저장소입니다.

현재 단계: **GitHub 홈페이지 게시·도메인 등록 완료 / Hostinger DNS 전환 대기**. 공개 대상 18편을 실제 게시하고 웹 응답을 확인했습니다. `knowledgewalk.net`은 GitHub에 등록했으나 DNS가 아직 Hostinger를 가리켜 도메인 연결 전환은 끝나지 않았습니다. [현재 상태와 남은 작업](docs/domain-migration.md)을 확인합니다. 정기 AI 생성과 예약 게시 주기는 설정하지 않았습니다.

## 준비된 화면

- `index.html`: 첫 화면. 8개 분야와 추천 이야기를 표시합니다.
- `categories/`: 8개 분야 및 43개 세부 분류의 자동 생성 목록.
- `stories/<고유 ID>/index.html`: 글 읽기 화면. 분류를 옮겨도 주소는 유지합니다.
- `search.html`: 제목·본문·분류를 대상으로 하는 한국어 부분 문자열 검색과 분야 필터.
- `404.html`: 없는 페이지 안내.

검토용 화면에는 총 21편이 있습니다. **18편은 기관 자료 대조를 마쳤고 3편은 추가 확인 중**입니다. 이번 도메인 전환 요청으로 자료 대조 완료 18편의 공개 승인을 기록했습니다. 공개용 빌드에는 이 18편만 포함하며, 추가 확인 중인 3편은 제외합니다. GitHub 게시는 완료됐고 Hostinger DNS 연결 변경은 남아 있습니다. 빈 세부 분류는 실제로 준비 중임을 표시하고 가짜 글이나 수치를 넣지 않습니다.

[글과 이미지를 함께 보는 검토 목록](docs/review/README.md)과 [출처 검토 상태](docs/pilot-source-review.md)를 확인할 수 있습니다. 기관 공식 자료와 공식 기술 문서의 실제 본문을 읽고 원고의 사실을 대조했습니다. 확인한 항목·최종 URL·응답 해시·짧은 근거는 [조사 기록](docs/research/)에 남겼습니다. 추가 확인을 위한 3개 도메인은 환경 설정 초안에 저장했으나 적용을 기다리고 있습니다.

다음 소재는 [균형 순환 편집 기준](docs/editorial-selection.md)에 따라 빈 세부 주제와 원고가 적은 분야를 먼저 살피되 자료가 충분한 이야기를 선정합니다. [43개 세부 주제 현황](docs/topic-coverage.md)은 `python3 tools/topic_coverage.py`로 갱신합니다. 현재 원고가 있는 세부 주제는 21개이며, 실제 공개된 글의 수가 아닙니다.

화면 캡처: [첫 화면](docs/previews/home-desktop.png), [모바일 첫 화면](docs/previews/home-mobile.png), [글 읽기](docs/previews/story-desktop.png), [모바일 글 읽기](docs/previews/story-mobile.png). 캡처는 미게시 원고를 포함하는 검토용 빌드의 모습입니다. 화면 캡처는 클릭 가능한 실제 웹 미리보기가 아닙니다.

이번에 추가한 [이야기 12편](docs/review/batch-20261027-more.md)은 비어 있던 세부 주제에 한 편씩 배치했습니다. 사진 5장과 AI 삽화 7장을 준비하고 [자료·이미지 확인 기록](docs/research/twelve-stories-20261027.json)을 남겼습니다. 첫 화면의 이야기 목록은 최대 9편을 보여주며 전체 글은 분류와 검색에서 확인합니다.

## 홈페이지와 읽기 구분

[홈페이지 확인 안내](docs/homepage-review.md)에서 검토용 홈페이지를 내려받고 화면을 확인할 수 있습니다. `python3 tools/package_review.py`는 21편의 검토본을 `downloads/knowledgewalk-homepage-review.zip`으로 묶습니다. 압축을 모두 풀고 `index.html`을 열면 됩니다. 웹 배포나 운영 사이트 변경은 수행하지 않습니다.

`library.html`은 8개 분야 / 43개 소주제별 서가, `reading.html`은 개인 읽기 목록입니다. 읽음은 사용자가 직접 표시하며 브라우저 로컬 저장소에만 보관합니다. 기기 간 동기화·편집 승인 기능은 아닙니다. 저장소 접근이 막히면 표시 기능을 끄고 글은 계속 보여줍니다.

원고 JSON과 GitHub 읽기용 Markdown을 모두 `분야/소주제/` 아래로 옮겼습니다. 생성기·내보내기·집계는 하위 폴더를 읽고, 원고의 분류와 실제 경로가 다르면 빌드를 중단합니다. 글의 HTML 주소는 ID 기준을 유지합니다. 빈 소주제도 GitHub에서 안내 파일로 확인할 수 있습니다.

## 실행

Python 3.10 이상이면 빌드와 기본 검사가 실행됩니다. 외부 패키지 설치, API 키, 인터넷, Node 빌드가 필요 없습니다. 기존의 격리된 체크아웃을 사용하며 별도 Git worktree는 만들지 않습니다.

저장소 루트에서:

```sh
# 공개 가능한 글만 골라 _site/ 생성. 업로드나 배포는 하지 않습니다.
python3 tools/build_site.py

# 미게시 초안을 포함한 검토 화면을 _preview/에 생성합니다.
python3 tools/build_site.py --preview

# 검토용 결과를 로컬 HTTP 서버로 확인합니다.
python3 -m http.server 8000 --bind 127.0.0.1 --directory _preview
```

서버는 검사나 작업이 끝나면 종료합니다. 이미지와 내비게이션은 파일을 직접 열어도 작동하지만, 검색 자료도 함께 생성하므로 검색은 파일을 직접 열어도 작동합니다. 파일 모드의 읽기 기록 보존은 브라우저별로 다를 수 있습니다.

체크인된 루트 `index.html`과 관련 HTML·리소스를 공개용 결과로 갱신하려면:

```sh
python3 tools/build_site.py --sync-root
```

현재 GitHub Pages는 기존의 `main:/` legacy/Jekyll 게시 설정을 사용합니다. `--sync-root`는 `_site/`의 승인된 공개 파일만 루트에 복사하고 `_config.yml`에 그 외 원고·문서·이전 코드의 제외 목록을 생성합니다. 파일을 삭제하지 않으며 공개 제외 경로는 실제 웹에서 404로 확인했습니다. `.nojekyll`을 추가하거나 `_config.yml`을 제거하지 않습니다. 별도 워크플로는 검사·아티팩트 보관을 담당하고, 기존 Pages 작업이 실제 게시를 수행합니다. 다른 호스팅에서는 `_site/`만 배포합니다. `_preview/`의 `noindex`는 접근 제한 기능이 아닙니다. 현재 GitHub에 `CNAME`을 등록했으며, Hostinger DNS와 도메인 HTTPS 검증은 남아 있습니다.

## 콘텐츠와 분류

- `config/categories.json`: 사용자 스크린샷의 8개 분야와 43개 세부 분류. 표기와 순서를 보존했습니다.
- `content/stories/<분야>/<소주제>/*.json`: 새 사이트가 읽는 원고와 메타데이터.
- `content/drafts/`: 집필 원본과 편집 메모. 빌더가 이 폴더를 자동 수집하지 않습니다.
- `site/`: CSS·JavaScript·파비콘 원본. 외부 글꼴·CDN·추적 스크립트에 의존하지 않습니다.
- `tools/build_site.py`: 검증과 HTML 생성. 새 원고를 넣으면 글 페이지, 분류 목록, 첫 화면, 검색 자료에 반영합니다.
- `legacy/index-before-static-site.html`: 기존 루트 첫 화면의 원본 보관본.

사자 이야기의 웹용 JSON은 승인받은 짧은 Markdown 원고를 옮긴 것입니다. 이후 사이트의 수정 기준은 해당 JSON이고, 이전 Markdown은 집필 이력으로 보존합니다. 원고의 본문은 HTML이 아닌 문단 텍스트로 저장하며, 출력 시 이스케이프합니다.

새 글은 `content/stories/cities/europe/venice-winged-lion.json`의 형식을 따라 작성합니다. 글마다 고유 `id`, 대분류 하나, 세부 분류 하나, 제목·소개, 이미지, 본문 단락, 출처·검토 상태가 필요합니다. AI가 이 파일을 작성·관리하며 사용자가 JSON을 배울 필요는 없습니다.

선택적으로 `featured: true`를 지정하면 해당 빌드에 포함되는 글 가운데 먼저 표시합니다. 미검증 초안에 이 값이 있어도 공개용 결과물에는 들어가지 않습니다. 나머지 글은 분야 순서와 고유 ID 순서로 정렬합니다.

검토용 Markdown을 GitHub에서 읽기 좋게 다시 내보내려면 `python3 tools/export_review.py`를 실행합니다. 원고 JSON이 수정 기준이며, `docs/review/`의 글은 그 복사본입니다. 각 글의 삽화는 저장소 안의 실제 이미지로 연결되어 GitHub에서 확인할 수 있습니다.

이미지는 `image.file`의 저장소 내부 파일을 가리킵니다. 빌더가 선택된 글의 이미지만 배포 결과의 `media/`로 복사합니다. AI 그림은 `ai_illustration`으로 구분하고 설명용 삽화임을 표시합니다. 사진과 미술 작품 이미지는 출처 URL과 이용 조건도 기록해야 합니다.

「독서당계회도」는 국립고궁박물관 소장품 상세 페이지에서 출처표시 이용 조건을 확인한 실제 소장품 이미지입니다. 공개 표시용 사진을 그대로 복사하고 소장·제공 기관과 원문 링크를 표기했습니다. 고해상도 내려받기 신청서나 이용목적 정보는 제출하지 않았습니다. 세로 작품의 실제 크기를 `image.width`, `image.height`에 기록하며, 목록과 읽기 화면에서 전체 작품을 자르지 않고 표시합니다. 새 원고는 `Culture → Art` 한 곳에만 배치합니다.

## 공개 조건

공개용 빌드에 들어가려면 **모든** 조건이 충족되어야 합니다.

- `status`가 `approved`.
- `publication_ready`가 JSON 불리언 `true`.
- `source_review`가 `verified`.
- `approved_by`와 `approved_at`에 실제 승인 정보가 있음. 승인 날짜는 `YYYY-MM-DD`.
- 출처가 하나 이상이며, 각 출처에 `title`, HTTPS `url`, `checked_at` 날짜, `verified: true`가 있음.

승인 표시가 있는데 출처나 승인 정보가 빠져 있으면 조용히 게시하지 않고 빌드 자체를 실패시킵니다. 이 검사는 데이터의 누락을 막을 뿐, 출처의 진위나 주장의 정확성을 AI가 자동 보증하는 기능은 아닙니다. 값을 채우기 전에 실제 사실 확인과 편집 승인이 필요합니다. 테스트에서만 쓰는 가상 승인 자료는 실제 콘텐츠에 저장하지 않습니다.

생성기는 콘텐츠를 만들거나 API를 호출하지 않습니다. 대량 초안 작성, 출처 조사, 이미지 준비, 공개 결정과 사이트 HTML 생성은 분리합니다. 제작 주기·수량·게시 시점은 아직 미정입니다.

자료 대조만 끝난 글은 `status: review`, `source_review: verified`, `publication_ready: false`로 보관합니다. 이때도 확인한 출처 기록이 모두 있어야 빌드 검증을 통과합니다. 검토 화면과 GitHub 문서에는 ‘자료 대조 완료·게시 승인 대기’를 표시하고, 출처별로 무엇을 확인했는지 안내합니다. 일부 근거만 확인된 글은 원고 단위의 `source_review`를 `pending`으로 유지합니다.

## 검증

```sh
python3 -m unittest discover -s tests -v
node --check site/site.js
```

기본 검사는 분류 수, 미검증 초안의 공개 제외, 잘못된 승인 차단, 파일 경로, 글 주소 유지, 텍스트 이스케이프, 생성된 모든 페이지의 로컬 링크·이미지·목차 연결 등을 확인합니다.

실제 브라우저 검사는 선택 사항입니다. 이 클라우드 환경에 있는 Playwright Python과 `/usr/bin/chromium`을 사용합니다. 새 환경에는 별도 설치가 필요할 수 있으며 기본 빌드의 의존성은 아닙니다.

```sh
python3 tools/build_site.py --preview
python3 tools/build_site.py
python3 tests/browser_check.py
```

브라우저 검사는 데스크톱·모바일 내비게이션, 이미지 로딩, 한국어 검색·필터·초기화, 소주제 서가, 읽음 저장·취소·필터·탭 간 반영, 저장소 접근 실패 안내, 빈 목록, 자바스크립트 없는 읽기, 공개용 결과의 초안 제외를 확인하고 화면 캡처를 갱신합니다. 관리형 Chromium의 파일 URL 정책 때문에 파일 직접 열기는 검사하지 못하며, 포함된 검색 자료는 JSON fetch를 막은 상태에서 검증합니다. 검사 중 만든 로컬 서버와 브라우저는 종료합니다.

## 남은 작업

- 원고 21편의 편집·이미지 검토와 남은 3편의 추가 출처 대조. 자료 대조와 공개 승인은 별도입니다.
- 첫 화면과 읽기 화면의 사용자 검토.
- 제작·검토·게시 주기와 승인 방식 결정.
- Hostinger DNS 전환·사용자 지정 도메인 HTTPS 설정과 최종 접속 검증. GitHub 게시와 도메인 등록은 완료됐으며 같은 전환 승인을 다시 요청하지 않습니다.
