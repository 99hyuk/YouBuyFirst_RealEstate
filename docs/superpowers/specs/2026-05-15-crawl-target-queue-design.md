# CrawlTarget Queue And Persistent Backoff Design

## Background

The pipeline already has a `CrawlTarget` value object and an in-memory backoff map. That is enough for one running Python process, but it does not survive a restart and it cannot become an admin-managed queue.

The next step is to make `CrawlTarget` a backend-owned execution record. In plain terms: the system should remember "which board or stock discussion room should be crawled next, why it may be waiting, and when it is allowed to run again."

## Human Rule

There are two separate decisions.

1. Source policy decides whether a community source is allowed in this runtime.
   - Example: NAVER can be allowed in local research but not in public runtime.
2. `CrawlTarget` decides which specific board inside an allowed source should run next.
   - Example: NAVER KR:005930 can wait until 15:00 because it is under backoff.

The admin-facing meaning is: an operator should not only see that data is missing. They should see whether the source is disabled, the target is paused, the target is cooling down after failure, or it is simply waiting for its normal next slot.

## Goals

- Persist crawl targets in MySQL so target priority and backoff survive pipeline restarts.
- Keep source policy above target scheduling instead of mixing legal/runtime policy into every target row.
- Store target-level backoff in structured columns rather than parsing `crawl_runs.error_message`.
- Give future admin pages enough data to list targets, pause/resume a target, and clear a backoff.
- Keep the first implementation small enough to ship as backend contract first, then pipeline integration.

## Non-Goals

- This does not approve any source for public operation.
- This does not add new crawler sources.
- This does not implement front/admin UI yet.
- This does not add dynamic priority scoring from market data, user watchlists, or data-track signals.
- This does not add multi-region or high-throughput distributed scheduling.

## Core Concepts

### Source Policy

Source policy is the upper gate. It answers: "May this source send an external HTTP request in the current runtime?"

The existing states stay the source-level contract:

| Status | Meaning |
| --- | --- |
| `enabled` | May run in public and local runtime. |
| `local-research-only` | May run only in local or private research runtime. |
| `public-demo-only` | Public runtime uses sample/demo data, not live external requests. |
| `disabled` | No new external requests. |

Backend target selection should not duplicate the full source policy table in the first implementation. Instead, the pipeline should call the claim endpoint with `allowedSources`, computed from its current source policy registry and runtime.

### CrawlTarget

`CrawlTarget` is the concrete unit of work.

| Kind | Example target id | Meaning |
| --- | --- | --- |
| `stock-board` | `NAVER:KR:005930` | A source-specific board for one instrument. |
| `community-board` | `FMKOREA:community-board` | A general board where many instruments can appear. |

`target_id` must stay stable across backend and pipeline. The current Python format is already good enough for the first DB contract.

### Target Status

Target status is not the same as source policy.

| Status | Claimable | Meaning |
| --- | --- | --- |
| `ACTIVE` | Yes, when due and not under backoff | Normal queue target. |
| `PAUSED` | No | Operator temporarily stops one target without changing the whole source. |
| `DISABLED` | No | Target should not be scheduled anymore, but history remains. |

## Minimal Database Contract

Add `crawl_targets` as the queue table.

```sql
create table crawl_targets (
    id bigint not null auto_increment,
    source varchar(40) not null,
    target_id varchar(160) not null,
    target_kind varchar(40) not null,
    status varchar(20) not null,
    market varchar(20),
    symbol varchar(40),
    url varchar(1000),
    label varchar(200),
    priority integer not null,
    crawl_interval_seconds integer not null,
    next_attempt_at datetime(6) not null,
    last_attempt_at datetime(6),
    last_success_at datetime(6),
    last_status varchar(20),
    consecutive_failures integer not null,
    backoff_category varchar(40),
    backoff_until datetime(6),
    backoff_reason varchar(500),
    lease_owner varchar(120),
    leased_until datetime(6),
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_crawl_target_id unique (target_id)
);

create index idx_crawl_targets_due on crawl_targets (status, next_attempt_at, priority);
create index idx_crawl_targets_source_status on crawl_targets (source, status);
create index idx_crawl_targets_backoff_until on crawl_targets (backoff_until);
```

Field meaning:

| Field | Meaning |
| --- | --- |
| `priority` | Lower number runs earlier when multiple targets are due. Existing Python defaults keep NAVER at `100` and FMKOREA at `200`. |
| `crawl_interval_seconds` | Normal delay after a successful or empty run. Initial default is `1800`. |
| `next_attempt_at` | The earliest time this target can be claimed. |
| `backoff_until` | A stronger wait caused by blocked, transient, or unknown failures. |
| `consecutive_failures` | Resets to `0` on success, increments on failure. |
| `lease_owner` / `leased_until` | Prevents two workers from claiming the same target if a second worker is added later. |

Extend `crawl_runs` with structured target/backoff fields so admin views do not have to parse `error_message`.

```sql
alter table crawl_runs
    add column target_id varchar(160),
    add column target_kind varchar(40),
    add column backoff_category varchar(40),
    add column backoff_until datetime(6),
    add column backoff_reason varchar(500),
    add column skip_reason varchar(500);

create index idx_crawl_runs_target_started_at on crawl_runs (target_id, started_at);
```

`error_message` can remain as a human-readable fallback. Structured fields become the admin/API source of truth.

## Internal API Contract

### Claim Due Targets

`POST /internal/crawl-targets/claim`

Request:

```json
{
  "workerId": "pipeline-local-1",
  "runtimeEnvironment": "local",
  "allowedSources": ["NAVER", "FMKOREA"],
  "limit": 20
}
```

Response:

```json
{
  "targets": [
    {
      "source": "NAVER",
      "targetId": "NAVER:KR:005930",
      "targetKind": "stock-board",
      "market": "KR",
      "symbol": "005930",
      "url": null,
      "label": "NAVER KR:005930",
      "priority": 100
    }
  ]
}
```

Claim rules:

- Only `ACTIVE` targets are claimable.
- `next_attempt_at <= now` must be true.
- `backoff_until` must be null or in the past.
- `leased_until` must be null or expired.
- `source` must be in `allowedSources`.
- Claim sets `lease_owner` and `leased_until`.

### Complete Target Run

`POST /internal/crawl-targets/{targetId}/complete`

Request:

```json
{
  "workerId": "pipeline-local-1",
  "status": "SUCCESS",
  "startedAt": "2026-05-15T12:00:00Z",
  "finishedAt": "2026-05-15T12:00:12Z",
  "postsSeen": 10,
  "postsAccepted": 3,
  "backoffCategory": null,
  "backoffUntil": null,
  "backoffReason": null,
  "skipReason": null,
  "errorMessage": null
}
```

Completion rules:

| Result | Target update |
| --- | --- |
| `SUCCESS` | Clear backoff, reset failures, set `last_success_at`, set `next_attempt_at = finishedAt + crawl_interval_seconds`. |
| `SKIPPED` by source policy | Release lease and set `next_attempt_at = finishedAt + crawl_interval_seconds`; do not increment failures. |
| `PARTIAL_FAILURE` blocked | Store `blocked` backoff, increment failures, set `next_attempt_at = backoff_until`. |
| `FAILED` transient | Store `transient-error` backoff, increment failures, set `next_attempt_at = backoff_until`. |
| `FAILED` unknown | Store `unknown-error` backoff, increment failures, set `next_attempt_at = backoff_until`. |

The completion endpoint should also be able to write or update a structured `crawl_runs` record in the backend implementation. If the implementation keeps the existing ingestion endpoints for run history, the target completion endpoint must at least update the target row with the same run result.

## Admin API Contract

The first admin backend contract should be read-heavy.

| Endpoint | Purpose |
| --- | --- |
| `GET /admin/crawl-targets` | List targets with status, priority, next attempt, backoff, and last status. |
| `POST /admin/crawl-targets/{targetId}/pause` | Set one target to `PAUSED`. |
| `POST /admin/crawl-targets/{targetId}/resume` | Set one target to `ACTIVE` without clearing backoff. |
| `POST /admin/crawl-targets/{targetId}/clear-backoff` | Clear backoff and set `next_attempt_at = now`. |

Admin actions must not change source policy. Pausing one NAVER stock board is different from approving NAVER as a public source.

## Pipeline Flow

1. Build source policy registry from current config.
2. Compute `allowedSources` for the current runtime.
3. Claim due targets from backend.
4. Convert claimed targets into existing adapters.
5. Run the existing pipeline enrichment and ingestion.
6. Report target completion with structured backoff data.
7. If the backend target API is unavailable in local development, keep the current static target fallback for one transition PR.

This keeps the current crawler adapters small. The adapters should continue to know how to fetch one target, not how to decide the global queue.

## Backoff Rules

The persisted rules mirror the current in-memory policy.

| Category | Trigger | Retry window |
| --- | --- | --- |
| `blocked` | `SourceBlockedError`, usually `403` or `429` | 6 hours |
| `transient-error` | timeout, network, or `5xx` | 15 minutes |
| `unknown-error` | parser/runtime error that is not clearly temporary | 60 minutes |

Success clears backoff. Empty success is still success and should not increase failures.

## Implementation Split

1. Backend contract PR
   - Add `crawl_targets` table.
   - Add structured target/backoff columns to `crawl_runs`.
   - Add entity/repository/service tests for claim and completion.
   - Add admin list endpoint and minimal pause/resume/clear-backoff endpoints.
2. Pipeline integration PR
   - Add backend target client.
   - Fetch targets through claim endpoint.
   - Keep static `default_crawl_targets` fallback for local transition.
   - Send completion events with backoff metadata.
3. Admin/front PR
   - Show target status, next attempt, backoff reason, and actions.

## Verification Criteria

- Backend tests prove only due, active, allowed-source targets are claimed.
- Backend tests prove a claimed target is leased and not claimed twice before lease expiry.
- Backend tests prove success clears backoff and schedules the next normal attempt.
- Backend tests prove blocked/transient/unknown failures persist the expected backoff.
- Admin tests prove target list exposes structured fields without parsing `error_message`.
- Pipeline tests prove the static fallback still works while the backend target API is introduced.

## Risks

- Source policy and target status can be confused. The PR body must explain that source policy is the legal/runtime gate and target status is the scheduling gate.
- Claim/lease logic adds statefulness. The first implementation should keep one worker in mind but include lease fields so a second worker does not require a schema rewrite.
- Backoff may hide parser bugs if the only view is "waiting." Admin views should show `backoff_reason` and `last_status` together.
