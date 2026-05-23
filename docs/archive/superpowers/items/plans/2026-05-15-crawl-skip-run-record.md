# Crawl Policy Skip Run Record Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make source policy skips visible in backend crawl run history as `SKIPPED` records.

**Architecture:** Extend the backend crawl run status enum and reuse the existing crawl run ingestion endpoint. In the pipeline source policy deny branch, record a zero-count skipped run with target/policy context in `errorMessage`, then return the existing local `skipped` result.

**Tech Stack:** Spring Boot 3.3, Java 21, JPA enum string mapping, Python 3.10, pytest, Docker test runners.

---

## File Map

- Modify `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlRunStatus.java`
  - Adds the `SKIPPED` status accepted by ingestion and shown by admin views.
- Modify `backend/src/test/java/com/youbuyfirst/backend/IngestionApiIntegrationTest.java`
  - Adds an integration test for recording and reading a skipped crawl run.
- Modify `pipeline/src/youbuyfirst_pipeline/pipeline.py`
  - Records skipped runs from the source policy gate.
  - Adds a helper for compact skip run messages.
- Modify `pipeline/tests/test_pipeline_source_policy.py`
  - Updates skip tests to expect backend run records while still preventing remote fetches.
- Create `docs/work-units/2026-05-15-crawl-skip-run-record.md`
  - Records scope, verification, and follow-up boundaries.

## Tasks

- [x] **Step 1: Write backend failing test**
  - Add `recordsSkippedCrawlRunsForAdminInspection()` that posts a crawl run report with `CrawlRunStatus.SKIPPED` and asserts `/admin/crawl-runs` includes `SKIPPED` and `sourceStatus=local-research-only`.
  - Run backend tests and confirm compilation fails because `SKIPPED` does not exist yet.

- [x] **Step 2: Write pipeline failing tests**
  - Update disabled/public source policy tests to assert skipped sources do not fetch but do call `record_crawl_run()` with status `SKIPPED`.
  - Run the focused pytest file and confirm it fails because skip runs are not recorded yet.

- [x] **Step 3: Implement backend status**
  - Add `SKIPPED` to `CrawlRunStatus`.
  - Do not add a Flyway migration because `crawl_runs.status` is already `varchar(20)`.

- [x] **Step 4: Implement pipeline skip recording**
  - Build a skip run message from `targetId`, `sourceStatus`, `runtimeEnvironment`, and `reason`.
  - Call `_safe_record_run(..., "SKIPPED", 0, 0, skip_message)` in the policy deny branch.
  - Add `recordError` to the returned result only if recording fails.

- [x] **Step 5: Document the work unit**
  - Add the work-unit note with included scope, excluded scope, verification commands, and follow-up work.

- [x] **Step 6: Verify and ship**
  - Run backend Docker tests.
  - Run pipeline Docker tests.
  - Run `git diff --check`.
  - Commit, push, open PR, add labels, and verify the Korean PR body is not garbled.
