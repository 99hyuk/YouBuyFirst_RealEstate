import httpx
import pytest
import respx

from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher, SourceBlockedError


@pytest.mark.anyio
@respx.mock
async def test_fetcher_treats_rate_limit_as_blocked_without_browser_fallback():
    respx.get("https://example.com/board").mock(return_value=httpx.Response(429))

    with pytest.raises(SourceBlockedError, match="429"):
        await BrowserCapableFetcher(user_agent="test").fetch_html("https://example.com/board")


@pytest.mark.anyio
@respx.mock
async def test_fetcher_sends_standard_html_request_headers():
    route = respx.get("https://example.com/board").mock(return_value=httpx.Response(200, text="<html></html>"))

    await BrowserCapableFetcher(user_agent="test").fetch_html("https://example.com/board")

    request_headers = route.calls.last.request.headers
    assert request_headers["accept"].startswith("text/html")
    assert "ko-KR" in request_headers["accept-language"]


def test_fetcher_keeps_optional_browser_channel_for_local_rendering():
    fetcher = BrowserCapableFetcher(user_agent="test", browser_channel="msedge")

    assert fetcher.browser_channel == "msedge"


@pytest.mark.anyio
@respx.mock
async def test_fetcher_treats_fmkorea_security_page_as_blocked_without_browser_fallback():
    respx.get("https://www.fmkorea.com/stock").mock(
        return_value=httpx.Response(
            430,
            text="<html><title>에펨코리아 보안 시스템</title><body>보안 시스템</body></html>",
        )
    )

    with pytest.raises(SourceBlockedError, match="430"):
        await BrowserCapableFetcher(user_agent="test").fetch_html("https://www.fmkorea.com/stock")


@pytest.mark.anyio
@respx.mock
async def test_fetcher_treats_fmkorea_security_html_as_blocked_without_browser_fallback():
    respx.get("https://www.fmkorea.com/stock").mock(
        return_value=httpx.Response(
            200,
            text="<html><title>에펨코리아 보안 시스템</title><body>보안 시스템</body></html>",
        )
    )

    with pytest.raises(SourceBlockedError, match="block page"):
        await BrowserCapableFetcher(user_agent="test").fetch_html("https://www.fmkorea.com/stock")


@pytest.mark.anyio
@respx.mock
async def test_fetcher_can_fetch_browser_html_directly(monkeypatch):
    fetcher = BrowserCapableFetcher(user_agent="test")
    browser_urls = []

    async def fake_browser_result(url: str):
        browser_urls.append(url)
        from youbuyfirst_pipeline.crawlers.base import FetchResult

        return FetchResult(url=url, html="<html><body>browser rendered</body></html>", status_code=200)

    monkeypatch.setattr(fetcher, "_fetch_browser", fake_browser_result)

    result = await fetcher.fetch_browser_html("https://www.fmkorea.com/stock")

    assert result.html == "<html><body>browser rendered</body></html>"
    assert browser_urls == ["https://www.fmkorea.com/stock"]


@pytest.mark.anyio
@respx.mock
async def test_fetcher_treats_captcha_html_as_blocked_without_browser_fallback():
    respx.get("https://example.com/board").mock(
        return_value=httpx.Response(200, text="<html><title>captcha</title><body>verify you are human</body></html>")
    )

    with pytest.raises(SourceBlockedError, match="CAPTCHA"):
        await BrowserCapableFetcher(user_agent="test").fetch_html("https://example.com/board")
