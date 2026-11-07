# knowledgewalk.net 하나로 국가별·분야별 읽기

2026-11-07 사용자 후속 요청으로 net 단일 도메인 운영을 적용했습니다. 별도 knowledgewalk.kr 도메인·Hostinger·FTP 설정과 배포는 사용하지 않습니다. 이전 FTP 비밀번호 등록 요청도 더 이상 필요하지 않습니다.

- 국가별 보기: https://knowledgewalk.net/
- 분야별 보기: https://knowledgewalk.net/knowledge/
- 음악 서가: https://knowledgewalk.net/knowledge/categories/arts/음악/index.html

원고421편 중 승인408편을 두 탐색 방식에서 함께 제공합니다. 미승인13편은 제외합니다. 원문·이미지·출처는 하나이며 국가와 분야 분류만 다릅니다. 국가에 연결되지 않는 글은 공통 교양·전체 서가·검색에서 제공합니다.

베토벤의 〈엘리제를 위하여〉는 독일 문화 목록과 분야별 음악 서가에서 같은 글로 연결됩니다. 글 안의 국가·분야 서가 링크, 기존 이미지와 번호 소제목·별도 바로가기를 유지합니다.

## 주소와 검색

모든 원고의 대표주소는 `https://knowledgewalk.net/stories/<id>/index.html`입니다. 기존 `/knowledge/stories/<id>/index.html`에서도 같은 본문을 읽을 수 있으며 대표주소는 net 본문을 안내합니다. 예전 분야·소주제·묶음 링크도 유지합니다. 사이트맵은 글마다 대표주소 하나만 포함합니다.

국가별·분야별 검색은 같은408개 승인ID를 사용합니다. 여러 분야에 연결된 글은 관련 분야 필터에서도 찾을 수 있습니다. 같은 net 안의 두 보기이므로 기존 읽음 기록도 같은 브라우저에서 공유됩니다.

## 배포

`config/deployment.json`의 `single_domain:true`가 현재 운영을 나타냅니다. 공개 산출물 `_site`에는 첫 화면과 `/knowledge/` 분야별 보기가 함께 들어갑니다. 별도 `_kr-site` 생성·Hostinger 업로드 워크플로·kr 산출물 업로드는 중단했습니다. 도메인이나 DNS 설정 변경 없이 기존 GitHub Pages로 게시합니다.

내부의 과거 분류 데이터 일부에는 이전 도메인 배치 기록이 남아 있지만 현재 게시와 대표주소는 net만 사용합니다. 콘텐츠 원문과 게시 승인 상태는 바꾸지 않았습니다.
