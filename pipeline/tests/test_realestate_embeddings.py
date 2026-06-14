import json

import httpx
import pytest
import respx

from youbuyfirst_pipeline.realestate_embeddings import (
    GmsGeminiEmbeddingClient,
    build_real_estate_embedding_inputs,
    load_real_estate_embedding_inputs,
)


@respx.mock
def test_gms_gemini_embedding_client_calls_embed_content_with_gms_key():
    route = respx.post(
        "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"embedding": {"values": [0.12, -0.25, 0.5]}},
        )
    )
    client = GmsGeminiEmbeddingClient(api_key="test-gms-key")

    embedding = client.embed_text("마포 전세 우려와 학군 기대가 같이 언급됩니다.")

    assert embedding == [0.12, -0.25, 0.5]
    assert route.called
    request = route.calls[0].request
    assert request.headers["x-goog-api-key"] == "test-gms-key"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {
        "content": {
            "parts": [
                {
                    "text": "마포 전세 우려와 학군 기대가 같이 언급됩니다.",
                }
            ]
        }
    }


def test_embedding_inputs_are_loaded_from_jsonl_and_use_window_summary_text(tmp_path):
    path = tmp_path / "snapshots.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "targetType": "region",
                        "targetId": "region-seoul-mapo",
                        "windowStart": "2026-06-14T00:00:00Z",
                        "windowEnd": "2026-06-14T01:00:00Z",
                        "mentionCount": 12,
                        "expectationScore": 52.5,
                        "concernScore": 31.2,
                        "heatScore": 74,
                        "issues": [
                            {"issueKey": "jeonse", "label": "전세", "summary": "전세 매물 우려"},
                            {"issueKey": "school", "label": "학군", "summary": "학군 기대"},
                        ],
                    },
                    ensure_ascii=False,
                )
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_real_estate_embedding_inputs(path)
    inputs = build_real_estate_embedding_inputs(loaded)

    assert len(inputs) == 1
    assert inputs[0].input_id == "reaction-window:region-seoul-mapo:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z"
    assert inputs[0].target_id == "region-seoul-mapo"
    assert inputs[0].ref_type == "reaction_snapshot"
    assert inputs[0].model_name == "gemini-embedding-2"
    assert "언급 12건" in inputs[0].text
    assert "기대 52.5%" in inputs[0].text
    assert "전세: 전세 매물 우려" in inputs[0].text


def test_embedding_client_requires_non_empty_text():
    client = GmsGeminiEmbeddingClient(api_key="test-gms-key")

    with pytest.raises(ValueError, match="text is required"):
        client.embed_text("  ")
