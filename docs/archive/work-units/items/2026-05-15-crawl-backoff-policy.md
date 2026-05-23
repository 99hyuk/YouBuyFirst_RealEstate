# Work Unit: Crawl Backoff Policy

## Goal

Stop the same long-running pipeline process from repeatedly calling a source immediately after block or failure signals.

## Scope

- Add in-memory backoff decisions inside `CommunityPipeline`.
- Classify blocked, transient, and unknown crawler errors into different retry windows.
- Record active backoff skips as backend `SKIPPED` crawl runs.
- Include readable backoff metadata in local results and backend `errorMessage`.

## Out of Scope

- Persistent DB-backed backoff state.
- Admin UI for backoff inspection or override.
- Cross-process locking.
- New crawler sources.

## Human Explanation

This is the difference between "we know a run failed" and "we changed the next action because it failed." A block or rate limit should cool down for hours. A timeout can retry sooner. Parser-like unknown errors should pause long enough to avoid noisy repeated failures.

## Verification

- Backoff unit tests cover category and retry-window decisions.
- Pipeline tests cover active backoff skipping external fetches.
- Full pipeline Docker test suite passed with 30 tests.
- `git diff --check` passed.
