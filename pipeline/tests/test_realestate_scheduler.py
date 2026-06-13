from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from youbuyfirst_pipeline.realestate_scheduler import RealEstateMarketFactsRefreshJob
from youbuyfirst_pipeline.scheduler import configure_scheduler


class _MolitProvider:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = []

    def fetch_apt_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        self.calls.append(("trade", lawd_code, deal_ym, now))
        if self.fail:
            raise RuntimeError("provider failed")
        return [f"trade:{lawd_code}:{deal_ym}"]

    def fetch_apt_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        self.calls.append(("rent", lawd_code, deal_ym, now))
        if self.fail:
            raise RuntimeError("provider failed")
        return [f"rent:{lawd_code}:{deal_ym}"]


class _RealEstateClient:
    def __init__(self, fail_targets: bool = False) -> None:
        self.fail_targets = fail_targets
        self.pushed_batches = []

    def list_real_estate_market_data_targets(self, enabled=True):
        if self.fail_targets:
            raise RuntimeError("backend unavailable")
        return [
            {
                "targetId": "region-11110",
                "provider": "molit",
                "providerDataset": "molit_apt_trade",
                "lawdCode": "11110",
                "enabled": True,
            },
            {
                "targetId": "region-11110",
                "provider": "molit",
                "providerDataset": "molit_apt_rent",
                "lawdCode": "11110",
                "enabled": True,
            },
        ]

    def publish_real_estate_market_facts(self, facts):
        self.pushed_batches.append(list(facts))


class _Pipeline:
    async def run_once(self) -> list[str]:
        return []


def test_real_estate_market_facts_refresh_job_collects_backend_targets_and_pushes_facts():
    provider = _MolitProvider()
    client = _RealEstateClient()
    now = datetime(2026, 6, 11, 1, 0, tzinfo=timezone.utc)
    job = RealEstateMarketFactsRefreshJob(
        provider=provider,
        client=client,
        deal_ym="202606",
        clock=lambda: now,
    )

    result = job.run_once()

    assert result.status == "OK"
    assert result.target_count == 2
    assert result.fact_count == 2
    assert provider.calls == [
        ("trade", "11110", "202606", now),
        ("rent", "11110", "202606", now),
    ]
    assert client.pushed_batches == [["trade:11110:202606", "rent:11110:202606"]]


def test_real_estate_market_facts_refresh_job_reports_client_error_when_registry_is_unavailable():
    provider = _MolitProvider()
    client = _RealEstateClient(fail_targets=True)
    job = RealEstateMarketFactsRefreshJob(provider=provider, client=client, deal_ym="202606")

    result = job.run_once()

    assert result.status == "CLIENT_ERROR"
    assert result.target_count == 0
    assert result.fact_count == 0
    assert provider.calls == []
    assert client.pushed_batches == []


def test_real_estate_market_facts_refresh_job_reports_provider_error_without_push():
    provider = _MolitProvider(fail=True)
    client = _RealEstateClient()
    job = RealEstateMarketFactsRefreshJob(provider=provider, client=client, deal_ym="202606")

    result = job.run_once()

    assert result.status == "PROVIDER_ERROR"
    assert result.target_count == 2
    assert result.fact_count == 0
    assert client.pushed_batches == []


def test_configure_scheduler_registers_real_estate_market_facts_refresh_job():
    scheduler = AsyncIOScheduler(timezone="UTC")
    realestate_job = RealEstateMarketFactsRefreshJob(
        provider=_MolitProvider(),
        client=_RealEstateClient(),
        deal_ym="202606",
    )

    configure_scheduler(
        scheduler,
        pipeline=_Pipeline(),
        crawl_interval_minutes=30,
        realestate_market_facts_refresh_job=realestate_job,
        realestate_market_facts_interval_minutes=360,
    )

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert jobs["community-crawl"].trigger.interval.total_seconds() == 30 * 60
    assert jobs["realestate-market-facts-refresh"].trigger.interval.total_seconds() == 360 * 60
