# Work Unit: Initial MVP

## Goal

Build the first YouBuyFirst data pipeline MVP.

## Scope

- Spring Boot ingestion/admin APIs
- MySQL/Flyway schema
- Python crawler/LLM pipeline
- Docker Compose runtime
- Project context and workflow docs

## Verification

- Backend Docker test: passed, 2 tests.
- Pipeline Docker test: passed, 4 tests.
- Docker Compose: starts MySQL, backend, pipeline.
- Manual pipeline run: stores Naver and FM Korea crawl runs.

## Notes

This initial work is intentionally larger than future PRs because it bootstraps an empty repository. Future work should be split into smaller feature PRs.

