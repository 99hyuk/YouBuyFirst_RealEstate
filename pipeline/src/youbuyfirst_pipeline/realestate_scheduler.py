from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.realestate_public_data import (
    MolitRealEstatePublicDataClient,
    build_molit_public_data_client_from_env,
    collect_molit_real_estate_market_facts_from_data_targets,
)

logger = logging.getLogger(__name__)


class RealEstateMarketFactsProvider(Protocol):
    def fetch_apt_trades(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        ...

    def fetch_apt_rents(self, lawd_code, deal_ym, page_no=1, num_rows=100, now=None):
        ...


class RealEstateMarketFactsClient(Protocol):
    def list_real_estate_market_data_targets(self, enabled: bool | None = True) -> list[dict]:
        ...

    def publish_real_estate_market_facts(self, facts) -> None:
        ...


@dataclass(frozen=True)
class RealEstateMarketFactsRefreshResult:
    status: str
    target_count: int
    fact_count: int


class RealEstateMarketFactsRefreshJob:
    def __init__(
            self,
            provider: RealEstateMarketFactsProvider,
            client: RealEstateMarketFactsClient,
            deal_ym: str,
            clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.provider = provider
        self.client = client
        self.deal_ym = deal_ym
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def run_once(self) -> RealEstateMarketFactsRefreshResult:
        try:
            targets = self.client.list_real_estate_market_data_targets(enabled=True)
        except Exception as exc:
            logger.warning("real-estate market facts refresh skipped; backend target registry unavailable: %s", exc)
            return RealEstateMarketFactsRefreshResult(status="CLIENT_ERROR", target_count=0, fact_count=0)

        try:
            facts = collect_molit_real_estate_market_facts_from_data_targets(
                self.provider,
                targets,
                deal_ym=self.deal_ym,
                now=self.clock(),
            )
        except Exception:
            logger.exception("real-estate market facts refresh failed")
            return RealEstateMarketFactsRefreshResult(
                status="PROVIDER_ERROR",
                target_count=len(targets),
                fact_count=0,
            )

        if facts:
            self.client.publish_real_estate_market_facts(facts)

        result = RealEstateMarketFactsRefreshResult(
            status="OK",
            target_count=len(targets),
            fact_count=len(facts),
        )
        logger.info(
            "real-estate market facts refresh finished; status=%s target_count=%s fact_count=%s deal_ym=%s",
            result.status,
            result.target_count,
            result.fact_count,
            self.deal_ym,
        )
        return result


def build_real_estate_market_facts_refresh_job(
        *,
        client: SpringIngestionClient,
        deal_ym: str,
        provider: MolitRealEstatePublicDataClient | None = None,
) -> RealEstateMarketFactsRefreshJob:
    return RealEstateMarketFactsRefreshJob(
        provider=provider or build_molit_public_data_client_from_env(),
        client=client,
        deal_ym=deal_ym,
    )
