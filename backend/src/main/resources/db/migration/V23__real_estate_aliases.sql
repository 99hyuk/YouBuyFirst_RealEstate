create table real_estate_aliases (
    id bigint not null auto_increment,
    target_id varchar(120) not null,
    target_type varchar(30) not null,
    alias varchar(200) not null,
    normalized_alias varchar(200) not null,
    alias_type varchar(40) not null,
    source varchar(120) not null,
    evidence_url varchar(1000),
    confidence double not null,
    review_state varchar(30) not null,
    ambiguous boolean not null default false,
    created_by varchar(80) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_real_estate_aliases_target foreign key (target_id) references real_estate_targets (id),
    constraint uk_real_estate_alias_target_normalized unique (target_id, normalized_alias)
);

create index idx_real_estate_aliases_matcher
    on real_estate_aliases (review_state, ambiguous, target_type, normalized_alias);

create index idx_real_estate_aliases_target
    on real_estate_aliases (target_id, review_state, ambiguous);
