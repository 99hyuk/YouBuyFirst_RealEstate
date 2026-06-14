import asyncio
import json
import sys
import uuid

from youbuyfirst_pipeline import main as pipeline_main


class _FakeVectorStoreClient:
    def __init__(self) -> None:
        self.collection_name = "realestate_reaction_windows"
        self.collection_sizes = []
        self.upserted_points = []
        self.search_requests = []

    def ensure_collection(self, *, vector_size: int):
        self.collection_sizes.append(vector_size)

    def upsert_points(self, points):
        self.upserted_points.append(points)
        return {"result": {"operation_id": 11}}

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


class _FakeVectorStoreHealthClient:
    collection_name = "realestate_reaction_windows"

    def collection_info(self):
        return {
            "result": {
                "status": "green",
                "points_count": 7,
                "vectors_count": 7,
            }
        }


def test_realestate_vector_health_command_prints_collection_status(monkeypatch, capsys):
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: _FakeVectorStoreHealthClient())
    monkeypatch.setattr(sys, "argv", ["youbuyfirst-pipeline", "realestate-vector-health"])

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "collection": "realestate_reaction_windows",
        "ready": True,
        "status": "green",
        "pointsCount": 7,
        "vectorsCount": 7,
        "message": "collection_ready",
    }


def test_realestate_vector_upsert_command_pushes_embeddings_to_qdrant(monkeypatch, tmp_path, capsys):
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(json.dumps({"items": [_embedding_item("source-window")]}, ensure_ascii=False), encoding="utf-8")
    fake_client = _FakeVectorStoreClient()
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-vector-upsert",
            "--embeddings-jsonl",
            str(embeddings_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"collection": "realestate_reaction_windows", "vectorSize": 3, "upsertedPoints": 1}
    assert fake_client.collection_sizes == [3]
    assert fake_client.upserted_points[0][0]["id"] == str(
        uuid.uuid5(uuid.NAMESPACE_URL, "youbuyfirst-realestate:source-window")
    )


def test_realestate_vector_search_command_prints_evidence_compatible_matches(monkeypatch, tmp_path, capsys):
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(json.dumps({"items": [_embedding_item("source-window")]}, ensure_ascii=False), encoding="utf-8")
    fake_client = _FakeVectorStoreClient()
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-vector-search",
            "--embeddings-jsonl",
            str(embeddings_path),
            "--vector-source-input-id",
            "source-window",
            "--vector-top-n",
            "1",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert fake_client.search_requests == [
        {
            "vector": [0.1, 0.2, 0.3],
            "top_n": 1,
            "exclude_input_id": "source-window",
        }
    ]
    assert payload["items"][0]["matchedTargetId"] == "region-gwangju"
    assert payload["items"][0]["evidenceItem"]["evidenceType"] == "similar_window"
    assert payload["items"][0]["evidenceItem"]["valueText"].startswith("유사도 91.0%")


def test_realestate_vector_search_command_joins_after_market_facts(monkeypatch, tmp_path, capsys):
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(json.dumps({"items": [_embedding_item("source-window")]}, ensure_ascii=False), encoding="utf-8")
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
            "realestate-vector-search",
            "--embeddings-jsonl",
            str(embeddings_path),
            "--vector-source-input-id",
            "source-window",
            "--vector-top-n",
            "1",
            "--similar-market-facts-jsonl",
            str(facts_path),
            "--similar-horizon-days",
            "90",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["afterMarketSummary"]["items"][0]["deltaPct"] == 6.0
    assert payload["items"][0]["caveat"] is None
    assert payload["items"][0]["evidenceItem"]["valueText"] == "유사도 91.0% · 매매 +6.0%"


def _embedding_item(input_id: str):
    return {
        "inputId": input_id,
        "targetType": "region",
        "targetId": "region-seoul-mapo",
        "refType": "reaction_snapshot",
        "refId": f"snapshot-{input_id}",
        "provider": "gms:gemini",
        "modelName": "gemini-embedding-2",
        "text": "마포 전세 우려와 교통 기대",
        "embedding": [0.1, 0.2, 0.3],
        "dimensions": 3,
        "dataStatus": "generated",
    }
