# Context Handoff

Use this file at the start of a new chat or when handing work to another agent. For the newest short summary, read `docs/CURRENT_HANDOFF.md` first.

## Product

Human Indicator is a simulated investment product that turns community crowd psychology into stock-level indicators. The final product vision is documented in `docs/FINAL_PRODUCT_PLAN.md`. The current MVP is only the data pipeline: crawl community posts, detect stock mentions, classify investment sentiment, and store/query metrics.

## Current MVP

- Sources: Naver Finance discussion boards and FM Korea stock board.
- Backend: Spring Boot owns ingestion, validation, persistence, metrics, and Swagger admin APIs.
- Worker: Python owns crawling, Playwright rendering fallback, instrument matching, and LLM sentiment analysis.
- Runtime: Docker Compose starts MySQL, backend, and worker.

## Important Decisions

- Work conservatively: one branch and one PR per feature or bugfix.
- Keep PRs small enough to review and debug.
- Keep `docs/CURRENT_HANDOFF.md` updated so future chats can continue without reconstructing context.
- No dashboard, OCR, real trading, user auth, proxy rotation, CAPTCHA bypass, or login-session scraping in this MVP.
- Store limited raw content only: title, content snippet, URL, author hash, published time, content hash.
- `OPENAI_API_KEY` enables OpenAI analysis; otherwise the worker uses mock sentiment for local demos.
- MySQL host port is `3307` to avoid colliding with local MySQL on `3306`.

## Working URLs

- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/swagger-ui.html`
- MySQL: `localhost:3307`

## Verification Snapshot

Last known local checks:

- Backend Docker test: passed, 2 tests.
- Worker Docker test: passed, 4 tests.
- Docker Compose: starts MySQL, backend, worker.
- Manual worker batch: successfully stored Naver and FM Korea crawl runs.

## Read First

1. `AGENTS.md`
2. `docs/CURRENT_HANDOFF.md`
3. `docs/FINAL_PRODUCT_PLAN.md`
4. `docs/PROJECT_BRIEF.md`
5. `docs/TASKS.md`
6. `docs/WORKFLOW.md`
7. Latest file in `docs/work-units/`
