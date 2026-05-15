from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from youbuyfirst_pipeline.models import Instrument

FMKOREA_STOCK_BOARD_URL = "https://www.fmkorea.com/stock"


class CrawlTargetKind(str, Enum):
    STOCK_BOARD = "stock-board"
    COMMUNITY_BOARD = "community-board"


@dataclass(frozen=True)
class CrawlTarget:
    source: str
    target_id: str
    kind: CrawlTargetKind
    priority: int = 100
    label: str = ""
    market: str | None = None
    symbol: str | None = None
    url: str | None = None

    def __post_init__(self) -> None:
        normalized_source = self.source.strip().upper()
        if not normalized_source:
            raise ValueError("source is required")
        if self.priority < 0:
            raise ValueError("priority must be zero or greater")
        object.__setattr__(self, "source", normalized_source)
        object.__setattr__(self, "kind", CrawlTargetKind(self.kind))
        object.__setattr__(self, "target_id", self.target_id.strip())
        if not self.target_id:
            raise ValueError("target_id is required")

    @classmethod
    def stock_board(
        cls,
        source: str,
        market: str,
        symbol: str,
        priority: int = 100,
        label: str | None = None,
    ) -> CrawlTarget:
        normalized_source = source.strip().upper()
        normalized_market = market.strip().upper()
        normalized_symbol = symbol.strip().upper()
        if not normalized_market:
            raise ValueError("market is required for stock-board targets")
        if not normalized_symbol:
            raise ValueError("symbol is required for stock-board targets")
        return cls(
            source=normalized_source,
            target_id=f"{normalized_source}:{normalized_market}:{normalized_symbol}",
            kind=CrawlTargetKind.STOCK_BOARD,
            priority=priority,
            label=label or f"{normalized_source} {normalized_market}:{normalized_symbol}",
            market=normalized_market,
            symbol=normalized_symbol,
        )

    @classmethod
    def community_board(
        cls,
        source: str,
        url: str | None = None,
        priority: int = 200,
        label: str | None = None,
    ) -> CrawlTarget:
        normalized_source = source.strip().upper()
        return cls(
            source=normalized_source,
            target_id=f"{normalized_source}:community-board",
            kind=CrawlTargetKind.COMMUNITY_BOARD,
            priority=priority,
            label=label or f"{normalized_source} community board",
            url=url,
        )


def default_crawl_targets(
    instruments: Iterable[Instrument],
    naver_stock_codes: Iterable[str] | None = None,
    fmkorea_url: str | None = None,
) -> list[CrawlTarget]:
    if naver_stock_codes is None:
        naver_codes = [instrument.symbol for instrument in instruments if instrument.market.upper() == "KR"]
    else:
        naver_codes = list(naver_stock_codes)

    targets = [
        CrawlTarget.stock_board("NAVER", market="KR", symbol=code)
        for code in _unique_non_empty(naver_codes)
    ]
    targets.append(
        CrawlTarget.community_board(
            "FMKOREA",
            url=fmkorea_url or FMKOREA_STOCK_BOARD_URL,
            priority=200,
            label="FMKOREA stock board",
        )
    )
    return targets


def _unique_non_empty(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        normalized = value.strip().upper()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique
