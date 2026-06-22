# 현재 작업 인수인계

마지막 갱신: 2026-06-22

새 채팅이 방향을 잡는 짧은 요약입니다. 전문 읽기를 기본값으로 두지 말고 필요한 섹션만 확인합니다.

## 현재 상태

- Repository: 새 부동산 전용 복제본
- Workspace: `C:\agents\YouBuyFirst_RealEstate`
- Branch: `codex/realestate-bootstrap`
- Remote: 아직 없음. 원본 `C:\agents\YouBuyFirst`로 push하지 않도록 복제 직후 `origin`을 제거했습니다.
- 기반: Spring Boot backend, Python pipeline, MySQL, Docker Compose, Vue 3 front mock shell

## 구현 스냅샷

- 이 repo는 이제 부동산 서비스만 담당합니다.
- root `AGENTS.md`는 부동산 전용 라우터입니다.
- 제품 방향 정본은 `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`와 `docs/product/FINAL_PRODUCT_PLAN.md`입니다.
- 핵심 구현 기준은 `docs/product/real-estate-one-page-plan.html`과 `docs/product/CORE_IMPLEMENTATION_SCOPE.md`입니다.
- `docs/domains/realestate/`가 새 주 도메인입니다.
- 기존 금융 서비스 전용 구현은 active runtime에서 제거했고, 필요한 맥락은 git history와 결정 로그로만 확인합니다.
- front는 부동산 화면 기준으로 재정렬했습니다. 남은 화면 변경은 realestate dashboard와 target detail Screen Brief를 기준으로 진행합니다.

## 최근 결정

- 부동산은 후순위 버티컬이 아니라 이 프로젝트의 주 도메인입니다.
- 실거래 탐색, 시장 fact, 주요 일정, 유사 과거 비교, 근거 로그 구조는 부동산 target 기준으로 운영합니다.
- 화면과 API는 지도 기반 지역 흐름, 실거래/전세 탐색, 주요 일정, 시장 사실, 근거 로그 중심으로 정렬합니다.
- 부동산은 대상이 훨씬 쪼개져 있고 지역 단위 상승, 정책, 교통, 공급, 대출, 청약, 학군, 재건축 이벤트에 민감합니다.
- 따라서 region/complex/living_area/policy_area target graph와 policy timeline은 1차 구현 범위입니다.
- 사용자는 오늘 확인할 지역 시장 흐름, 실거래/전세 row, 주요 일정, 시장 사실 타임라인, 유사 과거 상황, 에이전트 근거 로그를 봅니다.
- 특정 매수, 매도, 청약, 대출 행동을 권유하거나 가격 상승을 단정하는 표현은 쓰지 않습니다.
- 확인되지 않은 데이터는 `unknown`, `null`, `확인 필요`, `mock`으로 구분합니다.
- 실거래/전세/매물/정책 데이터는 provider, `asOf`, `stale`, 지연 여부를 함께 표시합니다.
- 공공데이터포털에는 국토교통부 아파트 매매/전월세 실거래가 API가 있고 업데이트 주기가 `실시간`으로 표시됩니다. 다만 제품에서는 매일 확정 공시처럼 표현하지 않고 신고/공개/수집 시각을 분리합니다.
- 공개 커뮤니티 반응은 핵심 정체성이 아니라 보조 관찰 신호입니다. 별도 대표 랭킹이나 서비스 결론처럼 보이게 만들지 않습니다.
- 별칭 DB는 검색, 공식 단지 매칭, 뉴스/원문 연결의 보조 입력입니다. 공식명, 줄임말, 커뮤니티 별칭, 오타, 생활권 표현을 후보로 받되 `approved` 전에는 정식 target 연결이나 사용자-facing 요약에 섞지 않습니다.
- 부동산 source는 공식 데이터 provider와 근거 링크 source registry를 우선 관리합니다. 공개 원문 source는 네이버 카페/다음 카페처럼 비로그인 공개 목록 접근이 가능한 경우만 보조로 검토합니다.
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
- `/realestate/transactions` 실거래 탐색 API와 화면 계약 확정
- `/indicators` 주요 일정 화면의 schedule provider/source 계약 확정
- 공식 데이터 provider와 근거 링크 source registry 정리
- 지역/단지 alias seed와 검수 기준 정리
- `pipeline/src/youbuyfirst_pipeline/realestate/` matcher 초안 설계
- 기존 금융 서비스 전용 코드와 문서는 active runtime에서 제거하고 부동산 정본 문서만 유지
