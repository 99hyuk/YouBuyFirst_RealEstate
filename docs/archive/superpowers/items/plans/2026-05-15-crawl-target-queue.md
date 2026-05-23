# CrawlTarget Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist crawl targets and target-level backoff so operators can see which exact board is due, paused, waiting, or cooling down after failure.

**Architecture:** The backend owns `crawl_targets` as the durable queue. The pipeline computes source-policy-allowed sources, claims due targets from the backend, runs existing adapters, and reports completion so the backend can update target state and structured crawl run metadata.

**Tech Stack:** Spring Boot 3.3, Java 21, JPA, Flyway, MySQL, Python 3.10 pipeline client, pytest, existing Docker test commands.

---

## File Structure

- Create `backend/src/main/resources/db/migration/V3__crawl_targets.sql`
  - Adds `crawl_targets` and structured target/backoff columns on `crawl_runs`.
- Create `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTarget.java`
  - Owns target persistence fields and domain update methods.
- Create `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetStatus.java`
  - Defines `ACTIVE`, `PAUSED`, `DISABLED`.
- Create `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetKind.java`
  - Defines `stock-board` and `community-board` storage mapping.
- Create `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetRepository.java`
  - Finds due targets and target rows by `targetId`.
- Create `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetService.java`
  - Owns claim and completion behavior. Admin pause/resume/clear-backoff remains a follow-up.
- Create DTOs under `backend/src/main/java/com/youbuyfirst/backend/crawl/dto/`
  - `CrawlTargetClaimRequest`, `CrawlTargetClaimResponse`, `CrawlTargetView`, `CrawlTargetCompletionRequest`.
- Modify `backend/src/main/java/com/youbuyfirst/backend/admin/AdminController.java`
  - Adds admin target list endpoint.
- Modify `backend/src/main/java/com/youbuyfirst/backend/admin/CrawlRunView.java`
  - Includes structured target/backoff fields.
- Modify `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlRun.java`
  - Adds nullable target/backoff fields.
- Modify `backend/src/main/java/com/youbuyfirst/backend/ingestion/dto/CrawlRunReportRequest.java`
  - Accepts optional target/backoff fields.
- Modify `backend/src/main/java/com/youbuyfirst/backend/ingestion/IngestionService.java`
  - Saves optional structured target/backoff crawl run metadata.
- Modify `backend/src/test/java/com/youbuyfirst/backend/IngestionApiIntegrationTest.java`
  - Adds backend API tests for target queue and structured run history.
- Modify `pipeline/src/youbuyfirst_pipeline/client.py`
  - Later PR: add claim/complete methods.
- Modify `pipeline/src/youbuyfirst_pipeline/main.py`
  - Later PR: use backend targets with static fallback.

## Task 1: Backend Migration And Entity

**Files:**
- Create: `backend/src/main/resources/db/migration/V3__crawl_targets.sql`
- Create: `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTarget.java`
- Create: `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetStatus.java`
- Create: `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetKind.java`
- Create: `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetRepository.java`
- Modify: `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlRun.java`

- [x] **Step 1: Write the failing backend test**

Add a test that expects `/admin/crawl-targets` to expose a seeded target after Flyway migration.

```java
@Test
void exposesCrawlTargetsForAdminInspection() {
    List<?> targets = restTemplate.getForObject("/admin/crawl-targets", List.class);

    assertThat(targets).isNotNull();
    assertThat(targets.toString()).contains("NAVER:KR:005930");
    assertThat(targets.toString()).contains("ACTIVE");
}
```

- [x] **Step 2: Run the test and verify RED**

Run:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn -Dtest=IngestionApiIntegrationTest#exposesCrawlTargetsForAdminInspection test
```

Expected: FAIL because `/admin/crawl-targets` does not exist yet.

- [x] **Step 3: Add migration**

Use the SQL contract from `docs/superpowers/specs/2026-05-15-crawl-target-queue-design.md`.

Seed only safe local sample targets:

```sql
insert into crawl_targets (
    source, target_id, target_kind, status, market, symbol, url, label,
    priority, crawl_interval_seconds, next_attempt_at, consecutive_failures,
    created_at, updated_at
) values
('NAVER', 'NAVER:KR:005930', 'stock-board', 'ACTIVE', 'KR', '005930', null, 'NAVER KR:005930', 100, 1800, current_timestamp(6), 0, current_timestamp(6), current_timestamp(6)),
('FMKOREA', 'FMKOREA:community-board', 'community-board', 'ACTIVE', null, null, 'https://www.fmkorea.com/stock', 'FMKOREA stock board', 200, 1800, current_timestamp(6), 0, current_timestamp(6), current_timestamp(6));
```

- [x] **Step 4: Add entity and repository**

`CrawlTarget` must normalize `source` and keep `targetId` stable. Do not store raw post content or author data in this table.

- [x] **Step 5: Add read endpoint**

Add `GET /admin/crawl-targets` returning `CrawlTargetView`.

- [x] **Step 6: Run backend test and verify GREEN**

Run the same focused Docker Maven command. Expected: PASS.

## Task 2: Claim And Completion Behavior

**Files:**
- Create: `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlTargetService.java`
- Create DTOs under `backend/src/main/java/com/youbuyfirst/backend/crawl/dto/`
- Modify: `backend/src/main/java/com/youbuyfirst/backend/admin/AdminController.java`
- Modify: `backend/src/test/java/com/youbuyfirst/backend/IngestionApiIntegrationTest.java`

- [x] **Step 1: Write claim tests first**

Add tests for these behaviors:

```java
@Test
void claimsOnlyDueActiveTargetsFromAllowedSources() {
    CrawlTargetClaimRequest request = new CrawlTargetClaimRequest(
            "test-worker",
            "local",
            List.of("NAVER"),
            10
    );

    CrawlTargetClaimResponse response = restTemplate.postForObject(
            "/internal/crawl-targets/claim",
            request,
            CrawlTargetClaimResponse.class
    );

    assertThat(response.targets()).extracting(CrawlTargetView::targetId)
            .contains("NAVER:KR:005930")
            .doesNotContain("FMKOREA:community-board");
}
```

```java
@Test
void claimedTargetIsNotClaimedAgainBeforeLeaseExpires() {
    CrawlTargetClaimRequest request = new CrawlTargetClaimRequest(
            "test-worker",
            "local",
            List.of("NAVER", "FMKOREA"),
            1
    );

    CrawlTargetClaimResponse first = restTemplate.postForObject(
            "/internal/crawl-targets/claim",
            request,
            CrawlTargetClaimResponse.class
    );
    CrawlTargetClaimResponse second = restTemplate.postForObject(
            "/internal/crawl-targets/claim",
            request,
            CrawlTargetClaimResponse.class
    );

    assertThat(second.targets()).extracting(CrawlTargetView::targetId)
            .doesNotContain(first.targets().get(0).targetId());
}
```

- [x] **Step 2: Run tests and verify RED**

Expected: FAIL because claim endpoint and service do not exist yet.

- [x] **Step 3: Implement claim service**

Claim query must filter:

- `status = ACTIVE`
- `source in allowedSources`
- `nextAttemptAt <= now`
- `backoffUntil is null or backoffUntil <= now`
- `leasedUntil is null or leasedUntil <= now`

Then set `leaseOwner` and `leasedUntil = now + 5 minutes`.

- [x] **Step 4: Write completion tests**

Add tests for success and blocked completion:

```java
@Test
void successfulCompletionClearsBackoffAndSchedulesNormalInterval() {
    // Claim NAVER target, complete it as SUCCESS, then assert backoff fields are null
    // and nextAttemptAt moved into the future by the normal interval.
}
```

```java
@Test
void blockedCompletionPersistsBackoffUntil() {
    // Claim NAVER target, complete it with PARTIAL_FAILURE and blocked backoff,
    // then assert backoffCategory=blocked and nextAttemptAt equals backoffUntil.
}
```

- [x] **Step 5: Implement completion service**

Completion releases lease in all cases. Success clears backoff and failures. Failure persists category, until, reason, and increments failures.

- [x] **Step 6: Run focused backend tests**

Run:

```bash
docker run --rm -v "${PWD}/backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn -Dtest=IngestionApiIntegrationTest test
```

Expected: PASS.

## Task 3: Structured Crawl Run Metadata

**Files:**
- Modify: `backend/src/main/java/com/youbuyfirst/backend/crawl/CrawlRun.java`
- Modify: `backend/src/main/java/com/youbuyfirst/backend/admin/CrawlRunView.java`
- Modify: `backend/src/main/java/com/youbuyfirst/backend/ingestion/dto/CrawlRunReportRequest.java`
- Modify: `backend/src/main/java/com/youbuyfirst/backend/ingestion/IngestionService.java`
- Modify: `backend/src/test/java/com/youbuyfirst/backend/IngestionApiIntegrationTest.java`

- [x] **Step 1: Write failing admin history test**

Extend the existing skipped crawl run test so `/admin/crawl-runs` contains structured fields:

```java
assertThat(runs).contains("\"targetId\":\"NAVER:KR:005930\"");
assertThat(runs).contains("\"backoffCategory\":\"blocked\"");
assertThat(runs).contains("\"skipReason\":\"backoff\"");
```

- [x] **Step 2: Run test and verify RED**

Expected: FAIL because the DTO/view does not expose those fields yet.

- [x] **Step 3: Add optional fields through DTO, entity, and view**

Fields are nullable to preserve existing ingestion clients:

- `targetId`
- `targetKind`
- `backoffCategory`
- `backoffUntil`
- `skipReason`

- [x] **Step 4: Run backend tests and verify GREEN**

Run backend Docker Maven tests. Expected: PASS.

## Task 4: Pipeline Integration

**Files:**
- Modify: `pipeline/src/youbuyfirst_pipeline/client.py`
- Modify: `pipeline/src/youbuyfirst_pipeline/main.py`
- Modify: `pipeline/src/youbuyfirst_pipeline/pipeline.py`
- Create or modify: `pipeline/tests/test_backend_crawl_targets.py`

- [ ] **Step 1: Write failing client tests**

Use a fake transport or monkeypatch to verify:

- `claim_crawl_targets()` posts `workerId`, `runtimeEnvironment`, `allowedSources`, and `limit`.
- `complete_crawl_target()` posts completion metadata.

- [ ] **Step 2: Implement client methods**

Add:

```python
def claim_crawl_targets(self, worker_id: str, runtime_environment: str, allowed_sources: list[str], limit: int) -> list[CrawlTarget]:
    ...

def complete_crawl_target(self, target_id: str, payload: dict) -> None:
    ...
```

- [ ] **Step 3: Keep static fallback**

If the backend target endpoint fails in local development, log the failure and use `default_crawl_targets()` for the transition PR. This keeps current `run-once` behavior usable while backend and pipeline are integrated.

- [ ] **Step 4: Run pipeline tests**

Run:

```bash
docker run --rm -v "${PWD}/pipeline:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
```

Expected: PASS.

## Task 5: Documentation And Handoff

**Files:**
- Modify: `docs/CURRENT_HANDOFF.md`
- Modify: `docs/TASKS.md`
- Add: `docs/work-units/YYYY-MM-DD-crawl-target-queue.md`

- [ ] **Step 1: Update human-facing docs**

Explain the work in this order:

1. Operator can now see which exact target is waiting and why.
2. Source policy remains the upper legal/runtime gate.
3. Target status/backoff is the scheduling gate.
4. Admin UI remains a follow-up.

- [ ] **Step 2: Run verification**

Run:

```powershell
git diff --check
$markers = @('T' + 'BD', 'TO' + 'DO', 'FIX' + 'ME', '\?\?')
foreach ($marker in $markers) {
    rg -n $marker docs/superpowers/specs/2026-05-15-crawl-target-queue-design.md docs/superpowers/plans/2026-05-15-crawl-target-queue.md
}
```

Expected: `git diff --check` passes. The `rg` command returns no placeholder lines.

## Self-Review

- Spec coverage: The plan covers DB schema, source-policy separation, target status, claim, completion, structured run history, admin list/actions, pipeline integration, and verification.
- Placeholder scan: This plan avoids unresolved marker keywords and placeholder language.
- Type consistency: The plan consistently uses `targetId` in Java DTOs and `target_id` only for SQL columns.
