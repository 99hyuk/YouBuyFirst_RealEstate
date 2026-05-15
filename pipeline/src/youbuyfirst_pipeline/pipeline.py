from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.crawlers.base import CommunityAdapter, SourceBlockedError
from youbuyfirst_pipeline.llm import LLMProvider
from youbuyfirst_pipeline.matcher import InstrumentMatcher
from youbuyfirst_pipeline.models import Analysis, EnrichedPost, Mention, MentionDecision, RawPost
from youbuyfirst_pipeline.source_policy import (
    CrawlRuntimeEnvironment,
    SourcePolicyDecision,
    SourcePolicyRegistry,
    default_source_policy_registry,
)


class CommunityPipeline:
    def __init__(
        self,
        adapters: list[CommunityAdapter],
        matcher: InstrumentMatcher,
        llm_provider: LLMProvider,
        client: SpringIngestionClient,
        source_policy_registry: SourcePolicyRegistry | None = None,
        runtime_environment: CrawlRuntimeEnvironment = CrawlRuntimeEnvironment.PUBLIC,
    ) -> None:
        self.adapters = adapters
        self.matcher = matcher
        self.llm_provider = llm_provider
        self.client = client
        self.source_policy_registry = source_policy_registry or default_source_policy_registry()
        self.runtime_environment = runtime_environment

    async def run_once(self) -> list[dict]:
        results: list[dict] = []
        for adapter in self.adapters:
            started = datetime.now(timezone.utc)
            run_id = f"{adapter.source.lower()}-{started.strftime('%Y%m%d%H%M')}-{uuid4().hex[:8]}"
            result_context = _target_result_context(adapter)
            policy_decision = self.source_policy_registry.decide(adapter.source, self.runtime_environment)
            if not policy_decision.allowed:
                finished = datetime.now(timezone.utc)
                skip_message = _skip_record_message(result_context, policy_decision)
                record_error = self._safe_record_run(
                    adapter.source, run_id, started, finished, "SKIPPED", 0, 0, skip_message
                )
                result = {
                    "source": adapter.source,
                    **result_context,
                    "runId": run_id,
                    "status": "skipped",
                    "sourceStatus": policy_decision.policy.status.value,
                    "runtimeEnvironment": self.runtime_environment.value,
                    "skipReason": policy_decision.reason,
                }
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
                continue
            try:
                raw_posts = await adapter.fetch_posts()
                enriched = [self._enrich(post) for post in raw_posts]
                finished = datetime.now(timezone.utc)
                if enriched:
                    result = self.client.ingest(adapter.source, run_id, started, finished, enriched)
                    results.append({**result_context, **result})
                else:
                    record_error = self._safe_record_run(adapter.source, run_id, started, finished, "SUCCESS", 0, 0, None)
                    results.append(
                        {"source": adapter.source, **result_context, "runId": run_id, "seenPosts": 0, "acceptedPosts": 0}
                    )
                    if record_error:
                        results[-1]["recordError"] = record_error
            except SourceBlockedError as exc:
                finished = datetime.now(timezone.utc)
                record_error = self._safe_record_run(adapter.source, run_id, started, finished, "PARTIAL_FAILURE", 0, 0, str(exc))
                result = {"source": adapter.source, **result_context, "runId": run_id, "status": "blocked", "error": str(exc)}
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
            except Exception as exc:
                finished = datetime.now(timezone.utc)
                record_error = self._safe_record_run(adapter.source, run_id, started, finished, "FAILED", 0, 0, str(exc))
                result = {"source": adapter.source, **result_context, "runId": run_id, "status": "failed", "error": str(exc)}
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
        return results

    def _enrich(self, post: RawPost) -> EnrichedPost:
        text = f"{post.title}\n{post.content}"
        candidates = self.matcher.match(text)
        decisions = self.llm_provider.resolve_mentions(post.title, post.content, candidates)
        accepted_decisions = _accepted_decisions(candidates, decisions)
        mentions = [
            Mention(market=decision.market, symbol=decision.symbol, matched_text=decision.matched_text)
            for decision in accepted_decisions
        ]
        analyses = [
            Analysis(
                market=decision.market,
                symbol=decision.symbol,
                sentiment=decision.reaction_direction,
                confidence=decision.confidence,
                rationale=decision.rationale,
                model=decision.model,
            )
            for decision in accepted_decisions
        ]
        return EnrichedPost(
            source=post.source,
            external_id=post.external_id,
            url=post.url,
            title=post.title,
            content=post.content,
            author=post.author,
            published_at=post.published_at,
            mentions=mentions,
            analyses=analyses,
        )

    def _safe_record_run(
        self,
        source: str,
        run_id: str,
        started: datetime,
        finished: datetime,
        status: str,
        posts_seen: int,
        posts_accepted: int,
        error_message: str | None,
    ) -> str | None:
        try:
            self.client.record_crawl_run(source, run_id, started, finished, status, posts_seen, posts_accepted, error_message)
            return None
        except Exception as exc:
            return str(exc)


def _accepted_decisions(candidates: list[Mention], decisions: list[MentionDecision]) -> list[MentionDecision]:
    candidate_keys = {(candidate.market.upper(), candidate.symbol.upper(), candidate.matched_text) for candidate in candidates}
    accepted: list[MentionDecision] = []
    seen: set[tuple[str, str, str]] = set()
    for decision in decisions:
        key = (decision.market.upper(), decision.symbol.upper(), decision.matched_text)
        if key in seen or key not in candidate_keys or not decision.is_mentioned:
            continue
        seen.add(key)
        accepted.append(decision)
    return accepted


def _target_result_context(adapter: CommunityAdapter) -> dict:
    target = getattr(adapter, "target", None)
    if target is None:
        return {}
    context = {
        "targetId": target.target_id,
        "targetKind": target.kind.value,
        "targetLabel": target.label,
    }
    if target.market:
        context["targetMarket"] = target.market
    if target.symbol:
        context["targetSymbol"] = target.symbol
    if target.url:
        context["targetUrl"] = target.url
    return context


def _skip_record_message(result_context: dict, policy_decision: SourcePolicyDecision) -> str:
    parts: list[str] = []
    target_id = result_context.get("targetId")
    if target_id:
        parts.append(f"targetId={target_id}")
    parts.extend(
        [
            f"sourceStatus={policy_decision.policy.status.value}",
            f"runtimeEnvironment={policy_decision.runtime_environment.value}",
            f"reason={policy_decision.reason}",
        ]
    )
    return "; ".join(parts)
