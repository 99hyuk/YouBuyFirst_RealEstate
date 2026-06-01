# 제품/기술 고민 메모

이 문서는 사용자가 작업 중 던진 제품/기술 고민을 나중에 다시 찾기 위한 얇은 기록입니다. 확정된 제품 방향은 `docs/product/FINAL_PRODUCT_PLAN.md`, 현재 작업 기준은 `docs/current/HANDOFF.md`, 기술/운영 리스크는 `docs/governance/TECHNICAL_RISK_REGISTER.md`에 반영합니다.

중요한 기술 의사결정이나 취업 포트폴리오 소재는 Notion 개발자 기술 경험 DB에 별도 기록합니다. 이 문서는 Notion을 대체하지 않고, 대화 중 생긴 고민을 잃어버리지 않기 위한 인덱스입니다.

## 기록 규칙

- 사용자가 "고민거리", "나중에 볼 수 있게", "이거 기록"처럼 말하면 이 문서에 짧게 추가합니다.
- 한 항목은 배경, 현재 판단, 남은 확인으로 나눕니다.
- 이미 결론이 난 항목도 삭제하지 않고 `현재 판단`을 갱신합니다.
- 세부 근거가 길어지면 관련 기획/리스크/작업 단위 문서로 승격합니다.

## 현재 고민 목록

### 2026-06-01. 이 repo는 주식이 아니라 부동산 서비스만 담당한다

- 배경: `C:\agents\YouBuyFirst`를 복제해 새 프로젝트를 만들었지만, 복제본의 활성 문서에는 주식, 종목, 시세, 모의투자 중심 표현이 많이 남아 있었습니다.
- 현재 판단: 부동산은 후순위 버티컬이 아니라 이 repo의 주 도메인입니다. 기존 YouBuyFirst의 커뮤니티 수집, 반응 분석, 지표화, 유사 과거 비교, 근거 로그 구조는 재사용하지만, 주식 도메인 안에 부동산을 넣지 않습니다.
- 설계 기준: root `AGENTS.md`, `docs/current/*`, `docs/product/*`, `docs/layers/ops/*`, `docs/domains/realestate/*`는 부동산 중심으로 정렬합니다. `stock`, `market`, `simulation`은 당장 삭제하지 않고 참고/비활성 영역으로 분류합니다.
- 남은 확인: code package와 front route까지 부동산 기준으로 옮길 때 기존 stock 코드의 삭제/공통화/참고 보관 범위를 별도 PR로 결정합니다.

### 2026-06-01. 부동산 반응 지표를 어떻게 만들지

- 배경: 주식 프로젝트의 `개미 심리 지수`를 그대로 가져오면 부동산에서 행동 지시나 투자 판단처럼 보일 수 있습니다.
- 현재 판단: 부동산 화면의 대표값은 `지역/단지 반응 지표`, `기대/우려`, `쟁점 비율`, `표본 신뢰도`로 둡니다. 점수 하나로 행동을 유도하지 않고, 반응과 시장 사실을 함께 관찰하게 만듭니다.
- 설계 기준: `RealEstateReactionSnapshot`은 target/window 단위 mention count, expectation score, concern score, issueMix, sourceCount, sourceSkew, confidence를 가집니다.
- 남은 확인: expectation/concern 산식, 낮은 표본 수 숨김 기준, source skew 경고 기준, 1일/1주/1개월 window를 정합니다.

### 2026-06-01. 실거래/전세/매물 데이터 freshness를 어떻게 표현할지

- 배경: 주식 quote freshness와 부동산 market fact freshness는 성격이 다릅니다. 실거래와 전세, 매물, 정책 이벤트는 갱신 주기와 지연이 서로 다릅니다.
- 현재 판단: 국토교통부 아파트 매매/전월세 실거래가 API는 공공데이터포털에서 제공되고 업데이트 주기가 `실시간`으로 표시됩니다. 그래도 제품에서는 매일 확정 공시처럼 말하지 않고, 신고/공개/수집 시각을 분리합니다.
- 설계 기준: `RealEstateMarketFact`는 factType, observedAt, valueJson, provider, providerDataset, asOf, ingestedAt, sourceUpdatedAt, stale, dataStatus를 가집니다.
- 남은 확인: API별 실제 응답 필드, 서비스키/트래픽 제한, provider별 지연 기준, UI stale 배지 문구, mock과 실제 데이터 전환 기준을 정합니다.

### 2026-06-01. 부동산 source는 30개 내외 후보 registry로 먼저 관리한다

- 배경: 부동산 정보는 주식보다 흩어져 있고, 네이버 카페/다음 카페 같은 커뮤니티에도 지역/단지 반응이 많을 가능성이 큽니다.
- 현재 판단: adapter를 바로 30개 만드는 것이 아니라 `crawl_sources` registry에 후보를 먼저 쌓고, 공개 접근성/robots/약관/로그인 필요 여부/신호 품질을 검토합니다.
- 설계 기준: source 상태는 `disabled`, `local-research-only`, `public-demo-only`, `enabled`로 관리합니다. 로그인, CAPTCHA, 프록시, fingerprint 우회가 필요한 source는 구현하지 않습니다.
- 남은 확인: 30개 내외 후보 목록, source별 게시판 id, 예상 글 빈도, parser 난이도, alias matcher에 필요한 별칭 seed를 정합니다.

### 2026-06-01. 별칭 DB는 크롤링의 1차 필수 요소다

- 배경: 커뮤니티에서는 공식 지역명/단지명보다 줄임말, 별칭, 오타, 생활권 표현이 자주 쓰일 수 있습니다.
- 현재 판단: `real_estate_aliases`는 부가 기능이 아니라 수집/매칭의 기본 입력입니다. 후보 alias는 자동 생성 가능하지만 `approved` 전에는 ranking과 정식 지표에 섞지 않습니다.
- 설계 기준: aliasType은 `official`, `short_name`, `nickname`, `typo`, `nearby_area`, `community_slang`로 시작합니다. reviewState는 `candidate`, `approved`, `rejected`, `ambiguous`를 씁니다.
- 남은 확인: 초기 alias seed를 공공데이터 공식명, 수동 입력, 커뮤니티 후보에서 어떻게 모을지 정합니다.

### 2026-06-01. 유사 과거 상황 비교를 어디까지 넣을지

- 배경: 부동산 기획의 차별점은 현재 반응만 보여주는 것이 아니라 비슷한 과거 상황과 이후 시장 흐름을 연결하는 데 있습니다.
- 현재 판단: 유사 과거 비교는 예측이나 행동 지시가 아니라 과거 관찰 사례를 함께 보여주는 분석 레이어입니다.
- 설계 기준: 비교 입력은 reaction snapshot, issueMix, 뉴스/정책 이벤트, market fact timeline입니다. 출력은 유사점, 차이점, 이후 market fact 흐름, caveat입니다.
- 남은 확인: 벡터DB 없이 Python batch로 먼저 실험할 범위와, 벡터 저장소 도입 시 검색 단위를 정합니다.

### 2026-06-01. 에이전트 문구 수위를 어떻게 잡을지

- 배경: 기존 주식 프로젝트에는 종목 상태를 강하게 표현하는 팩트폭격/roast 방향이 있었습니다. 부동산에서는 특정 지역/단지에 대한 단정이 더 민감할 수 있습니다.
- 현재 판단: 부동산 에이전트는 행동 지시나 가격 단정을 하지 않고, `관찰 요약`, `근거`, `caveat`, `데이터 상태`를 남깁니다. 재미있는 톤을 쓰더라도 대상은 사용자가 아니라 데이터의 불일치나 표본 부족이어야 합니다.
- 설계 기준: `docs/domains/agent/REAL_ESTATE_EVALUATION_COPY.md`에서 사용자용 평가 문구 기준을 관리합니다.
- 남은 확인: 공개 화면 기본 톤과 데모용 강한 톤을 분리할지, 개인화 화면에서는 어떤 문구를 금지할지 정합니다.

### 2026-06-01. 너나사 시리즈 UI는 패턴을 공유하고 accent만 바꾼다

- 배경: 사용자는 이 서비스를 기존 주식 서비스와 완전히 별개의 브랜드가 아니라 `너나사 주식`, `너나사 부동산`처럼 이동 가능한 시리즈로 보고 싶어 합니다.
- 현재 판단: UI shell, nav, 검색, 오른쪽 rail, dashboard grid, card, timeline, table 패턴은 주식과 부동산이 최대한 공유합니다. 부동산은 대표 accent만 blue에서 warm orange 계열로 바꿉니다.
- 설계 기준: `--brand`는 부동산 active 화면에서 `--series-realestate`를 가리키고, `--series-stock`은 기존 주식 reference의 accent로 남깁니다.
- 남은 확인: 실제 front CSS에서 브랜드 blue와 의미색 blue를 분리한 뒤, token 교체와 screenshot QA를 진행합니다.
