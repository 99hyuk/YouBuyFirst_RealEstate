insert into real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
) values
    ('region-seoul-mapo', 'region', '서울 마포구', 'seoul-mapo', '서울마포구', 'approved', 'ok', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('living-area-gyeonggi-dongtan-station', 'living_area', '동탄역권', 'gyeonggi-dongtan-station', '동탄역권', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('living-area-seoul-seongsu', 'living_area', '성수동 생활권', 'seoul-seongsu', '성수동생활권', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('living-area-seoul-jamsil', 'living_area', '잠실동 단지군', 'seoul-jamsil', '잠실동단지군', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('living-area-gyeonggi-bundang-pangyo', 'living_area', '분당·판교', 'gyeonggi-bundang-pangyo', '분당판교', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('living-area-incheon-songdo', 'living_area', '송도국제도시', 'incheon-songdo', '송도국제도시', 'approved', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('complex-raemian-onebailey', 'complex', '래미안 원베일리', 'raemian-onebailey', '래미안원베일리', 'candidate', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('complex-helio-city', 'complex', '헬리오시티', 'helio-city', '헬리오시티', 'candidate', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('complex-mapo-raemian-prugio', 'complex', '마포래미안푸르지오', 'mapo-raemian-prugio', '마포래미안푸르지오', 'candidate', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('complex-pangyo-prugio-grandble', 'complex', '판교푸르지오그랑블', 'pangyo-prugio-grandble', '판교푸르지오그랑블', 'candidate', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('complex-songdo-the-sharp-central', 'complex', '송도더샵센트럴', 'songdo-the-sharp-central', '송도더샵센트럴', 'candidate', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('complex-dongtan-lotte-castle', 'complex', '동탄역 롯데캐슬', 'dongtan-lotte-castle', '동탄역롯데캐슬', 'candidate', 'mock', '2026-06-13 00:00:00', '2026-06-13 00:00:00');

insert into real_estate_regions (
    target_id, region_level, parent_region_id, legal_dong_code, region_code, source
) values
    ('region-seoul-mapo', 'sigungu', 'region-seoul', '11440', '11440', 'seed:frontend-target-identity');

insert into real_estate_market_data_targets (
    target_id, provider, provider_dataset, lawd_code, enabled, refresh_interval_hours, stale_after_hours, created_at, updated_at
) values
    ('region-seoul-mapo', 'molit', 'molit_apt_trade', '11440', true, 24, 72, '2026-06-13 00:00:00', '2026-06-13 00:00:00'),
    ('region-seoul-mapo', 'molit', 'molit_apt_rent', '11440', true, 24, 72, '2026-06-13 00:00:00', '2026-06-13 00:00:00');
