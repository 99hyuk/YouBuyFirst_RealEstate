# Crawl Policy Skip Run Record Design

## Background

Source policy gate already stops crawler adapters before any remote request when a source is disabled or not allowed in the current runtime. That behavior is safe, but the current backend run history cannot show why nothing was fetched because skipped targets are only returned from the local pipeline result.

Operators need to see policy skips in the same inspection path as successful and failed crawl runs:

```text
/admin/crawl-runs -> source, runId, status, errorMessage
```

## Goal

Record policy-denied crawler executions as backend `crawl_runs` rows with status `SKIPPED`, zero posts seen, zero posts accepted, and a readable skip message.

## Scope

- Add `SKIPPED` to the backend `CrawlRunStatus` contract.
- Keep the existing `crawl_runs.status` column because it is `varchar(20)`, not a database enum.
- Record skipped runs from `CommunityPipeline.run_once()` before continuing to the next adapter.
- Include target and source policy context in `errorMessage` so `/admin/crawl-runs` is useful without a schema change.
- Preserve local pipeline result status as `skipped`.

## Out Of Scope

- Backend target columns or a persistent target queue.
- Admin UI for changing source status.
- Source approval for public crawling.
- New crawler sources.
- Backoff scheduling.

## Skip Message

Skipped run messages use compact key-value text:

```text
targetId=NAVER:KR:005930; sourceStatus=local-research-only; runtimeEnvironment=public; reason=source policy local-research-only is not allowed in public runtime
```

This keeps the current ingestion payload stable while making admin history searchable by target id, source status, runtime, and reason.

## Verification

- Backend integration test accepts and exposes `SKIPPED` crawl runs through `/admin/crawl-runs`.
- Pipeline source policy tests verify skipped sources do not fetch remote posts and do record a backend run.
- Full backend and pipeline Docker test suites pass.
