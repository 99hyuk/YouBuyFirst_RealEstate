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
async def test_fetcher_treats_captcha_html_as_blocked_without_browser_fallback():
    respx.get("https://example.com/board").mock(
        return_value=httpx.Response(200, text="<html><title>captcha</title><body>verify you are human</body></html>")
    )

    with pytest.raises(SourceBlockedError, match="CAPTCHA"):
        await BrowserCapableFetcher(user_agent="test").fetch_html("https://example.com/board")
