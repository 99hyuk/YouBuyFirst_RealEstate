from dataclasses import asdict
from datetime import datetime, timezone

from youbuyfirst_pipeline.models import RawPost
from youbuyfirst_pipeline.pipeline import CommunityPipeline


class _NoopClient:
    pass


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
