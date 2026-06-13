create table policy_events (
    id varchar(120) not null,
    event_type varchar(40) not null,
    title varchar(200) not null,
    summary text,
    source_url varchar(1000),
    published_at datetime(6),
    effective_from datetime(6),
    effective_to datetime(6),
    target_scope varchar(40) not null,
    data_status varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id)
);

create table policy_event_targets (
    policy_event_id varchar(120) not null,
    target_id varchar(120) not null,
    impact_type varchar(40) not null,
    confidence double not null,
    review_state varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (policy_event_id, target_id, impact_type),
    constraint fk_policy_event_targets_event foreign key (policy_event_id) references policy_events (id),
    constraint fk_policy_event_targets_target foreign key (target_id) references real_estate_targets (id)
);

create table timeline_events (
    id varchar(360) not null,
    target_id varchar(120) not null,
    event_type varchar(40) not null,
    source_ref_type varchar(40) not null,
    source_ref_id varchar(120) not null,
    title varchar(200) not null,
    summary text,
    occurred_at datetime(6),
    as_of datetime(6),
    data_status varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_timeline_events_target foreign key (target_id) references real_estate_targets (id)
);

create index idx_policy_event_targets_target on policy_event_targets (target_id);
create index idx_timeline_events_target_occurred on timeline_events (target_id, occurred_at);
create index idx_timeline_events_source_ref on timeline_events (source_ref_type, source_ref_id);
