import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


def test_realestate_reaction_observations_command_prints_classifier_payload(monkeypatch, tmp_path, capsys):
    aliases_path = tmp_path / "aliases.jsonl"
    aliases_path.write_text(
        '{"targetType":"complex","targetId":"complex-dunsan-xi","alias":"둔산자이","reviewState":"approved","confidence":0.87}',
        encoding="utf-8",
    )
    posts_path = tmp_path / "posts.jsonl"
    posts_path.write_text(
        '{"source":"PPOMPPU:house","externalId":"post-1","publishedAt":"2026-06-11T00:10:00Z","title":"둔산자이 GTX 호재 기대","contentSnippet":"대전 교통 개선 이야기","url":"https://example.test/post-1"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-reaction-observations",
            "--realestate-aliases-jsonl",
            str(aliases_path),
            "--community-posts-jsonl",
            str(posts_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "items": [
            {
                "source": "PPOMPPU:house",
                "externalId": "post-1",
                "targetType": "complex",
                "targetId": "complex-dunsan-xi",
                "publishedAt": "2026-06-11T00:10:00Z",
                "matchedText": "둔산자이",
                "matchSource": "title",
                "reactionDirection": "expectation",
                "confidence": 0.73,
                "issues": [
                    {
                        "issueKey": "transport",
                        "label": "교통",
                        "direction": "expectation",
                        "summary": "교통 호재와 접근성 기대가 함께 언급됨",
                        "confidence": 0.78,
                    }
                ],
            }
        ]
    }
