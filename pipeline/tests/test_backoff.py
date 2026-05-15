from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from youbuyfirst_pipeline.backoff import CrawlBackoffPolicy, format_utc
from youbuyfirst_pipeline.crawlers.base import SourceBlockedError


NOW = datetime(2026, 5, 15, 0, 0, tzinfo=timezone.utc)


def test_blocked_source_uses_long_cooldown():
    decision = CrawlBackoffPolicy().for_exception(SourceBlockedError("https://example.com returned 429"), NOW)

    assert decision.category == "blocked"
    assert decision.seconds == 21600
    assert decision.retry_after == NOW + timedelta(hours=6)
    assert "block or rate-limit" in decision.reason


def test_timeout_uses_short_transient_cooldown():
    decision = CrawlBackoffPolicy().for_exception(httpx.TimeoutException("read timed out"), NOW)

    assert decision.category == "transient-error"
    assert decision.seconds == 900
    assert decision.retry_after == NOW + timedelta(minutes=15)


def test_unknown_error_uses_medium_cooldown():
    decision = CrawlBackoffPolicy().for_exception(RuntimeError("parser failed"), NOW)

    assert decision.category == "unknown-error"
    assert decision.seconds == 3600
    assert decision.retry_after == NOW + timedelta(hours=1)


def test_format_utc_uses_z_suffix():
    assert format_utc(NOW) == "2026-05-15T00:00:00Z"
