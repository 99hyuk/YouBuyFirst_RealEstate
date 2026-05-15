create table crawl_targets (
    id bigint not null auto_increment,
    source varchar(40) not null,
    target_id varchar(160) not null,
    target_kind varchar(40) not null,
    status varchar(20) not null,
    market varchar(20),
    symbol varchar(40),
    url varchar(1000),
    label varchar(200),
    priority integer not null,
    crawl_interval_seconds integer not null,
    next_attempt_at datetime(6) not null,
    last_attempt_at datetime(6),
    last_success_at datetime(6),
    last_status varchar(20),
    consecutive_failures integer not null,
    backoff_category varchar(40),
    backoff_until datetime(6),
    backoff_reason varchar(500),
    lease_owner varchar(120),
    leased_until datetime(6),
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_crawl_target_id unique (target_id)
);

create index idx_crawl_targets_due on crawl_targets (status, next_attempt_at, priority);
create index idx_crawl_targets_source_status on crawl_targets (source, status);
create index idx_crawl_targets_backoff_until on crawl_targets (backoff_until);

alter table crawl_runs
    add column target_id varchar(160);

alter table crawl_runs
    add column target_kind varchar(40);

alter table crawl_runs
    add column backoff_category varchar(40);

alter table crawl_runs
    add column backoff_until datetime(6);

alter table crawl_runs
    add column backoff_reason varchar(500);

alter table crawl_runs
    add column skip_reason varchar(500);

create index idx_crawl_runs_target_started_at on crawl_runs (target_id, started_at);

insert into crawl_targets (
    source,
    target_id,
    target_kind,
    status,
    market,
    symbol,
    url,
    label,
    priority,
    crawl_interval_seconds,
    next_attempt_at,
    consecutive_failures,
    created_at,
    updated_at
) values
(
    'NAVER',
    'NAVER:KR:005930',
    'stock-board',
    'ACTIVE',
    'KR',
    '005930',
    null,
    'NAVER KR:005930',
    100,
    1800,
    current_timestamp(6),
    0,
    current_timestamp(6),
    current_timestamp(6)
),
(
    'FMKOREA',
    'FMKOREA:community-board',
    'community-board',
    'ACTIVE',
    null,
    null,
    'https://www.fmkorea.com/stock',
    'FMKOREA stock board',
    200,
    1800,
    current_timestamp(6),
    0,
    current_timestamp(6),
    current_timestamp(6)
);
