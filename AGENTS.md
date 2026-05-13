# Agent Working Guide

This repository implements the Human Indicator MVP: a community crawling and sentiment ingestion pipeline.

## Product Goal

Collect new posts from Naver Finance discussion boards and FM Korea stock boards every 30 minutes, detect mentions of Korean stocks plus US-listed stocks/ETFs, classify each mention as `bullish`, `bearish`, or `neutral`, and persist metrics through the Spring Boot backend.

## Current Architecture

- `backend/`: Spring Boot 3.3, Java 21, JPA, Flyway, MySQL, Swagger.
- `worker/`: Python worker with APScheduler, HTTPX, BeautifulSoup, Playwright fallback, OpenAI provider abstraction.
- `docker-compose.yml`: local MySQL + backend + worker runtime.

## Boundaries

- Do not add dashboard UI, OCR asset sync, real trading, or login/security unless a task explicitly asks for it.
- Do not add CAPTCHA bypass, login-session scraping, proxy rotation, or fingerprint evasion.
- Prefer public HTTP crawling first; use Playwright only as a rendering fallback.
- Keep stored raw content limited to title, content snippet, URL, author hash, published time, and content hash.

## Verification Commands

Backend:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn test
```

Worker:

```bash
docker run --rm -v "${PWD}/worker:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
```

Local app:

```bash
docker compose up --build -d
docker compose ps
```

Swagger:

```text
http://localhost:8080/swagger-ui.html
```

## Branch/PR Habit

Use one branch per work unit. This is a hard project habit: one feature, bugfix, or infrastructure change maps to one PR.

```text
codex/<short-task-name>
```

Before opening a PR:

1. Read `docs/CONTEXT.md`.
2. Read `docs/CURRENT_HANDOFF.md`.
3. Create or update a file in `docs/work-units/`.
4. Run relevant tests.
5. Update `docs/CURRENT_HANDOFF.md` and `docs/TASKS.md` if the task changes project state or scope.
6. Use `scripts/open-pr.ps1` when GitHub remote and `gh` are configured.

Do not mix unrelated backend, worker, infrastructure, and product-scope changes in one PR unless the repository is being bootstrapped.

## Planning References

- Final product vision: `docs/FINAL_PRODUCT_PLAN.md`
- Current MVP scope: `docs/PROJECT_BRIEF.md`
- Current handoff state: `docs/CURRENT_HANDOFF.md`
- PR workflow: `docs/WORKFLOW.md` and `docs/PR_AUTOMATION.md`
