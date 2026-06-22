-- SSAFY_HOME -> YouBuyFirst real-estate bootstrap.
--
-- Purpose:
--   Keep the SSAFY_HOME dump as a source/staging schema, then project it into
--   the service-owned real_estate_* tables. The app must keep reading the
--   normalized tables, not ssafy_home directly.
--
-- Preconditions:
--   1. Run backend Flyway migrations for the target database first.
--   2. Import SSAFY_HOME_Schema.sql into schema `ssafy_home`.
--   3. Import SSAFY_HOME_Dump_2604.sql into schema `ssafy_home`.
--   4. Execute this file with the target service database selected.
--
-- Optional deal import:
--   SET @deal_min_no = 1;
--   SET @deal_max_no = 100000;
--   SET @import_ssafy_housedeals = TRUE;
--   SOURCE tools/realestate/ssafy_home_bootstrap.sql;

SET @ssafy_bootstrap_now = CURRENT_TIMESTAMP(6);
SET @deal_min_no = COALESCE(@deal_min_no, 0);
SET @deal_max_no = COALESCE(@deal_max_no, 9223372036854775807);
SET @import_ssafy_housedeals = COALESCE(@import_ssafy_housedeals, FALSE);

INSERT INTO real_estate_public_data_datasets (
    dataset_id, provider, provider_name, owner_org, display_name, fact_type, access_method, response_format,
    source_url, endpoint_url, target_granularity, date_granularity, refresh_interval, stale_after_hours,
    priority, backfill_required, enabled_for_backfill, source_row_count, notes, created_at, updated_at
)
VALUES
    (
        'ssafy_home_houseinfos', 'ssafy_home', 'SSAFY HOME dump', 'SSAFY',
        'SSAFY HOME 아파트 단지 좌표', 'complex_registry', 'sql_dump', 'mysql',
        'local:SSAFY_HOME_Dump_2604.sql', NULL, 'complex', 'snapshot', 'manual', 8760,
        5, true, false, NULL,
        'Local bootstrap source for apartment target, address, coordinate, alias, and provider-key registry.',
        @ssafy_bootstrap_now, @ssafy_bootstrap_now
    ),
    (
        'ssafy_home_housedeals', 'ssafy_home', 'SSAFY HOME dump', 'SSAFY',
        'SSAFY HOME 아파트 매매 실거래', 'apt_trade', 'sql_dump', 'mysql',
        'local:SSAFY_HOME_Dump_2604.sql', NULL, 'complex', 'day', 'manual', 8760,
        6, true, false, NULL,
        'Local bootstrap source for historical apartment trade facts. Use providerObjectId=ssafy_home:housedeals:{no}.',
        @ssafy_bootstrap_now, @ssafy_bootstrap_now
    )
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    notes = VALUES(notes),
    updated_at = VALUES(updated_at);

DROP TEMPORARY TABLE IF EXISTS tmp_ssafy_home_regions;
CREATE TEMPORARY TABLE tmp_ssafy_home_regions AS
SELECT
    dc.dong_code,
    CASE
        WHEN SUBSTRING(dc.dong_code, 3) = '00000000' THEN CONCAT(SUBSTRING(dc.dong_code, 1, 2), '000')
        WHEN SUBSTRING(dc.dong_code, 6) = '00000' THEN SUBSTRING(dc.dong_code, 1, 5)
        ELSE dc.dong_code
    END AS legal_dong_code,
    CASE
        WHEN SUBSTRING(dc.dong_code, 3) = '00000000' THEN SUBSTRING(dc.dong_code, 1, 2)
        WHEN SUBSTRING(dc.dong_code, 6) = '00000' THEN SUBSTRING(dc.dong_code, 1, 5)
        ELSE dc.dong_code
    END AS region_code,
    CASE
        WHEN SUBSTRING(dc.dong_code, 3) = '00000000' THEN 'sido'
        WHEN SUBSTRING(dc.dong_code, 6) = '00000' THEN 'sigungu'
        ELSE 'eupmyeondong'
    END AS region_level,
    CASE
        WHEN SUBSTRING(dc.dong_code, 3) = '00000000' THEN NULL
        WHEN SUBSTRING(dc.dong_code, 6) = '00000' THEN CONCAT(SUBSTRING(dc.dong_code, 1, 2), '000')
        ELSE SUBSTRING(dc.dong_code, 1, 5)
    END AS parent_legal_dong_code,
    CONCAT('region-', CASE
        WHEN SUBSTRING(dc.dong_code, 3) = '00000000' THEN CONCAT(SUBSTRING(dc.dong_code, 1, 2), '000')
        WHEN SUBSTRING(dc.dong_code, 6) = '00000' THEN SUBSTRING(dc.dong_code, 1, 5)
        ELSE dc.dong_code
    END) AS target_id,
    TRIM(CONCAT_WS(' ', dc.sido_name, dc.gugun_name, dc.dong_name)) AS display_name
FROM ssafy_home.dongcodes dc
WHERE dc.dong_code IS NOT NULL
  AND dc.dong_code REGEXP '^[0-9]{10}$'
  AND TRIM(CONCAT_WS(' ', dc.sido_name, dc.gugun_name, dc.dong_name)) <> '';

CREATE INDEX idx_tmp_ssafy_home_regions_code ON tmp_ssafy_home_regions (legal_dong_code);
CREATE INDEX idx_tmp_ssafy_home_regions_level ON tmp_ssafy_home_regions (region_level);

INSERT INTO real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
)
SELECT
    r.target_id,
    'region',
    r.display_name,
    r.target_id,
    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(r.display_name), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', '')),
    'approved',
    'ok',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_regions r
WHERE NOT EXISTS (
    SELECT 1
    FROM real_estate_regions existing_region
    WHERE existing_region.legal_dong_code = r.legal_dong_code
)
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    normalized_name = VALUES(normalized_name),
    review_state = 'approved',
    data_status = 'ok',
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_regions (
    target_id, region_level, parent_region_id, legal_dong_code, region_code, source
)
SELECT
    r.target_id,
    r.region_level,
    NULL,
    r.legal_dong_code,
    r.region_code,
    'ssafy_home:dongcodes'
FROM tmp_ssafy_home_regions r
WHERE r.region_level = 'sido'
  AND NOT EXISTS (
      SELECT 1 FROM real_estate_regions existing_region
      WHERE existing_region.legal_dong_code = r.legal_dong_code
  )
ON DUPLICATE KEY UPDATE
    region_level = VALUES(region_level),
    parent_region_id = VALUES(parent_region_id),
    legal_dong_code = VALUES(legal_dong_code),
    region_code = VALUES(region_code),
    source = VALUES(source);

INSERT INTO real_estate_regions (
    target_id, region_level, parent_region_id, legal_dong_code, region_code, source
)
SELECT
    r.target_id,
    r.region_level,
    parent.target_id,
    r.legal_dong_code,
    r.region_code,
    'ssafy_home:dongcodes'
FROM tmp_ssafy_home_regions r
LEFT JOIN real_estate_regions parent
    ON parent.legal_dong_code = r.parent_legal_dong_code
WHERE r.region_level = 'sigungu'
  AND NOT EXISTS (
      SELECT 1 FROM real_estate_regions existing_region
      WHERE existing_region.legal_dong_code = r.legal_dong_code
  )
ON DUPLICATE KEY UPDATE
    region_level = VALUES(region_level),
    parent_region_id = VALUES(parent_region_id),
    legal_dong_code = VALUES(legal_dong_code),
    region_code = VALUES(region_code),
    source = VALUES(source);

INSERT INTO real_estate_regions (
    target_id, region_level, parent_region_id, legal_dong_code, region_code, source
)
SELECT
    r.target_id,
    r.region_level,
    parent.target_id,
    r.legal_dong_code,
    r.region_code,
    'ssafy_home:dongcodes'
FROM tmp_ssafy_home_regions r
LEFT JOIN real_estate_regions parent
    ON parent.legal_dong_code = r.parent_legal_dong_code
WHERE r.region_level = 'eupmyeondong'
  AND NOT EXISTS (
      SELECT 1 FROM real_estate_regions existing_region
      WHERE existing_region.legal_dong_code = r.legal_dong_code
  )
ON DUPLICATE KEY UPDATE
    region_level = VALUES(region_level),
    parent_region_id = VALUES(parent_region_id),
    legal_dong_code = VALUES(legal_dong_code),
    region_code = VALUES(region_code),
    source = VALUES(source);

DROP TEMPORARY TABLE IF EXISTS tmp_ssafy_home_complexes;
CREATE TEMPORARY TABLE tmp_ssafy_home_complexes AS
SELECT
    hi.apt_seq,
    CONCAT('complex-ssafy-home-', LOWER(REPLACE(hi.apt_seq, '_', '-'))) AS target_id,
    COALESCE(region_full.target_id, region_sigungu.target_id) AS region_target_id,
    CONCAT(hi.sgg_cd, hi.umd_cd) AS legal_dong_code,
    hi.apt_nm AS display_name,
    LOWER(CONCAT('ssafy-home-', REPLACE(hi.apt_seq, '_', '-'))) AS slug,
    TRIM(CONCAT_WS(' ', dc.sido_name, dc.gugun_name, hi.umd_nm, hi.jibun)) AS jibun_address,
    TRIM(CONCAT_WS(
        ' ',
        dc.sido_name,
        dc.gugun_name,
        hi.road_nm,
        CONCAT(
            NULLIF(TRIM(hi.road_nm_bonbun), ''),
            CASE
                WHEN NULLIF(TRIM(hi.road_nm_bubun), '') IS NULL OR TRIM(hi.road_nm_bubun) IN ('0', '00', '000') THEN ''
                ELSE CONCAT('-', TRIM(hi.road_nm_bubun))
            END
        )
    )) AS road_address,
    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(CONCAT_WS('', dc.sido_name, dc.gugun_name, hi.umd_nm, hi.jibun, hi.apt_nm)), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', '')) AS normalized_address,
    hi.build_year,
    CAST(NULLIF(TRIM(hi.latitude), '') AS DECIMAL(10, 7)) AS latitude,
    CAST(NULLIF(TRIM(hi.longitude), '') AS DECIMAL(10, 7)) AS longitude,
    hi.umd_nm,
    hi.jibun
FROM ssafy_home.houseinfos hi
LEFT JOIN ssafy_home.dongcodes dc
    ON dc.dong_code = CONCAT(hi.sgg_cd, hi.umd_cd)
LEFT JOIN real_estate_regions region_full
    ON region_full.legal_dong_code = CONCAT(hi.sgg_cd, hi.umd_cd)
LEFT JOIN real_estate_regions region_sigungu
    ON region_sigungu.legal_dong_code = hi.sgg_cd
WHERE hi.apt_seq IS NOT NULL
  AND TRIM(hi.apt_seq) <> ''
  AND hi.apt_nm IS NOT NULL
  AND TRIM(hi.apt_nm) <> '';

CREATE INDEX idx_tmp_ssafy_home_complexes_apt_seq ON tmp_ssafy_home_complexes (apt_seq);
CREATE INDEX idx_tmp_ssafy_home_complexes_target ON tmp_ssafy_home_complexes (target_id);
CREATE INDEX idx_tmp_ssafy_home_complexes_region ON tmp_ssafy_home_complexes (region_target_id);

INSERT INTO real_estate_targets (
    id, target_type, display_name, slug, normalized_name, review_state, data_status, created_at, updated_at
)
SELECT
    c.target_id,
    'complex',
    c.display_name,
    c.slug,
    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(c.display_name), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', '')),
    'approved',
    'ok',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_complexes c
ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    normalized_name = VALUES(normalized_name),
    review_state = 'approved',
    data_status = 'ok',
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_complexes (
    target_id, region_target_id, legal_dong_code, road_address, jibun_address, normalized_address,
    built_year, household_count, source, created_at, updated_at,
    latitude, longitude, coordinate_provider, coordinate_as_of, coordinate_status,
    marker_tone, price_summary, change_label, reaction_summary, marker_note, marker_data_status, marker_stale
)
SELECT
    c.target_id,
    c.region_target_id,
    c.legal_dong_code,
    NULLIF(c.road_address, ''),
    NULLIF(c.jibun_address, ''),
    NULLIF(c.normalized_address, ''),
    c.build_year,
    NULL,
    'ssafy_home:houseinfos',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now,
    c.latitude,
    c.longitude,
    'ssafy_home_dump',
    @ssafy_bootstrap_now,
    CASE WHEN c.latitude IS NOT NULL AND c.longitude IS NOT NULL THEN 'verified' ELSE 'unknown' END,
    'flat',
    '실거래 확인',
    'unknown',
    '커뮤니티 반응 연결 전',
    'SSAFY HOME dump의 houseinfos 좌표와 단지 정보를 기준으로 생성한 marker입니다.',
    CASE WHEN c.latitude IS NOT NULL AND c.longitude IS NOT NULL THEN 'ok' ELSE 'partial' END,
    CASE WHEN c.latitude IS NOT NULL AND c.longitude IS NOT NULL THEN FALSE ELSE TRUE END
FROM tmp_ssafy_home_complexes c
ON DUPLICATE KEY UPDATE
    region_target_id = VALUES(region_target_id),
    legal_dong_code = VALUES(legal_dong_code),
    road_address = VALUES(road_address),
    jibun_address = VALUES(jibun_address),
    normalized_address = VALUES(normalized_address),
    built_year = VALUES(built_year),
    source = VALUES(source),
    latitude = VALUES(latitude),
    longitude = VALUES(longitude),
    coordinate_provider = VALUES(coordinate_provider),
    coordinate_as_of = VALUES(coordinate_as_of),
    coordinate_status = VALUES(coordinate_status),
    marker_tone = VALUES(marker_tone),
    price_summary = VALUES(price_summary),
    change_label = VALUES(change_label),
    reaction_summary = VALUES(reaction_summary),
    marker_note = VALUES(marker_note),
    marker_data_status = VALUES(marker_data_status),
    marker_stale = VALUES(marker_stale),
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_complex_provider_keys (
    complex_target_id, provider, provider_dataset, provider_object_id, legal_dong_code,
    key_json, confidence, review_state, created_at, updated_at
)
SELECT
    c.target_id,
    'ssafy_home',
    'ssafy_home_houseinfos',
    c.apt_seq,
    c.legal_dong_code,
    JSON_OBJECT(
        'aptSeq', c.apt_seq,
        'sourceTable', 'houseinfos',
        'legalDongCode', c.legal_dong_code,
        'regionTargetId', c.region_target_id
    ),
    1.0,
    'approved',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_complexes c
ON DUPLICATE KEY UPDATE
    complex_target_id = VALUES(complex_target_id),
    legal_dong_code = VALUES(legal_dong_code),
    key_json = VALUES(key_json),
    confidence = VALUES(confidence),
    review_state = VALUES(review_state),
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_aliases (
    target_id, target_type, alias, normalized_alias, alias_type, source, evidence_url,
    confidence, review_state, ambiguous, created_by, created_at, updated_at
)
SELECT
    c.target_id,
    'complex',
    c.display_name,
    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(c.display_name), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', '')),
    'official',
    'ssafy_home:houseinfos',
    NULL,
    0.92,
    'approved',
    FALSE,
    'system',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_complexes c
WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(c.display_name), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', '')) <> ''
ON DUPLICATE KEY UPDATE
    alias = VALUES(alias),
    alias_type = VALUES(alias_type),
    source = VALUES(source),
    confidence = VALUES(confidence),
    review_state = VALUES(review_state),
    ambiguous = VALUES(ambiguous),
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_aliases (
    target_id, target_type, alias, normalized_alias, alias_type, source, evidence_url,
    confidence, review_state, ambiguous, created_by, created_at, updated_at
)
SELECT
    c.target_id,
    'complex',
    CONCAT(c.umd_nm, ' ', c.display_name),
    LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(CONCAT(c.umd_nm, ' ', c.display_name)), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', '')),
    'nearby_area',
    'ssafy_home:houseinfos',
    NULL,
    0.78,
    'approved',
    FALSE,
    'system',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_complexes c
WHERE c.umd_nm IS NOT NULL
  AND TRIM(c.umd_nm) <> ''
  AND LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(CONCAT(c.umd_nm, ' ', c.display_name)), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', ''))
      <> LOWER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(c.display_name), ' ', ''), '-', ''), '_', ''), '.', ''), ',', ''), '/', ''))
ON DUPLICATE KEY UPDATE
    alias = VALUES(alias),
    alias_type = VALUES(alias_type),
    source = VALUES(source),
    confidence = VALUES(confidence),
    review_state = VALUES(review_state),
    ambiguous = VALUES(ambiguous),
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type,
    confidence, source, review_state, created_at, updated_at
)
SELECT
    c.region_target_id,
    'region',
    c.target_id,
    'complex',
    'contains',
    0.90,
    'ssafy_home:houseinfos',
    'approved',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_complexes c
WHERE c.region_target_id IS NOT NULL
ON DUPLICATE KEY UPDATE
    confidence = VALUES(confidence),
    source = VALUES(source),
    review_state = VALUES(review_state),
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type,
    confidence, source, review_state, created_at, updated_at
)
SELECT
    parent_region.target_id,
    'region',
    c.target_id,
    'complex',
    'contains',
    0.86,
    'ssafy_home:houseinfos:ancestor',
    'approved',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_complexes c
JOIN real_estate_regions child_region
    ON child_region.target_id = c.region_target_id
JOIN real_estate_regions parent_region
    ON parent_region.target_id = child_region.parent_region_id
WHERE c.region_target_id IS NOT NULL
ON DUPLICATE KEY UPDATE
    confidence = GREATEST(confidence, VALUES(confidence)),
    source = VALUES(source),
    review_state = VALUES(review_state),
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_target_edges (
    from_target_id, from_target_type, to_target_id, to_target_type, edge_type,
    confidence, source, review_state, created_at, updated_at
)
SELECT
    grandparent_region.target_id,
    'region',
    c.target_id,
    'complex',
    'contains',
    0.82,
    'ssafy_home:houseinfos:ancestor',
    'approved',
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM tmp_ssafy_home_complexes c
JOIN real_estate_regions child_region
    ON child_region.target_id = c.region_target_id
JOIN real_estate_regions parent_region
    ON parent_region.target_id = child_region.parent_region_id
JOIN real_estate_regions grandparent_region
    ON grandparent_region.target_id = parent_region.parent_region_id
WHERE c.region_target_id IS NOT NULL
ON DUPLICATE KEY UPDATE
    confidence = GREATEST(confidence, VALUES(confidence)),
    source = VALUES(source),
    review_state = VALUES(review_state),
    updated_at = VALUES(updated_at);

INSERT INTO real_estate_market_facts (
    target_type, target_id, fact_type, provider, provider_dataset, provider_object_id,
    legal_dong_code, observed_at, as_of, ingested_at, source_updated_at,
    value_json, data_status, stale, created_at, updated_at
)
SELECT
    'complex',
    c.target_id,
    'apt_trade',
    'ssafy_home',
    'ssafy_home_housedeals',
    CONCAT('ssafy_home:housedeals:', hd.no),
    c.legal_dong_code,
    STR_TO_DATE(CONCAT(hd.deal_year, '-', LPAD(hd.deal_month, 2, '0'), '-', LPAD(hd.deal_day, 2, '0')), '%Y-%m-%d'),
    STR_TO_DATE(CONCAT(hd.deal_year, '-', LPAD(hd.deal_month, 2, '0'), '-01'), '%Y-%m-%d'),
    @ssafy_bootstrap_now,
    NULL,
    JSON_OBJECT(
        'apartmentName', c.display_name,
        'legalDongName', c.umd_nm,
        'jibun', c.jibun,
        'aptSeq', c.apt_seq,
        'aptDong', NULLIF(TRIM(hd.apt_dong), ''),
        'floor', NULLIF(TRIM(hd.floor), ''),
        'exclusiveAreaSqm', hd.exclu_use_ar,
        'dealAmountManwon', CAST(REPLACE(hd.deal_amount, ',', '') AS UNSIGNED),
        'builtYear', c.build_year,
        'latitude', c.latitude,
        'longitude', c.longitude,
        'sourceTable', 'housedeals'
    ),
    'ok',
    FALSE,
    @ssafy_bootstrap_now,
    @ssafy_bootstrap_now
FROM ssafy_home.housedeals hd
JOIN tmp_ssafy_home_complexes c
    ON c.apt_seq = hd.apt_seq
WHERE hd.no BETWEEN @deal_min_no AND @deal_max_no
  AND @import_ssafy_housedeals = TRUE
  AND hd.deal_year IS NOT NULL
  AND hd.deal_month BETWEEN 1 AND 12
  AND hd.deal_day BETWEEN 1 AND 31
  AND NULLIF(TRIM(hd.deal_amount), '') IS NOT NULL
ON DUPLICATE KEY UPDATE
    target_id = VALUES(target_id),
    legal_dong_code = VALUES(legal_dong_code),
    observed_at = VALUES(observed_at),
    as_of = VALUES(as_of),
    ingested_at = VALUES(ingested_at),
    value_json = VALUES(value_json),
    data_status = VALUES(data_status),
    stale = VALUES(stale),
    updated_at = VALUES(updated_at);

SELECT
    (SELECT COUNT(*) FROM real_estate_regions WHERE source = 'ssafy_home:dongcodes') AS imported_regions,
    (SELECT COUNT(*) FROM real_estate_complexes WHERE source = 'ssafy_home:houseinfos') AS imported_complexes,
    (SELECT COUNT(*) FROM real_estate_market_facts WHERE provider = 'ssafy_home') AS imported_market_facts,
    @deal_min_no AS deal_min_no,
    @deal_max_no AS deal_max_no;
