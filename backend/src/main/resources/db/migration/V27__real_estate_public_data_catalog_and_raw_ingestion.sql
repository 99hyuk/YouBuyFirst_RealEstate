create table real_estate_public_data_datasets (
    dataset_id varchar(100) not null,
    provider varchar(60) not null,
    provider_name varchar(120) not null,
    owner_org varchar(120) not null,
    display_name varchar(160) not null,
    fact_type varchar(60) not null,
    access_method varchar(40) not null,
    response_format varchar(40) not null,
    source_url varchar(1000) not null,
    endpoint_url varchar(1000),
    target_granularity varchar(60) not null,
    date_granularity varchar(60) not null,
    refresh_interval varchar(60) not null,
    stale_after_hours int not null,
    priority int not null,
    backfill_required boolean not null,
    enabled_for_backfill boolean not null,
    source_row_count bigint,
    notes text,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (dataset_id)
);

create table real_estate_public_data_import_runs (
    id bigint not null auto_increment,
    run_key varchar(180) not null,
    provider_dataset varchar(100) not null,
    run_type varchar(40) not null,
    requested_from date,
    requested_to date,
    request_params_json text not null,
    status varchar(30) not null,
    rows_seen bigint not null default 0,
    rows_landed bigint not null default 0,
    rows_staged bigint not null default 0,
    rows_promoted bigint not null default 0,
    started_at datetime(6) not null,
    finished_at datetime(6),
    error_message text,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint uk_real_estate_public_data_import_runs_run_key unique (run_key),
    constraint fk_real_estate_public_data_import_runs_dataset foreign key (provider_dataset) references real_estate_public_data_datasets (dataset_id)
);

create table real_estate_public_data_raw_items (
    id bigint not null auto_increment,
    import_run_id bigint not null,
    provider_dataset varchar(100) not null,
    provider_object_id varchar(240) not null,
    legal_dong_code varchar(20),
    target_id varchar(120),
    observed_at date,
    as_of date not null,
    source_updated_at datetime(6),
    payload_hash char(64) not null,
    raw_payload_json text not null,
    landing_status varchar(30) not null,
    created_at datetime(6) not null,
    primary key (id),
    constraint fk_real_estate_public_data_raw_items_run foreign key (import_run_id) references real_estate_public_data_import_runs (id),
    constraint fk_real_estate_public_data_raw_items_dataset foreign key (provider_dataset) references real_estate_public_data_datasets (dataset_id),
    constraint uk_real_estate_public_data_raw_items_provider_object unique (provider_dataset, provider_object_id)
);

create table real_estate_market_fact_staging (
    id bigint not null auto_increment,
    raw_item_id bigint not null,
    provider_dataset varchar(100) not null,
    provider_object_id varchar(240) not null,
    target_type varchar(30) not null,
    target_id varchar(120),
    legal_dong_code varchar(20),
    fact_type varchar(60) not null,
    observed_at date,
    as_of date not null,
    value_json text not null,
    validation_status varchar(30) not null,
    validation_message text,
    created_at datetime(6) not null,
    primary key (id),
    constraint fk_real_estate_market_fact_staging_raw_item foreign key (raw_item_id) references real_estate_public_data_raw_items (id),
    constraint fk_real_estate_market_fact_staging_dataset foreign key (provider_dataset) references real_estate_public_data_datasets (dataset_id),
    constraint uk_real_estate_market_fact_staging_raw_item unique (raw_item_id)
);

create index idx_real_estate_public_data_datasets_priority on real_estate_public_data_datasets (priority);
create index idx_real_estate_public_data_datasets_backfill on real_estate_public_data_datasets (enabled_for_backfill, priority);
create index idx_real_estate_public_data_import_runs_dataset_status on real_estate_public_data_import_runs (provider_dataset, status);
create index idx_real_estate_public_data_import_runs_started on real_estate_public_data_import_runs (started_at);
create index idx_real_estate_public_data_raw_items_lawd_as_of on real_estate_public_data_raw_items (legal_dong_code, as_of);
create index idx_real_estate_public_data_raw_items_target on real_estate_public_data_raw_items (target_id, as_of);
create index idx_real_estate_market_fact_staging_status on real_estate_market_fact_staging (validation_status);
create index idx_real_estate_market_fact_staging_lawd_as_of on real_estate_market_fact_staging (legal_dong_code, as_of);

insert into real_estate_public_data_datasets (
    dataset_id, provider, provider_name, owner_org, display_name, fact_type, access_method, response_format,
    source_url, endpoint_url, target_granularity, date_granularity, refresh_interval, stale_after_hours,
    priority, backfill_required, enabled_for_backfill, source_row_count, notes, created_at, updated_at
) values
    (
        'molit_apt_trade', 'molit', '국토교통부', '국토교통부', '아파트 매매 실거래가', 'apt_trade', 'openapi', 'xml',
        'https://www.data.go.kr/data/15126469/openapi.do',
        'https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade',
        'sigungu', 'month', 'daily-check', 72,
        10, true, true, null, 'LAWD_CD and DEAL_YMD based collection. Store observedAt/asOf separately.', '2026-06-12 00:00:00', '2026-06-12 00:00:00'
    ),
    (
        'molit_apt_rent', 'molit', '국토교통부', '국토교통부', '아파트 전월세 실거래가', 'apt_rent', 'openapi', 'xml',
        'https://www.data.go.kr/data/15126474/openapi.do',
        'https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent',
        'sigungu', 'month', 'daily-check', 72,
        20, true, true, null, 'Deposit/monthly-rent facts are normalized into market_facts.', '2026-06-12 00:00:00', '2026-06-12 00:00:00'
    ),
    (
        'molit_official_apartment_price_csv', 'molit', '국토교통부', '국토교통부', '공동주택 호별 공시가격', 'official_apartment_price', 'file', 'csv_zip',
        'https://www.data.go.kr/data/3073746/fileData.do',
        null,
        'complex_unit', 'year', 'annual', 8880,
        30, true, true, 15580435, 'Large CSV; import through raw landing and staging, not spreadsheet tooling.', '2026-06-12 00:00:00', '2026-06-12 00:00:00'
    ),
    (
        'reb_real_estate_statistics', 'reb', '한국부동산원', '한국부동산원', '부동산통계 조회 서비스', 'price_index', 'openapi', 'json_xml',
        'https://www.data.go.kr/data/15134761/openapi.do',
        null,
        'region', 'week_or_month', 'weekly-monthly', 1080,
        40, true, true, null, 'Use for price index, demand/supply mood, transaction statistics, and regional market context.', '2026-06-12 00:00:00', '2026-06-12 00:00:00'
    ),
    (
        'molit_unsold_housing_stat', 'molit_stat', '국토교통 통계누리', '국토교통부', '미분양주택현황보고', 'unsold_housing', 'stat_file_or_api', 'csv_json_xml',
        'https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=32',
        null,
        'region', 'month', 'monthly', 1560,
        50, true, true, null, 'Published around the end of the following month; separate unsold and completed-unsold facts.', '2026-06-12 00:00:00', '2026-06-12 00:00:00'
    ),
    (
        'molit_housing_permit_stat', 'molit_stat', '국토교통 통계누리', '국토교통부', '주택 인허가 실적', 'housing_permit', 'file', 'csv',
        'https://www.data.go.kr/data/15068726/fileData.do',
        null,
        'region', 'month_or_year', 'monthly', 1560,
        60, true, true, null, 'Supply leading indicator; later split permits, starts, completions when provider layouts are confirmed.', '2026-06-12 00:00:00', '2026-06-12 00:00:00'
    ),
    (
        'molit_buildinghub_housing_approval', 'molit_buildinghub', '국토교통부 건축HUB', '국토교통부', '주택건설사업계획승인 정보', 'supply_event', 'openapi', 'json_xml',
        'https://www.data.go.kr/data/15136560/openapi.do',
        null,
        'parcel_or_project', 'event', 'weekly-check', 720,
        70, false, false, null, 'Reference source until project key mapping and complex linkage are verified.', '2026-06-12 00:00:00', '2026-06-12 00:00:00'
    );
