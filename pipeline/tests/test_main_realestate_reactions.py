import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakeSpringClient:
    def __init__(self) -> None:
        self.reaction_batches = []

    def publish_real_estate_reaction_snapshots(self, snapshots) -> None:
        self.reaction_batches.append([snapshot.to_request_dict() for snapshot in snapshots])


def test_realestate_reaction_snapshots_command_prints_payload(monkeypatch, tmp_path, capsys):
    observations_path = tmp_path / "observations.jsonl"
    observations_path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-daejeon","publishedAt":"2026-06-11T00:05:00Z","source":"naver-cafe","reactionDirection":"expectation"}',
                '{"targetType":"region","targetId":"region-daejeon","publishedAt":"2026-06-10T23:30:00Z","source":"dcinside","reactionDirection":"concern"}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reaction-snapshots",
            "--reaction-observations-jsonl",
            str(observations_path),
            "--reaction-window-start",
            "2026-06-11T00:00:00Z",
            "--reaction-window-minutes",
            "60",
            "--reaction-as-of",
            "2026-06-11T01:02:00Z",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["targetId"] == "region-daejeon"
    assert payload["items"][0]["mentionCount"] == 1
    assert payload["items"][0]["previousMentionCount"] == 1


def test_realestate_reaction_snapshots_command_applies_stale_after_minutes(monkeypatch, tmp_path, capsys):
    observations_path = tmp_path / "observations.jsonl"
    observations_path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-jeju","publishedAt":"2026-06-11T00:05:00Z","source":"naver-cafe","reactionDirection":"expectation"}',
                '{"targetType":"region","targetId":"region-jeju","publishedAt":"2026-06-11T00:15:00Z","source":"dcinside","reactionDirection":"concern"}',
                '{"targetType":"region","targetId":"region-jeju","publishedAt":"2026-06-11T00:25:00Z","source":"naver-cafe","reactionDirection":"neutral"}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reaction-snapshots",
            "--reaction-observations-jsonl",
            str(observations_path),
            "--reaction-window-start",
            "2026-06-11T00:00:00Z",
            "--reaction-window-minutes",
            "1440",
            "--reaction-as-of",
            "2026-06-11T08:30:00Z",
            "--reaction-stale-after-minutes",
            "120",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["targetId"] == "region-jeju"
    assert payload["items"][0]["coverageStatus"] == "stale"
    assert payload["items"][0]["stale"] is True


def test_realestate_reaction_snapshots_push_command_publishes_payload(monkeypatch, tmp_path):
    observations_path = tmp_path / "observations.jsonl"
    observations_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","publishedAt":"2026-06-11T00:05:00Z","source":"naver-cafe","reactionDirection":"expectation"}',
        encoding="utf-8",
    )
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reaction-snapshots-push",
            "--reaction-observations-jsonl",
            str(observations_path),
            "--reaction-window-start",
            "2026-06-11T00:00:00Z",
            "--reaction-window-minutes",
            "60",
            "--reaction-as-of",
            "2026-06-11T01:02:00Z",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert fake_client.reaction_batches[0][0]["targetId"] == "region-daejeon"
    assert fake_client.reaction_batches[0][0]["mentionCount"] == 1
