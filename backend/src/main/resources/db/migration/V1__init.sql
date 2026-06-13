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
