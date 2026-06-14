import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakeVectorStoreClient:
    def __init__(self) -> None:
        self.search_requests = []

    def search(self, *, vector, top_n: int, exclude_input_id: str | None = None):
        self.search_requests.append(
            {
                "vector": vector,
                "top_n": top_n,
                "exclude_input_id": exclude_input_id,
            }
        )
        return [
            {
                "id": "matched-window",
                "score": 0.91,
                "payload": {
                    "targetId": "region-gwangju",
                    "refId": "snapshot-matched-window",
                    "windowStart": "2026-03-01T00:00:00Z",
                    "windowEnd": "2026-03-01T01:00:00Z",
                    "text": "광주 전세 우려와 교통 기대",
                },
            }
        ]


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


def test_realestate_similar_windows_command_can_use_qdrant_engine(monkeypatch, tmp_path, capsys):
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "inputId": "reaction-window:region-daejeon:2026-06-11T00:00:00Z:2026-06-11T01:00:00Z",
                        "targetType": "region",
                        "targetId": "region-daejeon",
                        "refType": "reaction_snapshot",
                        "refId": "snapshot-source-window",
                        "provider": "gms:gemini",
                        "modelName": "gemini-embedding-2",
                        "text": "대전 교통 기대와 공급 우려",
                        "embedding": [0.1, 0.2, 0.3],
                        "dimensions": 3,
                        "dataStatus": "generated",
                    }
                ]
            },
            ensure_ascii=False,
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
    fake_client = _FakeVectorStoreClient()
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-similar-windows",
            "--similar-engine",
            "qdrant",
            "--embeddings-jsonl",
            str(embeddings_path),
            "--vector-source-input-id",
            "reaction-window:region-daejeon:2026-06-11T00:00:00Z:2026-06-11T01:00:00Z",
            "--similar-market-facts-jsonl",
            str(facts_path),
            "--similar-top-n",
            "1",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert fake_client.search_requests == [
        {
            "vector": [0.1, 0.2, 0.3],
            "top_n": 1,
            "exclude_input_id": "reaction-window:region-daejeon:2026-06-11T00:00:00Z:2026-06-11T01:00:00Z",
        }
    ]
    assert payload["engine"] == "qdrant"
    assert payload["items"][0]["sourceTargetId"] == "region-daejeon"
    assert payload["items"][0]["matchedTargetId"] == "region-gwangju"
    assert payload["items"][0]["afterMarketSummary"]["items"][0]["deltaPct"] == 6.0
    assert payload["items"][0]["evidenceItem"]["valueText"] == "유사도 91.0% · 매매 +6.0%"
