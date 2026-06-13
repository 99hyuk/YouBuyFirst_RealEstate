alter table real_estate_complexes
    add column latitude decimal(10, 7);

alter table real_estate_complexes
    add column longitude decimal(10, 7);

alter table real_estate_complexes
    add column coordinate_provider varchar(80);

alter table real_estate_complexes
    add column coordinate_as_of datetime(6);

alter table real_estate_complexes
    add column coordinate_status varchar(30) not null default 'unknown';

alter table real_estate_complexes
    add column marker_tone varchar(20) not null default 'flat';

alter table real_estate_complexes
    add column price_summary varchar(80);

alter table real_estate_complexes
    add column change_label varchar(40);

alter table real_estate_complexes
    add column reaction_summary varchar(200);

alter table real_estate_complexes
    add column marker_note varchar(500);

alter table real_estate_complexes
    add column marker_data_status varchar(30) not null default 'unknown';

alter table real_estate_complexes
    add column marker_stale boolean not null default true;

create index idx_real_estate_complexes_coordinate_status
    on real_estate_complexes (coordinate_status);

update real_estate_targets
set display_name = '서울 마포구',
    normalized_name = '서울마포구',
    data_status = 'ok',
    updated_at = '2026-06-14 00:00:00'
where id = 'region-seoul-mapo';

update real_estate_targets
set display_name = '동탄역권',
    normalized_name = '동탄역권',
    updated_at = '2026-06-14 00:00:00'
where id = 'living-area-gyeonggi-dongtan-station';

update real_estate_targets
set display_name = '마포래미안푸르지오',
    normalized_name = '마포래미안푸르지오',
    updated_at = '2026-06-14 00:00:00'
where id = 'complex-mapo-raemian-prugio';

update real_estate_targets
set display_name = '동탄역 롯데캐슬',
    normalized_name = '동탄역롯데캐슬',
    updated_at = '2026-06-14 00:00:00'
where id = 'complex-dongtan-lotte-castle';

insert into real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
)
select 'complex-gongdeok-xi', 'complex', '공덕자이', 'gongdeok-xi', '공덕자이', 'candidate', 'mock', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (select 1 from real_estate_targets where id = 'complex-gongdeok-xi');

insert into real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
)
select 'complex-ahyeon-raemian', 'complex', '아현래미안', 'ahyeon-raemian', '아현래미안', 'candidate', 'mock', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (select 1 from real_estate_targets where id = 'complex-ahyeon-raemian');

insert into real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
)
select 'complex-dongtan-station-prugio', 'complex', '동탄역 푸르지오', 'dongtan-station-prugio', '동탄역푸르지오', 'candidate', 'mock', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (select 1 from real_estate_targets where id = 'complex-dongtan-station-prugio');

insert into real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
)
select 'complex-dongtan-ubora', 'complex', '동탄역 반도유보라', 'dongtan-ubora', '동탄역반도유보라', 'candidate', 'mock', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (select 1 from real_estate_targets where id = 'complex-dongtan-ubora');

insert into real_estate_complexes (
    target_id, region_target_id, legal_dong_code, road_address, jibun_address, normalized_address,
    built_year, household_count, source, created_at, updated_at,
    latitude, longitude, coordinate_provider, coordinate_as_of, coordinate_status,
    marker_tone, price_summary, change_label, reaction_summary, marker_note, marker_data_status, marker_stale
)
select 'complex-mapo-raemian-prugio', 'region-seoul-mapo', null, '서울 마포구 아현동 일대', '서울 마포구 아현동 일대', '서울마포구아현동마포래미안푸르지오',
       null, null, 'seed:front-fixture-marker', '2026-06-14 00:00:00', '2026-06-14 00:00:00',
       37.5536000, 126.9564000, 'front_fixture', '2026-06-13 00:00:00', 'mock',
       'up', '15.3억', '+0.21%', '학군·전세권 언급 증가', '실제 단지 좌표 provider 연결 전 상세 지도 UX 검증용 marker입니다.', 'mock', true
where not exists (select 1 from real_estate_complexes where target_id = 'complex-mapo-raemian-prugio');

insert into real_estate_complexes (
    target_id, region_target_id, legal_dong_code, road_address, jibun_address, normalized_address,
    built_year, household_count, source, created_at, updated_at,
    latitude, longitude, coordinate_provider, coordinate_as_of, coordinate_status,
    marker_tone, price_summary, change_label, reaction_summary, marker_note, marker_data_status, marker_stale
)
select 'complex-gongdeok-xi', 'region-seoul-mapo', null, '서울 마포구 공덕동 일대', '서울 마포구 공덕동 일대', '서울마포구공덕동공덕자이',
       null, null, 'seed:front-fixture-marker', '2026-06-14 00:00:00', '2026-06-14 00:00:00',
       37.5452000, 126.9508000, 'front_fixture', '2026-06-13 00:00:00', 'mock',
       'flat', '14.8억', '+0.03%', '전세 매물 확인 필요', '단지 provider key와 실거래 API 매핑 전 후보 marker입니다.', 'mock', true
where not exists (select 1 from real_estate_complexes where target_id = 'complex-gongdeok-xi');

insert into real_estate_complexes (
    target_id, region_target_id, legal_dong_code, road_address, jibun_address, normalized_address,
    built_year, household_count, source, created_at, updated_at,
    latitude, longitude, coordinate_provider, coordinate_as_of, coordinate_status,
    marker_tone, price_summary, change_label, reaction_summary, marker_note, marker_data_status, marker_stale
)
select 'complex-ahyeon-raemian', 'region-seoul-mapo', null, '서울 마포구 아현동 일대', '서울 마포구 아현동 일대', '서울마포구아현동아현래미안',
       null, null, 'seed:front-fixture-marker', '2026-06-14 00:00:00', '2026-06-14 00:00:00',
       37.5571000, 126.9518000, 'front_fixture', '2026-06-13 00:00:00', 'mock',
       'down', '13.9억', '-0.06%', '가격 부담·전세 우려', '반응 지표와 시장 fact 연결 전 비교용 후보 marker입니다.', 'mock', true
where not exists (select 1 from real_estate_complexes where target_id = 'complex-ahyeon-raemian');

insert into real_estate_complexes (
    target_id, region_target_id, legal_dong_code, road_address, jibun_address, normalized_address,
    built_year, household_count, source, created_at, updated_at,
    latitude, longitude, coordinate_provider, coordinate_as_of, coordinate_status,
    marker_tone, price_summary, change_label, reaction_summary, marker_note, marker_data_status, marker_stale
)
select 'complex-dongtan-lotte-castle', 'region-gyeonggi', null, '경기 화성시 동탄역권 일대', '경기 화성시 동탄역권 일대', '경기화성동탄역롯데캐슬',
       null, null, 'seed:front-fixture-marker', '2026-06-14 00:00:00', '2026-06-14 00:00:00',
       37.1991000, 127.0986000, 'front_fixture', '2026-06-13 00:00:00', 'mock',
       'up', '12.2억', '+0.19%', 'GTX·전세권 언급 증가', '카카오맵 SDK와 리포트 패널 상호작용 검증용 marker입니다.', 'mock', true
where not exists (select 1 from real_estate_complexes where target_id = 'complex-dongtan-lotte-castle');

insert into real_estate_complexes (
    target_id, region_target_id, legal_dong_code, road_address, jibun_address, normalized_address,
    built_year, household_count, source, created_at, updated_at,
    latitude, longitude, coordinate_provider, coordinate_as_of, coordinate_status,
    marker_tone, price_summary, change_label, reaction_summary, marker_note, marker_data_status, marker_stale
)
select 'complex-dongtan-station-prugio', 'region-gyeonggi', null, '경기 화성시 오산동 일대', '경기 화성시 오산동 일대', '경기화성오산동동탄역푸르지오',
       null, null, 'seed:front-fixture-marker', '2026-06-14 00:00:00', '2026-06-14 00:00:00',
       37.2021000, 127.0943000, 'front_fixture', '2026-06-13 00:00:00', 'mock',
       'flat', '10.6억', '+0.02%', '교통 기대와 입주 우려 공존', '실제 단지 좌표와 provider key 연결 전 후보 marker입니다.', 'mock', true
where not exists (select 1 from real_estate_complexes where target_id = 'complex-dongtan-station-prugio');

insert into real_estate_complexes (
    target_id, region_target_id, legal_dong_code, road_address, jibun_address, normalized_address,
    built_year, household_count, source, created_at, updated_at,
    latitude, longitude, coordinate_provider, coordinate_as_of, coordinate_status,
    marker_tone, price_summary, change_label, reaction_summary, marker_note, marker_data_status, marker_stale
)
select 'complex-dongtan-ubora', 'region-gyeonggi', null, '경기 화성시 동탄역권 일대', '경기 화성시 동탄역권 일대', '경기화성동탄역반도유보라',
       null, null, 'seed:front-fixture-marker', '2026-06-14 00:00:00', '2026-06-14 00:00:00',
       37.1955000, 127.1021000, 'front_fixture', '2026-06-13 00:00:00', 'mock',
       'down', '9.7억', '-0.08%', '입주 물량·전세 매물 우려', '공급과 전세 지표를 함께 대조할 후보 marker입니다.', 'mock', true
where not exists (select 1 from real_estate_complexes where target_id = 'complex-dongtan-ubora');

insert into real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type, confidence, source, review_state, created_at, updated_at
)
select 'region-seoul-mapo', 'region', 'complex-mapo-raemian-prugio', 'complex', 'contains', 0.80, 'seed:complex-map-marker', 'candidate', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (
    select 1 from real_estate_target_edges
    where from_target_id = 'region-seoul-mapo' and to_target_id = 'complex-mapo-raemian-prugio' and edge_type = 'contains'
);

insert into real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type, confidence, source, review_state, created_at, updated_at
)
select 'region-seoul-mapo', 'region', 'complex-gongdeok-xi', 'complex', 'contains', 0.70, 'seed:complex-map-marker', 'candidate', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (
    select 1 from real_estate_target_edges
    where from_target_id = 'region-seoul-mapo' and to_target_id = 'complex-gongdeok-xi' and edge_type = 'contains'
);

insert into real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type, confidence, source, review_state, created_at, updated_at
)
select 'region-seoul-mapo', 'region', 'complex-ahyeon-raemian', 'complex', 'contains', 0.70, 'seed:complex-map-marker', 'candidate', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (
    select 1 from real_estate_target_edges
    where from_target_id = 'region-seoul-mapo' and to_target_id = 'complex-ahyeon-raemian' and edge_type = 'contains'
);

insert into real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type, confidence, source, review_state, created_at, updated_at
)
select 'living-area-gyeonggi-dongtan-station', 'living_area', 'complex-dongtan-lotte-castle', 'complex', 'contains', 0.78, 'seed:complex-map-marker', 'candidate', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (
    select 1 from real_estate_target_edges
    where from_target_id = 'living-area-gyeonggi-dongtan-station' and to_target_id = 'complex-dongtan-lotte-castle' and edge_type = 'contains'
);

insert into real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type, confidence, source, review_state, created_at, updated_at
)
select 'living-area-gyeonggi-dongtan-station', 'living_area', 'complex-dongtan-station-prugio', 'complex', 'contains', 0.68, 'seed:complex-map-marker', 'candidate', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (
    select 1 from real_estate_target_edges
    where from_target_id = 'living-area-gyeonggi-dongtan-station' and to_target_id = 'complex-dongtan-station-prugio' and edge_type = 'contains'
);

insert into real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type, confidence, source, review_state, created_at, updated_at
)
select 'living-area-gyeonggi-dongtan-station', 'living_area', 'complex-dongtan-ubora', 'complex', 'contains', 0.66, 'seed:complex-map-marker', 'candidate', '2026-06-14 00:00:00', '2026-06-14 00:00:00'
where not exists (
    select 1 from real_estate_target_edges
    where from_target_id = 'living-area-gyeonggi-dongtan-station' and to_target_id = 'complex-dongtan-ubora' and edge_type = 'contains'
);
