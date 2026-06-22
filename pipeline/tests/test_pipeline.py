from dataclasses import asdict
from datetime import datetime, timezone

from youbuyfirst_pipeline.board_stream import BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.models import RawPost
from youbuyfirst_pipeline.pipeline import CommunityPipeline, _watermark_for_adapter


class _NoopClient:
    pass


class _WatermarkClient:
    def get_board_watermark(self, source: str, board_id: str) -> BoardWatermark:
        return BoardWatermark(
            last_seen_external_id=f"{source}-{board_id}-latest",
            cutoff_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )


class _Adapter:
    source = "PPOMPPU"
    target = CrawlTarget.community_board("PPOMPPU", board_id="house", url="https://example.com/house")


def test_enrich_keeps_community_post_fields_without_legacy_analysis_fields():
    post = RawPost(
        source="TEST",
        board_id="house",
        external_id="1",
        url="https://example.com/1",
        title="Seoul rent discussion",
        content="market reaction snippet",
        author="sample",
        published_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        view_count=10,
        recommend_count=2,
        comment_count=3,
    )
    pipeline = CommunityPipeline(adapters=[], client=_NoopClient())

    enriched = pipeline._enrich(post)

    assert asdict(enriched) == asdict(post)
    assert not hasattr(enriched, "mentions")
    assert not hasattr(enriched, "analyses")


def test_watermark_for_adapter_can_ignore_backend_watermark_for_weekly_backfill():
    cutoff_at = datetime(2026, 6, 9, tzinfo=timezone.utc)

    watermark = _watermark_for_adapter(
        _Adapter(),
        _WatermarkClient(),
        default_cutoff_at=cutoff_at,
        ignore_watermark=True,
    )

    assert watermark == BoardWatermark(last_seen_external_id=None, cutoff_at=cutoff_at)


def test_watermark_for_adapter_uses_backend_watermark_by_default():
    cutoff_at = datetime(2026, 6, 9, tzinfo=timezone.utc)

    watermark = _watermark_for_adapter(
        _Adapter(),
        _WatermarkClient(),
        default_cutoff_at=cutoff_at,
    )

    assert watermark == BoardWatermark(
        last_seen_external_id="PPOMPPU-house-latest",
        cutoff_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
