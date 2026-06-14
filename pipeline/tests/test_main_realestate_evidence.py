import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakeSpringClient:
    def __init__(self) -> None:
        self.evidence_batches = []

    def publish_real_estate_evidence_logs(self, logs) -> None:
        self.evidence_batches.append(list(logs))


def test_realestate_evidence_logs_command_prints_evaluation_payload(monkeypatch, tmp_path, capsys):
    paths = _write_input_files(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-evidence-logs",
            "--reaction-snapshots-jsonl",
            str(paths["snapshots"]),
            "--evidence-target-id",
            "region-daejeon",
            "--evidence-window-start",
            "2026-06-11T00:00:00Z",
            "--evidence-evaluated-at",
            "2026-06-12T02:00:00Z",
            "--evidence-market-facts-jsonl",
            str(paths["facts"]),
            "--evidence-similar-windows-jsonl",
            str(paths["similar"]),
            "--evidence-content-items-jsonl",
            str(paths["content"]),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["logs"][0]["targetId"] == "region-daejeon"
    assert [item["evidenceType"] for item in payload["logs"][0]["evidenceItems"]] == [
        "reaction",
        "market_fact",
        "similar_window",
        "search_candidate",
    ]


def test_realestate_evidence_logs_push_command_publishes_evaluation_payload(monkeypatch, tmp_path):
    paths = _write_input_files(tmp_path)
    fake_client = _FakeSpringClient()
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-evidence-logs-push",
            "--reaction-snapshots-jsonl",
            str(paths["snapshots"]),
            "--evidence-target-id",
            "region-daejeon",
            "--evidence-window-start",
            "2026-06-11T00:00:00Z",
            "--evidence-evaluated-at",
            "2026-06-12T02:00:00Z",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert fake_client.evidence_batches[0][0]["evidenceLogId"] == (
        "evidence-region-daejeon-20260611000000-20260612020000-realestate-eval-v1"
    )
    assert fake_client.evidence_batches[0][0]["caveats"][-3:] == [
        "market_fact_missing",
        "similar_window_missing",
        "search_candidate_missing",
    ]


def _write_input_files(tmp_path):
    snapshots = tmp_path / "snapshots.jsonl"
    snapshots.write_text(
        json.dumps(
            {
                "targetType": "region",
                "targetId": "region-daejeon",
                "windowStart": "2026-06-11T00:00:00Z",
                "windowEnd": "2026-06-11T01:00:00Z",
                "asOf": "2026-06-11T01:02:00Z",
                "mentionCount": 4,
                "previousMentionCount": 2,
                "expectationScore": 50.0,
                "concernScore": 25.0,
                "neutralScore": 25.0,
                "heatScore": 71,
                "confidence": 0.66,
                "sourceCount": 3,
                "sourceSkew": 0.5,
                "coverageStatus": "partial",
                "stale": False,
                "issues": [{"issueKey": "rail", "label": "교통", "share": 0.5, "direction": "expectation"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    facts = tmp_path / "facts.jsonl"
    facts.write_text(
        json.dumps(
            {
                "targetId": "region-daejeon",
                "factType": "apt_trade",
                "observedAt": "2026-06-10",
                "providerObjectId": "molit_apt_trade:30200:202606:1",
                "valueJson": {"dealAmountManwon": 73000},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    similar = tmp_path / "similar.jsonl"
    similar.write_text(
        json.dumps(
            {
                "evidenceItem": {
                    "evidenceItemId": "similar-region-daejeon-region-gwangju",
                    "evidenceType": "similar_window",
                    "refType": "similar_window",
                    "refId": "region-gwangju-2026-03-01",
                    "label": "유사 과거 window",
                    "valueText": "유사도 96.2%",
                    "severity": "info",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    content = tmp_path / "content.jsonl"
    content.write_text(
        json.dumps(
            {
                "contentId": "serpapi-issue-daejeon",
                "sourceId": "serpapi:google_news",
                "title": "대전 교통 이슈 후보",
                "url": "https://example.com/daejeon",
                "targets": [{"targetId": "region-daejeon", "linkType": "search_candidate"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {
        "snapshots": snapshots,
        "facts": facts,
        "similar": similar,
        "content": content,
    }
