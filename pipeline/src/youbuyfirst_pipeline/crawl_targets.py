from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DCINSIDE_REALESTATE_BOARD_URL = "https://gall.dcinside.com/board/lists/?id=immovables"
PPOMPPU_REALESTATE_BOARD_URL = "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1"


class CrawlTargetKind(str, Enum):
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
        target_id = f"{normalized_source}:{normalized_board_id}" if normalized_board_id else f"{normalized_source}:community-board"
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
    domain_scope: str
    latest_url: str
    latest_priority: int
    enabled_by_default: bool = True
    crawl_policy: str = "realestate-general-board-latest"
    diffusion_boards: tuple[DiffusionBoardRegistryEntry, ...] = ()


def real_estate_community_board_registry() -> tuple[CommunityBoardRegistryEntry, ...]:
    return (
        CommunityBoardRegistryEntry(
            source="PPOMPPU",
            board_id="house",
            display_name="PPOMPPU real estate forum",
            domain_scope="KR_REALESTATE",
            latest_url=PPOMPPU_REALESTATE_BOARD_URL,
            latest_priority=200,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="DCINSIDE",
            board_id="immovables",
            display_name="DCInside real estate gallery",
            domain_scope="KR_REALESTATE",
            latest_url=DCINSIDE_REALESTATE_BOARD_URL,
            latest_priority=210,
            enabled_by_default=False,
        ),
    )


def real_estate_seed_crawl_targets() -> list[CrawlTarget]:
    return [
        CrawlTarget.community_board(
            entry.source,
            board_id=entry.board_id,
            url=entry.latest_url,
            priority=entry.latest_priority,
            label=entry.display_name,
            crawl_interval_seconds=3600,
        )
        for entry in real_estate_community_board_registry()
    ]


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
