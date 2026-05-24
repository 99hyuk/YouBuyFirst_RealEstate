from youbuyfirst_pipeline.crawl_targets import (
    CrawlTarget,
    CrawlTargetKind,
    community_board_registry,
    default_crawl_targets,
)
from youbuyfirst_pipeline import main
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
        "DCINSIDE:nyse",
        "DCINSIDE:neostock",
        "DCINSIDE:koreastock",
        "PPOMPPU:stock",
        "DCINSIDE:nyse:diffusion:concept",
        "DCINSIDE:neostock:diffusion:concept",
        "DCINSIDE:koreastock:diffusion:concept",
    ]
    assert targets[0].kind == CrawlTargetKind.STOCK_BOARD
    assert targets[2].kind == CrawlTargetKind.COMMUNITY_BOARD
    assert targets[2].url == "https://example.com/stock"
    latest_targets = [target for target in targets[2:] if target.kind == CrawlTargetKind.COMMUNITY_BOARD]
    assert [(target.source, target.board_id) for target in latest_targets] == [
        ("FMKOREA", "stock"),
        ("DCINSIDE", "nyse"),
        ("DCINSIDE", "neostock"),
        ("DCINSIDE", "koreastock"),
        ("PPOMPPU", "stock"),
    ]
    diffusion_targets = [target for target in targets if target.kind == CrawlTargetKind.GENERAL_BOARD_DIFFUSION]
    assert [(target.board_id, target.diffusion_type, target.url) for target in diffusion_targets] == [
        ("nyse", "concept", "https://gall.dcinside.com/mini/board/lists/?id=nyse&exception_mode=recommend"),
        ("neostock", "concept", "https://gall.dcinside.com/board/lists/?id=neostock&exception_mode=recommend"),
        ("koreastock", "concept", "https://gall.dcinside.com/mini/board/lists/?id=koreastock&exception_mode=recommend"),
    ]
    assert [target.priority for target in diffusion_targets] == [260, 270, 280]


def test_community_board_registry_keeps_disabled_diffusion_candidates_out_of_default_targets():
    registry = community_board_registry(fmkorea_url="https://example.com/stock")

    assert [entry.board_id for entry in registry] == ["stock", "nyse", "neostock", "koreastock", "stock"]
    assert [(entry.source, entry.display_name, entry.market_scope) for entry in registry] == [
        ("FMKOREA", "FMKOREA stock board", "KR_US"),
        ("DCINSIDE", "DCInside US stock gallery", "US"),
        ("DCINSIDE", "DCInside stock gallery", "KR_GENERAL"),
        ("DCINSIDE", "DCInside domestic stock gallery", "KR"),
        ("PPOMPPU", "PPOMPPU stock forum", "KR_US"),
    ]
    assert registry[0].latest_url == "https://example.com/stock"
    assert registry[0].diffusion_boards[0].diffusion_type == "popular"
    assert registry[0].diffusion_boards[0].enabled_by_default is False
    assert registry[-1].diffusion_boards[0].diffusion_type == "popular"
    assert registry[-1].diffusion_boards[0].enabled_by_default is False


def test_community_diffusion_target_builds_separate_target_identity():
    target = CrawlTarget.community_diffusion_board(
        "dcinside",
        board_id="stockus",
        diffusion_type="Concept",
        url="https://example.com/concept",
        priority=215,
    )

    assert target.source == "DCINSIDE"
    assert target.kind == CrawlTargetKind.GENERAL_BOARD_DIFFUSION
    assert target.target_id == "DCINSIDE:stockus:diffusion:concept"
    assert target.board_id == "stockus"
    assert target.diffusion_type == "concept"
    assert target.url == "https://example.com/concept"
    assert target.priority == 215


def test_default_crawl_targets_use_all_kr_instruments_when_codes_are_not_configured():
    instruments = [
        Instrument(market="KR", symbol="005930", name="Samsung", aliases=[]),
        Instrument(market="US", symbol="AAPL", name="Apple", aliases=[]),
    ]

    targets = default_crawl_targets(instruments)

    assert [target.target_id for target in targets] == [
        "NAVER:KR:005930",
        "FMKOREA:community-board",
        "DCINSIDE:nyse",
        "DCINSIDE:neostock",
        "DCINSIDE:koreastock",
        "PPOMPPU:stock",
        "DCINSIDE:nyse:diffusion:concept",
        "DCINSIDE:neostock:diffusion:concept",
        "DCINSIDE:koreastock:diffusion:concept",
    ]
    assert targets[1].url == "https://www.fmkorea.com/stock"


def test_adapters_are_created_from_targets_with_target_metadata():
    fetcher = BrowserCapableFetcher(user_agent="test")
    targets = [
        CrawlTarget.stock_board("NAVER", market="KR", symbol="005930"),
        CrawlTarget.community_board("FMKOREA", board_id="stock", url="https://example.com/stock"),
        CrawlTarget.community_diffusion_board("DCINSIDE", board_id="nyse", diffusion_type="concept", url="https://example.com/concept"),
        CrawlTarget.community_board("DCINSIDE", board_id="nyse", url="https://example.com/dc"),
        CrawlTarget.community_board("PPOMPPU", board_id="stock", url="https://example.com/ppomppu"),
    ]

    adapters = _adapters_from_targets(targets, fetcher)

    assert [adapter.source for adapter in adapters] == ["NAVER", "FMKOREA", "DCINSIDE", "DCINSIDE", "PPOMPPU"]
    assert [adapter.target.target_id for adapter in adapters] == [
        "NAVER:KR:005930",
        "FMKOREA:community-board",
        "DCINSIDE:nyse:diffusion:concept",
        "DCINSIDE:nyse",
        "PPOMPPU:stock",
    ]


def test_stream_crawler_from_env_configures_limits_and_page_delay(monkeypatch):
    monkeypatch.setenv("CRAWLER_MAX_PAGES_PER_RUN", "7")
    monkeypatch.setenv("CRAWLER_MAX_POSTS_PER_RUN", "120")
    monkeypatch.setenv("CRAWLER_PAGE_DELAY_MIN_SECONDS", "1.25")
    monkeypatch.setenv("CRAWLER_PAGE_DELAY_MAX_SECONDS", "3.5")

    factory = getattr(main, "_stream_crawler_from_env", None)
    assert factory is not None

    crawler = factory()

    assert crawler.max_pages_per_run == 7
    assert crawler.max_posts_per_run == 120
    assert crawler.page_delay_min_seconds == 1.25
    assert crawler.page_delay_max_seconds == 3.5
