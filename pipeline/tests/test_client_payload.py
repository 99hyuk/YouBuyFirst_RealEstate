from datetime import datetime, timezone

import httpx
import respx

from youbuyfirst_pipeline.board_stream import BoardWatermark
from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.models import EnrichedPost


def test_post_payload_includes_board_and_engagement_counts():
    post = EnrichedPost(
        source="PPOMPPU",
        board_id="stock",
        external_id="PPOMPPU-stock-359353",
        url="https://www.ppomppu.co.kr/zboard/view.php?id=stock&no=359353",
        title="삼성전자 노조 여전함",
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

    assert watermark == BoardWatermark(last_seen_external_id="FMKOREA-100")


@respx.mock
def test_client_returns_none_when_backend_has_no_watermark():
    respx.get("http://backend/internal/crawl-watermarks").mock(return_value=httpx.Response(204))

    watermark = SpringIngestionClient("http://backend").get_board_watermark("FMKOREA", "stock")

    assert watermark is None
