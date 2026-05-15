from youbuyfirst_pipeline.crawl_targets import CrawlTarget, CrawlTargetKind, default_crawl_targets
from youbuyfirst_pipeline.main import _adapters_from_targets
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher
from youbuyfirst_pipeline.models import Instrument


def test_stock_board_target_normalizes_source_and_builds_stable_id():
    target = CrawlTarget.stock_board(
        source="naver",
        market="kr",
        symbol="005930",
        priority=10,
        label="Samsung board",
    )

    assert target.source == "NAVER"
    assert target.kind == CrawlTargetKind.STOCK_BOARD
    assert target.market == "KR"
    assert target.symbol == "005930"
    assert target.target_id == "NAVER:KR:005930"
    assert target.priority == 10
    assert target.label == "Samsung board"


def test_default_crawl_targets_use_selected_naver_codes_and_fmkorea_board():
    instruments = [
        Instrument(market="KR", symbol="005930", name="Samsung", aliases=[]),
        Instrument(market="KR", symbol="000660", name="SK Hynix", aliases=[]),
        Instrument(market="US", symbol="AAPL", name="Apple", aliases=[]),
    ]

    targets = default_crawl_targets(
        instruments,
        naver_stock_codes=["005930", "005930", "000660"],
        fmkorea_url="https://example.com/stock",
    )

    assert [target.target_id for target in targets] == [
        "NAVER:KR:005930",
        "NAVER:KR:000660",
        "FMKOREA:community-board",
    ]
    assert targets[0].kind == CrawlTargetKind.STOCK_BOARD
    assert targets[2].kind == CrawlTargetKind.COMMUNITY_BOARD
    assert targets[2].url == "https://example.com/stock"


def test_default_crawl_targets_use_all_kr_instruments_when_codes_are_not_configured():
    instruments = [
        Instrument(market="KR", symbol="005930", name="Samsung", aliases=[]),
        Instrument(market="US", symbol="AAPL", name="Apple", aliases=[]),
    ]

    targets = default_crawl_targets(instruments)

    assert [target.target_id for target in targets] == [
        "NAVER:KR:005930",
        "FMKOREA:community-board",
    ]
    assert targets[1].url == "https://www.fmkorea.com/stock"


def test_adapters_are_created_from_targets_with_target_metadata():
    fetcher = BrowserCapableFetcher(user_agent="test")
    targets = [
        CrawlTarget.stock_board("NAVER", market="KR", symbol="005930"),
        CrawlTarget.community_board("FMKOREA", url="https://example.com/stock"),
    ]

    adapters = _adapters_from_targets(targets, fetcher)

    assert [adapter.source for adapter in adapters] == ["NAVER", "FMKOREA"]
    assert [adapter.target.target_id for adapter in adapters] == [
        "NAVER:KR:005930",
        "FMKOREA:community-board",
    ]
