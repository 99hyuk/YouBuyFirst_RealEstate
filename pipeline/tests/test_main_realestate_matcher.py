import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


def test_realestate_target_matches_command_prints_matched_posts(monkeypatch, tmp_path, capsys):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-daejeon","alias":"대전","reviewState":"approved","confidence":0.95}',
                '{"targetType":"complex","targetId":"complex-dunsan-xi","alias":"둔산자이","reviewState":"approved","confidence":0.87}',
            ]
        ),
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        "\n".join(
            [
                '{"source":"PPOMPPU:house","externalId":"post-1","publishedAt":"2026-06-11T00:10:00Z","title":"둔산자이랑 대전","contentSnippet":"교통 이야기","url":"https://example.test/post-1"}',
                '{"source":"PPOMPPU:house","externalId":"post-2","publishedAt":"2026-06-11T00:11:00Z","title":"별칭 없는 글","contentSnippet":"관망","url":"https://example.test/post-2"}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-target-matches",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--community-posts-jsonl",
            str(posts_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert [item["externalId"] for item in payload["items"]] == ["post-1", "post-2"]
    assert payload["items"][0]["title"] == "둔산자이랑 대전"
    assert payload["items"][0]["contentSnippet"] == "교통 이야기"
    assert payload["items"][0]["matched"] is True
    assert [mention["targetId"] for mention in payload["items"][0]["mentions"]] == [
        "complex-dunsan-xi",
        "region-daejeon",
    ]
    assert payload["items"][1]["matched"] is False


class _FakeSpringClient:
    published_alias_candidates = []

    def list_real_estate_aliases(self, **_kwargs):
        return [
            {
                "targetType": "region",
                "targetId": "region-daejeon",
                "alias": "대전",
                "aliasType": "official",
                "reviewState": "approved",
                "confidence": 0.95,
                "ambiguous": False,
                "source": "backend:test",
            }
        ]

    def publish_real_estate_alias_candidates(self, candidates):
        self.published_alias_candidates = candidates
        _FakeSpringClient.published_alias_candidates = candidates


def test_realestate_target_matches_command_can_read_approved_aliases_from_backend(monkeypatch, tmp_path, capsys):
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"post-1","publishedAt":"2026-06-11T00:10:00Z","title":"대전 관심 증가","contentSnippet":"대전 전세 이야기도 많음"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-target-matches",
            "--realestate-use-backend-aliases",
            "--community-posts-jsonl",
            str(posts_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["matched"] is True
    assert payload["items"][0]["mentions"][0]["targetId"] == "region-daejeon"


def test_realestate_alias_candidates_command_prints_candidate_aliases(monkeypatch, tmp_path, capsys):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"complex","targetId":"complex-mrp","alias":"Mapo Raemian Prugio","reviewState":"approved","confidence":0.96}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"post-mrp-1","publishedAt":"2026-06-13T01:00:00Z","title":"Mapo Raemian Prugio(MRP) rent anxiety","contentSnippet":"MRP is mentioned again","url":"https://example.test/post-mrp-1"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-alias-candidates",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--community-posts-jsonl",
            str(posts_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["targetId"] == "complex-mrp"
    assert payload["items"][0]["alias"] == "MRP"
    assert payload["items"][0]["reviewState"] == "candidate"
    assert payload["items"][0]["source"] == "community:auto-candidate:PPOMPPU:house"


def test_realestate_alias_candidates_push_sends_candidates_to_backend(monkeypatch, tmp_path):
    _FakeSpringClient.published_alias_candidates = []
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"complex","targetId":"complex-mrp","alias":"Mapo Raemian Prugio","reviewState":"approved","confidence":0.96}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"post-mrp-1","publishedAt":"2026-06-13T01:00:00Z","title":"Mapo Raemian Prugio(MRP) rent anxiety","contentSnippet":"MRP is mentioned again","url":"https://example.test/post-mrp-1"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-alias-candidates-push",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--community-posts-jsonl",
            str(posts_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert [candidate.alias for candidate in _FakeSpringClient.published_alias_candidates] == ["MRP"]


def test_realestate_alias_coverage_command_prints_source_level_report(monkeypatch, tmp_path, capsys):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-daejeon","alias":"Daejeon","reviewState":"approved","confidence":0.95}',
                '{"targetType":"complex","targetId":"complex-mrp","alias":"Mapo Raemian Prugio","reviewState":"approved","confidence":0.96}',
            ]
        ),
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        "\n".join(
            [
                '{"source":"PPOMPPU:house","externalId":"post-1","publishedAt":"2026-06-13T01:00:00Z","title":"Daejeon traffic","contentSnippet":"Daejeon rent anxiety","url":"https://example.test/post-1"}',
                '{"source":"PPOMPPU:house","externalId":"post-2","publishedAt":"2026-06-13T01:05:00Z","title":"Unknown nickname","contentSnippet":"missing alias","url":"https://example.test/post-2"}',
                '{"source":"DCINSIDE:immovables","externalId":"post-3","publishedAt":"2026-06-13T01:10:00Z","title":"Mapo Raemian Prugio(MRP) rent anxiety","contentSnippet":"MRP slang","url":"https://example.test/post-3"}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-alias-coverage",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--community-posts-jsonl",
            str(posts_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["totals"]["matchRate"] == 0.6667
    assert [source["source"] for source in payload["sources"]] == [
        "DCINSIDE:immovables",
        "PPOMPPU:house",
    ]
    assert payload["sources"][0]["candidateAliases"][0]["alias"] == "MRP"
    assert payload["sources"][1]["unmatchedExamples"][0]["externalId"] == "post-2"
