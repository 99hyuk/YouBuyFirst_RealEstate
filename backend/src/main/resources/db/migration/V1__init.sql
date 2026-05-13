create table instruments (
    id bigint not null auto_increment,
    market varchar(20) not null,
    symbol varchar(40) not null,
    name_ko varchar(200) not null,
    name_en varchar(200),
    type varchar(40) not null,
    primary key (id),
    constraint uk_instrument_market_symbol unique (market, symbol)
);

create table instrument_aliases (
    id bigint not null auto_increment,
    instrument_id bigint not null,
    alias varchar(200) not null,
    primary key (id),
    constraint uk_instrument_alias unique (instrument_id, alias),
    constraint fk_alias_instrument foreign key (instrument_id) references instruments (id)
);

create table community_posts (
    id bigint not null auto_increment,
    source varchar(40) not null,
    external_id varchar(200) not null,
    url varchar(1000) not null,
    title varchar(500) not null,
    content_snippet varchar(1000),
    author_hash varchar(64) not null,
    published_at datetime(6) not null,
    content_hash varchar(64) not null,
    crawled_at datetime(6) not null,
    primary key (id),
    constraint uk_post_source_external unique (source, external_id)
);

create index idx_posts_published_at on community_posts (published_at);
create index idx_posts_source_published_at on community_posts (source, published_at);

create table post_mentions (
    id bigint not null auto_increment,
    post_id bigint not null,
    instrument_id bigint not null,
    matched_text varchar(200) not null,
    primary key (id),
    constraint fk_mention_post foreign key (post_id) references community_posts (id) on delete cascade,
    constraint fk_mention_instrument foreign key (instrument_id) references instruments (id)
);

create table sentiment_analyses (
    id bigint not null auto_increment,
    post_id bigint not null,
    instrument_id bigint not null,
    sentiment varchar(20) not null,
    confidence double not null,
    rationale varchar(500),
    model varchar(100),
    analyzed_at datetime(6) not null,
    primary key (id),
    constraint fk_sentiment_post foreign key (post_id) references community_posts (id) on delete cascade,
    constraint fk_sentiment_instrument foreign key (instrument_id) references instruments (id)
);

create index idx_sentiment_instrument on sentiment_analyses (instrument_id);

create table crawl_runs (
    id bigint not null auto_increment,
    source varchar(40) not null,
    external_run_id varchar(120) not null,
    started_at datetime(6) not null,
    finished_at datetime(6),
    status varchar(20) not null,
    posts_seen integer not null,
    posts_accepted integer not null,
    error_message varchar(1000),
    primary key (id)
);

create index idx_crawl_runs_started_at on crawl_runs (started_at);

create table metric_snapshots (
    id bigint not null auto_increment,
    instrument_id bigint not null,
    window_start datetime(6) not null,
    window_end datetime(6) not null,
    mention_count integer not null,
    bullish_count integer not null,
    bearish_count integer not null,
    neutral_count integer not null,
    net_sentiment double not null,
    momentum_percent double,
    primary key (id),
    constraint uk_metric_instrument_window unique (instrument_id, window_start),
    constraint fk_metric_instrument foreign key (instrument_id) references instruments (id)
);

create index idx_metrics_window_start on metric_snapshots (window_start);
