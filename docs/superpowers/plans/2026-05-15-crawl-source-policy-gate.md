# Crawl Source Policy Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a crawl source policy gate so the pipeline only calls crawler adapters when the source status is allowed in the current runtime environment.

**Architecture:** Add a focused `source_policy.py` module that owns source statuses, runtime environment parsing, default source policies, and allow/skip decisions. Inject the policy registry and runtime environment into `CommunityPipeline.run_once()` so both `run-once` and `serve` use the same gate before `adapter.fetch_posts()`.

**Tech Stack:** Python 3.10+, dataclasses, enum, existing pytest suite, Docker Compose local runtime.

---

## File Map

- Create `pipeline/src/youbuyfirst_pipeline/source_policy.py`
  - Owns `SourceStatus`, `CrawlRuntimeEnvironment`, `SourcePolicy`, `SourcePolicyDecision`, `SourcePolicyRegistry`, `default_source_policy_registry()`, and `runtime_environment_from_env()`.
- Create `pipeline/tests/test_source_policy.py`
  - Unit tests for default disabled behavior, local/public environment parsing, and status allow/deny decisions.
- Create `pipeline/tests/test_pipeline_source_policy.py`
  - Pipeline-level tests proving skipped sources do not call `fetch_posts()` and allowed local research sources still run in local runtime.
- Modify `pipeline/src/youbuyfirst_pipeline/pipeline.py`
  - Adds policy registry and runtime environment constructor dependencies.
  - Adds skip decision before `adapter.fetch_posts()`.
- Modify `pipeline/src/youbuyfirst_pipeline/main.py`
  - Reads `CRAWL_RUNTIME_ENV`, builds default source policies, and passes both into `CommunityPipeline`.
- Modify `docker-compose.yml`
  - Sets `CRAWL_RUNTIME_ENV: local` for the local compose pipeline service.
- Modify `README.md`
  - Documents source policy statuses and the fail-closed runtime environment rule.

---

### Task 1: Source Policy Module

**Files:**
- Create: `pipeline/src/youbuyfirst_pipeline/source_policy.py`
- Create: `pipeline/tests/test_source_policy.py`

- [ ] **Step 1: Write failing source policy tests**

Create `pipeline/tests/test_source_policy.py`:

```python
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicy,
    SourcePolicyRegistry,
    SourceStatus,
    default_source_policy_registry,
    runtime_environment_from_env,
)


def test_unknown_source_defaults_to_disabled():
    registry = SourcePolicyRegistry({})

    decision = registry.decide("UNKNOWN", CrawlRuntimeEnvironment.LOCAL)

    assert decision.allowed is False
    assert decision.policy.source == "UNKNOWN"
    assert decision.policy.status == SourceStatus.DISABLED
    assert "default disabled" in decision.reason


def test_default_registry_marks_current_mvp_sources_local_research_only():
    registry = default_source_policy_registry()

    naver = registry.policy_for("NAVER")
    fmkorea = registry.policy_for("FMKOREA")

    assert naver.status == SourceStatus.LOCAL_RESEARCH_ONLY
    assert fmkorea.status == SourceStatus.LOCAL_RESEARCH_ONLY


def test_local_research_source_runs_only_in_local_runtime():
    registry = SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy(
                source="NAVER",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="local research only",
            )
        }
    )

    local_decision = registry.decide("NAVER", CrawlRuntimeEnvironment.LOCAL)
    public_decision = registry.decide("NAVER", CrawlRuntimeEnvironment.PUBLIC)

    assert local_decision.allowed is True
    assert public_decision.allowed is False
    assert "not allowed in public runtime" in public_decision.reason


def test_public_demo_and_disabled_sources_never_run():
    registry = SourcePolicyRegistry(
        {
            "DEMO": SourcePolicy("DEMO", SourceStatus.PUBLIC_DEMO_ONLY, "demo source"),
            "OFF": SourcePolicy("OFF", SourceStatus.DISABLED, "disabled source"),
        }
    )

    for runtime in (CrawlRuntimeEnvironment.LOCAL, CrawlRuntimeEnvironment.PUBLIC):
        assert registry.decide("DEMO", runtime).allowed is False
        assert registry.decide("OFF", runtime).allowed is False


def test_enabled_source_runs_in_local_and_public_runtime():
    registry = SourcePolicyRegistry(
        {
            "SAFE": SourcePolicy("SAFE", SourceStatus.ENABLED, "review complete"),
        }
    )

    assert registry.decide("SAFE", CrawlRuntimeEnvironment.LOCAL).allowed is True
    assert registry.decide("SAFE", CrawlRuntimeEnvironment.PUBLIC).allowed is True


def test_runtime_environment_parsing_fails_closed_to_public():
    assert runtime_environment_from_env("local") == CrawlRuntimeEnvironment.LOCAL
    assert runtime_environment_from_env("LOCAL") == CrawlRuntimeEnvironment.LOCAL
    assert runtime_environment_from_env("public") == CrawlRuntimeEnvironment.PUBLIC
    assert runtime_environment_from_env(None) == CrawlRuntimeEnvironment.PUBLIC
    assert runtime_environment_from_env("") == CrawlRuntimeEnvironment.PUBLIC
    assert runtime_environment_from_env("staging") == CrawlRuntimeEnvironment.PUBLIC
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```powershell
& 'C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_source_policy.py -q
```

Expected result:

```text
ModuleNotFoundError: No module named 'youbuyfirst_pipeline.source_policy'
```

- [ ] **Step 3: Implement the source policy module**

Create `pipeline/src/youbuyfirst_pipeline/source_policy.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceStatus(str, Enum):
    ENABLED = "enabled"
    PUBLIC_DEMO_ONLY = "public-demo-only"
    LOCAL_RESEARCH_ONLY = "local-research-only"
    DISABLED = "disabled"


class CrawlRuntimeEnvironment(str, Enum):
    LOCAL = "local"
    PUBLIC = "public"


@dataclass(frozen=True)
class SourcePolicy:
    source: str
    status: SourceStatus
    reason: str


@dataclass(frozen=True)
class SourcePolicyDecision:
    source: str
    policy: SourcePolicy
    runtime_environment: CrawlRuntimeEnvironment
    allowed: bool
    reason: str


class SourcePolicyRegistry:
    def __init__(self, policies: dict[str, SourcePolicy]) -> None:
        self._policies = {source.upper(): policy for source, policy in policies.items()}

    def policy_for(self, source: str) -> SourcePolicy:
        normalized = source.upper()
        return self._policies.get(
            normalized,
            SourcePolicy(
                source=normalized,
                status=SourceStatus.DISABLED,
                reason="source is not registered; default disabled",
            ),
        )

    def decide(self, source: str, runtime_environment: CrawlRuntimeEnvironment) -> SourcePolicyDecision:
        policy = self.policy_for(source)
        if policy.status == SourceStatus.ENABLED:
            return SourcePolicyDecision(source, policy, runtime_environment, True, policy.reason)
        if policy.status == SourceStatus.LOCAL_RESEARCH_ONLY:
            if runtime_environment == CrawlRuntimeEnvironment.LOCAL:
                return SourcePolicyDecision(source, policy, runtime_environment, True, policy.reason)
            return SourcePolicyDecision(
                source,
                policy,
                runtime_environment,
                False,
                "source policy local-research-only is not allowed in public runtime",
            )
        if policy.status == SourceStatus.PUBLIC_DEMO_ONLY:
            return SourcePolicyDecision(
                source,
                policy,
                runtime_environment,
                False,
                "source policy public-demo-only uses fixture or sample data; external requests are disabled",
            )
        return SourcePolicyDecision(source, policy, runtime_environment, False, policy.reason)


def default_source_policy_registry() -> SourcePolicyRegistry:
    return SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy(
                source="NAVER",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP source allowed only for local research before public review",
            ),
            "FMKOREA": SourcePolicy(
                source="FMKOREA",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP source allowed only for local research before public review",
            ),
        }
    )


def runtime_environment_from_env(value: str | None) -> CrawlRuntimeEnvironment:
    if value and value.strip().lower() == CrawlRuntimeEnvironment.LOCAL.value:
        return CrawlRuntimeEnvironment.LOCAL
    return CrawlRuntimeEnvironment.PUBLIC
```

- [ ] **Step 4: Run source policy tests and verify they pass**

Run:

```powershell
& 'C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_source_policy.py -q
```

Expected result:

```text
6 passed
```

---

### Task 2: Pipeline Gate

**Files:**
- Modify: `pipeline/src/youbuyfirst_pipeline/pipeline.py`
- Create: `pipeline/tests/test_pipeline_source_policy.py`

- [ ] **Step 1: Write failing pipeline gate tests**

Create `pipeline/tests/test_pipeline_source_policy.py`:

```python
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from youbuyfirst_pipeline.models import RawPost
from youbuyfirst_pipeline.pipeline import CommunityPipeline
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicy,
    SourcePolicyRegistry,
    SourceStatus,
)


class FakeAdapter:
    def __init__(self, source: str, posts: list[RawPost] | None = None) -> None:
        self.source = source
        self.posts = posts or []
        self.called = False

    async def fetch_posts(self) -> list[RawPost]:
        self.called = True
        return self.posts


class FakeMatcher:
    def match(self, text: str) -> list:
        return []


class FakeLLMProvider:
    def analyze(self, title: str, content: str, mentions: list) -> list:
        return []


class FakeClient:
    def __init__(self) -> None:
        self.recorded_runs: list[dict] = []
        self.ingested_batches: list[dict] = []

    def ingest(self, source, run_id, batch_started_at, batch_finished_at, posts):
        payload = {"source": source, "runId": run_id, "acceptedPosts": len(list(posts))}
        self.ingested_batches.append(payload)
        return payload

    def record_crawl_run(
        self,
        source,
        run_id,
        batch_started_at,
        batch_finished_at,
        status,
        posts_seen,
        posts_accepted,
        error_message=None,
    ):
        self.recorded_runs.append(
            {
                "source": source,
                "runId": run_id,
                "status": status,
                "postsSeen": posts_seen,
                "postsAccepted": posts_accepted,
                "errorMessage": error_message,
            }
        )


def _pipeline(adapter: FakeAdapter, registry: SourcePolicyRegistry, runtime: CrawlRuntimeEnvironment) -> CommunityPipeline:
    return CommunityPipeline(
        adapters=[adapter],
        matcher=FakeMatcher(),
        llm_provider=FakeLLMProvider(),
        client=FakeClient(),
        source_policy_registry=registry,
        runtime_environment=runtime,
    )


def test_public_runtime_skips_local_research_source_without_fetching():
    adapter = FakeAdapter("NAVER")
    registry = SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy("NAVER", SourceStatus.LOCAL_RESEARCH_ONLY, "local only"),
        }
    )
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is False
    assert results[0]["source"] == "NAVER"
    assert results[0]["status"] == "skipped"
    assert results[0]["sourceStatus"] == "local-research-only"
    assert results[0]["runtimeEnvironment"] == "public"
    assert "not allowed in public runtime" in results[0]["skipReason"]


def test_disabled_source_skips_without_backend_run_record():
    adapter = FakeAdapter("UNKNOWN")
    registry = SourcePolicyRegistry({})
    client = FakeClient()
    pipeline = CommunityPipeline(
        adapters=[adapter],
        matcher=FakeMatcher(),
        llm_provider=FakeLLMProvider(),
        client=client,
        source_policy_registry=registry,
        runtime_environment=CrawlRuntimeEnvironment.LOCAL,
    )

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is False
    assert results[0]["status"] == "skipped"
    assert client.recorded_runs == []


def test_local_runtime_allows_local_research_source_to_fetch():
    adapter = FakeAdapter("NAVER")
    registry = SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy("NAVER", SourceStatus.LOCAL_RESEARCH_ONLY, "local only"),
        }
    )
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.LOCAL)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["source"] == "NAVER"
    assert results[0]["seenPosts"] == 0
    assert results[0]["acceptedPosts"] == 0


def test_enabled_source_still_ingests_enriched_posts():
    post = RawPost(
        source="SAFE",
        external_id="SAFE-1",
        url="https://example.com/1",
        title="테스트",
        content="",
        author="anon",
        published_at=datetime.now(timezone.utc),
    )
    adapter = FakeAdapter("SAFE", posts=[post])
    registry = SourcePolicyRegistry(
        {
            "SAFE": SourcePolicy("SAFE", SourceStatus.ENABLED, "review complete"),
        }
    )
    pipeline = _pipeline(adapter, registry, CrawlRuntimeEnvironment.PUBLIC)

    results = asyncio.run(pipeline.run_once())

    assert adapter.called is True
    assert results[0]["source"] == "SAFE"
    assert results[0]["acceptedPosts"] == 1
```

- [ ] **Step 2: Run the new pipeline tests and verify they fail**

Run:

```powershell
& 'C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_pipeline_source_policy.py -q
```

Expected result:

```text
TypeError: CommunityPipeline.__init__() got an unexpected keyword argument 'source_policy_registry'
```

- [ ] **Step 3: Add source policy dependencies to `CommunityPipeline`**

Modify imports in `pipeline/src/youbuyfirst_pipeline/pipeline.py`:

```python
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicyRegistry,
    default_source_policy_registry,
)
```

Modify the constructor:

```python
    def __init__(
        self,
        adapters: list[CommunityAdapter],
        matcher: InstrumentMatcher,
        llm_provider: LLMProvider,
        client: SpringIngestionClient,
        source_policy_registry: SourcePolicyRegistry | None = None,
        runtime_environment: CrawlRuntimeEnvironment = CrawlRuntimeEnvironment.PUBLIC,
    ) -> None:
        self.adapters = adapters
        self.matcher = matcher
        self.llm_provider = llm_provider
        self.client = client
        self.source_policy_registry = source_policy_registry or default_source_policy_registry()
        self.runtime_environment = runtime_environment
```

- [ ] **Step 4: Add the skip gate before `fetch_posts()`**

In `CommunityPipeline.run_once()`, insert this block immediately after `run_id` is created and before the `try` block:

```python
            policy_decision = self.source_policy_registry.decide(adapter.source, self.runtime_environment)
            if not policy_decision.allowed:
                results.append(
                    {
                        "source": adapter.source,
                        "runId": run_id,
                        "status": "skipped",
                        "sourceStatus": policy_decision.policy.status.value,
                        "runtimeEnvironment": self.runtime_environment.value,
                        "skipReason": policy_decision.reason,
                    }
                )
                continue
```

The skip branch must not call `adapter.fetch_posts()` and must not call `client.record_crawl_run()` because the backend does not yet have a `SKIPPED` crawl-run status.

- [ ] **Step 5: Run pipeline gate tests and verify they pass**

Run:

```powershell
& 'C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_pipeline_source_policy.py -q
```

Expected result:

```text
4 passed
```

---

### Task 3: Runtime Wiring and Local Documentation

**Files:**
- Modify: `pipeline/src/youbuyfirst_pipeline/main.py`
- Modify: `docker-compose.yml`
- Modify: `README.md`

- [ ] **Step 1: Wire runtime environment in `main.py`**

Modify imports in `pipeline/src/youbuyfirst_pipeline/main.py`:

```python
from youbuyfirst_pipeline.source_policy import default_source_policy_registry, runtime_environment_from_env
```

Inside `build_pipeline()`, add this near the other environment reads:

```python
    runtime_environment = runtime_environment_from_env(os.getenv("CRAWL_RUNTIME_ENV"))
```

Pass the policy dependencies into `CommunityPipeline`:

```python
    return CommunityPipeline(
        adapters=adapters,
        matcher=matcher,
        llm_provider=build_llm_provider(),
        client=client,
        source_policy_registry=default_source_policy_registry(),
        runtime_environment=runtime_environment,
    )
```

- [ ] **Step 2: Mark Docker Compose as local runtime**

In `docker-compose.yml`, add `CRAWL_RUNTIME_ENV: local` to the `pipeline.environment` block:

```yaml
  pipeline:
    build:
      context: ./pipeline
    environment:
      SPRING_BASE_URL: http://backend:8080
      CRAWL_RUNTIME_ENV: local
      CRAWL_INTERVAL_MINUTES: 30
      NAVER_STOCK_CODES: 005930,000660
      INSTRUMENT_CSV_PATH: data/instruments.sample.csv
      LOG_LEVEL: INFO
```

- [ ] **Step 3: Document the source policy behavior**

In `README.md`, add this section after `## 종목 마스터` and before `## 테스트`:

```markdown
## 수집 소스 정책

pipeline은 crawler adapter를 실행하기 전에 소스 상태와 실행 환경을 확인합니다. 현재 MVP 소스인 `NAVER`, `FMKOREA`는 공개 검토 전까지 `local-research-only`로 취급합니다.

상태 의미:

- `enabled`: local/public 환경에서 실제 수집 가능
- `local-research-only`: `CRAWL_RUNTIME_ENV=local`일 때만 실제 수집 가능
- `public-demo-only`: 실제 외부 요청 금지, fixture/sample 데이터만 사용
- `disabled`: 실제 외부 요청 금지

`CRAWL_RUNTIME_ENV`가 없거나 알 수 없는 값이면 `public`처럼 처리합니다. 공개 환경에서 값을 빠뜨렸을 때 외부 요청이 나가지 않게 하기 위한 fail-closed 기본값입니다. 로컬에서 실제 수집을 돌리려면 아래처럼 명시합니다.

```bash
CRAWL_RUNTIME_ENV=local
```
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
& 'C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_source_policy.py tests/test_pipeline_source_policy.py -q
```

Expected result:

```text
10 passed
```

---

### Task 4: Full Verification and Commit

**Files:**
- Verify all files changed in Tasks 1-3.

- [ ] **Step 1: Run the pipeline test suite with bundled Python**

Run from `C:\agents\YouBuyFirst\.worktrees\crawl-source-policy-stages\pipeline`:

```powershell
& 'C:\Users\JYH\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest
```

Expected result:

```text
14 passed
```

The exact count can be higher if other merged branches add tests. There must be zero failures.

- [ ] **Step 2: Run official Docker verification when Docker Desktop is available**

Run from `C:\agents\YouBuyFirst\.worktrees\crawl-source-policy-stages`:

```powershell
docker run --rm -v "${PWD}/pipeline:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] && pytest"
```

Expected result:

```text
pytest exits 0 with all pipeline tests passing
```

If Docker Desktop is not running, record the exact Docker connection error in the PR verification section and include the bundled-Python pytest result.

- [ ] **Step 3: Run whitespace validation**

Run:

```powershell
git diff --check
```

Expected result:

```text
no output
```

- [ ] **Step 4: Review the diff**

Run:

```powershell
git diff -- pipeline/src/youbuyfirst_pipeline/source_policy.py pipeline/src/youbuyfirst_pipeline/pipeline.py pipeline/src/youbuyfirst_pipeline/main.py pipeline/tests/test_source_policy.py pipeline/tests/test_pipeline_source_policy.py docker-compose.yml README.md
```

Expected review points:

- skip decisions happen before `adapter.fetch_posts()`
- skipped sources do not record backend crawl runs
- `CRAWL_RUNTIME_ENV` fails closed to public
- Docker Compose explicitly opts local runtime into local collection
- README tells local users how to opt in

- [ ] **Step 5: Commit the implementation**

Run:

```powershell
git add pipeline/src/youbuyfirst_pipeline/source_policy.py pipeline/src/youbuyfirst_pipeline/pipeline.py pipeline/src/youbuyfirst_pipeline/main.py pipeline/tests/test_source_policy.py pipeline/tests/test_pipeline_source_policy.py docker-compose.yml README.md
git commit -m "[crawl][feat] 소스 정책 실행 게이트"
```

Expected result:

```text
[codex/crawl-source-policy-stages <hash>] [crawl][feat] 소스 정책 실행 게이트
```

---

## PR Notes Draft

Use these points in the Korean PR body:

- 한눈에 보기: source policy registry와 runtime gate를 추가해 허용되지 않은 소스는 외부 요청 전에 skip합니다.
- 바뀐 내용: `NAVER`, `FMKOREA` 기본 상태를 `local-research-only`로 두고, `CRAWL_RUNTIME_ENV=local`에서만 실제 수집이 실행되게 했습니다.
- 리뷰 가이드: `CommunityPipeline.run_once()`의 `policy_decision` 분기와 `source_policy.py`의 상태별 허용 규칙을 먼저 봅니다.
- PR 범위: static policy와 pipeline gate만 포함하며 backend `SKIPPED` 상태, admin API, 관리자 화면, parser 보강은 포함하지 않습니다.
- 검증 결과: bundled Python pytest 결과, Docker verification 가능 여부, `git diff --check` 결과를 적습니다.
- 리스크와 후속 작업: backend skip 기록, admin 조회/변경, 운영 audit log는 후속 PR로 남깁니다.
