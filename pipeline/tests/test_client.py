from youbuyfirst_pipeline.client import SpringIngestionClient


class _Response:
    def raise_for_status(self) -> None:
        return None


class _FakeHttpxClient:
    posts: list[dict] = []

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __enter__(self) -> "_FakeHttpxClient":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def post(self, url: str, json: dict) -> _Response:
        self.posts.append({"url": url, "json": json, "timeout": self.timeout})
        return _Response()


class _CandleSet:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def to_request_dict(self) -> dict:
        return {"symbol": self.symbol, "bars": []}


def test_spring_client_batches_chart_candle_pushes_to_keep_internal_requests_bounded(monkeypatch):
    _FakeHttpxClient.posts = []
    monkeypatch.setattr("youbuyfirst_pipeline.client.httpx.Client", _FakeHttpxClient)
    client = SpringIngestionClient(
        "http://backend:8080",
        timeout_seconds=60,
        chart_candle_batch_size=2,
    )

    client.publish_chart_candles([
        _CandleSet("AAPL"),
        _CandleSet("MSFT"),
        _CandleSet("NVDA"),
        _CandleSet("TSLA"),
        _CandleSet("005930.KS"),
    ])

    assert [post["json"]["items"] for post in _FakeHttpxClient.posts] == [
        [{"symbol": "AAPL", "bars": []}, {"symbol": "MSFT", "bars": []}],
        [{"symbol": "NVDA", "bars": []}, {"symbol": "TSLA", "bars": []}],
        [{"symbol": "005930.KS", "bars": []}],
    ]
    assert {post["timeout"] for post in _FakeHttpxClient.posts} == {60}


def test_spring_client_defaults_to_longer_timeout_for_market_batches():
    assert SpringIngestionClient("http://backend:8080").timeout_seconds == 60.0
