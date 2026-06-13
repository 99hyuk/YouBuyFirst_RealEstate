import asyncio
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakePipeline:
    pass


class _FakeSpringClient:
    pass


class _FakeRefreshJob:
    def run_once(self) -> dict:
        return {"status": "OK"}


class _FakeRecentIssueClient:
    pass


def test_serve_command_can_enable_real_estate_market_facts_refresh(monkeypatch):
    captured = {}
    realestate_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: realestate_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--realestate-market-facts-refresh-interval-minutes",
            "720",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_market_facts_refresh_job"] is realestate_job
    assert captured["kwargs"]["realestate_market_facts_interval_minutes"] == 720


def test_serve_command_can_enable_real_estate_reaction_snapshot_refresh(monkeypatch):
    captured = {}
    builder_kwargs = {}
    reaction_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    def fake_build_reaction_job(**kwargs):
        builder_kwargs.update(kwargs)
        return reaction_job

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        fake_build_reaction_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-aliases-jsonl",
            "aliases.jsonl",
            "--community-posts-jsonl",
            "posts.jsonl",
            "--reaction-window-minutes",
            "60",
            "--reaction-stale-after-minutes",
            "180",
            "--realestate-reaction-snapshots-refresh-interval-minutes",
            "15",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_reaction_snapshot_refresh_job"] is reaction_job
    assert captured["kwargs"]["realestate_reaction_snapshot_interval_minutes"] == 15
    assert builder_kwargs["stale_after_minutes"] == 180


def test_serve_command_can_group_real_estate_refresh_jobs_into_daily_refresh(monkeypatch, tmp_path):
    captured = {}
    market_job = _FakeRefreshJob()
    targets_path = tmp_path / "targets.jsonl"
    targets_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통"]}',
        encoding="utf-8",
    )

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: market_job,
    )
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: _FakeRecentIssueClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--realestate-daily-refresh-interval-minutes",
            "1440",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--enable-realestate-recent-issues-refresh",
            "--realestate-search-targets-jsonl",
            str(targets_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert captured["kwargs"]["realestate_market_facts_refresh_job"] is None
    assert captured["kwargs"]["realestate_daily_refresh_interval_minutes"] == 1440
    assert [name for name, _step in daily_job.steps] == ["market_facts", "recent_issues"]
