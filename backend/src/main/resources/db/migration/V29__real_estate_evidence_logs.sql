create table evidence_logs (
    id varchar(120) not null,
    target_id varchar(120) not null,
    snapshot_id bigint,
    evaluation_version varchar(80) not null,
    prompt_version varchar(80),
    model_name varchar(80),
    tone varchar(40) not null,
    summary text not null,
    subtitle text,
    caveats_json text not null,
    data_quality varchar(30) not null,
    confidence double,
    skip_reason varchar(500),
    evaluated_at datetime(6) not null,
    as_of datetime(6) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_evidence_logs_target foreign key (target_id) references real_estate_targets (id),
    constraint fk_evidence_logs_snapshot foreign key (snapshot_id) references real_estate_reaction_snapshots (id)
);

create table evidence_log_items (
    id varchar(120) not null,
    evidence_log_id varchar(120) not null,
    evidence_type varchar(40) not null,
    ref_type varchar(60) not null,
    ref_id varchar(120) not null,
    label varchar(160) not null,
    value_text varchar(500),
    severity varchar(40),
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_evidence_log_items_log foreign key (evidence_log_id) references evidence_logs (id)
);

create index idx_evidence_logs_target_evaluated on evidence_logs (target_id, evaluated_at);
create index idx_evidence_logs_snapshot on evidence_logs (snapshot_id);
create index idx_evidence_log_items_log on evidence_log_items (evidence_log_id);
create index idx_evidence_log_items_ref on evidence_log_items (ref_type, ref_id);
