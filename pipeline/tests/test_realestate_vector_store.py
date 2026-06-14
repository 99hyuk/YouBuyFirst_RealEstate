import json
import uuid

import httpx
import respx

from youbuyfirst_pipeline.realestate_vector_store import (
    QdrantRealEstateVectorStoreClient,
    build_qdrant_points,
    qdrant_collection_health_payload,
    qdrant_search_results_to_similar_windows,
)


@respx.mock
def test_qdrant_client_creates_collection_and_upserts_embedding_points():
    collection_route = respx.put("http://qdrant.local/collections/realestate_windows").mock(
        return_value=httpx.Response(200, json={"result": True})
    )
    upsert_route = respx.put("http://qdrant.local/collections/realestate_windows/points").mock(
        return_value=httpx.Response(200, json={"result": {"operation_id": 7}})
    )
    client = QdrantRealEstateVectorStoreClient(
        base_url="http://qdrant.local",
        api_key="test-qdrant-key",
        collection_name="realestate_windows",
    )
    points = build_qdrant_points([_embedding_item("source-window", [0.1, 0.2, 0.3])])

    client.ensure_collection(vector_size=3)
    result = client.upsert_points(points)

    assert result == {"result": {"operation_id": 7}}
    assert collection_route.called
    collection_request = json.loads(collection_route.calls[0].request.content)
    assert collection_request == {
        "vectors": {"size": 3, "distance": "Cosine"},
    }
    upsert_request = upsert_route.calls[0].request
    assert upsert_request.headers["api-key"] == "test-qdrant-key"
    assert json.loads(upsert_request.content)["points"][0] == {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "youbuyfirst-realestate:source-window")),
        "vector": [0.1, 0.2, 0.3],
        "payload": {
            "inputId": "source-window",
            "targetType": "region",
            "targetId": "region-seoul-mapo",
            "refType": "reaction_snapshot",
            "refId": "snapshot-source-window",
            "provider": "gms:gemini",
            "modelName": "gemini-embedding-2",
            "text": "마포 전세 우려와 교통 기대",
            "dimensions": 3,
            "dataStatus": "generated",
        },
    }


@respx.mock
def test_qdrant_client_searches_by_vector_and_returns_raw_results():
    search_route = respx.post("http://qdrant.local/collections/realestate_windows/points/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": [
                    {
                        "id": "matched-window",
                        "score": 0.94,
                        "payload": {
                            "targetId": "region-gwangju",
                            "refId": "snapshot-matched-window",
                            "windowStart": "2026-03-01T00:00:00Z",
                            "windowEnd": "2026-03-01T01:00:00Z",
                            "text": "광주 전세 우려와 교통 기대",
                        },
                    }
                ]
            },
        )
    )
    client = QdrantRealEstateVectorStoreClient(
        base_url="http://qdrant.local",
        collection_name="realestate_windows",
    )

    result = client.search(vector=[0.1, 0.2, 0.3], top_n=1, exclude_input_id="source-window")

    assert result[0]["score"] == 0.94
    assert json.loads(search_route.calls[0].request.content) == {
        "vector": [0.1, 0.2, 0.3],
        "limit": 1,
        "with_payload": True,
        "filter": {
            "must_not": [
                {
                    "key": "inputId",
                    "match": {"value": "source-window"},
                }
            ]
        },
    }


@respx.mock
def test_qdrant_client_reads_collection_info_without_exposing_secret():
    info_route = respx.get("http://qdrant.local/collections/realestate_windows").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": {
                    "status": "green",
                    "points_count": 42,
                    "vectors_count": 42,
                }
            },
        )
    )
    client = QdrantRealEstateVectorStoreClient(
        base_url="http://qdrant.local",
        api_key="test-qdrant-key",
        collection_name="realestate_windows",
    )

    payload = qdrant_collection_health_payload(client)

    assert info_route.called
    assert info_route.calls[0].request.headers["api-key"] == "test-qdrant-key"
    assert payload == {
        "collection": "realestate_windows",
        "ready": True,
        "status": "green",
        "pointsCount": 42,
        "vectorsCount": 42,
        "message": "collection_ready",
    }
    assert "test-qdrant-key" not in json.dumps(payload)


@respx.mock
def test_qdrant_collection_health_payload_marks_missing_collection_not_ready():
    respx.get("http://qdrant.local/collections/realestate_windows").mock(return_value=httpx.Response(404))
    client = QdrantRealEstateVectorStoreClient(
        base_url="http://qdrant.local",
        collection_name="realestate_windows",
    )

    payload = qdrant_collection_health_payload(client)

    assert payload == {
        "collection": "realestate_windows",
        "ready": False,
        "status": "missing",
        "pointsCount": None,
        "vectorsCount": None,
        "message": "collection_not_found",
    }


def test_qdrant_search_results_are_converted_to_evidence_compatible_similar_windows():
    source_input_id = "reaction-window:region-seoul-mapo:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z"
    items = qdrant_search_results_to_similar_windows(
        source_input=_embedding_item(source_input_id, [0.1, 0.2, 0.3]),
        search_results=[
            {
                "id": "matched-window",
                "score": 0.94,
                "payload": {
                    "targetId": "region-gwangju",
                    "refId": "snapshot-matched-window",
                    "windowStart": "2026-03-01T00:00:00Z",
                    "windowEnd": "2026-03-01T01:00:00Z",
                    "text": "광주 전세 우려와 교통 기대",
                },
            }
        ],
    )

    assert items == [
        {
            "sourceTargetId": "region-seoul-mapo",
            "sourceWindowStart": "2026-06-14T00:00:00Z",
            "matchedTargetId": "region-gwangju",
            "matchedWindowStart": "2026-03-01T00:00:00Z",
            "matchedWindowEnd": "2026-03-01T01:00:00Z",
            "similarityScore": 0.94,
            "matchReason": "qdrant:cosine",
            "issueOverlap": [],
            "afterMarketSummary": {"horizonDays": None, "items": []},
            "caveat": "market_fact_not_joined",
            "evidenceItem": {
                "evidenceItemId": "similar-window-region-seoul-mapo-region-gwangju-snapshot-matched-window",
                "evidenceType": "similar_window",
                "refType": "similar_window",
                "refId": "snapshot-matched-window",
                "label": "유사 과거 window",
                "valueText": "유사도 94.0% · 광주 전세 우려와 교통 기대",
                "severity": "info",
            },
        }
    ]


def test_qdrant_search_results_join_after_market_fact_summary():
    source_input_id = "reaction-window:region-seoul-mapo:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z"
    items = qdrant_search_results_to_similar_windows(
        source_input=_embedding_item(source_input_id, [0.1, 0.2, 0.3]),
        search_results=[
            {
                "id": "matched-window",
                "score": 0.94,
                "payload": {
                    "targetId": "region-gwangju",
                    "refId": "snapshot-matched-window",
                    "windowStart": "2026-03-01T00:00:00Z",
                    "windowEnd": "2026-03-01T01:00:00Z",
                    "text": "광주 전세 우려와 교통 기대",
                },
            }
        ],
        market_facts=[
            {
                "targetId": "region-gwangju",
                "factType": "apt_trade",
                "observedAt": "2026-03-10",
                "valueJson": {"dealAmountManwon": 50000},
            },
            {
                "targetId": "region-gwangju",
                "factType": "apt_trade",
                "observedAt": "2026-04-20",
                "valueJson": {"dealAmountManwon": 53000},
            },
        ],
        horizon_days=90,
    )

    assert items[0]["afterMarketSummary"] == {
        "horizonDays": 90,
        "items": [
            {
                "factType": "apt_trade",
                "metric": "dealAmountManwon",
                "firstObservedAt": "2026-03-10",
                "lastObservedAt": "2026-04-20",
                "firstValue": 50000.0,
                "lastValue": 53000.0,
                "deltaPct": 6.0,
                "sampleCount": 2,
            }
        ],
    }
    assert items[0]["caveat"] is None
    assert items[0]["evidenceItem"]["valueText"] == "유사도 94.0% · 매매 +6.0%"


def test_qdrant_search_results_skip_non_past_windows():
    source_input_id = "reaction-window:region-seoul-mapo:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z"
    items = qdrant_search_results_to_similar_windows(
        source_input=_embedding_item(source_input_id, [0.1, 0.2, 0.3]),
        search_results=[
            {
                "id": "future-window",
                "score": 0.99,
                "payload": {
                    "targetId": "region-busan",
                    "refId": "snapshot-future-window",
                    "windowStart": "2026-06-15T00:00:00Z",
                    "windowEnd": "2026-06-15T01:00:00Z",
                    "text": "미래 window는 유사 과거 후보가 아닙니다",
                },
            },
            {
                "id": "matched-window",
                "score": 0.94,
                "payload": {
                    "targetId": "region-gwangju",
                    "refId": "snapshot-matched-window",
                    "windowStart": "2026-03-01T00:00:00Z",
                    "windowEnd": "2026-03-01T01:00:00Z",
                    "text": "광주 전세 우려와 교통 기대",
                },
            },
        ],
    )

    assert [item["matchedTargetId"] for item in items] == ["region-gwangju"]


def _embedding_item(input_id: str, embedding: list[float]):
    return {
        "inputId": input_id,
        "targetType": "region",
        "targetId": "region-seoul-mapo",
        "refType": "reaction_snapshot",
        "refId": f"snapshot-{input_id}",
        "provider": "gms:gemini",
        "modelName": "gemini-embedding-2",
        "text": "마포 전세 우려와 교통 기대",
        "embedding": embedding,
        "dimensions": len(embedding),
        "dataStatus": "generated",
    }
