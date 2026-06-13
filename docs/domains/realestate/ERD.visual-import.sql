-- Visual ERD import SQL for ChartDB/DrawSQL/Erd Go. MySQL 기준 DDL이며 enum은 VARCHAR(255)로 단순화했다.
-- SQL dump generated using DBML (dbml.dbdiagram.io)
-- Database: MySQL
-- Generated at: 2026-06-04T06:52:42.597Z

CREATE TABLE `app_users` (
  `id` CHAR(36) PRIMARY KEY,
  `email` VARCHAR(255) UNIQUE,
  `display_name` VARCHAR(255),
  `auth_provider` VARCHAR(255),
  `created_at` DATETIME NOT NULL,
  `last_seen_at` DATETIME
);

CREATE TABLE `real_estate_targets` (
  `id` CHAR(36) PRIMARY KEY,
  `target_type` VARCHAR(255) NOT NULL,
  `display_name` VARCHAR(255) NOT NULL,
  `slug` VARCHAR(255) UNIQUE NOT NULL,
  `normalized_name` VARCHAR(255) NOT NULL,
  `review_state` VARCHAR(255) NOT NULL DEFAULT 'candidate',
  `data_status` VARCHAR(255) NOT NULL DEFAULT 'unknown',
  `created_at` DATETIME NOT NULL,
  `updated_at` DATETIME NOT NULL
);

CREATE TABLE `real_estate_regions` (
  `target_id` CHAR(36) PRIMARY KEY,
  `region_level` VARCHAR(255) NOT NULL,
  `parent_region_id` CHAR(36),
  `legal_dong_code` VARCHAR(255),
  `region_code` VARCHAR(255),
  `geometry_id` VARCHAR(255),
  `source` VARCHAR(255)
);

CREATE TABLE `real_estate_complexes` (
  `target_id` CHAR(36) PRIMARY KEY,
  `region_target_id` CHAR(36) NOT NULL,
  `address` VARCHAR(255),
  `legal_dong_code` VARCHAR(255),
  `built_year` INT,
  `household_count` INT,
  `latitude` DECIMAL(12,4),
  `longitude` DECIMAL(12,4),
  `provider_keys` JSON
);

CREATE TABLE `real_estate_target_edges` (
  `from_target_id` CHAR(36) NOT NULL,
  `to_target_id` CHAR(36) NOT NULL,
  `edge_type` VARCHAR(255) NOT NULL,
  `confidence` DECIMAL(12,4) NOT NULL,
  `source` VARCHAR(255),
  `review_state` VARCHAR(255) NOT NULL DEFAULT 'candidate',
  PRIMARY KEY (`from_target_id`, `to_target_id`, `edge_type`)
);

CREATE TABLE `real_estate_aliases` (
  `id` CHAR(36) PRIMARY KEY,
  `target_id` CHAR(36) NOT NULL,
  `alias` VARCHAR(255) NOT NULL,
  `normalized_alias` VARCHAR(255) NOT NULL,
  `alias_type` VARCHAR(255) NOT NULL,
  `source` VARCHAR(255),
  `evidence_url` VARCHAR(255),
  `confidence` DECIMAL(12,4) NOT NULL,
  `review_state` VARCHAR(255) NOT NULL DEFAULT 'candidate',
  `created_by` VARCHAR(255) NOT NULL
);

CREATE TABLE `map_boundary_assets` (
  `id` CHAR(36) PRIMARY KEY,
  `asset_type` VARCHAR(255) NOT NULL,
  `source_label` VARCHAR(255) NOT NULL,
  `base_year` VARCHAR(255),
  `asset_url` VARCHAR(255) NOT NULL,
  `imported_at` DATETIME NOT NULL
);

CREATE TABLE `map_features` (
  `id` CHAR(36) PRIMARY KEY,
  `boundary_asset_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `geometry_id` VARCHAR(255) NOT NULL,
  `region_code` VARCHAR(255),
  `parent_region_code` VARCHAR(255)
);

CREATE TABLE `map_layer_snapshots` (
  `id` CHAR(36) PRIMARY KEY,
  `target_id` CHAR(36) NOT NULL,
  `layer_type` VARCHAR(255) NOT NULL,
  `period_key` VARCHAR(255) NOT NULL,
  `change_pct` DECIMAL(12,4),
  `sample_count` INT,
  `confidence` DECIMAL(12,4),
  `as_of` DATETIME NOT NULL,
  `data_status` VARCHAR(255) NOT NULL DEFAULT 'unknown'
);

CREATE TABLE `crawl_sources` (
  `id` VARCHAR(255) PRIMARY KEY,
  `display_name` VARCHAR(255) NOT NULL,
  `source_type` VARCHAR(255) NOT NULL,
  `root_url` VARCHAR(255) NOT NULL,
  `access_mode` VARCHAR(255) NOT NULL,
  `status` VARCHAR(255) NOT NULL DEFAULT 'disabled',
  `robots_status` VARCHAR(255) NOT NULL DEFAULT 'unknown',
  `terms_status` VARCHAR(255) NOT NULL DEFAULT 'unknown',
  `target_scope` VARCHAR(255),
  `expected_volume` VARCHAR(255),
  `parser_status` VARCHAR(255) NOT NULL DEFAULT 'none',
  `rate_limit_policy` VARCHAR(255),
  `last_reviewed_at` DATETIME
);

CREATE TABLE `source_boards` (
  `id` CHAR(36) PRIMARY KEY,
  `source_id` VARCHAR(255) NOT NULL,
  `board_key` VARCHAR(255) NOT NULL,
  `board_name` VARCHAR(255),
  `board_url` VARCHAR(255),
  `status` VARCHAR(255) NOT NULL DEFAULT 'disabled',
  `last_crawled_at` DATETIME
);

CREATE TABLE `community_posts` (
  `id` CHAR(36) PRIMARY KEY,
  `source_id` VARCHAR(255) NOT NULL,
  `board_id` CHAR(36),
  `external_id` VARCHAR(255),
  `url` VARCHAR(255) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `content_snippet` TEXT,
  `published_at` DATETIME,
  `time_confidence` VARCHAR(255) NOT NULL DEFAULT 'unknown',
  `author_hash` VARCHAR(255),
  `view_count` INT,
  `recommend_count` INT,
  `comment_count` INT,
  `content_hash` VARCHAR(255) NOT NULL,
  `ingested_at` DATETIME NOT NULL
);

CREATE TABLE `content_items` (
  `id` CHAR(36) PRIMARY KEY,
  `source_id` VARCHAR(255),
  `content_type` VARCHAR(255) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `snippet` TEXT,
  `url` VARCHAR(255) NOT NULL,
  `domain` VARCHAR(255),
  `published_at` DATETIME,
  `metric_label` VARCHAR(255),
  `status_label` VARCHAR(255),
  `ingested_at` DATETIME NOT NULL
);

CREATE TABLE `content_target_links` (
  `content_item_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `link_type` VARCHAR(255) NOT NULL,
  `confidence` DECIMAL(12,4) NOT NULL,
  PRIMARY KEY (`content_item_id`, `target_id`, `link_type`)
);

CREATE TABLE `real_estate_mentions` (
  `id` CHAR(36) PRIMARY KEY,
  `post_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `matched_alias_id` CHAR(36),
  `matched_text` VARCHAR(255) NOT NULL,
  `match_source` VARCHAR(255) NOT NULL,
  `confidence` DECIMAL(12,4) NOT NULL,
  `review_state` VARCHAR(255) NOT NULL DEFAULT 'auto'
);

CREATE TABLE `issue_taxonomy` (
  `id` VARCHAR(255) PRIMARY KEY,
  `label` VARCHAR(255) NOT NULL,
  `group_name` VARCHAR(255),
  `description` TEXT,
  `active` TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE `reaction_analyses` (
  `id` CHAR(36) PRIMARY KEY,
  `mention_id` CHAR(36) NOT NULL,
  `reaction_direction` VARCHAR(255) NOT NULL,
  `issue_id` VARCHAR(255),
  `confidence` DECIMAL(12,4) NOT NULL,
  `evidence_snippet` TEXT,
  `model_version` VARCHAR(255),
  `analyzed_at` DATETIME NOT NULL
);

CREATE TABLE `reaction_snapshots` (
  `id` CHAR(36) PRIMARY KEY,
  `target_id` CHAR(36) NOT NULL,
  `window_start` DATETIME NOT NULL,
  `window_end` DATETIME NOT NULL,
  `mention_count` INT NOT NULL,
  `expectation_score` DECIMAL(12,4) NOT NULL,
  `concern_score` DECIMAL(12,4) NOT NULL,
  `neutral_count` INT NOT NULL,
  `overall_reaction` VARCHAR(255) NOT NULL,
  `source_count` INT NOT NULL,
  `source_skew` DECIMAL(12,4),
  `confidence` DECIMAL(12,4) NOT NULL,
  `coverage_status` VARCHAR(255) NOT NULL,
  `as_of` DATETIME NOT NULL
);

CREATE TABLE `reaction_snapshot_issues` (
  `snapshot_id` CHAR(36) NOT NULL,
  `issue_id` VARCHAR(255) NOT NULL,
  `share_pct` DECIMAL(12,4) NOT NULL,
  `direction` VARCHAR(255) NOT NULL,
  `summary` TEXT,
  `confidence` DECIMAL(12,4) NOT NULL,
  PRIMARY KEY (`snapshot_id`, `issue_id`, `direction`)
);

CREATE TABLE `reaction_ranking_snapshots` (
  `id` CHAR(36) PRIMARY KEY,
  `ranking_type` VARCHAR(255) NOT NULL,
  `window_key` VARCHAR(255) NOT NULL,
  `window_start` DATETIME NOT NULL,
  `window_end` DATETIME NOT NULL,
  `as_of` DATETIME NOT NULL,
  `data_status` VARCHAR(255) NOT NULL
);

CREATE TABLE `reaction_ranking_rows` (
  `id` CHAR(36) PRIMARY KEY,
  `ranking_snapshot_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `rank_no` INT NOT NULL,
  `mention_count` INT NOT NULL,
  `mention_delta_pct` DECIMAL(12,4),
  `heat_score` DECIMAL(12,4),
  `headline_issue` VARCHAR(255),
  `freshness_label` VARCHAR(255)
);

CREATE TABLE `real_estate_market_facts` (
  `id` CHAR(36) PRIMARY KEY,
  `target_id` CHAR(36) NOT NULL,
  `fact_type` VARCHAR(255) NOT NULL,
  `provider` VARCHAR(255) NOT NULL,
  `provider_dataset` VARCHAR(255),
  `provider_object_id` VARCHAR(255),
  `observed_at` DATETIME,
  `as_of` DATETIME NOT NULL,
  `source_updated_at` DATETIME,
  `ingested_at` DATETIME NOT NULL,
  `value_json` JSON NOT NULL,
  `data_status` VARCHAR(255) NOT NULL,
  `stale` TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE `market_indicator_defs` (
  `id` CHAR(36) PRIMARY KEY,
  `category` VARCHAR(255) NOT NULL,
  `indicator_key` VARCHAR(255) UNIQUE NOT NULL,
  `display_name` VARCHAR(255) NOT NULL,
  `unit` VARCHAR(255),
  `provider` VARCHAR(255),
  `provider_dataset` VARCHAR(255),
  `default_period` VARCHAR(255)
);

CREATE TABLE `market_indicator_values` (
  `id` CHAR(36) PRIMARY KEY,
  `indicator_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36),
  `period_start` DATETIME NOT NULL,
  `period_end` DATETIME NOT NULL,
  `value_num` DECIMAL(12,4),
  `value_text` VARCHAR(255),
  `change_pct` DECIMAL(12,4),
  `as_of` DATETIME NOT NULL,
  `data_status` VARCHAR(255) NOT NULL
);

CREATE TABLE `market_data_schedules` (
  `id` CHAR(36) PRIMARY KEY,
  `indicator_id` CHAR(36),
  `schedule_label` VARCHAR(255),
  `title` VARCHAR(255) NOT NULL,
  `expected_at` DATETIME,
  `watch_note` VARCHAR(255),
  `status` VARCHAR(255)
);

CREATE TABLE `policy_events` (
  `id` CHAR(36) PRIMARY KEY,
  `event_type` VARCHAR(255) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `summary` TEXT,
  `source_url` VARCHAR(255),
  `published_at` DATETIME,
  `effective_from` DATETIME,
  `effective_to` DATETIME,
  `target_scope` VARCHAR(255),
  `data_status` VARCHAR(255) NOT NULL
);

CREATE TABLE `policy_event_targets` (
  `policy_event_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `impact_type` VARCHAR(255) NOT NULL,
  `confidence` DECIMAL(12,4) NOT NULL,
  `review_state` VARCHAR(255) NOT NULL DEFAULT 'candidate',
  PRIMARY KEY (`policy_event_id`, `target_id`, `impact_type`)
);

CREATE TABLE `timeline_events` (
  `id` CHAR(36) PRIMARY KEY,
  `target_id` CHAR(36) NOT NULL,
  `event_type` VARCHAR(255) NOT NULL,
  `source_ref_type` VARCHAR(255) NOT NULL,
  `source_ref_id` CHAR(36) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `summary` TEXT,
  `occurred_at` DATETIME,
  `as_of` DATETIME,
  `data_status` VARCHAR(255) NOT NULL
);

CREATE TABLE `similar_window_matches` (
  `source_snapshot_id` CHAR(36) NOT NULL,
  `matched_snapshot_id` CHAR(36) NOT NULL,
  `similarity_score` DECIMAL(12,4) NOT NULL,
  `match_reason` TEXT,
  `after_market_summary` JSON,
  `caveat` TEXT,
  PRIMARY KEY (`source_snapshot_id`, `matched_snapshot_id`)
);

CREATE TABLE `evidence_logs` (
  `id` CHAR(36) PRIMARY KEY,
  `target_id` CHAR(36) NOT NULL,
  `snapshot_id` CHAR(36),
  `evaluation_version` VARCHAR(255) NOT NULL,
  `tone` VARCHAR(255) NOT NULL,
  `summary` TEXT NOT NULL,
  `subtitle` TEXT,
  `caveats_json` JSON,
  `data_quality` VARCHAR(255) NOT NULL,
  `evaluated_at` DATETIME NOT NULL,
  `as_of` DATETIME NOT NULL
);

CREATE TABLE `evidence_log_items` (
  `id` CHAR(36) PRIMARY KEY,
  `evidence_log_id` CHAR(36) NOT NULL,
  `evidence_type` VARCHAR(255) NOT NULL,
  `ref_type` VARCHAR(255) NOT NULL,
  `ref_id` CHAR(36) NOT NULL,
  `label` VARCHAR(255) NOT NULL,
  `value_text` VARCHAR(255),
  `severity` VARCHAR(255)
);

CREATE TABLE `user_watch_targets` (
  `user_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `watch_label` VARCHAR(255),
  `status` VARCHAR(255) NOT NULL DEFAULT 'watching',
  `created_at` DATETIME NOT NULL,
  PRIMARY KEY (`user_id`, `target_id`)
);

CREATE TABLE `alert_rules` (
  `id` CHAR(36) PRIMARY KEY,
  `user_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `rule_type` VARCHAR(255) NOT NULL,
  `threshold_json` JSON NOT NULL,
  `enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL
);

CREATE TABLE `alert_events` (
  `id` CHAR(36) PRIMARY KEY,
  `alert_rule_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `event_title` VARCHAR(255) NOT NULL,
  `event_summary` TEXT,
  `triggered_at` DATETIME NOT NULL,
  `status` VARCHAR(255) NOT NULL
);

CREATE TABLE `observation_logs` (
  `id` CHAR(36) PRIMARY KEY,
  `user_id` CHAR(36) NOT NULL,
  `target_id` CHAR(36) NOT NULL,
  `log_type` VARCHAR(255) NOT NULL,
  `summary` TEXT NOT NULL,
  `source_ref_id` CHAR(36),
  `created_at` DATETIME NOT NULL
);

CREATE INDEX ON `real_estate_targets` (`target_type`, `normalized_name`);

CREATE INDEX ON `real_estate_targets` (`target_type`, `review_state`);

CREATE INDEX ON `real_estate_regions` (`legal_dong_code`);

CREATE INDEX ON `real_estate_regions` (`region_code`);

CREATE INDEX ON `real_estate_regions` (`parent_region_id`);

CREATE INDEX ON `real_estate_complexes` (`region_target_id`);

CREATE INDEX ON `real_estate_complexes` (`legal_dong_code`);

CREATE INDEX ON `real_estate_complexes` (`latitude`, `longitude`);

CREATE INDEX ON `real_estate_target_edges` (`to_target_id`);

CREATE UNIQUE INDEX ON `real_estate_aliases` (`target_id`, `normalized_alias`);

CREATE INDEX ON `real_estate_aliases` (`normalized_alias`);

CREATE INDEX ON `real_estate_aliases` (`review_state`);

CREATE UNIQUE INDEX ON `map_features` (`boundary_asset_id`, `geometry_id`);

CREATE INDEX ON `map_features` (`target_id`);

CREATE INDEX ON `map_features` (`region_code`);

CREATE UNIQUE INDEX ON `map_layer_snapshots` (`target_id`, `layer_type`, `period_key`, `as_of`);

CREATE INDEX ON `map_layer_snapshots` (`layer_type`, `period_key`, `as_of`);

CREATE UNIQUE INDEX ON `source_boards` (`source_id`, `board_key`);

CREATE UNIQUE INDEX ON `community_posts` (`source_id`, `external_id`);

CREATE INDEX ON `community_posts` (`content_hash`);

CREATE INDEX ON `community_posts` (`published_at`);

CREATE UNIQUE INDEX ON `content_items` (`url`);

CREATE INDEX ON `content_items` (`content_type`, `published_at`);

CREATE INDEX ON `content_target_links` (`target_id`);

CREATE INDEX ON `real_estate_mentions` (`post_id`);

CREATE INDEX ON `real_estate_mentions` (`target_id`);

CREATE INDEX ON `real_estate_mentions` (`matched_alias_id`);

CREATE INDEX ON `reaction_analyses` (`mention_id`);

CREATE INDEX ON `reaction_analyses` (`issue_id`);

CREATE INDEX ON `reaction_analyses` (`reaction_direction`);

CREATE UNIQUE INDEX ON `reaction_snapshots` (`target_id`, `window_start`, `window_end`);

CREATE INDEX ON `reaction_snapshots` (`window_end`, `overall_reaction`);

CREATE UNIQUE INDEX ON `reaction_ranking_snapshots` (`ranking_type`, `window_key`, `as_of`);

CREATE UNIQUE INDEX ON `reaction_ranking_rows` (`ranking_snapshot_id`, `rank_no`);

CREATE UNIQUE INDEX ON `reaction_ranking_rows` (`ranking_snapshot_id`, `target_id`);

CREATE INDEX ON `reaction_ranking_rows` (`target_id`);

CREATE INDEX ON `real_estate_market_facts` (`target_id`, `fact_type`, `as_of`);

CREATE INDEX ON `real_estate_market_facts` (`provider`, `provider_dataset`, `provider_object_id`);

CREATE UNIQUE INDEX ON `market_indicator_values` (`indicator_id`, `target_id`, `period_start`, `period_end`);

CREATE INDEX ON `market_indicator_values` (`indicator_id`, `as_of`);

CREATE INDEX ON `policy_event_targets` (`target_id`);

CREATE INDEX ON `timeline_events` (`target_id`, `occurred_at`);

CREATE INDEX ON `timeline_events` (`source_ref_type`, `source_ref_id`);

CREATE INDEX ON `similar_window_matches` (`matched_snapshot_id`);

CREATE INDEX ON `evidence_logs` (`target_id`, `evaluated_at`);

CREATE INDEX ON `evidence_logs` (`snapshot_id`);

CREATE INDEX ON `evidence_log_items` (`evidence_log_id`);

CREATE INDEX ON `evidence_log_items` (`ref_type`, `ref_id`);

CREATE INDEX ON `user_watch_targets` (`target_id`);

CREATE INDEX ON `alert_rules` (`user_id`, `target_id`, `rule_type`);

CREATE INDEX ON `alert_events` (`alert_rule_id`);

CREATE INDEX ON `alert_events` (`target_id`, `triggered_at`);

CREATE INDEX ON `observation_logs` (`user_id`, `created_at`);

CREATE INDEX ON `observation_logs` (`target_id`, `created_at`);

ALTER TABLE `real_estate_regions` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `real_estate_regions` ADD FOREIGN KEY (`parent_region_id`) REFERENCES `real_estate_regions` (`target_id`);

ALTER TABLE `real_estate_complexes` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `real_estate_complexes` ADD FOREIGN KEY (`region_target_id`) REFERENCES `real_estate_regions` (`target_id`);

ALTER TABLE `real_estate_target_edges` ADD FOREIGN KEY (`from_target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `real_estate_target_edges` ADD FOREIGN KEY (`to_target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `real_estate_aliases` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `map_features` ADD FOREIGN KEY (`boundary_asset_id`) REFERENCES `map_boundary_assets` (`id`);

ALTER TABLE `map_features` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `map_layer_snapshots` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `source_boards` ADD FOREIGN KEY (`source_id`) REFERENCES `crawl_sources` (`id`);

ALTER TABLE `community_posts` ADD FOREIGN KEY (`source_id`) REFERENCES `crawl_sources` (`id`);

ALTER TABLE `community_posts` ADD FOREIGN KEY (`board_id`) REFERENCES `source_boards` (`id`);

ALTER TABLE `content_items` ADD FOREIGN KEY (`source_id`) REFERENCES `crawl_sources` (`id`);

ALTER TABLE `content_target_links` ADD FOREIGN KEY (`content_item_id`) REFERENCES `content_items` (`id`);

ALTER TABLE `content_target_links` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `real_estate_mentions` ADD FOREIGN KEY (`post_id`) REFERENCES `community_posts` (`id`);

ALTER TABLE `real_estate_mentions` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `real_estate_mentions` ADD FOREIGN KEY (`matched_alias_id`) REFERENCES `real_estate_aliases` (`id`);

ALTER TABLE `reaction_analyses` ADD FOREIGN KEY (`mention_id`) REFERENCES `real_estate_mentions` (`id`);

ALTER TABLE `reaction_analyses` ADD FOREIGN KEY (`issue_id`) REFERENCES `issue_taxonomy` (`id`);

ALTER TABLE `reaction_snapshots` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `reaction_snapshot_issues` ADD FOREIGN KEY (`snapshot_id`) REFERENCES `reaction_snapshots` (`id`);

ALTER TABLE `reaction_snapshot_issues` ADD FOREIGN KEY (`issue_id`) REFERENCES `issue_taxonomy` (`id`);

ALTER TABLE `reaction_ranking_rows` ADD FOREIGN KEY (`ranking_snapshot_id`) REFERENCES `reaction_ranking_snapshots` (`id`);

ALTER TABLE `reaction_ranking_rows` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `real_estate_market_facts` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `market_indicator_values` ADD FOREIGN KEY (`indicator_id`) REFERENCES `market_indicator_defs` (`id`);

ALTER TABLE `market_indicator_values` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `market_data_schedules` ADD FOREIGN KEY (`indicator_id`) REFERENCES `market_indicator_defs` (`id`);

ALTER TABLE `policy_event_targets` ADD FOREIGN KEY (`policy_event_id`) REFERENCES `policy_events` (`id`);

ALTER TABLE `policy_event_targets` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `timeline_events` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `similar_window_matches` ADD FOREIGN KEY (`source_snapshot_id`) REFERENCES `reaction_snapshots` (`id`);

ALTER TABLE `similar_window_matches` ADD FOREIGN KEY (`matched_snapshot_id`) REFERENCES `reaction_snapshots` (`id`);

ALTER TABLE `evidence_logs` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `evidence_logs` ADD FOREIGN KEY (`snapshot_id`) REFERENCES `reaction_snapshots` (`id`);

ALTER TABLE `evidence_log_items` ADD FOREIGN KEY (`evidence_log_id`) REFERENCES `evidence_logs` (`id`);

ALTER TABLE `user_watch_targets` ADD FOREIGN KEY (`user_id`) REFERENCES `app_users` (`id`);

ALTER TABLE `user_watch_targets` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `alert_rules` ADD FOREIGN KEY (`user_id`) REFERENCES `app_users` (`id`);

ALTER TABLE `alert_rules` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `alert_events` ADD FOREIGN KEY (`alert_rule_id`) REFERENCES `alert_rules` (`id`);

ALTER TABLE `alert_events` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);

ALTER TABLE `observation_logs` ADD FOREIGN KEY (`user_id`) REFERENCES `app_users` (`id`);

ALTER TABLE `observation_logs` ADD FOREIGN KEY (`target_id`) REFERENCES `real_estate_targets` (`id`);
