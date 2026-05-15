# Work Unit: CrawlTarget Queue Design

## Goal

Define the durable queue contract for crawl targets and persistent target-level backoff before changing backend schema or pipeline runtime behavior.

## Scope

- Explain the difference between source policy and `CrawlTarget` scheduling.
- Define the first `crawl_targets` table shape.
- Define structured target/backoff fields for `crawl_runs`.
- Define internal claim/complete endpoints for the pipeline.
- Define admin read/action endpoints for future management screens.
- Record implementation split so backend, pipeline, and front/admin work can land in separate PRs.

## Out of Scope

- No Flyway migration in this PR.
- No backend entity/API implementation in this PR.
- No pipeline runtime change in this PR.
- No admin/front UI in this PR.
- No public source approval in this PR.

## Human Explanation

This design turns "the crawler remembers a backoff only while Python is running" into "the product can later remember each crawl target in the database."

For an operator, this means a future admin page can answer: which exact source target is due, which one is paused, which one is cooling down after a block, and when it will be tried again.

## Design Summary

- Source policy stays above the queue and answers whether a source may run in the current runtime.
- `CrawlTarget` becomes the queue row and answers which exact board or stock discussion room should run next.
- `crawl_targets` stores target status, priority, next attempt time, lease, failure count, and backoff fields.
- `crawl_runs` should receive structured target/backoff columns so admin views do not parse `error_message`.
- The first implementation should be split into backend contract, pipeline integration, and admin/front follow-up.

## Verification

- Markdown whitespace check should pass.
- Placeholder scan should show no unresolved marker keywords.
- Because this PR is design-only, backend and pipeline test suites are not required for behavioral proof.
