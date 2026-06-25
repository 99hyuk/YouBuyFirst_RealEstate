update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '화성시는 GTX-A 동탄역 접근성과 반도체 배후 수요, 외곽 택지 입주 부담이 동시에 작동하는 시장',
    summary = '화성시는 동탄역권과 삼성 화성·기흥 반도체 배후 수요가 가격 하방을 만들지만, 동탄2·봉담·남양권 입주 흡수 여부가 상승 지속성을 제한하는 구간입니다.',
    body = '평가: 화성시는 동탄역권과 삼성 화성·기흥 반도체 배후 수요가 가장 선명하고, 봉담·남양·향남은 같은 화성 안에서도 가격 설명력이 다릅니다.
전망: 선별 관망. GTX-A 접근성과 반도체 배후 수요는 긍정적이나 외곽 택지 입주가 전세를 누르면 매매 회복은 동탄 핵심권 위주로 제한될 가능성이 큽니다.',
    expectation_points_json = '["삼성 화성·기흥 배후 수요","GTX-A 동탄역 접근성"]',
    concern_points_json = '["동탄2·봉담 입주 흡수","외곽 택지 전세 민감도"]',
    confidence = 0.84,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-gyeonggi-hwaseongsi'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';

update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '광명시는 뉴타운 신축 전환과 철산·하안 구축 격차를 분리해야 하는 서울 서남권 대체 시장',
    summary = '광명시는 서울 서남권 대체 수요와 광명뉴타운 신축 선호가 강하지만, 철산·하안 구축까지 같은 속도로 따라오기는 어려운 시장입니다.',
    body = '평가: 광명시는 광명뉴타운 신축 전환이 가격 기준을 끌어올리고, 서울 구로·금천·영등포 접근성이 실수요를 받치는 구조입니다.
전망: 선별 회복 가능성. 신축 입주권과 준신축은 방어력이 있으나 철산·하안 구축은 전세와 거래량이 동행하지 않으면 가격 격차가 더 벌어질 수 있습니다.',
    expectation_points_json = '["광명뉴타운 신축 전환","서울 서남권 대체 수요"]',
    concern_points_json = '["철산·하안 구축 격차","정비 이주·입주 시차"]',
    confidence = 0.84,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-gyeonggi-gwangmyeong'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';

update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '성남 수정구는 위례 접근성과 원도심 정비 기대가 공존하지만 공급 경쟁을 피하기 어려운 시장',
    summary = '성남 수정구는 위례·판교 접근 생활권이라는 장점이 있으나, 위례 공급 경쟁과 원도심 구축 유동성을 함께 봐야 합니다.',
    body = '평가: 성남 수정구는 위례와 판교 접근성이 장점이지만, 원도심과 위례 생활권의 수요층이 완전히 같지는 않습니다.
전망: 보수적 선별. 정비 기대가 있는 구간은 관심을 받을 수 있으나 위례 공급 경쟁과 구축 유동성이 약하면 단기 상승은 제한될 가능성이 높습니다.',
    expectation_points_json = '["위례·판교 접근 생활권","성남 원도심 정비 기대"]',
    concern_points_json = '["위례 공급 경쟁","원도심 구축 유동성"]',
    confidence = 0.82,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-gyeonggi-seongnamsisujeonggu'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';

update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '성남 중원구는 산업 배후와 노후 주거 비중이 맞물려 가격 탄력이 제한되는 시장',
    summary = '성남 중원구는 성남하이테크밸리와 모란·상대원 생활권 수요가 있으나, 노후 주거 비중과 분당·판교 대체 한계가 부담입니다.',
    body = '평가: 성남 중원구는 성남하이테크밸리 배후 수요와 모란·상대원 상권 접근성이 있지만, 주거 상품성은 분당·판교와 뚜렷하게 갈립니다.
전망: 관망 우위. 저가 실거주 수요는 방어력이 있으나 노후 단지 비중이 높아 전세와 거래량 회복이 확인되기 전까지 상승 탄력은 제한적입니다.',
    expectation_points_json = '["성남하이테크밸리 배후","모란·상대원 상권 수요"]',
    concern_points_json = '["노후 주거 비중","분당·판교 대체 한계"]',
    confidence = 0.82,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-gyeonggi-seongnamsijungwongu'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';

update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '분당구는 판교 업무 배후와 1기 신도시 정비 기대가 강하지만 고가 선반영 부담이 큰 시장',
    summary = '분당구는 판교 업무 배후 전세 수요와 1기 신도시 정비 기대가 핵심이나, 고가 구간은 재건축 일정이 길어질수록 부담이 커집니다.',
    body = '평가: 분당구는 판교 업무 배후 수요와 학군·생활 인프라가 강해 성남권 안에서도 가장 방어력이 높은 구간입니다.
전망: 선별 회복 가능성. 다만 고가 구간은 이미 정비 기대가 상당 부분 반영돼 있어 재건축 일정과 전세가 동행하지 않으면 당분간 가격 부담이 남습니다.',
    expectation_points_json = '["판교 업무 배후 전세","1기 신도시 정비 기대"]',
    concern_points_json = '["고가 구간 선반영","재건축 일정 장기화"]',
    confidence = 0.85,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-gyeonggi-seongnamsibundanggu'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';

update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '성북구는 길음·장위 정비 신축과 외곽 구축의 온도 차가 커지는 동북권 시장',
    summary = '성북구는 길음·장위 정비 신축과 동북권 실거주 가격대가 기대 요인이지만, 외곽 구축 거래 둔화와 기대 선반영은 부담입니다.',
    body = '평가: 성북구는 길음·장위 정비 신축이 가격 기준을 만들고, 동북권 실거주 가격대가 하방을 받치는 시장입니다.
전망: 선별 관망. 신축·준신축은 방어력이 있으나 외곽 구축은 거래량이 얇아 정비 기대만으로 지속 상승을 설명하기 어렵습니다.',
    expectation_points_json = '["길음·장위 정비 신축","동북권 실거주 가격대"]',
    concern_points_json = '["외곽 구축 거래 둔화","정비 기대 선반영"]',
    confidence = 0.82,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-seoul-seongbuk'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';

update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '구로구는 G밸리 직주근접 수요가 뚜렷하지만 구축 노후화가 가격 상단을 누르는 시장',
    summary = '구로구는 G밸리와 신도림·구로 환승 수요가 실수요를 만들지만, 서남권 구축 노후화와 산업 배후 수요 변동성을 분리해야 합니다.',
    body = '평가: 구로구는 G밸리 직주근접과 신도림·구로 환승 수요가 뚜렷해 실거주 기반은 분명합니다.
전망: 관망 우위. 직주근접 수요는 하방을 받치지만 구축 노후화와 산업 배후 수요 변동성이 커서 전세 방어가 확인되기 전까지 상승 지속성은 제한적입니다.',
    expectation_points_json = '["G밸리 직주근접 수요","신도림·구로 환승 수요"]',
    concern_points_json = '["서남권 구축 노후화","산업 배후 수요 변동"]',
    confidence = 0.82,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-seoul-guro'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';

update real_estate_regional_reports
set report_version = 'regional-report-assessment-v5',
    prompt_version = 'codex-regional-assessment-diversification-prompt-20260625',
    model_name = 'codex-gpt-5-regional-assessment',
    headline = '도봉구는 GTX-C·창동상계 기대가 있으나 착공 전 기대 선반영을 경계해야 하는 시장',
    summary = '도봉구는 GTX-C와 창동상계 개발 기대, 중저가 실거주 수요가 장점이나 착공 전 기대 선반영과 노후 단지 전세 약세가 부담입니다.',
    body = '평가: 도봉구는 GTX-C와 창동상계 개발 기대가 가장 큰 재평가 논리이고, 서울 안 중저가 실거주 수요가 하방을 지지합니다.
전망: 보수적 관망. 교통·개발 기대가 가격에 먼저 반영될 수 있어 착공·사업 속도와 노후 단지 전세 회복이 확인되기 전까지 추격 매수 논리는 약합니다.',
    expectation_points_json = '["GTX-C·창동상계 기대","중저가 실거주 방어"]',
    concern_points_json = '["착공 전 기대 선반영","노후 단지 전세 약세"]',
    confidence = 0.82,
    as_of = '2026-06-25 00:00:00',
    published_at = '2026-06-25 05:40:00',
    updated_at = '2026-06-25 05:40:00'
where target_id = 'region-seoul-dobong'
  and generated_by = 'codex-quality-rewrite:regional-assessment-20260625';
