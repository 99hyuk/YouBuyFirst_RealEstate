alter table instrument_aliases
    add column normalized_alias varchar(200) not null default '';

alter table instrument_aliases
    add column source varchar(80) not null default 'seed';

alter table instrument_aliases
    add column confidence double not null default 1.0;

alter table instrument_aliases
    add column status varchar(40) not null default 'ACCEPTED';

alter table instrument_aliases
    add column ambiguous boolean not null default false;

alter table instrument_aliases
    add column notes varchar(500);

alter table instrument_aliases
    add column created_at datetime(6) not null default current_timestamp;

alter table instrument_aliases
    add column updated_at datetime(6) not null default current_timestamp;

update instrument_aliases
set normalized_alias = upper(alias)
where normalized_alias = '';

create index idx_instrument_alias_status
    on instrument_aliases (status);

create index idx_instrument_alias_normalized
    on instrument_aliases (normalized_alias);

create table instrument_alias_candidates (
    id bigint not null auto_increment,
    source varchar(40) not null,
    alias varchar(200) not null,
    normalized_alias varchar(200) not null,
    suggested_market varchar(20),
    suggested_symbol varchar(40),
    reason varchar(80) not null,
    context_snippet varchar(500),
    sample_url varchar(1000),
    first_seen_at datetime(6) not null,
    last_seen_at datetime(6) not null,
    occurrence_count integer not null default 1,
    status varchar(40) not null default 'PENDING',
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_alias_candidate_source_alias_symbol unique (source, normalized_alias, suggested_market, suggested_symbol)
);

create index idx_alias_candidate_status_last_seen
    on instrument_alias_candidates (status, last_seen_at);

create index idx_alias_candidate_source_last_seen
    on instrument_alias_candidates (source, last_seen_at);
