# 프론트 MVP mock/fixture 감사

> 2026-06-22 보강: 프론트/기획 우선 정리와 단지 반응 품질 기준은 [FRONT_PLANNING_FIRST_URGENT_TASKS.md](./FRONT_PLANNING_FIRST_URGENT_TASKS.md)를 우선 참조한다.

작성일: 2026-06-15

이 문서는 "사용자가 보는 프론트 기준 MVP"에서 mock/fixture처럼 보이는 영역을 제거하기 위한 현재 감사표입니다. 완료 기준은 실제 API, EvidenceLog, content item, reaction snapshot, market fact가 있으면 우선 표시하고, 없으면 mock 값으로 채우지 않고 `수집 전`, `insufficient`, `stale`, `unknown`, `오류` 상태를 표시하는 것입니다.

## 이번에 보정한 영역

| 화면 | 영역 | 변경 |
| --- | --- | --- |
| `/dashboard` | Today 3줄 브리핑, 지역 흐름 카드, 핵심 콘텐츠 피드 | region reaction ranking을 전면 노출하지 않고 지도 흐름, 뉴스룸, 공식 지표, 근거 브리핑 중심으로 표시 |
| `/dashboard` | headline, 라이징 스타 drawer | 기존 보조 drawer와 과열 지표는 제거하고, 오른쪽 패널은 핵심 지역 흐름 카드 하나로 축소 |
| `/dashboard` | 핵심 지역별 상승률 chart | `dashboard-summary.json` 지역 series 대신 `GET /api/realestate/map/layers?layerType=sido` period snapshot을 랭킹형 차트로 표시 |
| `/dashboard` | 주요 지표 카드와 drawer 지표 | market summary API가 비거나 실패하면 fixture 지표를 섞지 않고 빈 상태/오류 상태 표시 |
| `/dashboard` | 뉴스, 리포트, 영상, 블로그/커뮤니티 카드 | `dashboard-summary.json` fixture feed 대신 `GET /api/realestate/newsroom?feed=all&page=1&pageSize=40` 우선 표시 |
| `/dashboard` | TOP 반응 지역 AI 근거 리포트 | region ranking 상위 target의 `GET /api/realestate/targets/{targetId}/evidence-logs?limit=1` 응답을 표시하고, 없으면 `AI 근거 수집 전/insufficient` 표시 |
| 공통 shell | 상단 mock badge, 고정 속보, 오른쪽 rail mock 관심 목록 | mock/관심 목록처럼 보이는 보조 UI를 제거하고 핵심 이동 route만 유지 |
| `/newsroom` | 종합/개별 feed 목록 | API 빈 응답 또는 실패 때 mock feed를 넣지 않고 빈 상태와 오류 상태 표시 |
| `/realestate/mypage` (`/realestate/watchlist` redirect) | 저장 지역/단지, 방문 후 변화, 알림 조건, 개인 메모, 저장 지역 비교 | 로그인/사용자 저장 API 전에는 실제 저장 목록처럼 보이는 mock watchlist를 두지 않고 준비 상태 표시 |
| `/realestate/transactions` (`/realestate/reactions` redirect) | 실거래 탐색 shell | 팀원 구현 전까지 빈 shell만 유지하고, 지역 반응 route는 실거래 route로 redirect |
| `/realestate/map/:regionId` | 오른쪽 지역 보고서 | 시도 상세 route 진입 즉시 해당 시도 target의 최신 EvidenceLog를 표시하고, 하위 지역을 클릭하면 선택한 하위 지역 targetId의 EvidenceLog로 교체 |
| `/indicators` | 지표 fallback 문구 | API가 비면 정적 수치를 실제값처럼 섞지 않고 `수집 전/insufficient`, `unknown`으로 표시 |
| `/realestate/targets/:targetId` | 상세 좌표/리포트 상태 | `mock 좌표`, `fixture fallback` 노출 문구를 `좌표 검증 전`, `timeline 수집 전`, `EvidenceLog API 반영` 기준으로 보정 |

## 아직 남은 mock/fixture 노출 위험

| 화면 | 남은 영역 | 현재 상태 | 다음 조치 |
| --- | --- | --- | --- |
| `/dashboard` | 확인 필요 copy, 시장 fact coverage 부족 | fixture 수치 노출은 제거했지만 운영 체크리스트와 공공데이터 coverage 부족이 남음 | 확인 필요 copy를 배치 상태/품질 지표 API로 승격 |
| `/newsroom` | fallback fixture 배열 | 화면에는 노출하지 않지만 파일 내부에 남아 있음 | 다음 PR에서 미사용 fixture 생성 코드를 제거 |
| `/realestate/map` | seed/mock map snapshot, 일부 지역 drilldown | API 우선이며 market fact가 없으면 reaction-only partial snapshot으로 대체 가능 | 공공데이터/반응 snapshot refresh coverage 확대, fallback 표시를 `수집 전/insufficient`로 유지 |
| `/realestate/map/:regionId` | 지역별 오른쪽 보고서 | 최근 7일 TOP target은 EvidenceLog가 있고, TOP10 밖 하위 지역은 없을 수 있음 | 지도 클릭 target에 EvidenceLog가 없으면 일일 배치 대상에 포함하거나 빈 리포트 상태 표시 |
| `/realestate/transactions` | 실거래 탐색 본문 | 팀원 구현 전 empty shell | 실거래/전세 필터, 거래 row, provider/asOf 계약 연결 |
| `/realestate/targets/:targetId` | 마포/동탄/단지 일부 상세 fixture, 후보 좌표 | EvidenceLog API는 우선 조회하지만 market/timeline/좌표 provider 검증이 남음 | target detail summary API와 검증 좌표 provider 연결 |
| `/indicators` | 상세 route의 선형 trend chart | 허브의 지역 방향/괴리 표는 map layer와 reaction ranking API로 전환했고, 상세 SVG chart는 아직 관찰 shell | 상세 chart series를 실제 market fact/reaction window series로 연결 |
| `/realestate/mypage` | 실제 사용자 저장 mypage | mock 목록은 제거했고 현재는 로그인 연동 준비 상태와 빈 저장 보드 | 로그인/사용자 watch API가 열리면 저장 지역/알림/메모를 실제 계정 상태로 연결 |

## 크롤링/SerpApi/AI 운영 기준

- `realestate-daily-refresh`는 `market_facts -> community_crawl -> reaction_snapshots -> recent_issues -> evidence_logs -> map_layers` 순서로 한 번 실행할 수 있습니다.
- 현재 공개 source 전체 운영 크롤링이 아니라 P0 공개 source 중심 smoke/시연 경로입니다.
- MOLIT 공공데이터 API가 timeout/502를 반환하면 raw-push는 전체를 중단하지 않고 해당 run을 `provider_error`로 저장합니다. 이 상태에서는 dashboard/indicators/map이 `수집 전`, `insufficient`, `partial`로 보여야 합니다.
- SerpApi 결과는 관심도 점수가 아니라 EvidenceLog 근거 후보 content item으로만 저장합니다.
- GMS AI는 EvidenceLog의 `summary`, `subtitle`, `tone` 보강에 사용하고, 매수/매도/청약/대출 권유 문구는 guardrail로 폐기합니다.

## 다음 PR 우선순위

1. 지역별 market fact coverage를 넓힙니다. 전국 R-ONE 공식 지표는 연결됐지만, 지도/상세 리포트가 지역별 가격·전세·거래 fact를 직접 쓰려면 시도/시군구 단위 provider 매핑과 백필이 더 필요합니다.
2. `/indicators` 상세 chart series를 실제 market fact/reaction window series로 연결합니다.
3. 뉴스룸 파일 내부의 미사용 fallback fixture 생성 코드를 제거합니다.
4. 지도/지역 상세의 seed/mock coverage를 실제 공공데이터/반응 snapshot refresh로 확대합니다.

## 2026-06-15 MVP live 연결 재확인

- 로컬 daily refresh 기준 공개 source 2곳에서 community crawl을 실행했고, 24시간 reaction snapshot 15개 지역을 생성/조회했습니다.
- SerpApi 최근 이슈 후보는 reaction ranking 15개 지역까지 확장해 190건을 content candidate로 저장했습니다.
- GMS `gpt-5-mini` EvidenceLog는 15개 지역에 대해 생성됐습니다. `market_fact_missing`, `similar_window_missing`, `low_sample`, `stale` caveat은 숨기지 않습니다.
- `/dashboard`와 `/newsroom`은 content API에 후보가 있는데 리포트/영상/커뮤니티 유형이 비어 보이는 경우, mock feed를 섞지 않고 "이번 갱신에서는 해당 유형이 아직 분리되지 않았습니다"로 표시합니다.
- `/realestate/targets/:targetId`는 반응 snapshot이 있는 지도 지역이면 EvidenceLog API를 우선 표시합니다. 반응이 없는 seed/mock 지역은 근거 없는 AI 보고서를 만들지 않고 근거 로그 대기 상태로 둡니다.
- `/realestate/map`의 시도 heatmap은 실제 market fact가 부족한 구간에서 `real_estate_reaction_snapshots` 기반 partial snapshot을 쓸 수 있습니다. 이때 stale 여부는 reaction snapshot의 stale 값을 그대로 따릅니다.

## 2026-06-15 MVP mock-like UI 추가 제거

- `/newsroom`의 미사용 dashboard fixture 기반 fallback feed 생성 코드를 제거했습니다. content API가 비거나 실패하면 더 이상 예전 기사/리포트/영상 행을 채우지 않고 `수집 전/insufficient` 또는 오류 상태만 표시합니다.
- `/realestate/reactions`의 지역/단지 TOP10, 급증 신호, AI 로그 fallback 배열을 제거했습니다. reaction API 실패 또는 빈 응답에서는 정적 TOP10을 보여주지 않고 수집 전/오류 상태를 표시합니다.
- `/realestate/map/:regionId`의 하위 지역 리포트에서 시군구 period snapshot이 없을 때 변화율, 표본 수, 언급량, 출처 비율, 단지 후보를 임의 생성하지 않도록 했습니다. 하위 layer가 없으면 회색/수집 전 상태와 EvidenceLog 대기 상태로 남깁니다.
- `/realestate/targets/:targetId`는 로컬 상세 fixture의 headline, metric, reaction, timeline, evidence, marker를 화면 fallback으로 쓰지 않고 EvidenceLog/content/timeline/nearby-complex API가 있을 때만 표시합니다. 없으면 각각 `수집 전/insufficient` 상태를 노출합니다.

## 2026-06-16 MVP report wiring 보강

- 한국부동산원 R-ONE 전국 주요 지표 3건을 `legalDongCode=00000` market fact로 적재했고, `/dashboard`와 `/indicators`는 이 값을 공식 지표로 우선 표시합니다.
- 최신 24시간 reaction TOP10 target은 SerpApi 후보와 GMS `gpt-5-mini` EvidenceLog가 모두 생성되어 있습니다. 지역별 market fact가 없는 target은 전국 공식 지표를 배경 근거로 붙이고, 사용자 화면에는 `전국 지표만 반영` 주의 사항으로 표시합니다.
- `/dashboard`, `/realestate/reactions`, `/realestate/targets/:targetId`, `/realestate/map/:regionId`는 최신 EvidenceLog 1건만 조회합니다. 예전 로그의 raw caveat code가 화면에 같이 섞이지 않도록 했습니다.
- `/realestate/map/:regionId`는 시도 상세 지도 진입 시점부터 부모 시도 리포트를 열고, 하위 시군구 클릭 시 같은 패널을 하위 지역 리포트로 교체합니다.
- 브라우저 확인 기준 `/dashboard`, `/newsroom`, `/realestate/map/gyeonggi`, `/realestate/reactions`, `/realestate/targets/region-seoul`, `/indicators`에서 `mock`, `fixture`, `fallback`, `demo`, `front_fixture`, `market_fact_missing`, `national_market_fact_only`, `similar_window_missing` raw 문구는 노출되지 않았습니다.
- `/indicators`의 `지역별 지표 방향`은 `/api/realestate/map/layers?layerType=sido`, `지표와 반응이 엇갈린 지역`은 `/api/realestate/reactions/rankings`를 함께 사용합니다. 정적 마포/동탄/송도/분당 행은 화면에서 제거했고, API가 비면 수집 전/insufficient 상태만 표시합니다.

## 2026-06-16 MVP 화면 체감 보정

- 전국 지도 시도 버튼은 실제 `<a href="/realestate/map/{targetId}">` 링크와 router push를 함께 사용합니다. 라우트 변경 watcher가 리포트 닫기 로직을 타며 전국 지도로 되돌아가던 문제를 분리해, 대전 버튼 클릭이 `/realestate/map/region-daejeon`으로 정상 이동하는 것을 브라우저에서 확인했습니다.
- `/dashboard`, `/newsroom`, `/realestate/map`, `/realestate/map/region-daejeon`, `/realestate/transactions`, `/indicators`, `/realestate/mypage`, `/realestate/targets/region-seoul-mapo` 기준으로 `mock`, `fixture`, `stale`, `unknown`, `EvidenceLog`, `SerpApi`, `GMS`, `API`, `snapshot`, `front-only` 같은 mock-like/internal 용어가 사용자 화면에 노출되지 않는 것을 브라우저 스캔으로 확인했습니다.
- 화면에는 내부 테이블명이나 provider code 대신 `반응 데이터 반영`, `AI 근거 반영`, `지도 흐름 자료`, `한국부동산원`, `근거 링크 반영`, `지도 좌표 반영` 같은 사용자용 상태 라벨을 표시합니다.
- GMS 보강이 timeout될 때 EvidenceLog daily step 전체가 실패하던 문제를 개별 로그 fallback으로 보정했습니다. 이후 TOP10 지역 EvidenceLog를 90초 timeout으로 재실행했고, 최신 TOP10 모두 `gpt-5-mini` 기반 요약이 API에서 조회됩니다.
- 공개 source 크롤링은 local runtime smoke 기준 source 2곳만 확인했습니다. 현재 정본 화면은 크롤링/지역 반응 페이지가 아니라 실거래 탐색, 지역 분석, 주요 일정, 마이페이지 중심이므로, 반응 ranking은 보조 근거로만 표현합니다.
- 2026-06-16 completion audit에서 라우터 기준 active route 샘플 22개(`/`, dashboard, newsroom filter, map drilldown, reactions tab, indicators detail, watchlist, region/complex/living-area target detail)를 브라우저로 순회했습니다. 사용자 화면 텍스트에서 `mock`, `fixture`, `front_fixture`, `fallback`, `EvidenceLog`, `SerpApi`, `GMS`, `API`, `snapshot`, `provider`, `asOf`, raw caveat code, stock-era 용어가 모두 0건임을 확인했습니다.
- GMS 요약 본문 안에 raw caveat code나 `EvidenceLog`/`snapshot`이 섞여 내려와도 대시보드, 지도 리포트, 상세 리포트는 사용자용 한국어 표현으로 치환합니다. 상세 리포트 테스트에도 raw code가 화면에 노출되지 않는 회귀 검사를 추가했습니다.
