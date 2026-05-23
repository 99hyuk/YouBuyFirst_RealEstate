# indicator

## 역할

커뮤니티 반응과 시장 데이터를 제품에서 읽을 수 있는 지표로 바꿉니다. 이 도메인은 너나사의 핵심 가치인 열기 지수, 개미 심리 지수, 30분 snapshot, 유사 상황 검색을 소유합니다.

## 담당 범위

- 열기 지수 산식
- 개미 심리 지수 산식과 신뢰도 배지 입력
- 30분 indicator snapshot
- AI 3줄 요약 입력 데이터
- 커뮤니티별 신호와 이후 수익률 비교용 원천 지표
- `CommunitySignal`, `ForwardReturn`, `CommunityPerformanceSnapshot`
- 커뮤니티 반응 토픽 클러스터와 과거 유사 상황 검색 후보
- `CommunityTopicCluster` 후보: `symbol`, `windowStart`, `windowEnd`, `label`, `summary`, `postCount`, `representativePostIds`, `sentimentMix`, `confidence`
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

1. 30분 집계 산식 검증 테스트 추가
2. 열기 지수 산식 문서화
3. 개미 심리 지수 산식 문서화
4. 커뮤니티별 성과 비교용 snapshot 모델 설계
5. 커뮤니티 토픽 클러스터링 실험 범위 정리
6. 종목 상세 팩트폭격 헤드라인에 넣을 지표 evidence schema 후보 정리

## 임베딩/클러스터링 적용 원칙

- 먼저 글/댓글 수집, 종목 매칭, 반응 방향 분류, 30분 집계를 안정화합니다.
- 임베딩은 실시간 종목 인식의 정본으로 쓰지 않고, 이미 매칭된 글을 의미 단위로 묶는 분석 레이어로 둡니다.
- 초기에는 벡터DB 없이 window 단위 batch에서 임베딩과 클러스터링을 실험하고, 토픽 라벨/대표 글/감정 비율/신뢰도만 저장합니다.
- 벡터 저장소는 과거 유사 상황 검색, 사용자 질문형 분석, RAG, 유사 이슈 확산 추적이 실제 제품 기능으로 필요해질 때 도입합니다.
- 벡터 검색의 1차 대상은 개별 원문 전체가 아니라 30분 window, 토픽 클러스터, 대표 snippet, 뉴스/공시/이벤트 metadata처럼 재현 가능한 근거 단위입니다.

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
