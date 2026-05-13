from youbuyfirst_worker.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_worker.crawlers.naver import NaverBoardAdapter


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
