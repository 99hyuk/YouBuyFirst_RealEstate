update real_estate_public_data_datasets
set provider_name = '국토교통부',
    owner_org = '국토교통부',
    display_name = '아파트 매매 실거래가',
    updated_at = '2026-06-13 00:00:00'
where dataset_id = 'molit_apt_trade';

update real_estate_public_data_datasets
set provider_name = '국토교통부',
    owner_org = '국토교통부',
    display_name = '아파트 전월세 실거래가',
    updated_at = '2026-06-13 00:00:00'
where dataset_id = 'molit_apt_rent';

update real_estate_public_data_datasets
set provider_name = '국토교통부',
    owner_org = '국토교통부',
    display_name = '공동주택 호별 공시가격',
    updated_at = '2026-06-13 00:00:00'
where dataset_id = 'molit_official_apartment_price_csv';

update real_estate_public_data_datasets
set provider_name = '한국부동산원',
    owner_org = '한국부동산원',
    display_name = '부동산통계 조회 서비스',
    updated_at = '2026-06-13 00:00:00'
where dataset_id = 'reb_real_estate_statistics';

update real_estate_public_data_datasets
set provider_name = '국토교통 통계누리',
    owner_org = '국토교통부',
    display_name = '미분양주택현황보고',
    updated_at = '2026-06-13 00:00:00'
where dataset_id = 'molit_unsold_housing_stat';

update real_estate_public_data_datasets
set provider_name = '국토교통 통계누리',
    owner_org = '국토교통부',
    display_name = '주택 인허가 실적',
    updated_at = '2026-06-13 00:00:00'
where dataset_id = 'molit_housing_permit_stat';

update real_estate_public_data_datasets
set provider_name = '국토교통부 건축HUB',
    owner_org = '국토교통부',
    display_name = '주택건설사업계획승인 정보',
    updated_at = '2026-06-13 00:00:00'
where dataset_id = 'molit_buildinghub_housing_approval';
