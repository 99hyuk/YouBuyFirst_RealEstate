create table map_boundary_assets (
    id varchar(120) not null,
    asset_type varchar(60) not null,
    source_label varchar(160) not null,
    base_year varchar(20),
    asset_url varchar(500),
    imported_at datetime(6) not null,
    primary key (id)
);

create table map_features (
    id varchar(160) not null,
    boundary_asset_id varchar(120) not null,
    target_id varchar(120) not null,
    layer_type varchar(30) not null,
    geometry_id varchar(120) not null,
    region_code varchar(30) not null,
    parent_region_code varchar(30),
    primary key (id),
    constraint fk_map_features_asset foreign key (boundary_asset_id) references map_boundary_assets (id),
    constraint fk_map_features_target foreign key (target_id) references real_estate_targets (id),
    constraint uk_map_features_asset_geometry unique (boundary_asset_id, geometry_id)
);

create table map_layer_snapshots (
    id varchar(180) not null,
    target_id varchar(120) not null,
    layer_type varchar(30) not null,
    period_key varchar(30) not null,
    change_pct decimal(12,4) not null,
    sample_count int not null,
    confidence decimal(12,4) not null,
    as_of datetime(6) not null,
    provider varchar(60) not null,
    source_label varchar(160) not null,
    data_status varchar(30) not null,
    stale boolean not null,
    created_at datetime(6) not null,
    primary key (id),
    constraint fk_map_layer_snapshots_target foreign key (target_id) references real_estate_targets (id),
    constraint uk_map_layer_snapshots_target_period unique (target_id, layer_type, period_key, as_of)
);

create index idx_map_features_layer_parent on map_features (layer_type, parent_region_code);
create index idx_map_features_region_code on map_features (region_code);
create index idx_map_layer_snapshots_layer_period on map_layer_snapshots (layer_type, period_key, as_of);

insert into real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
) values
    ('region-incheon', 'region', '인천광역시', 'incheon', '인천광역시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-gyeonggi', 'region', '경기도', 'gyeonggi', '경기도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-gangwon', 'region', '강원특별자치도', 'gangwon', '강원특별자치도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-chungnam', 'region', '충청남도', 'chungnam', '충청남도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-sejong', 'region', '세종특별자치시', 'sejong', '세종특별자치시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-daejeon', 'region', '대전광역시', 'daejeon', '대전광역시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-chungbuk', 'region', '충청북도', 'chungbuk', '충청북도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-gyeongbuk', 'region', '경상북도', 'gyeongbuk', '경상북도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-daegu', 'region', '대구광역시', 'daegu', '대구광역시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-jeonbuk', 'region', '전북특별자치도', 'jeonbuk', '전북특별자치도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-gwangju', 'region', '광주광역시', 'gwangju', '광주광역시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-jeonnam', 'region', '전라남도', 'jeonnam', '전라남도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-gyeongnam', 'region', '경상남도', 'gyeongnam', '경상남도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-ulsan', 'region', '울산광역시', 'ulsan', '울산광역시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-busan', 'region', '부산광역시', 'busan', '부산광역시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-jeju', 'region', '제주특별자치도', 'jeju', '제주특별자치도', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00');

insert into real_estate_regions (
    target_id, region_level, parent_region_id, legal_dong_code, region_code, source
) values
    ('region-incheon', 'sido', null, null, '23', 'seed:kostat-2018-map'),
    ('region-gyeonggi', 'sido', null, null, '31', 'seed:kostat-2018-map'),
    ('region-gangwon', 'sido', null, null, '32', 'seed:kostat-2018-map'),
    ('region-chungnam', 'sido', null, null, '34', 'seed:kostat-2018-map'),
    ('region-sejong', 'sido', null, null, '29', 'seed:kostat-2018-map'),
    ('region-daejeon', 'sido', null, null, '25', 'seed:kostat-2018-map'),
    ('region-chungbuk', 'sido', null, null, '33', 'seed:kostat-2018-map'),
    ('region-gyeongbuk', 'sido', null, null, '37', 'seed:kostat-2018-map'),
    ('region-daegu', 'sido', null, null, '22', 'seed:kostat-2018-map'),
    ('region-jeonbuk', 'sido', null, null, '35', 'seed:kostat-2018-map'),
    ('region-gwangju', 'sido', null, null, '24', 'seed:kostat-2018-map'),
    ('region-jeonnam', 'sido', null, null, '36', 'seed:kostat-2018-map'),
    ('region-gyeongnam', 'sido', null, null, '38', 'seed:kostat-2018-map'),
    ('region-ulsan', 'sido', null, null, '26', 'seed:kostat-2018-map'),
    ('region-busan', 'sido', null, null, '21', 'seed:kostat-2018-map'),
    ('region-jeju', 'sido', null, null, '39', 'seed:kostat-2018-map');

insert into map_boundary_assets (
    id, asset_type, source_label, base_year, asset_url, imported_at
) values
    ('map-sido-kostat-2018', 'sido_topology', 'southkorea/southkorea-maps KOSTAT 2018 시도 TopoJSON', '2018', 'front/src/fixtures/skorea-provinces-2018-topo-simple.json', '2026-06-13 00:00:00'),
    ('map-sigungu-kostat-2018', 'sigungu_topology', 'southkorea/southkorea-maps KOSTAT 2018 시군구 TopoJSON', '2018', 'front/src/fixtures/skorea-municipalities-2018-topo-simple.json', '2026-06-13 00:00:00');

insert into map_features (
    id, boundary_asset_id, target_id, layer_type, geometry_id, region_code, parent_region_code
) values
    ('map-feature-sido-11', 'map-sido-kostat-2018', 'region-seoul', 'sido', 'sido-11', '11', null),
    ('map-feature-sido-23', 'map-sido-kostat-2018', 'region-incheon', 'sido', 'sido-23', '23', null),
    ('map-feature-sido-31', 'map-sido-kostat-2018', 'region-gyeonggi', 'sido', 'sido-31', '31', null),
    ('map-feature-sido-32', 'map-sido-kostat-2018', 'region-gangwon', 'sido', 'sido-32', '32', null),
    ('map-feature-sido-34', 'map-sido-kostat-2018', 'region-chungnam', 'sido', 'sido-34', '34', null),
    ('map-feature-sido-29', 'map-sido-kostat-2018', 'region-sejong', 'sido', 'sido-29', '29', null),
    ('map-feature-sido-25', 'map-sido-kostat-2018', 'region-daejeon', 'sido', 'sido-25', '25', null),
    ('map-feature-sido-33', 'map-sido-kostat-2018', 'region-chungbuk', 'sido', 'sido-33', '33', null),
    ('map-feature-sido-37', 'map-sido-kostat-2018', 'region-gyeongbuk', 'sido', 'sido-37', '37', null),
    ('map-feature-sido-22', 'map-sido-kostat-2018', 'region-daegu', 'sido', 'sido-22', '22', null),
    ('map-feature-sido-35', 'map-sido-kostat-2018', 'region-jeonbuk', 'sido', 'sido-35', '35', null),
    ('map-feature-sido-24', 'map-sido-kostat-2018', 'region-gwangju', 'sido', 'sido-24', '24', null),
    ('map-feature-sido-36', 'map-sido-kostat-2018', 'region-jeonnam', 'sido', 'sido-36', '36', null),
    ('map-feature-sido-38', 'map-sido-kostat-2018', 'region-gyeongnam', 'sido', 'sido-38', '38', null),
    ('map-feature-sido-26', 'map-sido-kostat-2018', 'region-ulsan', 'sido', 'sido-26', '26', null),
    ('map-feature-sido-21', 'map-sido-kostat-2018', 'region-busan', 'sido', 'sido-21', '21', null),
    ('map-feature-sido-39', 'map-sido-kostat-2018', 'region-jeju', 'sido', 'sido-39', '39', null),
    ('map-feature-sigungu-11010', 'map-sigungu-kostat-2018', 'region-seoul-jongno', 'sigungu', 'sigungu-11010', '11010', '11'),
    ('map-feature-sigungu-11140', 'map-sigungu-kostat-2018', 'region-seoul-mapo', 'sigungu', 'sigungu-11140', '11140', '11');

insert into map_layer_snapshots (
    id, target_id, layer_type, period_key, change_pct, sample_count, confidence, as_of, provider, source_label, data_status, stale, created_at
) values
    ('map-sido-region-seoul-week-20260601', 'region-seoul', 'sido', 'week', 0.1800, 218, 0.8200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-seoul-month-20260601', 'region-seoul', 'sido', 'month', 0.6200, 218, 0.8200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-seoul-halfYear-20260601', 'region-seoul', 'sido', 'halfYear', 1.8000, 218, 0.8200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-incheon-week-20260601', 'region-incheon', 'sido', 'week', -0.0400, 96, 0.6400, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-incheon-month-20260601', 'region-incheon', 'sido', 'month', -0.1800, 96, 0.6400, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-incheon-halfYear-20260601', 'region-incheon', 'sido', 'halfYear', 0.4200, 96, 0.6400, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeonggi-week-20260601', 'region-gyeonggi', 'sido', 'week', 0.1100, 304, 0.7900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeonggi-month-20260601', 'region-gyeonggi', 'sido', 'month', 0.4400, 304, 0.7900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeonggi-halfYear-20260601', 'region-gyeonggi', 'sido', 'halfYear', 1.3200, 304, 0.7900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gangwon-week-20260601', 'region-gangwon', 'sido', 'week', 0.0200, 41, 0.4600, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gangwon-month-20260601', 'region-gangwon', 'sido', 'month', 0.0900, 41, 0.4600, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gangwon-halfYear-20260601', 'region-gangwon', 'sido', 'halfYear', 0.3600, 41, 0.4600, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-chungnam-week-20260601', 'region-chungnam', 'sido', 'week', -0.0700, 73, 0.5800, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-chungnam-month-20260601', 'region-chungnam', 'sido', 'month', -0.2600, 73, 0.5800, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-chungnam-halfYear-20260601', 'region-chungnam', 'sido', 'halfYear', 0.0800, 73, 0.5800, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-sejong-week-20260601', 'region-sejong', 'sido', 'week', 0.0500, 52, 0.5500, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-sejong-month-20260601', 'region-sejong', 'sido', 'month', 0.2200, 52, 0.5500, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-sejong-halfYear-20260601', 'region-sejong', 'sido', 'halfYear', 0.6400, 52, 0.5500, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-daejeon-week-20260601', 'region-daejeon', 'sido', 'week', 0.0300, 68, 0.6000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-daejeon-month-20260601', 'region-daejeon', 'sido', 'month', 0.1600, 68, 0.6000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-daejeon-halfYear-20260601', 'region-daejeon', 'sido', 'halfYear', 0.4800, 68, 0.6000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-chungbuk-week-20260601', 'region-chungbuk', 'sido', 'week', 0.0100, 57, 0.5200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-chungbuk-month-20260601', 'region-chungbuk', 'sido', 'month', 0.0500, 57, 0.5200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-chungbuk-halfYear-20260601', 'region-chungbuk', 'sido', 'halfYear', 0.2800, 57, 0.5200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeongbuk-week-20260601', 'region-gyeongbuk', 'sido', 'week', -0.0100, 82, 0.5700, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeongbuk-month-20260601', 'region-gyeongbuk', 'sido', 'month', -0.0800, 82, 0.5700, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeongbuk-halfYear-20260601', 'region-gyeongbuk', 'sido', 'halfYear', 0.1800, 82, 0.5700, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-daegu-week-20260601', 'region-daegu', 'sido', 'week', -0.1000, 110, 0.6700, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-daegu-month-20260601', 'region-daegu', 'sido', 'month', -0.4100, 110, 0.6700, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-daegu-halfYear-20260601', 'region-daegu', 'sido', 'halfYear', -0.6200, 110, 0.6700, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeonbuk-week-20260601', 'region-jeonbuk', 'sido', 'week', 0.0000, 63, 0.4900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeonbuk-month-20260601', 'region-jeonbuk', 'sido', 'month', 0.0400, 63, 0.4900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeonbuk-halfYear-20260601', 'region-jeonbuk', 'sido', 'halfYear', 0.1200, 63, 0.4900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gwangju-week-20260601', 'region-gwangju', 'sido', 'week', -0.0300, 59, 0.5200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gwangju-month-20260601', 'region-gwangju', 'sido', 'month', -0.1400, 59, 0.5200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gwangju-halfYear-20260601', 'region-gwangju', 'sido', 'halfYear', -0.2200, 59, 0.5200, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeonnam-week-20260601', 'region-jeonnam', 'sido', 'week', -0.0100, 48, 0.4300, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeonnam-month-20260601', 'region-jeonnam', 'sido', 'month', -0.0600, 48, 0.4300, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeonnam-halfYear-20260601', 'region-jeonnam', 'sido', 'halfYear', 0.0500, 48, 0.4300, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeongnam-week-20260601', 'region-gyeongnam', 'sido', 'week', 0.0400, 88, 0.5900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeongnam-month-20260601', 'region-gyeongnam', 'sido', 'month', 0.1900, 88, 0.5900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-gyeongnam-halfYear-20260601', 'region-gyeongnam', 'sido', 'halfYear', 0.5100, 88, 0.5900, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-ulsan-week-20260601', 'region-ulsan', 'sido', 'week', 0.0300, 47, 0.5000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-ulsan-month-20260601', 'region-ulsan', 'sido', 'month', 0.1200, 47, 0.5000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-ulsan-halfYear-20260601', 'region-ulsan', 'sido', 'halfYear', 0.3900, 47, 0.5000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-busan-week-20260601', 'region-busan', 'sido', 'week', -0.0200, 126, 0.6600, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-busan-month-20260601', 'region-busan', 'sido', 'month', -0.0900, 126, 0.6600, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-busan-halfYear-20260601', 'region-busan', 'sido', 'halfYear', 0.2100, 126, 0.6600, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeju-week-20260601', 'region-jeju', 'sido', 'week', -0.0500, 36, 0.4000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeju-month-20260601', 'region-jeju', 'sido', 'month', -0.2100, 36, 0.4000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sido-region-jeju-halfYear-20260601', 'region-jeju', 'sido', 'halfYear', -0.3400, 36, 0.4000, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sigungu-region-seoul-jongno-week-20260601', 'region-seoul-jongno', 'sigungu', 'week', 0.0900, 26, 0.6100, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sigungu-region-seoul-jongno-month-20260601', 'region-seoul-jongno', 'sigungu', 'month', 0.1800, 26, 0.6100, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sigungu-region-seoul-jongno-halfYear-20260601', 'region-seoul-jongno', 'sigungu', 'halfYear', 0.4200, 26, 0.6100, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sigungu-region-seoul-mapo-week-20260601', 'region-seoul-mapo', 'sigungu', 'week', 0.1700, 42, 0.7400, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sigungu-region-seoul-mapo-month-20260601', 'region-seoul-mapo', 'sigungu', 'month', 0.3100, 42, 0.7400, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00'),
    ('map-sigungu-region-seoul-mapo-halfYear-20260601', 'region-seoul-mapo', 'sigungu', 'halfYear', 0.9200, 42, 0.7400, '2026-06-01 00:00:00', 'seed', 'mock heat layer · 실제 공공데이터 연결 전', 'mock', true, '2026-06-13 00:00:00');
