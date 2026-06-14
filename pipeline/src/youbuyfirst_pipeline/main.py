from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from youbuyfirst_pipeline.board_stream import BoardStreamCrawler
from youbuyfirst_pipeline.client import SpringIngestionClient
from youbuyfirst_pipeline.crawl_targets import (
    CrawlTarget,
    CrawlTargetKind,
    real_estate_seed_crawl_targets,
)
from youbuyfirst_pipeline.crawlers.base import BrowserCapableFetcher
from youbuyfirst_pipeline.crawlers.dcinside import DcinsideAdapter
from youbuyfirst_pipeline.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_pipeline.crawlers.ppomppu import PpomppuAdapter
from youbuyfirst_pipeline.pipeline import CommunityPipeline
from youbuyfirst_pipeline.realestate_public_data import (
    DATA_GO_SERVICE_KEY_ENV,
    RealEstatePublicDataRawIngestion,
    build_official_apartment_price_raw_ingestions,
    build_regional_stat_raw_ingestions,
    build_molit_raw_ingestions,
    build_molit_public_data_client_from_env,
    collect_molit_real_estate_market_facts,
    collect_molit_real_estate_market_facts_from_data_targets,
    inspect_official_apartment_price_csv,
    inspect_regional_stat_csv,
    iter_official_apartment_price_market_facts,
    iter_regional_stat_market_facts,
)
from youbuyfirst_pipeline.realestate_backfill_plan import (
    build_molit_backfill_plan,
    build_molit_backfill_plan_from_data_targets,
    chunk_molit_backfill_plan,
    load_molit_backfill_plan_manifest,
)
from youbuyfirst_pipeline.realestate_provider_catalog import (
    public_data_catalog_payload,
    public_data_catalog_seed_sql,
)
from youbuyfirst_pipeline.realestate_matcher import (
    RealEstateAliasRule,
    build_real_estate_alias_coverage_report,
    load_real_estate_alias_rules,
    load_real_estate_posts_for_matching,
    match_real_estate_posts,
    suggest_real_estate_alias_candidates,
)
from youbuyfirst_pipeline.realestate_reaction_classifier import (
    RuleBasedRealEstateReactionClassifier,
    classify_real_estate_reaction_observations,
    real_estate_reaction_observation_to_dict,
)
from youbuyfirst_pipeline.realestate_recent_issues import (
    SerpApiRecentIssueClient,
    build_recent_issue_content_items,
    load_recent_issue_search_targets,
)
from youbuyfirst_pipeline.realestate_daily_scheduler import (
    RealEstateDailyRefreshJob,
    RealEstateEvidenceLogRefreshJob,
    RealEstateMapLayerRefreshJob,
    RealEstateRecentIssuesRefreshJob,
)
from youbuyfirst_pipeline.realestate_evidence import (
    DEFAULT_EVALUATION_VERSION,
    DEFAULT_PROMPT_VERSION,
    build_real_estate_evidence_logs,
    load_real_estate_evidence_content_items,
    load_real_estate_evidence_market_facts,
    load_real_estate_evidence_reaction_snapshots,
    load_real_estate_evidence_similar_windows,
    load_real_estate_evidence_timeline_events,
)
from youbuyfirst_pipeline.realestate_embeddings import (
    DEFAULT_GMS_GEMINI_BASE_URL,
    DEFAULT_GMS_GEMINI_EMBEDDING_MODEL,
    GmsGeminiEmbeddingClient,
    build_real_estate_embedding_inputs,
    load_real_estate_embedding_inputs,
)
from youbuyfirst_pipeline.realestate_llm_evaluation import (
    DEFAULT_GMS_EVIDENCE_PROMPT_VERSION,
    DEFAULT_GMS_OPENAI_BASE_URL,
    DEFAULT_GMS_OPENAI_CHAT_MODEL,
    GmsOpenAIChatEvaluationClient,
    apply_real_estate_llm_evaluation,
)
from youbuyfirst_pipeline.realestate_reactions import (
    build_real_estate_reaction_snapshots,
    load_real_estate_reaction_observations,
    parse_reaction_datetime,
)
from youbuyfirst_pipeline.realestate_similarity import (
    find_real_estate_similar_windows,
    load_real_estate_market_fact_payloads,
    load_real_estate_reaction_snapshot_payloads,
)
from youbuyfirst_pipeline.realestate_vector_store import (
    DEFAULT_QDRANT_COLLECTION,
    QdrantRealEstateVectorStoreClient,
    build_qdrant_points,
    find_embedding_by_input_id,
    load_real_estate_embedding_payloads,
    qdrant_search_results_to_similar_windows,
)
from youbuyfirst_pipeline.realestate_source_registry import (
    build_real_estate_crawl_target_manifest,
    load_real_estate_source_candidates_jsonl,
)
from youbuyfirst_pipeline.realestate_reaction_scheduler import build_real_estate_reaction_snapshot_refresh_job
from youbuyfirst_pipeline.realestate_regions import (
    build_molit_region_market_data_targets,
    parse_molit_legal_dong_code_csv,
)
from youbuyfirst_pipeline.realestate_scheduler import build_real_estate_market_facts_refresh_job
from youbuyfirst_pipeline.realestate_target_graph import (
    RealEstateTargetEdgeRule,
    load_real_estate_target_edge_rules,
    roll_up_real_estate_reaction_observations,
)
from youbuyfirst_pipeline.scheduler import serve
from youbuyfirst_pipeline.source_policy import default_source_policy_registry, runtime_environment_from_env


ACTIVE_COMMANDS = [
    "run-once",
    "serve",
    "realestate-market-facts",
    "realestate-market-facts-push",
    "realestate-market-facts-raw-push",
    "realestate-regional-stat-csv-inspect",
    "realestate-regional-stat-csv-raw-push",
    "realestate-official-apartment-prices-inspect",
    "realestate-official-apartment-prices-raw-push",
    "realestate-market-facts-promote-staging",
    "realestate-market-facts-backfill-plan",
    "realestate-public-data-preflight",
    "realestate-public-data-providers",
    "realestate-regions-inspect",
    "realestate-regions-import",
    "realestate-aliases-fetch",
    "realestate-alias-coverage",
    "realestate-alias-candidates",
    "realestate-alias-candidates-push",
    "realestate-target-edges-fetch",
    "realestate-target-matches",
    "realestate-crawl-target-manifest",
    "realestate-reaction-observations",
    "realestate-reaction-snapshots",
    "realestate-reaction-snapshots-push",
    "realestate-reaction-snapshots-from-posts",
    "realestate-reaction-snapshots-from-posts-push",
    "realestate-recent-issues",
    "realestate-recent-issues-push",
    "realestate-similar-windows",
    "realestate-embeddings",
    "realestate-vector-upsert",
    "realestate-vector-search",
    "realestate-evidence-logs",
    "realestate-evidence-logs-push",
]


def build_pipeline() -> CommunityPipeline:
    load_dotenv()
    runtime_environment = runtime_environment_from_env(os.getenv("CRAWL_RUNTIME_ENV"))
    user_agent = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    )
    fetcher = BrowserCapableFetcher(
        user_agent=user_agent,
        timeout_seconds=float(os.getenv("CRAWLER_TIMEOUT_SECONDS", "10")),
        browser_channel=_optional_env(os.getenv("CRAWLER_BROWSER_CHANNEL")),
    )

    targets = real_estate_seed_crawl_targets()
    adapters = _adapters_from_targets(
        targets,
        fetcher,
        stream_crawler=_stream_crawler_from_env(),
    )

    client = _spring_client()
    return CommunityPipeline(
        adapters=adapters,
        client=client,
        source_policy_registry=default_source_policy_registry(),
        runtime_environment=runtime_environment,
        default_board_lookback_hours=float(os.getenv("CRAWLER_LATEST_LOOKBACK_HOURS", "24")),
        diffusion_max_age_hours=float(os.getenv("CRAWLER_DIFFUSION_MAX_AGE_HOURS", "24")),
        comment_trigger_min_comments=int(os.getenv("CRAWLER_COMMENT_TRIGGER_MIN_COMMENTS", "30")),
        comment_trigger_min_recommends=int(os.getenv("CRAWLER_COMMENT_TRIGGER_MIN_RECOMMENDS", "30")),
        comment_trigger_min_views=int(os.getenv("CRAWLER_COMMENT_TRIGGER_MIN_VIEWS", "5000")),
        high_engagement_max_comments=int(os.getenv("CRAWLER_HIGH_ENGAGEMENT_MAX_COMMENTS", "30")),
        diffusion_max_comments=int(os.getenv("CRAWLER_DIFFUSION_MAX_COMMENTS", "50")),
    )


def _optional_env(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _stream_crawler_from_env() -> BoardStreamCrawler:
    return BoardStreamCrawler(
        max_pages_per_run=int(os.getenv("CRAWLER_MAX_PAGES_PER_RUN", "20")),
        max_posts_per_run=int(os.getenv("CRAWLER_MAX_POSTS_PER_RUN", "500")),
        page_delay_min_seconds=float(os.getenv("CRAWLER_PAGE_DELAY_MIN_SECONDS", "1.5")),
        page_delay_max_seconds=float(os.getenv("CRAWLER_PAGE_DELAY_MAX_SECONDS", "4.0")),
    )


def _adapters_from_targets(
    targets: list[CrawlTarget],
    fetcher: BrowserCapableFetcher,
    stream_crawler: BoardStreamCrawler | None = None,
) -> list:
    adapters = []
    for target in targets:
        if target.source == "FMKOREA" and target.kind in {
            CrawlTargetKind.COMMUNITY_BOARD,
            CrawlTargetKind.GENERAL_BOARD_DIFFUSION,
        }:
            adapters.append(
                FmkoreaAdapter(
                    fetcher,
                    url=target.url,
                    target=target,
                    stream_crawler=stream_crawler,
                )
            )
            continue
        if target.source == "DCINSIDE" and target.kind in {
            CrawlTargetKind.COMMUNITY_BOARD,
            CrawlTargetKind.GENERAL_BOARD_DIFFUSION,
        }:
            adapters.append(DcinsideAdapter(fetcher, target=target, stream_crawler=stream_crawler))
            continue
        if target.source == "PPOMPPU" and target.kind in {
            CrawlTargetKind.COMMUNITY_BOARD,
            CrawlTargetKind.GENERAL_BOARD_DIFFUSION,
        }:
            adapters.append(PpomppuAdapter(fetcher, target=target, stream_crawler=stream_crawler))
            continue
        raise ValueError(f"unsupported crawl target: {target.target_id}")
    return adapters


async def async_main() -> None:
    _configure_stdout_utf8()
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=ACTIVE_COMMANDS,
    )
    parser.add_argument("--interval-minutes", type=int, default=int(os.getenv("CRAWL_INTERVAL_MINUTES", "30")))
    parser.add_argument("--realestate-lawd-code", default=os.getenv("REALESTATE_LAWD_CODE"))
    parser.add_argument(
        "--realestate-lawd-codes",
        nargs="+",
        default=_configured_realestate_lawd_codes(os.getenv("REALESTATE_LAWD_CODES")),
    )
    parser.add_argument("--realestate-deal-ym", default=os.getenv("REALESTATE_DEAL_YM"))
    parser.add_argument("--realestate-start-ym", default=os.getenv("REALESTATE_START_YM"))
    parser.add_argument("--realestate-end-ym", default=os.getenv("REALESTATE_END_YM"))
    parser.add_argument(
        "--realestate-backfill-plan-json",
        default=os.getenv("REALESTATE_BACKFILL_PLAN_JSON"),
    )
    parser.add_argument(
        "--realestate-backfill-plan-output",
        default=os.getenv("REALESTATE_BACKFILL_PLAN_OUTPUT"),
    )
    parser.add_argument(
        "--realestate-backfill-chunk-size",
        type=int,
        default=int(os.getenv("REALESTATE_BACKFILL_CHUNK_SIZE", "0")),
    )
    parser.add_argument("--realestate-provider-dataset", default=os.getenv("REALESTATE_PROVIDER_DATASET"))
    parser.add_argument("--realestate-provider", default=os.getenv("REALESTATE_PROVIDER"))
    parser.add_argument(
        "--realestate-provider-output",
        choices=["json", "sql"],
        default=os.getenv("REALESTATE_PROVIDER_OUTPUT", "json"),
    )
    parser.add_argument("--realestate-fact-type", default=os.getenv("REALESTATE_FACT_TYPE"))
    parser.add_argument("--realestate-stat-csv", default=os.getenv("REALESTATE_STAT_CSV"))
    parser.add_argument("--realestate-stat-unit", default=os.getenv("REALESTATE_STAT_UNIT"))
    parser.add_argument(
        "--realestate-stat-batch-size",
        type=int,
        default=int(os.getenv("REALESTATE_STAT_BATCH_SIZE", "1000")),
    )
    parser.add_argument("--realestate-run-key", default=os.getenv("REALESTATE_RUN_KEY"))
    parser.add_argument(
        "--realestate-validation-status",
        default=os.getenv("REALESTATE_VALIDATION_STATUS", "valid"),
    )
    parser.add_argument(
        "--realestate-promote-limit",
        type=int,
        default=int(os.getenv("REALESTATE_PROMOTE_LIMIT", "1000")),
    )
    parser.add_argument(
        "--realestate-promote-after-raw-push",
        action="store_true",
        default=os.getenv("REALESTATE_PROMOTE_AFTER_RAW_PUSH", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-skip-completed-runs",
        action="store_true",
        default=os.getenv("REALESTATE_SKIP_COMPLETED_RUNS", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-run-limit",
        type=int,
        default=int(os.getenv("REALESTATE_RUN_LIMIT", "0")),
    )
    parser.add_argument(
        "--realestate-large-run-threshold",
        type=int,
        default=int(os.getenv("REALESTATE_LARGE_RUN_THRESHOLD", "50")),
    )
    parser.add_argument(
        "--realestate-confirm-large-run",
        action="store_true",
        default=os.getenv("REALESTATE_CONFIRM_LARGE_RUN", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-public-data-page-size",
        type=int,
        default=int(os.getenv("REALESTATE_PUBLIC_DATA_PAGE_SIZE", "100")),
    )
    parser.add_argument(
        "--realestate-public-data-max-pages",
        type=int,
        default=int(os.getenv("REALESTATE_PUBLIC_DATA_MAX_PAGES", "1000")),
    )
    parser.add_argument(
        "--realestate-official-apartment-price-csv",
        default=os.getenv("REALESTATE_OFFICIAL_APARTMENT_PRICE_CSV"),
    )
    parser.add_argument(
        "--realestate-official-apartment-price-base-date",
        default=os.getenv("REALESTATE_OFFICIAL_APARTMENT_PRICE_BASE_DATE"),
    )
    parser.add_argument(
        "--realestate-official-apartment-price-batch-size",
        type=int,
        default=int(os.getenv("REALESTATE_OFFICIAL_APARTMENT_PRICE_BATCH_SIZE", "1000")),
    )
    parser.add_argument(
        "--realestate-datasets",
        nargs="+",
        default=_configured_realestate_datasets(os.getenv("REALESTATE_DATASETS")),
        help="Real-estate public datasets: trade rent",
    )
    parser.add_argument(
        "--realestate-use-backend-targets",
        action="store_true",
        default=os.getenv("REALESTATE_USE_BACKEND_TARGETS", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--enable-realestate-market-facts-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_MARKET_FACT_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-market-facts-refresh-interval-minutes",
        type=int,
        default=int(os.getenv("REALESTATE_MARKET_FACT_REFRESH_INTERVAL_MINUTES", "360")),
    )
    parser.add_argument(
        "--enable-realestate-reaction-snapshots-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_REACTION_SNAPSHOT_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-reaction-snapshots-refresh-interval-minutes",
        type=int,
        default=int(os.getenv("REALESTATE_REACTION_SNAPSHOT_REFRESH_INTERVAL_MINUTES", "30")),
    )
    parser.add_argument(
        "--enable-realestate-daily-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_DAILY_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-daily-refresh-interval-minutes",
        type=int,
        default=int(os.getenv("REALESTATE_DAILY_REFRESH_INTERVAL_MINUTES", "1440")),
    )
    parser.add_argument(
        "--enable-realestate-recent-issues-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_RECENT_ISSUES_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--enable-realestate-evidence-logs-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_EVIDENCE_LOG_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--enable-realestate-map-layer-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_MAP_LAYER_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-map-layer-types",
        nargs="+",
        default=_configured_csv_values(os.getenv("REALESTATE_MAP_LAYER_TYPES"), ["sido", "sigungu"]),
    )
    parser.add_argument(
        "--realestate-map-layer-periods",
        nargs="+",
        default=_configured_csv_values(os.getenv("REALESTATE_MAP_LAYER_PERIODS"), ["week", "month", "halfYear"]),
    )
    parser.add_argument(
        "--realestate-evidence-target-type",
        default=os.getenv("REALESTATE_EVIDENCE_TARGET_TYPE", "region"),
    )
    parser.add_argument(
        "--realestate-evidence-ranking-limit",
        type=int,
        default=int(os.getenv("REALESTATE_EVIDENCE_RANKING_LIMIT", "20")),
    )
    parser.add_argument(
        "--realestate-evidence-market-fact-limit",
        type=int,
        default=int(os.getenv("REALESTATE_EVIDENCE_MARKET_FACT_LIMIT", "20")),
    )
    parser.add_argument(
        "--realestate-evidence-timeline-limit",
        type=int,
        default=int(os.getenv("REALESTATE_EVIDENCE_TIMELINE_LIMIT", "20")),
    )
    parser.add_argument(
        "--realestate-evidence-content-limit",
        type=int,
        default=int(os.getenv("REALESTATE_EVIDENCE_CONTENT_LIMIT", "20")),
    )
    parser.add_argument("--legal-dong-code-csv", default=os.getenv("REALESTATE_LEGAL_DONG_CODE_CSV"))
    parser.add_argument(
        "--realestate-aliases-jsonl",
        default=os.getenv("REALESTATE_ALIASES_JSONL"),
    )
    parser.add_argument(
        "--realestate-use-backend-aliases",
        action="store_true",
        default=os.getenv("REALESTATE_USE_BACKEND_ALIASES", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-target-edges-jsonl",
        default=os.getenv("REALESTATE_TARGET_EDGES_JSONL"),
    )
    parser.add_argument(
        "--realestate-use-backend-target-edges",
        action="store_true",
        default=os.getenv("REALESTATE_USE_BACKEND_TARGET_EDGES", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-source-candidates-jsonl",
        default=os.getenv("REALESTATE_SOURCE_CANDIDATES_JSONL"),
    )
    parser.add_argument(
        "--realestate-crawl-target-manifest-output",
        default=os.getenv("REALESTATE_CRAWL_TARGET_MANIFEST_OUTPUT"),
    )
    parser.add_argument(
        "--crawl-runtime-environment",
        choices=["local", "public"],
        default=os.getenv("CRAWL_RUNTIME_ENV", "public"),
    )
    parser.add_argument(
        "--community-posts-jsonl",
        default=os.getenv("REALESTATE_COMMUNITY_POSTS_JSONL"),
    )
    parser.add_argument(
        "--reaction-observations-jsonl",
        default=os.getenv("REALESTATE_REACTION_OBSERVATIONS_JSONL"),
    )
    parser.add_argument(
        "--reaction-snapshots-jsonl",
        default=os.getenv("REALESTATE_REACTION_SNAPSHOTS_JSONL"),
    )
    parser.add_argument(
        "--reaction-window-start",
        default=os.getenv("REALESTATE_REACTION_WINDOW_START"),
    )
    parser.add_argument(
        "--reaction-window-minutes",
        type=int,
        default=int(os.getenv("REALESTATE_REACTION_WINDOW_MINUTES", "60")),
    )
    parser.add_argument(
        "--reaction-as-of",
        default=os.getenv("REALESTATE_REACTION_AS_OF"),
    )
    parser.add_argument(
        "--reaction-stale-after-minutes",
        type=int,
        default=int(os.getenv("REALESTATE_REACTION_STALE_AFTER_MINUTES", "360")),
    )
    parser.add_argument(
        "--realestate-search-targets-jsonl",
        default=os.getenv("REALESTATE_SEARCH_TARGETS_JSONL"),
    )
    parser.add_argument(
        "--realestate-issue-keywords",
        nargs="+",
        default=_configured_issue_keywords(os.getenv("REALESTATE_ISSUE_KEYWORDS")),
    )
    parser.add_argument(
        "--realestate-search-as-of",
        default=os.getenv("REALESTATE_SEARCH_AS_OF"),
    )
    parser.add_argument(
        "--serpapi-result-limit",
        type=int,
        default=int(os.getenv("SERPAPI_RESULT_LIMIT", "5")),
    )
    parser.add_argument(
        "--similar-source-target-id",
        default=os.getenv("REALESTATE_SIMILAR_SOURCE_TARGET_ID"),
    )
    parser.add_argument(
        "--similar-source-window-start",
        default=os.getenv("REALESTATE_SIMILAR_SOURCE_WINDOW_START"),
    )
    parser.add_argument(
        "--similar-market-facts-jsonl",
        default=os.getenv("REALESTATE_SIMILAR_MARKET_FACTS_JSONL"),
    )
    parser.add_argument(
        "--similar-top-n",
        type=int,
        default=int(os.getenv("REALESTATE_SIMILAR_TOP_N", "5")),
    )
    parser.add_argument(
        "--similar-horizon-days",
        type=int,
        default=int(os.getenv("REALESTATE_SIMILAR_HORIZON_DAYS", "90")),
    )
    parser.add_argument(
        "--embedding-model-name",
        default=os.getenv("GMS_GEMINI_EMBEDDING_MODEL", DEFAULT_GMS_GEMINI_EMBEDDING_MODEL),
    )
    parser.add_argument(
        "--embedding-timeout-seconds",
        type=float,
        default=float(os.getenv("GMS_TIMEOUT_SECONDS", "30")),
    )
    parser.add_argument(
        "--embeddings-jsonl",
        default=os.getenv("REALESTATE_EMBEDDINGS_JSONL"),
    )
    parser.add_argument(
        "--vector-source-input-id",
        default=os.getenv("REALESTATE_VECTOR_SOURCE_INPUT_ID"),
    )
    parser.add_argument(
        "--vector-top-n",
        type=int,
        default=int(os.getenv("REALESTATE_VECTOR_TOP_N", "5")),
    )
    parser.add_argument(
        "--evidence-target-id",
        default=os.getenv("REALESTATE_EVIDENCE_TARGET_ID"),
    )
    parser.add_argument(
        "--evidence-window-start",
        default=os.getenv("REALESTATE_EVIDENCE_WINDOW_START"),
    )
    parser.add_argument(
        "--evidence-evaluated-at",
        default=os.getenv("REALESTATE_EVIDENCE_EVALUATED_AT"),
    )
    parser.add_argument(
        "--evidence-market-facts-jsonl",
        default=os.getenv("REALESTATE_EVIDENCE_MARKET_FACTS_JSONL"),
    )
    parser.add_argument(
        "--evidence-timeline-events-jsonl",
        default=os.getenv("REALESTATE_EVIDENCE_TIMELINE_EVENTS_JSONL"),
    )
    parser.add_argument(
        "--evidence-similar-windows-jsonl",
        default=os.getenv("REALESTATE_EVIDENCE_SIMILAR_WINDOWS_JSONL"),
    )
    parser.add_argument(
        "--evidence-content-items-jsonl",
        default=os.getenv("REALESTATE_EVIDENCE_CONTENT_ITEMS_JSONL"),
    )
    parser.add_argument(
        "--evidence-evaluation-version",
        default=os.getenv("REALESTATE_EVIDENCE_EVALUATION_VERSION", DEFAULT_EVALUATION_VERSION),
    )
    parser.add_argument(
        "--evidence-prompt-version",
        default=os.getenv("REALESTATE_EVIDENCE_PROMPT_VERSION", DEFAULT_PROMPT_VERSION),
    )
    parser.add_argument(
        "--evidence-model-name",
        default=os.getenv("REALESTATE_EVIDENCE_MODEL_NAME"),
    )
    parser.add_argument(
        "--evidence-use-gms-llm",
        action="store_true",
        default=os.getenv("REALESTATE_EVIDENCE_USE_GMS_LLM", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--evidence-llm-model",
        default=os.getenv("GMS_OPENAI_CHAT_MODEL", DEFAULT_GMS_OPENAI_CHAT_MODEL),
    )
    parser.add_argument(
        "--evidence-llm-prompt-version",
        default=os.getenv("REALESTATE_EVIDENCE_LLM_PROMPT_VERSION", DEFAULT_GMS_EVIDENCE_PROMPT_VERSION),
    )
    parser.add_argument(
        "--evidence-llm-timeout-seconds",
        type=float,
        default=float(os.getenv("GMS_TIMEOUT_SECONDS", "30")),
    )
    args = parser.parse_args()

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    if args.command == "realestate-public-data-providers":
        if args.realestate_provider_output == "sql":
            print(public_data_catalog_seed_sql())
            return
        print(json.dumps(public_data_catalog_payload(), ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-public-data-preflight":
        print(json.dumps(_realestate_public_data_preflight_payload(args), ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-market-facts-backfill-plan":
        spring_client = _spring_client() if args.realestate_use_backend_targets or args.realestate_skip_completed_runs else None
        plan, skipped_completed_run_keys, planned_run_count = _realestate_raw_push_task_selection(
            args,
            spring_client=spring_client,
        )
        payload = _realestate_backfill_plan_payload(args, plan)
        if args.realestate_skip_completed_runs or args.realestate_run_limit > 0:
            payload = {
                **payload,
                "plannedRuns": planned_run_count,
                "remainingRuns": len(plan),
                "skippedCompletedRuns": skipped_completed_run_keys,
            }
            payload.update(_realestate_run_limit_payload(args, planned_run_count, skipped_completed_run_keys, plan))
        _write_realestate_backfill_plan_output(args, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-aliases-fetch":
        aliases = _load_real_estate_alias_rules_from_args(args, force_backend=True)
        print(json.dumps({"items": [_real_estate_alias_rule_to_dict(alias) for alias in aliases]}, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-target-edges-fetch":
        edges = _load_real_estate_target_edge_rules_from_args(args, force_backend=True)
        print(json.dumps({"items": [_real_estate_target_edge_rule_to_dict(edge) for edge in edges]}, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-regions-inspect":
        if not args.legal_dong_code_csv:
            raise SystemExit("--legal-dong-code-csv is required")
        payload = _realestate_regions_inspect_payload(args)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-regions-import":
        if not args.legal_dong_code_csv:
            raise SystemExit("--legal-dong-code-csv is required")
        csv_text = Path(args.legal_dong_code_csv).read_text(encoding="utf-8-sig")
        regions = parse_molit_legal_dong_code_csv(csv_text)
        client = _spring_client()
        client.publish_real_estate_regions(regions)
        return

    if args.command == "realestate-target-matches":
        if not args.community_posts_jsonl:
            raise SystemExit("--community-posts-jsonl is required")
        aliases = _load_real_estate_alias_rules_from_args(args)
        posts = load_real_estate_posts_for_matching(args.community_posts_jsonl)
        matched_posts = match_real_estate_posts(posts, aliases)
        print(json.dumps({"items": [post.to_dict() for post in matched_posts]}, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-alias-coverage":
        if not args.community_posts_jsonl:
            raise SystemExit("--community-posts-jsonl is required")
        aliases = _load_real_estate_alias_rules_from_args(args)
        posts = load_real_estate_posts_for_matching(args.community_posts_jsonl)
        report = build_real_estate_alias_coverage_report(posts, aliases)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-crawl-target-manifest":
        if not args.realestate_source_candidates_jsonl:
            raise SystemExit("--realestate-source-candidates-jsonl is required")
        candidates = load_real_estate_source_candidates_jsonl(args.realestate_source_candidates_jsonl)
        manifest = build_real_estate_crawl_target_manifest(
            candidates,
            runtime_environment=runtime_environment_from_env(args.crawl_runtime_environment),
        )
        _write_realestate_crawl_target_manifest_output(args, manifest)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return

    if args.command in {"realestate-alias-candidates", "realestate-alias-candidates-push"}:
        candidates = _real_estate_alias_candidates_from_args(args)
        if args.command == "realestate-alias-candidates":
            print(json.dumps({"items": [candidate.to_request_dict() for candidate in candidates]}, ensure_ascii=False, indent=2))
            return
        client = _spring_client()
        client.publish_real_estate_alias_candidates(candidates)
        return

    if args.command == "realestate-reaction-observations":
        if not args.community_posts_jsonl:
            raise SystemExit("--community-posts-jsonl is required")
        observations = _real_estate_reaction_observations_from_posts(args)
        print(
            json.dumps(
                {"items": [real_estate_reaction_observation_to_dict(observation) for observation in observations]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command in {
        "realestate-reaction-snapshots-from-posts",
        "realestate-reaction-snapshots-from-posts-push",
    }:
        if not args.community_posts_jsonl:
            raise SystemExit("--community-posts-jsonl is required")
        if not args.reaction_window_start:
            raise SystemExit("--reaction-window-start is required")
        observations = _real_estate_reaction_observations_from_posts(args)
        snapshots = build_real_estate_reaction_snapshots(
            observations,
            window_start=parse_reaction_datetime(args.reaction_window_start),
            window_minutes=args.reaction_window_minutes,
            as_of=parse_reaction_datetime(args.reaction_as_of) if args.reaction_as_of else None,
            stale_after_minutes=args.reaction_stale_after_minutes,
        )
        if args.command == "realestate-reaction-snapshots-from-posts":
            print(json.dumps({"items": [snapshot.to_request_dict() for snapshot in snapshots]}, ensure_ascii=False, indent=2))
            return
        client = _spring_client()
        client.publish_real_estate_reaction_snapshots(snapshots)
        return

    if args.command in {"realestate-reaction-snapshots", "realestate-reaction-snapshots-push"}:
        if not args.reaction_observations_jsonl:
            raise SystemExit("--reaction-observations-jsonl is required")
        if not args.reaction_window_start:
            raise SystemExit("--reaction-window-start is required")
        observations = load_real_estate_reaction_observations(args.reaction_observations_jsonl)
        observations = _roll_up_real_estate_reaction_observations_from_args(args, observations)
        snapshots = build_real_estate_reaction_snapshots(
            observations,
            window_start=parse_reaction_datetime(args.reaction_window_start),
            window_minutes=args.reaction_window_minutes,
            as_of=parse_reaction_datetime(args.reaction_as_of) if args.reaction_as_of else None,
            stale_after_minutes=args.reaction_stale_after_minutes,
        )
        if args.command == "realestate-reaction-snapshots":
            print(json.dumps({"items": [snapshot.to_request_dict() for snapshot in snapshots]}, ensure_ascii=False, indent=2))
            return
        client = _spring_client()
        client.publish_real_estate_reaction_snapshots(snapshots)
        return

    if args.command in {"realestate-recent-issues", "realestate-recent-issues-push"}:
        if not args.realestate_search_targets_jsonl:
            raise SystemExit("--realestate-search-targets-jsonl is required")
        targets = load_recent_issue_search_targets(args.realestate_search_targets_jsonl)
        items = build_recent_issue_content_items(
            targets=targets,
            search_client=_serpapi_recent_issue_client(),
            issue_keywords=tuple(args.realestate_issue_keywords or ()),
            ingested_at=_parse_cli_datetime(args.realestate_search_as_of) if args.realestate_search_as_of else datetime.now(timezone.utc),
            result_limit=args.serpapi_result_limit,
        )
        if args.command == "realestate-recent-issues":
            print(json.dumps({"items": [item.to_content_item_dict() for item in items]}, ensure_ascii=False, indent=2))
            return
        client = _spring_client()
        client.publish_real_estate_content_items(items)
        return

    if args.command == "realestate-similar-windows":
        if not args.reaction_snapshots_jsonl:
            raise SystemExit("--reaction-snapshots-jsonl is required")
        if not args.similar_source_target_id:
            raise SystemExit("--similar-source-target-id is required")
        if not args.similar_source_window_start:
            raise SystemExit("--similar-source-window-start is required")
        market_facts = (
            load_real_estate_market_fact_payloads(args.similar_market_facts_jsonl)
            if args.similar_market_facts_jsonl
            else []
        )
        matches = find_real_estate_similar_windows(
            load_real_estate_reaction_snapshot_payloads(args.reaction_snapshots_jsonl),
            source_target_id=args.similar_source_target_id,
            source_window_start=args.similar_source_window_start,
            market_facts=market_facts,
            horizon_days=args.similar_horizon_days,
            top_n=args.similar_top_n,
        )
        print(json.dumps({"items": [match.to_dict() for match in matches]}, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-embeddings":
        if not args.reaction_snapshots_jsonl:
            raise SystemExit("--reaction-snapshots-jsonl is required")
        inputs = build_real_estate_embedding_inputs(
            load_real_estate_embedding_inputs(args.reaction_snapshots_jsonl),
            model_name=args.embedding_model_name,
        )
        if not inputs:
            print(json.dumps({"items": []}, ensure_ascii=False, indent=2))
            return
        embedding_client = _gms_gemini_embedding_client(
            model_name=args.embedding_model_name,
            timeout_seconds=args.embedding_timeout_seconds,
        )
        print(
            json.dumps(
                {
                    "items": [
                        item.to_embedding_dict(embedding_client.embed_text(item.text))
                        for item in inputs
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "realestate-vector-upsert":
        if not args.embeddings_jsonl:
            raise SystemExit("--embeddings-jsonl is required")
        embedding_items = load_real_estate_embedding_payloads(args.embeddings_jsonl)
        points = build_qdrant_points(embedding_items)
        if not points:
            print(json.dumps({"collection": DEFAULT_QDRANT_COLLECTION, "vectorSize": 0, "upsertedPoints": 0}, ensure_ascii=False, indent=2))
            return
        vector_size = len(points[0]["vector"])
        vector_client = _qdrant_vector_store_client()
        vector_client.ensure_collection(vector_size=vector_size)
        vector_client.upsert_points(points)
        print(
            json.dumps(
                {
                    "collection": vector_client.collection_name,
                    "vectorSize": vector_size,
                    "upsertedPoints": len(points),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "realestate-vector-search":
        if not args.embeddings_jsonl:
            raise SystemExit("--embeddings-jsonl is required")
        if not args.vector_source_input_id:
            raise SystemExit("--vector-source-input-id is required")
        embedding_items = load_real_estate_embedding_payloads(args.embeddings_jsonl)
        source_input = find_embedding_by_input_id(embedding_items, args.vector_source_input_id)
        vector_client = _qdrant_vector_store_client()
        search_results = vector_client.search(
            vector=source_input["embedding"],
            top_n=args.vector_top_n,
            exclude_input_id=source_input["inputId"],
        )
        print(
            json.dumps(
                {
                    "items": qdrant_search_results_to_similar_windows(
                        source_input=source_input,
                        search_results=search_results,
                    )
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command in {"realestate-evidence-logs", "realestate-evidence-logs-push"}:
        if not args.reaction_snapshots_jsonl:
            raise SystemExit("--reaction-snapshots-jsonl is required")
        if not args.evidence_target_id:
            raise SystemExit("--evidence-target-id is required")
        if not args.evidence_window_start:
            raise SystemExit("--evidence-window-start is required")
        evaluated_at = args.evidence_evaluated_at or datetime.now(timezone.utc)
        logs = build_real_estate_evidence_logs(
            load_real_estate_evidence_reaction_snapshots(args.reaction_snapshots_jsonl),
            target_id=args.evidence_target_id,
            window_start=args.evidence_window_start,
            evaluated_at=evaluated_at,
            market_facts=(
                load_real_estate_evidence_market_facts(args.evidence_market_facts_jsonl)
                if args.evidence_market_facts_jsonl
                else []
            ),
            timeline_events=(
                load_real_estate_evidence_timeline_events(args.evidence_timeline_events_jsonl)
                if args.evidence_timeline_events_jsonl
                else []
            ),
            similar_windows=(
                load_real_estate_evidence_similar_windows(args.evidence_similar_windows_jsonl)
                if args.evidence_similar_windows_jsonl
                else []
            ),
            content_items=(
                load_real_estate_evidence_content_items(args.evidence_content_items_jsonl)
                if args.evidence_content_items_jsonl
                else []
            ),
            evaluation_version=args.evidence_evaluation_version,
            prompt_version=args.evidence_prompt_version,
            model_name=args.evidence_model_name,
        )
        if args.evidence_use_gms_llm:
            evaluation_client = _gms_openai_evaluation_client(
                model_name=args.evidence_llm_model,
                timeout_seconds=args.evidence_llm_timeout_seconds,
            )
            logs = [
                apply_real_estate_llm_evaluation(
                    log,
                    evaluation_client.evaluate(log),
                    model_name=args.evidence_llm_model,
                    prompt_version=args.evidence_llm_prompt_version,
                )
                for log in logs
            ]
        if args.command == "realestate-evidence-logs":
            print(json.dumps({"logs": logs}, ensure_ascii=False, indent=2))
            return
        client = _spring_client()
        client.publish_real_estate_evidence_logs(logs)
        return

    if args.command in {"realestate-market-facts", "realestate-market-facts-push"}:
        if not args.realestate_deal_ym:
            raise SystemExit("--realestate-deal-ym is required")
        provider = build_molit_public_data_client_from_env()
        spring_client = _spring_client()
        if args.realestate_use_backend_targets:
            targets = spring_client.list_real_estate_market_data_targets(enabled=True)
            facts = collect_molit_real_estate_market_facts_from_data_targets(
                provider,
                targets,
                deal_ym=args.realestate_deal_ym,
                page_size=args.realestate_public_data_page_size,
                max_pages=args.realestate_public_data_max_pages,
            )
        else:
            if not args.realestate_lawd_code:
                raise SystemExit("--realestate-lawd-code is required unless --realestate-use-backend-targets is set")
            facts = collect_molit_real_estate_market_facts(
                provider,
                lawd_code=args.realestate_lawd_code,
                deal_ym=args.realestate_deal_ym,
                datasets=args.realestate_datasets,
                page_size=args.realestate_public_data_page_size,
                max_pages=args.realestate_public_data_max_pages,
            )
        if args.command == "realestate-market-facts":
            print(json.dumps({"items": [fact.to_ingestion_dict() for fact in facts]}, ensure_ascii=False, indent=2))
            return
        spring_client.publish_real_estate_market_facts(facts)
        return

    if args.command == "realestate-market-facts-raw-push":
        spring_client = _spring_client()
        tasks, skipped_completed_run_keys, planned_run_count = _realestate_raw_push_task_selection(
            args,
            spring_client=spring_client,
        )
        _require_realestate_large_run_confirmation(args, tasks)
        provider = build_molit_public_data_client_from_env() if tasks else None
        run_summaries = []
        for task in tasks:
            started_at = datetime.now(timezone.utc)
            facts = collect_molit_real_estate_market_facts(
                provider,
                lawd_code=task.lawd_code,
                deal_ym=task.deal_ym,
                datasets=[_dataset_alias_from_fact_type(task.fact_type)],
                page_size=args.realestate_public_data_page_size,
                max_pages=args.realestate_public_data_max_pages,
                now=started_at,
            )
            ingestions = build_molit_raw_ingestions(
                facts,
                lawd_code=task.lawd_code,
                deal_ym=task.deal_ym,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
            )
            if not ingestions:
                ingestions = [
                    RealEstatePublicDataRawIngestion(
                        run_key=task.run_key,
                        provider_dataset=task.provider_dataset,
                        lawd_code=task.lawd_code,
                        deal_ym=task.deal_ym,
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                        facts=tuple(),
                    )
                ]
            for ingestion in ingestions:
                promoted = False
                promoted_facts = None
                spring_client.publish_real_estate_public_data_raw_ingestion(ingestion)
                if args.realestate_promote_after_raw_push:
                    promote_result = spring_client.promote_real_estate_public_data_staging(
                        provider_dataset=ingestion.provider_dataset,
                        run_key=ingestion.run_key,
                        validation_status=args.realestate_validation_status,
                        limit=args.realestate_promote_limit,
                    )
                    promoted = True
                    promoted_facts = promote_result.get("promotedFacts") if isinstance(promote_result, dict) else None
                raw_items = len(ingestion.facts)
                run_summaries.append(
                    {
                        "runKey": ingestion.run_key,
                        "providerDataset": ingestion.provider_dataset,
                        "lawdCode": ingestion.lawd_code,
                        "dealYm": ingestion.deal_ym,
                        "fetchedFacts": len(facts),
                        "rawItems": raw_items,
                        "empty": raw_items == 0,
                        "promoted": promoted,
                        "promotedFacts": promoted_facts,
                    }
                )
        payload = {
            "taskCount": len(tasks),
            "publishedRuns": len(run_summaries),
            "publishedItems": sum(item["rawItems"] for item in run_summaries),
            "emptyRuns": sum(1 for item in run_summaries if item["empty"]),
            "promotedRuns": sum(1 for item in run_summaries if item["promoted"]),
            "items": run_summaries,
        }
        if args.realestate_skip_completed_runs:
            payload = {
                "plannedRuns": planned_run_count,
                "skippedCompletedRuns": skipped_completed_run_keys,
                **payload,
            }
        if args.realestate_run_limit > 0:
            payload = {
                "plannedRuns": planned_run_count,
                **_realestate_run_limit_payload(args, planned_run_count, skipped_completed_run_keys, tasks),
                **payload,
            }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-regional-stat-csv-inspect":
        if not args.realestate_stat_csv:
            raise SystemExit("--realestate-stat-csv is required")
        if not args.realestate_provider:
            raise SystemExit("--realestate-provider is required")
        if not args.realestate_provider_dataset:
            raise SystemExit("--realestate-provider-dataset is required")
        if not args.realestate_fact_type:
            raise SystemExit("--realestate-fact-type is required")

        csv_path = Path(args.realestate_stat_csv)
        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            manifest = inspect_regional_stat_csv(
                csv_file,
                provider=args.realestate_provider,
                provider_dataset=args.realestate_provider_dataset,
                fact_type=args.realestate_fact_type,
                batch_size=args.realestate_stat_batch_size,
                source_label=str(csv_path),
                default_unit=args.realestate_stat_unit,
                ingested_at=datetime.now(timezone.utc),
            )
        print(json.dumps(manifest.to_payload(), ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-regional-stat-csv-raw-push":
        if not args.realestate_stat_csv:
            raise SystemExit("--realestate-stat-csv is required")
        if not args.realestate_provider:
            raise SystemExit("--realestate-provider is required")
        if not args.realestate_provider_dataset:
            raise SystemExit("--realestate-provider-dataset is required")
        if not args.realestate_fact_type:
            raise SystemExit("--realestate-fact-type is required")

        csv_path = Path(args.realestate_stat_csv)
        started_at = datetime.now(timezone.utc)
        spring_client = _spring_client()
        run_summaries = []
        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            facts = iter_regional_stat_market_facts(
                csv_file,
                provider=args.realestate_provider,
                provider_dataset=args.realestate_provider_dataset,
                fact_type=args.realestate_fact_type,
                default_unit=args.realestate_stat_unit,
                ingested_at=started_at,
            )
            for ingestion in build_regional_stat_raw_ingestions(
                facts,
                provider_dataset=args.realestate_provider_dataset,
                started_at=started_at,
                batch_size=args.realestate_stat_batch_size,
                source_label=str(csv_path),
                finished_at=datetime.now(timezone.utc),
            ):
                promoted = False
                promoted_facts = None
                spring_client.publish_real_estate_public_data_raw_ingestion(ingestion)
                if args.realestate_promote_after_raw_push:
                    promote_result = spring_client.promote_real_estate_public_data_staging(
                        provider_dataset=ingestion.provider_dataset,
                        run_key=ingestion.run_key,
                        validation_status=args.realestate_validation_status,
                        limit=args.realestate_promote_limit,
                    )
                    promoted = True
                    promoted_facts = promote_result.get("promotedFacts") if isinstance(promote_result, dict) else None
                run_summaries.append(
                    {
                        "runKey": ingestion.run_key,
                        "providerDataset": ingestion.provider_dataset,
                        "rawItems": len(ingestion.facts),
                        "promoted": promoted,
                        "promotedFacts": promoted_facts,
                    }
                )
        print(
            json.dumps(
                {
                    "publishedRuns": len(run_summaries),
                    "publishedItems": sum(item["rawItems"] for item in run_summaries),
                    "promotedRuns": sum(1 for item in run_summaries if item["promoted"]),
                    "items": run_summaries,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "realestate-official-apartment-prices-inspect":
        if not args.realestate_official_apartment_price_csv:
            raise SystemExit("--realestate-official-apartment-price-csv is required")
        if not args.realestate_official_apartment_price_base_date:
            raise SystemExit("--realestate-official-apartment-price-base-date is required")

        csv_path = Path(args.realestate_official_apartment_price_csv)
        base_date = date.fromisoformat(args.realestate_official_apartment_price_base_date)
        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            manifest = inspect_official_apartment_price_csv(
                csv_file,
                base_date=base_date,
                batch_size=args.realestate_official_apartment_price_batch_size,
                source_label=str(csv_path),
                ingested_at=datetime.now(timezone.utc),
            )
        print(json.dumps(manifest.to_payload(), ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-official-apartment-prices-raw-push":
        if not args.realestate_official_apartment_price_csv:
            raise SystemExit("--realestate-official-apartment-price-csv is required")
        if not args.realestate_official_apartment_price_base_date:
            raise SystemExit("--realestate-official-apartment-price-base-date is required")

        csv_path = Path(args.realestate_official_apartment_price_csv)
        base_date = date.fromisoformat(args.realestate_official_apartment_price_base_date)
        started_at = datetime.now(timezone.utc)
        spring_client = _spring_client()
        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            facts = iter_official_apartment_price_market_facts(csv_file, ingested_at=started_at)
            for ingestion in build_official_apartment_price_raw_ingestions(
                facts,
                base_date=base_date,
                started_at=started_at,
                batch_size=args.realestate_official_apartment_price_batch_size,
                source_label=str(csv_path),
                finished_at=datetime.now(timezone.utc),
            ):
                spring_client.publish_real_estate_public_data_raw_ingestion(ingestion)
                if args.realestate_promote_after_raw_push:
                    spring_client.promote_real_estate_public_data_staging(
                        provider_dataset=ingestion.provider_dataset,
                        run_key=ingestion.run_key,
                        validation_status=args.realestate_validation_status,
                        limit=args.realestate_promote_limit,
                    )
        return

    if args.command == "realestate-market-facts-promote-staging":
        spring_client = _spring_client()
        result = spring_client.promote_real_estate_public_data_staging(
            provider_dataset=args.realestate_provider_dataset,
            run_key=args.realestate_run_key,
            validation_status=args.realestate_validation_status,
            limit=args.realestate_promote_limit,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    pipeline = build_pipeline()
    if args.command == "run-once":
        results = await pipeline.run_once()
        for result in results:
            print(result)
    else:
        realestate_market_facts_refresh_job = None
        realestate_reaction_snapshot_refresh_job = None
        realestate_daily_refresh_job = None
        market_client = _spring_client()
        if args.enable_realestate_market_facts_refresh:
            if not args.realestate_deal_ym:
                raise SystemExit("--realestate-deal-ym is required when real-estate market facts refresh is enabled")
            realestate_market_facts_refresh_job = build_real_estate_market_facts_refresh_job(
                client=market_client,
                deal_ym=args.realestate_deal_ym,
            )
        if args.enable_realestate_reaction_snapshots_refresh:
            if not args.realestate_aliases_jsonl:
                raise SystemExit("--realestate-aliases-jsonl is required when real-estate reaction snapshot refresh is enabled")
            if not args.community_posts_jsonl:
                raise SystemExit("--community-posts-jsonl is required when real-estate reaction snapshot refresh is enabled")
            realestate_reaction_snapshot_refresh_job = build_real_estate_reaction_snapshot_refresh_job(
                client=market_client,
                aliases_jsonl=args.realestate_aliases_jsonl,
                community_posts_jsonl=args.community_posts_jsonl,
                window_minutes=args.reaction_window_minutes,
                target_edges_jsonl=args.realestate_target_edges_jsonl,
                stale_after_minutes=args.reaction_stale_after_minutes,
            )
        if args.enable_realestate_recent_issues_refresh and not args.enable_realestate_daily_refresh:
            raise SystemExit("--enable-realestate-recent-issues-refresh requires --enable-realestate-daily-refresh")
        if args.enable_realestate_evidence_logs_refresh and not args.enable_realestate_daily_refresh:
            raise SystemExit("--enable-realestate-evidence-logs-refresh requires --enable-realestate-daily-refresh")
        if args.enable_realestate_map_layer_refresh and not args.enable_realestate_daily_refresh:
            raise SystemExit("--enable-realestate-map-layer-refresh requires --enable-realestate-daily-refresh")
        if args.enable_realestate_daily_refresh:
            daily_steps = []
            if realestate_market_facts_refresh_job is not None:
                daily_steps.append(("market_facts", realestate_market_facts_refresh_job))
                realestate_market_facts_refresh_job = None
            if realestate_reaction_snapshot_refresh_job is not None:
                daily_steps.append(("reaction_snapshots", realestate_reaction_snapshot_refresh_job))
                realestate_reaction_snapshot_refresh_job = None
            if args.enable_realestate_recent_issues_refresh:
                if not args.realestate_search_targets_jsonl:
                    raise SystemExit("--realestate-search-targets-jsonl is required when real-estate recent issues refresh is enabled")
                daily_steps.append(
                    (
                        "recent_issues",
                        RealEstateRecentIssuesRefreshJob(
                            client=market_client,
                            search_client=_serpapi_recent_issue_client(),
                            search_targets_jsonl=args.realestate_search_targets_jsonl,
                            issue_keywords=args.realestate_issue_keywords,
                            result_limit=args.serpapi_result_limit,
                        ),
                    )
                )
            if args.enable_realestate_map_layer_refresh:
                daily_steps.append(
                    (
                        "map_layers",
                        RealEstateMapLayerRefreshJob(
                            client=market_client,
                            layer_types=args.realestate_map_layer_types,
                            periods=args.realestate_map_layer_periods,
                        ),
                    )
                )
            if args.enable_realestate_evidence_logs_refresh:
                evidence_llm_evaluator = None
                if args.evidence_use_gms_llm:
                    evidence_llm_client = _gms_openai_evaluation_client(
                        model_name=args.evidence_llm_model,
                        timeout_seconds=args.evidence_llm_timeout_seconds,
                    )

                    def evidence_llm_evaluator(log):
                        return apply_real_estate_llm_evaluation(
                            log,
                            evidence_llm_client.evaluate(log),
                            model_name=args.evidence_llm_model,
                            prompt_version=args.evidence_llm_prompt_version,
                        )

                daily_steps.append(
                    (
                        "evidence_logs",
                        RealEstateEvidenceLogRefreshJob(
                            client=market_client,
                            target_type=args.realestate_evidence_target_type,
                            window_minutes=args.reaction_window_minutes,
                            ranking_limit=args.realestate_evidence_ranking_limit,
                            market_fact_limit=args.realestate_evidence_market_fact_limit,
                            timeline_limit=args.realestate_evidence_timeline_limit,
                            content_limit=args.realestate_evidence_content_limit,
                            llm_evaluator=evidence_llm_evaluator,
                        ),
                    )
                )
            if not daily_steps:
                raise SystemExit(
                    "--enable-realestate-daily-refresh requires at least one real-estate refresh step "
                    "(market facts, reaction snapshots, recent issues, map layers, or evidence logs)"
                )
            realestate_daily_refresh_job = RealEstateDailyRefreshJob(daily_steps)
        await serve(
            pipeline,
            interval_minutes=args.interval_minutes,
            realestate_market_facts_refresh_job=realestate_market_facts_refresh_job,
            realestate_market_facts_interval_minutes=args.realestate_market_facts_refresh_interval_minutes,
            realestate_reaction_snapshot_refresh_job=realestate_reaction_snapshot_refresh_job,
            realestate_reaction_snapshot_interval_minutes=args.realestate_reaction_snapshots_refresh_interval_minutes,
            realestate_daily_refresh_job=realestate_daily_refresh_job,
            realestate_daily_refresh_interval_minutes=args.realestate_daily_refresh_interval_minutes,
        )


def _configured_realestate_datasets(value: str | None) -> list[str]:
    if not value:
        return ["trade", "rent"]
    return [dataset.strip() for dataset in value.split(",") if dataset.strip()]


def _configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if not reconfigure:
        return
    try:
        reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        return


def _configured_realestate_lawd_codes(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [lawd_code.strip() for lawd_code in value.split(",") if lawd_code.strip()]


def _configured_issue_keywords(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [keyword.strip() for keyword in value.split(",") if keyword.strip()]


def _configured_csv_values(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _realestate_raw_push_tasks(args, spring_client=None) -> list:
    return _realestate_raw_push_task_selection(args, spring_client=spring_client)[0]


def _realestate_public_data_preflight_payload(args) -> dict:
    spring_client = _spring_client() if args.realestate_use_backend_targets or args.realestate_skip_completed_runs else None
    tasks, skipped_completed_run_keys, planned_run_count = _realestate_raw_push_task_selection(
        args,
        spring_client=spring_client,
    )
    service_key_configured = bool((os.getenv(DATA_GO_SERVICE_KEY_ENV) or "").strip())
    data_go_service_key_status = "not_required"
    missing = []
    if tasks:
        data_go_service_key_status = "configured" if service_key_configured else "missing"
        if not service_key_configured:
            missing.append(DATA_GO_SERVICE_KEY_ENV)

    period = _realestate_backfill_period_from_args(args, tasks)
    return {
        "ready": not missing,
        "missing": missing,
        "checks": {
            "dataGoServiceKey": data_go_service_key_status,
            "backendTargets": "used" if args.realestate_use_backend_targets else "not_required",
            "completedRunSkip": "used" if args.realestate_skip_completed_runs else "not_requested",
        },
        "plannedRuns": planned_run_count,
        "remainingRuns": len(tasks),
        "skippedCompletedRuns": skipped_completed_run_keys,
        "willCallPublicApi": bool(tasks) and service_key_configured,
        "promoteAfterRawPush": bool(args.realestate_promote_after_raw_push),
        "pageSize": args.realestate_public_data_page_size,
        "maxPages": args.realestate_public_data_max_pages,
        "period": period,
        "datasets": _unique_in_order([task.provider_dataset for task in tasks]),
        "lawdCodes": _unique_in_order([task.lawd_code for task in tasks]),
        **_realestate_run_limit_payload(args, planned_run_count, skipped_completed_run_keys, tasks),
        **_realestate_large_run_payload(args, tasks),
    }


def _realestate_regions_inspect_payload(args) -> dict:
    csv_text = Path(args.legal_dong_code_csv).read_text(encoding="utf-8-sig")
    regions = parse_molit_legal_dong_code_csv(csv_text)
    market_data_targets = build_molit_region_market_data_targets(regions, datasets=args.realestate_datasets)
    backfill_tasks = _realestate_region_backfill_tasks(args, market_data_targets)
    if backfill_tasks:
        _write_realestate_backfill_plan_output(args, {"items": [task.to_payload() for task in backfill_tasks]})

    return {
        "source": "import:molit-legal-dong-code",
        "regionCount": len(regions),
        "regionLevelCounts": _realestate_region_level_counts(regions),
        "marketDataTargetCount": len(market_data_targets),
        "backfillPlan": {
            "plannedRuns": len(backfill_tasks),
            "period": _realestate_backfill_period_from_args(args, backfill_tasks),
            "datasets": _unique_in_order([task.provider_dataset for task in backfill_tasks]),
            "lawdCodes": _unique_in_order([task.lawd_code for task in backfill_tasks]),
        },
        "sampleRegions": [region.to_import_dict() for region in regions[:5]],
        "sampleMarketDataTargets": [target.to_import_dict() for target in market_data_targets[:10]],
    }


def _realestate_region_backfill_tasks(args, market_data_targets: list) -> list:
    start_ym = args.realestate_deal_ym or args.realestate_start_ym
    end_ym = args.realestate_deal_ym or args.realestate_end_ym or start_ym
    if not start_ym or not end_ym:
        return []
    lawd_codes = _unique_in_order([target.lawd_code for target in market_data_targets])
    if not lawd_codes:
        return []
    return build_molit_backfill_plan(
        lawd_codes=lawd_codes,
        start_ym=start_ym,
        end_ym=end_ym,
        datasets=args.realestate_datasets,
    )


def _realestate_region_level_counts(regions: list) -> dict:
    counts: dict[str, int] = {}
    for region in regions:
        counts[region.region_level] = counts.get(region.region_level, 0) + 1
    return counts


def _write_realestate_backfill_plan_output(args, payload: dict) -> None:
    output_path = getattr(args, "realestate_backfill_plan_output", None)
    if not output_path:
        return
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _realestate_backfill_plan_payload(args, plan: list) -> dict:
    chunk_size = int(getattr(args, "realestate_backfill_chunk_size", 0) or 0)
    if chunk_size <= 0:
        return {"items": [task.to_payload() for task in plan]}
    chunks = chunk_molit_backfill_plan(plan, chunk_size=chunk_size)
    return {
        "plannedRuns": len(plan),
        "remainingRuns": len(plan),
        "chunkSize": chunk_size,
        "chunkCount": len(chunks),
        "chunks": [chunk.to_payload() for chunk in chunks],
    }


def _write_realestate_crawl_target_manifest_output(args, payload: dict) -> None:
    output_path = getattr(args, "realestate_crawl_target_manifest_output", None)
    if not output_path:
        return
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _realestate_backfill_period_from_args(args, tasks: list | None = None) -> dict:
    start_ym = args.realestate_deal_ym or args.realestate_start_ym
    end_ym = args.realestate_deal_ym or args.realestate_end_ym or start_ym
    if (not start_ym or not end_ym) and tasks:
        deal_yms = [task.deal_ym for task in tasks]
        start_ym = min(deal_yms)
        end_ym = max(deal_yms)
    return {
        "startYm": start_ym,
        "endYm": end_ym,
    }


def _realestate_raw_push_task_selection(args, spring_client=None) -> tuple[list, list[str], int]:
    tasks = _realestate_raw_push_task_candidates(args, spring_client=spring_client)
    planned_run_count = len(tasks)
    if not args.realestate_skip_completed_runs:
        return _limit_realestate_run_tasks(args, tasks), [], planned_run_count

    client = spring_client or _spring_client()
    completed_run_keys = _realestate_completed_import_run_keys(client, tasks)
    remaining_tasks = [task for task in tasks if task.run_key not in completed_run_keys]
    skipped_completed_run_keys = [task.run_key for task in tasks if task.run_key in completed_run_keys]
    return _limit_realestate_run_tasks(args, remaining_tasks), skipped_completed_run_keys, planned_run_count


def _limit_realestate_run_tasks(args, tasks: list) -> list:
    limit = int(getattr(args, "realestate_run_limit", 0) or 0)
    if limit <= 0:
        return tasks
    return tasks[:limit]


def _realestate_run_limit_payload(args, planned_run_count: int, skipped_completed_run_keys: list[str], selected_tasks: list) -> dict:
    limit = int(getattr(args, "realestate_run_limit", 0) or 0)
    if limit <= 0:
        return {}
    available_after_skip = max(0, planned_run_count - len(skipped_completed_run_keys))
    return {
        "runLimit": limit,
        "omittedByRunLimit": max(0, available_after_skip - len(selected_tasks)),
    }


def _realestate_large_run_payload(args, selected_tasks: list) -> dict:
    threshold = int(getattr(args, "realestate_large_run_threshold", 0) or 0)
    if threshold <= 0:
        return {
            "largeRunThreshold": threshold,
            "largeRunRequiresConfirmation": False,
        }
    requires_confirmation = _realestate_large_run_requires_confirmation(args, selected_tasks)
    return {
        "largeRunThreshold": threshold,
        "largeRunRequiresConfirmation": requires_confirmation,
    }


def _realestate_large_run_requires_confirmation(args, selected_tasks: list) -> bool:
    threshold = int(getattr(args, "realestate_large_run_threshold", 0) or 0)
    if threshold <= 0:
        return False
    if getattr(args, "realestate_confirm_large_run", False):
        return False
    if int(getattr(args, "realestate_run_limit", 0) or 0) > 0:
        return False
    return len(selected_tasks) > threshold


def _require_realestate_large_run_confirmation(args, selected_tasks: list) -> None:
    if not _realestate_large_run_requires_confirmation(args, selected_tasks):
        return
    threshold = int(getattr(args, "realestate_large_run_threshold", 0) or 0)
    raise SystemExit(
        f"realestate-market-facts-raw-push selected {len(selected_tasks)} runs, above threshold {threshold}. "
        "Use --realestate-run-limit for sample runs or --realestate-confirm-large-run to execute all selected runs."
    )


def _realestate_raw_push_task_candidates(args, spring_client=None) -> list:
    if args.realestate_backfill_plan_json:
        return load_molit_backfill_plan_manifest(args.realestate_backfill_plan_json)

    if args.realestate_use_backend_targets:
        if not args.realestate_deal_ym and not args.realestate_start_ym:
            raise SystemExit("--realestate-deal-ym or --realestate-start-ym is required")
        start_ym = args.realestate_deal_ym or args.realestate_start_ym
        end_ym = args.realestate_deal_ym or args.realestate_end_ym
        if not end_ym:
            raise SystemExit("--realestate-end-ym is required when --realestate-deal-ym is not set")
        client = spring_client or _spring_client()
        return build_molit_backfill_plan_from_data_targets(
            client.list_real_estate_market_data_targets(enabled=True),
            start_ym=start_ym,
            end_ym=end_ym,
        )

    if args.realestate_deal_ym:
        lawd_codes = _realestate_requested_lawd_codes(args)
        if not lawd_codes:
            raise SystemExit("--realestate-lawd-code or --realestate-lawd-codes is required")
        return build_molit_backfill_plan(
            lawd_codes=lawd_codes,
            start_ym=args.realestate_deal_ym,
            end_ym=args.realestate_deal_ym,
            datasets=args.realestate_datasets,
        )

    if not args.realestate_start_ym:
        raise SystemExit("--realestate-start-ym is required when --realestate-deal-ym is not set")
    if not args.realestate_end_ym:
        raise SystemExit("--realestate-end-ym is required when --realestate-deal-ym is not set")
    lawd_codes = _realestate_requested_lawd_codes(args)
    if not lawd_codes:
        raise SystemExit("--realestate-lawd-codes is required for range backfill")
    return build_molit_backfill_plan(
        lawd_codes=lawd_codes,
        start_ym=args.realestate_start_ym,
        end_ym=args.realestate_end_ym,
        datasets=args.realestate_datasets,
    )


def _realestate_completed_import_run_keys(spring_client, tasks: list) -> set[str]:
    completed_run_keys: set[str] = set()
    run_keys = [task.run_key for task in tasks]
    for run_key_chunk in _chunks(run_keys, 100):
        runs = spring_client.list_real_estate_public_data_import_runs(
            run_keys=run_key_chunk,
            status="completed",
        )
        completed_run_keys.update(
            str(run.get("runKey", "")).strip()
            for run in runs
            if str(run.get("status", "")).strip().lower() == "completed"
        )
    return {run_key for run_key in completed_run_keys if run_key}


def _chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def _unique_in_order(values: list[str]) -> list[str]:
    seen = set()
    unique_values = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def _realestate_requested_lawd_codes(args) -> list[str]:
    if args.realestate_lawd_codes:
        return args.realestate_lawd_codes
    if args.realestate_lawd_code:
        return [args.realestate_lawd_code]
    return []


def _dataset_alias_from_fact_type(fact_type: str) -> str:
    if fact_type == "apt_trade":
        return "trade"
    if fact_type == "apt_rent":
        return "rent"
    raise ValueError(f"unsupported real-estate market fact type: {fact_type}")


def _real_estate_reaction_observations_from_posts(args) -> list:
    aliases = _load_real_estate_alias_rules_from_args(args)
    posts = load_real_estate_posts_for_matching(args.community_posts_jsonl)
    matched_posts = match_real_estate_posts(posts, aliases)
    observations = classify_real_estate_reaction_observations(
        matched_posts,
        classifier=RuleBasedRealEstateReactionClassifier(),
    )
    return _roll_up_real_estate_reaction_observations_from_args(args, observations)


def _real_estate_alias_candidates_from_args(args) -> list:
    if not args.community_posts_jsonl:
        raise SystemExit("--community-posts-jsonl is required")
    aliases = _load_real_estate_alias_rules_from_args(args)
    posts = load_real_estate_posts_for_matching(args.community_posts_jsonl)
    return suggest_real_estate_alias_candidates(posts, aliases)


def _load_real_estate_alias_rules_from_args(args, *, force_backend: bool = False) -> list[RealEstateAliasRule]:
    if force_backend or args.realestate_use_backend_aliases:
        return [
            _real_estate_alias_rule_from_mapping(item)
            for item in _spring_client().list_real_estate_aliases(
                review_state="approved",
                ambiguous=False,
            )
        ]
    if not args.realestate_aliases_jsonl:
        raise SystemExit("--realestate-aliases-jsonl is required")
    return load_real_estate_alias_rules(args.realestate_aliases_jsonl)


def _real_estate_alias_rule_from_mapping(item: dict) -> RealEstateAliasRule:
    return RealEstateAliasRule(
        target_type=str(item.get("targetType") or item.get("target_type") or "").strip(),
        target_id=str(item.get("targetId") or item.get("target_id") or "").strip(),
        alias=str(item.get("alias") or "").strip(),
        alias_type=str(item.get("aliasType") or item.get("alias_type") or "official").strip() or "official",
        review_state=str(item.get("reviewState") or item.get("review_state") or "approved").strip().lower(),
        confidence=float(item.get("confidence", 1.0)),
        ambiguous=bool(item.get("ambiguous", False)),
        source=str(item.get("source")).strip() if item.get("source") else None,
    )


def _real_estate_alias_rule_to_dict(alias: RealEstateAliasRule) -> dict:
    return {
        "targetType": alias.target_type,
        "targetId": alias.target_id,
        "alias": alias.alias,
        "aliasType": alias.alias_type,
        "reviewState": alias.review_state,
        "confidence": alias.confidence,
        "ambiguous": alias.ambiguous,
        "source": alias.source,
    }


def _roll_up_real_estate_reaction_observations_from_args(args, observations: list) -> list:
    edges = _load_real_estate_target_edge_rules_from_args(args)
    if not edges:
        return observations
    return roll_up_real_estate_reaction_observations(observations, edges)


def _load_real_estate_target_edge_rules_from_args(args, *, force_backend: bool = False) -> list[RealEstateTargetEdgeRule]:
    if force_backend or args.realestate_use_backend_target_edges:
        return [
            _real_estate_target_edge_rule_from_mapping(item)
            for item in _spring_client().list_real_estate_target_edges(
                review_state="approved",
                edge_type="contains",
                direction="both",
            )
        ]
    if not args.realestate_target_edges_jsonl:
        return []
    return load_real_estate_target_edge_rules(args.realestate_target_edges_jsonl)


def _real_estate_target_edge_rule_from_mapping(item: dict) -> RealEstateTargetEdgeRule:
    return RealEstateTargetEdgeRule(
        from_target_type=str(item.get("fromTargetType") or item.get("from_target_type") or "").strip(),
        from_target_id=str(item.get("fromTargetId") or item.get("from_target_id") or "").strip(),
        to_target_type=str(item.get("toTargetType") or item.get("to_target_type") or "").strip(),
        to_target_id=str(item.get("toTargetId") or item.get("to_target_id") or "").strip(),
        edge_type=str(item.get("edgeType") or item.get("edge_type") or "contains").strip().lower() or "contains",
        review_state=str(item.get("reviewState") or item.get("review_state") or "approved").strip().lower(),
        confidence=float(item.get("confidence", 1.0)),
        source=str(item.get("source")).strip() if item.get("source") else None,
    )


def _real_estate_target_edge_rule_to_dict(edge: RealEstateTargetEdgeRule) -> dict:
    return {
        "fromTargetType": edge.from_target_type,
        "fromTargetId": edge.from_target_id,
        "toTargetType": edge.to_target_type,
        "toTargetId": edge.to_target_id,
        "edgeType": edge.edge_type,
        "reviewState": edge.review_state,
        "confidence": edge.confidence,
        "source": edge.source,
    }


def _spring_client() -> SpringIngestionClient:
    return SpringIngestionClient(
        os.getenv("SPRING_BASE_URL", "http://localhost:8080"),
        timeout_seconds=float(os.getenv("SPRING_CLIENT_TIMEOUT_SECONDS", "60")),
    )


def _serpapi_recent_issue_client() -> SerpApiRecentIssueClient:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise SystemExit("SERPAPI_API_KEY is required")
    return SerpApiRecentIssueClient(
        api_key,
        timeout_seconds=float(os.getenv("SERPAPI_TIMEOUT_SECONDS", "30")),
    )


def _gms_gemini_embedding_client(
    *,
    model_name: str = DEFAULT_GMS_GEMINI_EMBEDDING_MODEL,
    timeout_seconds: float = 30.0,
) -> GmsGeminiEmbeddingClient:
    api_key = os.getenv("GMS_KEY")
    if not api_key:
        raise SystemExit("GMS_KEY is required")
    return GmsGeminiEmbeddingClient(
        api_key,
        base_url=os.getenv("GMS_GEMINI_BASE_URL", DEFAULT_GMS_GEMINI_BASE_URL),
        model_name=model_name,
        timeout_seconds=timeout_seconds,
    )


def _gms_openai_evaluation_client(
    *,
    model_name: str = DEFAULT_GMS_OPENAI_CHAT_MODEL,
    timeout_seconds: float = 30.0,
) -> GmsOpenAIChatEvaluationClient:
    api_key = os.getenv("GMS_KEY")
    if not api_key:
        raise SystemExit("GMS_KEY is required")
    return GmsOpenAIChatEvaluationClient(
        api_key,
        base_url=os.getenv("GMS_OPENAI_BASE_URL", DEFAULT_GMS_OPENAI_BASE_URL),
        model_name=model_name,
        timeout_seconds=timeout_seconds,
    )


def _qdrant_vector_store_client() -> QdrantRealEstateVectorStoreClient:
    base_url = os.getenv("QDRANT_URL")
    if not base_url:
        raise SystemExit("QDRANT_URL is required")
    return QdrantRealEstateVectorStoreClient(
        base_url=base_url,
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=os.getenv("REALESTATE_VECTOR_COLLECTION", DEFAULT_QDRANT_COLLECTION),
        timeout_seconds=float(os.getenv("QDRANT_TIMEOUT_SECONDS", "30")),
    )


def _parse_cli_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
