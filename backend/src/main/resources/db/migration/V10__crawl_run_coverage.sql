alter table crawl_runs
    add column pages_fetched integer;

alter table crawl_runs
    add column rows_seen integer;

alter table crawl_runs
    add column ignored_pinned_count integer;

alter table crawl_runs
    add column duplicate_stop boolean;

alter table crawl_runs
    add column cutoff_stop boolean;

alter table crawl_runs
    add column oldest_seen_at datetime(6);

alter table crawl_runs
    add column newest_seen_at datetime(6);

alter table crawl_runs
    add column last_cursor varchar(120);

alter table crawl_runs
    add column coverage_status varchar(40);
