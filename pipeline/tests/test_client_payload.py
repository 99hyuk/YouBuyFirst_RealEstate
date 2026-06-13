import json
from datetime import datetime, timezone

import httpx
import respx

from youbuyfirst_pipeline.board_stream import BoardWatermark
from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.models import CommentCollectionTarget, DiffusionEvent, EnrichedPost


def test_post_payload_includes_board_and_engagement_counts_without_legacy_analysis_fields():
    post = EnrichedPost(
        source="PPOMPPU",
        board_id="house",
        external_id="PPOMPPU-house-359353",
        url="https://m.ppomppu.co.kr/new/bbs_view.php?id=house&no=359353",
        title="Seoul rent discussion",
        content="limited snippet",
        author="sample",
        published_at=datetime(2026, 5, 24, 0, 57, tzinfo=timezone.utc),
        view_count=1788,
        recommend_count=8,
        comment_count=19,
    )

    payload = SpringIngestionClient._post_payload(post)

    assert payload == {
        "externalId": "PPOMPPU-house-359353",
        "boardId": "house",
        "url": "https://m.ppomppu.co.kr/new/bbs_view.php?id=house&no=359353",
        "title": "Seoul rent discussion",
        "contentSnippet": "limited snippet",
        "authorDisplayName": "sample",
        "publishedAt": "2026-05-24T00:57:00Z",
        "viewCount": 1788,
        "recommendCount": 8,
        "commentCount": 19,
    }
    assert "mentions" not in payload
    assert "senti" + "ments" not in payload


@respx.mock
def test_ingest_sends_diffusion_events_as_separate_layer():
    route = respx.post("http://backend/internal/ingestions/community-posts").mock(
        return_value=httpx.Response(
            200,
            json={"source": "DCINSIDE", "runId": "run-1", "seenPosts": 1, "acceptedPosts": 1, "duplicatePosts": 0},
        )
    )
    post = EnrichedPost(
        source="DCINSIDE",
        board_id="immovables",
        external_id="DCINSIDE-immovables-777",
        url="https://gall.dcinside.com/board/view/?id=immovables&no=777",
        title="regional heat thread",
        content="limited snippet",
        author="sample",
        published_at=datetime(2026, 5, 24, 0, 58, tzinfo=timezone.utc),
        view_count=2300,
        recommend_count=41,
        comment_count=86,
    )
    event = DiffusionEvent(
        external_id="DCINSIDE-immovables-777",
        board_id="immovables",
        diffusion_type="concept",
        list_position=1,
        observed_at=datetime(2026, 5, 24, 1, 1, tzinfo=timezone.utc),
        view_count=2300,
        recommend_count=41,
        comment_count=86,
        diffusion_only=False,
    )

    SpringIngestionClient("http://backend").ingest(
        "DCINSIDE",
        "run-1",
        datetime(2026, 5, 24, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 5, 24, 1, 2, tzinfo=timezone.utc),
        [post],
        diffusion_events=[event],
    )

    payload = json.loads(route.calls.last.request.content)
    assert not any(key == "alias" + "Candidates" for key in payload)
    assert payload["diffusionEvents"] == [
        {
            "externalId": "DCINSIDE-immovables-777",
            "boardId": "immovables",
            "diffusionType": "concept",
            "listPosition": 1,
            "observedAt": "2026-05-24T01:01:00Z",
            "viewCount": 2300,
            "recommendCount": 41,
            "commentCount": 86,
            "diffusionOnly": False,
        }
    ]


@respx.mock
def test_ingest_sends_comment_collection_targets_as_limited_queue():
    route = respx.post("http://backend/internal/ingestions/community-posts").mock(
        return_value=httpx.Response(
            200,
            json={"source": "DCINSIDE", "runId": "run-1", "seenPosts": 0, "acceptedPosts": 0, "duplicatePosts": 0},
        )
    )
    target = CommentCollectionTarget(
        external_id="DCINSIDE-immovables-777",
        board_id="immovables",
        trigger_reason="diffusion",
        triggered_at=datetime(2026, 5, 24, 1, 1, tzinfo=timezone.utc),
        max_comments=50,
        priority=50,
        view_count=2300,
        recommend_count=41,
        comment_count=86,
    )

    SpringIngestionClient("http://backend").ingest(
        "DCINSIDE",
        "run-1",
        datetime(2026, 5, 24, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 5, 24, 1, 2, tzinfo=timezone.utc),
        [],
        comment_collection_targets=[target],
    )

    payload = json.loads(route.calls.last.request.content)
    assert payload["commentCollectionTargets"] == [
        {
            "externalId": "DCINSIDE-immovables-777",
            "boardId": "immovables",
            "triggerReason": "diffusion",
            "triggeredAt": "2026-05-24T01:01:00Z",
            "maxComments": 50,
            "priority": 50,
            "viewCount": 2300,
            "recommendCount": 41,
            "commentCount": 86,
        }
    ]


@respx.mock
def test_client_reads_board_watermark_from_backend():
    respx.get("http://backend/internal/crawl-watermarks").mock(
        return_value=httpx.Response(
            200,
            json={
                "source": "PPOMPPU",
                "boardId": "house",
                "lastSeenExternalId": "PPOMPPU-house-100",
                "lastSeenPublishedAt": "2026-05-24T02:00:00Z",
            },
        )
    )

    watermark = SpringIngestionClient("http://backend").get_board_watermark("PPOMPPU", "house")

    assert watermark == BoardWatermark(
        last_seen_external_id="PPOMPPU-house-100",
        cutoff_at=datetime(2026, 5, 24, 2, 0, tzinfo=timezone.utc),
    )


@respx.mock
def test_client_returns_none_when_backend_has_no_watermark():
    respx.get("http://backend/internal/crawl-watermarks").mock(return_value=httpx.Response(204))

    watermark = SpringIngestionClient("http://backend").get_board_watermark("PPOMPPU", "house")

    assert watermark is None
