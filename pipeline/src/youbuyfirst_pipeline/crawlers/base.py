from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Protocol

import httpx

from youbuyfirst_pipeline.models import RawPost


class SourceBlockedError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


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
    def __init__(
        self,
        user_agent: str,
        timeout_seconds: float = 10.0,
        browser_channel: str | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.browser_channel = browser_channel.strip() if browser_channel else None
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    async def fetch_html(
        self,
        url: str,
        allow_browser_fallback: bool = True,
    ) -> FetchResult:
        try:
            return await self._fetch_http(url)
        except SourceBlockedError:
            raise
        except httpx.HTTPError:
            if not allow_browser_fallback:
                raise
            return await self._fetch_browser(url)

    async def fetch_browser_html(self, url: str) -> FetchResult:
        return await self._fetch_browser(url)

    async def _fetch_http(self, url: str) -> FetchResult:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.timeout_seconds,
            headers=self.headers,
        ) as client:
            response = await client.get(url)
            if response.status_code in {403, 429, 430}:
                raise SourceBlockedError(f"{url} returned {response.status_code}", status_code=response.status_code)
            response.raise_for_status()
            html = _decode_html(url, response)
            _raise_if_block_page(str(response.url), html)
            return FetchResult(url=str(response.url), html=html, status_code=response.status_code)

    async def _fetch_browser(self, url: str) -> FetchResult:
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            launch_options = {"headless": True}
            if self.browser_channel:
                launch_options["channel"] = self.browser_channel
            browser = await playwright.chromium.launch(**launch_options)
            page = await browser.new_page(user_agent=self.user_agent)
            response = await page.goto(url, wait_until="domcontentloaded", timeout=int(self.timeout_seconds * 1000))
            html = await page.content()
            status = response.status if response else 200
            await browser.close()
            if status in {403, 429, 430}:
                raise SourceBlockedError(f"{url} returned {status} with browser fallback", status_code=status)
            _raise_if_block_page(url, html)
            return FetchResult(url=url, html=html, status_code=status)


def parse_datetime(value: str | None) -> datetime:
    kst = timezone(timedelta(hours=9))
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.strip()
    for fmt in (
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d. %H:%M:%S",
        "%Y.%m.%d. %H:%M",
        "%y.%m.%d %H:%M:%S",
        "%y.%m.%d %H:%M",
    ):
        try:
            return datetime.strptime(normalized, fmt).replace(tzinfo=kst).astimezone(timezone.utc)
        except ValueError:
            pass
    for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%Y.%m.%d.", "%y.%m.%d", "%y.%m.%d."):
        try:
            return datetime.strptime(normalized, fmt).replace(tzinfo=kst).astimezone(timezone.utc)
        except ValueError:
            pass
    for fmt in ("%y-%m-%d", "%y-%m-%d."):
        try:
            return datetime.strptime(normalized, fmt).replace(tzinfo=kst).astimezone(timezone.utc)
        except ValueError:
            pass
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(normalized, fmt)
            now = datetime.now(kst)
            return now.replace(
                hour=parsed.hour,
                minute=parsed.minute,
                second=parsed.second,
                microsecond=0,
            ).astimezone(timezone.utc)
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


def _raise_if_block_page(url: str, html: str) -> None:
    normalized = html.lower()
    if "captcha" in normalized or "verify you are human" in normalized or "human verification" in normalized:
        raise SourceBlockedError(f"{url} returned CAPTCHA or human verification page")
    if "fmkorea.com" in url and "security check" in normalized[:2000]:
        raise SourceBlockedError(f"{url} returned known block page")
    if "fmkorea.com" in url and "에펨코리아 보안 시스템" in html[:2000]:
        raise SourceBlockedError(f"{url} returned known block page")
