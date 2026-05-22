from datetime import date, datetime, timezone
from decimal import Decimal

from youbuyfirst_pipeline.market_investor_flows import (
    InvestorFlowLeg,
    InvestorFlowSnapshot,
    MarketInvestorFlowProvider,
    NaverFinanceInvestorFlowClient,
)


class _FakeInvestorFlowClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, date]] = []

    def flow(self, code: str, trade_date: date) -> tuple[InvestorFlowLeg, InvestorFlowLeg, InvestorFlowLeg]:
        self.calls.append((code, trade_date))
        if self.fail:
            raise RuntimeError("provider failed")
        return (
            InvestorFlowLeg(net_amount=Decimal("125000000000"), net_volume=1700000),
            InvestorFlowLeg(net_amount=Decimal("-90000000000"), net_volume=-1100000),
            InvestorFlowLeg(net_amount=Decimal("-35000000000"), net_volume=-600000),
        )


class _FakeKoreaMetadataProvider:
    def resolve(self, symbol: str):
        return type(
            "Metadata",
            (),
            {
                "symbol": symbol,
                "name": "Samsung Electronics",
                "market": "KR",
                "currency": "KRW",
            },
        )()


def test_market_investor_flow_provider_builds_previous_day_contract():
    client = _FakeInvestorFlowClient()
    provider = MarketInvestorFlowProvider(
        flow_client=client,
        metadata_provider=_FakeKoreaMetadataProvider(),
    )

    snapshot = provider.snapshot(
        "005930.KS",
        trade_date=date(2026, 5, 21),
        now=datetime(2026, 5, 22, 1, 0, tzinfo=timezone.utc),
    )

    assert client.calls == [("005930", date(2026, 5, 21))]
    assert snapshot.to_api_dict() == {
        "symbol": "005930.KS",
        "name": "Samsung Electronics",
        "market": "KR",
        "currency": "KRW",
        "tradeDate": "2026-05-21",
        "provider": "pykrx",
        "sourceLabel": "KRX investor trading by date via pykrx",
        "delayLabel": "Previous trading day investor flow",
        "asOf": "2026-05-21T00:00:00Z",
        "stale": False,
        "dataStatus": "OK",
        "individual": {"netAmount": 125000000000, "netVolume": 1700000, "derived": False},
        "foreign": {"netAmount": -90000000000, "netVolume": -1100000, "derived": False},
        "institution": {"netAmount": -35000000000, "netVolume": -600000, "derived": False},
    }


def test_market_investor_flow_provider_builds_recent_history_latest_first():
    client = _FakeInvestorFlowClient()
    provider = MarketInvestorFlowProvider(
        flow_client=client,
        metadata_provider=_FakeKoreaMetadataProvider(),
    )

    snapshots = provider.snapshots(
        ["005930.KS"],
        trade_date=date(2026, 5, 21),
        limit=3,
        now=datetime(2026, 5, 22, 1, 0, tzinfo=timezone.utc),
    )

    assert client.calls == [
        ("005930", date(2026, 5, 21)),
        ("005930", date(2026, 5, 20)),
        ("005930", date(2026, 5, 19)),
    ]
    assert [snapshot.trade_date for snapshot in snapshots] == [
        date(2026, 5, 21),
        date(2026, 5, 20),
        date(2026, 5, 19),
    ]
    assert all(snapshot.data_status == "OK" for snapshot in snapshots)


def test_market_investor_flow_provider_skips_provider_errors_without_fake_zero_rows():
    provider = MarketInvestorFlowProvider(
        flow_client=_FakeInvestorFlowClient(fail=True),
        metadata_provider=_FakeKoreaMetadataProvider(),
    )

    snapshots = provider.snapshots(
        ["005930.KS"],
        trade_date=date(2026, 5, 21),
        limit=3,
        now=datetime(2026, 5, 22, 1, 0, tzinfo=timezone.utc),
    )

    assert snapshots == []


def test_naver_finance_investor_flow_client_parses_volume_history_with_residual_individual():
    html = """
    <html><body>
      <table><tr><td>ignore</td></tr></table>
      <table>
        <thead>
          <tr>
            <th>날짜</th><th>종가</th><th>전일비</th><th>등락률</th><th>거래량</th>
            <th>기관순매매량</th><th>외국인순매매량</th><th>외국인보유주수</th><th>외국인보유율</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>2026.05.21</td><td>78,500</td><td>하락 100</td><td>-0.13%</td><td>1,291,447</td>
            <td>44,087</td><td>5,607</td><td>712,123</td><td>6.85%</td>
          </tr>
          <tr>
            <td>2026.05.20</td><td>78,600</td><td>상승 14,700</td><td>23.00%</td><td>2,943,189</td>
            <td>102,516</td><td>-52,011</td><td>716,689</td><td>6.89%</td>
          </tr>
        </tbody>
      </table>
    </body></html>
    """
    requested_urls: list[str] = []

    def fetcher(url: str) -> str:
        requested_urls.append(url)
        return html

    client = NaverFinanceInvestorFlowClient(fetcher=fetcher)

    rows = client.history("001820", end_date=date(2026, 5, 21), limit=2)

    assert requested_urls == ["https://finance.naver.com/item/frgn.nhn?code=001820&page=1"]
    assert [row.trade_date for row in rows] == [date(2026, 5, 21), date(2026, 5, 20)]
    latest = rows[0]
    assert latest.foreign == InvestorFlowLeg(net_amount=None, net_volume=5607)
    assert latest.institution == InvestorFlowLeg(net_amount=None, net_volume=44087)
    assert latest.individual == InvestorFlowLeg(net_amount=None, net_volume=-49694, derived=True)


def test_market_investor_flow_provider_uses_naver_history_rows_with_partial_source_labels():
    html = """
    <table>
      <tr>
        <th>날짜</th><th>종가</th><th>전일비</th><th>등락률</th><th>거래량</th>
        <th>기관순매매량</th><th>외국인순매매량</th><th>외국인보유주수</th><th>외국인보유율</th>
      </tr>
      <tr>
        <td>2026.05.21</td><td>299,500</td><td>상승 23,500</td><td>8.51%</td><td>36,168,689</td>
        <td>2,608,486</td><td>3,672,423</td><td>2,829,121,739</td><td>48.39%</td>
      </tr>
    </table>
    """
    provider = MarketInvestorFlowProvider(
        flow_client=NaverFinanceInvestorFlowClient(fetcher=lambda _url: html),
        metadata_provider=_FakeKoreaMetadataProvider(),
    )

    snapshots = provider.history(
        "005930.KS",
        trade_date=date(2026, 5, 21),
        limit=1,
        now=datetime(2026, 5, 22, 1, 0, tzinfo=timezone.utc),
    )

    assert [snapshot.to_api_dict() for snapshot in snapshots] == [
        {
            "symbol": "005930.KS",
            "name": "Samsung Electronics",
            "market": "KR",
            "currency": "KRW",
            "tradeDate": "2026-05-21",
            "provider": "naver-finance",
            "sourceLabel": "Naver Finance investor trend; individual is residual from foreign and institution",
            "delayLabel": "Previous trading day investor trend",
            "asOf": "2026-05-21T00:00:00Z",
            "stale": False,
            "dataStatus": "OK",
            "individual": {"netAmount": None, "netVolume": -6280909, "derived": True},
            "foreign": {"netAmount": None, "netVolume": 3672423, "derived": False},
            "institution": {"netAmount": None, "netVolume": 2608486, "derived": False},
        }
    ]


def test_investor_flow_snapshot_request_payload_excludes_stale():
    snapshot = InvestorFlowSnapshot(
        symbol="005930.KS",
        name="Samsung Electronics",
        market="KR",
        currency="KRW",
        trade_date=date(2026, 5, 21),
        provider="pykrx",
        source_label="KRX investor trading by date via pykrx",
        delay_label="Previous trading day investor flow",
        as_of=datetime(2026, 5, 21, tzinfo=timezone.utc),
        stale=False,
        data_status="OK",
        individual=InvestorFlowLeg(Decimal("1"), 2),
        foreign=InvestorFlowLeg(Decimal("-3"), -4),
        institution=InvestorFlowLeg(Decimal("5"), 6),
    )

    payload = snapshot.to_request_dict()

    assert "stale" not in payload
    assert payload["individual"] == {"netAmount": 1, "netVolume": 2, "derived": False}
