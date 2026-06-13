import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


def test_realestate_similar_windows_command_prints_matches_with_evidence_item(monkeypatch, tmp_path, capsys):
    snapshots_path = tmp_path / "snapshots.jsonl"
    snapshots_path.write_text(
        "\n".join(
            [
                '{"targetType":"region","targetId":"region-daejeon","windowStart":"2026-06-11T00:00:00Z","windowEnd":"2026-06-11T01:00:00Z","asOf":"2026-06-11T01:02:00Z","mentionCount":4,"previousMentionCount":2,"expectationScore":50.0,"concernScore":25.0,"neutralScore":25.0,"heatScore":71,"confidence":0.66,"sourceCount":3,"sourceSkew":0.5,"coverageStatus":"partial","stale":false,"issues":[{"issueKey":"rail","label":"교통","share":0.5,"direction":"expectation","summary":"교통 기대","confidence":0.7}]}',
                '{"targetType":"region","targetId":"region-gwangju","windowStart":"2026-03-01T00:00:00Z","windowEnd":"2026-03-01T01:00:00Z","asOf":"2026-03-01T01:02:00Z","mentionCount":8,"previousMentionCount":4,"expectationScore":52.0,"concernScore":24.0,"neutralScore":24.0,"heatScore":70,"confidence":0.72,"sourceCount":3,"sourceSkew":0.5,"coverageStatus":"partial","stale":false,"issues":[{"issueKey":"rail","label":"교통","share":0.45,"direction":"expectation","summary":"교통 기대","confidence":0.8}]}',
            ]
        ),
        encoding="utf-8",
    )
    facts_path = tmp_path / "facts.jsonl"
    facts_path.write_text(
        "\n".join(
            [
                '{"targetId":"region-gwangju","factType":"apt_trade","observedAt":"2026-03-10","valueJson":{"dealAmountManwon":50000}}',
                '{"targetId":"region-gwangju","factType":"apt_trade","observedAt":"2026-04-20","valueJson":{"dealAmountManwon":53000}}',
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-similar-windows",
            "--reaction-snapshots-jsonl",
            str(snapshots_path),
            "--similar-source-target-id",
            "region-daejeon",
            "--similar-source-window-start",
            "2026-06-11T00:00:00Z",
            "--similar-market-facts-jsonl",
            str(facts_path),
            "--similar-top-n",
            "1",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["matchedTargetId"] == "region-gwangju"
    assert payload["items"][0]["evidenceItem"]["evidenceType"] == "similar_window"
    assert payload["items"][0]["evidenceItem"]["valueText"] == "유사도 99.3% · 매매 +6.0%"
    assert payload["items"][0]["afterMarketSummary"]["items"][0]["deltaPct"] == 6.0
