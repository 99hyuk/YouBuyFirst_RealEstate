# Context Handoff

새 채팅이나 다른 에이전트에게 작업을 넘길 때 이 파일을 읽습니다. 가장 최신 상태 요약은 `docs/CURRENT_HANDOFF.md`를 먼저 봅니다.

## 제품

너나사 (YouBuyFirst)는 커뮤니티 군중 심리를 종목 단위 지표로 바꾸는 모의투자/분석 제품입니다. 최종 제품 방향은 `docs/FINAL_PRODUCT_PLAN.md`에 있고, 현재 MVP는 데이터 파이프라인에 집중합니다.

## 현재 MVP

- Source: 네이버 종토방, 에펨코리아 주식 게시판
- Backend: Spring Boot가 ingestion, validation, persistence, metrics, Swagger admin API를 담당
- Worker: Python이 crawling, Playwright rendering fallback, instrument matching, LLM sentiment analysis를 담당
- Runtime: Docker Compose가 MySQL, backend, worker를 실행

## 중요한 결정

- 한 작업은 한 브랜치와 한 PR로 처리합니다.
- PR은 작게 유지합니다. 선호는 5개 파일 이하, 허용은 10개 파일 이하입니다.
- 사용자용 스크립트는 두지 않고, 에이전트가 `git`과 `gh`를 직접 사용합니다.
- PR 제목과 커밋 본문은 한국어로 작성합니다.
- PR 제목은 `[타입][영역] 한국어 요약` 형식을 씁니다.
- 현재 MVP에는 dashboard, OCR, 실거래, user auth, proxy rotation, CAPTCHA bypass, login-session scraping을 넣지 않습니다.
- 원문은 제한 저장합니다: title, content snippet, URL, author hash, published time, content hash.
- `OPENAI_API_KEY`가 있으면 OpenAI 분석을 사용하고, 없으면 로컬 demo용 mock sentiment를 사용합니다.
- MySQL host port는 로컬 `3306` 충돌을 피하기 위해 `3307`을 사용합니다.

## Working URLs

- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/swagger-ui.html`
- MySQL: `localhost:3307`

## 마지막 검증 Snapshot

- PR #1 GitHub Actions: Backend pass, Worker pass
- Backend Docker test: pass, 2 tests
- Worker Docker test: pass, 4 tests
- Docker Compose: MySQL, backend, worker start 확인
- Manual worker batch: Naver와 FM Korea crawl run 저장 확인

## Read First

1. `AGENTS.md`
2. `docs/CURRENT_HANDOFF.md`
3. `docs/FINAL_PRODUCT_PLAN.md`
4. `docs/PROJECT_BRIEF.md`
5. `docs/TASKS.md`
6. `docs/WORKFLOW.md`
7. `docs/GIT_CONVENTION.md`
8. Latest file in `docs/work-units/`
