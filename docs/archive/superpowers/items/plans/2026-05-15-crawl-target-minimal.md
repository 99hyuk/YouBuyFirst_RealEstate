# CrawlTarget Minimal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit `CrawlTarget` execution unit for current MVP crawler adapters without changing backend API or persistence.

**Architecture:** Introduce a focused target module that builds static target definitions from instruments and environment values. Wire `main.build_pipeline()` through targets before adapters, attach target metadata to adapters, and include target metadata in pipeline run results.

**Tech Stack:** Python 3.10+, dataclasses, enum, existing pytest suite, Docker Python verification.

---

## File Map

- Create `pipeline/src/youbuyfirst_pipeline/crawl_targets.py`
  - Owns `CrawlTargetKind`, `CrawlTarget`, constructors, and MVP target builder.
- Modify `pipeline/src/youbuyfirst_pipeline/main.py`
  - Builds targets first, then maps targets to existing adapters.
- Modify `pipeline/src/youbuyfirst_pipeline/crawlers/naver.py`
  - Stores `CrawlTarget` metadata on Naver adapters.
- Modify `pipeline/src/youbuyfirst_pipeline/crawlers/fmkorea.py`
  - Stores `CrawlTarget` metadata on FM Korea adapters.
- Modify `pipeline/src/youbuyfirst_pipeline/pipeline.py`
  - Adds target metadata to returned result dictionaries.
- Create `pipeline/tests/test_crawl_targets.py`
  - Unit tests for target construction.
- Modify `pipeline/tests/test_pipeline_source_policy.py`
  - Verifies target metadata appears for skipped, empty, and ingested results.
- Create `docs/work-units/2026-05-15-crawl-target-minimal.md`
  - Records scope and verification.

## Tasks

1. Write failing target unit tests for deterministic target ids and MVP target list construction.
2. Implement `crawl_targets.py`.
3. Wire adapters to carry optional target metadata.
4. Write failing pipeline result tests for target metadata.
5. Add target metadata to `CommunityPipeline.run_once()` result dictionaries.
6. Update `main.build_pipeline()` to build targets before adapters.
7. Add work-unit documentation.
8. Run focused tests, full pipeline tests, Docker verification, and `git diff --check`.

## PR Scope

Included: static target model, adapter target metadata, main pipeline target construction, target metadata in local run results, tests, work-unit documentation.

Excluded: backend schema, admin API/UI, persistent target queue, backoff, per-target policy, new crawler sources.
