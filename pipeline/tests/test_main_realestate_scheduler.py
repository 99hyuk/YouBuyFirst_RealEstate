import asyncio
import json
import sys

from youbuyfirst_pipeline import main as pipeline_main


class _FakePipeline:
    pass


class _FakeSpringClient:
    pass


class _FakeRefreshJob:
    def run_once(self) -> dict:
        return {"status": "OK"}


class _FakeRecentIssueClient:
    pass


class _FakeQdrantClient:
    collection_name = "realestate_reaction_windows"

    def __init__(self, *, ready: bool = True) -> None:
        self.ready = ready
        self.search_requests = []

    def collection_info(self):
        if not self.ready:
            return {"status": "missing", "result": None}
        return {
            "result": {
                "status": "green",
                "points_count": 8,
                "vectors_count": 8,
            }
        }

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
                "score": 0.93,
                "payload": {
                    "targetId": "region-gwangju",
                    "refId": "snapshot-gwangju-20260301000000",
                    "windowStart": "2026-03-01T00:00:00Z",
                    "windowEnd": "2026-03-01T01:00:00Z",
                    "text": "광주 전세 우려와 교통 기대",
                },
            }
        ]


def _daily_embedding_item(target_id: str = "region-daejeon") -> dict:
    return {
        "inputId": f"reaction-window:{target_id}:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z",
        "targetType": "region",
        "targetId": target_id,
        "refType": "reaction_snapshot",
        "refId": f"snapshot-{target_id}-20260614000000",
        "provider": "gms:gemini",
        "modelName": "gemini-embedding-2",
        "text": "대전 교통 기대와 공급 우려",
        "embedding": [0.1, 0.2, 0.3],
        "dimensions": 3,
        "dataStatus": "generated",
        "windowStart": "2026-06-14T00:00:00Z",
        "windowEnd": "2026-06-14T01:00:00Z",
    }


def test_serve_command_can_enable_real_estate_market_facts_refresh(monkeypatch):
    captured = {}
    realestate_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: realestate_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--realestate-market-facts-refresh-interval-minutes",
            "720",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_market_facts_refresh_job"] is realestate_job
    assert captured["kwargs"]["realestate_market_facts_interval_minutes"] == 720


def test_serve_command_can_enable_real_estate_reaction_snapshot_refresh(monkeypatch):
    captured = {}
    builder_kwargs = {}
    reaction_job = object()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    def fake_build_reaction_job(**kwargs):
        builder_kwargs.update(kwargs)
        return reaction_job

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_reaction_snapshot_refresh_job",
        fake_build_reaction_job,
    )
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-reaction-snapshots-refresh",
            "--realestate-aliases-jsonl",
            "aliases.jsonl",
            "--community-posts-jsonl",
            "posts.jsonl",
            "--reaction-window-minutes",
            "60",
            "--reaction-stale-after-minutes",
            "180",
            "--realestate-reaction-snapshots-refresh-interval-minutes",
            "15",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    assert captured["kwargs"]["realestate_reaction_snapshot_refresh_job"] is reaction_job
    assert captured["kwargs"]["realestate_reaction_snapshot_interval_minutes"] == 15
    assert builder_kwargs["stale_after_minutes"] == 180


def test_serve_command_can_group_real_estate_refresh_jobs_into_daily_refresh(monkeypatch, tmp_path):
    captured = {}
    market_job = _FakeRefreshJob()
    targets_path = tmp_path / "targets.jsonl"
    targets_path.write_text(
        '{"targetType":"region","targetId":"region-daejeon","displayName":"대전","keywords":["교통"]}',
        encoding="utf-8",
    )

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: _FakeSpringClient())
    monkeypatch.setattr(
        pipeline_main,
        "build_real_estate_market_facts_refresh_job",
        lambda **kwargs: market_job,
    )
    monkeypatch.setattr(pipeline_main, "_serpapi_recent_issue_client", lambda: _FakeRecentIssueClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--realestate-daily-refresh-interval-minutes",
            "1440",
            "--enable-realestate-market-facts-refresh",
            "--realestate-deal-ym",
            "202606",
            "--enable-realestate-recent-issues-refresh",
            "--realestate-search-targets-jsonl",
            str(targets_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert captured["kwargs"]["realestate_market_facts_refresh_job"] is None
    assert captured["kwargs"]["realestate_daily_refresh_interval_minutes"] == 1440
    assert [name for name, _step in daily_job.steps] == ["market_facts", "recent_issues"]


def test_serve_command_can_group_evidence_log_refresh_into_daily_refresh(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--reaction-window-minutes",
            "1440",
            "--realestate-evidence-ranking-limit",
            "3",
            "--realestate-evidence-market-fact-limit",
            "7",
            "--realestate-evidence-timeline-limit",
            "6",
            "--realestate-evidence-content-limit",
            "5",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == ["evidence_logs"]
    evidence_step = daily_job.steps[0][1]
    assert evidence_step.client is spring_client
    assert evidence_step.target_type == "region"
    assert evidence_step.window_minutes == 1440
    assert evidence_step.ranking_limit == 3
    assert evidence_step.market_fact_limit == 7
    assert evidence_step.timeline_limit == 6
    assert evidence_step.content_limit == 5


def test_serve_command_can_enable_gms_llm_for_daily_evidence_refresh(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    class _FakeLlmClient:
        def evaluate(self, log):
            return {
                "tone": "watch",
                "summary": "관심이 빠르게 증가했고 근거 확인이 필요합니다.",
                "subtitle": "시장 사실과 반응 지표를 함께 봅니다.",
            }

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_gms_openai_evaluation_client", lambda **_kwargs: _FakeLlmClient())
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--evidence-use-gms-llm",
            "--evidence-llm-model",
            "gpt-5-mini",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    evidence_step = daily_job.steps[0][1]
    assert evidence_step.llm_evaluator is not None


def test_serve_command_can_attach_similar_windows_jsonl_to_daily_evidence_refresh(monkeypatch, tmp_path):
    captured = {}
    spring_client = _FakeSpringClient()
    similar_windows_path = tmp_path / "similar-windows.json"
    similar_windows_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "sourceTargetId": "region-daejeon",
                        "sourceWindowStart": "2026-06-14T00:00:00Z",
                        "matchedTargetId": "region-gwangju",
                        "similarityScore": 0.91,
                        "evidenceItem": {
                            "evidenceItemId": "similar-region-daejeon-region-gwangju",
                            "evidenceType": "similar_window",
                            "refType": "similar_window",
                            "refId": "snapshot-gwangju-20260301000000",
                            "label": "유사 과거 window",
                            "valueText": "유사도 91.0% · 매매 +6.0%",
                            "severity": "info",
                        },
                    },
                    {
                        "sourceTargetId": "region-busan",
                        "sourceWindowStart": "2026-06-14T00:00:00Z",
                        "matchedTargetId": "region-jeju",
                        "similarityScore": 0.73,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--evidence-similar-windows-jsonl",
            str(similar_windows_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    evidence_step = daily_job.steps[0][1]
    similar_windows = evidence_step.similar_windows_provider(
        "region-daejeon",
        {"targetId": "region-daejeon"},
        {"windowStart": "2026-06-14T00:00:00Z"},
    )
    assert [item["matchedTargetId"] for item in similar_windows] == ["region-gwangju"]


def test_serve_command_can_attach_qdrant_similar_provider_to_daily_evidence_refresh(monkeypatch, tmp_path):
    captured = {}
    spring_client = _FakeSpringClient()
    fake_qdrant = _FakeQdrantClient()
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(json.dumps({"items": [_daily_embedding_item()]}, ensure_ascii=False), encoding="utf-8")

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: fake_qdrant)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--similar-engine",
            "qdrant",
            "--embeddings-jsonl",
            str(embeddings_path),
            "--similar-top-n",
            "1",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    evidence_step = daily_job.steps[0][1]
    similar_windows = evidence_step.similar_windows_provider(
        "region-daejeon",
        {"targetId": "region-daejeon"},
        {
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
        },
    )
    assert [item["matchedTargetId"] for item in similar_windows] == ["region-gwangju"]
    assert similar_windows[0]["evidenceItem"]["evidenceType"] == "similar_window"
    assert fake_qdrant.search_requests == [
        {
            "vector": [0.1, 0.2, 0.3],
            "top_n": 21,
            "exclude_input_id": "reaction-window:region-daejeon:2026-06-14T00:00:00Z:2026-06-14T01:00:00Z",
        }
    ]


def test_serve_command_qdrant_similar_provider_skips_when_collection_is_not_ready(monkeypatch, tmp_path):
    captured = {}
    spring_client = _FakeSpringClient()
    fake_qdrant = _FakeQdrantClient(ready=False)
    embeddings_path = tmp_path / "embeddings.json"
    embeddings_path.write_text(json.dumps({"items": [_daily_embedding_item()]}, ensure_ascii=False), encoding="utf-8")

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "_qdrant_vector_store_client", lambda: fake_qdrant)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-evidence-logs-refresh",
            "--similar-engine",
            "qdrant",
            "--embeddings-jsonl",
            str(embeddings_path),
        ],
    )

    asyncio.run(pipeline_main.async_main())

    evidence_step = captured["kwargs"]["realestate_daily_refresh_job"].steps[0][1]
    assert evidence_step.similar_windows_provider(
        "region-daejeon",
        {"targetId": "region-daejeon"},
        {
            "windowStart": "2026-06-14T00:00:00Z",
            "windowEnd": "2026-06-14T01:00:00Z",
        },
    ) == []
    assert fake_qdrant.search_requests == []


def test_serve_command_can_group_map_layer_refresh_into_daily_refresh(monkeypatch):
    captured = {}
    spring_client = _FakeSpringClient()

    async def fake_serve(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(pipeline_main, "build_pipeline", lambda: _FakePipeline())
    monkeypatch.setattr(pipeline_main, "_spring_client", lambda: spring_client)
    monkeypatch.setattr(pipeline_main, "serve", fake_serve)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "youbuyfirst-pipeline",
            "serve",
            "--enable-realestate-daily-refresh",
            "--enable-realestate-map-layer-refresh",
            "--realestate-map-layer-types",
            "sido",
            "sigungu",
            "--realestate-map-layer-periods",
            "month",
            "halfYear",
        ],
    )

    asyncio.run(pipeline_main.async_main())

    daily_job = captured["kwargs"]["realestate_daily_refresh_job"]
    assert [name for name, _step in daily_job.steps] == ["map_layers"]
    map_step = daily_job.steps[0][1]
    assert map_step.client is spring_client
    assert map_step.layer_types == ("sido", "sigungu")
    assert map_step.periods == ("month", "halfYear")
