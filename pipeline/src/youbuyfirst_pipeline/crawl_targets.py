from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DCINSIDE_REALESTATE_BOARD_URL = "https://gall.dcinside.com/board/lists/?id=immovables"
PPOMPPU_REALESTATE_BOARD_URL = "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1"
FMKOREA_REALESTATE_BOARD_URL = "https://www.fmkorea.com/realestate"
NAVER_CAFE_PUBLIC_SEARCH_URL = "serpapi://google?domain=cafe.naver.com"
DAUM_CAFE_PUBLIC_SEARCH_URL = "serpapi://google?domain=cafe.daum.net"
CLIEN_PARK_BOARD_URL = "https://m.clien.net/service/board/park"
COOK82_FREEBOARD_URL = "https://www.82cook.com/entiz/enti.php?bn=15"
DEALAGORA_COMMUNITY_BOARD_URL = "https://dealagora.co.kr/subpage/bbs/borad.php?cate=&code=community&order=new"
THEQOO_SQUARE_BOARD_URL = "https://theqoo.net/square"
MLBPARK_BULLPEN_BOARD_URL = "https://mlbpark.donga.com/mp/b.php?m=list&b=bullpen"
NATEPANN_TALK_BOARD_URL = "https://pann.nate.com/talk/c20002"
TODAYHUMOR_ECONOMY_BOARD_URL = "https://www.todayhumor.co.kr/board/list.php?table=economy"
TODAYHUMOR_FREEBOARD_URL = "https://www.todayhumor.co.kr/board/list.php?table=freeboard"
RULIWEB_COMMUNITY_BOARD_URL = "https://bbs.ruliweb.com/community/board/300143"
BOBAEDREAM_FREEBOARD_URL = "https://www.bobaedream.co.kr/list?code=freeb"
INSTIZ_NAME_BOARD_URL = "https://www.instiz.net/name"
SLRCLUB_FREE_BOARD_URL = "https://www.slrclub.com/bbs/zboard.php?id=free"
INVEN_WEBZINE_BOARD_URL = "https://www.inven.co.kr/board/webzine/2097"


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
        CommunityBoardRegistryEntry(
            source="FMKOREA",
            board_id="realestate",
            display_name="FMKOREA real estate board",
            domain_scope="KR_REALESTATE",
            latest_url=FMKOREA_REALESTATE_BOARD_URL,
            latest_priority=220,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="NAVER_CAFE",
            board_id="public_search",
            display_name="Naver Cafe public real-estate search discovery",
            domain_scope="KR_REALESTATE",
            latest_url=NAVER_CAFE_PUBLIC_SEARCH_URL,
            latest_priority=230,
            enabled_by_default=False,
            crawl_policy="realestate-cafe-public-search",
        ),
        CommunityBoardRegistryEntry(
            source="DAUM_CAFE",
            board_id="public_search",
            display_name="Daum Cafe public real-estate search discovery",
            domain_scope="KR_REALESTATE",
            latest_url=DAUM_CAFE_PUBLIC_SEARCH_URL,
            latest_priority=231,
            enabled_by_default=False,
            crawl_policy="realestate-cafe-public-search",
        ),
        CommunityBoardRegistryEntry(
            source="CLIEN",
            board_id="park",
            display_name="Clien park real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=CLIEN_PARK_BOARD_URL,
            latest_priority=300,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="COOK82",
            board_id="freeboard",
            display_name="82cook freeboard real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=COOK82_FREEBOARD_URL,
            latest_priority=300,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="DEALAGORA",
            board_id="community",
            display_name="Dealagora real-estate community board",
            domain_scope="KR_REALESTATE",
            latest_url=DEALAGORA_COMMUNITY_BOARD_URL,
            latest_priority=240,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="THEQOO",
            board_id="square",
            display_name="Theqoo square real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=THEQOO_SQUARE_BOARD_URL,
            latest_priority=310,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="MLBPARK",
            board_id="bullpen",
            display_name="MLBPark bullpen real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=MLBPARK_BULLPEN_BOARD_URL,
            latest_priority=320,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="NATEPANN",
            board_id="talk",
            display_name="Nate Pann talk real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=NATEPANN_TALK_BOARD_URL,
            latest_priority=330,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="TODAYHUMOR",
            board_id="economy",
            display_name="TodayHumor economy real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=TODAYHUMOR_ECONOMY_BOARD_URL,
            latest_priority=340,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="TODAYHUMOR",
            board_id="freeboard",
            display_name="TodayHumor freeboard real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=TODAYHUMOR_FREEBOARD_URL,
            latest_priority=341,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="RULIWEB",
            board_id="community",
            display_name="Ruliweb community real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=RULIWEB_COMMUNITY_BOARD_URL,
            latest_priority=350,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="BOBAEDREAM",
            board_id="freeb",
            display_name="Bobaedream freeboard real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=BOBAEDREAM_FREEBOARD_URL,
            latest_priority=360,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="INSTIZ",
            board_id="name",
            display_name="Instiz name real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=INSTIZ_NAME_BOARD_URL,
            latest_priority=370,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="SLRCLUB",
            board_id="free",
            display_name="SLRClub freeboard real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=SLRCLUB_FREE_BOARD_URL,
            latest_priority=380,
            enabled_by_default=False,
        ),
        CommunityBoardRegistryEntry(
            source="INVEN",
            board_id="webzine2097",
            display_name="Inven webzine freeboard real-estate keyword board",
            domain_scope="KR_REALESTATE",
            latest_url=INVEN_WEBZINE_BOARD_URL,
            latest_priority=390,
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
