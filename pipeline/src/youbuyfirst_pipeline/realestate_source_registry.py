from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from youbuyfirst_pipeline.crawl_targets import (
    BOBAEDREAM_FREEBOARD_URL,
    CLIEN_PARK_BOARD_URL,
    COOK82_FREEBOARD_URL,
    DCINSIDE_REALESTATE_BOARD_URL,
    DEALAGORA_COMMUNITY_BOARD_URL,
    DAUM_CAFE_PUBLIC_SEARCH_URL,
    FMKOREA_REALESTATE_BOARD_URL,
    INSTIZ_NAME_BOARD_URL,
    INVEN_WEBZINE_BOARD_URL,
    MLBPARK_BULLPEN_BOARD_URL,
    NATEPANN_TALK_BOARD_URL,
    NAVER_CAFE_PUBLIC_SEARCH_URL,
    PPOMPPU_REALESTATE_BOARD_URL,
    RULIWEB_COMMUNITY_BOARD_URL,
    SLRCLUB_FREE_BOARD_URL,
    THEQOO_SQUARE_BOARD_URL,
    TODAYHUMOR_ECONOMY_BOARD_URL,
    TODAYHUMOR_FREEBOARD_URL,
    CrawlTarget,
)
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicyRegistry,
    default_source_policy_registry,
)


_SUPPORTED_BOARD_SOURCES = {
    "DCINSIDE",
    "PPOMPPU",
    "FMKOREA",
    "NAVER_CAFE",
    "DAUM_CAFE",
    "CLIEN",
    "COOK82",
    "DEALAGORA",
    "THEQOO",
    "MLBPARK",
    "NATEPANN",
    "TODAYHUMOR",
    "RULIWEB",
    "BOBAEDREAM",
    "INSTIZ",
    "SLRCLUB",
    "INVEN",
}
_CRAWLABLE_CANDIDATE_POLICIES = {"enabled", "local-research-only", "public-http-candidate"}
_DEFAULT_ALLOWED_STORAGE = ["title", "contentSnippet", "url", "authorHash", "publishedAt", "contentHash"]
_KNOWN_SOURCE_TARGETS = {
    "ppomppu_house": {
        "source": "PPOMPPU",
        "boardId": "house",
        "url": PPOMPPU_REALESTATE_BOARD_URL,
        "priority": 200,
    },
    "dc_immovables": {
        "source": "DCINSIDE",
        "boardId": "immovables",
        "url": DCINSIDE_REALESTATE_BOARD_URL,
        "priority": 210,
    },
    "fmkorea_realestate": {
        "source": "FMKOREA",
        "boardId": "realestate",
        "url": FMKOREA_REALESTATE_BOARD_URL,
        "priority": 220,
    },
    "naver_cafe_public_search": {
        "source": "NAVER_CAFE",
        "boardId": "public_search",
        "url": NAVER_CAFE_PUBLIC_SEARCH_URL,
        "priority": 230,
    },
    "daum_cafe_public_search": {
        "source": "DAUM_CAFE",
        "boardId": "public_search",
        "url": DAUM_CAFE_PUBLIC_SEARCH_URL,
        "priority": 231,
    },
    "clien_park_realestate": {
        "source": "CLIEN",
        "boardId": "park",
        "url": CLIEN_PARK_BOARD_URL,
        "priority": 300,
    },
    "cook82_freeboard_realestate": {
        "source": "COOK82",
        "boardId": "freeboard",
        "url": COOK82_FREEBOARD_URL,
        "priority": 300,
    },
    "dealagora_community": {
        "source": "DEALAGORA",
        "boardId": "community",
        "url": DEALAGORA_COMMUNITY_BOARD_URL,
        "priority": 240,
    },
    "theqoo_square_realestate": {
        "source": "THEQOO",
        "boardId": "square",
        "url": THEQOO_SQUARE_BOARD_URL,
        "priority": 310,
    },
    "mlbpark_bullpen_realestate": {
        "source": "MLBPARK",
        "boardId": "bullpen",
        "url": MLBPARK_BULLPEN_BOARD_URL,
        "priority": 320,
    },
    "natepann_talk_realestate": {
        "source": "NATEPANN",
        "boardId": "talk",
        "url": NATEPANN_TALK_BOARD_URL,
        "priority": 330,
    },
    "todayhumor_economy_realestate": {
        "source": "TODAYHUMOR",
        "boardId": "economy",
        "url": TODAYHUMOR_ECONOMY_BOARD_URL,
        "priority": 340,
    },
    "todayhumor_freeboard_realestate": {
        "source": "TODAYHUMOR",
        "boardId": "freeboard",
        "url": TODAYHUMOR_FREEBOARD_URL,
        "priority": 341,
    },
    "ruliweb_community_realestate": {
        "source": "RULIWEB",
        "boardId": "community",
        "url": RULIWEB_COMMUNITY_BOARD_URL,
        "priority": 350,
    },
    "bobaedream_freeb_realestate": {
        "source": "BOBAEDREAM",
        "boardId": "freeb",
        "url": BOBAEDREAM_FREEBOARD_URL,
        "priority": 360,
    },
    "instiz_name_realestate": {
        "source": "INSTIZ",
        "boardId": "name",
        "url": INSTIZ_NAME_BOARD_URL,
        "priority": 370,
    },
    "slrclub_free_realestate": {
        "source": "SLRCLUB",
        "boardId": "free",
        "url": SLRCLUB_FREE_BOARD_URL,
        "priority": 380,
    },
    "inven_webzine_realestate": {
        "source": "INVEN",
        "boardId": "webzine2097",
        "url": INVEN_WEBZINE_BOARD_URL,
        "priority": 390,
    },
}


def load_real_estate_source_candidates_jsonl(path: str | Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            item = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid source candidate JSONL at line {line_number}: {exc.msg}") from exc
        if not isinstance(item, dict):
            raise ValueError(f"source candidate line {line_number} must be a JSON object")
        candidates.append(item)
    return candidates


def build_real_estate_crawl_target_manifest(
    candidates: Iterable[dict[str, Any]],
    runtime_environment: CrawlRuntimeEnvironment,
    source_policy_registry: SourcePolicyRegistry | None = None,
) -> dict[str, Any]:
    registry = source_policy_registry or default_source_policy_registry()
    items: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for candidate in candidates:
        source_id = _candidate_source_id(candidate)
        policy = _candidate_policy(candidate)
        skip_reason = _candidate_skip_reason(candidate, policy)
        if skip_reason:
            skipped.append({"sourceId": source_id, "reason": skip_reason})
            continue

        source = _candidate_adapter_source(candidate)
        if source not in _SUPPORTED_BOARD_SOURCES:
            skipped.append({"sourceId": source_id, "reason": f"adapter source {source or 'unknown'} is not supported"})
            continue

        decision = registry.decide(source, runtime_environment)
        if not decision.allowed:
            skipped.append({"sourceId": source_id, "reason": decision.reason})
            continue

        target = CrawlTarget.community_board(
            source=source,
            board_id=_candidate_board_id(candidate),
            url=_candidate_url(candidate),
            priority=_candidate_priority(candidate),
            label=str(candidate.get("displayName") or source_id),
            crawl_interval_seconds=_candidate_interval(candidate),
        )
        items.append(
            {
                "targetId": target.target_id,
                "sourceId": source_id,
                "source": target.source,
                "boardId": target.board_id,
                "kind": target.kind.value,
                "url": target.url,
                "label": target.label,
                "sourceType": str(candidate.get("sourceType") or "general_board"),
                "targetScope": _string_list(candidate.get("targetScope")),
                "crawlPolicy": policy,
                "runtimeEnvironment": runtime_environment.value,
                "priority": target.priority,
                "crawlIntervalSeconds": target.crawl_interval_seconds,
                "allowedStorage": _string_list(candidate.get("allowedStorage")) or list(_DEFAULT_ALLOWED_STORAGE),
            }
        )

    return {
        "items": items,
        "skipped": skipped,
        "counts": {"accepted": len(items), "skipped": len(skipped)},
    }


def _candidate_source_id(candidate: dict[str, Any]) -> str:
    return str(candidate.get("sourceId") or candidate.get("id") or "unknown").strip()


def _candidate_policy(candidate: dict[str, Any]) -> str:
    return str(candidate.get("crawlPolicy") or candidate.get("crawlPolicyCandidate") or "disabled").strip()


def _candidate_skip_reason(candidate: dict[str, Any], policy: str) -> str | None:
    normalized_policy = policy.lower()
    if normalized_policy == "disabled" or normalized_policy.startswith("excluded-"):
        return f"source policy {policy} is not crawlable"
    if normalized_policy not in _CRAWLABLE_CANDIDATE_POLICIES:
        return f"source policy {policy} is not crawlable"
    if bool(candidate.get("requiresLogin")):
        return "source requires login"
    if candidate.get("publicListObserved") is False:
        return "public list was not observed"
    return None


def _candidate_defaults(candidate: dict[str, Any]) -> dict[str, Any]:
    return _KNOWN_SOURCE_TARGETS.get(_candidate_source_id(candidate), {})


def _candidate_adapter_source(candidate: dict[str, Any]) -> str:
    defaults = _candidate_defaults(candidate)
    value = candidate.get("adapterSource") or candidate.get("source") or defaults.get("source")
    return str(value or "").strip().upper()


def _candidate_board_id(candidate: dict[str, Any]) -> str | None:
    defaults = _candidate_defaults(candidate)
    value = candidate.get("boardId") or defaults.get("boardId")
    return str(value).strip() if value else None


def _candidate_url(candidate: dict[str, Any]) -> str | None:
    defaults = _candidate_defaults(candidate)
    value = candidate.get("latestUrl") or candidate.get("primaryUrl") or defaults.get("url")
    return str(value).strip() if value else None


def _candidate_priority(candidate: dict[str, Any]) -> int:
    defaults = _candidate_defaults(candidate)
    value = candidate.get("crawlPriority") or defaults.get("priority") or candidate.get("priority") or 300
    if isinstance(value, int):
        return value
    priority_text = str(value).strip().upper()
    if priority_text.startswith("P") and priority_text[1:].isdigit():
        return 200 + (int(priority_text[1:]) * 100)
    try:
        return int(priority_text)
    except ValueError:
        return 300


def _candidate_interval(candidate: dict[str, Any]) -> int:
    value = candidate.get("crawlIntervalSeconds")
    if value is None:
        return 3600
    return int(value)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []
