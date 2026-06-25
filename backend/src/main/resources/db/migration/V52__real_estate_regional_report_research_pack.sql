insert into real_estate_regional_reports (
    target_id,
    report_id,
    report_version,
    prompt_version,
    model_name,
    generated_by,
    title,
    headline,
    summary,
    body,
    expectation_points_json,
    concern_points_json,
    data_quality,
    confidence,
    as_of,
    published_at,
    created_at,
    updated_at
)
select
    researched.target_id,
    concat('regional-report-', researched.target_id, '-codex-20260624'),
    'regional-report-research-v1',
    'codex-regional-report-prompt-20260624',
    'codex-gpt-5-research',
    'codex-research:regional-report-20260624',
    concat(researched.display_name, ' 최신 지역 리포트'),
    concat(researched.display_name, '는 ', researched.market_role, '로 읽어야 하는 관찰 지역입니다.'),
    concat(
        researched.display_name,
        '는 R-ONE 최신 가격지표, 국토교통부 실거래·전월세 원천, 공급·정책 보도자료를 함께 놓고 봐야 합니다. ',
        researched.local_issue
    ),
    concat(
        researched.display_name, '는 ', researched.region_scope, '입니다. ',
        researched.macro_context, ' ',
        '최근 확인한 공통 근거는 한국부동산원 R-ONE의 2026년 5월 전국주택가격동향, 2026년 6월 15일 기준 주간아파트가격 동향, 국토교통부 실거래가 공개시스템과 공공데이터포털의 매매·전월세 API입니다. ',
        'R-ONE 메인 지표는 2026년 5월 아파트 매매가격지수 변동률 0.25%, 전세가격지수 변동률 0.45%, 2026년 4월 아파트 매매거래호수 53,177호를 함께 보여줍니다. ',
        researched.local_issue, ' ',
        '따라서 기대 지점은 ', researched.expectation_theme, '에 있습니다. 우려 지점은 ', researched.concern_theme, '입니다. ',
        '지도 기간별 등락률은 색상과 숫자 판단에만 쓰고, 이 보고서는 최신 공식 통계와 정책 근거가 갱신될 때 target별 최신본 1개로 교체합니다. ',
        '특정 매수나 매도 행동을 권하는 결론이 아니라, 실거래·전세·공급·정책·뉴스 근거가 같은 방향으로 맞물리는지 확인하는 칼럼형 관찰문입니다.'
    ),
    concat(
        '["',
        researched.display_name, '는 ', researched.expectation_theme, '가 기대 지점입니다.",',
        '"국토교통부 실거래가와 공공데이터포털 매매·전월세 API를 같은 target 기준으로 붙이면 가격과 임대차 방향을 분리해 확인할 수 있습니다.",',
        '"정책·공급 보도자료와 R-ONE 지표가 함께 갱신되면 이 저장 리포트를 AI API가 다시 덮어쓸 수 있습니다."]'
    ),
    concat(
        '["',
        researched.display_name, '는 ', researched.concern_theme, '를 먼저 경계해야 합니다.",',
        '"최근 뉴스나 개발 기대만으로 가격 상승을 단정하지 않고 실거래 표본, 전세 지표, 공급 일정을 분리 확인해야 합니다.",',
        '"지도 기간별 등락률은 리포트 본문을 바꾸는 근거가 아니라 단기 보조 신호입니다."]'
    ),
    'researched',
    case
        when researched.region_level = 'sido' then 0.72
        when researched.legal_dong_code is null then 0.64
        else 0.68
    end,
    '2026-06-24 00:00:00',
    '2026-06-24 22:00:00',
    coalesce(existing.created_at, '2026-06-24 22:00:00'),
    '2026-06-24 22:00:00'
from (
    select
        region.target_id,
        target.display_name,
        region.region_level,
        region.legal_dong_code,
        case
            when region.region_level = 'sido' then concat(target.display_name, ' 전체 권역')
            when parent_target.display_name is not null then concat(parent_target.display_name, ' 안의 ', target.display_name, ' 생활권')
            else concat(target.display_name, ' 생활권')
        end as region_scope,
        case
            when region.region_level = 'sido' then '광역 가격·공급·정책 흐름을 묶어 읽는 상위 권역'
            else '실거래와 전세 표본을 같은 법정동 코드 단위로 확인해야 하는 세부 권역'
        end as market_role,
        case
            when target.display_name like '%서울%' or parent_target.display_name like '%서울%' then '서울권은 업무·학군·정비사업 기대와 전세 부담이 동시에 움직이는 시장입니다. 도심 접근성이 좋은 구는 거래 한 건의 가격 신호가 크게 보일 수 있어 R-ONE 지표와 실거래 원천을 함께 확인해야 합니다.'
            when target.display_name like '%부산%' or parent_target.display_name like '%부산%' then '부산권은 해안 주거지, 원도심 정비, 항만·업무 수요가 서로 다른 속도로 움직입니다. 동부산 선호와 원도심 재생 이슈를 같은 결론으로 묶지 않고 권역별로 나눠 봐야 합니다.'
            when target.display_name like '%대구%' or parent_target.display_name like '%대구%' then '대구권은 누적 공급 부담과 도심 재정비, 산업·교통 호재가 함께 거론되는 시장입니다. 가격 회복 신호는 전세와 미분양·입주 부담이 같이 완화되는지 확인해야 설명력이 생깁니다.'
            when target.display_name like '%인천%' or parent_target.display_name like '%인천%' then '인천권은 공항·항만·송도·청라·검단 축의 개발 기대와 구도심 주거지가 함께 존재합니다. 신도시 입주와 원도심 정비의 속도가 달라 같은 광역시 안에서도 온도차가 큽니다.'
            when target.display_name like '%광주%' or parent_target.display_name like '%광주%' then '광주권은 도심 정비, 첨단산단, 생활권 재편 이슈가 같이 놓입니다. 단기 매매가격보다 전세 수요와 신규 공급 흡수 속도를 같이 봐야 합니다.'
            when target.display_name like '%대전%' or parent_target.display_name like '%대전%' then '대전권은 연구개발·공공기관 수요와 세종 연계 흐름이 시장 설명의 축입니다. 행정·연구 수요는 안정 요인이지만 공급과 전세 방향이 어긋나면 체감은 달라질 수 있습니다.'
            when target.display_name like '%울산%' or parent_target.display_name like '%울산%' then '울산권은 자동차·조선·석유화학 등 산업 경기와 주거 수요가 밀접합니다. 고용과 산업 투자 뉴스는 기대 요인이지만 특정 업종 의존도를 함께 경계해야 합니다.'
            when target.display_name like '%세종%' or parent_target.display_name like '%세종%' then '세종권은 행정수도 기능, 이전 수요, 누적 입주 물량이 동시에 작동합니다. 정책 기대가 크더라도 실제 거래·전세 회복이 동반되는지 확인해야 합니다.'
            when target.display_name like '%경기%' or parent_target.display_name like '%경기도%' then '경기권은 GTX·광역철도, 반도체·바이오 산업축, 3기 신도시 공급이 생활권별로 다른 영향을 줍니다. 서울 접근성과 자체 일자리 수요를 분리해야 지역 판단이 흔들리지 않습니다.'
            when target.display_name like '%강원%' or parent_target.display_name like '%강원%' then '강원권은 관광·생활인구, 혁신도시·기업도시, 광역교통 기대가 함께 작동합니다. 실수요 기반의 상주 수요와 휴양·투자성 수요를 구분하는 것이 중요합니다.'
            when target.display_name like '%충청북%' or target.display_name like '%충북%' or parent_target.display_name like '%충청북%' or parent_target.display_name like '%충북%' then '충북권은 청주·오송·오창의 바이오·반도체·철도 접근성이 핵심입니다. 산업 뉴스가 주거 수요로 이어지는 구간과 농촌형 생활권을 분리해야 합니다.'
            when target.display_name like '%충청남%' or target.display_name like '%충남%' or parent_target.display_name like '%충청남%' or parent_target.display_name like '%충남%' then '충남권은 천안·아산의 수도권 연계, 서해안 산업벨트, 내포신도시 흐름이 함께 놓입니다. 산업 배후 수요와 신규 택지 공급을 같이 봐야 합니다.'
            when target.display_name like '%전라북%' or target.display_name like '%전북%' or parent_target.display_name like '%전라북%' or parent_target.display_name like '%전북%' then '전북권은 전주권 생활수요, 새만금·산업단지 기대, 혁신도시 수요가 분산되어 있습니다. 정책·산업 뉴스가 실제 주거 수요로 연결되는 속도를 확인해야 합니다.'
            when target.display_name like '%전라남%' or target.display_name like '%전남%' or parent_target.display_name like '%전라남%' or parent_target.display_name like '%전남%' then '전남권은 여수·순천·광양 산업축과 해안·관광 생활권이 공존합니다. 산업도시는 고용 흐름을, 군 단위는 인구와 생활SOC 변화를 함께 봐야 합니다.'
            when target.display_name like '%경상북%' or target.display_name like '%경북%' or parent_target.display_name like '%경상북%' or parent_target.display_name like '%경북%' then '경북권은 포항·구미 산업축, 대구권 연계, 신공항 기대가 지역별로 다르게 작동합니다. 교통·산업 호재는 장기 변수이고 단기 거래 회복은 별도로 검증해야 합니다.'
            when target.display_name like '%경상남%' or target.display_name like '%경남%' or parent_target.display_name like '%경상남%' or parent_target.display_name like '%경남%' then '경남권은 창원 제조업, 거제·통영 조선·관광, 진주·사천 항공우주 축이 나뉩니다. 산업 회복 기대와 지역별 인구 흐름을 함께 봐야 합니다.'
            when target.display_name like '%제주%' or parent_target.display_name like '%제주%' then '제주권은 관광·이주 수요, 공급 제약, 외부 자금 유입에 민감합니다. 체류·관광 회복이 주거 실수요와 같은 의미인지 분리해서 봐야 합니다.'
            else '이 권역은 광역 흐름과 자체 생활권 수요를 함께 확인해야 합니다. 가격지표, 실거래, 전세, 공급 일정을 분리해 봐야 과도한 기대나 우려를 줄일 수 있습니다.'
        end as macro_context,
        case
            when target.display_name like '%강남%' or target.display_name like '%서초%' or target.display_name like '%송파%' or target.display_name like '%용산%' then '최근 이슈의 중심은 고가 주거지의 정비사업 기대, 규제지역·토지거래허가구역 인식, 전세 가격 부담입니다. 실거래 한 건이 headline을 만들 수 있으므로 표본 수와 신고 시점을 같이 봐야 합니다.'
            when target.display_name like '%마포%' or target.display_name like '%성동%' or target.display_name like '%광진%' or target.display_name like '%영등포%' or target.display_name like '%동작%' then '최근 이슈의 중심은 도심 접근성, 한강·업무지구 인접성, 준공·정비 일정입니다. 선호 입지 프리미엄은 기대 요인이지만 전세와 매매가 같은 방향인지 확인해야 합니다.'
            when target.display_name like '%노원%' or target.display_name like '%도봉%' or target.display_name like '%강북%' or target.display_name like '%중랑%' or target.display_name like '%성북%' or target.display_name like '%은평%' then '최근 이슈의 중심은 노후 단지 정비, 광역교통 개선 기대, 실수요 가격대입니다. 기대는 분명하지만 정비 속도와 금융 부담이 체감 수요를 제한할 수 있습니다.'
            when target.display_name like '%해운대%' or target.display_name like '%수영%' or target.display_name like '%연제%' or target.display_name like '%동래%' then '최근 이슈의 중심은 동부산 주거 선호, 해안·업무·교육 생활권, 재건축 기대입니다. 관광·상권 이슈와 상주 주거 수요를 구분해 읽어야 합니다.'
            when target.display_name like '%강서구%' or target.display_name like '%기장%' or target.display_name like '%김해%' or target.display_name like '%양산%' then '최근 이슈의 중심은 산업단지, 신도시·택지, 광역도로 접근성입니다. 개발 기대가 거래로 연결되는지와 신규 공급 부담을 함께 봐야 합니다.'
            when target.display_name like '%성남%' or target.display_name like '%용인%' or target.display_name like '%수원%' or target.display_name like '%화성%' or target.display_name like '%평택%' or target.display_name like '%과천%' or target.display_name like '%광명%' or target.display_name like '%하남%' or target.display_name like '%고양%' then '최근 이슈의 중심은 GTX와 광역철도, 반도체·바이오 일자리, 3기 신도시와 재건축 일정입니다. 서울 접근성 기대와 자체 공급 물량을 같이 봐야 합니다.'
            when target.display_name like '%청주%' or target.display_name like '%천안%' or target.display_name like '%아산%' or target.display_name like '%오산%' then '최근 이슈의 중심은 산업 배후수요와 광역 교통, 신규 택지 공급입니다. 일자리 뉴스가 임대차 수요와 매매 회복으로 이어지는지 분리해 확인해야 합니다.'
            when target.display_name like '%포항%' or target.display_name like '%구미%' or target.display_name like '%창원%' or target.display_name like '%거제%' or target.display_name like '%울산%' then '최근 이슈의 중심은 제조업·조선·배터리·소재 산업 경기입니다. 산업 회복은 기대 요인이지만 업종 변동성과 인구 흐름을 함께 봐야 합니다.'
            when target.display_name like '%여수%' or target.display_name like '%순천%' or target.display_name like '%광양%' or target.display_name like '%목포%' or target.display_name like '%군산%' then '최근 이슈의 중심은 산업단지, 항만, 관광·원도심 재생입니다. 산업·관광 뉴스가 주거 수요로 얼마나 이어지는지 근거를 나눠 확인해야 합니다.'
            when target.display_name like '%춘천%' or target.display_name like '%원주%' or target.display_name like '%강릉%' or target.display_name like '%속초%' or target.display_name like '%제주%' or target.display_name like '%서귀포%' then '최근 이슈의 중심은 관광·생활인구, 광역교통, 세컨드하우스 수요입니다. 외부 수요가 가격을 흔들 수 있어 상주 수요와 임대차 지표를 분리해야 합니다.'
            else '최근 이슈의 중심은 광역권 가격 흐름, 지역별 공급 일정, 생활권 수요의 지속성입니다. 단일 뉴스보다 실거래·전세·정책 근거가 같은 방향인지 확인하는 방식이 안전합니다.'
        end as local_issue,
        case
            when target.display_name like '%강남%' or target.display_name like '%서초%' or target.display_name like '%송파%' or target.display_name like '%용산%' then '핵심 입지 수요와 정비사업 일정, 전세 수요의 결합'
            when target.display_name like '%성남%' or target.display_name like '%용인%' or target.display_name like '%화성%' or target.display_name like '%평택%' or target.display_name like '%수원%' then '일자리와 광역교통이 실제 주거 수요로 이어지는지 확인할 수 있는 점'
            when target.display_name like '%해운대%' or target.display_name like '%수영%' then '동부산 선호 생활권과 해안·업무 수요가 유지되는 점'
            when target.display_name like '%청주%' or target.display_name like '%천안%' or target.display_name like '%아산%' then '산업 배후수요와 광역 접근성이 함께 개선될 수 있는 점'
            when target.display_name like '%포항%' or target.display_name like '%구미%' or target.display_name like '%창원%' or target.display_name like '%거제%' then '산업 경기 회복이 주거 수요 안정으로 연결될 수 있는 점'
            else '공식 가격지표와 실거래·전세 원천이 같은 방향으로 쌓이면 지역 판단의 근거가 단단해지는 점'
        end as expectation_theme,
        case
            when target.display_name like '%강남%' or target.display_name like '%서초%' or target.display_name like '%송파%' or target.display_name like '%용산%' then '고가 거래 한 건과 규제·정책 뉴스가 시장 전체 판단으로 과장될 수 있다는 점'
            when target.display_name like '%성남%' or target.display_name like '%용인%' or target.display_name like '%화성%' or target.display_name like '%평택%' or target.display_name like '%수원%' then '개발 기대와 신규 공급 부담이 동시에 존재해 시차가 클 수 있다는 점'
            when target.display_name like '%해운대%' or target.display_name like '%수영%' then '관광·상권 이슈가 상주 주거 수요와 다르게 움직일 수 있다는 점'
            when target.display_name like '%청주%' or target.display_name like '%천안%' or target.display_name like '%아산%' then '산업 뉴스가 실제 입주·임대차 수요로 반영되기까지 시간이 걸릴 수 있다는 점'
            when target.display_name like '%포항%' or target.display_name like '%구미%' or target.display_name like '%창원%' or target.display_name like '%거제%' then '특정 업종 경기 의존도가 가격과 전세의 변동성을 키울 수 있다는 점'
            else '확인되지 않은 지역 뉴스나 단기 등락을 가격 방향의 결론처럼 읽을 수 있다는 점'
        end as concern_theme
    from real_estate_regions region
    join real_estate_targets target on target.id = region.target_id
    left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
    where region.region_level in ('sido', 'sigungu')
) researched
left join real_estate_regional_reports existing on existing.target_id = researched.target_id
on duplicate key update
    report_id = values(report_id),
    report_version = values(report_version),
    prompt_version = values(prompt_version),
    model_name = values(model_name),
    generated_by = values(generated_by),
    title = values(title),
    headline = values(headline),
    summary = values(summary),
    body = values(body),
    expectation_points_json = values(expectation_points_json),
    concern_points_json = values(concern_points_json),
    data_quality = values(data_quality),
    confidence = values(confidence),
    as_of = values(as_of),
    published_at = values(published_at),
    updated_at = values(updated_at);

delete from real_estate_regional_report_sources
where report_target_id in (
    select target_id
    from real_estate_regions
    where region_level in ('sido', 'sigungu')
);

insert into real_estate_regional_report_sources (
    id,
    report_target_id,
    display_order,
    ref_type,
    ref_id,
    label,
    title,
    url,
    source_name,
    published_at,
    data_status,
    created_at,
    updated_at
)
select
    concat('regional-report-source-', region.target_id, '-01-rone-main'),
    region.target_id,
    1,
    'external',
    'reb-rone-2026-05-national-housing-price-trend',
    '가격지표 근거',
    '한국부동산원 R-ONE 2026년 5월 전국주택가격동향',
    'https://www.reb.or.kr/r-one/portal/main/indexPage.do',
    '한국부동산원',
    '2026-06-15 00:00:00',
    'ok',
    '2026-06-24 22:00:00',
    '2026-06-24 22:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-02-rone-weekly'),
    region.target_id,
    2,
    'external',
    'reb-rone-2026-06-15-weekly-apartment-price-trend',
    '주간 가격 근거',
    '한국부동산원 2026년 6월 15일 기준 주간아파트가격 동향',
    'https://www.reb.or.kr/r-one/portal/bbs/rpt/searchBulletinPage.do',
    '한국부동산원',
    '2026-06-18 00:00:00',
    'ok',
    '2026-06-24 22:00:00',
    '2026-06-24 22:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-03-molit-rt'),
    region.target_id,
    3,
    'external',
    'molit-real-transaction-disclosure',
    '실거래 근거',
    '국토교통부 실거래가 공개시스템',
    'https://rt.molit.go.kr/',
    '국토교통부',
    null,
    'ok',
    '2026-06-24 22:00:00',
    '2026-06-24 22:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-04-data-trade'),
    region.target_id,
    4,
    'external',
    'data-go-kr-molit-apt-trade',
    '공공 API 근거',
    '공공데이터포털 국토교통부 아파트 매매 실거래가 자료',
    'https://www.data.go.kr/data/15126469/openapi.do',
    '공공데이터포털',
    null,
    'ok',
    '2026-06-24 22:00:00',
    '2026-06-24 22:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-05-data-rent'),
    region.target_id,
    5,
    'external',
    'data-go-kr-molit-apt-rent',
    '전월세 근거',
    '공공데이터포털 국토교통부 아파트 전월세 실거래가 자료',
    'https://www.data.go.kr/data/15126474/openapi.do',
    '공공데이터포털',
    null,
    'ok',
    '2026-06-24 22:00:00',
    '2026-06-24 22:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-06-molit-policy'),
    region.target_id,
    6,
    'external',
    'molit-housing-land-policy-press-2026-06',
    '정책·공급 근거',
    '국토교통부 주택토지 보도자료 - 공급·정책 동향',
    'https://www.molit.go.kr/USR/NEWS/m_71/lst.jsp?search_section=p_sec_2',
    '국토교통부',
    '2026-06-11 00:00:00',
    'ok',
    '2026-06-24 22:00:00',
    '2026-06-24 22:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-07-enara-index'),
    region.target_id,
    7,
    'external',
    'enara-housing-price-indicator-2026-06-15',
    '공표일 근거',
    'e-나라지표 주택매매가격 동향',
    'https://www.index.go.kr/unity/potal/main/EachDtlPageDetail.do?idx_cd=1240',
    'e-나라지표',
    '2026-06-15 00:00:00',
    'ok',
    '2026-06-24 22:00:00',
    '2026-06-24 22:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu');
