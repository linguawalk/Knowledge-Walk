# 두 도메인 분리 게시

2026-11-01 사용자 요청: “홈페이지를 net와 kr로 분리하여 게시”. 작업 저장소는 `linguawalk/Knowledge-Walk` 하나입니다.

## 설치 파일

[kr 설치 압축파일 내려받기](https://github.com/linguawalk/Knowledge-Walk/actions/runs/41303301260/artifacts/13081509047) — 약 203MiB, GitHub 로그인 필요. 이 결과물은 14일 보관됩니다. 파일 관리자에 올릴 때는 이 압축을 그대로 업로드하고 `public_html` 안에 풉니다.

## 구성과 현재 단계

- net: 국가와 이야기, 승인 원고 171편. 기존 GitHub Pages 도메인에서 실제 게시와 공개 응답 23개를 확인했습니다.
- kr: 발견과 지식, 승인 원고 117편, 기존 Hostinger에 올릴 독립 정적 사이트입니다. WordPress나 별도 데이터베이스를 사용하지 않습니다.
- kr의 Hostinger 업로드는 로그인 연결이 필요합니다. 이 채팅에는 Hostinger 접속 도구·인증정보가 없으며 GitHub 연결도 저장소 시크릿을 읽을 권한이 없습니다. 접속이 완료됐다고 표시하지 않습니다.
- kr 업로드 전에는 `https://knowledgewalk.net/knowledge/index.html`에서 주제 사이트를 임시 제공합니다. net의 교차 링크와 기존 117개 글 주소도 이곳으로 이어져 읽기 접근을 유지합니다. 이 임시 주소를 kr 도메인 게시 완료로 해석하지 않습니다.

`config/deployment.json`의 `kr_live: false`가 이 전환 단계를 나타냅니다. kr의 첫 화면·117편·이미지·검색·HTTPS를 확인한 뒤에만 `true`로 바꿉니다. 그러면 net의 연결 및 기존 글 안내가 실제 kr 도메인을 가리키게 됩니다.

## 생성·검증

```sh
python3 tools/build_site.py --sync-root
python3 -m unittest discover -s tests -v
python3 tools/build_domains.py --package-kr
```

설정에 따라 기본 공개 생성기도 분리 모드로 동작합니다. `--preview`는 기존처럼 미게시 원고를 포함하는 비공개 배포 대상 외의 로컬 검토본입니다.

- `_site/`: net 게시본. 국가 중심 검색·서가와 임시 주제 사이트, 이전 주소 안내를 포함합니다.
- `_kr-site/`: 독립 kr 게시본. 이미지·스타일·검색 자료가 함께 있습니다.
- `downloads/knowledgewalk-kr-site.zip`: 파일 관리자로 올릴 설치본. 압축 루트에 `index.html`·`.htaccess`·`stories`·`media`·`site-assets`가 있습니다. 원고 JSON·초안·비밀번호·CNAME·WordPress 파일은 포함하지 않습니다.

GitHub 검증 작업에서도 두 게시본을 생성하고 kr 설치본을 `knowledgewalk-kr-site` 결과물로 저장합니다. 이것은 Hostinger 자동 업로드가 완료됐다는 뜻이 아닙니다. FTP/SFTP 업로드 자동화에는 사용자가 안전하게 설정하는 별도의 인증 연결이 필요합니다. 비밀번호나 비밀 키를 채팅·Git에 기록하지 않습니다.

## Hostinger 초기 반영

1. `knowledgewalk.kr → Files → File Manager → Access files of knowledgewalk.kr`를 엽니다.
2. 해당 도메인의 `public_html`을 확인합니다. 다른 도메인·`art` 등의 파일은 변경하지 않습니다.
3. 기존 파일을 삭제하지 않습니다. `.htaccess`나 기존 `index.html`이 있으면 이름을 바꾸어 보관하거나 백업 후 설치본의 동명 파일을 반영합니다. WordPress의 `index.php`·설정·콘텐츠는 그대로 둡니다.
4. 설치 압축을 해당 폴더에 업로드하고 그 안에 풉니다. `public_html/knowledgewalk-kr-site/index.html`처럼 한 단계 더 들어가면 안 됩니다. `public_html/index.html`이 되어야 합니다.
5. 설치본 `.htaccess`는 `DirectoryIndex index.html index.php`로 새 정적 첫 화면을 우선 표시합니다. 기존 WordPress의 재작성 규칙을 새 설정으로 덮기 전에는 백업합니다. 문제가 생기면 새 `index.html`을 치우고 기존 `.htaccess`를 복원하여 이전 사이트로 돌아갈 수 있습니다.
6. 실제 kr 도메인의 HTTPS·첫 화면·이미지·임의 글·검색을 확인합니다. 검증 후 전환 설정을 활성화합니다.

현재 DNS가 기존 Hostinger 서버를 가리키고 있다면 이 방법에 DNS 변경은 필요하지 않습니다. 화면에 보인 과거 값을 근거로 새로운 DNS 변경을 수행하지 않으며, 이메일·하위 도메인·후이즈의 도메인 소유 정보는 건드리지 않습니다.

## 기존 주소와 콘텐츠 보존

net에 남는 171편은 `/stories/{id}/index.html` 주소를 유지합니다. kr로 갈 117편의 옛 net 주소는 일반 링크와 자바스크립트 자동 이동 페이지로 바꿉니다. 번호 소제목에 연결된 해시와 쿼리를 보존합니다. GitHub Pages가 임의의 HTTP 301을 지원한다고 가정하지 않습니다.

과거의 분야·소주제·묶음 주소도 각 글의 소유 사이트로 연결되게 유지합니다. 검토 원고 13편은 두 공개 사이트 모두에서 제외합니다. 원문·출처·이미지 권리 표시는 바꾸지 않습니다. 각 사이트의 본문은 서로 겹치지 않는 검색 목록으로 제공하며, 기존 미리보기의 이미지 호환을 위해 과거 공개 이미지 경로도 유지합니다.

새 국가 분류와 kr 배치가 실제로 달라지면 `config/proposals/net-kr-story-placement.json`을 먼저 갱신합니다. 폴더명이나 본사·박물관의 소재지로 자동 재분류하지 않습니다. 자동 글 생성은 활성화하지 않았습니다.

## AI 직접 업로드 연결

`.github/workflows/hostinger-kr.yml`은 수동 실행만 가능하며 기본값은 파일을 바꾸지 않는 연결 검사입니다. 직접 게시 요청을 받은 경우에만 `publish: true`로 실행합니다. `tools/deploy_hostinger.py`는 암호화된 FTPS만 사용하고 서버 인증서 확인을 끄거나 평문 FTP로 전환하지 않습니다. 서버 주소 145.79.26.89, 사용자 u250225041, 대상 knowledgewalk.kr의 public_html은 사용자가 보여 준 Hostinger 화면에서 확인했습니다.

GitHub 저장소의 [비밀정보 추가 화면](https://github.com/linguawalk/Knowledge-Walk/settings/secrets/actions/new)에서 이름 `HOSTINGER_FTP_PASSWORD`에 FTP 비밀번호를 등록합니다. 채팅이나 저장소 파일에는 비밀번호를 넣지 않습니다. 환경의 HTTPS 프록시 비밀정보를 FTP 인증에 사용할 수 있다고 가정하지 않습니다. GitHub 실행 환경이 비밀정보를 직접 받아 업로드하며 AI는 값을 읽을 필요가 없습니다.

실제 연결에서 서버 인증서의 이름이나 계정 내 경로가 다르면 업로드를 중단합니다. 해당 경우 정확한 서버 호스트명을 확인해 저장소 변수 `HOSTINGER_FTPS_HOST`에 지정합니다. IP 주소가 있다는 이유로 인증서 검사를 해제하지 않습니다. 대상 경로가 knowledgewalk.kr임을 확인하지 못해도 업로드하지 않습니다. 일반 FTP 연결 화면만으로 FTPS·로그인·업로드의 성공까지 확인된 것은 아닙니다.

게시할 때는 일반 파일과 이미지를 먼저 올리고 `.htaccess`·`index.html`을 마지막에 반영합니다. 기존 두 파일은 숨김 백업 이름으로 보관합니다. WordPress와 art 폴더를 삭제하는 동작은 없습니다. 업로드 후 실제 HTTPS 확인이 끝나야 `kr_live`를 활성화합니다.
