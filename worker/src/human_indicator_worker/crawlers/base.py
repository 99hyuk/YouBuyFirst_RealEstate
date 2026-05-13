from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Protocol

import httpx

from human_indicator_worker.models import RawPost


class SourceBlockedError(RuntimeError):
    pass


class CommunityAdapter(Protocol):
    source: str

    async def fetch_posts(self) -> list[RawPost]:
        ...


@dataclass(frozen=True)
class FetchResult:
    url: str
    html: str
    status_code: int


class BrowserCapableFetcher:
    def __init__(self, user_agent: str, timeout_seconds: float = 10.0) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    async def fetch_html(self, url: str, allow_browser_fallback: bool = True) -> FetchResult:
        try:
            return await self._fetch_http(url)
        except (httpx.HTTPError, SourceBlockedError):
            if not allow_browser_fallback:
                raise
            return await self._fetch_browser(url)

    async def _fetch_http(self, url: str) -> FetchResult:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.timeout_seconds,
            headers={"User-Agent": self.user_agent},
        ) as client:
            response = await client.get(url)
            if response.status_code in {403, 429}:
                raise SourceBlockedError(f"{url} returned {response.status_code}")
            response.raise_for_status()
            return FetchResult(url=str(response.url), html=_decode_html(url, response), status_code=response.status_code)

    async def _fetch_browser(self, url: str) -> FetchResult:
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page(user_agent=self.user_agent)
            response = await page.goto(url, wait_until="domcontentloaded", timeout=int(self.timeout_seconds * 1000))
            html = await page.content()
            status = response.status if response else 200
            await browser.close()
            if status in {403, 429}:
                raise SourceBlockedError(f"{url} returned {status} with browser fallback")
            return FetchResult(url=url, html=html, status_code=status)


def parse_datetime(value: str | None) -> datetime:
    kst = timezone(timedelta(hours=9))
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.strip()
    for fmt in ("%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M", "%Y.%m.%d. %H:%M"):
        try:
            return datetime.strptime(normalized, fmt).replace(tzinfo=kst).astimezone(timezone.utc)
        except ValueError:
            pass
    for fmt in ("%H:%M",):
        try:
            parsed = datetime.strptime(normalized, fmt)
            now = datetime.now(kst)
            return now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0).astimezone(timezone.utc)
        except ValueError:
            pass
    try:
        parsed = parsedate_to_datetime(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def _decode_html(url: str, response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "").lower()
    if "charset=utf-8" in content_type or "fmkorea.com" in url:
        return response.content.decode("utf-8", errors="replace")
    return response.text
