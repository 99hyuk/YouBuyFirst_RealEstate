from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from youbuyfirst_pipeline.crawlers.base import SourceBlockedError


@dataclass(frozen=True)
class CrawlBackoffDecision:
    category: str
    seconds: int
    reason: str
    retry_after: datetime


class CrawlBackoffPolicy:
    def __init__(
        self,
        blocked_seconds: int = 6 * 60 * 60,
        transient_seconds: int = 15 * 60,
        unknown_seconds: int = 60 * 60,
    ) -> None:
        self.blocked_seconds = blocked_seconds
        self.transient_seconds = transient_seconds
        self.unknown_seconds = unknown_seconds

    def for_exception(self, exc: Exception, now: datetime) -> CrawlBackoffDecision:
        if isinstance(exc, SourceBlockedError):
            return self._decision(
                "blocked",
                self.blocked_seconds,
                "source returned a block or rate-limit signal; cool down before retry",
                now,
            )
        if _is_transient(exc):
            return self._decision(
                "transient-error",
                self.transient_seconds,
                "temporary network or server error; retry after a short pause",
                now,
            )
        return self._decision(
            "unknown-error",
            self.unknown_seconds,
            "unexpected crawler error; pause before repeating the same failure",
            now,
        )

    @staticmethod
    def _decision(category: str, seconds: int, reason: str, now: datetime) -> CrawlBackoffDecision:
        normalized_now = now.astimezone(timezone.utc)
        return CrawlBackoffDecision(
            category=category,
            seconds=seconds,
            reason=reason,
            retry_after=normalized_now + timedelta(seconds=seconds),
        )


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_transient(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False
