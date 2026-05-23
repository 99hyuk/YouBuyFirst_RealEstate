# 현재 작업 인수인계

마지막 갱신: 2026-05-24

새 채팅이 방향을 잡는 짧은 요약입니다. 전문 읽기를 기본값으로 두지 말고 필요한 섹션만 확인합니다.

## 현재 상태

- Repository: `99hyuk/YouBuyFirst`
- Default branch: `main`
- 루트 checkout: `C:\agents\YouBuyFirst`는 main/조율용, 병렬 작업은 `.worktrees/<task>`에서 진행합니다.
- 최근 ops 정리: 문서 트리 구조, 도메인/layer `AGENTS.md`, 루트 QA 산출물 정리 기준이 `main`에 반영되어 있습니다.
- 기반: Spring Boot backend, Python pipeline, MySQL, Docker Compose, Vue 3 front mock shell

## 구현 스냅샷

- MVP는 커뮤니티 글 수집, 종목 언급 인식, 반응 방향 분석, backend 저장까지 연결된 ingestion 기반입니다.
- backend에는 ingestion/admin API, crawl run/posts/stock metrics 조회, `CrawlTarget` queue API가 있습니다.
- pipeline에는 source policy gate, skip run 기록, crawl backoff, AI mention resolver/mock provider 흐름이 있습니다.
- front는 `front/`의 Vue 3 + Vite + TypeScript mock 와이어프레임 shell입니다. 대시보드와 디자인/구현 정본은 현재 `front/` 코드와 짧은 `docs/layers/ui/WIREFRAME_HANDOFF.md`입니다. 과거 세부 로그는 `docs/archive/front/wireframe/`에서 필요할 때만 검색합니다.
- 화면별 기획, route, 하위 상세 화면, API 후보는 `docs/layers/ui/screens/`를 봅니다.
- 최종 제품은 전체 랭킹보다 관심종목 브리핑, 종목별 기사/공시/커뮤니티/가격 이벤트 타임라인, 신호 신뢰도/주의 배지를 매일 쓰는 투자자 루프로 강화합니다.
- 기획 정리 구간은 ui-first discovery로 갑니다. mock 화면을 먼저 세우고, API/데이터 계약은 화면에서 필요한 항목을 역으로 도출합니다.

## 최근 결정

- 새 채팅은 루트 `AGENTS.md`와 이 문서를 읽고, 작업 영역이 정해지면 해당 `docs/domains/.../AGENTS.md` 또는 `docs/layers/.../AGENTS.md`만 추가로 봅니다.
- 문서 구조는 `product`, `current`, `domains`, `layers`, `governance`, `archive`로 봅니다. 작업 영역은 domain/layer 기준이고, 기존 track 값은 PR/라벨/Notion 호환용 alias로만 봅니다.
- PR 제목, GitHub 라벨, Notion `트랙` 속성은 아직 legacy 값을 유지합니다. 다음 ops 작업에서 `area:*` 또는 `domain:*`/`layer:*` 기준으로 바꿀지 결정합니다.
- handoff에는 최신 기준과 상세 문서 위치만 남깁니다. 긴 근거, 과거 설계, 검증 로그는 도메인 문서나 archive로 넘깁니다.
- 채팅 오류는 제품 코드보다 대화 컨텍스트/도구 출력 과다를 먼저 의심합니다. 스킬 문서, gstack, Notion fetch, 세션 로그 검색은 시작 루틴이 아닙니다.
- 브랜치는 실제 PR 후보가 있을 때 열고, merge/close/대체 후에는 worktree와 함께 정리합니다. 열린 브랜치는 active, review, blocked, stale, close-candidate 중 하나로 설명할 수 있어야 합니다.
- 사용자 보고는 파일명/폴더명 나열보다 무엇이 해결됐고 이제 무엇을 판단하면 되는지 먼저 말합니다.
- 제품 핵심은 `커뮤니티 반응`과 `개미 심리 지수`입니다. 관심종목은 이 지표를 매일 쓰게 만드는 필터/개인화 레이어입니다.
- 제품명은 붙여 쓴 `너나사`를 기본 브랜드명으로 씁니다. 풀어서 설명할 때만 `너나 사` 말장난을 제한적으로 씁니다.
- 부동산은 주식 MVP에 섞지 않고 후순위 별도 버티컬로만 검토합니다.
- market MVP는 quote/chart를 `yfinance` + FinanceDataReader 조합으로 다루고, 국내 수급은 quote와 분리합니다. 화면에는 지연, provider, `asOf`, `stale`, 참고용 표시가 필요합니다. 상세 기준은 `docs/domains/market/README.md`, `docs/domains/market/CHART_CANDLES.md`, `docs/domains/market/INVESTOR_FLOWS.md`를 봅니다.
- 종목 상세 상단의 강한 한줄평은 커뮤니티 요약이 아니라 시황/기술지표/재무 기반 `종목 상태 팩트폭격 헤드라인`입니다. 생성 기준은 `docs/domains/agent/STOCK_DETAIL_HEADLINE.md`, UI 표현은 `docs/layers/ui/STOCK_DETAIL_BANNER.md`를 봅니다.
- 디자인과 프론트 구현은 기본적으로 Codex가 `front/` 코드에서 함께 진행합니다. Figma AI/Stitch는 사용자가 명시적으로 요청할 때만 참고 시안 탐색용으로 씁니다.
- 사용자 화면에서 `추천`, `매수`, `매도`, `수익 보장`, `진입`, `시그널 확정`처럼 투자 행동을 지시하는 표현은 서비스 판단이나 CTA로 쓰지 않습니다.
- 소스 상태는 `enabled`, `public-demo-only`, `local-research-only`, `disabled`로 나누며 새 소스는 기본 `disabled`입니다. 공개 배포 전에는 원문 재게시, 작성자 추적, 닉네임 랭킹을 하지 않습니다.
- `simulation`은 가상 주문, 체결, 정산, 원장, 포지션의 트랜잭션 정합성을 보여줍니다. `agent`는 통계 윈도우 기반 판단을 남기고, 체결/원장 수정은 `simulation` contract를 통합니다.
- 최종 기획상 생길 수 있는 기술/제품/운영 이슈는 `docs/governance/TECHNICAL_RISK_REGISTER.md`에 누적합니다. 실제 장애 복구 기록은 `docs/governance/TROUBLESHOOTING_GUIDE.md`와 PR/Notion 작업 로그에 남깁니다.

## 바로 가기

- 작업 영역: `docs/layers/ops/WORK_AREAS.md`
- 문서/컨텍스트 예산: `docs/layers/ops/DOCUMENTATION_GUIDE.md`
- 기술 리스크 목록: `docs/governance/TECHNICAL_RISK_REGISTER.md`
- 제품/기술 고민 메모: `docs/product/PRODUCT_DECISION_NOTES.md`
- 작업 방식: `docs/layers/ops/WORKFLOW.md`
- Git/PR 규칙: `docs/layers/ops/GIT_CONVENTION.md`
- 라벨: `docs/layers/ops/LABEL_GUIDE.md`
- Notion 정본 위치: `docs/layers/ops/DOCUMENTATION_GUIDE.md`, `docs/layers/ops/ENGINEERING_EVIDENCE_GUIDE.md`

## 다음 작업 후보

- UI: dashboard, stock detail, briefing, event timeline 화면을 실제 브라우저로 확인하고 Screen Brief를 최신 기준으로 유지합니다.
- market: chart candles, quote snapshot, investor flows provider를 분리해 안정화합니다.
- community/indicator: source registry, 인기글/개념글 확산 레이어, 신뢰 블로그 whitelist, 종목 언급/개미 심리 지수 계약을 정리합니다.
- simulation/agent: 모의 계좌/주문/체결/원장 트랜잭션과 agent 판단 key/idempotency를 설계합니다.
- backend/pipeline: `CrawlTarget` 연동, readiness wait, Swagger 예시, validation 오류 응답, 도메인 패키지 리네임 후보를 정리합니다.
- ops: 열린 브랜치/worktree와 오래된 문서 표현을 주기적으로 정리합니다.
