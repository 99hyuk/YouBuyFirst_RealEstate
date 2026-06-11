from youbuyfirst_pipeline.crawl_targets import (
    CrawlTarget,
    CrawlTargetKind,
    StockBoardTargetCandidate,
    build_naver_stock_board_targets,
    community_board_registry,
    default_crawl_targets,
    real_estate_community_board_registry,
    real_estate_seed_crawl_targets,
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
        crawl_interval_seconds=900,
    )

    assert target.source == "NAVER"
    assert target.kind == CrawlTargetKind.STOCK_BOARD
    assert target.market == "KR"
    assert target.symbol == "005930"
    assert target.target_id == "NAVER:KR:005930"
    assert target.priority == 10
    assert target.label == "Samsung board"
    assert target.crawl_interval_seconds == 900


def test_default_crawl_targets_prioritize_watchlist_before_core_stock_board_targets():
    instruments = [
        Instrument(market="KR", symbol="005930", name="Samsung", aliases=[]),
        Instrument(market="KR", symbol="000660", name="SK Hynix", aliases=[]),
        Instrument(market="US", symbol="AAPL", name="Apple", aliases=[]),
    ]

    targets = default_crawl_targets(
        instruments,
        naver_watchlist_codes=["000660", "005930.KS", "005930"],
        stock_board_target_limit=5,
        fmkorea_url="https://example.com/stock",
    )

    stock_targets = [target for target in targets if target.kind == CrawlTargetKind.STOCK_BOARD]
    assert [target.target_id for target in stock_targets] == [
        "NAVER:KR:000660",
        "NAVER:KR:005930",
        "NAVER:KR:069500",
        "NAVER:KR:454910",
        "NAVER:KR:035420",
    ]
    assert [target.priority for target in stock_targets] == [80, 80, 120, 120, 120]
    assert [target.crawl_interval_seconds for target in stock_targets] == [1800, 1800, 3600, 3600, 3600]

    latest_targets = [target for target in targets if target.kind == CrawlTargetKind.COMMUNITY_BOARD]
    assert latest_targets[0].url == "https://example.com/stock"
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


def test_real_estate_community_registry_keeps_p0_candidates_out_of_default_crawl():
    registry = real_estate_community_board_registry()

    assert [(entry.source, entry.board_id, entry.enabled_by_default) for entry in registry] == [
        ("PPOMPPU", "house", False),
        ("DCINSIDE", "immovables", False),
    ]
    assert registry[0].latest_url == "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1"
    assert registry[1].latest_url == "https://gall.dcinside.com/board/lists/?id=immovables"
    assert {entry.crawl_policy for entry in registry} == {"realestate-general-board-latest"}

    default_targets = default_crawl_targets([], stock_board_target_limit=0)

    assert "PPOMPPU:house" not in [target.target_id for target in default_targets]
    assert "DCINSIDE:immovables" not in [target.target_id for target in default_targets]


def test_real_estate_seed_crawl_targets_can_create_existing_board_adapters():
    targets = real_estate_seed_crawl_targets()
    fetcher = BrowserCapableFetcher(user_agent="test")

    adapters = _adapters_from_targets(targets, fetcher)

    assert [target.target_id for target in targets] == ["PPOMPPU:house", "DCINSIDE:immovables"]
    assert [target.kind for target in targets] == [CrawlTargetKind.COMMUNITY_BOARD, CrawlTargetKind.COMMUNITY_BOARD]
    assert [target.crawl_interval_seconds for target in targets] == [3600, 3600]
    assert [adapter.source for adapter in adapters] == ["PPOMPPU", "DCINSIDE"]


def test_default_crawl_targets_do_not_expand_to_all_kr_instruments_when_watchlist_is_empty():
    instruments = [
        Instrument(market="KR", symbol="005930", name="Samsung", aliases=[]),
        Instrument(market="KR", symbol="999999", name="Not in curated target list", aliases=[]),
        Instrument(market="US", symbol="AAPL", name="Apple", aliases=[]),
    ]

    targets = default_crawl_targets(instruments, stock_board_target_limit=3)

    stock_targets = [target for target in targets if target.kind == CrawlTargetKind.STOCK_BOARD]
    assert [target.target_id for target in stock_targets] == [
        "NAVER:KR:005930",
        "NAVER:KR:000660",
        "NAVER:KR:069500",
    ]
    assert "NAVER:KR:999999" not in [target.target_id for target in targets]
    assert [target for target in targets if target.target_id == "FMKOREA:community-board"][0].url == "https://www.fmkorea.com/stock"


def test_default_crawl_targets_falls_back_to_legacy_codes_when_watchlist_is_empty():
    targets = default_crawl_targets(
        [],
        naver_stock_codes=["000660"],
        naver_watchlist_codes=[],
        stock_board_target_limit=2,
    )

    stock_targets = [target for target in targets if target.kind == CrawlTargetKind.STOCK_BOARD]
    assert [target.target_id for target in stock_targets] == [
        "NAVER:KR:000660",
        "NAVER:KR:005930",
    ]
    assert stock_targets[0].priority == 80


def test_naver_stock_board_target_limit_is_capped_to_thirty():
    configured_codes = [f"{index:06d}" for index in range(1, 45)]

    targets = build_naver_stock_board_targets(
        watchlist_symbols=configured_codes,
        max_targets=99,
    )

    assert len(targets) == 30
    assert targets[0].target_id == "NAVER:KR:000001"
    assert targets[-1].target_id == "NAVER:KR:000030"


def test_naver_stock_board_builder_accepts_future_signal_candidates():
    targets = build_naver_stock_board_targets(
        extra_candidates=[
            StockBoardTargetCandidate(
                symbol="123456",
                reason="surging-mention",
                priority=60,
                crawl_interval_seconds=900,
                label="Surging mention sample",
            )
        ],
        max_targets=1,
    )

    assert len(targets) == 1
    assert targets[0].target_id == "NAVER:KR:123456"
    assert targets[0].priority == 60
    assert targets[0].crawl_interval_seconds == 900
    assert targets[0].label == "Surging mention sample"


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


def test_adapters_use_browser_fetch_for_fmkorea_by_default():
    fetcher = BrowserCapableFetcher(user_agent="test")
    target = CrawlTarget.community_board("FMKOREA", board_id="stock", url="https://example.com/stock")

    adapters = _adapters_from_targets([target], fetcher)

    assert adapters[0].source == "FMKOREA"
    assert adapters[0].use_local_browser_fetch is True


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
