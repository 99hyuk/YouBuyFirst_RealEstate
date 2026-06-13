create table real_estate_target_edges (
    id bigint not null auto_increment,
    from_target_id varchar(120) not null,
    from_target_type varchar(30) not null,
    to_target_id varchar(120) not null,
    to_target_type varchar(30) not null,
    edge_type varchar(40) not null,
    confidence double not null,
    source varchar(120) not null,
    review_state varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_real_estate_target_edges_from foreign key (from_target_id) references real_estate_targets (id),
    constraint fk_real_estate_target_edges_to foreign key (to_target_id) references real_estate_targets (id),
    constraint uk_real_estate_target_edges unique (from_target_id, to_target_id, edge_type)
);

create index idx_real_estate_target_edges_from
    on real_estate_target_edges (from_target_id, review_state, edge_type);

create index idx_real_estate_target_edges_to
    on real_estate_target_edges (to_target_id, review_state, edge_type);

create index idx_real_estate_target_edges_export
    on real_estate_target_edges (review_state, edge_type, from_target_type, to_target_type);
