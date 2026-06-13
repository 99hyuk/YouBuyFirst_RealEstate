from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from youbuyfirst_pipeline.realestate_reaction_scheduler import RealEstateReactionSnapshotRefreshJob
from youbuyfirst_pipeline.scheduler import configure_scheduler


class _Client:
    def __init__(self, fail_push: bool = False) -> None:
        self.fail_push = fail_push
        self.pushed_batches = []

    def publish_real_estate_reaction_snapshots(self, snapshots) -> None:
        if self.fail_push:
            raise RuntimeError("backend unavailable")
        self.pushed_batches.append([snapshot.to_request_dict() for snapshot in snapshots])


class _Pipeline:
    async def run_once(self) -> list[str]:
        return []


def test_real_estate_reaction_snapshot_refresh_job_builds_previous_completed_window_and_pushes(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","alias":"대전","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        "\n".join(
            [
                '{"source":"PPOMPPU:house","externalId":"prev","publishedAt":"2026-06-10T23:40:00Z","title":"대전 전세 불안","contentSnippet":"전세 부담"}',
                '{"source":"PPOMPPU:house","externalId":"now","publishedAt":"2026-06-11T00:20:00Z","title":"대전 GTX 호재","contentSnippet":"교통 개선 기대"}',
                '{"source":"PPOMPPU:house","externalId":"future","publishedAt":"2026-06-11T01:10:00Z","title":"대전 전세","contentSnippet":"아직 다음 window"}',
            ]
        ),
        encoding="utf-8",
    )
    client = _Client()
    now = datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc)
    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=aliases_path,
        community_posts_jsonl=posts_path,
        window_minutes=60,
        clock=lambda: now,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 1
    assert client.pushed_batches[0][0]["targetId"] == "region-daejeon"
    assert client.pushed_batches[0][0]["windowStart"] == "2026-06-11T00:00:00Z"
    assert client.pushed_batches[0][0]["windowEnd"] == "2026-06-11T01:00:00Z"
    assert client.pushed_batches[0][0]["asOf"] == "2026-06-11T01:02:00Z"
    assert client.pushed_batches[0][0]["mentionCount"] == 1
    assert client.pushed_batches[0][0]["previousMentionCount"] == 1


def test_real_estate_reaction_snapshot_refresh_job_rolls_child_region_up_to_parent(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-seoul-jongno","alias":"종로","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    target_edges_path = tmp_path / "target_edges.jsonl"
    target_edges_path.write_text(
        '{"fromTargetType":"region","fromTargetId":"region-seoul","toTargetType":"region","toTargetId":"region-seoul-jongno","edgeType":"contains","reviewState":"approved","confidence":0.9}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"now","publishedAt":"2026-06-11T00:20:00Z","title":"종로 재건축 기대","contentSnippet":"호재 기대"}',
        encoding="utf-8",
    )
    client = _Client()
    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=aliases_path,
        target_edges_jsonl=target_edges_path,
        community_posts_jsonl=posts_path,
        window_minutes=60,
        clock=lambda: datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.observation_count == 2
    assert result.snapshot_count == 2
    assert [snapshot["targetId"] for snapshot in client.pushed_batches[0]] == [
        "region-seoul",
        "region-seoul-jongno",
    ]


def test_real_estate_reaction_snapshot_refresh_job_reports_input_error_without_push(tmp_path):
    client = _Client()
    job = RealEstateReactionSnapshotRefreshJob(
        client=client,
        aliases_jsonl=tmp_path / "missing-aliases.jsonl",
        community_posts_jsonl=tmp_path / "missing-posts.jsonl",
        window_minutes=60,
    )

    result = job.run_once()

    assert result.status == "INPUT_ERROR"
    assert result.observation_count == 0
    assert result.snapshot_count == 0
    assert client.pushed_batches == []


def test_real_estate_reaction_snapshot_refresh_job_reports_client_error_when_push_fails(tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","alias":"대전","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"now","publishedAt":"2026-06-11T00:20:00Z","title":"대전 GTX 호재","contentSnippet":"교통 개선 기대"}',
        encoding="utf-8",
    )
    job = RealEstateReactionSnapshotRefreshJob(
        client=_Client(fail_push=True),
        aliases_jsonl=aliases_path,
        community_posts_jsonl=posts_path,
        window_minutes=60,
        clock=lambda: datetime(2026, 6, 11, 1, 2, tzinfo=timezone.utc),
    )

    result = job.run_once()

    assert result.status == "CLIENT_ERROR"
    assert result.observation_count == 1
    assert result.snapshot_count == 1


def test_configure_scheduler_registers_real_estate_reaction_snapshot_refresh_job():
    scheduler = AsyncIOScheduler(timezone="UTC")
    reaction_job = RealEstateReactionSnapshotRefreshJob(
        client=_Client(),
        aliases_jsonl="aliases.jsonl",
        community_posts_jsonl="posts.jsonl",
        window_minutes=60,
    )

    configure_scheduler(
        scheduler,
        pipeline=_Pipeline(),
        crawl_interval_minutes=30,
        realestate_reaction_snapshot_refresh_job=reaction_job,
        realestate_reaction_snapshot_interval_minutes=15,
    )

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert jobs["community-crawl"].trigger.interval.total_seconds() == 30 * 60
    assert jobs["realestate-reaction-snapshots-refresh"].trigger.interval.total_seconds() == 15 * 60
