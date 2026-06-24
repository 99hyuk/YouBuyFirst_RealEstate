# 너나사 부동산 화면 정의서

작성일: 2026-06-04
기준 화면: https://youbuyfirst-realestate.netlify.app/dashboard
기준 ERD: `docs/domains/realestate/ERD.md`, `docs/domains/realestate/ERD.visual-import.sql`

## 1. 서비스 한 줄 정의

실거래, 전세, 매물, 공급, 정책 이슈를 지역 기준으로 엮어 보여주는 AI 부동산 인사이트 탐색 서비스.

이 서비스는 매수, 매도, 청약, 대출 행동을 권유하지 않는다. 실거래/전세/매물/지표, 공급·청약 일정, 정책 이벤트, 뉴스/리포트를 함께 관찰해 "어느 지역의 시장 사실이 어떻게 바뀌고 있는지"를 설명하는 관찰형 분석 서비스다. 공개 커뮤니티 반응은 있으면 보조 근거로만 쓰고, 제품의 중심 화면이나 핵심 지표로 삼지 않는다.

## 2. 공통 화면 원칙

- 공통 내비게이션은 `대시보드`, `뉴스룸`, `지역 분석`, `실거래`, `주요 일정`, `마이페이지`로 유지한다.
- 너나사 시리즈의 UI 패턴은 유지하되, 부동산 서비스의 대표 포인트 컬러는 주황 계열을 쓴다.
- 상승, 기대, 긍정 방향은 빨강 계열로 표시한다.
- 하락, 우려, 냉각 방향은 파랑 계열로 표시한다.
- 모든 데이터 카드에는 가능한 경우 출처, 기준 시각, 갱신 지연, 수집 전, 표본 부족, 부분 반영 상태를 사용자용 라벨로 노출한다. `mock`, `provider`, `asOf`, `EvidenceLog`, `API` 같은 내부 표현을 화면 문구로 그대로 쓰지 않는다.
- 커뮤니티 반응은 핵심 판단이 아니라 보조 관찰 신호로만 표현한다.
- 화면 문구는 `실거래`, `전세`, `매물`, `공급`, `정책`, `시장 사실`, `인사이트`, `근거`, `공개 지연` 중심으로 쓴다.
- 투자 조언처럼 보이는 CTA는 쓰지 않는다. 예: `매수`, `진입`, `청약 추천`, `대출 추천` 금지.

## 3. ERD 기준 데이터 축

### 3.1 부동산 대상 정본

`real_estate_targets`가 모든 화면의 중심 테이블이다. 지역, 생활권, 단지군, 단지를 모두 같은 관찰 대상의 루트로 둔다.

- `real_estate_targets`: 화면에서 클릭하거나 랭킹에 올라오는 대상의 공통 정본. MVP에서는 시군구, 읍면동, 생활권 같은 지역 target을 우선한다.
- `real_estate_regions`: 지역 대상의 식별 하위 테이블, `target_id`가 PK이자 FK
- `real_estate_complexes`: 단지 대상의 식별 하위 테이블, `target_id`가 PK이자 FK
- `real_estate_aliases`: 검색/원문 연결 보조용 별칭, 줄임말, 생활권 명칭
- `real_estate_target_edges`: 생활권, 단지군, 인접 지역, 정책 영향권 같은 대상 간 관계

화면 라우트의 `targetId`는 `real_estate_targets.id`를 그대로 사용합니다. 화면 fixture도 `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`, `complex-mapo-raemian-prugio`처럼 backend target registry와 같은 kebab-case 식별자를 씁니다. 별도 화면용 대문자 ID와 API용 ID를 나누지 않습니다.

### 3.2 지도 데이터

- `map_boundary_assets`: 시도/시군구 지도 원본 asset
- `map_features`: 지도 geometry와 `real_estate_targets` 연결
- `map_layer_snapshots`: 기간별 상승/하락 heat layer 값, 표본 수, 신뢰도, asOf

### 3.3 보조 공개 원문과 반응 분석

- `crawl_sources`: 뉴스, 블로그, 공개 커뮤니티 등 보조 원문 후보 출처
- `source_boards`: 수집처 안의 게시판/섹션
- `community_posts`: 공개 원문 후보, 제목, snippet, URL, 작성 시각, 작성자 hash
- `real_estate_mentions`: 게시글 안에서 인식된 지역/단지 언급
- `reaction_analyses`: 언급 단위의 기대/우려/중립 방향과 쟁점 분류
- `reaction_snapshots`: 기간별 대상 반응 집계
- `reaction_snapshot_issues`: snapshot 안의 쟁점 비율
- `reaction_ranking_snapshots`, `reaction_ranking_rows`: 레거시/보조 화면용 랭킹 스냅샷. 신규 핵심 화면의 정본으로 쓰지 않는다.

### 3.4 뉴스, 리포트, 외부 링크

- `content_items`: 뉴스, 리포트, 영상, 블로그/커뮤니티 링크 카드
- `content_target_links`: 콘텐츠와 지역/단지 대상의 다대다 연결

### 3.5 시장 사실과 주요 일정

- `real_estate_market_facts`: 실거래, 전세, 매물, 청약, 미분양 같은 provider별 fact
- `market_indicator_defs`: 매매가격지수, 전세가격지수, 실거래가 지수, 거래량, 전세가율 등 지표 정의
- `market_indicator_values`: 기간/대상별 지표 값
- `market_data_schedules`: 주요 통계, 실거래 공개, 청약, 정책 발표 일정과 갱신 상태

### 3.6 정책, 타임라인, AI 근거

- `policy_events`: 정책, 교통, 청약, 대출 규제 등 이벤트
- `policy_event_targets`: 정책 이벤트와 대상의 다대다 영향 연결
- `timeline_events`: 대상별 시간대 변화
- `similar_window_matches`: 과거 유사 반응 구간 연결
- `evidence_logs`, `evidence_log_items`: AI 분석 결과와 근거 항목

### 3.7 사용자 관심과 알림

- `app_users`: 사용자 계정
- `user_watch_targets`: 사용자가 저장한 지역/단지, 다대다 연결
- `alert_rules`: 알림 조건
- `alert_events`: 실제 발생한 알림
- `observation_logs`: 사용자의 관찰/복기 로그

## 4. 화면 목록

| 화면 | Route | 화면 목적 | 핵심 데이터 |
| --- | --- | --- | --- |
| 대시보드 | `/dashboard` | 오늘 확인해야 할 지역 시장 흐름과 데이터 상태를 한 화면에서 파악 | 시장 fact, 일정, 뉴스/리포트, 데이터 상태 |
| 지도 | `/realestate/map` | 전국 시도별 흐름을 heat layer로 탐색 | 지도 feature, layer snapshot, 대상 정본 |
| 지역 상세 지도 | `/realestate/map/:regionId` | 시도 내부 시군구 흐름과 리포트 확인 | 지역 hierarchy, 지도 feature, 시장 fact |
| 실거래 | `/realestate/transactions` | 팀원 구현 전까지 빈 shell만 유지하고, 이후 지역·기간·거래 유형 기준의 실거래/전세 탐색을 붙인다 | transaction fact, filters, summary, evidence |
| 주요 일정 | `/indicators`, `/indicators/:category` | 공식 통계·정책·청약·금리 확인 일정 | market data schedules, source links |
| 뉴스룸 | `/newsroom?feed=&page=` | 뉴스, 리포트, 영상, 블로그/커뮤니티 원문 모음 | content item, content-target link |
| 마이페이지 | `/realestate/mypage` | 사용자가 저장한 지역을 관리하고 지난 방문 이후 바뀐 시장 사실을 확인 | user watch, alert rule/event, observation log |
| 지역/단지 상세 | `/realestate/targets/:targetId` | 특정 지역의 종합 리포트와 근거 확인. 단지는 검증된 경우 보조 상세로 확장 | target, aliases, snapshot, market facts, timeline, evidence |

## 5. 대시보드 정의

### 5.1 목적

사용자가 접속 직후 "지금 어떤 지역 시장 사실을 먼저 확인해야 하는지"를 빠르게 이해한다.

### 5.2 현재 화면 구성

- 상단 검색/요약 영역
  - 지역/단지 검색 placeholder
  - 검색창 아래 과한 반응 필터와 메타 칩은 표시하지 않음
- 오늘의 부동산 브리핑
  - 특정 지역 차트가 아니라 최신 저장 일일 브리핑의 `summaryHeadlines[3]`를 짧은 명사형 헤드라인으로 보여준다.
  - 상세 본문은 `/realestate/daily-briefing`에서 `오늘의 핵심 흐름`, `주목할 지역과 이유`, `시장 변수`, `관련 뉴스·리포트`로 표시한다.
  - 상세 본문 화면은 단순 문단 나열이 아니라 브리핑 보드로 구성한다. 상단 기준 정보, 3개 헤드라인 카드, 핵심 흐름 narrative 패널, 주목 지역 ledger, 시장 변수 list, 관련 뉴스·리포트 ledger를 분리한다.
  - 관련 뉴스·리포트 영역은 본문 요약을 반복하지 않는다. 실제 `sourceItems`가 있으면 원문 근거 링크를 표시하고, 부족하면 뉴스룸, 리포트, 주요 일정, 전국 지도 같은 내부 확인 화면으로 연결한다.
  - `자세한 분석 보러가기` CTA는 브리핑 제목과 같은 제목선에 두고, 캐주얼한 알약보다 단정한 주요 액션 버튼으로 표시한다.
  - 개별 항목별 바로가기는 두지 않고 `자세한 분석 보러가기` 단일 CTA로 일일 브리핑 상세 흐름에 진입한다.
  - 화면에는 내부 분석 렌즈용 기간 구간명을 섹션 제목으로 노출하지 않는다.
- 지역 시장 흐름 한눈에
  - 실거래 변화, 전세 압력, 거래량, 공급/청약, 정책 민감도 구분
  - 지역별 기준 시각, 공개 지연, 핵심 변화, 근거 링크 후보
  - 지도, 실거래, 지역 상세로 이동
- 뉴스/리포트/외부 링크
  - 실시간 뉴스
  - 정책·통계 리포트
  - 부동산 영상
  - 블로그·커뮤니티
  - 영상과 블로그·커뮤니티에는 순위 번호를 붙이지 않고 일반 콘텐츠 목록으로 표시
- 오른쪽 빠른 패널
  - 인사이트, 거래, 관심 탭 미리보기
  - 인사이트 탭: 지금 확인할 지역 시장 변화와 공개 지연 상태
  - 거래 탭: 최근 실거래/전세 요약과 탐색 진입
  - 관심 탭: 관심 대상

### 5.3 ERD 매핑

| 화면 블록 | 주요 테이블 |
| --- | --- |
| 오늘의 부동산 브리핑 | `real_estate_market_facts`, `market_indicator_values`, `market_data_schedules`, `content_items` |
| 지역 시장 흐름 | `map_layer_snapshots`, `real_estate_market_facts`, `market_indicator_values`, `policy_event_targets` |
| 뉴스/리포트/영상/링크 | `content_items`, `content_target_links`, `crawl_sources` |
| 빠른 패널 | `user_watch_targets`, `alert_events`, `real_estate_market_facts`, `market_data_schedules` |

### 5.4 API 후보

`GET /api/realestate/dashboard/summary?window=1h&period=month`

응답은 아래 묶음으로 나뉜다.

- `dailyBriefing`: 시장 fact, 공식 지표, 주요 일정, 최근 이슈 후보를 조합한 일일 브리핑
- `marketSummary`: 지역별 실거래/전세/매물/공급 요약
- `transactionSummary`: 최근 실거래/전세 탐색 진입용 요약
- `scheduleSummary`: 이번 주/이번 달 확인할 공식 일정 요약
- `contentFeeds`: 뉴스, 리포트, 영상, 링크
- `dataFreshness`: provider별 stale/mock/asOf
- `quickPanel`: 인사이트/거래/관심 미리보기

### 5.5 상태 정의

- `mock`: 화면용 fixture 또는 검증 전 데이터
- `stale`: provider 공개 지연 또는 마지막 수집 기준 초과
- `unknown`: provider, asOf, confidence를 아직 확정하지 못한 값
- `low_sample`: 표본 수가 낮아 방향 해석보다 신뢰도 배지를 우선해야 하는 값

## 6. 지도 화면 정의

### 6.1 전국 지도 `/realestate/map`

전국 시도별 가격·거래 흐름을 큰 지도에서 클릭 탐색한다.

주요 구성:

- 타이틀: 전국 지역 흐름 지도
- 내부 구현명, 지도 asset 출처, TopoJSON 출처 문구는 화면 헤더에 노출하지 않는다.
- 헤더 박스는 낮은 높이로 유지하고, 설명은 한 줄 가격·거래 흐름 안내로 제한한다.
- 헤더 액션: 기간 탭 1주, 1개월, 3개월, 6개월, 1년 노출. 기본 선택은 1개월로 둔다. 주간 R-ONE 원천이 아직 적재되지 않은 target은 월간 값으로 숨겨서 대체하지 않고 `자료 없음` 또는 `공식 지수 미공표` 상태를 명확히 표시한다.
- 지도 박스 우측에는 `UPDATE: YYYY.MM.DD` 형식의 낮은 강조 회색 배지를 둔다. 날짜는 현재 선택한 기간의 공식 period `asOf`를 우선하고, 없으면 지도 layer `asOf`로 fallback한다.
- 헤더에는 `공공데이터 반영 · 최신 반영 · 기준 시각`처럼 긴 상태 배지를 노출하지 않는다.
- 지도 본문: 시도별 3D heat layer
- 지도 stage의 보조 라벨과 제목은 `전국 흐름 지도`, `전국 부동산 흐름`, `지역 상세 지도`, `{지역명} 상세 흐름`처럼 사용자용 한국어로 표시한다.
- 범례: 상승 빨강, 하락 파랑, 공식 지수 미공표는 검정에 가까운 회색
- 지역 버튼: 각 시도 중심점에 표시
- 하단 요약: 가장 강한 지역, 하위 지역 수, 다음 단계

동작:

- 시도를 클릭하면 `/realestate/map/:regionId`로 이동한다.
- 색상 방향은 `map_layer_snapshots.change_pct`로 계산한다. 상승은 빨강, 하락은 파랑, 거의 보합은 회색이다.
- 색상 진하기는 현재 지도에 보이는 계산값의 기준선 대비 차이로 정한다. 전국 지도는 보이는 시도 계산값의 평균을 기준선으로, 시도 상세 지도는 선택한 시도 계산값을 기준선으로 쓰고 값이 없으면 하위 지역 평균을 쓴다.
- 공식 상승/하락 값이 있는 지역은 세종처럼 면적이 작은 region에서도 색이 배경에 묻히지 않도록 최소 진하기를 확보한다.
- 표본이 부족하면 색상보다 표본 부족 배지를 우선한다.

ERD 매핑:

- `map_boundary_assets`: 지도 asset 출처와 기준 연도
- `map_features`: 시도 geometry와 target 연결
- `map_layer_snapshots`: 기간별 상승/하락, 표본 수, confidence
- `real_estate_targets`, `real_estate_regions`: 지역 정본

API:

- `GET /api/realestate/map/layers?layerType=sido`
- 응답 root: `layerType`, `asOf`, `sourceLabel`, `mapDataSource`, `dataStatus`, `stale`, `periods[]`, `targets[]`
- `targets[].targetId`는 `real_estate_targets.id`와 같은 값이다. 지도 route는 `seoul` 같은 화면용 slug보다 `region-seoul`, `region-daejeon` 같은 DB target id를 우선 사용한다.
- `targets[].periods.week|month|quarter|halfYear|year`는 `changePct`, `sampleCount`, `confidence`, `provider`, `asOf`, `dataStatus`, `stale`을 가진다.
- API가 비어 있거나 실패하면 지도 geometry fallback을 사용하되, 화면에는 `지도 레이어 수집 전/insufficient` 또는 `partial/stale` 상태를 표시한다.
- 최신 snapshot은 Spring Batch `rebWeeklyPriceIndexRefreshJob`, R-ONE 월간 Open API 수집, 또는 backend 내부 `POST /internal/realestate/map/layer-snapshots/refresh`가 생성한다. 이 refresh는 저장된 R-ONE 주간/월간 아파트 매매가격지수 fact를 읽어 가격지도용 `map_layer_snapshots`에 저장한다.
- 지도 화면은 SSE `topic=map-layers`를 받으면 전국/현재 시도 지도 API를 다시 조회해 배치 결과를 반영한다.
- 지도 색상 API는 `seed/mock`과 `reaction snapshot` row를 가격 데이터로 취급하지 않는다. 공식 가격지수나 실거래 fact가 없으면 해당 period를 비워 두고, 화면은 검정에 가까운 회색 `공식 지수 미공표`/`자료 없음` 상태로 표시한다.
- 커뮤니티 반응 snapshot은 지도 색상 원천이 아니라 보조 리포트와 EvidenceLog의 참고 근거로만 사용한다. 하위 지역 period snapshot이 없으면 지도 리포트의 변화율, 표본 수, 언급량, 출처 비율, 단지 후보를 임의 계산하지 않는다.

### 6.2 지역 상세 지도 `/realestate/map/:regionId`

시도 내부의 시군구 흐름을 보여주고, 특정 하위 지역 클릭 시 오른쪽 리포트를 연다.

주요 구성:

- 타이틀: `{지역명} 상세 흐름 지도`
- 지도 박스 내부 왼쪽 위: 전국 지도로 돌아가기 버튼
- 권역 상세 지도에서는 `전국 지도로 돌아가기`와 `{지역명} 전체 권역 보기` 버튼을 세로로 분리해 눌림 영역이 겹치거나 붙어 보이지 않게 한다.
- 지도 본문: 시군구 boundary와 색상 heat layer
- 하위 지역 버튼: 실제 시군구 중심점에 표시
- 세종처럼 시도와 시군구가 사실상 같은 단일 행정계층은 상세 지도에서 단일 하위 region에 부모 시도 R-ONE 공식 period를 그대로 연결하고, 하위 region을 선택해도 리포트와 EvidenceLog 조회 target은 부모 `region-sejong`으로 통일한다.
- 지도 확대 시 라벨은 지도 확대 배율과 반대로 보정해 글자가 과도하게 커지거나 흐려지지 않게 한다.
- 경기도처럼 하위 시군구가 많아 라벨이 한 화면에 몰리는 지역은 처음부터 모든 시군구 버튼을 노출하지 않고 `북부`, `서부`, `중부`, `남부` 같은 권역 클러스터를 먼저 보여준다. `동부 1곳`처럼 단독 권역이 생기면 중부 등 인접 권역에 통합한다. 클러스터 초기 화면에서는 땅 polygon 클릭으로 개별 시군구 선택이 열리지 않아야 하며, 클러스터 버튼을 누를 때만 해당 권역 feature만 다시 투영한 권역 상세 지도로 들어간다. 그 안에서 개별 시군구 버튼을 더 크게 노출한다.
- 인천처럼 섬과 본토 간 거리가 커서 본토가 한쪽에 몰리는 지역은 행정구역 전체 shape을 억지로 늘리거나 찌그러뜨리지 않는다. 상세 지도에서는 과도하게 먼 원거리 섬 polygon 일부만 생략하고, 남은 본토/주요 섬의 실제 위치 관계를 유지한다. 하위 지역 버튼/라벨은 수동 배치하지 않고 각 구·군 경계 내부 중심점에 둔다.
- 하단 요약: 가장 강한 하위 지역, 하위 지역 수, 다음 단계
- 선택 리포트 패널
  - 지역 리포트 헤더
  - AI 핵심 브리핑. 선택한 하위 지역 `targetId` 기준 `GET /api/realestate/targets/{targetId}/evidence-logs?limit=1`을 조회하되, 첫 화면에는 raw confidence, `AI 근거`, `insufficient` 같은 내부 상태어를 노출하지 않는다. 없으면 `분석 근거 수집 전`처럼 사용자용 상태로 바꾼다.
  - 선택 기간 등락률: 지도에 숫자를 직접 올리지 않고, `AI 분석 리포트` 본문 첫머리의 큰 수치 박스로 표시한다. 본문은 이 박스 오른쪽에서 시작하고 문장이 길어지면 박스 아래로 자연스럽게 이어진다. 박스 내부는 `최근 1개월`, `최근 1년`처럼 현재 선택 기간과 큰 등락률 숫자만 표시하고, 하단 보조 라벨은 두지 않는다. 기간 탭은 숫자와 지도 색상 렌즈만 바꾸며 리포트 본문 자체를 새로 만들지 않는다.
  - 기대 지점/우려 지점: 대표 브리핑 카드 본문 전체 폭을 써서 각각 3줄로 보여준다. 대시보드의 지역·단지 반응 구분을 참고하되, 행동 권유가 아니라 공식 지표와 수집 상태 기준의 관찰 포인트로만 쓴다. 오른쪽 패널에서 읽기 편하도록 본문 글씨는 작은 보조 텍스트처럼 보이지 않게 한다.
  - AI 분석 리포트: 선택 기간마다 다른 리포트를 만들지 않고, 최신 기준의 종합 평가와 판단을 짧은 본문으로 표시한다. 우측 날짜는 `리포트 업데이트 {시각}`으로 표시하고, 선택 기간의 `asOf`가 아니라 최신 EvidenceLog 또는 고정 리포트 기준일을 사용한다. 선택 기간 등락률은 본문을 보조하는 숫자 렌즈다.
  - 관련 뉴스·리포트: 대시보드 전체 브리핑 하단처럼 가격지수, 실거래, 뉴스/리포트 원문 근거가 적재되는 ledger로 둔다. 원문이 없으면 `수집 전`, `공식 데이터 없음`, `원문 링크 적재 대기` 상태로 둔다.
  - 지역 내 비교: 시도에서는 하위 시군구, 시군구에서는 생활권/동/단지 후보를 데이터 있는 항목만 표시
  - 공급·정책·일정: 청약, 미분양, 통계 발표, 정책/교통 이벤트 후보
  - 근거 로그와 한계: 첫 화면에서는 기대/우려, AI 분석 리포트, 관련 뉴스·리포트 상태에 흡수하고, 상세 확장에서는 출처, 기준 시각, 갱신 상태, 상위 지역만 반영 여부, 분석 근거 상태를 더 자세히 보여준다.
  - 보조 반응: 공개 원문/커뮤니티 반응은 하단 참고 신호로만 표시
  - 단지 좌표 매핑 후보. 없으면 `수집 전` 상태 유지
  - 시각 구조: `/realestate/daily-briefing` 상세 화면의 narrative panel과 관련 근거 ledger 리듬을 참고하되 동일 컴포넌트처럼 보이지 않게 한다. 처음 보이는 오른쪽 패널은 `AI 핵심 브리핑/기대·우려`, `AI 분석 리포트/선택 기간 등락률`, `관련 뉴스·리포트`만 보여준다. 대표 브리핑 카드는 라벨과 제목을 촘촘한 한 묶음으로 두고, 아래 본문 전체 폭에 기대 지점과 우려 지점을 나란히 배치한다. 등락률은 분석 리포트 본문 첫머리의 큰 수치 박스로 두며, 지역 내 비교/공급·정책·보조 반응/단지 후보는 후속 상세 후보로 둔다.

동작:

- 처음 진입 시 지도는 중앙 정렬이다.
- 외부 카드에서 특정 시군구를 바로 열 때는 `/realestate/map/:regionId?selectedTargetId=:targetId&selectedRegionCode=:geometryCode&period=week` query를 사용하고, 지도 화면은 해당 시군구 버튼을 선택한 것과 같은 지도+리포트 split 상태로 진입한다.
- 하위 지역을 클릭하면 지도는 왼쪽으로 줄고 오른쪽에 리포트가 나타난다.
- 리포트는 갑작스러운 밀림보다 투명도 기반으로 부드럽게 나타난다.
- 리포트 닫기 후 다시 중앙 지도 상태로 돌아간다.
- 리포트는 새 report 테이블을 전제로 하지 않는다. UI 우선 단계에서는 지도 layer, target market facts, timeline/content, 최신 EvidenceLog를 조합해 보여주고, backend 후속 단계에서 기존 EvidenceLog의 evidence item을 `market_fact`, `timeline_event`, `content`, `schedule`, `similar_window`, `reaction`으로 구분해 보강한다.
- 화면 요청 중 AI를 호출하지 않는다. batch/pipeline이 만든 최신 EvidenceLog를 조회하며, 값이 없으면 `공식 데이터 없음`, `수집 전`, `상위 지역만 반영`, `공개 지연 가능` 상태로 둔다.

ERD 매핑:

- `real_estate_regions.parent_region_id`: 시도와 시군구 계층
- `map_features.parent_region_code`: 상위 지역 필터
- `map_layer_snapshots`: 시군구별 기간 값
- `reaction_snapshots`, `reaction_snapshot_issues`: 보조 공개 반응과 쟁점
- `real_estate_market_facts`: 실거래/전세/매물 fact
- `timeline_events`, `policy_event_targets`: 정책/교통 이슈
- `real_estate_complexes`: 다음 단계 단지 좌표 연결 후보

API:

- `GET /api/realestate/map/layers?layerType=sigungu&parentTargetId={targetId}`
- `parentTargetId`는 시도 target id를 사용한다. 예: `region-seoul`
- 응답 shape는 전국 지도와 같고, `targets[]`는 해당 시도 하위 시군구 target이다.
- 1차 구현은 DB snapshot이 있는 하위 지역만 실제 API 값으로 덮어쓴다. `seed/mock` snapshot은 가격지도 API에서 제외되며, 공식 가격지수나 실거래 fact가 없는 지역은 검정에 가까운 회색 `공식 지수 미공표` 상태로 남긴다. 이 지역의 버튼은 disabled 상태로 두고 클릭해도 오른쪽 지역 리포트를 열지 않는다.
- 하위 snapshot이 없으면 기존 도식화 topology fallback을 유지하고, 하단 상태에 `하위 레이어 fallback`을 표시한다.
- 하위 snapshot이 있으면 하단 상태에 대표 period의 `provider`, `dataStatus`, `fresh/stale`, `asOf`를 그대로 표시한다. `DB snapshot`처럼 출처와 기준 시각을 숨기는 축약 문구만 단독으로 쓰지 않는다.

### 6.3 동/단지 내장 지도

전국, 시도, 시군구, 동 단위의 큰 흐름은 자체 도식화 heatmap으로 유지한다. 다만 특정 동 또는 단지 상세 단계부터는 실제 위치감이 중요하므로 카카오맵 SDK를 사이트 내부에 내장한다. 사용자를 외부 지도 사이트로 보내지 않고, 우리 서비스의 지도와 리포트 패널 안에서 단지 marker, 선택 패널, 근거 리포트를 함께 보여준다.

주요 구성:

- 내장 지도 영역: 카카오맵 SDK 기반 지도 canvas
- 단지 marker: `real_estate_complexes`의 좌표, 주소, 법정동 코드, `targetId`를 기준으로 표시
- 선택 패널: 단지명, 주소, 최근 market fact 상태, 공개 지연, 표본 신뢰도
- 오른쪽 리포트 패널: 실거래/전세/매물 fact, 최근 이슈 후보, 보조 공개 반응, evidence log
- 상태 배지: 지도 key missing, mock marker, stale/asOf, provider를 숨기지 않음

환경 기준:

- 로컬 프론트는 `front/.env.local`의 `VITE_KAKAO_JAVASCRIPT_KEY`를 사용한다.
- 실제 key는 git에 올리지 않고 `front/.env.example`에는 변수명만 둔다.
- SDK가 비활성화되었거나 key가 없으면 도식화 지도와 mock/stale 배지를 유지한다.

ERD 매핑:

- `real_estate_complexes`: 단지 좌표, 주소, provider key
- `real_estate_targets`: 단지 target 정본
- `real_estate_market_facts`: 단지/동 단위 market fact
- `reaction_snapshots`, `reaction_snapshot_issues`: 단지/동 보조 반응 지표
- `content_items`, `content_target_links`: 최근 이슈 후보와 근거 링크
- `evidence_logs`, `evidence_log_items`: 선택 리포트의 AI 근거 로그

## 7. 실거래 화면 정의

Route: `/realestate/transactions`

Legacy route: `/realestate/reactions`는 북마크 호환 기간에만 `/realestate/transactions`로 redirect한다. 새 제품 문구와 내비게이션에서는 `지역 반응`을 노출하지 않는다.

### 7.1 목적

지역, 기간, 거래 유형, 가격, 면적 기준으로 실거래/전세 데이터를 탐색하고, 지도에서 본 흐름을 숫자와 거래 row로 확인한다. 단지 후보는 공식 거래 또는 좌표가 검증된 complex target이 있을 때만 보조로 다룬다.

### 7.2 화면 방식

현재 프론트는 팀원 구현 전 빈 shell만 제공한다. 필터와 결과 리스트는 다음 구현자가 붙이는 영역이며, 이번 전환에서는 네비게이션과 route만 확정한다.

### 7.3 현재 화면 구성

- 빈 shell
  - 내부 UI 없음
  - 네비게이션 진입과 legacy redirect만 유지
- 이후 팀원 구현 후보
  - 지역, 기간, 거래 유형, 가격대, 면적, 데이터 상태 필터
  - 실거래/전세 리스트
  - provider, 기준 시각, 공개 지연, stale 상태
- 보조 근거
  - 관련 뉴스/리포트, 정책 이벤트, 필요한 경우 보조 공개 반응

### 7.4 ERD 매핑

| 화면 블록 | 주요 테이블 |
| --- | --- |
| 필터 기준 | `real_estate_targets`, `real_estate_regions`, `real_estate_complexes` |
| 실거래/전세 리스트 | `real_estate_market_facts` |
| 지역 집계 | `real_estate_market_facts`, `market_indicator_values`, `map_layer_snapshots` |
| 일정/정책 연결 | `market_data_schedules`, `policy_events`, `policy_event_targets` |
| 근거 로그 | `evidence_logs`, `evidence_log_items`, `observation_logs` |
| 보조 공개 반응 | `reaction_snapshots`, `reaction_snapshot_issues`, `content_items` |

### 7.5 API 후보

- `GET /api/realestate/transactions?targetId=&from=&to=&tradeType=&priceMin=&priceMax=&areaMin=&areaMax=&page=`
- `GET /api/realestate/transactions/summary?targetId=&from=&to=&tradeType=`
- `GET /api/realestate/evidence-logs?targetId=&window=`

## 8. 주요 일정 화면 정의

Route: `/indicators`, `/indicators/:category`

### 8.1 목적

부동산 시장을 확인할 때 반복적으로 봐야 하는 공식 통계, 실거래, 미분양·공급, 금리, 청약, 정책 발표 일정을 캘린더로 보여준다. 사용자는 일정 chip이나 출처 카드를 눌러 공식 사이트로 이동한다.

### 8.2 일정 유형

- 가격지수: 한국부동산원 R-ONE 주간·월간 가격동향
- 실거래: 국토교통부 실거래가 공개시스템
- 공급: 미분양, 인허가, 착공, 준공 등 국토교통 통계
- 금융: 한국은행 기준금리, 통화정책방향
- 청약: 청약Home 접수, 당첨자 발표, 경쟁률
- 정책: 국토교통부 보도자료, 공급·교통·정비사업 발표

### 8.3 현재 화면 구성

- 주요 일정 히어로
- 월간 일정 캘린더
- 이번 달 체크할 일정
- 공식 출처 바로가기

### 8.4 상세 route 처리

기존 `/indicators/:category` route는 과거 북마크 호환용으로 유지한다. 별도 KPI 상세 화면을 만들지 않고 `/indicators`와 동일한 주요 일정 화면을 보여준다.

### 8.5 ERD 매핑

- `market_data_schedules`: 공식 일정, provider, source URL, schedule date, 상태
- `content_items`: 정책·보도자료·리포트 후보
- `real_estate_market_facts`: 일정 이후 적재되는 실거래, 가격지수, 미분양 등 원천 fact
- `market_data_providers`: 한국부동산원, 국토교통부, 한국은행, 청약Home 등 provider 정의

### 8.6 API 후보

- `GET /api/realestate/market-data-schedules?month=YYYY-MM`
- `GET /api/realestate/market-data-sources`

## 9. 뉴스룸 화면 정의

Route: `/newsroom?feed=all|news|reports|videos|links&page=`

### 9.1 목적

지역 인사이트와 실거래의 근거가 되는 뉴스, 정책/통계 리포트, 영상, 블로그/커뮤니티 링크를 한곳에서 탐색한다.

### 9.2 현재 화면 구성

- 뉴스룸 타이틀
- 종합 보기
  - 실시간 뉴스
  - 정책·통계 리포트
  - 부동산 영상
  - 블로그·커뮤니티
  - 영상과 블로그·커뮤니티는 순위형 지표가 아니라 출처 아이콘, 제목, 메타 중심의 콘텐츠 목록으로 표시
- feed별 목록 보기
  - 뉴스만 몰아보기
  - 리포트만 몰아보기
  - 영상만 몰아보기
  - 원문 링크만 몰아보기
- 페이지네이션
- 각 row에는 source icon, 제목, 출처, 시간/참여 지표, status label을 표시한다.

### 9.3 ERD 매핑

- `content_items`: 카드 본문
- `content_target_links`: 관련 지역/단지 연결
- `crawl_sources`: 출처 메타, 접근 방식, robots/terms 검토
- `community_posts`: 커뮤니티 원문 후보일 때 원문 snippet과 URL

### 9.4 API 후보

- `GET /api/realestate/newsroom?feed=all&page=1&pageSize=15`
- `GET /api/realestate/content-items/:id`
- `GET /api/realestate/targets/:targetId/content?feed=`

## 10. 마이페이지 화면 정의

Route: `/realestate/mypage`

레거시 북마크 호환을 위해 `/realestate/watchlist`는 `/realestate/mypage`로 redirect한다.

### 10.1 목적

사용자가 저장한 지역/단지의 시장 변화, 주요 일정, 알림 조건, 개인 메모, 저장 지역 비교를 확인한다. 로그인/사용자 저장 API가 열리기 전에는 실제 저장 목록처럼 보이는 mock watchlist를 두지 않고 준비 상태를 분리해서 보여준다.

### 10.2 현재 화면 구성

- 마이페이지 요약 상태
  - 저장 지역/단지
  - 지난 방문 이후 바뀐 것
  - 알림 조건
  - 관찰 메모
- 내 저장 지역/단지
  - 로그인 전에는 실제 저장 목록처럼 보이는 mock 목록을 두지 않고 빈 상태를 표시
  - 저장 이유 태그 후보: 실거주, 전세, 청약, 투자관찰, 교통, 재건축, 공급
- 지난 방문 이후 바뀐 것
  - 새 실거래/전세 거래
  - 주요 일정 도래
  - 정책/공급/청약 이슈 추가
  - 근거 리포트 갱신
  - 데이터 stale 또는 공식 데이터 없음 상태
- 내 알림 조건
  - `알림 조건 준비 중` 또는 `조건 관리` 상태로 표시
- 지역별 관찰 메모
  - 개인 기록으로만 표현하고 투자 행동을 권유하지 않음
- 저장 지역 비교
  - 실거래, 전세, 공급, 주요 일정, 근거 갱신 상태를 저장 지역끼리 비교

### 10.3 ERD 매핑

- `app_users`: 사용자
- `user_watch_targets`: 관심 대상 저장
- `alert_rules`: 알림 조건
- `alert_events`: 발생한 알림
- `observation_logs`: 관찰/복기 로그
- `real_estate_aliases`: 별칭 DB 연결 준비
- `crawl_sources`, `source_boards`: 원문 수집 후보
- `real_estate_market_facts`: 공공데이터 후보

### 10.4 API 후보

- `GET /api/users/me/watch-targets`
- `POST /api/users/me/watch-targets`
- `GET /api/users/me/alerts`
- `GET /api/users/me/observation-logs`
- 저장 기능 전 임시 후보: `GET /api/realestate/transactions/summary?windowMinutes=10080&limit=10`

현재 로그인은 화면상 버튼만 존재한다. 실제 사용자 기능이 열리기 전에는 저장된 관심 목록처럼 보이는 mock watchlist를 두지 않고, 저장 대상 없음/로그인 연동 준비 중/데이터 확인 전 상태를 분리해 표시한다. API가 비거나 실패하면 `데이터 확인 전/insufficient` 또는 오류 상태를 표시한다.

## 11. 지역/단지 상세 화면 정의

Route: `/realestate/targets/:targetId`

### 11.1 목적

특정 지역/단지에 대해 어떤 시장 사실이 바뀌었는지, 어떤 지표와 원문이 근거인지, 신뢰도와 데이터 지연 상태는 어떤지 리포트 형태로 보여준다.

### 11.2 현재 화면 구성

- 지역 한줄 브리핑
- 지역 상세 리포트 헤더
  - 대상명, targetId, 지역
  - 현재 시장 흐름
  - confidence
- 요약 지표
  - 매매가격지수
  - 전세가격지수 또는 전세수급지수
  - 거래량
  - 전세가율/준공 물량 등 대상별 지표
- 실거래/전세 흐름
  - 거래 row 요약
  - 전세 압력과 가격 흐름
  - 공개 지연과 provider 상태
- 보조 공개 반응
  - source별 mentions
  - 기대/우려 비율
  - 원문 요약
- 신호 신뢰도
- 시간대별 변화
- 근거 링크 후보

### 11.3 ERD 매핑

- `real_estate_targets`: 대상 정본
- `real_estate_regions`, `real_estate_complexes`: 지역/단지 상세 속성
- `real_estate_aliases`: 검색/원문 연결 별칭
- `reaction_snapshots`: 기간별 보조 반응 요약
- `reaction_snapshot_issues`: 보조 쟁점 비율
- `real_estate_market_facts`: 실거래/전세/매물 fact
- `market_indicator_values`: 지표 값
- `timeline_events`: 시간대별 변화
- `policy_event_targets`: 정책 영향
- `similar_window_matches`: 유사 과거 상황
- `evidence_logs`, `evidence_log_items`: AI 리포트 근거

### 11.4 API 후보

- `GET /api/realestate/targets/:targetId`
- `GET /api/realestate/targets/:targetId/report?window=1h&period=month`
- `GET /api/realestate/targets/:targetId/timeline`
- `GET /api/realestate/targets/:targetId/evidence`
- `GET /api/realestate/targets/:targetId/similar-windows`

## 12. 공통 컴포넌트 정의

공통 shell의 상단 인사이트 strip과 오른쪽 rail은 정적 mock 문구를 두지 않는다. 로그인/사용자 저장 기능이 열리기 전에는 `GET /api/realestate/transactions/summary?windowMinutes=10080&limit=6` 또는 dashboard summary 응답을 우선 사용하고, 응답이 비면 `데이터 확인 전/insufficient`, 실패하면 `시장 데이터 API 오류`를 표시한다.

### 12.1 상태 배지

| 배지 | 의미 | 표시 위치 |
| --- | --- | --- |
| `mock` | fixture 또는 검증 전 데이터 | 모든 카드 |
| `stale` | 공개 지연 또는 갱신 기준 초과 | 지표, 실거래, 매물, 뉴스 |
| `실시간 아님` | 수집/공개 지연 가능 | 대시보드, 지도, 지표 |
| `표본 부족` | sample count 부족 | 지도, 리포트, 지표 |
| `부동산 자문 아님` | 법적/서비스 경계 | footer 또는 별도 유의사항 영역 |

### 12.2 기간 탭

- `주`
- `월`
- `6개월`
- `년`

지도는 `1주`, `1개월`, `3개월`, `6개월`, `1년`을 쓴다. period key는 `week`, `month`, `quarter`, `halfYear`, `year`이며, 기본 선택은 `month`다. `week`는 최신 주간 지수와 직전 주간 지수 비교값이고, `month`/`quarter`/`halfYear`/`year`는 최신 월간 지수와 1/3/6/12개월 전 월간 지수 비교값이다. `week`는 월간 값으로 대체하지 않고, 해당 지수 history가 부족하면 `자료 없음` 또는 `공식 지수 미공표`로 표시한다.

### 12.3 리포트 패널

지도와 상세 화면의 리포트는 같은 정보 구조를 공유한다.

- 한줄 요약
- 데이터 상태
- 시장 fact 요약
- 쟁점 matrix
- 시장 fact
- 근거 링크
- 다음 확인 항목

### 12.4 근거 링크 row

근거 링크는 출처 이름, 문서/게시글 제목, URL, 상태, 관련 target, confidence를 가져야 한다.

ERD 후보:

- 뉴스/리포트: `content_items`, `content_target_links`
- 보조 공개 원문: `community_posts`, `real_estate_mentions`
- AI 근거: `evidence_log_items`

## 13. 화면별 우선순위

1. 대시보드
   - 서비스의 첫인상과 전체 정보 구조를 결정한다.
   - API가 늦어도 fixture shape를 먼저 고정해야 한다.
2. 지도
   - 부동산 서비스만의 차별점이다.
   - `map_features`, `map_layer_snapshots`, 지역 hierarchy API가 먼저 필요하다.
3. 실거래
   - 지도에서 본 흐름을 실제 거래/전세 row로 확인하는 화면이다.
   - filter, summary, transaction row, provider/asOf 계약이 중요하다.
4. 주요 일정
   - 공식 통계·정책·청약·금리 확인 일정을 캘린더와 출처 링크로 정리한다.
5. 뉴스룸
   - 시장 fact와 일정의 근거 링크를 확인하는 보조 탐색 화면이다.
6. 마이페이지
   - 사용자가 저장한 지역을 관리하고, 지난 방문 이후 바뀐 시장 사실을 확인하는 개인화 공간으로 둔다.
7. 지역/단지 상세
   - 지도와 실거래에서 클릭해 들어가는 최종 리포트다.

## 14. 구현 체크리스트

- [x] 화면 route의 `targetId`를 DB의 `target_id`와 같은 값으로 고정
- [ ] 대시보드 summary API fixture shape 확정
- [x] 지도 전국/시군구 API shape 확정
- [x] 동/단지 상세 카카오맵 SDK 내장 지도 prototype 확정
- [ ] `mock`, `stale`, `unknown`, `low_sample` 상태 표시 공통화
- [ ] 상승 빨강, 하락 파랑 색상 토큰 공통화
- [ ] 뉴스/리포트/보조 공개 원문 링크의 출처 icon fallback 정리
- [ ] 지역/단지 상세의 evidence log 구조 확정
- [ ] 마이페이지는 로그인 전 준비 상태와 로그인 후 실제 사용자 저장 상태 분리

## 15. 아직 결정이 필요한 부분

- 공공데이터 provider별 실제 갱신 주기와 stale 기준
- 뉴스, 블로그, 공개 커뮤니티 등 보조 원문 수집 가능 범위와 robots/terms 검토 결과
- 지역/생활권/단지군/단지의 target type 명명 규칙
- 지도 drilldown에서 단지 좌표를 언제부터 노출할지
- AI 리포트의 confidence 산식과 근거 노출 최소 단위
- 상세 화면에서 유사 과거 비교를 별도 섹션으로 넣을지 여부

## 16. 검증 기준

- 배포 화면 기준으로 모든 주요 route가 접근 가능해야 한다.
- 대시보드에서 각 상세 링크가 올바른 route로 이동해야 한다.
- 지도는 전국, 지역 상세, 리포트 패널 상태가 구분되어야 한다.
- 실거래는 `/realestate/transactions`에서 필터 query와 목록 상태가 함께 동작해야 한다.
- 주요 일정은 `/indicators`와 과거 상세 route 모두에서 같은 일정 캘린더로 접근 가능해야 한다.
- 뉴스룸은 `feed`와 `page` query로 목록 상태가 표현되어야 한다.
- 모든 화면은 mock/stale/asOf/provider 상태를 숨기지 않아야 한다.
- 가격 상승/긍정은 빨강, 하락/우려는 파랑으로 일관되어야 한다.
