from pathlib import Path

import pytest

from youbuyfirst_pipeline.board_stream import BoardStreamCrawler, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import FetchResult
from youbuyfirst_pipeline.crawlers.dcinside import DcinsideAdapter
from youbuyfirst_pipeline.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_pipeline.crawlers.ppomppu import PpomppuAdapter

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "crawlers"


class FakeFetcher:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.urls: list[str] = []
        self.browser_urls: list[str] = []

    async def fetch_html(self, url: str, allow_browser_fallback: bool = True) -> FetchResult:
        self.urls.append(url)
        return FetchResult(url=url, html=self.pages[url], status_code=200)

    async def fetch_browser_html(self, url: str) -> FetchResult:
        self.browser_urls.append(url)
        return FetchResult(url=url, html=self.pages[url], status_code=200)


def test_fmkorea_fixture_is_parsed_into_real_estate_posts():
    html = """
    <table>
      <tr>
        <td class="cate"><a href="/index.php?mid=realestate&category=1">real estate</a></td>
        <td class="title"><a href="/7001">Daejeon supply thread</a></td>
        <td class="author"><span>sample</span></td>
        <td class="time">09:20</td>
        <td class="m_no">10</td>
        <td class="m_no m_no_voted">1</td>
      </tr>
    </table>
    """

    posts = FmkoreaAdapter.parse_list_html(html, board_id="realestate")

    assert len(posts) == 1
    assert posts[0].source == "FMKOREA"
    assert posts[0].board_id == "realestate"
    assert posts[0].external_id == "FMKOREA-7001"
    assert posts[0].title == "Daejeon supply thread"
    assert posts[0].view_count == 10
    assert posts[0].recommend_count == 1


def test_fmkorea_query_links_skip_reply_links_and_keep_counts():
    html = """
    <table>
      <tr>
        <td class="title">
          <a href="/index.php?mid=realestate&document_srl=9829311712">Gangwon heat check</a>
          <a href="/index.php?mid=realestate&document_srl=9829311712#comment" class="replyNum">3</a>
        </td>
        <td class="author"><span>member</span></td>
        <td class="time">15:00</td>
        <td class="m_no">121</td>
        <td class="m_no m_no_voted">2</td>
      </tr>
    </table>
    """

    posts = FmkoreaAdapter.parse_list_html(html, board_id="realestate")

    assert [post.external_id for post in posts] == ["FMKOREA-9829311712"]
    assert posts[0].comment_count == 3
    assert posts[0].view_count == 121
    assert posts[0].recommend_count == 2


def test_dcinside_fixture_parses_board_counts_and_skips_notice_rows():
    html = """
    <table>
      <tr class="ub-content us-post">
        <td class="gall_num">notice</td>
        <td class="gall_tit"><a href="/board/view/?id=immovables&no=1">notice</a></td>
      </tr>
      <tr class="ub-content us-post">
        <td class="gall_num">7134003</td>
        <td class="gall_tit"><a href="/board/view/?id=immovables&no=7134003">Seoul rent anxiety <span class="reply_num">[3]</span></a></td>
        <td class="gall_writer" data-nick="writer">writer</td>
        <td class="gall_date" title="2026-05-24 04:34:20">04:34</td>
        <td class="gall_count">48</td>
        <td class="gall_recommend">2</td>
      </tr>
    </table>
    """

    posts = DcinsideAdapter.parse_list_html(
        html,
        board_id="immovables",
        base_url="https://gall.dcinside.com/board/lists/?id=immovables",
    )

    assert len(posts) == 1
    assert posts[0].source == "DCINSIDE"
    assert posts[0].board_id == "immovables"
    assert posts[0].external_id == "DCINSIDE-immovables-7134003"
    assert posts[0].title == "Seoul rent anxiety [3]"
    assert posts[0].author == "writer"
    assert posts[0].view_count == 48
    assert posts[0].recommend_count == 2
    assert posts[0].comment_count == 3


def test_dcinside_missing_reply_count_is_zero():
    html = """
    <table>
      <tr class="ub-content us-post">
        <td class="gall_num">7134004</td>
        <td class="gall_tit"><a href="/board/view/?id=immovables&no=7134004">No comments</a></td>
        <td class="gall_writer" data-nick="writer">writer</td>
        <td class="gall_date" title="2026-05-24 04:35:20">04:35</td>
        <td class="gall_count">12</td>
        <td class="gall_recommend">0</td>
      </tr>
    </table>
    """

    posts = DcinsideAdapter.parse_list_html(
        html,
        board_id="immovables",
        base_url="https://gall.dcinside.com/board/lists/?id=immovables",
    )

    assert len(posts) == 1
    assert posts[0].recommend_count == 0
    assert posts[0].comment_count == 0


def test_dcinside_real_estate_gallery_rows_keep_immovables_board_identity():
    html = (FIXTURE_DIR / "dcinside_realestate_immovables_sanitized.html").read_text(encoding="utf-8")

    posts = DcinsideAdapter.parse_list_html(
        html,
        board_id="immovables",
        base_url="https://gall.dcinside.com/board/lists/?id=immovables",
    )

    assert len(posts) == 2
    assert posts[0].board_id == "immovables"
    assert posts[0].external_id == "DCINSIDE-immovables-8537920"
    assert posts[0].url == "https://gall.dcinside.com/board/view/?id=immovables&no=8537920&page=1"
    assert posts[0].comment_count == 12
    assert posts[0].view_count == 1204
    assert posts[0].recommend_count == 8
    assert posts[1].external_id == "DCINSIDE-immovables-8537919"


def test_ppomppu_fixture_parses_house_board_counts_from_table_cells():
    html = """
    <table>
      <tr>
        <td>359353</td>
        <td><a href="/zboard/view.php?id=house&no=359353">Jeonse renewal question 19</a></td>
        <td>sample</td>
        <td>00:57:14</td>
        <td>8 - 0</td>
        <td>1,788</td>
      </tr>
    </table>
    """

    posts = PpomppuAdapter.parse_list_html(
        html,
        board_id="house",
        base_url="https://www.ppomppu.co.kr/zboard/zboard.php?id=house",
    )

    assert len(posts) == 1
    assert posts[0].source == "PPOMPPU"
    assert posts[0].board_id == "house"
    assert posts[0].external_id == "PPOMPPU-house-359353"
    assert posts[0].title == "Jeonse renewal question 19"
    assert posts[0].author == "sample"
    assert posts[0].view_count == 1788
    assert posts[0].recommend_count == 8
    assert posts[0].comment_count == 19


def test_ppomppu_real_estate_forum_rows_keep_house_board_identity():
    html = (FIXTURE_DIR / "ppomppu_realestate_house_mobile_sanitized.html").read_text(encoding="utf-8")

    posts = PpomppuAdapter.parse_list_html(
        html,
        board_id="house",
        base_url="https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1",
    )

    assert len(posts) == 2
    assert posts[0].board_id == "house"
    assert posts[0].external_id == "PPOMPPU-house-253149"
    assert posts[0].url == "https://m.ppomppu.co.kr/new/bbs_view.php?id=house&no=253149&page=1"
    assert posts[0].comment_count == 6
    assert posts[0].recommend_count == 0
    assert posts[0].view_count == 812
    assert posts[1].external_id == "PPOMPPU-house-253148"
    assert posts[1].comment_count == 0
    assert posts[1].view_count == 127
    assert posts[1].published_at.second == 31


def test_ppomppu_blank_recommend_and_missing_comment_are_zero():
    html = """
    <table>
      <tr align="center" class="baseList">
        <td class="baseList-space baseList-numb" colspan="2">362865</td>
        <td align="left" class="baseList-space">
          <a class="baseList-title" href="view.php?id=house&page=1&no=362865"><span>No reactions</span></a>
        </td>
        <td align="left" class="baseList-space" colspan="2">writer</td>
        <td class="baseList-space" colspan="2" title="26.05.24 15:10:41"><time class="baseList-time">15:10:41</time></td>
        <td class="baseList-space baseList-rec" colspan="2"></td>
        <td class="baseList-space baseList-views" colspan="2">257</td>
      </tr>
    </table>
    """

    posts = PpomppuAdapter.parse_list_html(
        html,
        board_id="house",
        base_url="https://www.ppomppu.co.kr/zboard/zboard.php?id=house",
    )

    assert len(posts) == 1
    assert posts[0].recommend_count == 0
    assert posts[0].comment_count == 0
    assert posts[0].view_count == 257


@pytest.mark.anyio
async def test_fmkorea_fetch_stream_walks_pages_until_duplicate_with_coverage():
    first_page = """
    <table><tr>
      <td class="title"><a href="/1002">new thread</a></td>
      <td class="author"><span>writer</span></td>
      <td class="time">09:20</td>
      <td class="m_no">10</td>
      <td class="m_no m_no_voted">1</td>
    </tr></table>
    """
    second_page = """
    <table><tr>
      <td class="title"><a href="/1001">old thread</a></td>
      <td class="author"><span>writer</span></td>
      <td class="time">09:19</td>
      <td class="m_no">9</td>
      <td class="m_no m_no_voted">0</td>
    </tr></table>
    """
    fetcher = FakeFetcher(
        {
            "https://www.fmkorea.com/realestate": first_page,
            "https://www.fmkorea.com/realestate?page=2": second_page,
        }
    )
    target = CrawlTarget.community_board("FMKOREA", board_id="realestate", url="https://www.fmkorea.com/realestate")
    adapter = FmkoreaAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=5))

    result = await adapter.fetch_stream(BoardWatermark(last_seen_external_id="FMKOREA-1001"))

    assert fetcher.urls == []
    assert fetcher.browser_urls == ["https://www.fmkorea.com/realestate", "https://www.fmkorea.com/realestate?page=2"]
    assert [post.external_id for post in result.posts] == ["FMKOREA-1002"]
    assert result.coverage.pages_fetched == 2
    assert result.coverage.rows_seen == 2
    assert result.coverage.duplicate_stop is True
    assert result.coverage.coverage_status == "complete"


@pytest.mark.anyio
async def test_fmkorea_fetch_stream_uses_browser_fetch_by_default_without_http_first():
    page = """
    <table><tr>
      <td class="title"><a href="/1002">new thread</a></td>
      <td class="author"><span>writer</span></td>
      <td class="time">09:20</td>
    </tr></table>
    """
    fetcher = FakeFetcher({"https://www.fmkorea.com/realestate": page})
    target = CrawlTarget.community_board("FMKOREA", board_id="realestate", url="https://www.fmkorea.com/realestate")
    adapter = FmkoreaAdapter(
        fetcher,
        target=target,
        stream_crawler=BoardStreamCrawler(max_pages_per_run=1),
    )

    result = await adapter.fetch_stream()

    assert [post.external_id for post in result.posts] == ["FMKOREA-1002"]
    assert fetcher.urls == []
    assert fetcher.browser_urls == ["https://www.fmkorea.com/realestate"]


@pytest.mark.anyio
async def test_dcinside_fetch_stream_walks_pages_until_duplicate():
    first_page = """
    <table><tr class="ub-content us-post">
      <td class="gall_num">2</td>
      <td class="gall_tit"><a href="/board/view/?id=immovables&no=2">new thread</a></td>
      <td class="gall_writer" data-nick="writer">writer</td>
      <td class="gall_date">09:20</td>
      <td class="gall_count">10</td>
      <td class="gall_recommend">1</td>
    </tr></table>
    """
    second_page = """
    <table><tr class="ub-content us-post">
      <td class="gall_num">1</td>
      <td class="gall_tit"><a href="/board/view/?id=immovables&no=1">old thread</a></td>
      <td class="gall_writer" data-nick="writer">writer</td>
      <td class="gall_date">09:19</td>
      <td class="gall_count">9</td>
      <td class="gall_recommend">0</td>
    </tr></table>
    """
    fetcher = FakeFetcher(
        {
            "https://gall.dcinside.com/board/lists/?id=immovables": first_page,
            "https://gall.dcinside.com/board/lists/?id=immovables&page=2": second_page,
        }
    )
    target = CrawlTarget.community_board(
        "DCINSIDE",
        board_id="immovables",
        url="https://gall.dcinside.com/board/lists/?id=immovables",
    )
    adapter = DcinsideAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=5))

    result = await adapter.fetch_stream(BoardWatermark(last_seen_external_id="DCINSIDE-immovables-1"))

    assert fetcher.urls == [
        "https://gall.dcinside.com/board/lists/?id=immovables",
        "https://gall.dcinside.com/board/lists/?id=immovables&page=2",
    ]
    assert [post.external_id for post in result.posts] == ["DCINSIDE-immovables-2"]
    assert result.coverage.duplicate_stop is True


@pytest.mark.anyio
async def test_ppomppu_fetch_stream_walks_pages_until_duplicate():
    first_page = """
    <table><tr>
      <td>2</td>
      <td><a href="/zboard/view.php?id=house&no=2">new thread</a></td>
      <td>writer</td>
      <td>09:20</td>
      <td>1 - 0</td>
      <td>10</td>
    </tr></table>
    """
    second_page = """
    <table><tr>
      <td>1</td>
      <td><a href="/zboard/view.php?id=house&no=1">old thread</a></td>
      <td>writer</td>
      <td>09:19</td>
      <td>0 - 0</td>
      <td>9</td>
    </tr></table>
    """
    fetcher = FakeFetcher(
        {
            "https://www.ppomppu.co.kr/zboard/zboard.php?id=house": first_page,
            "https://www.ppomppu.co.kr/zboard/zboard.php?id=house&page=2": second_page,
        }
    )
    target = CrawlTarget.community_board(
        "PPOMPPU",
        board_id="house",
        url="https://www.ppomppu.co.kr/zboard/zboard.php?id=house",
    )
    adapter = PpomppuAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=5))

    result = await adapter.fetch_stream(BoardWatermark(last_seen_external_id="PPOMPPU-house-1"))

    assert fetcher.urls == [
        "https://www.ppomppu.co.kr/zboard/zboard.php?id=house",
        "https://www.ppomppu.co.kr/zboard/zboard.php?id=house&page=2",
    ]
    assert [post.external_id for post in result.posts] == ["PPOMPPU-house-2"]
    assert result.coverage.duplicate_stop is True
