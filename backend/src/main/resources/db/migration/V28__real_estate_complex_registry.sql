create table real_estate_complexes (
    target_id varchar(120) not null,
    region_target_id varchar(120),
    legal_dong_code varchar(20),
    road_address varchar(300),
    jibun_address varchar(300),
    normalized_address varchar(300),
    built_year int,
    household_count int,
    source varchar(120) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (target_id),
    constraint fk_real_estate_complexes_target foreign key (target_id) references real_estate_targets (id),
    constraint fk_real_estate_complexes_region foreign key (region_target_id) references real_estate_targets (id)
);

create table real_estate_complex_provider_keys (
    id bigint not null auto_increment,
    complex_target_id varchar(120) not null,
    provider varchar(60) not null,
    provider_dataset varchar(100) not null,
    provider_object_id varchar(240) not null,
    legal_dong_code varchar(20),
    key_json text not null,
    confidence double not null,
    review_state varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_real_estate_complex_provider_keys_complex foreign key (complex_target_id) references real_estate_complexes (target_id),
    constraint uk_real_estate_complex_provider_keys_object unique (provider, provider_dataset, provider_object_id)
);

create index idx_real_estate_complexes_region on real_estate_complexes (region_target_id);
create index idx_real_estate_complexes_lawd on real_estate_complexes (legal_dong_code);
create index idx_real_estate_complexes_address on real_estate_complexes (normalized_address);
create index idx_real_estate_complex_provider_keys_complex on real_estate_complex_provider_keys (complex_target_id);
create index idx_real_estate_complex_provider_keys_lawd on real_estate_complex_provider_keys (legal_dong_code);
