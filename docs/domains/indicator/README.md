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

1. expectation/concern/neutral baseline 산식 정리
2. 1일/1주/1개월 window 집계 범위 정리
3. 표본 수, source 다양성, source skew, stale 기준을 confidence 산식에 반영
4. 유사 과거 상황 검색 후보 데이터 모델 정리

현재 구현:

- `real_estate_reaction_snapshots`, `real_estate_reaction_snapshot_issues`를 window 단위 중간 결과 테이블로 둡니다.
- `POST /internal/realestate/reaction-snapshots`는 pipeline/AI 분류기가 계산한 snapshot을 upsert하는 내부 입구입니다.
- `GET /api/realestate/reactions/rankings?type=&windowStart=&windowMinutes=`는 화면용 랭킹을 반환합니다. `windowStart`가 없으면 해당 target type의 최신 window를 사용합니다.
- `GET /api/realestate/targets/{targetId}/reaction-snapshot?windowStart=&windowMinutes=`는 지역/단지 상세와 지도 리포트 패널용 단일 target snapshot을 반환합니다. `windowStart`가 없으면 해당 target의 최신 window를 사용합니다.
- `GET /api/realestate/targets/{targetId}/reaction-graph?direction=&edgeType=&windowStart=&windowMinutes=`는 target graph edge와 연결 대상별 snapshot을 함께 반환합니다. 지도 drill-down, 하위 지역 비교, 관련 영향권 후보 패널의 입력입니다.
- 이 공개 API들은 집계 산식을 수행하지 않고, 이미 계산된 snapshot을 읽어 사용자 화면에 필요한 ratio, issueMix, freshness 형태로 변환합니다.
- pipeline은 분류된 관측치 JSONL을 `realestate-reaction-snapshots` 명령으로 window snapshot payload로 변환하고, `realestate-reaction-snapshots-push` 명령으로 내부 API에 전송합니다.
- 제한 게시글 JSONL과 alias JSONL이 있을 때는 `realestate-reaction-snapshots-from-posts` 명령으로 매칭, 1차 반응 분류, snapshot 집계를 한 번에 실행할 수 있습니다.
- `serve` 모드에서는 `--enable-realestate-reaction-snapshots-refresh`를 켜면 같은 흐름을 주기적으로 실행하고 내부 snapshot API로 전송합니다.
- `--realestate-target-edges-jsonl` 또는 `--realestate-use-backend-target-edges`를 쓰면 `approved contains` target edge 기준으로 하위 지역/단지 관측치를 상위 target snapshot에 roll-up합니다.
- `realestate-similar-windows` 명령은 이미 만들어진 reaction snapshot payload를 읽어 현재 window와 과거 window의 유사도를 계산합니다. 아직 VectorDB를 쓰지 않는 batch 기준이며, 반응 방향, 언급 증가, heat score, issue overlap을 함께 봅니다.
- `--similar-market-facts-jsonl`을 함께 주면 과거 후보 window 이후 `apt_trade`, `apt_rent`, 공시가격, 미분양, 가격지수 등 market fact 변화 요약을 붙입니다. 이 요약은 "비슷한 반응 이후 실제 지표가 어떻게 움직였는지"를 보여주는 후보 근거이며 원인 단정이 아닙니다.

초기 pipeline 집계 기준:

- 입력 관측치 필수값은 `targetType`, `targetId`, `publishedAt`, `source`, `reactionDirection`입니다. `reactionDirection`은 `expectation`, `concern`, `neutral`을 기본값으로 씁니다.
- 현재 window는 `[windowStart, windowEnd)`로 계산하고, 직전 window의 같은 target 언급 수를 `previousMentionCount`로 둡니다.
- 주기 refresh job은 실행 시각 기준 완료된 직전 window를 집계합니다. 예를 들어 01:02에 60분 window면 00:00-01:00 구간을 집계합니다.
- roll-up은 원본 관측치를 제거하지 않고 파생 관측치를 추가합니다. 상위 target에는 하위 target의 분위기가 합산되고, 직접 언급 여부는 `target_graph:contains` 메타로 구분합니다.
- `expectationScore`, `concernScore`, `neutralScore`는 현재 window 안의 방향별 비율을 0-100 점수로 저장합니다.
- `sourceSkew`는 가장 큰 source 기여도이며, `confidence`는 언급 수, source 수, source 편중도를 함께 보는 1차 산식입니다.
- `coverageStatus`는 `low_sample`, `source_skewed`, `stale`, `partial`을 우선 사용합니다. `low_sample`은 표본 3건 미만, `source_skewed`는 특정 source 비중이 80% 이상, `stale`은 최신 관측치가 `--reaction-stale-after-minutes`보다 오래된 경우입니다.
- stale snapshot은 confidence에 추가 패널티를 줍니다. 기본 지연 기준은 360분이며, CLI와 serve 모드에서 `--reaction-stale-after-minutes`로 조정합니다.
- `issueMix`는 관측치의 `issues` 배열을 `issueKey`, `label`, `direction` 기준으로 묶어 share와 평균 confidence를 계산합니다.

초기 유사 과거 검색 기준:

- 입력은 `realestate-reaction-snapshots`가 출력하는 snapshot payload입니다.
- source window보다 과거인 snapshot만 후보로 삼고, 같은 target/window 자기 자신은 제외합니다.
- 점수는 반응 방향 비율 40%, heat score 20%, issue overlap 25%, 언급 증가 패턴 15%로 계산합니다.
- `similarityScore`는 유사도 정렬용 후보 점수이며 관심도, 가격 상승 가능성, 투자 판단 점수가 아닙니다.
- 출력의 `evidenceItem`은 EvidenceLog 저장 API에 `evidenceType=similar_window`, `refType=similar_window`로 넣을 수 있는 형태입니다.

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
