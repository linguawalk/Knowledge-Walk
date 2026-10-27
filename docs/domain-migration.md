> 현재 상태 갱신: 환경 재연결 후 GitHub API 읽기와 DNS 조회가 가능해졌다. GitHub Pages는 이미 `main:/`에서 legacy/Jekyll 방식으로 게시 중이며, 게시 방식 변경 API는 연결된 인증에 HTTP 403을 반환했다. 따라서 기존 게시 방식을 유지하고 `_site/`의 공개 파일을 루트에 동기화하되 `_config.yml`로 초안·문서·이전 코드를 모두 제외한다. Pages의 기본 게시 작업이 실제 웹 배포를 수행하고, 별도 워크플로는 검증과 공개용 아티팩트 보관만 담당한다. 도메인 NS는 `ns1.dns-parking.com`, `ns2.dns-parking.com`으로 확인되어 Hostinger DNS를 사용한다. 아래 초기 차단 기록과 Actions 전환 계획은 이전 조사 이력이며 이 갱신 내용이 우선한다.

# knowledgewalk.net — GitHub Pages 전환 준비

기준일: 2026-10-27 (한국 시간). **아직 전환 완료 상태가 아닙니다.**

## 승인과 준비 결과

사용자가 현재 Codex 채팅에서 “지금 Hostinger에 연결된 사이트를 해제하고, 깃허브에서 만들어진 사이트를 도메인에 연결하였으면 합니다”라고 요청했다. 새 사이트 게시와 도메인 연결 변경의 승인으로 기록한다. 같은 작업의 배포 승인을 다시 요청하지 않는다.

출처 대조를 마친 18편을 공개 대상으로 설정했다. 추가 확인 중인 궁궐 품계석·오케스트라 조율·동전 테두리 이야기 3편은 공개 대상에서 제외했다. 승인 원고 목록과 요청 기록은 [최초 공개 기록](../config/releases/first-publication-20261027.json)을 따른다. 공개 승인과 실제 배포 성공은 구분한다.

공개용 생성 결과는 `_site/`이며, 현재 18편이 들어간다. 원고·편집 메모·검토용 ZIP·이전 WordPress 파일은 배포하지 않는다. 저장소 루트의 HTML은 편의 사본일 뿐 배포 경로가 아니다.

[GitHub Pages 작업 설정](../.github/workflows/pages.yml)은 `main`의 승인된 콘텐츠를 검사하고 `_site/`만 업로드·게시한다. 시간표나 AI 정기 집필은 설정하지 않는다. 공식 Actions는 실제 조회한 버전 커밋으로 고정했다. 이 파일을 검토 브랜치에 올린 것만으로 게시가 실행되지는 않는다.

## 아직 막혀 있는 부분

현재 실행 환경은 `api.github.com`, `knowledgewalk.net`, DNS 조회 주소에 대해 프록시 연결 단계의 HTTP 403을 반환했다. 이는 GitHub 저장소 권한이나 DNS 레코드 오류를 확인했다는 뜻이 아니다. 기존 Git 읽기·쓰기와 GitHub 웹 파일 열람은 가능하다. 기존 `GH_TOKEN` 변수가 있으므로 별도 토큰을 중복 요청하지 않았다.

환경 설정 변경안에 필요한 접속 도메인을 추가해 저장했다. **저장만으로 현재 환경의 제한이 풀린 것은 아니다.** 환경 설정의 변경안을 적용·게시한 후 GitHub API와 도메인 상태를 다시 조회해야 한다.

사용자는 도메인을 국내 후이즈에서 구매했고 Hostinger에서 연결 설정을 변경한 것으로 기억한다고 알려 주었다. Hostinger 도구나 도메인 관리 인증 정보는 현재 연결되어 있지 않다. 실제 DNS 관리 주체는 네임서버를 조회해 확인해야 한다. 후이즈 구매나 Hostinger 웹호스팅 사용만으로 현재 DNS 관리 업체를 단정하지 않는다. 비밀번호·API 키를 채팅이나 저장소에 넣지 않는다.

## 실제 전환 순서

1. 환경 접속 변경안을 적용한 뒤 이 저장소의 Pages 설정, 권한, 현재 DNS의 NS/A/AAAA/CNAME/MX/TXT/CAA를 읽는다. 기존 값을 기록해 복구할 수 있게 한다.
2. `origin/main`에 새 변경이 없는지 다시 조회한다. 현재 `main`은 준비 브랜치의 조상이며, 충돌이나 새로운 사용자 변경이 없을 때 준비 커밋을 일반 fast-forward로 반영한다. 강제 푸시는 하지 않는다.
3. GitHub Pages의 게시 방식을 GitHub Actions로 설정하고, 이 저장소에 `knowledgewalk.net`을 사용자 지정 도메인으로 등록한다. 워크플로가 실행되어 `_site/` 게시에 성공했는지 확인한다. Actions 방식에서는 CNAME 파일만 넣는 것으로 사용자 지정 도메인이 설정되지 않는다.
4. GitHub 측 도메인 등록·게시 준비가 확인된 뒤에만 도메인 관리 화면에서 웹사이트 연결 레코드를 전환한다. 이메일용 MX/TXT 등 관련 없는 레코드와 네임서버는 유지한다.
5. DNS 반영과 인증서 발급 뒤 HTTPS 강제를 켜고, `knowledgewalk.net` 및 `www.knowledgewalk.net`의 연결·HTTPS·대표 글·이미지·검색·읽음 표시를 실제 웹주소에서 확인한다.
6. 새 사이트가 정상 동작하면 전환 완료를 기록한다. 기존 Hostinger 사이트 파일·데이터베이스는 보존한다. 호스팅 계약 해지나 자동 결제 취소는 이번 요청에서 실행하지 않는다.

DNS 변경부터 먼저 하거나 Hostinger 사이트부터 삭제해 빈 페이지를 만들지 않는다. GitHub 쪽 준비에 문제가 있으면 전환 전 상태를 유지한다. 변경 후 문제가 발견되면 기록해 둔 웹 레코드로 복구한다.

## 계획된 웹 연결 값

아래는 GitHub 공식 문서에서 확인한 **목표 값**이며, 현재 DNS를 조회한 결과나 이미 적용된 값이 아니다.

| 이름 | 종류 | 목표 값 |
|---|---|---|
| `@` | A | `185.199.108.153` |
| `@` | A | `185.199.109.153` |
| `@` | A | `185.199.110.153` |
| `@` | A | `185.199.111.153` |
| `www` | CNAME | `linguawalk.github.io` |

기존 웹용 A/AAAA/ALIAS/CNAME 중 충돌하는 항목은 실제 값을 확인한 뒤 선택적으로 바꾼다. IPv6를 유지한다면 GitHub의 공식 AAAA 네 주소를 사용한다. 기존 Hostinger IPv6 주소를 남겨 두어 방문자마다 다른 사이트로 가게 하지 않는다. CAA가 인증서 발급을 제한한다면 실제 발급 기관과 GitHub의 진단 결과를 확인해 필요한 범위만 조정한다. 이메일 설정이나 다른 하위 도메인을 일괄 삭제하지 않는다.

공식 근거: [GitHub Pages의 사용자 지정 도메인 관리](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site). 이 환경에서는 [공식 문서 저장소의 같은 원문](https://github.com/github/docs/blob/main/content/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site.md)을 실제 읽어 주소와 설정 순서를 확인했다. 전환 당일 다시 공식 설정과 현재 계정 상태를 대조한다.

## 확인 명령

기본 검사와 공개용 생성:

```sh
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
```

접속 제한이 풀린 뒤 GitHub 게시 설정 확인:

```sh
gh api repos/linguawalk/Knowledge-Walk/pages
```

이 문서는 준비·차단 상태 기록이다. 실제 Pages 생성, 워크플로 실행 성공, DNS 수정, 인증서 발급과 최종 접속은 아직 확인하지 못했다.
