# knowledgewalk.net — 전환 진행 상태

기준일: 2026-10-27 (한국 시간).

**사이트 게시, Hostinger DNS 변경, 사용자 지정 도메인의 HTTPS 접속을 확인했습니다. GitHub Pages의 Enforce HTTPS 체크만 남아 있습니다.**

## 완료한 작업

- 사용자가 현재 Codex 채팅에서 사이트 게시와 `knowledgewalk.net` 연결 변경을 요청했다. 승인 기록은 [최초 공개 기록](../config/releases/first-publication-20261027.json)을 따른다. 같은 전환 승인을 다시 요청하지 않는다.
- 출처 확인이 끝난 18편을 공개 대상으로 설정했다. 추가 확인 중인 품계석·오케스트라 조율·동전 테두리 3편은 제외했다.
- `main`에 새 홈페이지를 반영했고 GitHub Pages의 실제 게시 작업에 성공했다.
- GitHub 기본 주소에서 공개 글 18편과 화면·검색·이미지 등 42개 리소스가 로컬 공개용 결과와 같은 바이트로 제공되는지 확인했다. 초안·편집 자료·이전 코드·검토용 ZIP 등 9개 제외 경로는 HTTP 404임을 확인했다. [실제 응답 검증 기록](research/first-live-deployment-20261027.json)을 따른다.
- 루트 [CNAME](../CNAME)에 `knowledgewalk.net`을 등록했고, GitHub Pages API에서도 `cname: knowledgewalk.net`으로 반영된 것을 확인했다.
- 현재 NS가 `ns1.dns-parking.com`, `ns2.dns-parking.com`인 것을 조회했다. 후이즈에서 구매한 도메인의 DNS는 현재 Hostinger 쪽에서 관리한다. [전환 전 공개 DNS 기록](research/domain-dns-before-migration-20261027.json)에 웹·이메일 레코드를 보관했다.
- 기본 검사 18개와 GitHub의 검증 작업이 통과했다. 데스크톱·모바일의 기존 로컬 브라우저 검증도 통과했다. 실제 외부 HTTPS 주소의 브라우저 검사는 이 환경의 Chromium 프록시 인증서 신뢰 오류로 완료하지 못했으며, 검증을 끄지 않았다. 실제 웹 리소스 확인은 정상 인증서 검증을 사용하는 HTTPS 요청으로 수행했다.

## 현재 게시 방식

이 저장소에는 기존에 `main`의 루트에서 게시하는 GitHub Pages legacy/Jekyll 설정이 있었다. API 읽기는 가능하지만 게시 방식 변경 API는 연결된 인증에 HTTP 403을 반환했다. 기존 게시 방식을 그대로 사용해 배포했다.

`python3 tools/build_site.py --sync-root`는 `_site/`의 승인된 공개 파일을 루트에 복사하고, `_config.yml`에 그 외 루트 항목의 제외 목록을 생성한다. 이전 코드나 원고 파일을 삭제하지 않는다. Jekyll이 이 제외 목록을 적용해 실제 사이트에는 공개 파일만 내보낸다. `_config.yml`을 없애거나 `.nojekyll`을 추가하면 이 보호가 사라지므로 하지 않는다.

Jekyll 3의 제외 목록은 단순 폴더 이름을 접두어로도 해석한다. 따라서 소스 폴더 `site`를 그대로 제외하면 공개 폴더 `site-assets`까지 제외되는 문제가 있어 폴더는 `site/*`와 같은 형태로 제외한다. 실제 웹에서 CSS·JavaScript를 포함한 42개 리소스의 제공을 재확인했다.

[별도 작업 설정](../.github/workflows/pages.yml)은 검사와 `_site/` 아티팩트 보관만 담당한다. 실제 배포는 기존 GitHub의 `pages build and deployment` 작업이 수행한다. 정기 AI 생성이나 게시 시간표는 설정하지 않았다.

다른 호스팅이나 추후 Actions 방식으로 바꿀 때는 `_site/`만 배포한다. 기존 legacy 방식에서 루트가 게시 원본인 것은 `_config.yml`의 제외와 원고별 승인 필터를 함께 검증한 경우에 한정한다. 저장소 전체를 그대로 복제하는 일반 정적 호스팅으로 배포하지 않는다.

## 도메인 전환 확인 결과

사용자가 Hostinger 화면에서 `ALIAS @`와 `CNAME www`를 모두 `linguawalk.github.io`로 바꾸었다. 실제 DNS에서 IPv4 네 주소와 IPv6 네 주소가 GitHub Pages를 가리키며, www CNAME도 반영된 것을 확인했다. 후이즈나 네임서버를 변경하지 않았고, 사용자 화면의 다른 레코드는 유지됐다. 실제 MX/TXT 응답도 전환 전 값과 같은 것을 대조했다.

`https://knowledgewalk.net/`의 글 18편과 화면·검색·CSS·JavaScript·이미지 등 42개 응답을 로컬 공개용 결과와 바이트 단위로 비교해 일치함을 확인했다. `https://www.knowledgewalk.net/search-index.json`도 `https://knowledgewalk.net/search-index.json`으로 이동하고 18편을 제공했다. [도메인 실접속 검증 기록](research/custom-domain-live-20261027.json)을 따른다. Hostinger 원본 자료나 호스팅 계약은 삭제·해지하지 않았다.

Hostinger의 ALIAS가 GitHub의 A/AAAA 응답을 제공하므로 네 개 A 레코드를 별도로 추가하거나 기존에 없는 AAAA를 삭제할 필요가 없다. 현재 Hostinger 설정에서 ALIAS와 CNAME 두 항목만 변경한 결과를 기준으로 한다.

## 남은 한 항목: HTTPS 자동 이동

GitHub Pages API에서 `https_enforced: false`인 것을 확인했다. 이미 HTTPS 자체로는 정상 접속되지만 항상 HTTPS를 사용하도록 강제하는 설정은 아직 꺼져 있다. 설정 변경 API는 연결된 인증에 HTTP 403을 반환했다. 이를 대신 우회하는 코드를 추가하지 않는다.

사용자가 [이 저장소의 Pages 설정](https://github.com/linguawalk/Knowledge-Walk/settings/pages)에서 **Enforce HTTPS**를 체크해야 한다. 체크가 비활성화돼 있으면 실제 화면의 설명을 확인하고 안내한다. 설정 후 AI가 `https_enforced: true`와 실제 접속을 다시 확인한다. 이는 새 배포 승인 요청이 아니라 제한된 계정 설정 한 항목의 조작이다.

현재 API 응답에는 `https_certificate` 필드 자체가 없다. 앞서 jq로 이 필드를 선택했을 때 나온 null은 인증서 부재의 증거가 아니므로, 실제 HTTPS 성공과 구분한다. TLS 검증을 끄지 않은 요청으로 도메인의 HTTPS 응답을 확인했다.

## 운영 시 주의할 구성

Hostinger 메일용 MX/TXT와 다른 하위 도메인, 네임서버는 유지한다. Hostinger 원본 파일·데이터베이스와 계약은 이번 전환으로 삭제하거나 해지하지 않는다. 도메인과 GitHub Pages 등록은 계속 함께 유지한다.

현재 GitHub Pages는 main 루트의 legacy/Jekyll 게시 방식이다. `_site/`를 동기화한 공개 파일만 내보내도록 `_config.yml`의 제외 목록을 유지한다. `.nojekyll`을 추가하거나 제외 목록을 제거하지 않는다. 다른 호스팅에는 `_site/`만 배포한다.
