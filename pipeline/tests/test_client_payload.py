import json
from datetime import datetime, timezone

import httpx
import respx

from youbuyfirst_pipeline.board_stream import BoardWatermark
from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.models import Analysis, AliasCandidate, CommentCollectionTarget, DiffusionEvent, EnrichedPost, Mention


def test_post_payload_includes_board_and_engagement_counts():
    post = EnrichedPost(
        source="PPOMPPU",
        board_id="stock",
        external_id="PPOMPPU-stock-359353",
        url="https://www.ppomppu.co.kr/zboard/view.php?id=stock&no=359353",
        title="Samsung union update",
        content="limited snippet",
        author="sample",
        published_at=datetime(2026, 5, 24, 0, 57, tzinfo=timezone.utc),
        view_count=1788,
        recommend_count=8,
        comment_count=19,
    )

    payload = SpringIngestionClient._post_payload(post)

    assert payload["boardId"] == "stock"
    assert payload["viewCount"] == 1788
    assert payload["recommendCount"] == 8
    assert payload["commentCount"] == 19


def test_post_payload_includes_instrument_ids_for_mentions_and_sentiments():
    post = EnrichedPost(
        source="FMKOREA",
        board_id="stock",
        external_id="fmk-107",
        url="https://www.fmkorea.com/stock/107",
        title="테슬라 강세",
        content="테슬라 실적 기대",
        author="sample",
        published_at=datetime(2026, 5, 27, 0, 57, tzinfo=timezone.utc),
        mentions=[Mention(instrument_id=7, market="US", symbol="TSLA", matched_text="테슬라")],
        analyses=[
            Analysis(
                instrument_id=7,
                market="US",
                symbol="TSLA",
                sentiment="bullish",
                confidence=0.8,
                rationale="실적 기대",
                model="mock",
            )
        ],
    )

    payload = SpringIngestionClient._post_payload(post)

    assert payload["mentions"] == [
        {
            "instrumentId": 7,
            "market": "US",
            "symbol": "TSLA",
            "matchedText": "테슬라",
        }
    ]
    assert payload["sentiments"] == [
        {
            "instrumentId": 7,
            "market": "US",
            "symbol": "TSLA",
            "sentiment": "bullish",
            "confidence": 0.8,
            "rationale": "실적 기대",
            "model": "mock",
        }
    ]


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
        board_id="stockus",
        external_id="dc-us-777",
        url="https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=777",
        title="NVDA concept thread",
        content="limited snippet",
        author="sample",
        published_at=datetime(2026, 5, 24, 0, 58, tzinfo=timezone.utc),
        view_count=2300,
        recommend_count=41,
        comment_count=86,
    )
    event = DiffusionEvent(
        external_id="dc-us-777",
        board_id="stockus",
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
    assert payload["diffusionEvents"] == [
        {
            "externalId": "dc-us-777",
            "boardId": "stockus",
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
def test_ingest_sends_alias_candidates_as_review_queue():
    route = respx.post("http://backend/internal/ingestions/community-posts").mock(
        return_value=httpx.Response(
            200,
            json={"source": "DCINSIDE", "runId": "run-1", "seenPosts": 1, "acceptedPosts": 1, "duplicatePosts": 0},
        )
    )
    post = EnrichedPost(
        source="DCINSIDE",
        external_id="dc-us-888",
        board_id="stockus",
        url="https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=888",
        title="슬라 오늘 언급 많음",
        content="슬라 실적 기대감",
        author="dc-user",
        published_at=datetime(2026, 5, 25, 1, 0, tzinfo=timezone.utc),
        alias_candidates=[
            AliasCandidate(
                alias="슬라",
                suggested_market="US",
                suggested_symbol="TSLA",
                reason="review-alias",
                context_snippet="슬라 오늘 언급 많음",
                sample_url="https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=888",
                observed_at=datetime(2026, 5, 25, 1, 0, tzinfo=timezone.utc),
            )
        ],
    )

    SpringIngestionClient("http://backend").ingest(
        "DCINSIDE",
        "run-1",
        datetime(2026, 5, 25, 1, 0, tzinfo=timezone.utc),
        datetime(2026, 5, 25, 1, 2, tzinfo=timezone.utc),
        [post],
    )

    payload = json.loads(route.calls.last.request.content)
    assert payload["aliasCandidates"] == [
        {
            "alias": "슬라",
            "suggestedMarket": "US",
            "suggestedSymbol": "TSLA",
            "reason": "review-alias",
            "contextSnippet": "슬라 오늘 언급 많음",
            "sampleUrl": "https://gall.dcinside.com/mgallery/board/view/?id=stockus&no=888",
            "observedAt": "2026-05-25T01:00:00Z",
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
        external_id="dc-us-777",
        board_id="stockus",
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
            "externalId": "dc-us-777",
            "boardId": "stockus",
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
                "source": "FMKOREA",
                "boardId": "stock",
                "lastSeenExternalId": "FMKOREA-100",
                "lastSeenPublishedAt": "2026-05-24T02:00:00Z",
            },
        )
    )

    watermark = SpringIngestionClient("http://backend").get_board_watermark("FMKOREA", "stock")

    assert watermark == BoardWatermark(
        last_seen_external_id="FMKOREA-100",
        cutoff_at=datetime(2026, 5, 24, 2, 0, tzinfo=timezone.utc),
    )


@respx.mock
def test_client_returns_none_when_backend_has_no_watermark():
    respx.get("http://backend/internal/crawl-watermarks").mock(return_value=httpx.Response(204))

    watermark = SpringIngestionClient("http://backend").get_board_watermark("FMKOREA", "stock")

    assert watermark is None
