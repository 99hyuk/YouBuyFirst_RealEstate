create table real_estate_regional_reports (
    target_id varchar(120) not null,
    report_id varchar(160) not null,
    report_version varchar(80) not null,
    prompt_version varchar(80),
    model_name varchar(80),
    generated_by varchar(80) not null,
    title varchar(200) not null,
    headline varchar(300) not null,
    summary text not null,
    body text not null,
    expectation_points_json text not null,
    concern_points_json text not null,
    data_quality varchar(30) not null,
    confidence double,
    as_of datetime(6) not null,
    published_at datetime(6) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (target_id),
    constraint uk_real_estate_regional_reports_report_id unique (report_id),
    constraint fk_real_estate_regional_reports_target foreign key (target_id) references real_estate_targets (id)
);

create table real_estate_regional_report_sources (
    id varchar(160) not null,
    report_target_id varchar(120) not null,
    display_order int not null,
    ref_type varchar(60) not null,
    ref_id varchar(160),
    label varchar(120) not null,
    title varchar(240) not null,
    url text,
    source_name varchar(160),
    published_at datetime(6),
    data_status varchar(30) not null,
    created_at datetime(6) not null,
    updated_at datetime(6) not null,
    primary key (id),
    constraint fk_real_estate_regional_report_sources_report
        foreign key (report_target_id) references real_estate_regional_reports (target_id)
);

create index idx_real_estate_regional_reports_as_of on real_estate_regional_reports (as_of);
create index idx_real_estate_regional_report_sources_report on real_estate_regional_report_sources (report_target_id, display_order);
create index idx_real_estate_regional_report_sources_ref on real_estate_regional_report_sources (ref_type, ref_id);

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
    region.target_id,
    concat('regional-report-', region.target_id, '-latest'),
    'regional-report-seed-v1',
    'regional-report-template-v1',
    null,
    'seed:regional-report-v1',
    concat(target.display_name, ' 최신 지역 리포트'),
    concat(target.display_name, '은 공식 가격지표, 실거래·전세, 공급·정책 근거를 한 번에 확인해야 하는 관찰 지역입니다.'),
    concat(target.display_name, ' 최신 리포트는 지도 기간 선택과 별도로 저장되는 최신 기준 브리핑입니다. 공식 가격지표, 실거래·전세 원천, 정책·공급 일정, 뉴스·리포트 근거가 같은 target_id로 연결되면 AI API가 이후 이 본문을 자동 갱신할 수 있습니다.'),
    concat(
        target.display_name,
        '은 단기 등락 하나로 판단하기보다 공식 가격지표와 실거래·전세 흐름, 공급·정책 일정, 최근 뉴스·리포트 근거를 함께 봐야 하는 지역입니다. ',
        '기대 지점은 데이터가 같은 지역 target에 쌓이면 가격 흐름과 이슈 맥락을 빠르게 비교할 수 있다는 점입니다. ',
        '우려 지점은 승인되지 않은 뉴스 후보나 부족한 실거래 표본이 결론처럼 읽힐 수 있다는 점입니다. ',
        '지도 기간별 등락은 보조 수치로만 사용하고, 이 종합 리포트는 최신 근거 묶음이 갱신될 때만 새로 적재합니다.'
    ),
    '["공식 가격지표와 지도 계층이 같은 target_id로 연결됩니다.","뉴스·리포트·정책 근거가 들어오면 최신 리포트를 자동 갱신할 수 있습니다.","시장 사실과 근거 링크를 분리 저장해 AI 재작성에 바로 사용할 수 있습니다."]',
    '["지역별 뉴스·정책 원문은 후보와 승인 상태를 분리 확인해야 합니다.","실거래·전세·공급 데이터가 부족한 지역은 판단을 보수적으로 유지합니다.","지도 기간별 등락은 본문 판단을 바꾸지 않고 보조 수치로만 봅니다."]',
    'partial',
    0.45,
    '2026-06-24 00:00:00',
    '2026-06-24 00:00:00',
    '2026-06-24 00:00:00',
    '2026-06-24 00:00:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
where region.region_level in ('sido', 'sigungu');

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
    concat('regional-report-source-', region.target_id, '-molit-rt'),
    region.target_id,
    1,
    'external',
    'molit-real-transaction-disclosure',
    '실거래 근거',
    '국토교통부 실거래가 공개시스템',
    'https://rt.molit.go.kr/',
    '국토교통부',
    null,
    'ok',
    '2026-06-24 00:00:00',
    '2026-06-24 00:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-reb-rone'),
    region.target_id,
    2,
    'external',
    'reb-rone-price-statistics',
    '가격지표 근거',
    '한국부동산원 R-ONE 부동산통계정보시스템',
    'https://www.reb.or.kr/r-one/portal/main/indexPage.do',
    '한국부동산원',
    null,
    'ok',
    '2026-06-24 00:00:00',
    '2026-06-24 00:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu')
union all
select
    concat('regional-report-source-', region.target_id, '-data-go-kr-apt-trade'),
    region.target_id,
    3,
    'external',
    'data-go-kr-molit-apt-trade',
    '공공 API 근거',
    '공공데이터포털 국토교통부 아파트 매매 실거래가 자료',
    'https://www.data.go.kr/data/15126469/openapi.do',
    '공공데이터포털',
    null,
    'ok',
    '2026-06-24 00:00:00',
    '2026-06-24 00:00:00'
from real_estate_regions region
where region.region_level in ('sido', 'sigungu');
