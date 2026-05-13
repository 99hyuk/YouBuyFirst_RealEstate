# Work Unit: Initial MVP

## Goal

Build the first Human Indicator data pipeline MVP.

## Scope

- Spring Boot ingestion/admin APIs
- MySQL/Flyway schema
- Python crawler/LLM worker
- Docker Compose runtime
- Project context and workflow docs

## Verification

- Backend Docker test: passed, 2 tests.
- Worker Docker test: passed, 4 tests.
- Docker Compose: starts MySQL, backend, worker.
- Manual worker run: stores Naver and FM Korea crawl runs.

## Notes

This initial work is intentionally larger than future PRs because it bootstraps an empty repository. Future work should be split into smaller feature PRs.

