# front route inventory 설계

작성일: 2026-05-15
트랙: `front`
작업 타입: `docs`
브랜치: `codex/front-route-inventory`

## 목적

이번 작업은 너나사 (YouBuyFirst)의 첫 프론트 구현 전에 화면 지도를 만든다. 구현 대상은 Vue 프로젝트 생성이 아니라, 다음 `Vue 3 + Vite + TypeScript` 와이어프레임 shell PR이 바로 따라갈 수 있는 route-first 인벤토리다.

이 문서는 화면 주소, 화면 목적, 필요한 mock data, API 응답 후보, 상태 표현, 기획자 확인 필요 항목을 한곳에 둔다. 실제 API 계약, 차트 라이브러리, 최종 디자인 시스템은 후속 PR에서 다룬다.

## 설계 선택

선택한 접근은 `Route-first`다.

먼저 사용자가 이동할 화면과 URL을 정하고, 각 화면이 소비할 정보와 mock/API 후보를 붙인다. 지금 저장소에는 프론트 패키지가 없기 때문에, route-first 문서는 다음 PR의 `routes.ts`, page shell, fixture 파일 이름을 가장 직접적으로 안내한다.

검토한 대안은 아래와 같다.

| 접근 | 장점 | 이번 PR에서 제외한 이유 |
| --- | --- | --- |
| `Data-contract-first` | data, market, trade, agent 트랙과 API 계약 논의가 쉽다. | 화면 골격이 아직 없어서 첫 Vue shell의 입력이 덜 선명하다. |
| `Storyboard-first` | 사용자의 투자 아이디어 탐색 흐름을 설명하기 좋다. | 바로 구현할 route와 fixture 단위가 route-first보다 늦게 드러난다. |

## 범위

포함한다.

- 사용자용 프론트 route 후보
- 화면별 목적과 핵심 위젯 후보
- 화면별 mock fixture 후보
- 화면별 API 응답 후보와 소유 트랙
- 로딩, 오류, 빈 상태 표현 기준
- `기획자 확인 필요` 항목
- 다음 Vue shell PR의 입력 파일 후보

제외한다.

- Vue 프로젝트 생성
- 실제 화면 구현
- 고충실도 디자인, 브랜드 컬러, 일러스트 확정
- 차트 라이브러리 확정
- backend API, DB schema, pipeline 변경
- 실제 투자 자문처럼 보이는 문구 확정

## Route map

초기 route는 최종 기능 전체를 모두 구현한다는 뜻이 아니라, 화면 골격과 mock 데이터를 나눌 기준이다. 실제 노출 여부는 후속 Vue shell PR에서 mock mode와 disabled state로 제어한다.

| route | 화면 이름 | 주 목적 | 초기 노출 상태 |
| --- | --- | --- | --- |
| `/dashboard` | 메인 대시보드 | 커뮤니티 반응이 큰 종목과 전체 시장 분위기를 빠르게 본다. | 기본 진입 화면 |
| `/stocks/:symbol` | 종목 상세 | 한 종목의 커뮤니티 반응, 가격, 대표 이슈를 함께 본다. | route shell |
| `/communities` | 커뮤니티 비교 | 소스별 반응 방향 분포와 커뮤니티별 성과 후보를 본다. | mock only |
| `/agents` | 에이전트 리더보드 | AI 페르소나와 커뮤니티 전략의 모의 성과를 본다. | mock only |
| `/portfolio` | 모의 포트폴리오 | 사용자 가상 자산, 주문, 수익률을 본다. | disabled shell |

`/portfolio`는 trade 도메인이 아직 없기 때문에 비활성 route shell로만 둔다. OCR 자산 연동, 인증, 실거래 연결은 이 route 설계에 포함하지 않는다.

## Page inventory

### `/dashboard`

목적: 사용자가 오늘 커뮤니티가 많이 반응하는 종목을 발견한다.

핵심 위젯 후보:

- 열기 지수 또는 언급량 급증 랭킹
- 낙관, 비관, 중립 반응 비율 요약
- 최근 1시간/24시간 변화
- stale quote 또는 quote 미연동 상태
- 원문 재게시 없이 대표 키워드와 AI 재서술 영역 placeholder

mock fixture 후보:

- `front/fixtures/dashboard-summary.json`
- `front/fixtures/reaction-ranking.json`
- `front/fixtures/quote-snapshots.json`

API 응답 후보:

- `GET /api/dashboard/summary`
- `GET /api/indicators/rankings?window=1h`
- `GET /api/quotes/latest?symbols=...`

소유 트랙:

- `data`: ranking, reaction direction ratio, indicator value
- `market`: latest quote, stale quote flag
- `front`: 표시 상태와 mock fixture

상태:

- loading: ranking과 quote 영역별 skeleton
- empty: "아직 집계된 커뮤니티 반응이 없습니다."
- error: data 실패와 quote 실패를 분리 표시

기획자 확인 필요:

- `열기 지수`라는 사용자용 이름을 그대로 쓸지
- ranking의 기본 시간창을 `1h`, `24h`, `30m` 중 무엇으로 둘지
- AI 3줄 요약 placeholder 문구

### `/stocks/:symbol`

목적: 사용자가 특정 종목의 커뮤니티 반응과 가격 상태를 함께 확인한다.

핵심 위젯 후보:

- 종목 헤더, 현재가, 등락률, stale quote badge
- 반응 방향 비율
- 언급량 추이 placeholder
- 소스별 반응 분포
- 대표 키워드와 제한 snippet 기반 재서술 placeholder

mock fixture 후보:

- `front/fixtures/stock-detail-samsung.json`
- `front/fixtures/stock-reaction-trend.json`

API 응답 후보:

- `GET /api/stocks/{symbol}/overview`
- `GET /api/stocks/{symbol}/indicators?window=24h`
- `GET /api/stocks/{symbol}/community-breakdown`
- `GET /api/quotes/latest?symbols={symbol}`

소유 트랙:

- `data`: stock overview, indicator trend, source breakdown
- `market`: quote snapshot
- `front`: 상세 화면 상태와 mock fixture

상태:

- loading: 종목 헤더와 차트 영역 분리 skeleton
- empty: 종목은 있으나 최근 반응 없음
- error: symbol 미인식, data 실패, quote 실패를 구분

기획자 확인 필요:

- 종목 검색/직접 이동을 첫 shell에 포함할지
- 원문 링크를 어디까지 노출할지
- 투자 판단으로 보이지 않는 상세 화면 고지 문구

### `/communities`

목적: 사용자가 커뮤니티별 반응과 사후 성과 비교 후보를 본다.

핵심 위젯 후보:

- 커뮤니티별 언급량과 반응 방향 분포
- 추종/역추종 전략 성과 placeholder
- 소스별 활성화 상태 badge
- 공개 배포 위험이 있는 소스의 demo-only 표시

mock fixture 후보:

- `front/fixtures/community-overview.json`
- `front/fixtures/community-performance.json`

API 응답 후보:

- `GET /api/communities/overview`
- `GET /api/communities/performance?window=7d`

소유 트랙:

- `data`: source-level reaction aggregation
- `agent`: community strategy performance, forward return summary
- `crawl`: source activation state
- `front`: 비교 화면과 source state 표시

상태:

- loading: 커뮤니티별 카드 skeleton
- empty: 비교 가능한 커뮤니티 데이터 없음
- error: 성과 데이터 미준비와 수집 상태 오류를 분리

기획자 확인 필요:

- 커뮤니티별 성과를 "맞았다/틀렸다"처럼 보이지 않게 표현하는 문구
- source activation state를 사용자에게 얼마나 자세히 보여줄지
- `public-demo-only`, `local-research-only`의 사용자용 한국어 표현

### `/agents`

목적: 사용자가 AI 페르소나와 커뮤니티 전략의 모의 성과를 비교한다.

핵심 위젯 후보:

- 에이전트별 수익률 leaderboard placeholder
- 페르소나 설명
- 최근 결정 로그 요약
- 투자 자문이 아니라 모의 실험이라는 고지

mock fixture 후보:

- `front/fixtures/agent-leaderboard.json`
- `front/fixtures/agent-decisions.json`

API 응답 후보:

- `GET /api/agents/leaderboard`
- `GET /api/agents/{agentId}/decisions`

소유 트랙:

- `agent`: persona, decision summary, performance
- `market`: 성과 계산에 필요한 quote baseline
- `front`: leaderboard와 decision log 표시

상태:

- loading: leaderboard skeleton
- empty: 아직 기록된 에이전트 결정 없음
- error: agent 데이터 미준비 상태를 명확히 표시

기획자 확인 필요:

- 에이전트 페르소나 이름
- 결정 근거의 길이와 노출 범위
- 수익률 표현이 수익 보장처럼 보이지 않게 하는 고지

### `/portfolio`

목적: 후속 trade 트랙에서 모의 포트폴리오가 생길 때 붙일 자리만 예약한다.

핵심 위젯 후보:

- 가상 예수금
- 보유 종목
- 주문 내역
- 평가 손익

mock fixture 후보:

- `front/fixtures/portfolio-disabled.json`

API 응답 후보:

- `GET /api/portfolio/summary`
- `GET /api/orders`

소유 트랙:

- `trade`: account, order, execution, portfolio
- `front`: disabled shell과 후속 연결 위치

상태:

- disabled: "모의투자 기능은 아직 준비 중입니다."

기획자 확인 필요:

- 첫 공개 화면에 portfolio tab을 보일지 숨길지
- 인증 없이 모의 포트폴리오를 어떻게 다룰지

## Mock/API candidate shape

응답 후보는 실제 backend 계약이 아니라 프론트 fixture 설계를 위한 초안이다. 후속 API 계약 PR에서 endpoint, field name, nullability를 다시 확정한다.

### `reaction-ranking`

```json
{
  "window": "1h",
  "generatedAt": "2026-05-15T08:00:00Z",
  "items": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "market": "KRX",
      "mentionCount": 128,
      "mentionDeltaPct": 42.3,
      "reactionDirectionRatio": {
        "bullish": 0.52,
        "bearish": 0.31,
        "neutral": 0.17
      },
      "heatScore": 82,
      "topKeywords": ["실적", "반도체", "외국인"],
      "quote": {
        "price": 78200,
        "changePct": 1.24,
        "stale": false
      }
    }
  ]
}
```

### `stock-detail`

```json
{
  "symbol": "005930",
  "name": "삼성전자",
  "market": "KRX",
  "quote": {
    "price": 78200,
    "changePct": 1.24,
    "stale": false,
    "updatedAt": "2026-05-15T08:00:00Z"
  },
  "reactionSummary": {
    "mentionCount": 128,
    "heatScore": 82,
    "direction": "bullish",
    "directionRatio": {
      "bullish": 0.52,
      "bearish": 0.31,
      "neutral": 0.17
    }
  },
  "sourceBreakdown": [
    {
      "source": "naver",
      "mentionCount": 84,
      "dominantDirection": "neutral"
    }
  ]
}
```

### `community-performance`

```json
{
  "window": "7d",
  "items": [
    {
      "community": "fmkorea",
      "strategyLabel": "추종 관찰",
      "signalCount": 12,
      "averageForwardReturnPct": 2.1,
      "maxDrawdownPct": -4.7,
      "dataStatus": "mock"
    }
  ]
}
```

## 다음 Vue shell PR 입력

다음 PR은 이 문서를 기준으로 최소 프론트 패키지를 만든다.

예상 파일 후보:

- `front/package.json`
- `front/vite.config.ts`
- `front/src/main.ts`
- `front/src/router/routes.ts`
- `front/src/App.vue`
- `front/src/pages/DashboardPage.vue`
- `front/src/pages/StockDetailPage.vue`
- `front/src/pages/CommunitiesPage.vue`
- `front/src/pages/AgentsPage.vue`
- `front/src/pages/PortfolioPage.vue`
- `front/src/fixtures/*.json`

다음 PR에서도 실제 API 연결은 하지 않는다. fixture/mock 기반 route shell과 기본 empty/loading/error 표시까지만 다룬다.

## 위험과 대응

| 위험 | 대응 |
| --- | --- |
| 화면 문서가 지표 정의를 임의 확정할 수 있음 | 지표 이름과 산식은 `기획자 확인 필요`로 남기고 data 트랙 계약 전에는 고정하지 않는다. |
| 투자 자문처럼 보이는 문구가 들어갈 수 있음 | 모든 성과, 에이전트, 커뮤니티 비교 표현은 모의 실험과 관찰로 제한한다. |
| market/trade/agent 기능을 front PR에 끌어올 수 있음 | 이번 PR은 route와 mock/API 후보만 다루고 구현은 각 트랙 계약 이후로 둔다. |
| 공개 배포 리스크가 있는 소스 상태를 과도하게 노출할 수 있음 | source activation state의 사용자용 표시 문구는 후속 기획 확인 항목으로 둔다. |

## 검증 기준

이번 설계 PR은 문서 PR이므로 아래를 확인하면 완료다.

- route 후보가 front 트랙 README의 초기 작업 순서와 충돌하지 않는다.
- 각 route마다 목적, mock fixture, API 후보, 소유 트랙, 상태 표현이 있다.
- `기획자 확인 필요` 항목이 화면별로 분리되어 있다.
- Vue 프로젝트 생성이나 backend/pipeline 변경이 섞이지 않는다.
- `git diff --check`가 통과한다.

## 사용자 검토 질문

사용자는 아래만 확인하면 된다.

1. 첫 화면을 `/dashboard`로 두는 것이 맞는가?
2. `/portfolio`를 처음부터 disabled shell로 예약할지, 아예 route 후보에서 빼둘지?
3. 커뮤니티 성과와 AI 에이전트 화면을 mock only 상태로 먼저 보여줄지?
4. `열기 지수`라는 화면 용어를 계속 사용할지?
