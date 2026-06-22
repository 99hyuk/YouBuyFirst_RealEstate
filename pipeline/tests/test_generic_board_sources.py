import pytest

from youbuyfirst_pipeline.board_stream import BoardStreamCrawler
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import FetchResult
from youbuyfirst_pipeline.crawlers.generic_board import GenericLinkBoardAdapter


class FakeFetcher:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.urls: list[str] = []

    async def fetch_html(self, url: str, allow_browser_fallback: bool = True) -> FetchResult:
        self.urls.append(url)
        return FetchResult(url=url, html=self.pages[url], status_code=200)


@pytest.mark.parametrize(
    ("source", "board_id", "base_url", "href", "expected_id", "expected_url"),
    [
        (
            "DEALAGORA",
            "community",
            "https://dealagora.co.kr/subpage/bbs/borad.php?cate=&code=community&order=new",
            "./view.php?code=community&idx=926&cate=",
            "DEALAGORA-community-926",
            "https://dealagora.co.kr/subpage/bbs/view.php?code=community&idx=926&cate=",
        ),
        (
            "THEQOO",
            "square",
            "https://theqoo.net/square",
            "/square/3516074637",
            "THEQOO-square-3516074637",
            "https://theqoo.net/square/3516074637",
        ),
        (
            "MLBPARK",
            "bullpen",
            "https://mlbpark.donga.com/mp/b.php?m=list&b=bullpen",
            "https://mlbpark.donga.com/mp/b.php?m=view&b=bullpen&id=2026061700001",
            "MLBPARK-bullpen-2026061700001",
            "https://mlbpark.donga.com/mp/b.php?m=view&b=bullpen&id=2026061700001",
        ),
        (
            "NATEPANN",
            "talk",
            "https://pann.nate.com/talk/c20002",
            "/talk/375468260",
            "NATEPANN-talk-375468260",
            "https://pann.nate.com/talk/375468260",
        ),
        (
            "TODAYHUMOR",
            "economy",
            "https://www.todayhumor.co.kr/board/list.php?table=economy",
            "/board/view.php?table=economy&no=33000&s_no=33000&page=1",
            "TODAYHUMOR-economy-33000",
            "https://www.todayhumor.co.kr/board/view.php?table=economy&no=33000&s_no=33000&page=1",
        ),
        (
            "RULIWEB",
            "community",
            "https://bbs.ruliweb.com/community/board/300143",
            "https://bbs.ruliweb.com/community/board/300143/read/75600588",
            "RULIWEB-community-75600588",
            "https://bbs.ruliweb.com/community/board/300143/read/75600588",
        ),
        (
            "BOBAEDREAM",
            "freeb",
            "https://www.bobaedream.co.kr/list?code=freeb",
            "/view?code=freeb&No=3411271&bm=1",
            "BOBAEDREAM-freeb-3411271",
            "https://www.bobaedream.co.kr/view?code=freeb&No=3411271&bm=1",
        ),
        (
            "INSTIZ",
            "name",
            "https://www.instiz.net/name",
            "https://www.instiz.net/name/66738382?page=1&category=1",
            "INSTIZ-name-66738382",
            "https://www.instiz.net/name/66738382?page=1&category=1",
        ),
        (
            "SLRCLUB",
            "free",
            "https://www.slrclub.com/bbs/zboard.php?id=free",
            "/bbs/vx2.php?id=free&no=41657896",
            "SLRCLUB-free-41657896",
            "https://www.slrclub.com/bbs/vx2.php?id=free&no=41657896",
        ),
        (
            "INVEN",
            "webzine2097",
            "https://www.inven.co.kr/board/webzine/2097",
            "https://www.inven.co.kr/board/webzine/2097/2681859",
            "INVEN-webzine2097-2681859",
            "https://www.inven.co.kr/board/webzine/2097/2681859",
        ),
    ],
)
def test_expanded_generic_board_sources_parse_public_post_links(
    source: str,
    board_id: str,
    base_url: str,
    href: str,
    expected_id: str,
    expected_url: str,
):
    html = f"""
    <ul>
      <li><a href="{href}">Gangnam apartment jeonse anxiety</a><span>2026-06-17 09:30</span></li>
    </ul>
    """

    posts = GenericLinkBoardAdapter.parse_list_html(html, source=source, board_id=board_id, base_url=base_url)

    assert len(posts) == 1
    assert posts[0].external_id == expected_id
    assert posts[0].url == expected_url
    assert posts[0].title == "Gangnam apartment jeonse anxiety"


def test_generic_keyword_boards_filter_unrelated_titles():
    html = '<a href="/square/3516074637">daily lunch thread</a>'

    posts = GenericLinkBoardAdapter.parse_list_html(
        html,
        source="THEQOO",
        board_id="square",
        base_url="https://theqoo.net/square",
    )

    assert posts == []


def test_generic_boards_filter_ad_and_recruiting_titles():
    html = '<a href="./view.php?code=community&idx=926&cate=">hiring apartment marketer</a>'

    posts = GenericLinkBoardAdapter.parse_list_html(
        html,
        source="DEALAGORA",
        board_id="community",
        base_url="https://dealagora.co.kr/subpage/bbs/borad.php?cate=&code=community&order=new",
    )

    assert posts == []


@pytest.mark.anyio
async def test_generic_fetch_stream_reports_filtered_candidate_counts():
    html = """
    <a href="/square/3516074637">Gangnam apartment jeonse anxiety</a>
    <a href="/square/3516074638">daily lunch thread</a>
    <a href="/square/3516074639">recruit apartment marketer</a>
    <a href="/square/3516074637">Gangnam apartment jeonse anxiety duplicate</a>
    <a href="/login">login</a>
    """
    fetcher = FakeFetcher({"https://theqoo.net/square": html})
    target = CrawlTarget.community_board("THEQOO", board_id="square", url="https://theqoo.net/square")
    adapter = GenericLinkBoardAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=1))

    result = await adapter.fetch_stream()

    assert [post.external_id for post in result.posts] == ["THEQOO-square-3516074637"]
    assert result.coverage is not None
    assert result.coverage.rows_seen == 1
    assert result.coverage.filtered_count == 2
    assert result.coverage.keyword_miss_count == 1
    assert result.coverage.excluded_title_count == 1
    assert result.coverage.duplicate_link_count == 1


def test_generic_board_truncates_card_style_titles_for_backend_contract():
    long_card_title = "Lh 신축매입약정 세미나 " + ("seminar detail " * 30) + " 딜 아고라 사는 이야기 2025-01-03 297 1 2"
    html = f'<a href="./view.php?code=community&idx=641&cate=">{long_card_title}</a>'

    posts = GenericLinkBoardAdapter.parse_list_html(
        html,
        source="DEALAGORA",
        board_id="community",
        base_url="https://dealagora.co.kr/subpage/bbs/borad.php?cate=&code=community&order=new",
    )

    assert len(posts) == 1
    assert posts[0].title.startswith("Lh 신축매입약정 세미나")
    assert "딜 아고라" not in posts[0].title
    assert len(posts[0].title) <= 180


@pytest.mark.anyio
async def test_generic_fetch_stream_walks_configured_page_templates():
    first_page = """
    <a href="/square/3516074637">Gangnam apartment jeonse anxiety</a>
    """
    second_page = """
    <a href="/square/3516074638">Mapo apartment transaction talk</a>
    """
    fetcher = FakeFetcher(
        {
            "https://theqoo.net/square": first_page,
            "https://theqoo.net/square?page=2": second_page,
        }
    )
    target = CrawlTarget.community_board("THEQOO", board_id="square", url="https://theqoo.net/square")
    adapter = GenericLinkBoardAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=2))

    result = await adapter.fetch_stream()

    assert fetcher.urls == ["https://theqoo.net/square", "https://theqoo.net/square?page=2"]
    assert [post.external_id for post in result.posts] == [
        "THEQOO-square-3516074637",
        "THEQOO-square-3516074638",
    ]
    assert result.coverage is not None
    assert result.coverage.pages_fetched == 2
