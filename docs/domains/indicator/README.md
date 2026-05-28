# indicator

## 역할

커뮤니티 반응과 시장 데이터를 제품에서 읽을 수 있는 지표로 바꿉니다. 이 도메인은 너나사의 핵심 가치인 열기 지수, 개미 심리 지수, 30분 snapshot, 유사 상황 검색을 소유합니다.

## 담당 범위

- 열기 지수 산식
- 개미 심리 지수 산식과 신뢰도 배지 입력
- 30분 indicator snapshot
- AI 3줄 요약 입력 데이터
- 통합 커뮤니티 반응과 이후 수익률 비교용 원천 지표
- `StockReactionWindow`, `ForwardReturn`, `BacktestRun`, `StrategyPerformanceSnapshot`
- 커뮤니티 반응 토픽 클러스터와 과거 유사 상황 검색 후보
- `StockReactionWindow` 후보: `symbol`, `windowStart`, `windowEnd`, `overallDirection`, `directionScore`, `confidence`, `mentionCount`, `issueMix`
- `ReactionIssue` 후보: `label`, `share`, `contributionDirection`, `summary`, `representativePostIds`, `confidence`
- 종목 상세 팩트폭격 헤드라인에 제공할 `stockHealthScore`와 지표 근거 후보

## 파일 소유권

주로 담당:

- `pipeline/src/youbuyfirst_pipeline/llm.py`
- `analysis`, `indicator` 관련 backend domain
- indicator API

공유 전 협의:

- crawler raw payload
- stock alias/matcher contract
- quote provider contract
- dashboard API contract
- stock detail roast headline API contract
- agent decision input contract
- simulation order/portfolio schema

## 현재 우선순위

1. 30분 baseline snapshot을 기준으로 열기 지수 산식 문서화
2. 개미 심리 지수 산식 문서화
3. 1일/1주 window 집계 확장 범위 정리
4. 통합 지표 기반 성과 비교용 snapshot 모델 설계
5. 커뮤니티 토픽 클러스터링 실험 범위 정리
6. 종목 상세 팩트폭격 헤드라인에 넣을 지표 evidence schema 후보 정리

## 구현된 snapshot

`GET /api/indicators/community-snapshots?windowStart=2026-05-27T00:00:00Z`는 저장된 커뮤니티 글, 종목 mention, 반응 방향 분석을 30분 window로 다시 읽어 baseline snapshot을 계산합니다. `windowMinutes`는 기본 30분이며, 탐색용으로 1분부터 10,080분까지 지정할 수 있습니다.

응답은 다음 묶음을 제공합니다.

- `freshness`: 원천 테이블 묶음, `asOf`, 최신 글 작성 시각, stale 여부와 이유
- `marketMood`: window 전체 mention 수, 낙관/비관/중립 count, net sentiment
- `sourceMoods`: source와 board별 mention 수, 반응 방향 count, top keywords
- `stockMentionCounts`: `instrumentId`, market, symbol, 이름, mention 수, 반응 방향 count, top keywords
- `topKeywords`: window 전체 제목/snippet 기반 상위 키워드

이 snapshot은 원천 데이터를 새로 수집하지 않습니다. 수집 주기는 community layer가 관리하고, indicator layer는 이미 저장된 데이터를 window 단위로 해석합니다. `asOf`는 window 안의 글 `crawledAt`과 반응 분석 `analyzedAt` 중 최신 시각입니다. `asOf`가 없거나 `windowEnd`보다 이르면 `stale=true`로 표시해, 아직 해당 window를 끝까지 처리하지 못한 값과 완료된 과거 snapshot을 구분합니다.

`sourceMoods`는 내부 분석과 운영 검증용 필드입니다. 사용자-facing API나 화면에서는 source 이름별 성향 비교를 그대로 노출하지 않고, `반응 일관성`, `소스 편중 주의`, `표본 신뢰도`, `coverage` 같은 압축 지표로 변환합니다.

## 통합 지표와 source 보정

커뮤니티별 글 수와 사용자 수가 다르므로 raw count를 단순 합산하지 않습니다. `개미 심리 지수`와 `종합 커뮤니티 반응`은 source별 baseline, 내부 percentile, 최근 평균 대비 증가율, coverage, stale 여부, source별 최대 기여도 cap을 함께 봅니다.

FMKOREA, DCINSIDE, PPOMPPU, NAVER 같은 source별 반응은 통합 지표의 입력입니다. 특정 source가 항상 맞는다는 식의 공개 결론을 만들지 않고, source-only 성과 실험은 내부 검증 데이터로만 둡니다.

## 임베딩/클러스터링 적용 원칙

- 먼저 글/댓글 수집, 종목 매칭, 반응 방향 분류, 30분 집계를 안정화합니다.
- 단순 낙관/비관/중립 count는 baseline signal입니다. 지표의 최종 신뢰도는 count만으로 확정하지 않고, 의미적으로 묶인 쟁점 구조, 확산도, 대표 근거, 표본/소스 신뢰도를 함께 봅니다.
- 임베딩은 실시간 종목 인식의 정본으로 쓰지 않고, 이미 매칭된 글을 의미 단위로 묶어 `issueMix`와 과거 유사 window를 만드는 핵심 분석 레이어로 둡니다.
- 사용자 화면의 1차 결론은 종목/window 단위 `overallDirection` 하나로 둡니다. 토픽/쟁점은 그 결론을 설명하는 `issueMix` 비율로 보여주며, 쟁점별 방향성은 내부 계산이나 보조 배지로만 둡니다.
- 초기에는 벡터DB 없이 window 단위 batch에서 임베딩과 클러스터링을 실험하고, 쟁점 라벨/비율/확산도/대표 글/요약/신뢰도만 저장합니다.
- 벡터 저장소는 과거 유사 상황 검색, 사용자 질문형 분석, RAG, 유사 이슈 확산 추적이 실제 제품 기능으로 필요해질 때 도입합니다.
- 벡터 검색의 1차 대상은 개별 원문 전체가 아니라 30분 window의 종합 반응, 쟁점 비율, 대표 snippet, 뉴스/공시/이벤트 metadata처럼 재현 가능한 근거 단위입니다.
- RAG는 종목 식별, 수익률 계산, 백테스트 체결 계산을 대신하지 않습니다. 검색된 과거 window, `ForwardReturn`, `issueMix`, 뉴스/공시 metadata를 바탕으로 사용자가 읽을 수 있는 해석과 근거 요약을 만듭니다.

## 종합 반응과 쟁점 비율

오픈마켓 리뷰에서 `제품 평판: 부정 우세`와 `배송 지연 45%, 품질 불량 27%`를 분리하듯이, 너나사는 종목별 커뮤니티 반응도 결론과 이유를 분리합니다.

예시:

```text
종합 커뮤니티 반응: 낙관 우세

주요 쟁점
- AI 수혜 기대 38%
- 기관 수급 기대 24%
- 단기 고점 부담 19%
- 실적 확인 대기 12%
```

`overallDirection`은 사용자가 먼저 읽는 결론입니다. `issueMix`는 결론을 만든 쟁점의 비율이며, 각 쟁점의 `contributionDirection`은 산식과 색상 보조에 쓰되 화면의 큰 텍스트 결론으로 반복하지 않습니다.

`개미 심리 지수`는 이 구조 위에서 계산합니다. 초기에는 언급량 변화, 반응 방향 비율, 표현 강도, 인기글 확산, 소스 다양성, 표본 수 신뢰도를 baseline으로 쓰되, 고도화 단계에서는 `issueMix`의 쟁점 비율과 확산도, 대표 근거 품질, 과거 유사 window 비교를 점수와 confidence에 반영합니다.

## 다른 도메인과의 접점

- `stock`: 모든 snapshot은 stock domain의 symbol 기준을 씁니다.
- `community`: 수집/분류된 반응 데이터를 입력으로 받습니다.
- `market`: quote, chart, investor flow를 보조 근거로 받을 수 있습니다.
- `agent`: 지표 snapshot과 유사 상황 검색 결과를 판단 입력으로 넘깁니다.
- `layers/ui`: 점수와 신뢰도, 표본 수, 기간을 함께 표시합니다.

## 하지 않는 일

- 크롤러 우회 전략
- 시세 provider 직접 연동
- 모의 주문 체결
- AI 매매 판단과 페르소나 실행
- UI 레이아웃 구현
