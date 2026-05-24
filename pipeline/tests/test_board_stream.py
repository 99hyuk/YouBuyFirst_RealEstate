from datetime import datetime, timezone

import pytest

from youbuyfirst_pipeline.board_stream import BoardPage, BoardStreamCrawler, BoardWatermark
from youbuyfirst_pipeline.models import RawPost


def _post(external_id: str, published_at: str) -> RawPost:
    return RawPost(
        source="FMKOREA",
        board_id="stock",
        external_id=external_id,
        url=f"https://example.com/{external_id}",
        title=external_id,
        content="",
        author="sample",
        published_at=datetime.fromisoformat(published_at).replace(tzinfo=timezone.utc),
    )


@pytest.mark.anyio
async def test_board_stream_stops_after_duplicate_and_records_coverage():
    requested_cursors: list[str | None] = []
    pages = {
        None: BoardPage(
            cursor="1",
            posts=[
                _post("FMKOREA-3", "2026-05-24T02:02:00"),
                _post("FMKOREA-2", "2026-05-24T02:01:00"),
            ],
            next_cursor="2",
            ignored_pinned_count=1,
        ),
        "2": BoardPage(
            cursor="2",
            posts=[
                _post("FMKOREA-1", "2026-05-24T02:00:00"),
                _post("FMKOREA-0", "2026-05-24T01:59:00"),
            ],
            next_cursor="3",
        ),
    }

    async def fetch_page(cursor: str | None) -> BoardPage:
        requested_cursors.append(cursor)
        return pages[cursor]

    result = await BoardStreamCrawler().collect(
        fetch_page,
        BoardWatermark(last_seen_external_id="FMKOREA-1"),
    )

    assert [post.external_id for post in result.posts] == ["FMKOREA-3", "FMKOREA-2"]
    assert requested_cursors == [None, "2"]
    assert result.coverage.pages_fetched == 2
    assert result.coverage.rows_seen == 4
    assert result.coverage.ignored_pinned_count == 1
    assert result.coverage.duplicate_stop is True
    assert result.coverage.cutoff_stop is False
    assert result.coverage.coverage_status == "complete"
    assert result.coverage.oldest_seen_at == datetime(2026, 5, 24, 1, 59, tzinfo=timezone.utc)
    assert result.coverage.newest_seen_at == datetime(2026, 5, 24, 2, 2, tzinfo=timezone.utc)


@pytest.mark.anyio
async def test_board_stream_continues_current_page_after_duplicate_or_cutoff_hit():
    requested_cursors: list[str | None] = []
    pages = {
        None: BoardPage(
            cursor="1",
            posts=[
                _post("FMKOREA-4", "2026-05-24T02:04:00"),
                _post("FMKOREA-1", "2026-05-24T02:00:00"),
                _post("FMKOREA-3", "2026-05-24T02:03:00"),
                _post("FMKOREA-0", "2026-05-24T01:59:00"),
            ],
            next_cursor="2",
        ),
        "2": BoardPage(cursor="2", posts=[_post("FMKOREA-next", "2026-05-24T01:58:00")]),
    }

    async def fetch_page(cursor: str | None) -> BoardPage:
        requested_cursors.append(cursor)
        return pages[cursor]

    result = await BoardStreamCrawler().collect(
        fetch_page,
        BoardWatermark(
            last_seen_external_id="FMKOREA-1",
            cutoff_at=datetime(2026, 5, 24, 2, 0, tzinfo=timezone.utc),
        ),
    )

    assert [post.external_id for post in result.posts] == ["FMKOREA-4", "FMKOREA-3"]
    assert requested_cursors == [None]
    assert result.coverage.rows_seen == 4
    assert result.coverage.duplicate_stop is True
    assert result.coverage.cutoff_stop is True


@pytest.mark.anyio
async def test_board_stream_uses_duplicate_time_as_cutoff_when_watermark_has_no_cutoff():
    requested_cursors: list[str | None] = []
    pages = {
        None: BoardPage(
            cursor="1",
            posts=[
                _post("FMKOREA-4", "2026-05-24T02:04:00"),
                _post("FMKOREA-1", "2026-05-24T02:00:00"),
                _post("FMKOREA-3", "2026-05-24T02:03:00"),
                _post("FMKOREA-0", "2026-05-24T01:59:00"),
            ],
            next_cursor="2",
        ),
        "2": BoardPage(cursor="2", posts=[_post("FMKOREA-next", "2026-05-24T01:58:00")]),
    }

    async def fetch_page(cursor: str | None) -> BoardPage:
        requested_cursors.append(cursor)
        return pages[cursor]

    result = await BoardStreamCrawler().collect(
        fetch_page,
        BoardWatermark(last_seen_external_id="FMKOREA-1"),
    )

    assert [post.external_id for post in result.posts] == ["FMKOREA-4", "FMKOREA-3"]
    assert requested_cursors == [None]
    assert result.coverage.duplicate_stop is True
    assert result.coverage.cutoff_stop is False


@pytest.mark.anyio
async def test_board_stream_waits_between_page_requests():
    requested_cursors: list[str | None] = []
    slept_seconds: list[float] = []
    pages = {
        None: BoardPage(cursor="1", posts=[_post("FMKOREA-3", "2026-05-24T02:02:00")], next_cursor="2"),
        "2": BoardPage(cursor="2", posts=[_post("FMKOREA-2", "2026-05-24T02:01:00")], next_cursor="3"),
        "3": BoardPage(cursor="3", posts=[_post("FMKOREA-1", "2026-05-24T02:00:00")], next_cursor=None),
    }

    async def fetch_page(cursor: str | None) -> BoardPage:
        requested_cursors.append(cursor)
        return pages[cursor]

    async def sleeper(seconds: float) -> None:
        slept_seconds.append(seconds)

    crawler = BoardStreamCrawler(
        page_delay_min_seconds=1.5,
        page_delay_max_seconds=4.0,
        random_delay=lambda minimum, maximum: maximum,
        sleeper=sleeper,
    )

    result = await crawler.collect(fetch_page)

    assert [post.external_id for post in result.posts] == ["FMKOREA-3", "FMKOREA-2", "FMKOREA-1"]
    assert requested_cursors == [None, "2", "3"]
    assert slept_seconds == [4.0, 4.0]


def test_board_stream_rejects_invalid_delay_window():
    with pytest.raises(ValueError, match="page_delay"):
        BoardStreamCrawler(page_delay_min_seconds=5.0, page_delay_max_seconds=1.0)
