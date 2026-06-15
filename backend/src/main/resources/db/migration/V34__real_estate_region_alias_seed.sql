insert into real_estate_aliases (
    target_id, target_type, alias, normalized_alias, alias_type, source, evidence_url,
    confidence, review_state, ambiguous, created_by, created_at, updated_at
)
select seed.target_id, seed.target_type, seed.alias, seed.normalized_alias, seed.alias_type,
       seed.source, seed.evidence_url, seed.confidence, seed.review_state, seed.ambiguous,
       seed.created_by, seed.created_at, seed.updated_at
from (
    select 'region-seoul' target_id, 'region' target_type, '서울' alias, '서울' normalized_alias, 'short_name' alias_type, 'seed:region-alias' source, null evidence_url, 1.0 confidence, 'approved' review_state, false ambiguous, 'seed' created_by, '2026-06-15 00:00:00' created_at, '2026-06-15 00:00:00' updated_at
    union all select 'region-seoul', 'region', '서울특별시', '서울특별시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-seoul-jongno', 'region', '종로', '종로', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-seoul-jongno', 'region', '종로구', '종로구', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-seoul-jongno', 'region', '서울 종로구', '서울종로구', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-seoul-mapo', 'region', '마포', '마포', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-seoul-mapo', 'region', '마포구', '마포구', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-seoul-mapo', 'region', '서울 마포구', '서울마포구', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-incheon', 'region', '인천', '인천', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-incheon', 'region', '인천광역시', '인천광역시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gyeonggi', 'region', '경기', '경기', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gyeonggi', 'region', '경기도', '경기도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gangwon', 'region', '강원', '강원', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gangwon', 'region', '강원도', '강원도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-chungnam', 'region', '충남', '충남', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-chungnam', 'region', '충청남도', '충청남도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-sejong', 'region', '세종', '세종', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-sejong', 'region', '세종시', '세종시', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-sejong', 'region', '세종특별자치시', '세종특별자치시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-daejeon', 'region', '대전', '대전', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-daejeon', 'region', '대전광역시', '대전광역시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-chungbuk', 'region', '충북', '충북', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-chungbuk', 'region', '충청북도', '충청북도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gyeongbuk', 'region', '경북', '경북', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gyeongbuk', 'region', '경상북도', '경상북도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-daegu', 'region', '대구', '대구', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-daegu', 'region', '대구광역시', '대구광역시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-jeonbuk', 'region', '전북', '전북', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-jeonbuk', 'region', '전라북도', '전라북도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gwangju', 'region', '광주', '광주', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gwangju', 'region', '광주광역시', '광주광역시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-jeonnam', 'region', '전남', '전남', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-jeonnam', 'region', '전라남도', '전라남도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gyeongnam', 'region', '경남', '경남', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-gyeongnam', 'region', '경상남도', '경상남도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-ulsan', 'region', '울산', '울산', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-ulsan', 'region', '울산광역시', '울산광역시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-busan', 'region', '부산', '부산', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-busan', 'region', '부산광역시', '부산광역시', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-jeju', 'region', '제주', '제주', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-jeju', 'region', '제주도', '제주도', 'short_name', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
    union all select 'region-jeju', 'region', '제주특별자치도', '제주특별자치도', 'official', 'seed:region-alias', null, 1.0, 'approved', false, 'seed', '2026-06-15 00:00:00', '2026-06-15 00:00:00'
) seed
join real_estate_targets target on target.id = seed.target_id
where not exists (
    select 1
    from real_estate_aliases existing
    where existing.target_id = seed.target_id
      and existing.normalized_alias = seed.normalized_alias
);
