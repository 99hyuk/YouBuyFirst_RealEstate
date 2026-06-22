-- SSAFY_HOME housedeals -> real_estate_market_facts chunk importer.
--
-- Run this after tools/realestate/ssafy_home_bootstrap.sql has imported
-- regions, complexes, provider keys, aliases, and contains edges.
--
-- Example:
--   SET @deal_min_no = 1;
--   SET @deal_max_no = 100000;
--   SOURCE tools/realestate/ssafy_home_housedeals_chunk.sql;

SET @ssafy_bootstrap_now = CURRENT_TIMESTAMP(6);
SET @deal_min_no = COALESCE(@deal_min_no, 0);
SET @deal_max_no = COALESCE(@deal_max_no, 100000);

DROP TEMPORARY TABLE IF EXISTS tmp_ssafy_home_complexes_for_deals;
CREATE TEMPORARY TABLE tmp_ssafy_home_complexes_for_deals AS
SELECT
    hi.apt_seq,
    CONCAT('complex-ssafy-home-', LOWER(REPLACE(hi.apt_seq, '_', '-'))) AS target_id,
    CONCAT(hi.sgg_cd, hi.umd_cd) AS legal_dong_code,
    hi.apt_nm AS display_name,
    hi.umd_nm,
    hi.jibun,
    hi.build_year,
    CAST(NULLIF(TRIM(hi.latitude), '') AS DECIMAL(10, 7)) AS latitude,
    CAST(NULLIF(TRIM(hi.longitude), '') AS DECIMAL(10, 7)) AS longitude
FROM ssafy_home.houseinfos hi
JOIN real_estate_complexes c
    ON c.target_id = CONCAT('complex-ssafy-home-', LOWER(REPLACE(hi.apt_seq, '_', '-')))
WHERE hi.apt_seq IS NOT NULL
  AND TRIM(hi.apt_seq) <> ''
  AND hi.apt_nm IS NOT NULL
  AND TRIM(hi.apt_nm) <> '';

CREATE INDEX idx_tmp_ssafy_home_complexes_for_deals_apt_seq ON tmp_ssafy_home_complexes_for_deals (apt_seq);

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
JOIN tmp_ssafy_home_complexes_for_deals c
    ON c.apt_seq = hd.apt_seq
WHERE hd.no BETWEEN @deal_min_no AND @deal_max_no
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
    COUNT(*) AS imported_market_facts_in_chunk,
    @deal_min_no AS deal_min_no,
    @deal_max_no AS deal_max_no
FROM real_estate_market_facts
WHERE provider = 'ssafy_home'
  AND provider_dataset = 'ssafy_home_housedeals'
  AND CAST(SUBSTRING(provider_object_id, 23) AS UNSIGNED) BETWEEN @deal_min_no AND @deal_max_no;
