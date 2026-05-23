# Crawl Backoff Policy Design

## Background

The crawler already records whether a run succeeded, failed, was blocked, or was skipped by source policy. That tells an operator what happened, but it does not yet change the next run. If a source returns `403` or `429`, the current scheduler can try the same source again on the next interval and repeat a request that should cool down.

Backoff means: when a crawl fails for a known reason, the pipeline remembers a temporary "do not retry before this time" decision for that source target.

## Human Rule

Not all failures deserve the same next action.

- A normal empty success means "keep the normal schedule."
- A temporary network/server error means "wait a little, then retry."
- A block or rate-limit signal means "wait much longer before touching that source again."
- A source policy skip is not a failure; source policy already controls it.

## Goal

Add an in-memory crawl backoff policy that prevents repeated external requests during the same long-running pipeline process after blocked or failed runs.

## Scope

- Add a pipeline backoff policy module.
- Classify failures into:
  - `blocked`: `SourceBlockedError`, usually `403` or `429`, retry after 6 hours.
  - `transient-error`: timeout, network, or `5xx` HTTP errors, retry after 15 minutes.
  - `unknown-error`: parser/runtime errors that are not clearly temporary, retry after 60 minutes.
- Store active backoff decisions in the `CommunityPipeline` instance keyed by `targetId` when available, otherwise by source.
- When backoff is active, skip `adapter.fetch_posts()`, record a backend `SKIPPED` crawl run, and return a local result with `status=backoff`.
- Include `backoffCategory`, `backoffSeconds`, `backoffUntil`, and `backoffReason` in local results and backend `errorMessage`.

## Out Of Scope

- DB columns for persistent backoff state.
- Admin UI for editing backoff.
- Cross-process coordination.
- New crawler sources.
- Changing source policy status meanings.

## Why In-Memory First

This is useful for the current `serve` runtime because APScheduler keeps the same Python process alive. It also avoids a larger backend schema/API PR. If the process restarts, backoff state is lost; that is acceptable for this step and should be solved later with a persistent `CrawlTarget` queue.

## Verification

- Unit tests verify failure classification and retry windows.
- Pipeline tests verify a blocked run sets backoff and the next run skips fetch.
- Pipeline tests verify a transient error records a shorter backoff.
- Full pipeline Docker test suite passes.
