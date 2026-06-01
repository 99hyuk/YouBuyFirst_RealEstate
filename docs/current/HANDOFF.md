# 현재 작업 인수인계

마지막 갱신: 2026-06-01

새 채팅이 방향을 잡는 짧은 요약입니다. 전문 읽기를 기본값으로 두지 말고 필요한 섹션만 확인합니다.

## 현재 상태

- Repository: 새 부동산 전용 복제본
- Workspace: `C:\agents\YouBuyFirst_RealEstate`
- Branch: `codex/realestate-bootstrap`
- Remote: 아직 없음. 원본 `C:\agents\YouBuyFirst`로 push하지 않도록 복제 직후 `origin`을 제거했습니다.
- 기반: Spring Boot backend, Python pipeline, MySQL, Docker Compose, Vue 3 front mock shell

## 구현 스냅샷

- 이 repo는 이제 주식이 아니라 부동산 서비스만 담당합니다.
- root `AGENTS.md`는 부동산 전용 라우터입니다.
- 제품 방향 정본은 `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`와 `docs/product/FINAL_PRODUCT_PLAN.md`입니다.
- 핵심 구현 기준은 `docs/product/real-estate-one-page-plan.html`과 `docs/product/CORE_IMPLEMENTATION_SCOPE.md`입니다.
- `docs/domains/realestate/`가 새 주 도메인입니다.
- `stock`, `market`, `simulation`은 기존 주식 프로젝트에서 넘어온 참고/비활성 영역입니다. 첫 정렬 단계에서는 삭제하지 않습니다.
- front는 아직 복제된 주식 mock 화면을 많이 포함합니다. 새 화면 기준은 realestate dashboard와 target detail Screen Brief로 재정렬해야 합니다.

## 최근 결정

- 부동산은 후순위 버티컬이 아니라 이 프로젝트의 주 도메인입니다.
- 기존 YouBuyFirst의 커뮤니티 수집, 반응 분석, 지표화, 유사 과거 비교, 근거 로그 구조는 재사용합니다.
- 주식의 종목/시세/모의투자 모델을 부동산에 억지로 일반화하지 않습니다.
- 주식과 기술 흐름은 거의 같지만, 부동산은 대상이 훨씬 쪼개져 있고 지역 단위 상승, 정책, 교통, 공급, 대출, 청약, 학군, 재건축 이벤트에 민감합니다.
- 따라서 region/complex/living_area/policy_area target graph와 policy timeline은 1차 구현 범위입니다.
- 사용자는 요즘 언급 많은 지역/단지, 주요 쟁점, 시장 사실 타임라인, 유사 과거 상황, 에이전트 근거 로그를 봅니다.
- 특정 매수, 매도, 청약, 대출 행동을 권유하거나 가격 상승을 단정하는 표현은 쓰지 않습니다.
- 확인되지 않은 데이터는 `unknown`, `null`, `확인 필요`, `mock`으로 구분합니다.
- 실거래/전세/매물/정책 데이터는 provider, `asOf`, `stale`, 지연 여부를 함께 표시합니다.
- 공공데이터포털에는 국토교통부 아파트 매매/전월세 실거래가 API가 있고 업데이트 주기가 `실시간`으로 표시됩니다. 다만 제품에서는 매일 확정 공시처럼 표현하지 않고 신고/공개/수집 시각을 분리합니다.
- 커뮤니티 별칭 DB는 크롤링의 1차 필수 요소입니다. 공식명, 줄임말, 커뮤니티 별칭, 오타, 생활권 표현을 후보로 받되 `approved` 전에는 정식 지표에 섞지 않습니다.
- 부동산 source는 30개 내외 후보를 `crawl_sources` registry에 먼저 넣고, 네이버 카페/다음 카페는 비로그인 공개 목록 접근이 가능한 경우만 검토합니다.
- 공개 HTTP 수집을 우선하고, CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전, fingerprint 위장은 하지 않습니다.
- 원문은 제목, 일부 snippet, URL, 작성자 해시, 작성 시각, 원문 해시 정도로 제한 저장합니다.

## 바로 가기

- 작업 영역: `docs/layers/ops/WORK_AREAS.md`
- 패키지 기준: `docs/layers/ops/DOMAIN_PACKAGE_GUIDE.md`
- 제품 방향: `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`
- 최종 기획: `docs/product/FINAL_PRODUCT_PLAN.md`
- 핵심 구현 범위: `docs/product/CORE_IMPLEMENTATION_SCOPE.md`
- 한페이지 기획안: `docs/product/real-estate-one-page-plan.html`
- 작업 지도: `docs/current/TASKS.md`
- realestate 도메인: `docs/domains/realestate/README.md`
- 데이터 계약: `docs/domains/realestate/DATA_CONTRACT.md`
- 문서/컨텍스트 예산: `docs/layers/ops/DOCUMENTATION_GUIDE.md`
- 작업 방식: `docs/layers/ops/WORKFLOW.md`
- Git/PR 규칙: `docs/layers/ops/GIT_CONVENTION.md`

## 다음 작업 후보

- 공공데이터 API 응답 필드와 실제 갱신 지연 기준 확인
- 부동산 source registry 후보 30개 내외 정리
- 지역/단지 alias seed와 검수 기준 정리
- `pipeline/src/youbuyfirst_pipeline/realestate/` matcher 초안 설계
- 기존 stock/market/simulation 문서와 코드를 legacy reference로 표시하고 후속 삭제 후보 목록 작성
