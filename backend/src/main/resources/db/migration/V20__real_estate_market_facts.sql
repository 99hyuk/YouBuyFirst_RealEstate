create table real_estate_market_facts (
    id bigint not null auto_increment,
    target_type varchar(30) not null,
    target_id varchar(120),
    fact_type varchar(40) not null,
    provider varchar(60) not null,
    provider_dataset varchar(80) not null,
    provider_object_id varchar(180) not null,
    legal_dong_code varchar(20) not null,
    observed_at date not null,
    as_of date not null,
    ingested_at datetime(6) not null,
    source_updated_at datetime(6),
    value_json text not null,
    data_status varchar(30) not null,
    stale boolean not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_real_estate_market_facts_provider_object unique (provider, provider_dataset, provider_object_id)
);

create index idx_real_estate_market_facts_legal_dong on real_estate_market_facts (legal_dong_code);
create index idx_real_estate_market_facts_fact_type on real_estate_market_facts (fact_type);
create index idx_real_estate_market_facts_as_of on real_estate_market_facts (as_of);
create index idx_real_estate_market_facts_observed_at on real_estate_market_facts (observed_at);
