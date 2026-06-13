create table real_estate_targets (
    id varchar(120) not null,
    target_type varchar(30) not null,
    display_name varchar(120) not null,
    slug varchar(160) not null,
    normalized_name varchar(160) not null,
    review_state varchar(30) not null,
    data_status varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_real_estate_targets_slug unique (slug)
);

create table real_estate_regions (
    target_id varchar(120) not null,
    region_level varchar(30) not null,
    parent_region_id varchar(120),
    legal_dong_code varchar(20),
    region_code varchar(30),
    source varchar(120) not null,
    primary key (target_id),
    constraint fk_real_estate_regions_target foreign key (target_id) references real_estate_targets (id),
    constraint fk_real_estate_regions_parent foreign key (parent_region_id) references real_estate_regions (target_id)
);

create table real_estate_market_data_targets (
    id bigint not null auto_increment,
    target_id varchar(120) not null,
    provider varchar(60) not null,
    provider_dataset varchar(80) not null,
    lawd_code varchar(20) not null,
    enabled boolean not null,
    refresh_interval_hours int not null,
    stale_after_hours int not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_real_estate_market_data_targets_target foreign key (target_id) references real_estate_targets (id),
    constraint uk_real_estate_market_data_targets_dataset unique (target_id, provider, provider_dataset, lawd_code)
);

alter table real_estate_market_facts
    add constraint fk_real_estate_market_facts_target foreign key (target_id) references real_estate_targets (id);

create index idx_real_estate_targets_display_name on real_estate_targets (display_name);
create index idx_real_estate_targets_normalized_name on real_estate_targets (normalized_name);
create index idx_real_estate_regions_legal_dong_code on real_estate_regions (legal_dong_code);
create index idx_real_estate_regions_parent on real_estate_regions (parent_region_id);
create index idx_real_estate_market_data_targets_enabled on real_estate_market_data_targets (enabled);

insert into real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
) values
    ('region-seoul', 'region', '서울특별시', 'seoul', '서울특별시', 'approved', 'ok', '2026-06-11 00:00:00', '2026-06-11 00:00:00'),
    ('region-seoul-jongno', 'region', '서울 종로구', 'seoul-jongno', '서울종로구', 'approved', 'ok', '2026-06-11 00:00:00', '2026-06-11 00:00:00');

insert into real_estate_regions (
    target_id, region_level, parent_region_id, legal_dong_code, region_code, source
) values
    ('region-seoul', 'sido', null, '11000', '11', 'seed:molit-legal-dong-code'),
    ('region-seoul-jongno', 'sigungu', 'region-seoul', '11110', '11110', 'seed:molit-legal-dong-code');

insert into real_estate_market_data_targets (
    target_id, provider, provider_dataset, lawd_code, enabled, refresh_interval_hours, stale_after_hours, created_at, updated_at
) values
    ('region-seoul-jongno', 'molit', 'molit_apt_trade', '11110', true, 24, 72, '2026-06-11 00:00:00', '2026-06-11 00:00:00'),
    ('region-seoul-jongno', 'molit', 'molit_apt_rent', '11110', true, 24, 72, '2026-06-11 00:00:00', '2026-06-11 00:00:00');
