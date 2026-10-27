# knowledgewalk.net — 전환 진행 상태

기준일: 2026-10-27 (한국 시간).

**GitHub 사이트 게시와 사용자 지정 도메인 등록은 완료했습니다. Hostinger DNS 전환과 도메인의 HTTPS 확인은 남아 있습니다.**

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

## 남은 작업: Hostinger의 웹 연결 변경

Hostinger 관리 계정이나 DNS 변경 도구가 이 채팅에 연결되어 있지 않아 DNS 레코드는 변경하지 않았다. 도메인은 아직 기존 Hostinger 주소를 가리킨다. Hostinger의 `knowledgewalk.net` DNS 설정 화면에서 현재 항목을 확인한 뒤 아래의 웹 레코드만 바꾼다.

| 이름 | 종류 | 새 값 |
|---|---|---|
| `@` | A | `185.199.108.153` |
| `@` | A | `185.199.109.153` |
| `@` | A | `185.199.110.153` |
| `@` | A | `185.199.111.153` |
| `www` | CNAME | `linguawalk.github.io` |

현재 `@`의 기존 A 두 주소는 `147.79.72.93`, `147.79.79.9`다. 기존 웹용 A를 위 네 주소로 교체하고, Hostinger로 향하는 `@`의 AAAA 두 항목은 제거하거나 GitHub의 공식 IPv6 값으로 교체해야 한다. 기존 IPv6를 남기면 일부 방문자가 계속 이전 사이트에 접속할 수 있다. `www`의 현재 CNAME은 `www.knowledgewalk.net.cdn.hstgr.net`이므로 위 값으로 바꾼다.

**MX/TXT 이메일 레코드, 다른 하위 도메인과 네임서버는 그대로 둔다.** 화면에서 항목이 잠겨 있거나 CDN 설정과 연동되어 있으면 화면을 먼저 확인하고 필요한 웹 연결만 조정한다. Hostinger 사이트 파일·데이터베이스를 삭제하거나 호스팅 계약을 해지하지 않는다. API 키·비밀번호를 채팅이나 저장소에 넣지 않는다.

공식 근거: [GitHub Pages 사용자 지정 도메인 관리](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site). 연결 값은 실제 열람한 [공식 문서 원문](https://github.com/github/docs/blob/main/content/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site.md)에 따른다.

## DNS를 바꾼 뒤

1. A/AAAA/CNAME의 실제 응답이 목표 값으로 반영됐는지 확인한다.
2. GitHub의 사용자 지정 도메인 검사와 인증서 발급 상태를 확인한다. 현재 등록 직후에는 인증서가 없고 HTTPS 강제도 꺼진 상태다.
3. 인증서가 준비되면 HTTPS 강제를 켜고 `knowledgewalk.net`, `www.knowledgewalk.net`의 연결·리디렉션·글·이미지·검색을 실제 도메인에서 다시 확인한다. 설정 변경 권한이 계속 제한되면 GitHub Pages 화면의 필요한 한 항목만 사용자에게 안내한다.
4. 검증 후에만 전체 전환 완료를 기록한다. 오류가 있으면 보관한 웹 레코드로 복구한다.

GitHub에 CNAME이 등록되면서 기본 `github.io` 주소는 사용자 지정 도메인으로 이동할 수 있다. DNS 전환 전에는 그 결과 기존 Hostinger 사이트가 보일 수 있으며, 이를 새 홈페이지의 도메인 전환 완료로 오인하지 않는다.
