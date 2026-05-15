from datetime import datetime, timezone

from youbuyfirst_pipeline.llm import MockLLMProvider
from youbuyfirst_pipeline.matcher import InstrumentMatcher
from youbuyfirst_pipeline.models import Instrument, RawPost
from youbuyfirst_pipeline.pipeline import CommunityPipeline


class _NoopClient:
    pass


def test_enrich_keeps_only_ai_accepted_mentions_and_analyses():
    post = RawPost(
        source="TEST",
        external_id="1",
        url="https://example.com/1",
        title="애플 먹고 싶고 테슬라 강하다",
        content="사과 이야기는 종목이 아니고 실적 기대",
        author="sample",
        published_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
    )
    matcher = InstrumentMatcher(
        [
            Instrument(market="US", symbol="AAPL", name="Apple", aliases=["애플"]),
            Instrument(market="US", symbol="TSLA", name="Tesla", aliases=["테슬라"]),
        ]
    )
    pipeline = CommunityPipeline(adapters=[], matcher=matcher, llm_provider=MockLLMProvider(), client=_NoopClient())

    enriched = pipeline._enrich(post)

    assert [(mention.market, mention.symbol, mention.matched_text) for mention in enriched.mentions] == [
        ("US", "TSLA", "테슬라")
    ]
    assert [(analysis.market, analysis.symbol, analysis.sentiment) for analysis in enriched.analyses] == [
        ("US", "TSLA", "bullish")
    ]
