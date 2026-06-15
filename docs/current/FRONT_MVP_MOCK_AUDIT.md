# 프론트 MVP mock/fixture 감사

작성일: 2026-06-15

이 문서는 "사용자가 보는 프론트 기준 MVP"에서 mock/fixture처럼 보이는 영역을 제거하기 위한 현재 감사표입니다. 완료 기준은 실제 API, EvidenceLog, content item, reaction snapshot, market fact가 있으면 우선 표시하고, 없으면 mock 값으로 채우지 않고 `수집 전`, `insufficient`, `stale`, `unknown`, `오류` 상태를 표시하는 것입니다.

## 이번에 보정한 영역

| 화면 | 영역 | 변경 |
| --- | --- | --- |
| `/dashboard` | 상단 지역 반응 캐러셀, 언급 합계, 관심 drawer | `reaction-ranking.json` 대신 `GET /api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10` 우선 표시 |
| `/dashboard` | 부동산 투기 과열 지표, headline, 라이징 스타 drawer | `dashboard-summary.json` fixture 대신 region reaction ranking 응답에서 파생하고, 비어 있으면 `수집 전/insufficient` 표시 |
| `/dashboard` | 핵심 지역별 상승률 chart | `dashboard-summary.json` 지역 series 대신 `GET /api/realestate/map/layers?layerType=sido` period snapshot을 랭킹형 차트로 표시 |
| `/dashboard` | 주요 지표 카드와 drawer 지표 | market summary API가 비거나 실패하면 fixture 지표를 섞지 않고 빈 상태/오류 상태 표시 |
| `/dashboard` | 뉴스, 리포트, 영상, 블로그/커뮤니티 카드 | `dashboard-summary.json` fixture feed 대신 `GET /api/realestate/newsroom?feed=all&page=1&pageSize=40` 우선 표시 |
| 공통 shell | 상단 mock badge, 고정 속보, 오른쪽 rail mock 관심 목록 | `GET /api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=6` 기반으로 전환하고 비면 `수집 전/insufficient` 표시 |
| `/newsroom` | 종합/개별 feed 목록 | API 빈 응답 또는 실패 때 mock feed를 넣지 않고 빈 상태와 오류 상태 표시 |
| `/realestate/watchlist` | 관심 지역 목록, 요약, 원문 후보, 알림 판단 | 저장 기능 전 mock watchlist 대신 `GET /api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10` 기반 관심 후보와 `수집 전/insufficient` 표시 |

## 아직 남은 mock/fixture 노출 위험

| 화면 | 남은 영역 | 현재 상태 | 다음 조치 |
| --- | --- | --- | --- |
| `/dashboard` | 확인 필요 copy, 시장 fact coverage 부족 | fixture 수치 노출은 제거했지만 운영 체크리스트와 공공데이터 coverage 부족이 남음 | 확인 필요 copy를 배치 상태/품질 지표 API로 승격 |
| `/newsroom` | fallback fixture 배열 | 화면에는 노출하지 않지만 파일 내부에 남아 있음 | 다음 PR에서 미사용 fixture 생성 코드를 제거 |
| `/realestate/map` | seed/mock map snapshot, 일부 지역 drilldown | API 우선이지만 coverage 부족 시 seed/mock fallback | 실제 공공데이터/반응 snapshot refresh coverage 확대, fallback 표시 유지 |
| `/realestate/map/:regionId` | 지역별 오른쪽 보고서 | 모든 지역에 EvidenceLog가 있는 상태는 아님 | 지도 클릭 target에 EvidenceLog가 없으면 일일 배치 대상에 포함하거나 빈 리포트 상태 표시 |
| `/realestate/reactions` | 단지군 TOP10, 보조 console 일부 | 지역 ranking은 API, 단지군은 coverage 부족 시 빈 상태 | alias/source coverage 보강 후 complex snapshot 생성 |
| `/realestate/targets/:targetId` | 마포/동탄/단지 일부 상세 fixture, mock 좌표 | EvidenceLog API는 우선 조회하지만 market/timeline/좌표 fixture가 남음 | target detail summary API와 검증 좌표 provider 연결 |
| `/indicators` | 일부 trend chart와 보조 히트맵 | API 우선 + mock fallback 혼합 | 지표별 API 빈 상태 분리, chart mock 제거 |
| `/realestate/watchlist` | 실제 사용자 저장 watchlist | mock 목록은 제거했고 현재는 reaction ranking 관심 후보 | 로그인/사용자 watch API가 열리면 후보 목록과 저장 목록을 분리 |

## 크롤링/SerpApi/AI 운영 기준

- `realestate-daily-refresh`는 `market_facts -> community_crawl -> reaction_snapshots -> recent_issues -> evidence_logs -> map_layers` 순서로 한 번 실행할 수 있습니다.
- 현재 공개 source 전체 운영 크롤링이 아니라 P0 공개 source 중심 smoke/시연 경로입니다.
- SerpApi 결과는 관심도 점수가 아니라 EvidenceLog 근거 후보 content item으로만 저장합니다.
- GMS AI는 EvidenceLog의 `summary`, `subtitle`, `tone` 보강에 사용하고, 매수/매도/청약/대출 권유 문구는 guardrail로 폐기합니다.

## 다음 PR 우선순위

1. `/realestate/targets/:targetId`에서 fixture market/timeline 값을 EvidenceLog, content, market fact API 빈 상태와 분리합니다.
2. `/indicators`의 visible mock fallback과 chart mock을 수집 전/insufficient 상태로 바꿉니다.
3. 뉴스룸 파일 내부의 미사용 fallback fixture 생성 코드를 제거합니다.
4. 지도/지역 상세의 seed/mock coverage를 실제 공공데이터/반응 snapshot refresh로 확대합니다.
