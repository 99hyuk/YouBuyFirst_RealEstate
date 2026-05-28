# 커뮤니티 통합 지표와 모의 전략 설계

이 문서는 커뮤니티 수집, 통합 지표, RAG/벡터DB, 백테스팅, 모의 에이전트의 경계를 한곳에 묶는 기준입니다. 공개 제품에서는 특정 커뮤니티를 직접 비교하거나 특정 커뮤니티 전용 판단 주체를 만들지 않고, 내부 분석에서는 source별 차이와 coverage를 보정 근거로 사용합니다.

## 2026-05-28 결정 요약

- 공개 대표값은 `종합 커뮤니티 반응`과 `개미 심리 지수`입니다.
- FMKOREA, DCINSIDE, PPOMPPU, NAVER 등 source별 데이터는 통합 지표의 입력입니다. 공개 화면에서 source별 성향, source별 수익률, source별 우열을 직접 노출하지 않습니다.
- FMKOREA 전용 에이전트, DC 전용 에이전트처럼 source별 판단 주체를 만들지 않습니다. 하나의 통합 커뮤니티 에이전트가 같은 입력 contract와 같은 전략 버전을 사용합니다.
- source별 slice 실험은 내부 검증용입니다. 예를 들어 같은 전략을 FMKOREA-only, DC-only 입력으로 돌려볼 수는 있지만, 사용자 화면에서는 `반응 일관성`, `표본 신뢰도`, `소스 편중 주의`처럼 압축합니다.
- FMKOREA는 로컬 개인 지표용 source로만 다루며, 수집이 허용된 로컬 환경에서도 HTTP 목록 요청을 먼저 보내지 않고 브라우저 렌더링으로만 접근합니다.
- `매수/매도 추천`, `수익 보장`, `이 전략을 따라라`처럼 투자 행동을 유도하는 표현은 쓰지 않습니다. 백테스팅과 에이전트 결과는 `모의`, `관찰`, `과거 검증`, `전략 실험`으로 표현합니다.

## 공개 노출과 내부 분석 경계

공개 화면에 노출하는 값:

- `종합 커뮤니티 반응`: 종목/window 단위의 하나의 결론
- `개미 심리 지수`: 여러 커뮤니티 반응을 압축한 0-100 관찰 지표
- `언급 급증`, `반응 방향`, `주요 쟁점`, `반응 일관성`, `확산 강도`, `신뢰도`
- `표본 부족`, `소스 편중`, `수집 지연`, `가격 지연` 같은 주의 배지
- 모의 전략의 과거 성과 요약과 리스크 지표

내부 분석으로만 두는 값:

- source별 mood, source별 mention count, source별 coverage
- source별 normalization factor, cap, baseline distribution
- source-only forward return 실험
- crawler별 접근 방식과 차단/부분 수집 상태

노출하지 않는 값:

- `FMKOREA 반응은 낙관`, `DC 반응은 비관`처럼 커뮤니티 이름별 성향 비교
- `FMKOREA 전략 수익률 1위`처럼 특정 source를 투자법처럼 보이게 하는 문구
- `FMKOREA 에이전트`, `DC 에이전트` 같은 source 전용 판단 주체

## 통합 지표 보정 원칙

커뮤니티별 사용자 수와 글 수가 다르므로 raw mention count를 단순 합산하지 않습니다. baseline 단계에서는 아래 입력을 함께 사용합니다.

- source 내부 최근 평균 대비 증가율
- source 내부 percentile 또는 z-score
- source별 최대 기여도 cap
- coverage 상태와 stale 여부
- 인기글/개념글/추천글 같은 확산 관찰 여부
- 반응 방향 비율과 표현 강도
- 같은 종목에 대한 source 다양성

임베딩과 클러스터링은 이 보정을 대체하지 않습니다. 통계 보정 위에 의미 기반 `issueMix`를 얹어 지표 품질을 높이는 분석 레이어입니다.

## issueMix, 벡터DB, RAG

`issueMix`는 종목/window 안의 글을 의미가 비슷한 쟁점으로 묶은 구조입니다. 예시는 다음과 같습니다.

```text
종합 커뮤니티 반응: 혼조
개미 심리 지수: 61

주요 쟁점
- 실적 기대 42%
- 유상증자 우려 28%
- 단타/밈성 언급 18%
- 테마 엮임 12%
```

벡터DB는 MVP 필수 저장소가 아닙니다. 먼저 Python batch에서 임베딩/클러스터링 실험을 하고, 아래 기능이 필요해질 때 Qdrant, pgvector 같은 저장소를 검토합니다.

- 현재 window와 비슷한 과거 커뮤니티 반응 검색
- 비슷한 `issueMix`를 가진 다른 종목 검색
- 같은 이슈가 여러 source로 퍼진 흐름 검색
- 사용자 질문형 분석
- 모의 에이전트 판단 로그의 과거 유사 사례 근거

RAG는 수익률을 계산하거나 종목을 식별하는 기능이 아닙니다. 검색된 과거 window, forward return, issueMix, 뉴스/공시 metadata를 AI 입력으로 넣어 설명을 만드는 방식입니다.

RAG가 맡는 일:

- 지금 반응과 비슷했던 과거 window를 요약
- 비슷한 반응 이후 1시간/24시간/7일 수익률 분포를 설명
- 개미 심리 지수가 왜 높거나 낮게 나왔는지 근거를 정리
- 백테스트 결과가 특정 구간에서 왜 좋거나 나빴는지 해석

RAG가 맡지 않는 일:

- 종목 식별 정본
- 실시간 수집 여부 판단
- forward return과 백테스트 수익률 계산
- 주문, 체결, 원장 정합성

## 백테스팅과 나만의 모의 전략

백테스팅은 가능하며 이 제품의 핵심 검증 기능 후보입니다. 다만 공개 표현은 `나만의 투자법 추천`이 아니라 `나만의 모의 전략`, `커뮤니티 반응 기반 전략 실험`, `과거 성과 비교`로 둡니다.

기본 흐름:

```text
StockReactionWindow
+ quote/chart candle
+ issueMix
+ 개미 심리 지수
+ coverage/reliability
→ strategy rule 적용
→ 가상 진입/청산 이벤트 계산
→ forward return / MDD / 승률 / 거래 횟수 저장
→ 전략 성과표와 리스크 요약
```

전략 rule 후보:

- 개미 심리 지수 급등 종목 추종
- 과열과 부정 반응이 동시에 증가한 종목 역추종
- `issueMix`에서 실적 기대 비중이 높고 반응 일관성이 높은 종목 관찰
- 언급량은 급증했지만 가격 반응이 약한 종목 관찰
- 특정 window 이후 1시간, 6시간, 24시간, 3일, 7일 forward return 비교

전략 저장 후보:

- `strategyId`
- `strategyVersion`
- `ruleJson`
- `createdBy`
- `universe`
- `rebalanceWindow`
- `entryRule`
- `exitRule`
- `riskRule`
- `dataRequirements`

성과 저장 후보:

- `BacktestRun`
- `StrategyPerformanceSnapshot`
- `ForwardReturn`
- `maxDrawdown`
- `winRate`
- `tradeCount`
- `coverageRequirementMet`
- `dataQuality`

## 충돌 검토 결과

정리하면서 확인한 충돌과 처리 기준입니다.

- 기존 `커뮤니티별 수익률 비교 에이전트` 표현은 source별 전용 에이전트로 읽힐 수 있습니다. `통합 지표 기반 모의 성과 검증`과 `내부 source-slice 실험`으로 분리합니다.
- 기존 `에펨코리아 추종 전략` 같은 표현은 FMKOREA 전용 투자법처럼 보일 수 있습니다. 공개 제품에서는 쓰지 않고 내부 실험명으로만 둡니다.
- 기존 UI의 `커뮤니티별 반응 비교`는 crawler source를 드러내는 화면으로 읽힐 수 있습니다. 공개 화면은 `반응 일관성`, `소스 편중 주의`, `표본 신뢰도`로 압축합니다.
- 기존 `sourceMoods` API는 운영/내부 분석에는 유지할 수 있지만, 사용자-facing 필드명으로 그대로 쓰지 않습니다.
- 벡터DB와 RAG는 실시간 matcher나 백테스트 계산기가 아닙니다. `collect -> match -> classify -> aggregate -> issueMix -> similar-window/RAG` 순서를 유지합니다.

## 구현 순서

1. `StockReactionWindow` 저장 모델과 30분 통합 지표 contract를 확정합니다.
2. 1시간, 6시간, 24시간, 3일, 7일 `ForwardReturn`을 저장합니다.
3. deterministic 백테스트 엔진과 `strategy rule JSON`을 설계합니다.
4. 전략 성과표와 리스크 지표를 계산합니다.
5. 임베딩/클러스터링 batch로 `issueMix`를 만듭니다.
6. 유사 window 검색이 실제 제품 기능이 될 때 벡터DB를 도입합니다.
7. RAG는 유사 사례와 백테스트 결과를 설명하는 레이어로 붙입니다.
