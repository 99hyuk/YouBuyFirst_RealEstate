from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import date, datetime, timedelta, timezone
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
from youbuyfirst_pipeline.crawlers.cafe_search import CAFE_SEARCH_SOURCES, CafeSearchAdapter
from youbuyfirst_pipeline.crawlers.dcinside import DcinsideAdapter
from youbuyfirst_pipeline.crawlers.fmkorea import FmkoreaAdapter
from youbuyfirst_pipeline.crawlers.generic_board import GenericLinkBoardAdapter, SUPPORTED_GENERIC_BOARD_SOURCES
from youbuyfirst_pipeline.crawlers.ppomppu import PpomppuAdapter
from youbuyfirst_pipeline.pipeline import CommunityPipeline
from youbuyfirst_pipeline.realestate_public_data import (
    DATA_GO_SERVICE_KEY_ENV,
    PublicDataProviderError,
    RealEstatePublicDataRawIngestion,
    build_reb_rone_monthly_price_index_client_from_env,
    build_reb_rone_regional_map_client_from_env,
    build_reb_rone_main_snapshot_client_from_env,
    build_official_apartment_price_raw_ingestions,
    build_regional_stat_raw_ingestions,
    build_molit_raw_ingestions,
    build_molit_public_data_client_from_env,
    collect_molit_real_estate_market_facts,
    collect_molit_real_estate_market_facts_from_data_targets,
    collect_reb_rone_main_snapshot_facts,
    collect_reb_rone_monthly_price_index_change_facts,
    collect_reb_rone_regional_map_facts,
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
from youbuyfirst_pipeline.realestate_complex_registry import (
    build_real_estate_complex_registry_from_market_facts,
    load_real_estate_complex_registry_market_facts,
)
from youbuyfirst_pipeline.realestate_community_complex_seed import (
    COMMUNITY_TRADE_TABLE_SOURCE,
    build_observed_community_complex_seed_registry,
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
    real_estate_posts_for_matching_from_records,
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
    RealEstateCommunityCrawlRefreshJob,
    RealEstateCommunityComplexSeedRefreshJob,
    RealEstateComplexRegistryRefreshJob,
    RealEstateConfigMissingRefreshJob,
    RealEstateDailyRefreshJob,
    RealEstateEvidenceLogRefreshJob,
    RealEstateMapLayerRefreshJob,
    RealEstateOfficialStatsRefreshJob,
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
    qdrant_collection_health_payload,
    qdrant_search_results_to_similar_windows,
)
from youbuyfirst_pipeline.realestate_source_registry import (
    build_real_estate_crawl_target_manifest,
    load_real_estate_source_candidates_jsonl,
)
from youbuyfirst_pipeline.realestate_reaction_scheduler import build_real_estate_reaction_snapshot_refresh_job
from youbuyfirst_pipeline.realestate_regions import (
    build_real_estate_region_alias_requests,
    build_molit_region_market_data_targets,
    parse_molit_legal_dong_code_csv,
)
from youbuyfirst_pipeline.realestate_scheduler import build_real_estate_market_facts_refresh_job
from youbuyfirst_pipeline.realestate_target_graph import (
    RealEstateTargetEdgeRule,
    load_real_estate_target_edge_rules,
    roll_up_real_estate_reaction_observations,
)
from youbuyfirst_pipeline.realestate_top10_readiness import build_real_estate_top10_readiness
from youbuyfirst_pipeline.scheduler import serve
from youbuyfirst_pipeline.source_policy import default_source_policy_registry, runtime_environment_from_env


logger = logging.getLogger(__name__)


ACTIVE_COMMANDS = [
    "run-once",
    "serve",
    "realestate-market-facts",
    "realestate-market-facts-push",
    "realestate-reb-rone-main-snapshot",
    "realestate-reb-rone-main-snapshot-push",
    "realestate-reb-rone-monthly-price-index",
    "realestate-reb-rone-monthly-price-index-push",
    "realestate-reb-rone-regional-map",
    "realestate-reb-rone-regional-map-push",
    "realestate-market-facts-raw-push",
    "realestate-regional-stat-csv-inspect",
    "realestate-regional-stat-csv-raw-push",
    "realestate-official-apartment-prices-inspect",
    "realestate-official-apartment-prices-raw-push",
    "realestate-market-facts-promote-staging",
    "realestate-market-facts-backfill-plan",
    "realestate-complex-registry",
    "realestate-complex-registry-push",
    "realestate-community-complex-seeds",
    "realestate-community-complex-seeds-push",
    "realestate-top10-readiness",
    "realestate-public-data-preflight",
    "realestate-public-data-providers",
    "realestate-regions-inspect",
    "realestate-regions-import",
    "realestate-region-aliases",
    "realestate-region-aliases-push",
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
    "realestate-daily-refresh",
    "realestate-similar-windows",
    "realestate-embeddings",
    "realestate-vector-health",
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
        ignore_board_watermark=_env_flag("CRAWLER_IGNORE_WATERMARK", default=False),
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


def _env_flag(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
                    use_local_browser_fetch=_env_flag("CRAWLER_FMKOREA_USE_BROWSER_FETCH", default=False),
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
            adapters.append(
                PpomppuAdapter(
                    fetcher,
                    target=target,
                    stream_crawler=stream_crawler,
                    detail_content_max_posts=int(os.getenv("CRAWLER_DETAIL_CONTENT_MAX_POSTS_PER_SOURCE", "40")),
                    detail_content_max_chars=int(os.getenv("CRAWLER_DETAIL_CONTENT_MAX_CHARS", "1000")),
                )
            )
            continue
        if target.source in CAFE_SEARCH_SOURCES and target.kind == CrawlTargetKind.COMMUNITY_BOARD:
            adapters.append(CafeSearchAdapter(target=target))
            continue
        if target.source in SUPPORTED_GENERIC_BOARD_SOURCES and target.kind in {
            CrawlTargetKind.COMMUNITY_BOARD,
            CrawlTargetKind.GENERAL_BOARD_DIFFUSION,
        }:
            adapters.append(GenericLinkBoardAdapter(fetcher, target=target, stream_crawler=stream_crawler))
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
        "--realestate-market-facts-jsonl",
        default=os.getenv("REALESTATE_MARKET_FACTS_JSONL"),
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
        "--realestate-rone-geo-code",
        default=os.getenv("REALESTATE_RONE_GEO_CODE", "10"),
        help="REB R-ONE regional map geoCd. Use 10 for nationwide sido rows.",
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
        "--realestate-reaction-use-current-window",
        action="store_true",
        default=os.getenv("REALESTATE_REACTION_USE_CURRENT_WINDOW", "false").lower() in {"1", "true", "yes"},
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
        "--realestate-daily-reaction-window-minutes",
        type=int,
        default=int(os.getenv("REALESTATE_DAILY_REACTION_WINDOW_MINUTES", "10080")),
    )
    parser.add_argument(
        "--enable-realestate-daily-crawl-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_DAILY_CRAWL_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--enable-realestate-community-complex-seed-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_COMMUNITY_COMPLEX_SEED_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--enable-realestate-official-stats-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_OFFICIAL_STATS_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--enable-realestate-complex-registry-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_COMPLEX_REGISTRY_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-complex-registry-market-fact-limit",
        type=int,
        default=int(os.getenv("REALESTATE_COMPLEX_REGISTRY_MARKET_FACT_LIMIT", "1000")),
    )
    parser.add_argument(
        "--realestate-top10-readiness-limit",
        type=int,
        default=int(os.getenv("REALESTATE_TOP10_READINESS_LIMIT", "10")),
    )
    parser.add_argument(
        "--enable-realestate-recent-issues-refresh",
        action="store_true",
        default=os.getenv("REALESTATE_RECENT_ISSUES_REFRESH_ENABLED", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-recent-issues-target-type",
        default=os.getenv("REALESTATE_RECENT_ISSUES_TARGET_TYPE", "region"),
    )
    parser.add_argument(
        "--realestate-recent-issues-ranking-limit",
        type=int,
        default=int(os.getenv("REALESTATE_RECENT_ISSUES_RANKING_LIMIT", "10")),
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
        default=_configured_csv_values(os.getenv("REALESTATE_MAP_LAYER_PERIODS"), ["month", "quarter", "halfYear"]),
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
        "--realestate-use-backend-community-posts",
        action="store_true",
        default=os.getenv("REALESTATE_USE_BACKEND_COMMUNITY_POSTS", "false").lower() in {"1", "true", "yes"},
    )
    parser.add_argument(
        "--realestate-community-posts-source",
        default=os.getenv("REALESTATE_COMMUNITY_POSTS_SOURCE"),
    )
    parser.add_argument(
        "--realestate-community-posts-limit",
        type=int,
        default=int(os.getenv("REALESTATE_COMMUNITY_POSTS_LIMIT", "1000")),
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
        "--similar-engine",
        choices=("batch", "qdrant"),
        default=os.getenv("REALESTATE_SIMILAR_ENGINE", "batch"),
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

    if args.command in {"realestate-complex-registry", "realestate-complex-registry-push"}:
        if not args.realestate_market_facts_jsonl:
            raise SystemExit("--realestate-market-facts-jsonl is required")
        registry = _realestate_complex_registry_payload_from_args(args)
        if args.command == "realestate-complex-registry":
            print(json.dumps(registry.to_dict(), ensure_ascii=False, indent=2))
            return
        client = _spring_client()
        client.publish_real_estate_targets(registry.targets)
        client.publish_real_estate_complexes(registry.complexes)
        client.publish_real_estate_aliases(registry.aliases)
        client.publish_real_estate_target_edges(registry.edges)
        print(
            json.dumps(
                {
                    "publishedTargets": len(registry.targets),
                    "publishedComplexes": len(registry.complexes),
                    "publishedAliases": len(registry.aliases),
                    "publishedEdges": len(registry.edges),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command in {"realestate-community-complex-seeds", "realestate-community-complex-seeds-push"}:
        registry = _realestate_community_complex_seed_registry_from_args(args)
        observed_complex_target_ids = set(registry.observed_target_ids)
        if not observed_complex_target_ids:
            observed_complex_target_ids = {
                str(target.get("targetId") or target.get("target_id") or "").strip()
                for target in registry.targets
            }
            observed_complex_target_ids.update(
                str(alias.get("targetId") or alias.get("target_id") or "").strip()
                for alias in registry.aliases
            )
            observed_complex_target_ids = {target_id for target_id in observed_complex_target_ids if target_id}
        if args.command == "realestate-community-complex-seeds-push":
            client = _spring_client()
            client.publish_real_estate_targets(registry.targets)
            client.publish_real_estate_complexes(registry.complexes)
            client.publish_real_estate_aliases(registry.aliases)
            client.publish_real_estate_target_edges(registry.edges)
        print(
                json.dumps(
                    {
                        "observedComplexTargets": len(observed_complex_target_ids),
                        "publishedTargets": len(registry.targets) if args.command.endswith("-push") else 0,
                        "publishedComplexes": len(registry.complexes) if args.command.endswith("-push") else 0,
                        "publishedAliases": len(registry.aliases) if args.command.endswith("-push") else 0,
                        "publishedEdges": len(registry.edges) if args.command.endswith("-push") else 0,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "realestate-aliases-fetch":
        aliases = _load_real_estate_alias_rules_from_args(args, force_backend=True)
        print(json.dumps({"items": [_real_estate_alias_rule_to_dict(alias) for alias in aliases]}, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-target-edges-fetch":
        edges = _load_real_estate_target_edge_rules_from_args(args, force_backend=True)
        print(json.dumps({"items": [_real_estate_target_edge_rule_to_dict(edge) for edge in edges]}, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-top10-readiness":
        payload = build_real_estate_top10_readiness(
            _spring_client(),
            window_minutes=args.realestate_daily_reaction_window_minutes,
            limit=args.realestate_top10_readiness_limit,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
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

    if args.command in {"realestate-region-aliases", "realestate-region-aliases-push"}:
        client = _spring_client()
        regions = client.list_real_estate_regions(limit=1000)
        aliases = build_real_estate_region_alias_requests(regions)
        if args.command == "realestate-region-aliases-push":
            client.publish_real_estate_aliases(aliases)
        print(
            json.dumps(
                {
                    "regionCount": len(regions),
                    "aliasCount": len(aliases),
                    "publishedAliases": len(aliases) if args.command == "realestate-region-aliases-push" else 0,
                    "approvedAliases": sum(1 for alias in aliases if alias["reviewState"] == "approved"),
                    "candidateAliases": sum(1 for alias in aliases if alias["reviewState"] != "approved"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "realestate-target-matches":
        aliases = _load_real_estate_alias_rules_from_args(args)
        posts = _realestate_posts_for_matching_from_args(args)
        matched_posts = match_real_estate_posts(posts, aliases)
        print(json.dumps({"items": [post.to_dict() for post in matched_posts]}, ensure_ascii=False, indent=2))
        return

    if args.command == "realestate-alias-coverage":
        aliases = _load_real_estate_alias_rules_from_args(args)
        posts = _realestate_posts_for_matching_from_args(args)
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
        if args.similar_engine == "qdrant":
            if args.similar_top_n <= 0:
                raise SystemExit("--similar-top-n must be positive")
            if not args.embeddings_jsonl:
                raise SystemExit("--embeddings-jsonl is required")
            if not args.vector_source_input_id:
                raise SystemExit("--vector-source-input-id is required")
            embedding_items = load_real_estate_embedding_payloads(args.embeddings_jsonl)
            source_input = find_embedding_by_input_id(embedding_items, args.vector_source_input_id)
            market_facts = (
                load_real_estate_market_fact_payloads(args.similar_market_facts_jsonl)
                if args.similar_market_facts_jsonl
                else None
            )
            vector_client = _qdrant_vector_store_client()
            search_results = vector_client.search(
                vector=source_input["embedding"],
                top_n=_qdrant_similar_fetch_limit(args.similar_top_n),
                exclude_input_id=source_input["inputId"],
            )
            items = qdrant_search_results_to_similar_windows(
                source_input=source_input,
                search_results=search_results,
                market_facts=market_facts,
                horizon_days=args.similar_horizon_days,
            )[: args.similar_top_n]
            print(
                json.dumps(
                    {
                        "engine": "qdrant",
                        "items": items,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
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
        print(json.dumps({"engine": "batch", "items": [match.to_dict() for match in matches]}, ensure_ascii=False, indent=2))
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

    if args.command == "realestate-vector-health":
        vector_client = _qdrant_vector_store_client()
        print(json.dumps(qdrant_collection_health_payload(vector_client), ensure_ascii=False, indent=2))
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
        market_facts = (
            load_real_estate_market_fact_payloads(args.similar_market_facts_jsonl)
            if args.similar_market_facts_jsonl
            else None
        )
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
                        market_facts=market_facts,
                        horizon_days=args.similar_horizon_days,
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

    if args.command in {"realestate-reb-rone-main-snapshot", "realestate-reb-rone-main-snapshot-push"}:
        provider = build_reb_rone_main_snapshot_client_from_env()
        facts = collect_reb_rone_main_snapshot_facts(provider)
        if args.command == "realestate-reb-rone-main-snapshot":
            print(json.dumps({"items": [fact.to_ingestion_dict() for fact in facts]}, ensure_ascii=False, indent=2))
            return
        _spring_client().publish_real_estate_market_facts(facts)
        return

    if args.command in {"realestate-reb-rone-regional-map", "realestate-reb-rone-regional-map-push"}:
        provider = build_reb_rone_regional_map_client_from_env()
        facts = collect_reb_rone_regional_map_facts(provider, geo_cd=args.realestate_rone_geo_code)
        if args.command == "realestate-reb-rone-regional-map":
            print(json.dumps({"items": [fact.to_ingestion_dict() for fact in facts]}, ensure_ascii=False, indent=2))
            return
        _spring_client().publish_real_estate_market_facts(facts)
        return

    if args.command in {"realestate-reb-rone-monthly-price-index", "realestate-reb-rone-monthly-price-index-push"}:
        provider = build_reb_rone_monthly_price_index_client_from_env()
        facts = collect_reb_rone_monthly_price_index_change_facts(provider)
        if args.command == "realestate-reb-rone-monthly-price-index":
            print(json.dumps({"items": [fact.to_ingestion_dict() for fact in facts]}, ensure_ascii=False, indent=2))
            return
        _spring_client().publish_real_estate_market_facts(facts)
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
            facts = []
            provider_error = None
            try:
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
            except PublicDataProviderError as exc:
                provider_error = str(exc)[:500]
                ingestions = [
                    RealEstatePublicDataRawIngestion(
                        run_key=task.run_key,
                        provider_dataset=task.provider_dataset,
                        lawd_code=task.lawd_code,
                        deal_ym=task.deal_ym,
                        started_at=started_at,
                        finished_at=datetime.now(timezone.utc),
                        facts=tuple(),
                        status="provider_error",
                        error_message=provider_error,
                    )
                ]
            for ingestion in ingestions:
                promoted = False
                promoted_facts = None
                spring_client.publish_real_estate_public_data_raw_ingestion(ingestion)
                if args.realestate_promote_after_raw_push and ingestion.status == "completed":
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
                        "status": ingestion.status,
                        "providerError": provider_error,
                        "promoted": promoted,
                        "promotedFacts": promoted_facts,
                    }
                )
        payload = {
            "taskCount": len(tasks),
            "publishedRuns": len(run_summaries),
            "publishedItems": sum(item["rawItems"] for item in run_summaries),
            "emptyRuns": sum(1 for item in run_summaries if item["empty"]),
            "failedRuns": sum(1 for item in run_summaries if item["status"] != "completed"),
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

    pipeline = _build_pipeline_from_args(args)
    if args.command == "run-once":
        results = await pipeline.run_once()
        for result in results:
            print(result)
    elif args.command == "realestate-daily-refresh":
        market_client = _spring_client()
        daily_job = _build_real_estate_daily_refresh_job(args, pipeline, market_client)
        print(json.dumps(daily_job.run_once().to_dict(), ensure_ascii=False, indent=2))
    else:
        realestate_market_facts_refresh_job = None
        realestate_reaction_snapshot_refresh_job = None
        realestate_daily_refresh_job = None
        market_client = _spring_client()
        realestate_market_facts_refresh_job = _build_real_estate_market_facts_refresh_job_from_args(args, market_client)
        realestate_reaction_snapshot_refresh_job = _build_real_estate_reaction_snapshot_refresh_job_from_args(args, market_client)
        _validate_real_estate_serve_refresh_flags(args)
        if args.enable_realestate_daily_refresh:
            realestate_daily_refresh_job = _build_real_estate_daily_refresh_job(args, pipeline, market_client)
            realestate_market_facts_refresh_job = None
            realestate_reaction_snapshot_refresh_job = None
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


def _build_real_estate_market_facts_refresh_job_from_args(args, market_client):
    if not args.enable_realestate_market_facts_refresh:
        return None
    if not args.realestate_deal_ym:
        raise SystemExit("--realestate-deal-ym is required when real-estate market facts refresh is enabled")
    return build_real_estate_market_facts_refresh_job(
        client=market_client,
        deal_ym=args.realestate_deal_ym,
    )


def _build_real_estate_reaction_snapshot_refresh_job_from_args(args, market_client, *, window_minutes: int | None = None):
    if not args.enable_realestate_reaction_snapshots_refresh:
        return None
    aliases_jsonl = args.realestate_aliases_jsonl
    alias_loader = None
    use_backend_registry_from_complex_refresh = args.enable_realestate_complex_registry_refresh
    candidate_sources = (COMMUNITY_TRADE_TABLE_SOURCE,) if args.enable_realestate_community_complex_seed_refresh else ()
    if args.realestate_use_backend_aliases or use_backend_registry_from_complex_refresh:
        aliases_jsonl = None

        def load_backend_aliases() -> list[RealEstateAliasRule]:
            alias_items = list(
                market_client.list_real_estate_aliases(
                    review_state="approved",
                    ambiguous=False,
                )
            )
            if candidate_sources:
                alias_items.extend(
                    item
                    for item in market_client.list_real_estate_aliases(
                        review_state="candidate",
                        ambiguous=False,
                        target_type="complex",
                    )
                    if str(item.get("source") or "").strip() in candidate_sources
                )
            return [_real_estate_alias_rule_from_mapping(item) for item in alias_items]

        alias_loader = load_backend_aliases
    elif not aliases_jsonl:
        raise SystemExit("--realestate-aliases-jsonl is required when real-estate reaction snapshot refresh is enabled")
    if not args.community_posts_jsonl and not args.realestate_use_backend_community_posts:
        raise SystemExit("--community-posts-jsonl is required when real-estate reaction snapshot refresh is enabled")
    target_edges_jsonl = args.realestate_target_edges_jsonl
    target_edge_loader = None
    if args.realestate_use_backend_target_edges or use_backend_registry_from_complex_refresh:
        target_edges_jsonl = None

        def load_backend_target_edges() -> list[RealEstateTargetEdgeRule]:
            edge_items = list(
                market_client.list_real_estate_target_edges(
                    review_state="approved",
                    edge_type="contains",
                    direction="both",
                )
            )
            if candidate_sources:
                edge_items.extend(
                    item
                    for item in market_client.list_real_estate_target_edges(
                        review_state="candidate",
                        edge_type="contains",
                        direction="both",
                    )
                    if str(item.get("source") or "").strip() in candidate_sources
                )
            return [_real_estate_target_edge_rule_from_mapping(item) for item in edge_items]

        target_edge_loader = load_backend_target_edges
    return build_real_estate_reaction_snapshot_refresh_job(
        client=market_client,
        aliases_jsonl=aliases_jsonl,
        alias_loader=alias_loader,
        community_posts_jsonl=None if args.realestate_use_backend_community_posts else args.community_posts_jsonl,
        window_minutes=window_minutes or args.reaction_window_minutes,
        target_edges_jsonl=target_edges_jsonl,
        target_edge_loader=target_edge_loader,
        backend_posts_source=args.realestate_community_posts_source if args.realestate_use_backend_community_posts else None,
        backend_posts_limit=args.realestate_community_posts_limit,
        stale_after_minutes=args.reaction_stale_after_minutes,
        use_current_window=args.realestate_reaction_use_current_window,
        candidate_alias_sources=candidate_sources,
        candidate_edge_sources=candidate_sources,
    )


def _build_real_estate_daily_refresh_job(args, pipeline, market_client) -> RealEstateDailyRefreshJob:
    daily_steps = []
    daily_reaction_window_minutes = args.realestate_daily_reaction_window_minutes
    market_facts_job = _build_real_estate_market_facts_refresh_job_from_args(args, market_client)
    reaction_snapshot_job = _build_real_estate_reaction_snapshot_refresh_job_from_args(
        args,
        market_client,
        window_minutes=daily_reaction_window_minutes,
    )
    if market_facts_job is not None:
        daily_steps.append(("market_facts", market_facts_job))
    if args.enable_realestate_official_stats_refresh:
        daily_steps.append(("official_stats", RealEstateOfficialStatsRefreshJob(client=market_client)))
    if args.enable_realestate_complex_registry_refresh:
        daily_steps.append(
            (
                "complex_registry",
                RealEstateComplexRegistryRefreshJob(
                    client=market_client,
                    market_fact_limit=args.realestate_complex_registry_market_fact_limit,
                ),
            )
        )
    if args.enable_realestate_daily_crawl_refresh:
        daily_steps.append(("community_crawl", RealEstateCommunityCrawlRefreshJob(pipeline=pipeline)))
    if args.enable_realestate_community_complex_seed_refresh:
        daily_steps.append(
            (
                "community_complex_seed",
                RealEstateCommunityComplexSeedRefreshJob(
                    client=market_client,
                    window_minutes=daily_reaction_window_minutes,
                    posts_source=args.realestate_community_posts_source,
                    posts_limit=args.realestate_community_posts_limit,
                ),
            )
        )
    if reaction_snapshot_job is not None:
        daily_steps.append(("reaction_snapshots", reaction_snapshot_job))
    if args.enable_realestate_recent_issues_refresh:
        search_client = _optional_serpapi_recent_issue_client()
        if search_client is None:
            daily_steps.append(
                (
                    "recent_issues",
                    RealEstateConfigMissingRefreshJob(
                        missing=["SERPAPI_API_KEY"],
                        message="SERPAPI_API_KEY is required for recent issue candidate collection.",
                    ),
                )
            )
        else:
            daily_steps.append(
                (
                    "recent_issues",
                    RealEstateRecentIssuesRefreshJob(
                        client=market_client,
                        search_client=search_client,
                        search_targets_jsonl=args.realestate_search_targets_jsonl,
                        issue_keywords=args.realestate_issue_keywords,
                        target_type=args.realestate_recent_issues_target_type,
                        window_minutes=daily_reaction_window_minutes,
                        ranking_limit=args.realestate_recent_issues_ranking_limit,
                        result_limit=args.serpapi_result_limit,
                    ),
                )
            )
    if args.enable_realestate_evidence_logs_refresh:
        daily_steps.append(
            (
                "evidence_logs",
                RealEstateEvidenceLogRefreshJob(
                    client=market_client,
                    target_type=args.realestate_evidence_target_type,
                    window_minutes=daily_reaction_window_minutes,
                    ranking_limit=args.realestate_evidence_ranking_limit,
                    market_fact_limit=args.realestate_evidence_market_fact_limit,
                    timeline_limit=args.realestate_evidence_timeline_limit,
                    content_limit=args.realestate_evidence_content_limit,
                    llm_evaluator=_real_estate_evidence_llm_evaluator_from_args(args),
                    similar_windows_provider=_similar_windows_provider_from_args(args),
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
    if not daily_steps:
        raise SystemExit(
            "real-estate daily refresh requires at least one refresh step "
            "(market facts, official stats, complex registry, community crawl, community complex seed, reaction snapshots, recent issues, evidence logs, or map layers)"
        )
    return RealEstateDailyRefreshJob(daily_steps)


def _build_pipeline_from_args(args) -> CommunityPipeline:
    pipeline = build_pipeline()
    if hasattr(pipeline, "runtime_environment"):
        pipeline.runtime_environment = runtime_environment_from_env(args.crawl_runtime_environment)
    return pipeline


def _real_estate_evidence_llm_evaluator_from_args(args):
    if not args.evidence_use_gms_llm:
        return None
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

    return evidence_llm_evaluator


def _validate_real_estate_serve_refresh_flags(args) -> None:
    if args.enable_realestate_official_stats_refresh and not args.enable_realestate_daily_refresh:
        raise SystemExit("--enable-realestate-official-stats-refresh requires --enable-realestate-daily-refresh")
    if args.enable_realestate_complex_registry_refresh and not args.enable_realestate_daily_refresh:
        raise SystemExit("--enable-realestate-complex-registry-refresh requires --enable-realestate-daily-refresh")
    if args.enable_realestate_community_complex_seed_refresh and not args.enable_realestate_daily_refresh:
        raise SystemExit("--enable-realestate-community-complex-seed-refresh requires --enable-realestate-daily-refresh")
    if args.enable_realestate_recent_issues_refresh and not args.enable_realestate_daily_refresh:
        raise SystemExit("--enable-realestate-recent-issues-refresh requires --enable-realestate-daily-refresh")
    if args.enable_realestate_daily_crawl_refresh and not args.enable_realestate_daily_refresh:
        raise SystemExit("--enable-realestate-daily-crawl-refresh requires --enable-realestate-daily-refresh")
    if args.enable_realestate_evidence_logs_refresh and not args.enable_realestate_daily_refresh:
        raise SystemExit("--enable-realestate-evidence-logs-refresh requires --enable-realestate-daily-refresh")
    if args.enable_realestate_map_layer_refresh and not args.enable_realestate_daily_refresh:
        raise SystemExit("--enable-realestate-map-layer-refresh requires --enable-realestate-daily-refresh")


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


def _similar_windows_provider_from_args(args):
    if not args.evidence_similar_windows_jsonl:
        if args.similar_engine == "qdrant":
            return _qdrant_similar_windows_provider_from_args(args)
        return None
    return _similar_windows_jsonl_provider_from_args(args)


def _similar_windows_jsonl_provider_from_args(args):
    similar_windows = load_real_estate_evidence_similar_windows(args.evidence_similar_windows_jsonl)

    def provider(target_id: str, _ranking_row: dict[str, object], ranking: dict[str, object]) -> list[dict[str, object]]:
        window_start = str(ranking.get("windowStart") or ranking.get("window_start") or "").strip()
        return [
            item
            for item in similar_windows
            if _similar_window_matches_daily_evidence_target(item, target_id=target_id, window_start=window_start)
        ]

    return provider


def _qdrant_similar_windows_provider_from_args(args):
    if not args.embeddings_jsonl:
        raise SystemExit("--embeddings-jsonl is required when daily evidence refresh uses --similar-engine qdrant")
    embedding_items = load_real_estate_embedding_payloads(args.embeddings_jsonl)
    market_facts = (
        load_real_estate_market_fact_payloads(args.similar_market_facts_jsonl)
        if args.similar_market_facts_jsonl
        else None
    )
    vector_client = _qdrant_vector_store_client()
    health = qdrant_collection_health_payload(vector_client)
    if not health.get("ready"):
        logger.warning(
            "real-estate qdrant similar provider skipped; collection=%s status=%s message=%s",
            health.get("collection"),
            health.get("status"),
            health.get("message"),
        )

        def unavailable_provider(
            _target_id: str,
            _ranking_row: dict[str, object],
            _ranking: dict[str, object],
        ) -> list[dict[str, object]]:
            return []

        return unavailable_provider

    def provider(target_id: str, _ranking_row: dict[str, object], ranking: dict[str, object]) -> list[dict[str, object]]:
        input_id = _daily_evidence_embedding_input_id(target_id, ranking)
        if not input_id:
            return []
        try:
            source_input = find_embedding_by_input_id(embedding_items, input_id)
        except ValueError:
            logger.warning("real-estate qdrant similar provider skipped; embedding input not found: %s", input_id)
            return []
        try:
            search_results = vector_client.search(
                vector=source_input["embedding"],
                top_n=_qdrant_similar_fetch_limit(args.similar_top_n),
                exclude_input_id=source_input["inputId"],
            )
        except Exception as exc:
            logger.warning("real-estate qdrant similar provider search failed: %s", exc.__class__.__name__)
            return []
        return qdrant_search_results_to_similar_windows(
            source_input=source_input,
            search_results=search_results,
            market_facts=market_facts,
            horizon_days=args.similar_horizon_days,
        )[: args.similar_top_n]

    return provider


def _daily_evidence_embedding_input_id(target_id: str, ranking: dict[str, object]) -> str | None:
    window_start = str(ranking.get("windowStart") or ranking.get("window_start") or "").strip()
    window_end = str(ranking.get("windowEnd") or ranking.get("window_end") or "").strip()
    if not target_id or not window_start or not window_end:
        return None
    return f"reaction-window:{target_id}:{window_start}:{window_end}"


def _similar_window_matches_daily_evidence_target(
    item: dict[str, object],
    *,
    target_id: str,
    window_start: str,
) -> bool:
    source_target_id = str(item.get("sourceTargetId") or item.get("source_target_id") or "").strip()
    if source_target_id and source_target_id != target_id:
        return False
    source_window_start = str(item.get("sourceWindowStart") or item.get("source_window_start") or "").strip()
    return not source_window_start or not window_start or source_window_start == window_start


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


def _realestate_complex_registry_payload_from_args(args):
    facts = load_real_estate_complex_registry_market_facts(args.realestate_market_facts_jsonl)
    return build_real_estate_complex_registry_from_market_facts(
        facts,
        region_targets_by_lawd_code=_realestate_region_targets_by_lawd_code_from_args(args),
    )


def _realestate_community_complex_seed_registry_from_args(args):
    existing_aliases = _load_real_estate_alias_rules_from_args(args) if args.realestate_use_backend_aliases else []
    if args.realestate_use_backend_community_posts:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=args.realestate_daily_reaction_window_minutes)
        posts = _spring_client().list_community_posts_for_reaction_refresh(
            source=args.realestate_community_posts_source,
            published_from=_iso_z(window_start),
            published_to=_iso_z(now),
            limit=args.realestate_community_posts_limit,
        )
        return build_observed_community_complex_seed_registry(posts, existing_aliases=existing_aliases)
    if not args.community_posts_jsonl:
        raise SystemExit("--community-posts-jsonl is required unless --realestate-use-backend-community-posts is set")
    return build_observed_community_complex_seed_registry(
        load_real_estate_posts_for_matching(args.community_posts_jsonl),
        existing_aliases=existing_aliases,
    )


def _realestate_posts_for_matching_from_args(args):
    if args.realestate_use_backend_community_posts:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=args.realestate_daily_reaction_window_minutes)
        posts = _spring_client().list_community_posts_for_reaction_refresh(
            source=args.realestate_community_posts_source,
            published_from=_iso_z(window_start),
            published_to=_iso_z(now),
            limit=args.realestate_community_posts_limit,
        )
        return real_estate_posts_for_matching_from_records(posts)
    if not args.community_posts_jsonl:
        raise SystemExit("--community-posts-jsonl is required unless --realestate-use-backend-community-posts is set")
    return load_real_estate_posts_for_matching(args.community_posts_jsonl)


def _realestate_region_targets_by_lawd_code_from_args(args) -> dict[str, str]:
    if not args.realestate_use_backend_targets:
        return {}
    client = _spring_client()
    mapping: dict[str, str] = {}
    for item in client.list_real_estate_market_data_targets(enabled=True):
        lawd_code = str(item.get("lawdCode") or item.get("lawd_code") or "").strip()
        target_id = str(item.get("targetId") or item.get("target_id") or "").strip()
        if not lawd_code or not target_id:
            continue
        mapping.setdefault(lawd_code, target_id)
    list_regions = getattr(client, "list_real_estate_regions", None)
    if callable(list_regions):
        for item in list_regions(region_level="eupmyeondong"):
            legal_dong_code = str(item.get("legalDongCode") or item.get("legal_dong_code") or "").strip()
            target_id = str(item.get("targetId") or item.get("target_id") or "").strip()
            if not legal_dong_code or not target_id:
                continue
            mapping.setdefault(legal_dong_code, target_id)
            sigungu_code = legal_dong_code[:5]
            for dong_name in _realestate_region_display_name_candidates(item):
                normalized_dong_name = _realestate_match_key(dong_name)
                if normalized_dong_name:
                    mapping.setdefault(f"{sigungu_code}:{normalized_dong_name}", target_id)
    return mapping


def _realestate_region_display_name_candidates(item: dict) -> list[str]:
    values = [
        item.get("displayName"),
        item.get("display_name"),
        item.get("slug"),
    ]
    candidates: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        candidates.append(text)
        candidates.extend(text.replace("/", " ").replace("-", " ").split()[-1:])
    return candidates


def _realestate_match_key(value: object) -> str:
    if value is None:
        return ""
    return "".join(char for char in str(value) if char.isalnum())


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
    posts = _realestate_posts_for_matching_from_args(args)
    matched_posts = match_real_estate_posts(posts, aliases)
    observations = classify_real_estate_reaction_observations(
        matched_posts,
        classifier=RuleBasedRealEstateReactionClassifier(),
    )
    return _roll_up_real_estate_reaction_observations_from_args(args, observations)


def _real_estate_alias_candidates_from_args(args) -> list:
    aliases = _load_real_estate_alias_rules_from_args(args)
    posts = _realestate_posts_for_matching_from_args(args)
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


def _optional_serpapi_recent_issue_client() -> SerpApiRecentIssueClient | None:
    try:
        return _serpapi_recent_issue_client()
    except SystemExit as exc:
        if str(exc) != "SERPAPI_API_KEY is required":
            raise
        return None


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


def _qdrant_similar_fetch_limit(top_n: int) -> int:
    return max(top_n * 5, top_n + 20)


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
