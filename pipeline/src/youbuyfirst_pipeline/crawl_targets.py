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
    crawl_interval_seconds: int = 1800
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
        if self.crawl_interval_seconds <= 0:
            raise ValueError("crawl_interval_seconds must be greater than zero")
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
        crawl_interval_seconds: int = 1800,
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
            crawl_interval_seconds=crawl_interval_seconds,
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
        crawl_interval_seconds: int = 1800,
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
            crawl_interval_seconds=crawl_interval_seconds,
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
        crawl_interval_seconds: int = 1800,
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
            crawl_interval_seconds=crawl_interval_seconds,
            label=label or f"{normalized_source} {normalized_board_id} {normalized_diffusion_type} diffusion",
            board_id=normalized_board_id,
            url=url.strip(),
            diffusion_type=normalized_diffusion_type,
        )


@dataclass(frozen=True)
class StockBoardTargetCandidate:
    symbol: str
    reason: str
    priority: int = 120
    crawl_interval_seconds: int = 3600
    label: str | None = None


NAVER_STOCK_BOARD_TARGET_HARD_LIMIT = 30
DEFAULT_NAVER_STOCK_BOARD_TARGET_LIMIT = 25

_DEFAULT_NAVER_STOCK_BOARD_CANDIDATES: tuple[StockBoardTargetCandidate, ...] = (
    StockBoardTargetCandidate("005930", reason="core-large-cap", label="Samsung Electronics board"),
    StockBoardTargetCandidate("000660", reason="core-large-cap", label="SK Hynix board"),
    StockBoardTargetCandidate("069500", reason="core-etf", label="KODEX 200 board"),
    StockBoardTargetCandidate("454910", reason="core-etf", label="KODEX KOSDAQ Global board"),
    StockBoardTargetCandidate("035420", reason="core-large-cap", label="NAVER board"),
    StockBoardTargetCandidate("005380", reason="core-large-cap", label="Hyundai Motor board"),
    StockBoardTargetCandidate("207940", reason="core-large-cap", label="Samsung Biologics board"),
    StockBoardTargetCandidate("068270", reason="core-large-cap", label="Celltrion board"),
    StockBoardTargetCandidate("105560", reason="core-large-cap", label="KB Financial board"),
    StockBoardTargetCandidate("055550", reason="core-large-cap", label="Shinhan Financial board"),
    StockBoardTargetCandidate("035720", reason="core-large-cap", label="Kakao board"),
    StockBoardTargetCandidate("051910", reason="core-large-cap", label="LG Chem board"),
    StockBoardTargetCandidate("006400", reason="core-large-cap", label="Samsung SDI board"),
    StockBoardTargetCandidate("005490", reason="core-large-cap", label="POSCO Holdings board"),
    StockBoardTargetCandidate("042700", reason="core-large-cap", label="Hanmi Semiconductor board"),
    StockBoardTargetCandidate("086520", reason="core-large-cap", label="Ecopro board"),
    StockBoardTargetCandidate("247540", reason="core-large-cap", label="Ecopro BM board"),
    StockBoardTargetCandidate("196170", reason="core-large-cap", label="Alteogen board"),
    StockBoardTargetCandidate("035900", reason="core-large-cap", label="JYP Ent. board"),
    StockBoardTargetCandidate("133690", reason="core-etf", label="TIGER NASDAQ 100 board"),
    StockBoardTargetCandidate("102110", reason="core-etf", label="TIGER 200 board"),
    StockBoardTargetCandidate("252670", reason="core-etf", label="KODEX 200 Futures Inverse 2X board"),
    StockBoardTargetCandidate("251340", reason="core-etf", label="KODEX KOSDAQ150 Futures Inverse board"),
    StockBoardTargetCandidate("229200", reason="core-etf", label="KODEX KOSDAQ150 board"),
    StockBoardTargetCandidate("122630", reason="core-etf", label="KODEX Leverage board"),
)


@dataclass(frozen=True)
class DiffusionBoardRegistryEntry:
    diffusion_type: str
    url: str | None
    enabled_by_default: bool = False
    priority_offset: int = 50
    note: str = ""


@dataclass(frozen=True)
class CommunityBoardRegistryEntry:
    source: str
    board_id: str
    display_name: str
    market_scope: str
    latest_url: str
    latest_priority: int
    enabled_by_default: bool = True
    crawl_policy: str = "general-board-latest"
    diffusion_boards: tuple[DiffusionBoardRegistryEntry, ...] = ()


def community_board_registry(fmkorea_url: str | None = None) -> tuple[CommunityBoardRegistryEntry, ...]:
    return (
        CommunityBoardRegistryEntry(
            source="FMKOREA",
            board_id="stock",
            display_name="FMKOREA stock board",
            market_scope="KR_US",
            latest_url=fmkorea_url or FMKOREA_STOCK_BOARD_URL,
            latest_priority=200,
            diffusion_boards=(
                DiffusionBoardRegistryEntry(
                    diffusion_type="popular",
                    url=None,
                    enabled_by_default=False,
                    note="Verify FMKOREA popular-board URL before enabling.",
                ),
            ),
        ),
        CommunityBoardRegistryEntry(
            source="DCINSIDE",
            board_id="nyse",
            display_name="DCInside US stock gallery",
            market_scope="US",
            latest_url=DCINSIDE_US_STOCK_BOARD_URL,
            latest_priority=210,
            diffusion_boards=(
                DiffusionBoardRegistryEntry(
                    diffusion_type="concept",
                    url="https://gall.dcinside.com/mini/board/lists/?id=nyse&exception_mode=recommend",
                    enabled_by_default=True,
                ),
            ),
        ),
        CommunityBoardRegistryEntry(
            source="DCINSIDE",
            board_id="neostock",
            display_name="DCInside stock gallery",
            market_scope="KR_GENERAL",
            latest_url=DCINSIDE_STOCK_BOARD_URL,
            latest_priority=220,
            diffusion_boards=(
                DiffusionBoardRegistryEntry(
                    diffusion_type="concept",
                    url="https://gall.dcinside.com/board/lists/?id=neostock&exception_mode=recommend",
                    enabled_by_default=True,
                ),
            ),
        ),
        CommunityBoardRegistryEntry(
            source="DCINSIDE",
            board_id="koreastock",
            display_name="DCInside domestic stock gallery",
            market_scope="KR",
            latest_url=DCINSIDE_KOREA_STOCK_BOARD_URL,
            latest_priority=230,
            diffusion_boards=(
                DiffusionBoardRegistryEntry(
                    diffusion_type="concept",
                    url="https://gall.dcinside.com/mini/board/lists/?id=koreastock&exception_mode=recommend",
                    enabled_by_default=True,
                ),
            ),
        ),
        CommunityBoardRegistryEntry(
            source="PPOMPPU",
            board_id="stock",
            display_name="PPOMPPU stock forum",
            market_scope="KR_US",
            latest_url=PPOMPPU_STOCK_BOARD_URL,
            latest_priority=240,
            diffusion_boards=(
                DiffusionBoardRegistryEntry(
                    diffusion_type="popular",
                    url=None,
                    enabled_by_default=False,
                    note="Verify PPOMPPU hot/popular category URL before enabling.",
                ),
            ),
        ),
    )


def default_crawl_targets(
    instruments: Iterable[Instrument],
    naver_stock_codes: Iterable[str] | None = None,
    naver_watchlist_codes: Iterable[str] | None = None,
    stock_board_target_limit: int = DEFAULT_NAVER_STOCK_BOARD_TARGET_LIMIT,
    fmkorea_url: str | None = None,
    extra_stock_board_candidates: Iterable[StockBoardTargetCandidate] | None = None,
) -> list[CrawlTarget]:
    _ = instruments
    watchlist_codes = _first_non_empty(naver_watchlist_codes, naver_stock_codes)

    targets = build_naver_stock_board_targets(
        watchlist_symbols=watchlist_codes,
        extra_candidates=extra_stock_board_candidates,
        max_targets=stock_board_target_limit,
    )
    community_entries = [
        entry for entry in community_board_registry(fmkorea_url=fmkorea_url)
        if entry.enabled_by_default
    ]
    for entry in community_entries:
        targets.append(
            CrawlTarget.community_board(
                entry.source,
                board_id=entry.board_id,
                url=entry.latest_url,
                priority=entry.latest_priority,
                label=entry.display_name,
            )
        )
    for entry in community_entries:
        targets.extend(_default_diffusion_targets(entry))
    return targets


def build_naver_stock_board_targets(
    watchlist_symbols: Iterable[str] | None = None,
    extra_candidates: Iterable[StockBoardTargetCandidate] | None = None,
    max_targets: int = DEFAULT_NAVER_STOCK_BOARD_TARGET_LIMIT,
) -> list[CrawlTarget]:
    target_limit = min(max(max_targets, 0), NAVER_STOCK_BOARD_TARGET_HARD_LIMIT)
    if target_limit == 0:
        return []

    candidates: list[StockBoardTargetCandidate] = []
    for symbol in watchlist_symbols or ():
        normalized_symbol = _normalize_naver_stock_code(symbol)
        if not normalized_symbol:
            continue
        candidates.append(
            StockBoardTargetCandidate(
                symbol=normalized_symbol,
                reason="watchlist",
                priority=80,
                crawl_interval_seconds=1800,
                label=f"NAVER watchlist KR:{normalized_symbol}",
            )
        )
    candidates.extend(extra_candidates or ())
    candidates.extend(_DEFAULT_NAVER_STOCK_BOARD_CANDIDATES)

    targets: list[CrawlTarget] = []
    seen_symbols: set[str] = set()
    for candidate in candidates:
        symbol = _normalize_naver_stock_code(candidate.symbol)
        if not symbol or symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)
        targets.append(
            CrawlTarget.stock_board(
                "NAVER",
                market="KR",
                symbol=symbol,
                priority=candidate.priority,
                label=candidate.label or f"NAVER {candidate.reason} KR:{symbol}",
                crawl_interval_seconds=candidate.crawl_interval_seconds,
            )
        )
        if len(targets) >= target_limit:
            break
    return targets


def _default_diffusion_targets(entry: CommunityBoardRegistryEntry) -> list[CrawlTarget]:
    targets: list[CrawlTarget] = []
    for diffusion_board in entry.diffusion_boards:
        if not diffusion_board.enabled_by_default or not diffusion_board.url:
            continue
        targets.append(
            CrawlTarget.community_diffusion_board(
                entry.source,
                board_id=entry.board_id,
                diffusion_type=diffusion_board.diffusion_type,
                url=diffusion_board.url,
                priority=entry.latest_priority + diffusion_board.priority_offset,
                label=f"{entry.display_name} {diffusion_board.diffusion_type}",
            )
        )
    return targets


def _normalize_naver_stock_code(value: str) -> str:
    normalized = value.strip().upper()
    if normalized.startswith("KR:"):
        normalized = normalized.removeprefix("KR:")
    for suffix in (".KS", ".KQ", ".KR"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized.strip()


def _first_non_empty(*values: Iterable[str] | None) -> list[str] | None:
    for value in values:
        if value is None:
            continue
        items = [item for item in value if item.strip()]
        if items:
            return items
    return None
