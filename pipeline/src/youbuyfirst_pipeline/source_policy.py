from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceStatus(str, Enum):
    ENABLED = "enabled"
    PUBLIC_DEMO_ONLY = "public-demo-only"
    LOCAL_RESEARCH_ONLY = "local-research-only"
    DISABLED = "disabled"


class CrawlRuntimeEnvironment(str, Enum):
    LOCAL = "local"
    PUBLIC = "public"


@dataclass(frozen=True)
class SourcePolicy:
    source: str
    status: SourceStatus
    reason: str


@dataclass(frozen=True)
class SourcePolicyDecision:
    source: str
    policy: SourcePolicy
    runtime_environment: CrawlRuntimeEnvironment
    allowed: bool
    reason: str


class SourcePolicyRegistry:
    def __init__(self, policies: dict[str, SourcePolicy]) -> None:
        self._policies = {source.upper(): policy for source, policy in policies.items()}

    def policy_for(self, source: str) -> SourcePolicy:
        normalized = source.upper()
        return self._policies.get(
            normalized,
            SourcePolicy(
                source=normalized,
                status=SourceStatus.DISABLED,
                reason="source is not registered; default disabled",
            ),
        )

    def decide(self, source: str, runtime_environment: CrawlRuntimeEnvironment) -> SourcePolicyDecision:
        policy = self.policy_for(source)
        if policy.status == SourceStatus.ENABLED:
            return SourcePolicyDecision(source, policy, runtime_environment, True, policy.reason)
        if policy.status == SourceStatus.LOCAL_RESEARCH_ONLY:
            if runtime_environment == CrawlRuntimeEnvironment.LOCAL:
                return SourcePolicyDecision(source, policy, runtime_environment, True, policy.reason)
            return SourcePolicyDecision(
                source,
                policy,
                runtime_environment,
                False,
                "source policy local-research-only is not allowed in public runtime",
            )
        if policy.status == SourceStatus.PUBLIC_DEMO_ONLY:
            return SourcePolicyDecision(
                source,
                policy,
                runtime_environment,
                False,
                "source policy public-demo-only uses fixture or sample data; external requests are disabled",
            )
        return SourcePolicyDecision(source, policy, runtime_environment, False, policy.reason)


def default_source_policy_registry() -> SourcePolicyRegistry:
    return SourcePolicyRegistry(
        {
            "NAVER": SourcePolicy(
                source="NAVER",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP source allowed only for local research before public review",
            ),
            "FMKOREA": SourcePolicy(
                source="FMKOREA",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP source allowed only for local research before public review",
            ),
            "NAVER_CAFE": SourcePolicy(
                source="NAVER_CAFE",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public search discovery only; direct cafe crawling requires separate review",
            ),
            "DAUM_CAFE": SourcePolicy(
                source="DAUM_CAFE",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public search discovery only; direct cafe crawling requires separate review",
            ),
            "DCINSIDE": SourcePolicy(
                source="DCINSIDE",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP source allowed only for local research before public review",
            ),
            "PPOMPPU": SourcePolicy(
                source="PPOMPPU",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP source allowed only for local research before public review",
            ),
            "CLIEN": SourcePolicy(
                source="CLIEN",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP keyword-board source allowed only for local research before public review",
            ),
            "COOK82": SourcePolicy(
                source="COOK82",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="MVP keyword-board source allowed only for local research before public review",
            ),
            "DEALAGORA": SourcePolicy(
                source="DEALAGORA",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="real-estate community source allowed only for local research before public review",
            ),
            "THEQOO": SourcePolicy(
                source="THEQOO",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "MLBPARK": SourcePolicy(
                source="MLBPARK",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "NATEPANN": SourcePolicy(
                source="NATEPANN",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "TODAYHUMOR": SourcePolicy(
                source="TODAYHUMOR",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "RULIWEB": SourcePolicy(
                source="RULIWEB",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "BOBAEDREAM": SourcePolicy(
                source="BOBAEDREAM",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "INSTIZ": SourcePolicy(
                source="INSTIZ",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "SLRCLUB": SourcePolicy(
                source="SLRCLUB",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
            "INVEN": SourcePolicy(
                source="INVEN",
                status=SourceStatus.LOCAL_RESEARCH_ONLY,
                reason="public keyword-board source allowed only for local research before public review",
            ),
        }
    )


def runtime_environment_from_env(value: str | None) -> CrawlRuntimeEnvironment:
    if value and value.strip().lower() == CrawlRuntimeEnvironment.LOCAL.value:
        return CrawlRuntimeEnvironment.LOCAL
    return CrawlRuntimeEnvironment.PUBLIC
