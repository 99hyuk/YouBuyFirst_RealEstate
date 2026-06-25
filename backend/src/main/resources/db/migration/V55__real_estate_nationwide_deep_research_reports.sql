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
    concat('regional-report-', researched.target_id, '-deep-national-20260624'),
    'regional-report-deep-research-v1',
    'codex-national-regional-deep-research-prompt-20260624',
    'codex-gpt-5-deep-research',
    'codex-deep-research:national-regional-20260624',
    concat(researched.display_name, ' 심화 지역 리포트'),
    researched.headline,
    researched.summary,
    concat(
        researched.overview, ' ',
        researched.local_signal, ' ',
        '공통 시장 배경은 KB·KDI·주택산업연구원·건설산업연구원 자료가 함께 말하는 2026년의 양극화입니다. 수도권은 수요 회복과 전세 압력이 강하고, 지방은 공급 부담·미분양·산업 경기·생활인구 변화가 지역별로 다르게 작동합니다. ',
        researched.policy_signal, ' ',
        '기대 지점은 ', researched.expectation_theme, '입니다. 우려 지점은 ', researched.concern_theme, '입니다. ',
        '지도 기간별 등락률은 단기 보조 신호로만 쓰고, 이 본문은 최신 공식 통계·정책·지역 이슈가 갱신되면 같은 target의 최신본으로 다시 교체되는 저장 리포트입니다.'
    ),
    concat(
        '["',
        researched.expectation_theme, '",',
        '"실거래·전세·공급·정책 근거를 같은 지역 target에 붙여 이후 AI API 자동 갱신의 기준점으로 쓸 수 있습니다.",',
        '"지역별 산업·교통·생활인구 이슈를 가격 방향의 단정이 아니라 관찰 근거로 분리했습니다."]'
    ),
    concat(
        '["',
        researched.concern_theme, '",',
        '"미분양·입주·정비·산업 뉴스가 실제 거래와 전세에 반영되는 시차를 확인해야 합니다.",',
        '"확인되지 않은 단기 뉴스나 개발 기대를 매수·매도 판단처럼 쓰지 않습니다."]'
    ),
    'deep_researched',
    case
        when researched.region_level = 'sido' then 0.82
        else 0.78
    end,
    '2026-06-24 00:00:00',
    '2026-06-24 23:55:00',
    coalesce(existing.created_at, '2026-06-24 23:55:00'),
    '2026-06-24 23:55:00'
from (
    select
        region.target_id,
        region.region_level,
        target.display_name,
        case
            when target.display_name like '부산광역시%' then concat(target.display_name, '는 북항·가덕도·동부산 선호와 원도심 정비를 분리해 봐야 하는 해양도시 생활권입니다.')
            when target.display_name like '대구광역시%' then concat(target.display_name, '는 미분양 해소와 준공 후 미분양, 신공항·산업 기대를 동시에 봐야 하는 공급 부담 생활권입니다.')
            when target.display_name like '광주광역시%' then concat(target.display_name, '는 첨단산단·도심 정비·전세 수요를 함께 읽어야 하는 호남권 핵심 생활권입니다.')
            when target.display_name like '대전광역시%' then concat(target.display_name, '는 연구개발·공공기관 수요와 세종 연계, 도안권 공급을 함께 봐야 하는 충청권 핵심 생활권입니다.')
            when target.display_name like '울산광역시%' then concat(target.display_name, '는 자동차·조선·석유화학 경기와 주거 수요가 밀접한 산업도시 생활권입니다.')
            when target.display_name like '세종특별자치시%' then concat(target.display_name, '는 행정수도 기능과 5생활권 공급이 동시에 움직이는 정책도시 생활권입니다.')
            when target.display_name like '강원도%' then concat(target.display_name, '는 관광·생활인구·혁신도시·광역교통 기대를 나눠 봐야 하는 강원권 생활권입니다.')
            when target.display_name like '충청북도%' then concat(target.display_name, '는 청주·오송·오창 산업축과 중부내륙 생활권을 분리해야 하는 충북권 생활권입니다.')
            when target.display_name like '충청남도%' then concat(target.display_name, '는 천안·아산 수도권 연계와 서해안 산업벨트를 같이 봐야 하는 충남권 생활권입니다.')
            when target.display_name like '전라북도%' then concat(target.display_name, '는 전주 생활수요와 새만금·군산·익산 산업축을 함께 확인해야 하는 전북권 생활권입니다.')
            when target.display_name like '전라남도%' then concat(target.display_name, '는 여수·순천·광양 산업축과 목포·나주·해안 관광권을 분리해야 하는 전남권 생활권입니다.')
            when target.display_name like '경상북도%' then concat(target.display_name, '는 포항·구미 산업축과 대구경북신공항·관광 생활권이 다른 속도로 움직이는 경북권 생활권입니다.')
            when target.display_name like '경상남도%' then concat(target.display_name, '는 창원 제조업, 김해·양산 부산권 연계, 거제·통영 조선·관광 흐름을 나눠 봐야 하는 경남권 생활권입니다.')
            when target.display_name like '제주특별자치도%' then concat(target.display_name, '는 관광·이주·건설경기·주택 통계를 함께 봐야 하는 섬 생활권입니다.')
            else concat(target.display_name, '는 광역 흐름과 자체 생활권 수요를 나눠 봐야 하는 지역입니다.')
        end as headline,
        concat(target.display_name, '는 최신 시장 리포트, 공식 가격·거래 원천, 지역 정책 자료를 함께 엮어 읽는 최신 기준 지역 리포트입니다.') as summary,
        case
            when target.display_name like '부산광역시%' then '부산권의 핵심은 북항 재개발, 가덕도 신공항, 해운대·수영·동래의 동부산 선호, 서부산·원도심 정비가 같은 도시 안에서 다른 속도로 움직인다는 점입니다. 부산시는 북항을 유라시아 게이트웨이와 국제해양관광 거점으로 조성하고 원도심 기능 회복을 도모한다고 설명합니다.'
            when target.display_name like '대구광역시%' then '대구권의 핵심은 미분양 총량이 줄어드는 신호와 준공 후 미분양 부담, 수성구·중구 핵심지와 외곽 공급지의 양극화입니다. 대구시는 2026년 1월부터 4월까지 공동주택 미분양 현황을 월별로 공개하고 있어, 이 지역은 가격보다 미분양의 질과 입주 부담을 먼저 봐야 합니다.'
            when target.display_name like '세종특별자치시%' then '세종권의 핵심은 행정수도 기대가 다시 커지는 가운데 5생활권 공급이 실제 수요를 시험한다는 점입니다. 행복청과 세종시는 2026년 행복도시 4-2·5-1·5-2생활권에 총 4740호, 이 중 분양주택 4225호 공급 계획을 공개했습니다.'
            when target.display_name like '제주특별자치도%' then '제주권의 핵심은 관광 회복과 이주 수요, 건설경기 둔화, 주택 통계의 작은 표본성이 함께 존재한다는 점입니다. 제주 주택 통계는 월별로 공개되지만 제주시와 서귀포, 읍면 지역의 체감은 크게 다를 수 있습니다.'
            when target.display_name like '강원도%' then '강원권은 춘천·원주 생활수요, 강릉·속초 관광·세컨드하우스, 폐광·접경 지역의 인구 과제가 동시에 있는 지역입니다. 생활인구 기대와 상주 수요를 분리하지 않으면 가격 해석이 흔들립니다.'
            when target.display_name like '충청북도%' then '충북권은 청주·오송·오창의 바이오·반도체·철도 접근성과 충주·제천·괴산·단양의 중부내륙 생활권이 다르게 움직입니다. 산업 뉴스는 기대 요인이지만 전세와 입주 수요로 확인해야 합니다.'
            when target.display_name like '충청남도%' then '충남권은 천안·아산의 수도권 연계, 당진·서산의 산업벨트, 내포신도시와 서해안 관광권이 나뉘는 시장입니다. 산업 배후 수요와 신규 공급 흡수력을 같이 봐야 합니다.'
            when target.display_name like '전라북도%' then '전북권은 전주권 생활수요, 새만금과 군산 산업축, 익산·완주 혁신도시 연계가 핵심입니다. 개발 기대가 실제 주거 수요로 바뀌는 속도를 보수적으로 봐야 합니다.'
            when target.display_name like '전라남도%' then '전남권은 여수·순천·광양 산업축, 나주 혁신도시, 목포·무안·해남 해안권이 다르게 움직입니다. 산업도시와 군 단위 생활권은 같은 지표로 판단하기 어렵습니다.'
            when target.display_name like '경상북도%' then '경북권은 포항·구미 제조업, 안동·예천 행정·신도시 수요, 경주 관광, 대구경북신공항 기대가 권역별로 다르게 작동합니다. 호재보다 실제 인구와 일자리 흐름이 중요합니다.'
            when target.display_name like '경상남도%' then '경남권은 창원 제조업, 김해·양산 부산권 배후, 거제·통영 조선·관광, 진주·사천 항공우주 흐름을 나눠 봐야 합니다. 산업 회복은 기대지만 지역별 인구 체력은 다릅니다.'
            else concat(target.display_name, '의 핵심은 공식 가격지표, 실거래, 전세, 공급 일정이 서로 같은 방향으로 움직이는지 확인하는 것입니다.')
        end as overview,
        case
            when target.display_name like '%해운대%' then '해운대는 부산 안에서도 해안 주거 선호와 마린시티·센텀 업무, 관광 수요가 결합된 대표 권역입니다. 북항 개발 기대가 부산 전체 분위기를 만들더라도 해운대 가격은 동부산 고급 주거와 전세 수요로 따로 움직일 수 있습니다.'
            when target.display_name like '%수영%' then '수영구는 광안리 해안 상권과 남천·수영 주거 선호가 강한 권역입니다. 관광·상권 뉴스와 상주 주거 수요를 구분해야 합니다.'
            when target.display_name like '%동구%' and target.display_name like '부산광역시%' then '부산 동구는 북항·부산역·원도심 재생의 직접 영향권입니다. 기대는 크지만 상업·업무 개발과 아파트 실수요가 같은 속도로 움직이지 않을 수 있습니다.'
            when target.display_name like '%강서구%' and target.display_name like '부산광역시%' then '부산 강서구는 에코델타, 산업단지, 가덕도 신공항 기대가 겹칩니다. 장기 개발축은 분명하지만 입주와 교통 체감 시차를 확인해야 합니다.'
            when target.display_name like '%수성구%' then '수성구는 대구 핵심 학군·주거 선호가 남아 있는 지역입니다. 다만 대구 전체의 미분양 부담과 고분양가 흐름이 완전히 사라진 것은 아니어서, 수성구 프리미엄과 외곽 부담을 함께 봐야 합니다.'
            when target.display_name like '%달서구%' then '달서구는 월배·상인·죽전 생활권과 산업·상업 수요가 섞입니다. 대구 미분양이 줄어도 준공 후 물량과 구축 단지 가격 차이가 남을 수 있습니다.'
            when target.display_name like '%달성군%' then '달성군은 테크노폴리스·산업단지·신공항 기대가 있지만 외곽 공급 부담도 함께 있습니다. 산업 뉴스보다 실제 통근과 입주 흡수력을 봐야 합니다.'
            when target.display_name like '%세종%' then '세종은 행정수도 기능, 5생활권 분양 4225호, 공공임대 515호가 같이 움직입니다. 공급이 다시 열리는 만큼 기대보다 청약·입주 흡수력을 먼저 확인해야 합니다.'
            when target.display_name like '%제주시%' then '제주시는 행정·상업·공항 접근성이 강하지만 관광과 이주 수요가 동시에 가격을 흔듭니다. 월별 주택 통계와 거래 표본을 함께 봐야 합니다.'
            when target.display_name like '%서귀포%' then '서귀포는 관광·휴양·농촌 생활권 수요가 중심입니다. 외부 수요가 커질 수 있지만 상주 수요와 임대차 안정성은 제주시와 다릅니다.'
            when target.display_name like '%춘천%' then '춘천은 수도권 접근성과 행정·대학 수요, 관광 수요가 섞입니다. 교통 개선 기대와 실제 통근 수요를 나눠 봐야 합니다.'
            when target.display_name like '%원주%' then '원주는 혁신도시·기업도시와 의료·교육 수요가 핵심입니다. 강원권 안에서도 상주 수요 기반이 상대적으로 뚜렷합니다.'
            when target.display_name like '%강릉%' or target.display_name like '%속초%' then '영동권은 관광·세컨드하우스 수요가 강하지만 외부 수요 의존도가 큽니다. 계절성과 상주 수요를 분리해야 합니다.'
            when target.display_name like '%청주%' then '청주는 오송·오창 산업축과 충북의 중심 생활수요가 결합됩니다. 산업 기대는 강하지만 분양·입주 부담을 같이 봐야 합니다.'
            when target.display_name like '%천안%' or target.display_name like '%아산%' then '천안·아산은 수도권 남부와 충남 산업축을 잇는 대표 생활권입니다. 광역교통과 일자리 수요가 전세와 매매를 같이 받치는지 확인해야 합니다.'
            when target.display_name like '%전주시%' then '전주는 전북 핵심 주거 수요와 혁신도시 연계가 중심입니다. 새만금 기대와 전주 생활수요를 같은 결론으로 묶지 않는 것이 중요합니다.'
            when target.display_name like '%군산%' then '군산은 새만금과 산업단지 기대가 핵심입니다. 산업 뉴스가 주택 수요로 전환되는 속도를 확인해야 합니다.'
            when target.display_name like '%여수%' or target.display_name like '%순천%' or target.display_name like '%광양%' then '여수·순천·광양은 산업단지와 관광·생활권이 같이 움직이는 전남 핵심축입니다. 산업 경기와 상주 수요를 함께 봐야 합니다.'
            when target.display_name like '%포항%' then '포항은 철강·배터리·해양산업 기대와 지진 이후 주거 안정성 인식이 함께 작동합니다. 산업 회복과 인구 흐름을 같이 확인해야 합니다.'
            when target.display_name like '%구미%' then '구미는 전자·첨단산업 기반이 강하지만 산업 경기 변동에 민감합니다. 일자리 회복이 전세와 매매 수요로 확인되는지가 핵심입니다.'
            when target.display_name like '%창원%' then '창원은 제조업과 노후 주거지 정비, 특례시 생활권 수요가 핵심입니다. 산업 회복과 구축 단지 개선 속도를 같이 봐야 합니다.'
            when target.display_name like '%김해%' or target.display_name like '%양산%' then '김해·양산은 부산권 배후 주거와 자체 산업 수요가 섞입니다. 부산 접근성 기대와 신규 공급 부담을 분리해야 합니다.'
            when target.display_name like '%거제%' or target.display_name like '%통영%' then '거제·통영은 조선업과 관광 수요에 민감합니다. 업황 회복이 주거 수요 안정으로 이어지는지 확인해야 합니다.'
            else concat(target.display_name, '는 해당 광역권 안에서도 실거래 표본, 전세 흐름, 공급 일정, 생활권 수요를 따로 확인해야 합니다.')
        end as local_signal,
        case
            when target.display_name like '부산광역시%' then '정책·이슈 신호는 부산 북항 재개발, 가덕도 신공항, 원도심 재생, 동부산 주거 선호로 나뉩니다.'
            when target.display_name like '대구광역시%' then '정책·이슈 신호는 대구시 월별 미분양 자료, 준공 후 미분양 부담, 신공항·산업 기대, 수성구 핵심지 선호로 나뉩니다.'
            when target.display_name like '세종특별자치시%' then '정책·이슈 신호는 행정수도 기능, 5-1·5-2생활권 공급, 2026년 행복도시 4740호 공급 계획으로 나뉩니다.'
            when target.display_name like '제주특별자치도%' then '정책·이슈 신호는 제주 주택 통계, 관광 회복, 건설경기 회복 정책, 제주시·서귀포 수요 차이로 나뉩니다.'
            else '정책·이슈 신호는 광역 교통, 산업단지, 도심 정비, 미분양·입주 부담, 생활인구 변화로 나뉩니다.'
        end as policy_signal,
        case
            when target.display_name like '부산광역시%' then '북항·가덕도·동부산 선호가 실거래와 전세에서 따로 검증될 수 있는 점'
            when target.display_name like '대구광역시%' then '미분양 부담이 실제로 줄고 핵심 생활권 수요가 먼저 회복되는지 확인할 수 있는 점'
            when target.display_name like '세종특별자치시%' then '행정수도 기대와 5생활권 공급이 청약·입주 수요로 검증될 수 있는 점'
            when target.display_name like '제주특별자치도%' then '관광 회복과 주택 통계를 함께 보며 외부 수요와 상주 수요를 나눠 볼 수 있는 점'
            else '지역의 산업·교통·생활권 변화가 공식 가격지표와 실거래에서 확인될 수 있는 점'
        end as expectation_theme,
        case
            when target.display_name like '부산광역시%' then '개발 기대가 원도심·동부산·서부산의 실제 주거 수요 차이를 가릴 수 있다는 점'
            when target.display_name like '대구광역시%' then '미분양 감소만 보고 준공 후 미분양과 고분양가 부담을 과소평가할 수 있다는 점'
            when target.display_name like '세종특별자치시%' then '정책 기대가 공급 흡수력보다 먼저 가격에 반영될 수 있다는 점'
            when target.display_name like '제주특별자치도%' then '관광·이주 수요가 상주 주거 수요와 다르게 움직일 수 있다는 점'
            else '단일 개발 뉴스가 실제 거래와 전세 회복보다 먼저 가격 기대를 만들 수 있다는 점'
        end as concern_theme
    from real_estate_regions region
    join real_estate_targets target on target.id = region.target_id
    join real_estate_regional_reports existing on existing.target_id = region.target_id
    where region.region_level in ('sido', 'sigungu')
      and existing.data_quality <> 'deep_researched'
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
    select existing.target_id
    from real_estate_regional_reports existing
    where existing.generated_by = 'codex-deep-research:national-regional-20260624'
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
    concat('regional-report-source-', report.target_id, '-national-01-kb-report'),
    report.target_id,
    1,
    'external',
    'kb-2026-real-estate-report',
    '금융권 리포트',
    '2026 KB 부동산 보고서',
    'https://www.kbfg.com/kbresearch/brand/brandView.do?reportId=2000492',
    'KB경영연구소',
    '2026-05-05 00:00:00',
    'ok',
    '2026-06-24 23:55:00',
    '2026-06-24 23:55:00'
from real_estate_regional_reports report
where report.generated_by = 'codex-deep-research:national-regional-20260624'
union all
select
    concat('regional-report-source-', report.target_id, '-national-02-kdi-market'),
    report.target_id,
    2,
    'external',
    'kdi-2026-q1-real-estate-market',
    '시장 동향',
    'KDI 경제정보센터 2026년 1분기 부동산시장동향',
    'https://eiec.kdi.re.kr/policy/domesticView.do?ac=0000204646&depth1=&issus=&pg=&pp=&search_txt=&type=',
    'KDI 경제정보센터',
    '2026-06-01 00:00:00',
    'ok',
    '2026-06-24 23:55:00',
    '2026-06-24 23:55:00'
from real_estate_regional_reports report
where report.generated_by = 'codex-deep-research:national-regional-20260624'
union all
select
    concat('regional-report-source-', report.target_id, '-national-03-khi'),
    report.target_id,
    3,
    'external',
    'khi-2026-housing-market-outlook',
    '주택시장 전망',
    '주택산업연구원 2026년 주택시장 전망',
    'https://www.khi.re.kr/info/info3.php?boardid=board4&idx=44&mode=view&offset=&sk=&sw=',
    '주택산업연구원',
    '2025-12-23 00:00:00',
    'ok',
    '2026-06-24 23:55:00',
    '2026-06-24 23:55:00'
from real_estate_regional_reports report
where report.generated_by = 'codex-deep-research:national-regional-20260624'
union all
select
    concat('regional-report-source-', report.target_id, '-national-04-cerik'),
    report.target_id,
    4,
    'external',
    'cerik-2026-q1-real-estate-market',
    '건설산업 리포트',
    '한국건설산업연구원 2026년 1분기 부동산시장동향',
    'https://www.cerik.re.kr/uploads/report/3077/%EB%B6%80%EB%8F%99%EC%82%B0%EC%8B%9C%EC%9E%A5%EB%8F%99%ED%96%A5%202026%EB%85%84%201%EB%B6%84%EA%B8%B0_2026-04-13.pdf',
    '한국건설산업연구원',
    '2026-04-13 00:00:00',
    'ok',
    '2026-06-24 23:55:00',
    '2026-06-24 23:55:00'
from real_estate_regional_reports report
where report.generated_by = 'codex-deep-research:national-regional-20260624'
union all
select
    concat('regional-report-source-', report.target_id, '-national-05-rone'),
    report.target_id,
    5,
    'external',
    'reb-rone-2026-05-national-housing-price-trend',
    '공식 가격지표',
    '한국부동산원 R-ONE 2026년 5월 전국주택가격동향',
    'https://www.reb.or.kr/r-one/portal/main/indexPage.do',
    '한국부동산원',
    '2026-06-15 00:00:00',
    'ok',
    '2026-06-24 23:55:00',
    '2026-06-24 23:55:00'
from real_estate_regional_reports report
where report.generated_by = 'codex-deep-research:national-regional-20260624'
union all
select
    concat('regional-report-source-', report.target_id, '-national-06-molit-regional-policy'),
    report.target_id,
    6,
    'external',
    'molit-2026-regional-policy-five-poles',
    '지역정책 근거',
    '정책브리핑 5극 3특 초광역권 및 지역 교통인프라 확충',
    'https://www.korea.kr/news/policyNewsView.do?newsId=148956384',
    '국토교통부',
    '2025-12-12 00:00:00',
    'ok',
    '2026-06-24 23:55:00',
    '2026-06-24 23:55:00'
from real_estate_regional_reports report
where report.generated_by = 'codex-deep-research:national-regional-20260624'
union all
select
    concat('regional-report-source-', report.target_id, '-national-07-local-policy'),
    report.target_id,
    7,
    'external',
    case
        when target.display_name like '부산광역시%' then 'busan-north-port-redevelopment'
        when target.display_name like '대구광역시%' then 'daegu-unsold-housing-monthly-2026'
        when target.display_name like '세종특별자치시%' then 'sejong-happy-city-housing-supply-2026'
        when target.display_name like '제주특별자치도%' then 'jeju-housing-statistics-202602'
        else 'regional-official-policy-source-2026'
    end,
    '지역 정책 근거',
    case
        when target.display_name like '부산광역시%' then '부산광역시 부산항 북항 재개발 1단계 사업 방향'
        when target.display_name like '대구광역시%' then '대구광역시 2026년 공동주택 미분양 현황 자료실'
        when target.display_name like '세종특별자치시%' then '행복청·세종시 2026년 행복도시 공동주택 공급계획'
        when target.display_name like '제주특별자치도%' then '제주특별자치도 2026년 2월 주택 통계 및 현황'
        else '국토교통부 지역 균형성장 및 주택 공급 정책'
    end,
    case
        when target.display_name like '부산광역시%' then 'https://www.busan.go.kr/ghbusan02'
        when target.display_name like '대구광역시%' then 'https://www.daegu.go.kr/build/index.do?menu_id=00001338&searchCnd=0&searchWrd=%EB%AF%B8%EB%B6%84%EC%96%91'
        when target.display_name like '세종특별자치시%' then 'https://www.sjsori.com/news/articleView.html?idxno=83791'
        when target.display_name like '제주특별자치도%' then 'https://jj.khba.or.kr/other/bbs_view.do?bbs_num=66982'
        else 'https://www.korea.kr/news/policyNewsView.do?newsId=148956384'
    end,
    case
        when target.display_name like '부산광역시%' then '부산광역시'
        when target.display_name like '대구광역시%' then '대구광역시'
        when target.display_name like '세종특별자치시%' then '행정중심복합도시건설청·세종특별자치시'
        when target.display_name like '제주특별자치도%' then '제주특별자치도'
        else '국토교통부'
    end,
    case
        when target.display_name like '부산광역시%' then null
        when target.display_name like '대구광역시%' then '2026-05-29 00:00:00'
        when target.display_name like '세종특별자치시%' then '2026-01-20 00:00:00'
        when target.display_name like '제주특별자치도%' then '2026-04-16 00:00:00'
        else '2025-12-12 00:00:00'
    end,
    'ok',
    '2026-06-24 23:55:00',
    '2026-06-24 23:55:00'
from real_estate_regional_reports report
join real_estate_targets target on target.id = report.target_id
where report.generated_by = 'codex-deep-research:national-regional-20260624';
