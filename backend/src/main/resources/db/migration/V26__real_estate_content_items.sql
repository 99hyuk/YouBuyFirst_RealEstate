create table content_items (
    id varchar(120) not null,
    source_id varchar(120),
    content_type varchar(40) not null,
    title varchar(200) not null,
    snippet text,
    url varchar(1000) not null,
    domain varchar(160),
    published_at datetime(6),
    metric_label varchar(120),
    status_label varchar(120),
    ingested_at datetime(6) not null,
    data_status varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_content_items_url unique (url)
);

create table content_target_links (
    content_item_id varchar(120) not null,
    target_id varchar(120) not null,
    link_type varchar(40) not null,
    confidence double not null,
    review_state varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (content_item_id, target_id, link_type),
    constraint fk_content_target_links_content foreign key (content_item_id) references content_items (id),
    constraint fk_content_target_links_target foreign key (target_id) references real_estate_targets (id)
);

create index idx_content_items_type_published on content_items (content_type, published_at);
create index idx_content_target_links_target on content_target_links (target_id);
