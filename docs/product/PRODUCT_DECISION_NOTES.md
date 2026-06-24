# 제품/기술 고민 메모

이 문서는 사용자가 작업 중 던진 제품/기술 고민을 나중에 다시 찾기 위한 얇은 기록입니다. 확정된 제품 방향은 `docs/product/FINAL_PRODUCT_PLAN.md`, 현재 작업 기준은 `docs/current/HANDOFF.md`, 기술/운영 리스크는 `docs/governance/TECHNICAL_RISK_REGISTER.md`에 반영합니다.

중요한 기술 의사결정이나 취업 포트폴리오 소재는 Notion 개발자 기술 경험 DB에 별도 기록합니다. 이 문서는 Notion을 대체하지 않고, 대화 중 생긴 고민을 잃어버리지 않기 위한 인덱스입니다.

## 기록 규칙

- 사용자가 "고민거리", "나중에 볼 수 있게", "이거 기록"처럼 말하면 이 문서에 짧게 추가합니다.
- 한 항목은 배경, 현재 판단, 남은 확인으로 나눕니다.
- 이미 결론이 난 항목도 삭제하지 않고 `현재 판단`을 갱신합니다.
- 세부 근거가 길어지면 관련 기획/리스크/작업 단위 문서로 승격합니다.

## 현재 고민 목록

### 2026-06-23. 지역 지도 가격 지표는 주간 아파트 매매가격지수를 우선 사용한다

- 배경: 지역 분석 지도에서 상승/하락 색상을 보여주려면 실제 지역별 가격 변화율 지표가 필요합니다. 기존 MVP는 월간 R-ONE 아파트 매매가격지수 변동률과 seed/mock snapshot이 섞여 있어, 지도 색상이 최신 주간 흐름처럼 보일 위험이 있었습니다.
- 현재 판단: 지도와 지역 요약의 가격 지표는 R-ONE 주간/월간 아파트 매매가격지수 원천값을 `price_index`로 저장한 뒤 period별 기준 시점과 최신 시점을 비교합니다. 서비스 내부 metricCode는 주간 `reb_weekly_apt_sale_price_index_region`, 월간 `reb_monthly_apt_sale_price_index_region`으로 둡니다. 1개월 이상 지도 period는 `reb_rone_monthly_apt_sale_price_index` 지수 history를 사용하고, 계산된 변동률 fact를 별도로 저장하지 않습니다.
- 설계 기준: 주간 1주 변화율은 원천 변동률을 쓰고, 1개월/3개월/6개월/1년은 R-ONE 지역 현황 지도 PR 응답의 월별 제공 변동률을 누적합니다. 규모별/연령별 매매가격지수는 지역 대표값이 아니라 상세 분석 보조 지표입니다. `주택` 또는 `종합` 범위 지표와 `아파트` 지표는 `housingScope`를 나눠 저장하고 같은 지도 색상 스케일에 섞지 않습니다.
- 수집 판단: 새 운영 수집은 Spring Batch로 구현합니다. 기존 Python/R-ONE 수집 코드는 운영 파이프라인으로 유지하지 않고, 요청 파라미터, 파싱 예외, 지역 매핑 검증 케이스만 참고합니다.
- 남은 확인: 공공데이터포털 파일데이터와 한국부동산원 부동산통계 조회 OpenAPI 중 어떤 채널을 1차 provider로 쓸지 정하고, 가평/양평 등 미공표처럼 보이는 지역이 공식 원천에 실제로 없는지 coverage audit을 먼저 돌립니다.

### 2026-06-22. 제품 정체성은 공식 데이터 기반 부동산 인사이트 탐색 서비스다

- 배경: 초기 참고 구조는 사람들의 반응을 시장 해석에 연결하는 방식이었습니다. 그러나 부동산은 실거래, 전세, 공급, 정책, 청약 일정처럼 드러나는 시장 사실이 더 중요한 탐색 축입니다.
- 현재 판단: 너나사 부동산은 `공식 데이터 기반 부동산 인사이트 탐색 서비스`입니다. 실거래/전세/매물/공급/정책 흐름과 주요 일정을 지역/생활권 기준으로 묶고, 시장 사실, 유사 과거, 최근 이슈를 함께 비교해 근거가 남는 평가를 제공합니다. 공개 커뮤니티 반응은 핵심 정체성이 아니라 보조 관찰 신호로만 사용합니다.
- 설계 기준: 벡터DB는 과거 유사 상황 검색용이며 target 식별이나 가격 계산의 정본이 아닙니다. SerpApi 같은 검색 API는 최근 이슈 후보와 근거 링크 보강용이며 검색 결과 수를 관심도 지표로 쓰지 않습니다. Langfuse는 LLM 호출 관측 도구이고 판단 정본은 DB의 evidence log와 snapshot입니다.
- 남은 확인: 실거래 탐색 API shape, 주요 일정 저장 모델, `realestate-eval-v1` 입력/출력 schema, 유사 과거 검색 단위, Langfuse trace와 DB evidence log 연결 key를 정합니다.

### 2026-06-01. 이 repo는 부동산 서비스만 담당한다

- 배경: 새 프로젝트의 active 문서와 코드가 부동산 전용 모델로 정리되어야 했습니다.
- 현재 판단: 부동산은 후순위 버티컬이 아니라 이 repo의 주 도메인입니다. 실거래 탐색, 시장 fact, 주요 일정, 유사 과거 비교, 근거 로그 구조는 부동산 target 기준으로만 운영합니다. 공개 반응 분석은 보조 신호로만 유지합니다.
- 설계 기준: root `AGENTS.md`, `docs/current/*`, `docs/product/*`, `docs/layers/ops/*`, `docs/domains/realestate/*`는 부동산 중심으로 정렬합니다. 부동산에 맞지 않는 구현은 active runtime에 보존하지 않고 git history로만 확인합니다.
- 남은 확인: code package와 front route는 부동산 기준으로 옮기고, 공통 패턴만 유지합니다.

### 2026-06-01. 부동산 반응 지표를 어떻게 만들지

- 배경: 반응 지표를 점수 하나로 표현하면 부동산에서 행동 지시나 투자 판단처럼 보일 수 있습니다.
- 현재 판단: 이 항목은 2026-06-22 방향 전환으로 보조 신호 기준이 되었습니다. 부동산 화면의 대표값은 실거래, 전세, 공급, 정책 일정, 근거 로그이며, 반응 지표는 상세 리포트나 EvidenceLog의 보조 관찰 데이터로만 둡니다.
- 설계 기준: `RealEstateReactionSnapshot`은 필요할 때 target/window 단위 mention count, expectation score, concern score, issueMix, sourceCount, sourceSkew, confidence를 가질 수 있지만 핵심 화면 정본은 아닙니다.
- 남은 확인: 보조 반응을 어느 상세 섹션에 노출할지, 낮은 표본 수 숨김 기준과 source skew 경고 기준을 정합니다.

### 2026-06-01. 실거래/전세/매물 데이터 freshness를 어떻게 표현할지

- 배경: 부동산 market fact는 원천별 갱신 주기와 공개 지연이 서로 다릅니다.
- 현재 판단: 국토교통부 아파트 매매/전월세 실거래가 API는 공공데이터포털에서 제공되고 업데이트 주기가 `실시간`으로 표시됩니다. 그래도 제품에서는 매일 확정 공시처럼 말하지 않고, 신고/공개/수집 시각을 분리합니다.
- 설계 기준: `RealEstateMarketFact`는 factType, observedAt, valueJson, provider, providerDataset, asOf, ingestedAt, sourceUpdatedAt, stale, dataStatus를 가집니다.
- 남은 확인: API별 실제 응답 필드, 서비스키/트래픽 제한, provider별 지연 기준, UI stale 배지 문구, mock과 실제 데이터 전환 기준을 정합니다.

### 2026-06-01. 부동산 source는 30개 내외 후보 registry로 먼저 관리한다

- 배경: 부동산 정보는 일반 금융 커뮤니티보다 흩어져 있고, 네이버 카페/다음 카페 같은 커뮤니티에도 지역/단지 반응이 많을 가능성이 큽니다.
- 현재 판단: adapter를 바로 30개 만드는 것이 아니라 공식 데이터 provider와 근거 링크 source registry를 우선 관리합니다. 공개 원문 source는 보조 근거 후보로만 검토하고, 공개 접근성/robots/약관/로그인 필요 여부/신호 품질을 확인합니다.
- 설계 기준: source 상태는 `disabled`, `local-research-only`, `public-demo-only`, `enabled`로 관리합니다. 로그인, CAPTCHA, 프록시, fingerprint 우회가 필요한 source는 구현하지 않습니다.
- 남은 확인: 30개 내외 후보 목록, source별 게시판 id, 예상 글 빈도, parser 난이도, alias matcher에 필요한 별칭 seed를 정합니다.

### 2026-06-01. 별칭 DB는 검색과 원문 연결의 보조 입력이다

- 배경: 커뮤니티에서는 공식 지역명/단지명보다 줄임말, 별칭, 오타, 생활권 표현이 자주 쓰일 수 있습니다.
- 현재 판단: `real_estate_aliases`는 검색, 공식 단지 매칭, 뉴스/원문 연결의 보조 입력입니다. 후보 alias는 자동 생성 가능하지만 `approved` 전에는 정식 target 연결이나 사용자-facing 요약에 섞지 않습니다.
- 설계 기준: aliasType은 `official`, `short_name`, `nickname`, `typo`, `nearby_area`, `community_slang`로 시작합니다. reviewState는 `candidate`, `approved`, `rejected`, `ambiguous`를 씁니다.
- 남은 확인: 초기 alias seed를 공공데이터 공식명, 수동 입력, 커뮤니티 후보에서 어떻게 모을지 정합니다.

### 2026-06-01. 유사 과거 상황 비교를 어디까지 넣을지

- 배경: 부동산 기획의 차별점은 현재 반응만 보여주는 것이 아니라 비슷한 과거 상황과 이후 시장 흐름을 연결하는 데 있습니다.
- 현재 판단: 유사 과거 비교는 예측이나 행동 지시가 아니라 과거 관찰 사례를 함께 보여주는 분석 레이어입니다.
- 설계 기준: 비교 입력은 reaction snapshot, issueMix, 뉴스/정책 이벤트, market fact timeline입니다. 출력은 유사점, 차이점, 이후 market fact 흐름, caveat입니다.
- 남은 확인: 벡터DB 없이 Python batch로 먼저 실험할 범위와, 벡터 저장소 도입 시 검색 단위를 정합니다.

### 2026-06-01. 에이전트 문구 수위를 어떻게 잡을지

- 배경: 부동산에서는 특정 지역/단지에 대한 단정적 표현이 민감할 수 있습니다.
- 현재 판단: 부동산 에이전트는 행동 지시나 가격 단정을 하지 않고, `관찰 요약`, `근거`, `caveat`, `데이터 상태`를 남깁니다. 재미있는 톤을 쓰더라도 대상은 사용자가 아니라 데이터의 불일치나 표본 부족이어야 합니다.
- 설계 기준: `docs/domains/agent/REAL_ESTATE_EVALUATION_COPY.md`에서 사용자용 평가 문구 기준을 관리합니다.
- 남은 확인: 공개 화면 기본 톤과 데모용 강한 톤을 분리할지, 개인화 화면에서는 어떤 문구를 금지할지 정합니다.

### 2026-06-01. 너나사 시리즈 UI는 패턴을 공유하고 accent만 바꾼다

- 배경: 사용자는 이 서비스를 `너나사 부동산`이라는 시리즈형 제품으로 보고 싶어 합니다.
- 현재 판단: UI shell, nav, 검색, 오른쪽 rail, dashboard grid, card, timeline, table 패턴은 너나사 시리즈의 일관성을 유지합니다. 부동산은 대표 accent를 warm orange 계열로 둡니다.
- 설계 기준: `--brand`는 부동산 active 화면에서 `--series-realestate`를 가리킵니다.
- 남은 확인: 실제 front CSS에서 브랜드 blue와 의미색 blue를 분리한 뒤, token 교체와 screenshot QA를 진행합니다.
