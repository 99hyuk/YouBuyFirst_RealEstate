from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from youbuyfirst_pipeline.models import Instrument

FMKOREA_STOCK_BOARD_URL = "https://www.fmkorea.com/stock"
DCINSIDE_US_STOCK_BOARD_URL = "https://gall.dcinside.com/mini/board/lists/?id=nyse"
DCINSIDE_STOCK_BOARD_URL = "https://gall.dcinside.com/board/lists/?id=neostock"
DCINSIDE_KOREA_STOCK_BOARD_URL = "https://gall.dcinside.com/mini/board/lists/?id=koreastock"
PPOMPPU_STOCK_BOARD_URL = "https://www.ppomppu.co.kr/zboard/zboard.php?id=stock"


class CrawlTargetKind(str, Enum):
    STOCK_BOARD = "stock-board"
    COMMUNITY_BOARD = "community-board"
    GENERAL_BOARD_DIFFUSION = "general-board-diffusion"


@dataclass(frozen=True)
class CrawlTarget:
    source: str
    target_id: str
    kind: CrawlTargetKind
    priority: int = 100
    label: str = ""
    board_id: str | None = None
    market: str | None = None
    symbol: str | None = None
    url: str | None = None
    diffusion_type: str | None = None

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
        board_id: str | None = None,
        url: str | None = None,
        priority: int = 200,
        label: str | None = None,
    ) -> CrawlTarget:
        normalized_source = source.strip().upper()
        normalized_board_id = board_id.strip() if board_id else None
        target_id = (
            f"{normalized_source}:{normalized_board_id}"
            if normalized_board_id and not (normalized_source == "FMKOREA" and normalized_board_id == "stock")
            else f"{normalized_source}:community-board"
        )
        return cls(
            source=normalized_source,
            target_id=target_id,
            kind=CrawlTargetKind.COMMUNITY_BOARD,
            priority=priority,
            label=label or f"{normalized_source} {normalized_board_id or 'community'} board",
            board_id=normalized_board_id,
            url=url,
        )

    @classmethod
    def community_diffusion_board(
        cls,
        source: str,
        board_id: str,
        diffusion_type: str,
        url: str,
        priority: int = 260,
        label: str | None = None,
    ) -> CrawlTarget:
        normalized_source = source.strip().upper()
        normalized_board_id = board_id.strip()
        normalized_diffusion_type = diffusion_type.strip().lower()
        if not normalized_board_id:
            raise ValueError("board_id is required for diffusion targets")
        if not normalized_diffusion_type:
            raise ValueError("diffusion_type is required for diffusion targets")
        if not url or not url.strip():
            raise ValueError("url is required for diffusion targets")
        return cls(
            source=normalized_source,
            target_id=f"{normalized_source}:{normalized_board_id}:diffusion:{normalized_diffusion_type}",
            kind=CrawlTargetKind.GENERAL_BOARD_DIFFUSION,
            priority=priority,
            label=label or f"{normalized_source} {normalized_board_id} {normalized_diffusion_type} diffusion",
            board_id=normalized_board_id,
            url=url.strip(),
            diffusion_type=normalized_diffusion_type,
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
            board_id="stock",
            url=fmkorea_url or FMKOREA_STOCK_BOARD_URL,
            priority=200,
            label="FMKOREA stock board",
        )
    )
    targets.extend(
        [
            CrawlTarget.community_board(
                "DCINSIDE",
                board_id="nyse",
                url=DCINSIDE_US_STOCK_BOARD_URL,
                priority=210,
                label="DCInside US stock mini gallery",
            ),
            CrawlTarget.community_board(
                "DCINSIDE",
                board_id="neostock",
                url=DCINSIDE_STOCK_BOARD_URL,
                priority=220,
                label="DCInside stock gallery",
            ),
            CrawlTarget.community_board(
                "DCINSIDE",
                board_id="koreastock",
                url=DCINSIDE_KOREA_STOCK_BOARD_URL,
                priority=230,
                label="DCInside domestic stock mini gallery",
            ),
            CrawlTarget.community_board(
                "PPOMPPU",
                board_id="stock",
                url=PPOMPPU_STOCK_BOARD_URL,
                priority=240,
                label="PPOMPPU stock forum",
            ),
        ]
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
