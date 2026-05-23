# Crawl Backoff Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent repeated crawler requests during the same scheduler process after blocked or failed runs.

**Architecture:** Add a focused Python backoff module that classifies exceptions into retry windows. `CommunityPipeline` owns an in-memory map of active backoff decisions by target/source key, checks it before `fetch_posts()`, and records backoff skips through the existing crawl run report endpoint.

**Tech Stack:** Python 3.10, dataclasses, httpx exception types, pytest, existing Spring ingestion client contract.

---

## File Map

- Create `pipeline/src/youbuyfirst_pipeline/backoff.py`
  - Owns `CrawlBackoffDecision`, `CrawlBackoffPolicy`, exception classification, and UTC formatting.
- Create `pipeline/tests/test_backoff.py`
  - Unit tests for blocked, transient, and unknown classification.
- Create `pipeline/tests/test_pipeline_backoff.py`
  - Pipeline behavior tests for blocked backoff and transient error metadata.
- Modify `pipeline/src/youbuyfirst_pipeline/pipeline.py`
  - Injects/creates a backoff policy.
  - Checks active backoff before source policy fetch.
  - Sets backoff after blocked or failed runs.
  - Clears expired/successful backoff.
- Add `docs/work-units/2026-05-15-crawl-backoff-policy.md`
  - Records scope, verification, and follow-up.

## Tasks

- [x] **Step 1: Write backoff unit tests**
  - Add tests proving `SourceBlockedError` maps to `blocked` for 6 hours, `httpx.TimeoutException` maps to `transient-error` for 15 minutes, and `RuntimeError` maps to `unknown-error` for 60 minutes.
  - Run focused tests and confirm they fail because `youbuyfirst_pipeline.backoff` does not exist.

- [x] **Step 2: Write pipeline behavior tests**
  - Add a test where the first run raises `SourceBlockedError`, sets `backoffUntil`, and the second run does not call `fetch_posts()`.
  - Add a test where a timeout raises `FAILED` with `transient-error` metadata.
  - Run focused tests and confirm they fail because `CommunityPipeline` has no backoff behavior yet.

- [x] **Step 3: Implement `backoff.py`**
  - Add the decision dataclass and policy classifier.
  - Keep the values explicit: blocked 21600 seconds, transient 900 seconds, unknown 3600 seconds.

- [x] **Step 4: Wire `CommunityPipeline`**
  - Add `backoff_policy` and `now_provider` constructor arguments.
  - Check active backoff before source policy/fetch.
  - Record active backoff skips as backend `SKIPPED`.
  - Add backoff metadata to blocked/failed results and run error messages.

- [x] **Step 5: Document and verify**
  - Add work-unit note.
  - Update `docs/TASKS.md` and `docs/CURRENT_HANDOFF.md`.
  - Run full pipeline Docker tests and `git diff --check`.
