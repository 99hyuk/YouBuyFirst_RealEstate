# Context Handoff

새 채팅이나 다른 에이전트에게 작업을 넘길 때 이 파일을 읽습니다. 가장 최신 상태 요약은 `docs/CURRENT_HANDOFF.md`를 먼저 봅니다.

## 제품

너나사 (YouBuyFirst)는 커뮤니티 반응, 시장 시세, AI 분석, 모의투자를 결합한 투자 참고형 시뮬레이터입니다. 최종 제품 방향은 `docs/FINAL_PRODUCT_PLAN.md`에 있고, 현재 실행 기반은 데이터 파이프라인 MVP입니다. 커뮤니티 분석 용어와 소스별 수집 전략은 `docs/COMMUNITY_REACTION_GUIDE.md`를 기준으로 합니다. 이후 구현은 `docs/workstreams/`의 병렬 트랙 단위로 진행합니다.

## 현재 MVP

- Source: 네이버 종토방, 에펨코리아 주식 게시판
- Backend: Spring Boot가 ingestion, validation, persistence, indicator, Swagger admin API를 담당
- Pipeline: Python이 crawling, Playwright rendering fallback, stock matching, LLM analysis를 담당
- Runtime: Docker Compose가 MySQL, backend, pipeline을 실행
- 30분 집계는 유지하되, 공개 배포 시 소스별 활성화 상태를 관리합니다.

## 중요한 결정

- 한 작업은 한 브랜치와 한 PR로 처리합니다.
- PR은 작게 유지합니다. 선호는 5개 파일 이하, 허용은 10개 파일 이하입니다.
- 사용자용 스크립트는 두지 않고, 에이전트가 `git`과 `gh`를 직접 사용합니다.
- PR 제목과 커밋 본문은 한국어로 작성합니다.
- PR 제목은 `[트랙][타입] 명사형 요약` 형식을 씁니다.
- 담당 트랙과 명시 요청 없이 OCR, 실거래, user auth, proxy rotation, CAPTCHA bypass, login-session scraping을 넣지 않습니다.
- 원문은 제한 저장합니다: title, content snippet, URL, author hash, published time, content hash.
- 공개 UI는 원문보다 집계 지표, 대표 키워드, 반응 방향 비율, AI 재서술 근거를 중심으로 보여줍니다.
- 병렬 작업은 `docs/workstreams/README.md`의 일곱 트랙으로 나눕니다.
- 트랙은 작업 관리 단위이고 코드 패키지는 도메인 단위입니다. 도메인 패키지 목표 이름은 `stock`, `analysis`, `indicator`, `market`, `trade`, `agent`입니다.
- 라벨은 `track:*`, `type:*`, `size:*`를 기본으로 쓰고, 실제 변경 표면이 분명할 때만 `part:*`를 추가합니다.
- `OPENAI_API_KEY`가 있으면 OpenAI 분석을 사용하고, 없으면 로컬 demo용 mock 반응 분석을 사용합니다.
- MySQL host port는 로컬 `3306` 충돌을 피하기 위해 `3307`을 사용합니다.

## Working URLs

- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/swagger-ui.html`
- MySQL: `localhost:3307`

## 마지막 검증 Snapshot

- PR #1 GitHub Actions: Backend pass, Pipeline pass
- Backend Docker test: pass, 2 tests
- Pipeline Docker test: pass, 4 tests
- Docker Compose: MySQL, backend, pipeline start 확인
- Manual pipeline batch: Naver와 FM Korea crawl run 저장 확인

## 시작 시 확인

새 채팅은 전문 읽기가 아니라 작업에 필요한 섹션 확인으로 시작합니다.

1. `AGENTS.md`와 `docs/CURRENT_HANDOFF.md`의 관련 줄만 확인합니다.
2. 트랙이 명확하면 담당 트랙 README를 봅니다.
3. 트랙 경계가 헷갈릴 때만 `docs/workstreams/README.md`를 봅니다.
4. 문서/컨텍스트/Notion 규칙을 바꿀 때만 `docs/DOCUMENTATION_GUIDE.md`와 `docs/WORKFLOW.md`의 관련 섹션을 봅니다.
5. PR 직전에만 `docs/GIT_CONVENTION.md`와 `docs/LABEL_GUIDE.md`의 필요한 섹션을 봅니다.

필요할 때만 `docs/FINAL_PRODUCT_PLAN.md`, `docs/PROJECT_BRIEF.md`, `docs/TASKS.md`, `docs/LEGAL_RISK_CASES.md`, `docs/TROUBLESHOOTING_GUIDE.md`, `docs/work-units/`를 검색해서 봅니다.
