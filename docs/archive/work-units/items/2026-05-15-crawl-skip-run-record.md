# Work Unit: Crawl Policy Skip Run Record

## Goal

Make source policy skips visible in backend crawl run history without treating them as failures.

## Scope

- Add backend `CrawlRunStatus.SKIPPED`.
- Record skipped pipeline runs through the existing backend crawl run report endpoint.
- Keep skipped runs at zero posts seen and zero posts accepted.
- Include target id, source status, runtime environment, and skip reason in `errorMessage`.
- Preserve existing local pipeline result status `skipped`.

## Out of Scope

- Backend schema changes for target columns.
- Admin UI or source status editing.
- Public approval for any source.
- Retry/backoff queue behavior.

## Verification

- Backend Docker test suite passed with 3 tests.
- Pipeline Docker test suite passed with 24 tests.
- `git diff --check` passed.

## Notes

`crawl_runs.status` is a string column, so this work only needs the Java enum contract update. Target-specific persistence remains a follow-up once the persistent `CrawlTarget` queue is designed.
