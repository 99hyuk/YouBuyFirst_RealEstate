# indicator

## 역할

커뮤니티 반응과 부동산 시장 사실 데이터를 제품에서 읽을 수 있는 지표로 바꿉니다. 이 도메인은 지역/단지 반응 지표, window snapshot, 쟁점 비율, 표본 신뢰도, 유사 상황 검색 후보를 소유합니다.

## 담당 범위

- 지역/단지별 언급량 변화
- 기대/우려/중립 baseline 산식
- `RealEstateReactionSnapshot`
- 쟁점 비율 `issueMix`
- 표본 신뢰도, source skew, 수집 지연 배지 입력
- 유사 과거 상황 검색 후보
- 에이전트 근거 로그에 제공할 지표 evidence

## 후보 모델

`RealEstateReactionSnapshot` 후보:

- `targetType`
- `targetId`
- `windowStart`
- `windowEnd`
- `mentionCount`
- `expectationScore`
- `concernScore`
- `overallReaction`
- `confidence`
- `issueMix`
- `sourceCount`
- `sourceSkew`
- `stale`

`ReactionIssue` 후보:

- `label`
- `share`
- `direction`
- `summary`
- `representativePostIds`
- `confidence`

## 파일 소유권

주로 담당:

- `analysis`, `indicator` 관련 backend domain
- indicator API
- LLM/embedding 기반 쟁점 분류 후보

공유 전 협의:

- crawler raw payload
- realestate alias/matcher contract
- market fact provider contract
- dashboard API contract
- target detail API contract
- agent evidence input contract

## 현재 우선순위

1. `RealEstateReactionSnapshot` 응답 shape 설계
2. expectation/concern/neutral baseline 산식 정리
3. issueMix 후보 라벨과 confidence 기준 정리
4. 1일/1주/1개월 window 집계 범위 정리
5. 표본 수, source 다양성, source skew, stale 기준 분리
6. 유사 과거 상황 검색 후보 데이터 모델 정리

## snapshot 해석 기준

snapshot은 원천 데이터를 새로 수집하지 않습니다. 수집 주기는 community layer가 관리하고, indicator layer는 이미 저장된 데이터를 window 단위로 해석합니다.

필수 freshness 필드:

- 원천 테이블 묶음
- `asOf`
- 최신 글 작성 시각
- stale 여부와 이유
- coverage 상태

source별 mood는 내부 분석과 운영 검증용 필드입니다. 사용자-facing API나 화면에서는 source 이름별 성향 비교를 그대로 노출하지 않고, `반응 일관성`, `소스 편중 주의`, `표본 신뢰도`, `coverage` 같은 압축 지표로 변환합니다.

## 통합 지표와 source 보정

커뮤니티별 글 수와 사용자 수가 다르므로 raw count를 단순 합산하지 않습니다. 지역/단지 반응 지표는 source별 baseline, 내부 percentile, 최근 평균 대비 증가율, coverage, stale 여부, source별 최대 기여도 cap을 함께 봅니다.

특정 source가 항상 맞는다는 식의 공개 결론을 만들지 않고, source-only 실험은 내부 검증 데이터로만 둡니다.

## 임베딩/클러스터링 적용 원칙

- 먼저 글/댓글 수집, 지역/단지 매칭, 반응 방향 분류, window 집계를 안정화합니다.
- 단순 기대/우려/중립 count는 baseline signal입니다.
- 임베딩은 실시간 지역/단지 인식의 정본으로 쓰지 않고, 이미 매칭된 글을 의미 단위로 묶어 `issueMix`와 과거 유사 window를 만드는 분석 레이어로 둡니다.
- 사용자 화면의 1차 결론은 target/window 단위 `overallReaction` 하나로 둡니다.
- 토픽/쟁점은 그 결론을 설명하는 `issueMix` 비율로 보여주며, 쟁점별 방향성은 내부 계산이나 보조 배지로만 둡니다.
- 초기에는 벡터DB 없이 window 단위 batch에서 임베딩과 클러스터링을 실험합니다.
- 벡터 저장소는 과거 유사 상황 검색, 사용자 질문형 분석, RAG, 유사 이슈 확산 추적이 실제 제품 기능으로 필요해질 때 도입합니다.

## 다른 도메인과의 접점

- `realestate`: 모든 snapshot은 region/complex target 기준을 씁니다.
- `community`: 수집/분류된 반응 데이터를 입력으로 받습니다.
- `agent`: 지표 snapshot과 유사 상황 검색 결과를 평가 입력으로 넘깁니다.
- `layers/ui`: 점수와 신뢰도, 표본 수, 기간을 함께 표시합니다.

## 하지 않는 일

- 크롤러 우회 전략
- 실거래/전세/매물 provider 직접 연동
- 매수, 매도, 청약, 대출 행동 판단
- UI 레이아웃 구현
