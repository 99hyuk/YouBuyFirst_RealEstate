# 현재 작업 인수인계

마지막 갱신: 2026-05-21

새 채팅이 방향을 잡는 짧은 요약입니다. 전문 읽기를 기본값으로 두지 말고 필요한 섹션만 확인합니다.

## 현재 상태

- Repository: `99hyuk/YouBuyFirst`
- Default branch: `main`
- 루트 checkout: `C:\agents\YouBuyFirst`는 main/조율용, 병렬 작업은 `.worktrees/<task>`에서 진행합니다.
- 최근 머지된 ops 규칙 PR: PR #60 `[ops][docs] PR 템플릿 적용 규칙 보강`
- 기반: Spring Boot backend, Python pipeline, MySQL, Docker Compose, Vue 3 front mock shell

## 구현 스냅샷

- MVP는 커뮤니티 글 수집, 종목 언급 인식, 반응 방향 분석, backend 저장까지 연결된 ingestion 기반입니다.
- backend에는 ingestion/admin API, crawl run/posts/stock metrics 조회, `CrawlTarget` queue API가 있습니다.
- pipeline에는 source policy gate, skip run 기록, crawl backoff, AI mention resolver/mock provider 흐름이 있습니다.
- front는 `front/`의 Vue 3 + Vite + TypeScript mock 와이어프레임 shell입니다. 대시보드와 디자인/구현 정본은 현재 `front/` 코드와 짧은 `docs/workstreams/front/WIREFRAME_HANDOFF.md`입니다. 과거 세부 로그는 `docs/workstreams/front/archive/`에서 필요할 때만 검색합니다.
- 화면별 기획, route, 하위 상세 화면, API 후보는 `docs/workstreams/front/screens/`를 봅니다.
- 최종 제품은 전체 랭킹보다 관심종목 브리핑, 종목별 기사/공시/커뮤니티/가격 이벤트 타임라인, 신호 신뢰도/주의 배지를 매일 쓰는 투자자 루프로 강화합니다.
- 기획 정리 구간은 front-first discovery로 갑니다. mock 화면을 먼저 세우고, API/데이터 계약은 화면에서 필요한 항목을 역으로 도출합니다.

## 최근 결정

- 문서는 길게 누적하지 않습니다. `AGENTS.md`, 이 문서, 스킬 문서, Notion, 세션 로그는 필요한 섹션만 봅니다.
- 채팅이 `앗, 오류가 발생했습니다`로 막히면 제품 코드보다 대화 컨텍스트/도구 출력 과다를 먼저 의심합니다.
- 스킬 문서, gstack, Notion fetch, 세션 로그 검색은 시작 루틴이 아닙니다.
- 큰 스킬 문서와 `docs/superpowers/` archive는 전문 출력하지 않습니다. Browser/gstack 검증은 필요할 때 한 번에 모아 실행합니다.
- 에이전트 행동 규칙 PR이 main에 머지되면 ops가 열린 장기 브랜치의 main 반영 여부를 확인합니다.
- 브랜치는 실제 PR 후보가 있을 때 열고, merge/close/대체 후에는 worktree와 함께 정리합니다. 열린 브랜치는 active, review, blocked, stale, close-candidate 중 하나로 설명할 수 있어야 합니다.
- 사용자 보고는 파일명/폴더명 나열보다 무엇이 해결됐고 이제 무엇을 판단하면 되는지 먼저 말합니다.
- gstack은 front/UI 변경처럼 실제 브라우저 확인 가치가 있을 때 사용하고, 콘솔/DOM 전문은 대화에 누적하지 않습니다.
- 로그/세션 분석은 JSONL 전문 검색이 아니라 `token_count` 같은 필요한 이벤트만 파싱해 수치로 요약합니다.
- 제품 용어는 사용자 화면에서 `커뮤니티 반응`, 단일 분석값은 `반응 방향`, 내부 후보 필드는 `reactionDirection`을 씁니다.
- 커뮤니티 기반 대표 점수는 `개미 심리 지수`로 둡니다. 0-100 점수로 종목/기간별 낙관, 비관, 과열, 무관심 정도를 보여주되 매수/매도 신호가 아니라 관찰 지표로 표시합니다.
- 제품명은 문서/화면/PR에서 붙여 쓴 `너나사`를 기본 브랜드명으로 씁니다. 풀어서 설명할 때만 `너나 사` 말장난을 제한적으로 씁니다.
- 제품 핵심은 관심종목 앱이 아니라 커뮤니티 반응 지표입니다. 관심종목은 커뮤니티 지표를 매일 쓰게 만드는 필터/개인화 레이어로 둡니다.
- 부동산은 주식 MVP에 섞지 않고 후순위 별도 버티컬로만 검토합니다. SSAFY 관통프로젝트 주제와 병행할 수는 있지만, 너나사 주식 서비스의 핵심 범위는 주식/ETF 커뮤니티 반응 분석입니다.
- market MVP 데이터 공급자는 `yfinance` + FinanceDataReader 조합으로 정합니다. `yfinance`는 국내/미국 시세와 거래량의 1차 provider, FinanceDataReader는 국내 종목 메타데이터와 전 거래일 수급 후보 provider로 둡니다. `.KS`/`.KQ` quote는 Yahoo Finance 원천 20분 지연과 pipeline 기본 10분 갱신 주기를 합쳐 최대 30분 지연으로 표시합니다. 미국 quote는 지연 시간을 단정하지 않고 10분 주기 refresh snapshot으로 표시합니다. 개인/외국인/기관 수급은 quote snapshot과 분리해 전 거래일 기준 데이터로만 다룹니다. `pykrx`는 기본 조합에서 빼고 KRX 수급 검증이 필요할 때만 보조 후보로 봅니다. 공개 화면에는 `지연 데이터`, provider, `asOf`, `stale`, `참고용` 표시가 필수입니다.
- 종목 상세 상단의 강한 한줄평은 커뮤니티 요약이 아니라 시황/기술지표/재무 기반 `종목 상태 팩트폭격 헤드라인`입니다. 프론트 배너뿐 아니라 backend/API 계약 후보이며, `headlineTone`, `headline`, `subtitle`, `evidence`, `asOf`, `dataQuality`, `personalizedSafe` 기준은 `docs/STOCK_DETAIL_COPY_GUIDE.md`를 봅니다.
- 디자인과 프론트 구현은 기본적으로 Codex가 `front/` 코드에서 함께 진행합니다. Figma AI/Stitch는 기본 흐름이 아니며, 사용자가 명시적으로 요청할 때만 참고 시안 탐색용으로 씁니다.
- 현재 디자인 판단 기준은 `docs/workstreams/front/README.md`의 `현재 디자인 우선순위` 섹션입니다. 가독성, 정보 밀도, 전문적인 차트 느낌, 토스증권/야선식 직관성을 우선하고, 다크/라이트 테마는 후속 작업으로 둡니다.
- 사용자 화면에서 `추천`, `매수`, `매도`, `수익 보장`, `진입`, `시그널 확정`처럼 투자 행동을 지시하는 표현은 서비스 판단이나 CTA로 쓰지 않습니다.
- 소스 상태는 `enabled`, `public-demo-only`, `local-research-only`, `disabled`로 나누며 새 소스는 기본 `disabled`입니다.
- 소스 후보에는 네이버 종토방, 에펨코리아 주식, 뽐뿌 증권포럼, 디시 미국 주식 갤러리, 디시 주식갤러리/국내주식 계열을 포함합니다. 디시 계열은 이름 하드코딩 대신 source/board registry로 관리합니다.
- 블로그는 전체 검색 결과보다 신뢰 블로그 whitelist를 추적하고, 인기글/개념글/추천글/조회수 상위글은 초기 감지가 아니라 이슈 확산 확인 레이어로 둡니다.
- 공개 배포 전에는 원문 재게시, 작성자 추적, 닉네임 랭킹을 하지 않습니다.
- `trade`는 실제 결제나 실거래가 아니라 가상 주문, 체결, 정산, 원장, 포지션의 트랜잭션 정합성을 보여주는 트랙입니다. 동시 클릭 경쟁보다 에이전트 판단/주문/체결 idempotency와 원장 기반 손익 재계산을 우선합니다.
- `agent`는 통계 윈도우를 보고 paper trading 결정을 남기며, `agentId + windowStart + symbol + strategyVersion` 같은 판단 key로 중복 판단을 막습니다. 체결 장부 수정은 `trade` contract를 통합니다.
- 최종 기획상 생길 수 있는 기술/제품/운영 이슈는 `docs/TECHNICAL_RISK_REGISTER.md`에 누적합니다. 실제 장애 복구 기록은 `docs/TROUBLESHOOTING_GUIDE.md`와 PR/Notion 작업 로그에 남깁니다.

## 바로 가기

- 트랙 경계: `docs/workstreams/`
- 문서/컨텍스트 예산: `docs/DOCUMENTATION_GUIDE.md`
- 기술 리스크 목록: `docs/TECHNICAL_RISK_REGISTER.md`
- 제품/기술 고민 메모: `docs/PRODUCT_DECISION_NOTES.md`
- 작업 방식: `docs/WORKFLOW.md`
- Git/PR 규칙: `docs/GIT_CONVENTION.md`
- 라벨: `docs/LABEL_GUIDE.md`
- Notion 정본 위치: `docs/DOCUMENTATION_GUIDE.md`, `docs/ENGINEERING_EVIDENCE_GUIDE.md`

## 다음 작업 후보

- front shell 브라우저 QA와 기획자 확인 필요 항목 정리
- front 메인 대시보드 와이어프레임 보강
- front 관심종목 브리핑과 종목 이벤트 타임라인 와이어프레임 설계
- 관심종목, 최신 기사/공시, 신호 신뢰도 API 후보 설계
- 유튜브/신뢰 블로그/인기글 링크 카드와 종목 이벤트 타임라인 field 후보 설계
- pipeline이 backend `CrawlTarget` API를 사용하되 static target fallback 유지
- admin target pause/resume/clear-backoff API와 화면 액션 연결
- 열린 브랜치/worktree 정리 후보 점검
- 종목 상세 실제 차트용 chart candle display API 구현
- front quote fixture를 `GET /api/quotes` 호출로 교체
- pipeline `quote-push` 10분 주기 실행 연결
- KODEX 200 기준 전 거래일 개인/외국인/기관 수급 slice 설계
- trade 모의 계좌/주문/체결/원장 트랜잭션 설계
- agent paper trading 판단 key와 중복 실행 방지 설계
- crawl source registry에 뽐뿌/디시 미주갤/주식갤/국내주식 계열 후보 정리
- crawl 인기글/개념글 확산 레이어와 신뢰 블로그 whitelist 후보 정리
- 실제 `OPENAI_API_KEY` 기반 AI mention resolver 샘플 품질 확인
- pipeline이 backend readiness를 기다리도록 개선
- admin API Swagger 예시와 validation 오류 응답 정리
- backend 도메인 패키지를 `stock`, `analysis`, `indicator` 목표 이름으로 리네임
