# Work Unit: CrawlTarget Backend API

## Goal

Persist crawl targets in the backend and expose the first worker/admin contract for target scheduling.

## Scope

- Add `crawl_targets` Flyway migration and seed the first NAVER/FM Korea targets.
- Add admin read endpoint for target status and backoff inspection.
- Add internal worker claim and completion endpoints.
- Add structured target/backoff fields to `crawl_runs`.
- Preserve the existing community post ingestion and crawl run reporting clients.

## Out Of Scope

- No Python pipeline runtime change in this PR.
- No admin/front UI in this PR.
- No public-source approval in this PR.
- No login, CAPTCHA, proxy, or fingerprint bypass work.

## Human Explanation

Before this work, the crawler could remember a temporary backoff only inside one running Python process. After a restart, that memory disappeared, and an admin page could not reliably explain which exact target was waiting.

Now the backend has a durable queue row per crawl target. In practice, the system can answer: this exact board is active, leased by a worker, waiting for its normal next attempt, or cooling down because a block/failure happened.

## Implementation Summary

- `GET /admin/crawl-targets` lists target status, priority, next attempt, last status, failure count, and backoff reason.
- `POST /internal/crawl-targets/claim` returns due `ACTIVE` targets from caller-provided `allowedSources` and leases them briefly.
- `POST /internal/crawl-targets/{targetId}/complete` updates success/failure state, releases the lease, schedules the next attempt, and persists backoff metadata.
- `POST /internal/ingestions/crawl-runs` now accepts optional structured target/backoff fields while keeping the old constructor/API shape usable.

## Verification

- Focused backend integration tests passed for admin target listing, claim filtering, lease duplicate prevention, success completion, blocked completion, and structured crawl run metadata.
- Full backend Docker Maven test passed: 8 tests.
- `git diff --check` passed.
- Placeholder scan passed.

## Follow-Up

- Connect the Python pipeline to claim/complete while keeping static target fallback for transition.
- Add admin pause/resume/clear-backoff actions with tests before wiring front controls.
