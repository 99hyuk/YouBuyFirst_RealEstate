from datetime import timezone
from pathlib import Path

import pytest

from youbuyfirst_pipeline.board_stream import BoardStreamCrawler, BoardWatermark
from youbuyfirst_pipeline.crawl_targets import CrawlTarget
from youbuyfirst_pipeline.crawlers.base import FetchResult
from youbuyfirst_pipeline.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_pipeline.crawlers.dcinside import DcinsideAdapter
from youbuyfirst_pipeline.crawlers.naver import NaverBoardAdapter
from youbuyfirst_pipeline.crawlers.ppomppu import PpomppuAdapter

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "crawlers"


class FakeFetcher:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.urls: list[str] = []

    async def fetch_html(self, url: str, allow_browser_fallback: bool = True) -> FetchResult:
        self.urls.append(url)
        return FetchResult(url=url, html=self.pages[url], status_code=200)


def test_naver_fixture_is_parsed_into_posts():
    html = """
    <table class="type2">
      <tr>
        <td class="title"><a href="/item/board_read.naver?code=005930&nid=1">삼전 오늘 반등?</a></td>
        <td class="p11">2026.05.13 09:10</td>
        <td class="p11">ㅇㅇ</td>
      </tr>
    </table>
    """

    posts = NaverBoardAdapter.parse_list_html(html, stock_code="005930")

    assert len(posts) == 1
    assert posts[0].source == "NAVER"
    assert posts[0].external_id == "NAVER-005930-1"
    assert posts[0].title == "삼전 오늘 반등?"
    assert posts[0].url.startswith("https://finance.naver.com")


def test_naver_realistic_board_fixture_uses_first_cell_as_published_at():
    html = (FIXTURE_DIR / "naver_board_realistic.html").read_text(encoding="utf-8")

    posts = NaverBoardAdapter.parse_list_html(html, stock_code="005930")

    assert len(posts) == 2
    assert posts[0].external_id == "NAVER-005930-420099001"
    assert posts[0].title == "삼전 수급 다시 확인"
    assert posts[0].author == "sample_writer"
    assert posts[0].published_at.isoformat() == "2026-05-15T08:13:00+00:00"
    assert posts[1].published_at.isoformat() == "2026-05-15T08:12:00+00:00"


def test_fmkorea_fixture_is_parsed_into_posts():
    html = """
    <table>
      <tr>
        <td class="cate"><a href="/index.php?mid=stock&category=1">국내주식</a></td>
        <td class="title"><a href="/7001">엔비디아 실적 기대</a></td>
        <td class="author"><span>익명</span></td>
        <td class="time">09:20</td>
      </tr>
    </table>
    """

    posts = FmkoreaAdapter.parse_list_html(html)

    assert len(posts) == 1
    assert posts[0].source == "FMKOREA"
    assert posts[0].external_id == "FMKOREA-7001"
    assert posts[0].title == "엔비디아 실적 기대"


def test_fmkorea_realistic_stock_fixture_skips_notices_and_parses_query_links():
    html = (FIXTURE_DIR / "fmkorea_stock_realistic.html").read_text(encoding="utf-8")

    posts = FmkoreaAdapter.parse_list_html(html)

    assert [post.external_id for post in posts] == [
        "FMKOREA-9829311712",
        "FMKOREA-9829309258",
    ]
    assert posts[0].title == "반도체 ETF는 다음주 진입각"
    assert posts[0].author == "sample_member"
    assert posts[0].board_id == "stock"
    assert posts[0].view_count == 121
    assert posts[0].recommend_count == 2
    assert posts[0].comment_count == 1
    assert posts[0].published_at.tzinfo is not None
    assert posts[1].title == "마이크론 실적 체크"
    assert posts[1].view_count == 252
    assert posts[1].recommend_count == 0
    assert posts[1].comment_count == 0
    assert posts[1].published_at.replace(tzinfo=timezone.utc).isoformat() == "2026-05-14T15:00:00+00:00"


def test_dcinside_fixture_parses_board_counts_and_skips_notice_rows():
    html = """
    <table>
      <tr class="ub-content us-post">
        <td class="gall_num">공지</td>
        <td class="gall_tit"><a href="/board/view/?id=neostock&no=1">공지</a></td>
      </tr>
      <tr class="ub-content us-post">
        <td class="gall_num">7134003</td>
        <td class="gall_tit"><a href="/board/view/?id=neostock&no=7134003">바닥 찍고 불장 신호옴 <span class="reply_num">[3]</span></a></td>
        <td class="gall_writer" data-nick="주갤러">주갤러</td>
        <td class="gall_date" title="2026-05-24 04:34:20">04:34</td>
        <td class="gall_count">48</td>
        <td class="gall_recommend">2</td>
      </tr>
    </table>
    """

    posts = DcinsideAdapter.parse_list_html(html, board_id="neostock", base_url="https://gall.dcinside.com/board/lists/?id=neostock")

    assert len(posts) == 1
    assert posts[0].source == "DCINSIDE"
    assert posts[0].board_id == "neostock"
    assert posts[0].external_id == "DCINSIDE-neostock-7134003"
    assert posts[0].title == "바닥 찍고 불장 신호옴 [3]"
    assert posts[0].author == "주갤러"
    assert posts[0].view_count == 48
    assert posts[0].recommend_count == 2
    assert posts[0].comment_count == 3
    assert posts[0].published_at.isoformat() == "2026-05-23T19:34:20+00:00"


def test_dcinside_missing_reply_count_is_zero():
    html = """
    <table>
      <tr class="ub-content us-post">
        <td class="gall_num">7134004</td>
        <td class="gall_tit"><a href="/board/view/?id=neostock&no=7134004">No comments</a></td>
        <td class="gall_writer" data-nick="writer">writer</td>
        <td class="gall_date" title="2026-05-24 04:35:20">04:35</td>
        <td class="gall_count">12</td>
        <td class="gall_recommend">0</td>
      </tr>
    </table>
    """

    posts = DcinsideAdapter.parse_list_html(html, board_id="neostock", base_url="https://gall.dcinside.com/board/lists/?id=neostock")

    assert len(posts) == 1
    assert posts[0].recommend_count == 0
    assert posts[0].comment_count == 0


def test_ppomppu_fixture_parses_board_counts_from_table_cells():
    html = """
    <table>
      <tr>
        <td>359353</td>
        <td><a href="/zboard/view.php?id=stock&no=359353">삼성전자 노조 여전함 19</a></td>
        <td>Ktae</td>
        <td>00:57:14</td>
        <td>8 - 0</td>
        <td>1,788</td>
      </tr>
    </table>
    """

    posts = PpomppuAdapter.parse_list_html(html, board_id="stock", base_url="https://www.ppomppu.co.kr/zboard/zboard.php?id=stock")

    assert len(posts) == 1
    assert posts[0].source == "PPOMPPU"
    assert posts[0].board_id == "stock"
    assert posts[0].external_id == "PPOMPPU-stock-359353"
    assert posts[0].title == "삼성전자 노조 여전함 19"
    assert posts[0].author == "Ktae"
    assert posts[0].view_count == 1788
    assert posts[0].recommend_count == 8
    assert posts[0].comment_count == 19


def test_ppomppu_realistic_stock_rows_ignore_news_links_and_parse_metadata():
    html = """
    <table>
      <tr><td><a href="/zboard/view.php?id=news&no=620408">연중 15도 뉴스</a></td></tr>
      <tr align="center" class="baseList">
        <td class="baseList-space baseList-numb" colspan="2">공지</td>
        <td align="left" class="baseList-space">
          <a class="baseList-title" href="view.php?id=stock&page=1&divpage=71&no=253231"><span>미국 주식 투자에 도움되는 사이트</span></a>
          <span class="baseList-c">418</span>
        </td>
        <td>notice_writer</td><td title="23.09.03 22:10:26">23/09/03</td><td>162</td><td>105585</td>
      </tr>
      <tr align="center" class="baseList">
        <td class="baseList-space baseList-numb" colspan="2">362864</td>
        <td align="left" class="baseList-space">
          <a class="baseList-title" href="view.php?id=stock&page=1&divpage=71&no=362864"><span>개발자인데 AI 버블 얘기 볼때마다 기분 좋습니다.</span></a>
          <span class="baseList-c">8</span>
        </td>
        <td align="left" class="baseList-space" colspan="2"><div class="list_name"><nobr>[* 익명 *]</nobr></div></td>
        <td class="baseList-space" colspan="2" title="26.05.24 15:03:46"><time class="baseList-time">15:03:46</time></td>
        <td class="baseList-space baseList-rec" colspan="2">7 - 0</td>
        <td class="baseList-space baseList-views" colspan="2">1,426</td>
      </tr>
    </table>
    """

    posts = PpomppuAdapter.parse_list_html(html, board_id="stock", base_url="https://www.ppomppu.co.kr/zboard/zboard.php?id=stock")

    assert [post.external_id for post in posts] == ["PPOMPPU-stock-362864"]
    assert posts[0].title == "개발자인데 AI 버블 얘기 볼때마다 기분 좋습니다."
    assert posts[0].author == "[* 익명 *]"
    assert posts[0].published_at.isoformat() == "2026-05-24T06:03:46+00:00"
    assert posts[0].recommend_count == 7
    assert posts[0].view_count == 1426
    assert posts[0].comment_count == 8


def test_ppomppu_blank_recommend_and_missing_comment_are_zero():
    html = """
    <table>
      <tr align="center" class="baseList">
        <td class="baseList-space baseList-numb" colspan="2">362865</td>
        <td align="left" class="baseList-space">
          <a class="baseList-title" href="view.php?id=stock&page=1&divpage=71&no=362865"><span>No reactions</span></a>
        </td>
        <td align="left" class="baseList-space" colspan="2">writer</td>
        <td class="baseList-space" colspan="2" title="26.05.24 15:10:41"><time class="baseList-time">15:10:41</time></td>
        <td class="baseList-space baseList-rec" colspan="2"></td>
        <td class="baseList-space baseList-views" colspan="2">257</td>
      </tr>
    </table>
    """

    posts = PpomppuAdapter.parse_list_html(html, board_id="stock", base_url="https://www.ppomppu.co.kr/zboard/zboard.php?id=stock")

    assert len(posts) == 1
    assert posts[0].recommend_count == 0
    assert posts[0].comment_count == 0
    assert posts[0].view_count == 257


@pytest.mark.anyio
async def test_fmkorea_fetch_stream_walks_pages_until_duplicate_with_coverage():
    first_page = """
    <table><tr>
      <td class="title"><a href="/1002">새 글</a></td>
      <td class="author"><span>writer</span></td>
      <td class="time">09:20</td>
      <td class="m_no">10</td>
      <td class="m_no m_no_voted">1</td>
    </tr></table>
    """
    second_page = """
    <table><tr>
      <td class="title"><a href="/1001">이미 본 글</a></td>
      <td class="author"><span>writer</span></td>
      <td class="time">09:19</td>
      <td class="m_no">9</td>
      <td class="m_no m_no_voted">0</td>
    </tr></table>
    """
    fetcher = FakeFetcher(
        {
            "https://www.fmkorea.com/stock": first_page,
            "https://www.fmkorea.com/stock?page=2": second_page,
        }
    )
    target = CrawlTarget.community_board("FMKOREA", board_id="stock", url="https://www.fmkorea.com/stock")
    adapter = FmkoreaAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=5))

    result = await adapter.fetch_stream(BoardWatermark(last_seen_external_id="FMKOREA-1001"))

    assert fetcher.urls == ["https://www.fmkorea.com/stock", "https://www.fmkorea.com/stock?page=2"]
    assert [post.external_id for post in result.posts] == ["FMKOREA-1002"]
    assert result.coverage.pages_fetched == 2
    assert result.coverage.rows_seen == 2
    assert result.coverage.duplicate_stop is True
    assert result.coverage.coverage_status == "complete"


@pytest.mark.anyio
async def test_dcinside_fetch_stream_walks_pages_until_duplicate():
    first_page = """
    <table><tr class="ub-content us-post">
      <td class="gall_num">2</td>
      <td class="gall_tit"><a href="/board/view/?id=neostock&no=2">새 글</a></td>
      <td class="gall_writer" data-nick="writer">writer</td>
      <td class="gall_date">09:20</td>
      <td class="gall_count">10</td>
      <td class="gall_recommend">1</td>
    </tr></table>
    """
    second_page = """
    <table><tr class="ub-content us-post">
      <td class="gall_num">1</td>
      <td class="gall_tit"><a href="/board/view/?id=neostock&no=1">이미 본 글</a></td>
      <td class="gall_writer" data-nick="writer">writer</td>
      <td class="gall_date">09:19</td>
      <td class="gall_count">9</td>
      <td class="gall_recommend">0</td>
    </tr></table>
    """
    fetcher = FakeFetcher(
        {
            "https://gall.dcinside.com/board/lists/?id=neostock": first_page,
            "https://gall.dcinside.com/board/lists/?id=neostock&page=2": second_page,
        }
    )
    target = CrawlTarget.community_board("DCINSIDE", board_id="neostock", url="https://gall.dcinside.com/board/lists/?id=neostock")
    adapter = DcinsideAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=5))

    result = await adapter.fetch_stream(BoardWatermark(last_seen_external_id="DCINSIDE-neostock-1"))

    assert fetcher.urls == [
        "https://gall.dcinside.com/board/lists/?id=neostock",
        "https://gall.dcinside.com/board/lists/?id=neostock&page=2",
    ]
    assert [post.external_id for post in result.posts] == ["DCINSIDE-neostock-2"]
    assert result.coverage.duplicate_stop is True


@pytest.mark.anyio
async def test_ppomppu_fetch_stream_walks_pages_until_duplicate():
    first_page = """
    <table><tr>
      <td>2</td>
      <td><a href="/zboard/view.php?id=stock&no=2">새 글</a></td>
      <td>writer</td>
      <td>09:20</td>
      <td>1 - 0</td>
      <td>10</td>
    </tr></table>
    """
    second_page = """
    <table><tr>
      <td>1</td>
      <td><a href="/zboard/view.php?id=stock&no=1">이미 본 글</a></td>
      <td>writer</td>
      <td>09:19</td>
      <td>0 - 0</td>
      <td>9</td>
    </tr></table>
    """
    fetcher = FakeFetcher(
        {
            "https://www.ppomppu.co.kr/zboard/zboard.php?id=stock": first_page,
            "https://www.ppomppu.co.kr/zboard/zboard.php?id=stock&page=2": second_page,
        }
    )
    target = CrawlTarget.community_board("PPOMPPU", board_id="stock", url="https://www.ppomppu.co.kr/zboard/zboard.php?id=stock")
    adapter = PpomppuAdapter(fetcher, target=target, stream_crawler=BoardStreamCrawler(max_pages_per_run=5))

    result = await adapter.fetch_stream(BoardWatermark(last_seen_external_id="PPOMPPU-stock-1"))

    assert fetcher.urls == [
        "https://www.ppomppu.co.kr/zboard/zboard.php?id=stock",
        "https://www.ppomppu.co.kr/zboard/zboard.php?id=stock&page=2",
    ]
    assert [post.external_id for post in result.posts] == ["PPOMPPU-stock-2"]
    assert result.coverage.duplicate_stop is True
