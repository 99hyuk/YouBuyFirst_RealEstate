# 부동산 제품 방향

이 문서는 너나사 부동산 프로젝트의 제품 방향입니다. 이 repo의 active runtime과 문서는 지역/단지 반응, 시장 사실 데이터, 근거 로그를 중심으로 한 부동산 전용 서비스만 다룹니다.

## 한 줄 설명

너나사 부동산은 수요자 반응 기반 부동산 시장 해석 서비스입니다.

지역과 단지에 대한 실제 사람들의 관심, 기대, 불안, 의심을 커뮤니티/댓글/뉴스/컬럼에서 추적하고, 실거래/전세/매물 같은 시장 사실 데이터와 함께 보여주는 관찰형 분석 서비스입니다.

핵심 구현 기준은 `docs/product/real-estate-one-page-plan.html`과 `docs/product/CORE_IMPLEMENTATION_SCOPE.md`입니다.

## 핵심 목표

- 커뮤니티 글, 댓글, 뉴스, 컬럼에서 지역과 단지 언급을 찾습니다.
- 커뮤니티 별칭과 줄임말을 별칭 DB로 관리해 크롤링과 matcher가 같은 기준을 쓰게 합니다.
- 언급량, 기대/우려, 쟁점 비율, 표본 신뢰도를 지표로 만듭니다.
- 실거래, 전세, 매물, 정책, 공급, 교통 이벤트를 provider/asOf/stale와 함께 보여줍니다.
- 비슷한 과거 반응 상황과 이후 시장 흐름을 연결합니다.
- 에이전트는 결론만 말하지 않고 어떤 근거를 봤는지 로그로 남깁니다.

## 핵심 판단 흐름

```text
수집 -> 지역/단지 언급 식별 -> 반응 지표화 -> 유사 과거 검색 -> 최근 이슈 후보 탐색 -> 에이전트 평가 -> 근거 로그 저장
```

- 언급량 지표는 단순 mention count가 아니라 최근 증가율, 반복 언급, source 다양성, 표본 수를 함께 봅니다.
- 반응 방향은 기대, 우려, 중립, 혼조로 분류하고, 쟁점은 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책, 개발 호재, 가격 부담, 실거주 만족도처럼 이유 중심으로 묶습니다.
- 벡터DB는 target 식별이나 가격 계산이 아니라 과거 유사 반응 패턴과 이후 시장 흐름 검색에만 씁니다.
- SerpApi 같은 검색 API는 최근 뉴스, 정책, 개발, 교통, 금리, 대출, 청약 이슈 후보와 근거 링크를 보강하는 용도입니다. 검색 결과 수 자체를 관심도 점수로 쓰지 않습니다.
- AI 에이전트는 반응 지표, 유사 과거, 최근 이슈, 시장 사실을 함께 보고 평가하되 특정 매수, 매도, 청약, 대출 행동을 지시하지 않습니다.

## 재사용할 구조

- 커뮤니티/뉴스/컬럼 수집 구조
- 원문 제한 저장과 출처 링크 정책
- 반응 방향 분석
- 언급량과 쟁점 지표화
- 표본 신뢰도, 소스 편중 주의 배지
- 유사 과거 상황 비교
- 에이전트 근거 로그
- dashboard 스타일의 UI 디자인 원칙

## 부동산 서비스에서 중요한 구현 조건

- 부동산은 지역, 단지, 생활권, 정책 영향권으로 대상이 훨씬 잘게 나뉩니다.
- 부동산은 지역 단위 상승, 정책, 교통, 공급, 대출, 청약, 학군, 재건축 같은 이벤트에 민감합니다.
- 따라서 target graph, alias DB, policy timeline, source registry를 1차 구현 범위로 둡니다.

## 부동산 정본 구조

- 대상 정본은 `region`, `complex`, `living_area`, `policy_area`, `real_estate_target`입니다.
- 시장 사실은 `transaction`, `rent`, `listing`, `policy event`, `market fact`로 나눕니다.
- 사용자 화면은 거래 판단이 아니라 관찰형 분석, 관심 지역 관리, 근거 로그 확인에 집중합니다.
- freshness는 실거래/매물/전세/정책 데이터별 `provider`, `asOf`, `stale`, `ingestedAt` 기준으로 분리합니다.

## 주요 기능 후보

| 기능 | 사용자에게 보여줄 의미 | 주의점 |
| --- | --- | --- |
| 요즘 언급 많은 지역/단지 | 관심이 급증한 대상을 빠르게 확인 | 관심 급등을 행동 지시처럼 표현하지 않음 |
| 실시간 이슈/뉴스/컬럼 | 정책, 교통, 공급, 전세, 개발 이슈를 한 흐름으로 확인 | 원문 전문 재게시 금지 |
| 지역/단지별 반응 지표 | 기대와 우려, 쟁점 비율, 표본 신뢰도 확인 | 표본 부족과 소스 편중 표시 |
| 시장 사실 타임라인 | 실거래, 전세, 매물, 정책 이벤트를 시간순으로 확인 | provider, `asOf`, `stale` 분리 |
| 유사 과거 상황 비교 | 비슷한 반응과 이후 흐름을 참고 | 미래 결과 단정 금지 |
| 에이전트 근거 로그 | 평가가 어떤 근거를 봤는지 추적 | 내부 추론 전문 노출 금지 |

## 1차 데이터 계약 초안

```text
real_estate_regions
  id
  name
  type
  parent_id
  legal_code
  normalized_name

real_estate_complexes
  id
  region_id
  name
  normalized_name
  address
  built_year
  household_count

real_estate_target_edges
  id
  from_target_type
  from_target_id
  to_target_type
  to_target_id
  edge_type
  confidence
  review_state

real_estate_aliases
  id
  target_type
  target_id
  alias
  normalized_alias
  alias_type
  source
  evidence_url
  confidence
  review_state

crawl_sources
  id
  display_name
  source_type
  root_url
  access_mode
  status
  robots_status
  terms_status
  target_scope
  expected_volume
  parser_status
  rate_limit_policy

real_estate_mentions
  id
  post_id
  target_type
  target_id
  confidence
  matched_alias

real_estate_reaction_analyses
  id
  mention_id
  reaction_direction
  issue_type
  confidence
  evidence_snippet

real_estate_reaction_snapshots
  id
  target_type
  target_id
  window_start
  window_minutes
  mention_count
  expectation_score
  concern_score
  issue_mix_json
  confidence
  source_count
  source_skew

real_estate_market_facts
  id
  target_type
  target_id
  fact_type
  observed_at
  value_json
  provider
  as_of
  stale

real_estate_policy_events
  id
  event_type
  title
  source_url
  published_at
  effective_from
  target_scope
  data_status

real_estate_evidence_logs
  id
  target_type
  target_id
  evaluated_at
  summary
  evidence_json
  caveats_json
```

## 수집 정책

- 공개 HTTP 수집을 우선합니다.
- Playwright는 렌더링 fallback으로만 씁니다.
- CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다.
- 부동산 source는 30개 내외 후보를 먼저 `crawl_sources` registry에 넣고, 정책/접근성/신호 품질을 검토한 뒤 adapter를 만듭니다.
- 네이버 카페와 다음 카페는 공개 목록 접근이 가능한 경우만 후보로 둡니다. 로그인이 필요한 카페는 `disabled` 상태로 둡니다.
- 원문 전문을 재게시하지 않습니다.
- 제목, 일부 snippet, URL, 작성자 해시, 작성 시각, 원문 해시 정도만 제한 저장합니다.
- 뉴스/컬럼은 제목, 출처, 링크, 키워드 중심으로만 표시합니다.
- 검색 API로 발견한 최근 이슈 후보도 제목, 출처, 날짜, 링크, 관련 키워드만 저장하고 검색 노출량을 지표화하지 않습니다.
- 실거래/전세/매물 데이터는 provider, `asOf`, `stale`, 지연 여부를 반드시 분리합니다.

## 공공데이터 확인 메모

- 국토교통부 아파트 매매 실거래가 자료와 아파트 전월세 실거래가 자료는 공공데이터포털에서 REST/XML API로 제공됩니다.
- 공공데이터포털에는 두 API의 업데이트 주기가 `실시간`으로 표시됩니다. 제품에서는 이를 매일 확정 공시로 단정하지 않고, 신고/공개 지연과 `asOf`/`ingestedAt`을 함께 보여줍니다.
- 국토교통부 건축HUB 건축물대장정보 서비스는 단지/건물 기본 속성 보강 후보입니다.
- 한국부동산원 공동주택 실거래가격지수는 지역 단위 흐름 참고 지표로 쓰고, 개별 단지 실거래 원장처럼 쓰지 않습니다.

## 1차 실행 범위

1. 문서와 작업 영역을 부동산 중심으로 정렬합니다.
2. `realestate` 도메인 문서와 데이터 contract를 만듭니다.
3. 지역/단지 alias matcher 초안을 만듭니다.
4. realestate dashboard와 target detail 화면 기준을 만듭니다.
5. active runtime과 화면 문구는 부동산 target, market fact, reaction snapshot, evidence log 기준으로 유지합니다.
