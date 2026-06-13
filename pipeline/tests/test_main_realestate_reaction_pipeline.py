import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakeSpringClient:
    def __init__(self) -> None:
        self.reaction_batches = []

    def publish_real_estate_reaction_snapshots(self, snapshots) -> None:
        self.reaction_batches.append([snapshot.to_request_dict() for snapshot in snapshots])

    def list_real_estate_target_edges(self, **_kwargs) -> list[dict]:
        return [
            {
                "fromTargetType": "region",
                "fromTargetId": "region-seoul",
                "toTargetType": "region",
                "toTargetId": "region-seoul-jongno",
                "edgeType": "contains",
                "reviewState": "approved",
                "confidence": 0.9,
                "source": "admin:registry",
            }
        ]


def test_realestate_reaction_snapshots_from_posts_command_prints_end_to_end_snapshot(monkeypatch, tmp_path, capsys):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","alias":"대전","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        "\n".join(
            [
                '{"source":"DCINSIDE:immovables","externalId":"post-prev","publishedAt":"2026-06-10T23:30:00Z","title":"대전 전세 불안","contentSnippet":"전세 부담이 커졌다는 이야기"}',
                '{"source":"PPOMPPU:house","externalId":"post-1","publishedAt":"2026-06-11T00:05:00Z","title":"대전 GTX 호재 기대","contentSnippet":"교통 개선 이야기가 많습니다"}',
                '{"source":"DCINSIDE:immovables","externalId":"post-2","publishedAt":"2026-06-11T00:25:00Z","title":"대전 전세 불안","contentSnippet":"보증금 부담 우려가 있습니다"}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reaction-snapshots-from-posts",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--community-posts-jsonl",
            str(posts_path),
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
    assert len(payload["items"]) == 1
    snapshot = payload["items"][0]
    assert snapshot["targetId"] == "region-daejeon"
    assert snapshot["mentionCount"] == 2
    assert snapshot["previousMentionCount"] == 1
    assert snapshot["expectationScore"] == 50.0
    assert snapshot["concernScore"] == 50.0
    assert snapshot["heatScore"] == 43
    assert snapshot["confidence"] == 0.52
    assert [(issue["issueKey"], issue["share"]) for issue in snapshot["issues"]] == [
        ("jeonse", 0.5),
        ("transport", 0.5),
    ]


def test_realestate_reaction_snapshots_from_posts_push_command_publishes_snapshots(monkeypatch, tmp_path):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","alias":"대전","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"post-1","publishedAt":"2026-06-11T00:05:00Z","title":"대전 GTX 호재 기대","contentSnippet":"교통 개선 이야기"}',
        encoding="utf-8",
    )
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reaction-snapshots-from-posts-push",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--community-posts-jsonl",
            str(posts_path),
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


def test_realestate_reaction_snapshots_from_posts_command_rolls_child_region_up_to_parent(
    monkeypatch,
    tmp_path,
    capsys,
):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"region","targetId":"region-seoul-jongno","alias":"종로","reviewState":"approved","confidence":0.95}',
        encoding="utf-8",
    )
    edges_path = tmp_path / "target_edges.jsonl"
    edges_path.write_text(
        '{"fromTargetType":"region","fromTargetId":"region-seoul","toTargetType":"region","toTargetId":"region-seoul-jongno","edgeType":"contains","reviewState":"approved","confidence":0.9}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"NAVER_CAFE:estate","externalId":"post-1","publishedAt":"2026-06-11T00:05:00Z","title":"종로 재건축 기대","contentSnippet":"재건축 호재와 학군 기대가 같이 나옵니다"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reaction-snapshots-from-posts",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--realestate-target-edges-jsonl",
            str(edges_path),
            "--community-posts-jsonl",
            str(posts_path),
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
    assert [item["targetId"] for item in payload["items"]] == [
        "region-seoul",
        "region-seoul-jongno",
    ]
    assert [item["mentionCount"] for item in payload["items"]] == [1, 1]


def test_realestate_target_edges_fetch_command_prints_backend_edges(monkeypatch, capsys):
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-target-edges-fetch",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["items"] == [
        {
            "fromTargetType": "region",
            "fromTargetId": "region-seoul",
            "toTargetType": "region",
            "toTargetId": "region-seoul-jongno",
            "edgeType": "contains",
            "reviewState": "approved",
            "confidence": 0.9,
            "source": "admin:registry",
        }
    ]
