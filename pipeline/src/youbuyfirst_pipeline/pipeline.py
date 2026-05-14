from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.crawlers.base import CommunityAdapter, SourceBlockedError
from youbuyfirst_pipeline.llm import LLMProvider
from youbuyfirst_pipeline.matcher import InstrumentMatcher
from youbuyfirst_pipeline.models import EnrichedPost, RawPost


class CommunityPipeline:
    def __init__(
        self,
        adapters: list[CommunityAdapter],
        matcher: InstrumentMatcher,
        llm_provider: LLMProvider,
        client: SpringIngestionClient,
    ) -> None:
        self.adapters = adapters
        self.matcher = matcher
        self.llm_provider = llm_provider
        self.client = client

    async def run_once(self) -> list[dict]:
        results: list[dict] = []
        for adapter in self.adapters:
            started = datetime.now(timezone.utc)
            run_id = f"{adapter.source.lower()}-{started.strftime('%Y%m%d%H%M')}-{uuid4().hex[:8]}"
            try:
                raw_posts = await adapter.fetch_posts()
                enriched = [self._enrich(post) for post in raw_posts]
                finished = datetime.now(timezone.utc)
                if enriched:
                    results.append(self.client.ingest(adapter.source, run_id, started, finished, enriched))
                else:
                    record_error = self._safe_record_run(adapter.source, run_id, started, finished, "SUCCESS", 0, 0, None)
                    results.append({"source": adapter.source, "runId": run_id, "seenPosts": 0, "acceptedPosts": 0})
                    if record_error:
                        results[-1]["recordError"] = record_error
            except SourceBlockedError as exc:
                finished = datetime.now(timezone.utc)
                record_error = self._safe_record_run(adapter.source, run_id, started, finished, "PARTIAL_FAILURE", 0, 0, str(exc))
                result = {"source": adapter.source, "runId": run_id, "status": "blocked", "error": str(exc)}
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
            except Exception as exc:
                finished = datetime.now(timezone.utc)
                record_error = self._safe_record_run(adapter.source, run_id, started, finished, "FAILED", 0, 0, str(exc))
                result = {"source": adapter.source, "runId": run_id, "status": "failed", "error": str(exc)}
                if record_error:
                    result["recordError"] = record_error
                results.append(result)
        return results

    def _enrich(self, post: RawPost) -> EnrichedPost:
        text = f"{post.title}\n{post.content}"
        mentions = self.matcher.match(text)
        analyses = self.llm_provider.analyze(post.title, post.content, mentions)
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
