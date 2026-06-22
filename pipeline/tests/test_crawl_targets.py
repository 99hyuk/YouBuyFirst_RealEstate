from youbuyfirst_pipeline import main
from youbuyfirst_pipeline.crawl_targets import (
    CrawlTarget,
    CrawlTargetKind,
    real_estate_community_board_registry,
    real_estate_seed_crawl_targets,
)
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher
from youbuyfirst_pipeline.main import _adapters_from_targets


def test_community_board_target_normalizes_source_and_builds_stable_id():
    target = CrawlTarget.community_board(
        source="ppomppu",
        board_id="house",
        url="https://example.com/house",
        priority=10,
        label="real estate forum",
        crawl_interval_seconds=900,
    )

    assert target.source == "PPOMPPU"
    assert target.kind == CrawlTargetKind.COMMUNITY_BOARD
    assert target.target_id == "PPOMPPU:house"
    assert target.board_id == "house"
    assert target.url == "https://example.com/house"
    assert target.priority == 10
    assert target.label == "real estate forum"
    assert target.crawl_interval_seconds == 900


def test_community_diffusion_target_builds_separate_target_identity():
    target = CrawlTarget.community_diffusion_board(
        "dcinside",
        board_id="immovables",
        diffusion_type="Concept",
        url="https://example.com/concept",
        priority=215,
    )

    assert target.source == "DCINSIDE"
    assert target.kind == CrawlTargetKind.GENERAL_BOARD_DIFFUSION
    assert target.target_id == "DCINSIDE:immovables:diffusion:concept"
    assert target.board_id == "immovables"
    assert target.diffusion_type == "concept"
    assert target.url == "https://example.com/concept"
    assert target.priority == 215


def test_real_estate_community_registry_contains_only_real_estate_boards():
    registry = real_estate_community_board_registry()
    identities = [(entry.source, entry.board_id, entry.enabled_by_default) for entry in registry]

    assert identities == [
        ("PPOMPPU", "house", False),
        ("DCINSIDE", "immovables", False),
        ("FMKOREA", "realestate", False),
        ("NAVER_CAFE", "public_search", False),
        ("DAUM_CAFE", "public_search", False),
        ("CLIEN", "park", False),
        ("COOK82", "freeboard", False),
        ("DEALAGORA", "community", False),
        ("THEQOO", "square", False),
        ("MLBPARK", "bullpen", False),
        ("NATEPANN", "talk", False),
        ("TODAYHUMOR", "economy", False),
        ("TODAYHUMOR", "freeboard", False),
        ("RULIWEB", "community", False),
        ("BOBAEDREAM", "freeb", False),
        ("INSTIZ", "name", False),
        ("SLRCLUB", "free", False),
        ("INVEN", "webzine2097", False),
    ]
    assert len(registry) >= 17
    assert registry[0].latest_url == "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1"
    assert registry[1].latest_url == "https://gall.dcinside.com/board/lists/?id=immovables"
    assert registry[3].crawl_policy == "realestate-cafe-public-search"
    assert registry[4].crawl_policy == "realestate-cafe-public-search"
    assert {entry.crawl_policy for entry in registry} == {
        "realestate-general-board-latest",
        "realestate-cafe-public-search",
    }
    assert {entry.domain_scope for entry in registry} == {"KR_REALESTATE"}


def test_real_estate_seed_crawl_targets_can_create_existing_board_adapters():
    targets = real_estate_seed_crawl_targets()
    fetcher = BrowserCapableFetcher(user_agent="test")

    adapters = _adapters_from_targets(targets, fetcher)

    assert [target.target_id for target in targets] == [
        "PPOMPPU:house",
        "DCINSIDE:immovables",
        "FMKOREA:realestate",
        "NAVER_CAFE:public_search",
        "DAUM_CAFE:public_search",
        "CLIEN:park",
        "COOK82:freeboard",
        "DEALAGORA:community",
        "THEQOO:square",
        "MLBPARK:bullpen",
        "NATEPANN:talk",
        "TODAYHUMOR:economy",
        "TODAYHUMOR:freeboard",
        "RULIWEB:community",
        "BOBAEDREAM:freeb",
        "INSTIZ:name",
        "SLRCLUB:free",
        "INVEN:webzine2097",
    ]
    assert {target.kind for target in targets} == {CrawlTargetKind.COMMUNITY_BOARD}
    assert [target.crawl_interval_seconds for target in targets] == [3600] * len(targets)
    assert [adapter.source for adapter in adapters] == [target.source for target in targets]


def test_adapters_are_created_from_real_estate_community_targets():
    fetcher = BrowserCapableFetcher(user_agent="test")
    targets = [
        CrawlTarget.community_board("FMKOREA", board_id="realestate", url="https://example.com/realestate"),
        CrawlTarget.community_diffusion_board(
            "DCINSIDE",
            board_id="immovables",
            diffusion_type="concept",
            url="https://example.com/concept",
        ),
        CrawlTarget.community_board("DCINSIDE", board_id="immovables", url="https://example.com/dc"),
        CrawlTarget.community_board("PPOMPPU", board_id="house", url="https://example.com/ppomppu"),
    ]

    adapters = _adapters_from_targets(targets, fetcher)

    assert [adapter.source for adapter in adapters] == ["FMKOREA", "DCINSIDE", "DCINSIDE", "PPOMPPU"]
    assert [adapter.target.target_id for adapter in adapters] == [
        "FMKOREA:realestate",
        "DCINSIDE:immovables:diffusion:concept",
        "DCINSIDE:immovables",
        "PPOMPPU:house",
    ]


def test_adapters_use_http_fetch_for_fmkorea_by_default():
    fetcher = BrowserCapableFetcher(user_agent="test")
    target = CrawlTarget.community_board("FMKOREA", board_id="realestate", url="https://example.com/realestate")

    adapters = _adapters_from_targets([target], fetcher)

    assert adapters[0].source == "FMKOREA"
    assert adapters[0].use_local_browser_fetch is False


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
