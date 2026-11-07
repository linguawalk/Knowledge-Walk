# KnowledgeWalk 두 도메인 콘텐츠 배치안

2026-11-07 기준. net 단일 도메인에서 국가별·분야별로 같은 승인 원고를 제공합니다. 별도 kr 연결·FTP 설정은 사용하지 않습니다.

- [net 국가별 배치표](net-placement.md)
- [kr 주제별 배치표](kr-placement.md)
- [전체 목록 CSV](net-kr-placement.csv) — 엑셀 등에서 제목·국가·상태별 정렬 가능
- [배치 데이터](../../config/proposals/net-kr-story-placement.json)
- [분류 구조 제안](../../config/proposals/net-kr-taxonomy.json)

## 공통 원고 수

| 탐색 사이트 | 원본 | 공개 | 미승인 |
|---|---:|---:|---:|
| 국가별 net | 421 | 408 | 13 |
| net 분야별 /knowledge/ | 421 | 408 | 13 |

같은 원고를 두 번 세지 않습니다. 논리적 원본은 421편이고 공개 원고는 408편입니다. 모든 글의 대표주소는 net으로 통일하며 두 탐색 경로에서 모두 읽을 수 있습니다. 국가와 직접 관련 없는 글은 공통 교양·전체 서가·검색으로 제공합니다.

## net의 메뉴와 보완 사항

사용자가 정한 4개 지역과 주요 국가 19개를 유지합니다. 튀르키에는 표준 표기인 **튀르키예**로 정리합니다. 각 지역 아래 **기타 국가**를 두고 실제 국가명을 표시합니다. 오스트리아·그리스·네덜란드 등은 기존 글이 있어도 우선 기타 국가에 놓습니다. 북유럽 전승처럼 한 나라로 좁히기 어려운 글에는 **지역에 걸친 이야기**를 제안합니다.

국가 안에서는 역사·도시·문화·생활로 찾아볼 수 있게 합니다. 2026-11-07 사용자 요청으로 언어 분류를 제거했습니다. 신화·민속은 문화, 식생활·의복·주거·풍습은 생활에 둡니다. 러시아·튀르키예의 메뉴 위치는 사용자 선택을 유지합니다.

| 지역 | 전체 원고 | 현재 게시 중 |
|---|---:|---:|
| 아시아대양주 | 67 | 66 |
| 유럽 | 129 | 122 |
| 아메리카 | 32 | 32 |
| 중동아프리카 | 31 | 31 |

현재 주요 국가 모두에 배치 원고가 있습니다. 미게시 원고를 포함한 수치이며, 국가별 분량을 맞추려고 억지로 분류하거나 빈 내용을 만들지 않습니다.

## kr의 메뉴

- **기업과 산업**: 창업과 성장, 경영과 조직, 공장과 생산, 상업과 유통, 브랜드와 소비
- **컴퓨터와 디지털**: 컴퓨터의 역사, 소프트웨어, 인터넷과 통신, 데이터와 기록, 인공지능, 디지털 생활과 보안
- **돈과 금융**: 돈과 화폐, 은행과 신용, 투자와 시장, 보험과 위험, 금융과 기술
- **과학과 발견**: 우주와 천문, 생명과 인체, 물질과 에너지, 수학과 측정, 과학자의 발견
- **생활을 바꾼 물건과 기술**: 식탁과 식품 보존, 옷과 재료, 집과 생활 도구, 이동과 운송, 놀이와 취미
- **생각과 지식**: 철학의 질문, 예술을 보는 법, 책과 이야기의 형식, 교육과 배움, 기록과 지식 전달, 사회와 제도의 탄생

문화·생활이라는 이름 전체를 한 사이트로 옮기지 않습니다. 특정 작품·작가·민속·지역 생활은 net, 예술을 관찰하는 방법이나 생활 기술의 작동 원리는 kr에 놓습니다. 과학자의 국적이나 기업의 본사 위치만으로 net에 분류하지 않습니다.

## 편집상 경계에 있는 원고

아래 원고는 권장 위치를 정했지만, 여러 문화권·이동 경로·제작국 확인 문제 때문에 배치 이유를 함께 읽는 것이 좋습니다. 확인 표시가 없는 글도 역사적 국경을 현대 국가와 동일시하지 않습니다.

| 제목·원고 | 현재 상태 | 제안 분류 | 배치 이유 |
|---|---|---|---|
| [하라파 — 작은 인장은 왜 먼 도시에서 나왔을까](../../content/stories/cities/asia/harappa-seal-and-distant-trade.json) | 게시 중 | 파키스탄 / 도시 | 유적의 현재 위치인 파키스탄으로 탐색 위치를 정하되 인더스 문명은 여러 현대 국가에 걸친 역사임을 명시. |
| [모헨조다로 — 작은 청동상에서 도시의 생활을 보다](../../content/stories/cities/asia/mohenjo-daro-bronze-and-city-life.json) | 게시 중 | 파키스탄 / 도시 | 현재 파키스탄의 유적 중심. 인더스 문명을 현대 파키스탄만의 역사로 한정하지 않음. |
| [동인도회사 — 장사하러 간 회사는 왜 세금을 걷었을까](../../content/stories/companies/finance/east-india-company-trade-and-taxes.json) | 게시 중 | 기업과 산업 / 상업과 유통 | 영국·인도 역사와 긴밀하지만 기업의 무역 권한·통치 권력이라는 조직 변화가 중심이므로 kr 우선. 국가별 편집 시 연결 가능. |
| [포스터를 한 장씩 붓으로 칠하던 작업장](../../content/stories/companies/media/tass-stencil-posters.json) | 게시 중 | 러시아 / 문화 | 소련 시기 TASS 포스터의 제작·전시라는 문화사 중심. 러시아를 탐색 위치로 삼되 소련 전체를 러시아와 동일시하지 않음. |
| [일본의 나무 장식은 관람석 아래에서 발견됐다](../../content/stories/culture/architecture/japan-phoenix-wood-panels.json) | 게시 중 | 일본 / 문화 | 시카고 박람회에서 전시된 일본관의 장식과 일본 건축 표현이 중심. 미국 전시 이력 때문에 일본 제작 맥락을 바꾸지 않음. |
| [바이외 자수 — 하늘의 긴 꼬리를 사람들이 가리킨 이유](../../content/stories/culture/art/bayeux-embroidery-comet-and-story.json) | 게시 중 | 프랑스 / 문화 | 프랑스의 바이외 유물 중심. 노르만 정복과 영국의 역사를 함께 보존. |
| [유명한 그림도 처음에는 거절당했다](../../content/stories/culture/art/el-greco-painting-journey.json) | 게시 중 | 미국 / 문화 | 작품의 제작국보다 시카고 미술관의 수집 과정이 이야기의 중심이므로 미국에 배치. 스페인·프랑스를 거친 이력은 함께 보존. |
| [옛 베개 사진 옆에는 왜 자가 서 있을까](../../content/stories/culture/art/glass-photo-pillow-ruler.json) | 게시 중 | 생각과 지식 / 기록과 지식 전달 | 베개 자체보다 유리건판 사진·측정 자·기록 방식이 중심이므로 kr의 기록과 지식 전달에 배치. |
| [에라스무스의 초상 — 글을 쓰는 손이 얼굴을 설명할 때](../../content/stories/culture/art/holbein-erasmus-writing.json) | 게시 중 | 생각과 지식 / 예술을 보는 법 | 현 원고는 초상화의 자세·독법이 중심이고 국가 맥락은 약함. 독일 화가·네덜란드 인물·스위스 활동을 추정해 국가를 강제하지 않고 kr의 감상법으로 배치. |
| [체스 말을 어디에 둘지 오래된 사진에 물었다](../../content/stories/culture/art/man-ray-chess-photo-layout.json) | 게시 중 | 생각과 지식 / 예술을 보는 법 | 국가보다 사진을 활용한 전시·감상 방식이 중심이므로 kr에 배치. |
| [모나리자 — 미소와 손, 그리고 그림이 사라진 해](../../content/stories/culture/art/mona-lisa-looking-guide.json) | 게시 중 | 이탈리아 / 문화 | 이탈리아에서 탄생한 작품 중심으로 배치. 프랑스의 소장·도난 사건도 중요하므로 프랑스 국가 페이지에서 연결할 수 있음. |
| [주전자의 이야기는 바닥에도 적혀 있다](../../content/stories/culture/art/silver-kettle-hidden-letters.json) | 게시 중 | 생각과 지식 / 예술을 보는 법 | 소장 기관의 위치만으로 제작국을 정할 수 없음. 현재 원고의 중심인 명문·물건을 관찰하는 방법에 따라 kr로 배치. |
| [롤랭 재상의 성모 — 작은 방 너머에 도시가 펼쳐진다](../../content/stories/culture/art/van-eyck-rolin-window.json) | 게시 중 | 벨기에 / 문화 | 현재 벨기에에 해당하는 저지대·플랑드르 미술 맥락을 탐색 기준으로 제안. 당대 국가 명칭으로 오해하지 않게 안내. |
| [반 고흐의 생애 — 그림 곁에는 편지가 있었다](../../content/stories/culture/art/van-gogh-life-and-letters.json) | 게시 중 | 네덜란드 / 문화 | 네덜란드 출신 화가의 생애를 대표 위치로 삼되 프랑스 활동을 함께 설명. 프랑스 배치도 가능한 편집 판단 항목. |
| [도리언 그레이의 초상 — 얼굴 대신 그림이 늙어 간다면](../../content/stories/culture/literature/dorian-gray-portrait-and-conscience.json) | 게시 중 | 영국 / 문화 | 런던과 빅토리아 시대를 배경으로 한 작품 맥락을 우선. 아일랜드 출신 작가의 정체성은 별도로 명시. |
| [80일간의 세계 일주 — 시계보다 늦게 알게 된 여행의 의미](../../content/stories/culture/literature/eighty-days-time-and-travel.json) | 게시 중 | 프랑스 / 문화 | 프랑스 문학 작품으로 배치하되 여행 경로의 각 나라를 작품의 소속 국가로 중복 지정하지 않음. |
| [프랑켄슈타인 — 만들어 낸 생명에게는 누가 책임질까](../../content/stories/culture/literature/frankenstein-creator-and-creature.json) | 게시 중 | 영국 / 문화 | 영국 문학 작품으로 배치. 스위스에서의 구상과 소설 속 여러 지역을 영국으로 바꾸어 서술하지 않음. |
| [『걸리버 여행기』 — 소인국보다 더 이상한 것은 무엇일까](../../content/stories/culture/literature/gulliver-travels-size-and-satire.json) | 게시 중 | 아일랜드 / 문화 | 아일랜드 문학의 작가와 풍자라는 맥락을 우선한 편집안. 영국 정치·영어권 문학 맥락도 함께 설명해야 함. |
| [『아이다』 — 개선행진곡이 울릴 때 슬퍼하는 사람들](../../content/stories/culture/music/aida-triumphal-march-private-grief.json) | 게시 중 | 이탈리아 / 문화 | 이탈리아 오페라로 배치. 이집트 배경·초연 장소와 작품의 문학·음악적 맥락을 구분. |
| [『세비야의 이발사』 — 피가로는 왜 이렇게 바쁠까](../../content/stories/culture/music/barber-seville-figaro-letters-disguises.json) | 게시 중 | 이탈리아 / 문화 | 이탈리아 오페라로 배치. 세비야라는 배경만으로 스페인에 중복 배치하지 않음. |
| [베토벤의 생애 — 들리는 세계가 달라져도 작업은 이어졌다](../../content/stories/culture/music/beethoven-life-and-work.json) | 게시 중 | 독일 / 문화 | 독일의 음악가라는 소개를 대표 위치로 삼되 빈에서의 활동과 오스트리아 맥락을 보존. |
| [카르멘 — 익숙한 노래 뒤에는 어떤 이야기가 있을까](../../content/stories/culture/music/carmen-love-freedom-and-stage.json) | 게시 중 | 프랑스 / 문화 | 프랑스 오페라로 배치. 스페인 배경이라는 이유만으로 스페인 작품으로 분류하지 않음. |
| [쇼팽의 생애 — 떠나온 나라가 피아노에 남을 때](../../content/stories/culture/music/chopin-life-piano-and-home.json) | 게시 중 | 폴란드 / 문화 | 폴란드와 고향의 기억을 대표 위치로 삼되 프랑스에서의 주요 활동을 보존. |
| [『돈 조반니』 — 저녁 식사에 석상을 초대한 남자](../../content/stories/culture/music/don-giovanni-statue-dinner-and-refusal.json) | 미게시 · verified | 오스트리아 / 문화 | 모차르트의 오스트리아 음악 맥락으로 배치. 프라하 초연과 스페인 배경을 별도 정보로 보존. |
| [『라 트라비아타』 — 축배가 끝난 뒤 비올레타에게 남은 것](../../content/stories/culture/music/la-traviata-violetta-party-and-silence.json) | 게시 중 | 이탈리아 / 문화 | 이탈리아 오페라로 배치. 프랑스 원작·배경은 설명에 유지. |
| [『피가로의 결혼』 — 결혼식 날 가장 바쁜 것은 누구일까](../../content/stories/culture/music/marriage-figaro-countess-susanna-garden.json) | 미게시 · verified | 오스트리아 / 문화 | 오스트리아 음악 맥락으로 배치. 프랑스 원작과 스페인 배경도 본문에서 유지. |
| [옛 녹음 사진에서 그는 노래를 듣고 있었다](../../content/stories/culture/music/mountain-chief-recorded-song.json) | 게시 중 | 미국 / 문화 | 미국에서 기록된 특정 인물·공동체의 자료 중심. 블랙풋 공동체의 미국·캐나다에 걸친 역사를 국경 하나로 단순화하지 않음. |
| [터키 행진곡 — 피아노에서 군악대가 들리는 이유](../../content/stories/culture/music/mozart-turkish-rondo.json) | 게시 중 | 오스트리아 / 문화 | 오스트리아 음악으로 배치. 제목의 튀르키예와 당시 유럽의 터키풍 음악 표현을 구분. |
| [버지니아 회사 — 신대륙의 꿈을 주식으로 팔다](../../content/stories/finance/investment/virginia-company-shares-and-colony.json) | 게시 중 | 돈과 금융 / 투자와 시장 | 식민지의 역사적 피해와 배경을 보존하되 주식·자금 조달이 글의 중심이므로 kr 우선. |
| [흑사병 뒤의 임금 — 일할 사람이 줄자 무엇이 달라졌을까](../../content/stories/finance/money/black-death-labor-and-wages.json) | 게시 중 | 생각과 지식 / 사회와 제도의 탄생 | 전염병 뒤 노동·임금·제도가 바뀌는 과정을 중심으로 kr 배치. 유럽 역사 페이지에서 연결 가능. |
| [존 로 — 종이돈과 미시시피의 꿈은 어떻게 엮였을까](../../content/stories/finance/money/john-law-paper-money-and-mississippi.json) | 게시 중 | 돈과 금융 / 돈과 화폐 | 프랑스의 사례를 사용하지만 화폐·신용과 기대의 작동이 중심이므로 kr 우선. |
| [쿠빌라이의 지폐 — 나무껍질이 돈이 되던 제국](../../content/stories/finance/money/kublai-paper-money-and-seal.json) | 게시 중 | 중국 / 역사 | 중국의 원대 화폐라는 역사 맥락으로 배치. 제국과 군주의 문화적 정체성을 현대 국적 하나로 환원하지 않음. |
| [만사 무사 — 순례길의 금은 왜 카이로에 흔적을 남겼을까](../../content/stories/finance/money/mansa-musa-gold-and-cairo.json) | 게시 중 | 말리 / 역사 | 말리 통치자와 순례를 중심으로 배치하되 이집트 카이로에서의 사건을 함께 설명. |
| [타가자 — 사막에서 소금은 왜 먼 길을 떠났을까](../../content/stories/history/africa/taghaza-salt-caravan-and-labor.json) | 게시 중 | 말리 / 역사 | 현재 말리의 타가자를 탐색 기준으로 사용. 사하라 교역과 노동은 여러 지역을 잇는 역사임을 명시. |
| [바퀴 없이 짐을 옮기던 긴 두 개의 막대](../../content/stories/history/america/canada-dog-travois.json) | 게시 중 | 캐나다 / 생활 | 캐나다의 자료와 원주민 운송 문화 맥락. 캐나다 전체의 단일 전통으로 일반화하지 않음. |
| [캐나다 철도 — 나라를 잇던 선로 위에는 누가 있었을까](../../content/stories/history/america/canadian-pacific-railway-workers-and-belonging.json) | 게시 중 | 캐나다 / 역사 | 캐나다의 철도 건설·이주노동·소속의 역사 중심. 기업 운영 원리만을 다룬 글과 구분. |
| [벤저민 프랭클린 — 인쇄공은 왜 함께 읽을 책을 모았을까](../../content/stories/history/america/franklin-printer-club-and-library.json) | 게시 중 | 미국 / 역사 | 필라델피아 시민의 결사·도서관이라는 구체적 역사 맥락을 우선해 미국에 배치. 일반 교육·도서관 원리를 다룬 글과 구분. |
| [키푸 — 잉카는 매듭으로 무엇을 기록했을까](../../content/stories/history/america/inca-quipu-knots-and-records.json) | 게시 중 | 페루 / 역사 | 페루를 대표 탐색 위치로 하되 잉카의 범위는 현대 여러 국가에 걸침을 유지. |
| [미라가 이사하려면 누구에게 물어봐야 할까](../../content/stories/history/america/mummy-museum-move.json) | 게시 중 | 생각과 지식 / 사회와 제도의 탄생 | 특정 국가의 고대사보다 박물관의 이송·관리라는 제도적 질문이 중심이므로 kr에 배치. |
| [공장의 시계 — 하루의 길이는 누가 정했을까](../../content/stories/history/europe/factory-clock-workday-and-human-time.json) | 게시 중 | 생각과 지식 / 사회와 제도의 탄생 | 공장의 특정 국가보다 노동시간과 생활 제도의 변화가 중심이므로 kr 배치. |
| [나이팅게일 — 등불보다 먼저 병실의 공기를 보다](../../content/stories/history/europe/nightingale-air-and-observation.json) | 게시 중 | 과학과 발견 / 과학자의 발견 | 영국 인물의 국적보다 관찰과 간호 환경 개선이라는 지식의 발전을 중심으로 kr 배치. |
| [시계에도 작은 문이 달린 집이 있었다](../../content/stories/history/korea/clock-little-door-case.json) | 게시 중 | 생활을 바꾼 물건과 기술 / 집과 생활 도구 | 제작국 근거가 부족하므로 한국 소장품이라는 이유만으로 한국 역사로 분류하지 않음. 보관 도구의 구조 중심으로 kr 배치. |
| [페르시아의 전령 — 빠른 말 뒤에는 어떤 준비가 있었을까](../../content/stories/history/middle-east/persian-couriers-and-relay-stations.json) | 게시 중 | 이란 / 역사 | 이란을 대표 탐색 위치로 하되 아케메네스 제국을 현대 이란 영토와 동일시하지 않음. |
| [피부 위의 무늬는 씻어 낸 뒤에도 남는다](../../content/stories/life/clothing/henna-paste-and-stain.json) | 게시 중 | 생활 | 한 국가의 전통으로 단정할 근거가 부족하여 지역에 걸친 이야기로 임시 배치. 남아시아에도 널리 이어지는 문화이므로 지역 한정의 소유 주장으로 읽히지 않게 안내. |
| [아난시 — 지혜를 항아리에 숨기려던 날](../../content/stories/life/folks/anansi-wisdom-pot-and-son.json) | 게시 중 | 문화 | 아칸권과 가나 등의 전승 및 디아스포라 확산을 고려하여 지역에 걸친 이야기로 배치. 특정 수집본의 출처를 전체 전승의 유일한 기원으로 확대하지 않음. |
| [마우이는 왜 태양에 밧줄을 걸었을까](../../content/stories/life/folks/maui-snaring-sun-kapa-days.json) | 게시 중 | 미국 / 문화 | 현재 미국 하와이를 기본 탐색 위치로 제안. 폴리네시아·태평양 문화 맥락이 중요하므로 아시아대양주 연결도 검토. 미국 전체의 신화로 일반화하지 않음. |
| [피그말리온 — 조각이 따뜻해진 순간](../../content/stories/life/folks/pygmalion-ivory-statue-and-living-person.json) | 미게시 · verified | 키프로스 / 문화 | 키프로스를 신화 속 배경에 따른 탐색 위치로 제안. 그리스·로마 전승과 오비디우스의 서술을 현대 국가의 소유로 해석하지 않음. |
| [까마귀 소년 — 빛을 조각내어 낮과 밤을 만들다](../../content/stories/life/folks/raven-boy-light-fragments-and-night.json) | 게시 중 | 미국 / 문화 | 현재 미국 알래스카의 특정 수집 전승을 기준으로 배치. 다른 원주민 공동체의 까마귀 신화와 합쳐 설명하지 않음. |
| [사비트리 — 죽음의 신을 따라 걸으며 나눈 말](../../content/stories/life/folks/savitri-words-along-yamas-road.json) | 게시 중 | 인도 / 문화 | 인도 전승을 바탕으로 한 재서술의 맥락. 본문이 사용하는 판본과 고전 전승 전체를 구분. |
| [토르 — 망치를 찾으러 신부가 된 날](../../content/stories/life/folks/thor-thrym-bridal-veil-and-hammer.json) | 게시 중 | 문화 | 북유럽 공유 전승으로 지역에 걸친 이야기에 배치. 아이슬란드 문헌 기록과 전승의 범위를 구분. |
| [접시 바닥에서 복 한 글자를 만나다](../../content/stories/life/food/blue-dish-hidden-fortune.json) | 게시 중 | 생각과 지식 / 예술을 보는 법 | 소장 기관만으로 제작국을 단정하지 않음. 복자와 무늬를 읽는 감상 중심으로 kr에 배치. |
| [팝콘 한 알은 어떻게 저렇게 커질까](../../content/stories/life/food/popcorn-little-explosion.json) | 게시 중 | 생활을 바꾼 물건과 기술 / 식탁과 식품 보존 | 특정 지역의 음식 풍습보다 곡물이 터지는 조리 과정이 중심이므로 kr 배치. |
| [옥수수와 콩, 호박은 왜 세 자매일까](../../content/stories/life/food/three-sisters-garden.json) | 게시 중 | 미국 / 생활 | 미국 지역의 자료를 탐색 위치로 제안. 하우데노사우니 등 공동체와 캐나다를 포함한 문화권을 별도로 설명. |
| [이 집은 다음 목초지까지 함께 간다](../../content/stories/life/housing/jordan-moving-tent.json) | 게시 중 | 요르단 / 생활 | 요르단의 특정 자료 중심. 베두인 문화를 요르단 한 국가로 한정하지 않음. |
| [한 지붕 아래 사람과 가축의 자리가 있었다](../../content/stories/life/housing/kabyle-house-shared-roof.json) | 게시 중 | 알제리 / 생활 | 알제리 카빌 지역의 특정 시기 주거 연구 중심. 현재 모든 가정의 모습으로 일반화하지 않음. |

## 이후 실제 이전 순서

1. 이 배치안을 기준으로 국가·주제 목록 화면을 미리 만듭니다. 기존 원고 본문과 이미지는 유지합니다.
2. kr 도메인의 현재 연결·기존 사이트·호스팅 상태를 먼저 확인합니다. 별도 저장소는 수정하지 않습니다. 현재 저장소 안에서 두 사이트를 관리하는 방식을 준비합니다.
3. 두 사이트의 미리보기에서 메뉴·이미지·번호 소제목·옆 바로가기·모바일 표시를 확인합니다. 미게시 원고는 공개 대상에 넣지 않습니다.
4. 전환안을 확인한 후 실제 도메인 연결과 게시를 진행합니다. 이 문서는 전환 실행 승인이 아닙니다.
5. 기존 공개 주소 `/stories/{id}/index.html`을 보존합니다. net에 남는 글은 그대로 두고, kr로 옮기는 글은 기존 net 주소에서 새 주소로 안내되도록 준비합니다. 국가명은 글 주소에 넣지 않아 분류 수정 때 주소가 바뀌지 않게 합니다.
6. GitHub Pages는 임의의 HTTP 301 규칙을 직접 제공하지 않습니다. 정적 안내 페이지의 자동 이동·일반 링크와 새 주소의 대표 주소 표시를 검토하거나, 실제 호스팅이 지원하는 서버 이동 규칙을 사용합니다. 검색 등록·사이트맵도 함께 조정하고 같은 본문을 두 도메인에서 계속 중복 공개하지 않습니다.

광고·외국어 앱·여행 사이트 연결은 이번 분류 작업에 포함하지 않았습니다. 자동 글 생성도 활성화하지 않았습니다. `config/proposals/`의 데이터는 실행 중인 생성기·사이트 설정을 대체하지 않습니다.
