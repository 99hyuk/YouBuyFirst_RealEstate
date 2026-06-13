# 부동산 반응 지표와 유사 상황 전략

이 문서는 커뮤니티 수집, 지역/단지 반응 지표, issueMix, 유사 과거 상황 검색, 에이전트 근거 로그의 경계를 한곳에 묶는 기준입니다.

## 2026-06-01 결정 요약

- 공개 대표값은 `지역/단지 반응 지표`와 `쟁점 비율`입니다.
- source별 데이터는 지표의 입력입니다. 공개 화면에서 source별 성향, source별 우열을 직접 노출하지 않습니다.
- source별 slice 실험은 내부 검증용입니다. 사용자 화면에서는 `반응 일관성`, `표본 신뢰도`, `소스 편중 주의`, `수집 지연`처럼 압축합니다.
- 특정 매수, 매도, 청약, 대출 행동을 유도하는 표현은 쓰지 않습니다. 결과는 `관찰`, `비교`, `과거 사례`, `근거 로그`로 표현합니다.

## 공개 노출과 내부 분석 경계

공개 화면에 노출하는 값:

- `지역/단지 반응 지표`: target/window 단위의 관찰 상태
- `쟁점 비율`: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책 등
- `언급 급증`, `기대/우려`, `반응 일관성`, `확산 강도`, `신뢰도`
- `표본 부족`, `소스 편중`, `수집 지연`, `market fact stale` 같은 주의 배지
- 유사 과거 상황과 이후 시장 흐름 요약

내부 분석으로만 두는 값:

- source별 mood, source별 mention count, source별 coverage
- source별 normalization factor, cap, baseline distribution
- crawler별 접근 방식과 차단/부분 수집 상태
- provider별 원천 품질 비교

노출하지 않는 값:

- 특정 커뮤니티 이름별 성향 우열
- 특정 source를 부동산 판단법처럼 보이게 하는 문구
- 행동을 지시하는 에이전트 평가

## 통합 지표 보정 원칙

커뮤니티별 사용자 수와 글 수가 다르므로 raw mention count를 단순 합산하지 않습니다. baseline 단계에서는 아래 입력을 함께 사용합니다.

- source 내부 최근 평균 대비 증가율
- source 내부 percentile 또는 z-score
- source별 최대 기여도 cap
- coverage 상태와 stale 여부
- 인기글/댓글/조회 확산 관찰 여부
- 기대/우려/중립 비율과 표현 강도
- 같은 지역/단지에 대한 source 다양성

임베딩과 클러스터링은 이 보정을 대체하지 않습니다. 통계 보정 위에 의미 기반 `issueMix`를 얹어 지표 품질을 높이는 분석 레이어입니다.

## issueMix, 벡터DB, RAG

`issueMix`는 target/window 안의 글을 의미가 비슷한 쟁점으로 묶은 구조입니다.

```text
지역 반응 지표: 혼조
표본 신뢰도: 보통

주요 쟁점
- 교통 호재 기대 34%
- 전세 불안 26%
- 공급 우려 18%
- 학군 관심 12%
```

벡터DB는 초기 필수 저장소가 아닙니다. 먼저 Python batch에서 임베딩/클러스터링 실험을 하고, 아래 기능이 필요해질 때 Qdrant, pgvector 같은 저장소를 검토합니다.

벡터DB의 역할은 과거 유사 상황 검색입니다. 지역/단지 식별, alias matcher, 실거래가 계산, 관심도 점수 산출의 정본으로 쓰지 않습니다. 예를 들어 현재 어떤 단지에서 `전세 불안 + 재건축 기대 + 매물 감소 + 커뮤니티 언급량 증가`가 동시에 나타났다면, 과거에 비슷한 반응 패턴이 있었던 target/window를 찾고 그 이후 실거래가, 전세가, 매물 흐름을 비교하는 데 사용합니다.

- 현재 window와 비슷한 과거 반응 검색
- 비슷한 `issueMix`를 가진 다른 지역/단지 검색
- 같은 정책/교통/전세 이슈가 여러 source로 퍼진 흐름 검색
- 사용자 질문형 분석
- 에이전트 근거 로그의 과거 유사 사례 근거

RAG는 가격을 예측하거나 행동을 결정하는 기능이 아닙니다. 검색된 과거 window, market fact, issueMix, 뉴스/정책 metadata를 AI 입력으로 넣어 설명을 만드는 방식입니다.

RAG가 맡는 일:

- 지금 반응과 비슷했던 과거 window 요약
- 비슷한 반응 이후 실거래/전세/매물 흐름 설명
- 반응 지표가 왜 높거나 낮게 나왔는지 근거 정리
- 데이터 품질이 낮은 구간에서 caveat 설명

RAG가 맡지 않는 일:

- 지역/단지 식별 정본
- 실시간 수집 여부 판단
- 실거래/전세/매물 원천 계산
- 매수, 매도, 청약, 대출 행동 판단

## 최근 이슈 검색 API

SerpApi 같은 검색 API는 최신 뉴스, 정책, 개발, 교통, 금리, 대출, 청약 이슈 후보를 찾는 보조 채널입니다. 검색 결과 수, 순위, 노출량은 편향이 크므로 지역/단지 관심도 점수나 반응 지표의 원천으로 쓰지 않습니다.

허용 용도:

- 최근 이슈 후보 discovery
- 근거 링크 보강
- 뉴스/컬럼/정책 metadata 후보 생성
- 에이전트 평가 입력의 `recentIssues` 근거 보강

저장 후보:

- 제목
- 출처
- 날짜
- 링크
- 관련 키워드
- 검색 provider와 query
- target 후보와 confidence

현재 구현:

- pipeline 명령: `realestate-recent-issues`, `realestate-recent-issues-push`
- 검색 provider: `serpapi:google_news`
- SerpApi 호출 기본값: `engine=google`, `tbm=nws`, `google_domain=google.co.kr`, `gl=kr`, `hl=ko`, `output=json`
- 저장 경로: `POST /internal/realestate/content-items`
- 저장 상태: `sourceId=serpapi:google_news`, `linkType=search_candidate`, `reviewState=candidate`, `dataStatus=candidate`
- query는 `metricLabel`에 `query: {지역/단지명} {쟁점 키워드} 부동산` 형태로 남깁니다.
- 후보 링크는 승인 전까지 target timeline 정본으로 materialize하지 않습니다.

금지 용도:

- 검색 결과 수를 관심도 점수로 변환
- 검색 순위를 기대/우려 비율로 해석
- 검색 API만으로 정책 영향권을 확정
- 원문 전문 저장 또는 재게시

## 유사 과거 상황 비교

유사 과거 비교는 가능하며 이 제품의 핵심 분석 기능 후보입니다. 다만 공개 표현은 예측이나 행동 지시가 아니라 `비슷한 과거 상황`, `이후 시장 흐름`, `관찰된 차이`로 둡니다.

기본 흐름:

```text
RealEstateReactionSnapshot
+ market fact timeline
+ issueMix
+ coverage/reliability
→ similar window 검색
→ 이후 market fact 변화 요약
→ 유사점/차이점/caveat 저장
→ 화면에 과거 비교 리포트 표시
```

저장 후보:

- `similarityRunId`
- `targetType`
- `targetId`
- `windowStart`
- `issueMix`
- `matchedHistoricalWindow`
- `similarityScore`
- `afterMarketFacts`
- `caveats`
- `dataQuality`

## 충돌 검토 결과

- 부동산에서는 `RealEstateReactionSnapshot`, `RealEstateMarketFact`, `EvidenceLog`, `similar historical window`를 정본으로 둡니다.
- 기존 `sourceMoods` API 개념은 운영/내부 분석에는 유지할 수 있지만, 사용자-facing 필드명으로 그대로 쓰지 않습니다.
- 벡터DB와 RAG는 실시간 matcher나 가격 계산기가 아닙니다. `collect -> match target -> classify reaction -> aggregate -> issueMix -> similar-window/RAG` 순서를 유지합니다.
- SerpApi 같은 검색 API는 관심도 지표가 아니라 최근 이슈 후보와 근거 링크를 찾는 보조 채널입니다.

## 구현 순서

1. `RealEstateReactionSnapshot` 저장 모델과 target/window 통합 지표 contract를 확정합니다.
2. `RealEstateMarketFact`와 timeline event contract를 확정합니다.
3. `issueMix` 후보 라벨과 confidence 기준을 정합니다.
4. 임베딩/클러스터링 batch로 유사 쟁점 후보를 만듭니다.
5. 유사 window 검색이 실제 제품 기능이 될 때 벡터DB를 도입합니다.
6. RAG는 유사 사례와 market fact 차이를 설명하는 레이어로 붙입니다.
