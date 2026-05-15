from datetime import timezone
from pathlib import Path

from youbuyfirst_pipeline.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_pipeline.crawlers.naver import NaverBoardAdapter

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "crawlers"


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
    assert posts[0].published_at.tzinfo is not None
    assert posts[1].title == "마이크론 실적 체크"
    assert posts[1].published_at.replace(tzinfo=timezone.utc).isoformat() == "2026-05-14T15:00:00+00:00"
