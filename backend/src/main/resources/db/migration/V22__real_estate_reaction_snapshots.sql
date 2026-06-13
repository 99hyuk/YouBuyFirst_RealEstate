create table real_estate_reaction_snapshots (
    id bigint not null auto_increment,
    target_type varchar(30) not null,
    target_id varchar(120) not null,
    window_start datetime(6) not null,
    window_end datetime(6) not null,
    as_of datetime(6) not null,
    mention_count int not null,
    previous_mention_count int not null,
    expectation_score double not null,
    concern_score double not null,
    neutral_score double not null,
    heat_score int not null,
    confidence double not null,
    source_count int not null,
    source_skew double not null,
    coverage_status varchar(30) not null,
    stale boolean not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_real_estate_reaction_snapshots_target_window unique (target_id, window_start, window_end),
    constraint fk_real_estate_reaction_snapshots_target foreign key (target_id) references real_estate_targets (id)
);

create table real_estate_reaction_snapshot_issues (
    id bigint not null auto_increment,
    snapshot_id bigint not null,
    issue_key varchar(80) not null,
    label varchar(80) not null,
    share double not null,
    direction varchar(30) not null,
    summary varchar(500),
    confidence double not null,
    primary key (id),
    constraint uk_real_estate_reaction_snapshot_issues_key unique (snapshot_id, issue_key),
    constraint fk_real_estate_reaction_snapshot_issues_snapshot foreign key (snapshot_id) references real_estate_reaction_snapshots (id)
);

create index idx_real_estate_reaction_snapshots_target_type on real_estate_reaction_snapshots (target_type);
create index idx_real_estate_reaction_snapshots_window on real_estate_reaction_snapshots (window_start, window_end);
create index idx_real_estate_reaction_snapshots_rank on real_estate_reaction_snapshots (mention_count, heat_score);
