import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakeEmbeddingClient:
    def __init__(self) -> None:
        self.texts = []

    def embed_text(self, text: str):
        self.texts.append(text)
        return [0.1, 0.2, 0.3]


def test_realestate_embeddings_command_prints_embedding_payload(monkeypatch, tmp_path, capsys):
    snapshots_path = tmp_path / "snapshots.jsonl"
    snapshots_path.write_text(
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
                "issues": [{"label": "전세", "summary": "전세 매물 우려"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    fake_client = _FakeEmbeddingClient()
    monkeypatch.setattr(pipeline_main, "_gms_gemini_embedding_client", lambda **_kwargs: fake_client)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "realestate-embeddings",
            "--reaction-snapshots-jsonl",
            str(snapshots_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    payload = json.loads(capsys.readouterr().out)
    assert fake_client.texts == [payload["items"][0]["text"]]
    assert payload["items"][0]["inputId"] == "reaction-window:region-seoul-mapo:2026-06-14T00:00:00Z"
    assert payload["items"][0]["targetId"] == "region-seoul-mapo"
    assert payload["items"][0]["provider"] == "gms:gemini"
    assert payload["items"][0]["modelName"] == "gemini-embedding-2"
    assert payload["items"][0]["embedding"] == [0.1, 0.2, 0.3]
