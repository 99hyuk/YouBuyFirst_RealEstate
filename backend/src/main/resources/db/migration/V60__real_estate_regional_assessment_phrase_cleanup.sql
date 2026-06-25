update real_estate_regional_reports
set body = replace(body, '단기 판단은 거래와 전세가 우선이다.', '단기 해석은 거래와 전세가 우선이다.'),
    updated_at = '2026-06-25 03:30:00'
where generated_by = 'codex-quality-rewrite:regional-assessment-20260625'
  and body like '%단기 판단은 거래와 전세가 우선이다.%';
