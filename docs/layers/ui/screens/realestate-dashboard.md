# 부동산 대시보드

## Route

- Parent: root app
- Route 후보: `/dashboard`, `/realestate`
- Child screens: `realestate-target-detail`

## 화면 목적

사용자가 지금 어느 지역과 단지가 많이 언급되는지, 그 반응이 기대인지 우려인지, 어떤 쟁점과 시장 사실이 함께 움직이는지 빠르게 확인합니다.

## 현재 섹션

- 상단 검색: 지역, 단지, 법정동, 키워드 검색
- 부동산 투기 과열 지표 gauge
- 핵심 지역별 상승률 chart
- 요즘 언급 많은 지역/단지 ranking
- 기대/우려 split meter와 쟁점 비율
- 실시간 이슈, 뉴스, 컬럼 링크
- 실거래/전세/매물/정책 데이터 상태 badge
- 표본 신뢰도, source skew, 수집 지연 rail
- 에이전트 근거 로그 최신 항목

## 주요 지표 방향

기존 금융 화면의 지수/등락률 패턴을 그대로 가져오면 부동산에서는 의미가 흐려질 수 있습니다. 부동산은 거래 빈도가 낮고 신고·공개 지연이 있으며, 지역·단지·면적·연식에 따라 같은 기간의 가격 신호가 다르게 보입니다. 따라서 첫 화면의 주요 지표는 "투자 점수"보다 "관찰 지표 묶음"으로 둡니다.

- 가격 흐름: 실거래가, 전세가, 공표 지수의 방향과 `asOf`, 표본 수, stale 여부를 함께 표시
- 거래 강도: 거래 건수, 신고 건수, 매물 소진 체감, 거래량 부족 caveat 표시
- 전세 압력: 전세가 변화, 전월세 비중, 전세 매물 감소/증가 반응
- 공급/청약: 입주 예정, 분양/청약 일정, 경쟁률, 미분양 후보 데이터
- 정책/교통 이벤트: 대출, 세제, 정비사업, 철도/도로 발표를 원인 확정이 아닌 context로 표시
- 커뮤니티 반응: 기대/우려/중립, 언급량, 별칭 확산, source skew를 가격 사실과 분리 표시
- 핵심 지역 상승률: 커뮤니티별 비교가 아니라 마포구, 성수동, 동탄역권, 송도처럼 사용자가 보는 지역 단위의 주/월/6개월/년 변화율로 표시

카드 라벨은 `상승률`, `강세` 같은 결론형 표현보다 `실거래 공개`, `전세 압력`, `거래 강도`, `정책 이벤트`, `커뮤니티 반응`처럼 사용자가 직접 판단할 수 있는 이름을 우선합니다.

## 상태와 빈 화면

- loading: ranking skeleton, timeline skeleton, stale badge placeholder
- empty: 수집된 지역/단지 mention 없음, source 상태와 mock 여부 표시
- error: 수집/API 실패 영역별 표시
- stale/mock: provider, `asOf`, `stale`, `mock` badge를 카드마다 표시

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `targets[]` | realestate/indicator | 언급 많은 지역/단지 목록 |
| `targets[].reactionSnapshot` | indicator | 기대/우려/중립, mention count, confidence |
| `targets[].issueMix` | indicator | 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책 비율 |
| `targets[].marketFacts` | realestate | 실거래/전세/매물/정책 fact와 provider/asOf/stale |
| `issueFeed[]` | community/realestate | 뉴스/컬럼/커뮤니티 링크 |
| `evidenceLogs[]` | agent | 최신 평가와 근거 요약 |

현재 구현:

- `GET /api/realestate/market-facts` 응답을 `실거래·지표 상태` 패널에 우선 표시합니다.
- `GET /api/realestate/dashboard/market-summary` 응답을 `주요 부동산 지표` 카드와 지표 drawer에 우선 표시합니다. API가 비거나 실패하면 fixture 지표를 섞지 않고 `수집 전/insufficient` 또는 오류 상태를 표시합니다.
- `GET /api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10` 응답을 부동산 투기 과열 지표, headline, 상단 반응 캐러셀, 언급 합계, 관심 drawer, 라이징 스타 drawer에 우선 표시합니다. API가 비거나 실패하면 fixture를 섞지 않고 `수집 전/insufficient` 또는 오류 상태를 표시합니다.
- `GET /api/realestate/map/layers?layerType=sido` 응답을 `핵심 지역별 상승률` 랭킹형 차트에 우선 표시합니다. 주/월/6개월은 snapshot period를 사용하고, 연간 snapshot이 없으면 `연간 수집 전`으로 둡니다.
- `GET /api/realestate/newsroom?feed=all&page=1&pageSize=40` 응답을 대시보드 뉴스/리포트/영상/커뮤니티 링크 카드에 우선 표시합니다. API가 비거나 실패하면 mock feed 대신 수집 전/오류 상태를 표시합니다.
- API가 비어 있거나 실패하면 `수집 대기`, `데이터 없음`, `공공데이터 대기` 상태로 표시하고, fixture 값을 실제 데이터처럼 보이게 대체하지 않습니다.
- 주요 지표 카드의 `changePct`가 없으면 `0%`로 보정하지 않고 `최신`으로 표시합니다.
- row와 카드에는 `provider`, `observedAt`, `asOf`, `stale/dataStatus`를 함께 노출합니다.

## 기획자 확인 필요

- 첫 화면 route를 `/dashboard`로 유지할지 `/realestate`로 둘지
- target 식별자를 region과 complex로 분리 노출할지 통합 target으로 노출할지
- 반응 지표를 점수형으로 보여줄지 split meter 중심으로 보여줄지
- 대표 색상 규칙: 기존 너나사 UI 패턴은 유지하되 부동산 서비스의 포인트 색은 주황 계열로 두고, 지도 상승/하락 색은 국내 사용자 관습에 맞춰 `빨강=상승`, `파랑=하락`을 기본값으로 둘지 확정 필요
- 지도형 탐색은 `/realestate/map`에서 먼저 시도 단위로 제공하고, 상세 단지 레이어는 좌표/별칭 DB가 준비된 뒤 후속 화면으로 확장

## 변경 로그

- 2026-06-01: 지도 route와 시도 단위 우선 구현 방침 추가
- 2026-06-01: 대시보드 좌상단 gauge를 부동산 투기 과열 지표로 전환하고, chart를 핵심 지역별 상승률 기준으로 변경
- 2026-06-01: 주요 지표를 점수형보다 관찰 지표 묶음으로 재정의
- 2026-06-01: 부동산 전용 대시보드 Screen Brief 생성
- 2026-06-11: `실거래·지표 상태` 패널을 `GET /api/realestate/market-facts` 우선 표시로 연결
- 2026-06-11: `주요 부동산 지표` 카드를 `GET /api/realestate/dashboard/market-summary` 우선 표시로 연결
- 2026-06-15: 대시보드 반응 캐러셀과 뉴스/리포트/영상/링크 카드를 API 우선으로 전환하고, 빈 응답은 mock feed 대신 수집 전 상태로 표시
- 2026-06-15: 투기 과열 지표와 headline을 지역 reaction ranking 기반으로 계산하고, 핵심 지역별 상승률 chart를 map layer snapshot 기반 랭킹으로 전환
