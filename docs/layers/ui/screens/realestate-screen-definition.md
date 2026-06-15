# 너나사 부동산 화면 정의서

작성일: 2026-06-04
기준 화면: https://youbuyfirst-realestate.netlify.app/dashboard
기준 ERD: `docs/domains/realestate/ERD.md`, `docs/domains/realestate/ERD.visual-import.sql`

## 1. 서비스 한 줄 정의

요즘 부동산 관심이 어디로 몰리는지, 사람들의 말과 시장 데이터를 엮어 보여주는 AI 부동산 인사이트 서비스.

이 서비스는 매수, 매도, 청약, 대출 행동을 권유하지 않는다. 커뮤니티 반응, 뉴스/리포트, 실거래/전세/매물/지표, 정책 이벤트를 함께 관찰해 "어디가 왜 뜨는지"를 설명하는 관찰형 분석 서비스다.

## 2. 공통 화면 원칙

- 공통 내비게이션은 `대시보드`, `뉴스룸`, `지도`, `지역 반응`, `주요 지표`, `관심 지역`으로 유지한다.
- 너나사 시리즈의 UI 패턴은 유지하되, 부동산 서비스의 대표 포인트 컬러는 주황 계열을 쓴다.
- 상승, 기대, 긍정 방향은 빨강 계열로 표시한다.
- 하락, 우려, 냉각 방향은 파랑 계열로 표시한다.
- 모든 데이터 카드에는 가능한 경우 `asOf`, `mock`, `stale`, `dataStatus`, `provider`를 노출한다.
- 커뮤니티 반응은 확정 판단이 아니라 관찰 신호로 표현한다.
- 화면 문구는 `관찰`, `반응 지표`, `쟁점`, `표본`, `신뢰도`, `근거`, `공개 지연` 중심으로 쓴다.
- 투자 조언처럼 보이는 CTA는 쓰지 않는다. 예: `매수`, `진입`, `청약 추천`, `대출 추천` 금지.

## 3. ERD 기준 데이터 축

### 3.1 부동산 대상 정본

`real_estate_targets`가 모든 화면의 중심 테이블이다. 지역, 생활권, 단지군, 단지를 모두 같은 관찰 대상의 루트로 둔다.

- `real_estate_targets`: 화면에서 클릭하거나 랭킹에 올라오는 대상의 공통 정본
- `real_estate_regions`: 지역 대상의 식별 하위 테이블, `target_id`가 PK이자 FK
- `real_estate_complexes`: 단지 대상의 식별 하위 테이블, `target_id`가 PK이자 FK
- `real_estate_aliases`: 커뮤니티 크롤링용 별칭, 줄임말, 카페식 명칭
- `real_estate_target_edges`: 생활권, 단지군, 인접 지역, 정책 영향권 같은 대상 간 관계

화면 라우트의 `targetId`는 `real_estate_targets.id`를 그대로 사용합니다. 화면 fixture도 `region-seoul-mapo`, `living-area-gyeonggi-dongtan-station`, `complex-mapo-raemian-prugio`처럼 backend target registry와 같은 kebab-case 식별자를 씁니다. 별도 화면용 대문자 ID와 API용 ID를 나누지 않습니다.

### 3.2 지도 데이터

- `map_boundary_assets`: 시도/시군구 지도 원본 asset
- `map_features`: 지도 geometry와 `real_estate_targets` 연결
- `map_layer_snapshots`: 기간별 상승/하락 heat layer 값, 표본 수, 신뢰도, asOf

### 3.3 커뮤니티 수집과 반응 분석

- `crawl_sources`: 네이버 카페, 다음 카페, 블로그, 커뮤니티, 뉴스 등 수집처
- `source_boards`: 수집처 안의 게시판/섹션
- `community_posts`: 공개 원문 후보, 제목, snippet, URL, 작성 시각, 작성자 hash
- `real_estate_mentions`: 게시글 안에서 인식된 지역/단지 언급
- `reaction_analyses`: 언급 단위의 기대/우려/중립 방향과 쟁점 분류
- `reaction_snapshots`: 기간별 대상 반응 집계
- `reaction_snapshot_issues`: snapshot 안의 쟁점 비율
- `reaction_ranking_snapshots`, `reaction_ranking_rows`: 화면용 랭킹 스냅샷

### 3.4 뉴스, 리포트, 외부 링크

- `content_items`: 뉴스, 리포트, 영상, 블로그/커뮤니티 링크 카드
- `content_target_links`: 콘텐츠와 지역/단지 대상의 다대다 연결

### 3.5 시장 사실과 주요 지표

- `real_estate_market_facts`: 실거래, 전세, 매물, 청약, 미분양 같은 provider별 fact
- `market_indicator_defs`: 매매가격지수, 전세가격지수, 실거래가 지수, 거래량, 전세가율 등 지표 정의
- `market_indicator_values`: 기간/대상별 지표 값
- `market_data_schedules`: 주요 통계 발표 일정과 갱신 상태

### 3.6 정책, 타임라인, AI 근거

- `policy_events`: 정책, 교통, 청약, 대출 규제 등 이벤트
- `policy_event_targets`: 정책 이벤트와 대상의 다대다 영향 연결
- `timeline_events`: 대상별 시간대 변화
- `similar_window_matches`: 과거 유사 반응 구간 연결
- `evidence_logs`, `evidence_log_items`: AI 분석 결과와 근거 항목

### 3.7 사용자 관심과 알림

- `app_users`: 사용자 계정
- `user_watch_targets`: 사용자가 저장한 관심 지역/단지, 다대다 연결
- `alert_rules`: 알림 조건
- `alert_events`: 실제 발생한 알림
- `observation_logs`: 사용자의 관찰/복기 로그

## 4. 화면 목록

| 화면 | Route | 화면 목적 | 핵심 데이터 |
| --- | --- | --- | --- |
| 대시보드 | `/dashboard` | 오늘 관심이 몰리는 지역과 이유를 한 화면에서 파악 | 랭킹, 반응 snapshot, 지표, 뉴스/리포트, 데이터 상태 |
| 지도 | `/realestate/map` | 전국 시도별 흐름을 heat layer로 탐색 | 지도 feature, layer snapshot, 대상 정본 |
| 지역 상세 지도 | `/realestate/map/:regionId` | 시도 내부 시군구 흐름과 리포트 확인 | 지역 hierarchy, 지도 feature, 반응/시장 fact |
| 지역 반응 | `/realestate/reactions?view=` | 커뮤니티 언급 급증, 순위, 근거 로그 확인 | reaction ranking, issue mix, evidence log |
| 주요 지표 | `/indicators`, `/indicators/:category` | 부동산 지표 묶음과 반응 괴리 확인 | indicator def/value, schedules, market facts |
| 뉴스룸 | `/newsroom?feed=&page=` | 뉴스, 리포트, 영상, 블로그/커뮤니티 원문 모음 | content item, content-target link |
| 관심 지역 | `/realestate/watchlist` | 저장한 지역/단지와 알림 판단 내역 확인 | user watch, alert rule/event, observation log |
| 지역/단지 상세 | `/realestate/targets/:targetId` | 특정 대상의 종합 리포트와 근거 확인 | target, aliases, snapshot, market facts, timeline, evidence |

## 5. 대시보드 정의

### 5.1 목적

사용자가 접속 직후 "지금 부동산 관심이 어디로 몰리고, 그 이유가 무엇인지"를 빠르게 이해한다.

### 5.2 현재 화면 구성

- 상단 검색/요약 영역
  - 부동산 투기 과열 지표
  - 지역/단지 검색 placeholder
  - 필터: 전체, 언급 증가, 정책 변화, 공공데이터 stale
  - 언급 합계, 지연 지표, 관찰 대상 수, 부동산 자문 아님 고지
- 핵심 지역별 상승률
  - 기간 탭: 주, 월, 6개월, 년
  - 지역별 가격 변화 선 그래프
  - 지도 화면으로 이동
- 지역·단지 반응 한눈에
  - 기대 반응, 우려 반응, 중립/기타 구분
  - 지역별 언급량, 기대/우려 비율, 핵심 쟁점, 근거 링크 후보
  - 지역 상세로 이동
- 주요 부동산 지표
  - 매매가격지수, 전세가격지수, 실거래가 지수, 거래량, 전세가율, 미분양
  - 기간 탭과 지연 가능 배지
  - 주요 지표 화면으로 이동
- 뉴스/리포트/외부 링크
  - 실시간 뉴스
  - 정책·통계 리포트
  - 부동산 영상 새 글
  - 블로그와 커뮤니티 링크
- 실거래·지표 상태
  - provider별 stale, mock, 공개 지연 상태
- 확인 필요
  - 별칭 매핑, 공공데이터 계약, 크롤링 출처 검토 등 작업 후보
- 오른쪽 빠른 패널
  - 반응, 지표, 관심 탭 미리보기
  - 지금 언급 급상승 지역, 라이징 스타, 주요 지표, 관심 대상

### 5.3 ERD 매핑

| 화면 블록 | 주요 테이블 |
| --- | --- |
| 부동산 투기 과열 지표 | `reaction_snapshots`, `market_indicator_values`, `real_estate_market_facts`, `evidence_logs` |
| 핵심 지역별 상승률 | `map_layer_snapshots`, `market_indicator_values`, `real_estate_targets` |
| 지역·단지 반응 | `reaction_ranking_snapshots`, `reaction_ranking_rows`, `reaction_snapshots`, `reaction_snapshot_issues` |
| 뉴스/리포트/영상/링크 | `content_items`, `content_target_links`, `crawl_sources` |
| 실거래·지표 상태 | `real_estate_market_facts`, `market_data_schedules` |
| 확인 필요 | `real_estate_aliases`, `crawl_sources`, `source_boards`, `evidence_logs` |
| 빠른 패널 | `user_watch_targets`, `alert_events`, `reaction_ranking_rows`, `market_indicator_values` |

### 5.4 API 후보

`GET /api/realestate/dashboard/summary?window=1h&period=month`

응답은 아래 묶음으로 나뉜다.

- `overheatIndex`: 과열 지표 값, 상태, 변화율, 키워드
- `regionalReturnSeries`: 지역별 가격/지표 변화 시계열
- `reactionGroups`: 기대/우려/중립 랭킹과 근거 링크
- `marketIndicators`: 주요 지표 카드
- `contentFeeds`: 뉴스, 리포트, 영상, 링크
- `dataFreshness`: provider별 stale/mock/asOf
- `todoSignals`: 확인 필요 항목
- `quickPanel`: 반응/지표/관심 미리보기

### 5.5 상태 정의

- `mock`: 화면용 fixture 또는 검증 전 데이터
- `stale`: provider 공개 지연 또는 마지막 수집 기준 초과
- `unknown`: provider, asOf, confidence를 아직 확정하지 못한 값
- `low_sample`: 표본 수가 낮아 방향 해석보다 신뢰도 배지를 우선해야 하는 값

## 6. 지도 화면 정의

### 6.1 전국 지도 `/realestate/map`

전국 시도별 가격/반응 흐름을 큰 지도에서 클릭 탐색한다.

주요 구성:

- 타이틀: 전국 지역 흐름 지도
- 기간 탭: 1주, 1개월, 6개월
- 지도 본문: 시도별 3D heat layer
- 범례: 상승 빨강, 하락 파랑, 표본 부족 회색
- 지역 버튼: 각 시도 중심점에 표시
- 하단 요약: 가장 강한 지역, 하위 지역 수, 다음 단계

동작:

- 시도를 클릭하면 `/realestate/map/:regionId`로 이동한다.
- 색상은 `map_layer_snapshots.change_pct`와 `confidence`로 계산한다.
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
- `targets[].periods.week|month|halfYear`는 `changePct`, `sampleCount`, `confidence`, `provider`, `asOf`, `dataStatus`, `stale`을 가진다.
- API가 비어 있거나 실패하면 fixture fallback을 사용하되, 화면에는 `mock fallback` 상태를 표시한다.
- 최신 snapshot은 backend 내부 `POST /internal/realestate/map/layer-snapshots/refresh`와 pipeline daily scheduler가 생성한다. 이 refresh는 실거래 market fact와 reaction snapshot을 읽어 `map_layer_snapshots`에 저장하며, 표본 부족 구간은 기존 seed/mock fallback을 유지한다.

### 6.2 지역 상세 지도 `/realestate/map/:regionId`

시도 내부의 시군구 흐름을 보여주고, 특정 하위 지역 클릭 시 오른쪽 리포트를 연다.

주요 구성:

- 타이틀: `{지역명} 상세 흐름 지도`
- 지도 박스 내부 왼쪽 위: 전국 지도로 돌아가기 버튼
- 지도 본문: 시군구 boundary와 색상 heat layer
- 하위 지역 버튼: 실제 시군구 중심점에 표시
- 하단 요약: 가장 강한 하위 지역, 하위 지역 수, 다음 단계
- 선택 리포트 패널
  - 지역 리포트 헤더
  - community pulse
  - 출처 비중
  - 핵심 쟁점
  - 가격 흐름, 거래 강도, 전세 압력, 공급/청약, 정책/교통, 커뮤니티 언급
  - 단지 좌표 매핑 후보

동작:

- 처음 진입 시 지도는 중앙 정렬이다.
- 하위 지역을 클릭하면 지도는 왼쪽으로 줄고 오른쪽에 리포트가 나타난다.
- 리포트는 갑작스러운 밀림보다 투명도 기반으로 부드럽게 나타난다.
- 리포트 닫기 후 다시 중앙 지도 상태로 돌아간다.

ERD 매핑:

- `real_estate_regions.parent_region_id`: 시도와 시군구 계층
- `map_features.parent_region_code`: 상위 지역 필터
- `map_layer_snapshots`: 시군구별 기간 값
- `reaction_snapshots`, `reaction_snapshot_issues`: 커뮤니티 반응과 쟁점
- `real_estate_market_facts`: 실거래/전세/매물 fact
- `timeline_events`, `policy_event_targets`: 정책/교통 이슈
- `real_estate_complexes`: 다음 단계 단지 좌표 연결 후보

API:

- `GET /api/realestate/map/layers?layerType=sigungu&parentTargetId={targetId}`
- `parentTargetId`는 시도 target id를 사용한다. 예: `region-seoul`
- 응답 shape는 전국 지도와 같고, `targets[]`는 해당 시도 하위 시군구 target이다.
- 1차 구현은 DB snapshot이 있는 하위 지역만 실제 API 값으로 덮어쓴다. 예: `parentTargetId=region-seoul`은 종로구/마포구 seed snapshot을 내려준다.
- 하위 snapshot이 없으면 기존 도식화 topology fallback을 유지하고, 하단 상태에 `하위 레이어 fallback`을 표시한다.
- 하위 snapshot이 있으면 하단 상태에 대표 period의 `provider`, `dataStatus`, `fresh/stale`, `asOf`를 그대로 표시한다. `DB snapshot`처럼 출처와 기준 시각을 숨기는 축약 문구만 단독으로 쓰지 않는다.

### 6.3 동/단지 내장 지도

전국, 시도, 시군구, 동 단위의 큰 흐름은 자체 도식화 heatmap으로 유지한다. 다만 특정 동 또는 단지 상세 단계부터는 실제 위치감이 중요하므로 카카오맵 SDK를 사이트 내부에 내장한다. 사용자를 외부 지도 사이트로 보내지 않고, 우리 서비스의 지도와 리포트 패널 안에서 단지 marker, 선택 패널, 근거 리포트를 함께 보여준다.

주요 구성:

- 내장 지도 영역: 카카오맵 SDK 기반 지도 canvas
- 단지 marker: `real_estate_complexes`의 좌표, 주소, 법정동 코드, `targetId`를 기준으로 표시
- 선택 패널: 단지명, 주소, 최근 market fact 상태, 반응 방향, 표본 신뢰도
- 오른쪽 리포트 패널: 커뮤니티 반응, 실거래/전세/매물 fact, 최근 이슈 후보, evidence log
- 상태 배지: 지도 key missing, mock marker, stale/asOf, provider를 숨기지 않음

환경 기준:

- 로컬 프론트는 `front/.env.local`의 `VITE_KAKAO_JAVASCRIPT_KEY`를 사용한다.
- 실제 key는 git에 올리지 않고 `front/.env.example`에는 변수명만 둔다.
- SDK가 비활성화되었거나 key가 없으면 도식화 지도와 mock/stale 배지를 유지한다.

ERD 매핑:

- `real_estate_complexes`: 단지 좌표, 주소, provider key
- `real_estate_targets`: 단지 target 정본
- `real_estate_market_facts`: 단지/동 단위 market fact
- `reaction_snapshots`, `reaction_snapshot_issues`: 단지/동 반응 지표
- `content_items`, `content_target_links`: 최근 이슈 후보와 근거 링크
- `evidence_logs`, `evidence_log_items`: 선택 리포트의 AI 근거 로그

## 7. 지역 반응 화면 정의

Route: `/realestate/reactions?view=overview|ranking|signals|agents`

### 7.1 목적

지역과 단지의 커뮤니티 언급 급증, 기대/우려 방향, 쟁점, AI 근거 로그를 한 화면에서 비교한다.

### 7.2 탭

- `종합`: 급증 지역, 순위, 급증 쟁점, 근거 로그를 함께 보여준다.
- `순위`: 지역 언급량 TOP 6, 단지군 관심 TOP 6 중심으로 보여준다.
- `반응`: 커뮤니티 언급 급증 지역 카드 중심으로 보여준다.
- `근거 로그`: 모의 에이전트 판단 기록 중심으로 보여준다.

### 7.3 현재 화면 구성

- 커뮤니티 언급 급증 지역
  - 언급 급증
  - 기대 우세
  - 우려 증가
  - 정책 민감
- 지역 언급량 TOP 6
  - 순위, 지역/단지, 언급량, 반응 비율, 쟁점, freshness
- 단지군 관심 TOP 6
  - 지역 순위와 동일한 열 구조
- 급증 쟁점
  - 전세 매물, GTX·교통, 재건축, 공급 부담
- 데이터 기준
  - 수집 시각, 실거래 공개 지연, mock/demo 상태
- 모의 에이전트 판단 기록
  - 시간, 지역/단지, 전략, 상태, 판단 입력값, 판단 key

### 7.4 ERD 매핑

| 화면 블록 | 주요 테이블 |
| --- | --- |
| 급증 지역 카드 | `reaction_ranking_rows`, `reaction_snapshots`, `reaction_snapshot_issues` |
| 지역/단지 순위 | `reaction_ranking_snapshots`, `reaction_ranking_rows`, `real_estate_targets` |
| 반응 비율 | `reaction_snapshots`, `reaction_analyses` |
| 쟁점 분류 | `issue_taxonomy`, `reaction_snapshot_issues` |
| 근거 로그 | `evidence_logs`, `evidence_log_items`, `observation_logs` |
| 커뮤니티 출처 | `crawl_sources`, `source_boards`, `community_posts`, `real_estate_mentions` |

### 7.5 API 후보

- `GET /api/realestate/reactions?view=overview&window=1h`
- `GET /api/realestate/reactions/rankings?type=region&window=1h`
- `GET /api/realestate/reactions/rankings?type=complex&window=1h`
- `GET /api/realestate/evidence-logs?targetId=&window=`

## 8. 주요 지표 화면 정의

Route: `/indicators`, `/indicators/:category`

### 8.1 목적

부동산 시장을 수치로 볼 때 필요한 지표를 가격/거래량, 공급/수급, 수요/심리, 거시경제/금융으로 나눠 보여준다. 지역 반응과 지표가 엇갈리는 구간을 별도로 보여준다.

### 8.2 카테고리

- 가격 및 거래량
  - 매매가격지수
  - 전세가격지수
  - 실거래가 지수
  - 매매/전월세 거래량
- 공급 및 수급
  - 미분양 주택
  - 준공 후 미분양
  - 인허가·착공·준공
  - 전세가율
- 수요 및 심리
  - 매매수급지수
  - 전세수급지수
  - 부동산시장 소비심리지수
  - 커뮤니티 언급량
- 거시경제 및 금융
  - 주택구입부담지수 K-HAI
  - 기준금리
  - 통화량 M2
  - 물가상승률

### 8.3 현재 화면 구성

- 주요 지표 히어로
- 핵심 지표 카테고리 카드 4개
- 지역별 지표 방향
- 지표 묶음별 관찰 포인트
- 지표와 반응이 엇갈린 지역
- 지표별 반응 히트맵
- 지표별 데이터 신선도
- 주요 일정

### 8.4 상세 화면

`/indicators/:category`에서는 선택 카테고리의 세부 KPI, 지표와 지역 반응 동시 변화, 데이터 신선도, 연결 키워드, 지표와 반응이 엇갈린 지역을 보여준다.

### 8.5 ERD 매핑

- `market_indicator_defs`: 카테고리와 지표 정의
- `market_indicator_values`: 기간/대상별 값, 변화율, 상태
- `market_data_schedules`: 발표 일정
- `real_estate_market_facts`: 실거래, 전세, 매물, 미분양 등 원천 fact
- `reaction_snapshots`: 지표와 반응 괴리 분석
- `map_layer_snapshots`: 지역별 방향 heat 요약

### 8.6 API 후보

- `GET /api/realestate/indicators?period=month`
- `GET /api/realestate/indicators/:category?period=month`
- `GET /api/realestate/indicators/anomalies?period=month`
- `GET /api/realestate/market-data-schedules`

## 9. 뉴스룸 화면 정의

Route: `/newsroom?feed=all|news|reports|videos|links&page=`

### 9.1 목적

지역/단지 반응의 근거가 되는 뉴스, 정책/통계 리포트, 영상, 블로그/커뮤니티 링크를 한곳에서 탐색한다.

### 9.2 현재 화면 구성

- 뉴스룸 타이틀
- 종합 보기
  - 실시간 뉴스
  - 정책·통계 리포트
  - 부동산 영상 새 글
  - 블로그와 커뮤니티 링크
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

## 10. 관심 지역 화면 정의

Route: `/realestate/watchlist`

레거시 호환 route는 제거하고 `/realestate/watchlist`만 사용한다.

### 10.1 목적

사용자가 저장한 관심 지역/단지의 반응 변화, 알림 판단, 원문/공공데이터 연결 후보, 복기 로그를 확인한다.

### 10.2 현재 화면 구성

- 관심 지역 요약 KPI
  - 관심 지역
  - 급증 알림
  - 전세 우려
  - 실거래 stale
  - 원문 후보
  - 확인 대기
- 관심 지역과 반응 연결
- 커뮤니티 원문·별칭 DB 연결 준비
- 원문/공공데이터 후보
- 알림 판단 내역
- 관찰 로그
- 알림 후 복기

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
- 저장 기능 전 임시 후보: `GET /api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=10`

현재 로그인은 화면상 버튼만 존재한다. 실제 사용자 기능이 열리기 전에는 저장된 관심 목록처럼 보이는 mock watchlist를 두지 않고, 지역 반응 TOP10을 `관심 후보`로 표시한다. API가 비거나 실패하면 `수집 전/insufficient` 또는 오류 상태를 표시한다.

## 11. 지역/단지 상세 화면 정의

Route: `/realestate/targets/:targetId`

### 11.1 목적

특정 지역/단지에 대해 왜 관심이 늘었는지, 어떤 지표와 원문이 근거인지, 신뢰도와 데이터 지연 상태는 어떤지 리포트 형태로 보여준다.

### 11.2 현재 화면 구성

- 지역 한줄 브리핑
- 지역 상세 리포트 헤더
  - 대상명, targetId, 지역
  - 현재 반응 방향
  - confidence
- 요약 지표
  - 매매가격지수
  - 전세가격지수 또는 전세수급지수
  - 거래량
  - 전세가율/준공 물량 등 대상별 지표
- 커뮤니티 반응 추이
  - source별 mentions
  - 기대/우려 비율
  - 원문 요약
- 신호 신뢰도
- 시간대별 변화
- 근거 링크 후보

### 11.3 ERD 매핑

- `real_estate_targets`: 대상 정본
- `real_estate_regions`, `real_estate_complexes`: 지역/단지 상세 속성
- `real_estate_aliases`: 검색/크롤링 별칭
- `reaction_snapshots`: 기간별 반응 요약
- `reaction_snapshot_issues`: 쟁점 비율
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

공통 shell의 상단 반응 strip과 오른쪽 rail은 정적 mock 문구를 두지 않는다. 로그인/사용자 저장 기능이 열리기 전에는 `GET /api/realestate/reactions/rankings?type=region&windowMinutes=1440&limit=6` 응답을 우선 사용하고, 응답이 비면 `수집 전/insufficient`, 실패하면 `reaction API 오류`를 표시한다.

### 12.1 상태 배지

| 배지 | 의미 | 표시 위치 |
| --- | --- | --- |
| `mock` | fixture 또는 검증 전 데이터 | 모든 카드 |
| `stale` | 공개 지연 또는 갱신 기준 초과 | 지표, 실거래, 매물, 뉴스 |
| `실시간 아님` | 수집/공개 지연 가능 | 대시보드, 지도, 지표 |
| `표본 부족` | sample count 부족 | 지도, 리포트, 지표 |
| `부동산 자문 아님` | 법적/서비스 경계 | 대시보드, footer, 관심 지역 |

### 12.2 기간 탭

- `주`
- `월`
- `6개월`
- `년`

지도는 현재 `1주`, `1개월`, `6개월`만 쓴다. 대시보드/지표와 period key를 통일할 때는 `week`, `month`, `halfYear`, `year`를 권장한다.

### 12.3 리포트 패널

지도와 상세 화면의 리포트는 같은 정보 구조를 공유한다.

- 한줄 요약
- 데이터 상태
- 반응 요약
- 쟁점 matrix
- 시장 fact
- 근거 링크
- 다음 확인 항목

### 12.4 근거 링크 row

근거 링크는 출처 이름, 문서/게시글 제목, URL, 상태, 관련 target, confidence를 가져야 한다.

ERD 후보:

- 뉴스/리포트: `content_items`, `content_target_links`
- 커뮤니티 원문: `community_posts`, `real_estate_mentions`
- AI 근거: `evidence_log_items`

## 13. 화면별 우선순위

1. 대시보드
   - 서비스의 첫인상과 전체 정보 구조를 결정한다.
   - API가 늦어도 fixture shape를 먼저 고정해야 한다.
2. 지도
   - 부동산 서비스만의 차별점이다.
   - `map_features`, `map_layer_snapshots`, 지역 hierarchy API가 먼저 필요하다.
3. 지역 반응
   - 커뮤니티 수집/분석 결과가 가장 직접적으로 드러나는 화면이다.
   - ranking snapshot과 evidence log 계약이 중요하다.
4. 주요 지표
   - 공공데이터 연결 전에는 mock/stale 표시를 강하게 유지한다.
5. 뉴스룸
   - 크롤링 출처가 늘어날수록 중요도가 커진다.
6. 관심 지역
   - 로그인/사용자 기능이 붙기 전까지는 demo/watchlist 성격으로 둔다.
7. 지역/단지 상세
   - 지도와 지역 반응에서 클릭해 들어가는 최종 리포트다.

## 14. 구현 체크리스트

- [x] 화면 route의 `targetId`를 DB의 `target_id`와 같은 값으로 고정
- [ ] 대시보드 summary API fixture shape 확정
- [x] 지도 전국/시군구 API shape 확정
- [x] 동/단지 상세 카카오맵 SDK 내장 지도 prototype 확정
- [ ] `mock`, `stale`, `unknown`, `low_sample` 상태 표시 공통화
- [ ] 상승 빨강, 하락 파랑 색상 토큰 공통화
- [ ] 뉴스/리포트/커뮤니티 링크의 출처 icon fallback 정리
- [ ] 지역/단지 상세의 evidence log 구조 확정
- [ ] 관심 지역은 로그인 전 reaction ranking 관심 후보와 로그인 후 실제 사용자 저장 상태 분리

## 15. 아직 결정이 필요한 부분

- 공공데이터 provider별 실제 갱신 주기와 stale 기준
- 네이버 카페, 다음 카페 등 커뮤니티 수집 가능 범위와 robots/terms 검토 결과
- 지역/생활권/단지군/단지의 target type 명명 규칙
- 지도 drilldown에서 단지 좌표를 언제부터 노출할지
- `부동산 투기 과열 지표` 산식
- AI 리포트의 confidence 산식과 근거 노출 최소 단위
- 상세 화면에서 유사 과거 비교를 별도 섹션으로 넣을지 여부

## 16. 검증 기준

- 배포 화면 기준으로 모든 주요 route가 접근 가능해야 한다.
- 대시보드에서 각 상세 링크가 올바른 route로 이동해야 한다.
- 지도는 전국, 지역 상세, 리포트 패널 상태가 구분되어야 한다.
- 지역 반응은 종합, 순위, 반응, 근거 로그 탭이 URL query로 식별되어야 한다.
- 주요 지표는 전체 화면과 카테고리 상세 화면이 분리되어야 한다.
- 뉴스룸은 `feed`와 `page` query로 목록 상태가 표현되어야 한다.
- 모든 화면은 mock/stale/asOf/provider 상태를 숨기지 않아야 한다.
- 가격 상승/긍정은 빨강, 하락/우려는 파랑으로 일관되어야 한다.
