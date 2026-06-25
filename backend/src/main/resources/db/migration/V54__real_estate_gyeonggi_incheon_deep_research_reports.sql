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
    concat('regional-report-', researched.target_id, '-deep-capital-20260624'),
    'regional-report-deep-research-v1',
    'codex-gyeonggi-incheon-deep-research-prompt-20260624',
    'codex-gpt-5-deep-research',
    'codex-deep-research:capital-west-south-20260624',
    concat(researched.display_name, ' 심화 지역 리포트'),
    researched.headline,
    researched.summary,
    concat(
        researched.overview, ' ',
        researched.local_signal, ' ',
        '공통 시장 배경은 수도권 전세 강세, 공급 인허가 부진, 대출 규제 안의 선별 수요입니다. KB·KDI·건설산업연구원 자료는 2026년 주택시장을 서울·수도권 중심의 차별화, 전세와 월세화, 공급 지연으로 설명합니다. ',
        researched.policy_signal, ' ',
        '기대 지점은 ', researched.expectation_theme, '입니다. 우려 지점은 ', researched.concern_theme, '입니다. ',
        '따라서 이 리포트는 단기 가격 방향을 권하는 글이 아니라, 실거래·전세·공급·정책 일정이 같은 방향으로 맞물리는지 판단하기 위한 최신 기준 칼럼형 관찰문입니다.'
    ),
    concat(
        '["',
        researched.expectation_theme, '",',
        '"공식 실거래와 전세 원천을 같은 target 기준으로 붙이면 개발 뉴스와 실제 체감 수요를 분리해 볼 수 있습니다.",',
        '"권역별 정책·공급 근거가 갱신되면 AI API가 같은 target의 최신 리포트를 다시 덮어쓸 수 있습니다."]'
    ),
    concat(
        '["',
        researched.concern_theme, '",',
        '"산업 뉴스나 교통 호재가 가격 방향을 바로 보장한다고 쓰지 않고, 착공·입주·전세 흡수 시차를 확인해야 합니다.",',
        '"지도 기간별 등락률은 본문을 바꾸는 근거가 아니라 단기 보조 신호로만 다룹니다."]'
    ),
    'deep_researched',
    case
        when researched.region_level = 'sido' then 0.84
        else 0.8
    end,
    '2026-06-24 00:00:00',
    '2026-06-24 23:45:00',
    coalesce(existing.created_at, '2026-06-24 23:45:00'),
    '2026-06-24 23:45:00'
from (
    select
        region.target_id,
        region.region_level,
        target.display_name,
        case
            when target.display_name = '경기도' then '경기도는 1기 신도시 정비, 3기 신도시 공급, 용인 반도체 축이 동시에 작동하는 수도권 핵심 관찰 권역입니다.'
            when target.display_name = '인천광역시' then '인천은 계양·검단 공급, 송도·청라·영종의 개발축, 원도심 정비 격차를 함께 읽어야 하는 서부 수도권 관찰 권역입니다.'
            when target.display_name like '경기도%' then concat(target.display_name, '는 경기권 안에서도 서울 접근성, 일자리 축, 신도시·정비 일정이 따로 움직이는 생활권입니다.')
            else concat(target.display_name, '는 인천권 안에서도 신도시 공급과 원도심 정비, 공항·항만·국제업무 수요를 분리해야 하는 생활권입니다.')
        end as headline,
        case
            when target.display_name = '경기도' then '경기도 전체 판단은 분당·일산·평촌·산본·중동 1기 신도시 정비, 남양주왕숙·하남교산·고양창릉·부천대장 3기 신도시, 용인 반도체와 경기남부 산업축을 한 화면에 놓아야 합니다.'
            when target.display_name = '인천광역시' then '인천 전체 판단은 인천계양 3기 신도시, 검단·청라·송도·영종의 신도시 축, 미추홀·부평·동구 원도심 정비 격차를 함께 봐야 합니다.'
            else concat(target.display_name, '는 광역 평균보다 생활권별 교통·산업·공급 시차가 더 크게 작동합니다.')
        end as summary,
        case
            when target.display_name = '경기도' then '경기도 전체 리포트의 결론은 한 방향의 경기 회복이 아니라 권역별 속도 차입니다. 2026년 수도권 공공택지 5만호 이상 착공과 3기 신도시 입주 시작은 남양주·하남·고양·부천·과천·광명 같은 공급 권역을 움직이고, 경기도가 분당·일산 기본계획 승인으로 1기 신도시 5곳 정비기본계획 수립을 마무리한 것은 노후계획도시 가격 기대를 다시 열었습니다.'
            when target.display_name = '인천광역시' then '인천 전체 리포트의 결론은 신도시 공급과 원도심 격차입니다. 계양테크노밸리는 2차 수도권 주택공급 계획상 약 335만㎡, 17천호 규모로 잡혀 있고, 국토교통부는 인천계양 A2·A3 1106호 공공분양과 2026년 입주 목표를 제시했습니다. 하지만 송도·청라·검단·영종의 기대와 미추홀·동구·부평 원도심 체감은 같은 속도로 움직이지 않습니다.'
            else concat(target.display_name, ' 리포트의 출발점은 광역 평균보다 생활권의 실제 쓰임입니다. 수도권은 전세 강세와 월세화, 공급 지연, 광역교통 기대가 동시에 작동하지만 이 힘이 모든 시·구에 같은 방향으로 번지지는 않습니다.')
        end as overview,
        case
            when target.display_name like '%용인시 처인구%' then '처인구는 용인 첨단시스템반도체 국가산단과 원삼·이동 일대 산업 기대가 직접 닿는 곳입니다. 산업 뉴스가 가장 선명하지만 주거 판단은 직주근접 수요, 도로·철도 접근성, 택지·입주 시차를 분리해야 합니다. 첨단시스템반도체 국가산단은 기대 지점이지만, 착공과 고용이 실제 임대차 수요로 연결되는 시간표를 확인해야 합니다.'
            when target.display_name like '%용인시 기흥구%' then '기흥구는 플랫폼시티·분당선·경부축 접근성과 반도체 배후 수요가 겹칩니다. 경기남부 산업축을 주거 수요로 연결하기 쉬운 곳이지만, 이미 선호가 반영된 단지와 노후 단지의 체감은 다릅니다.'
            when target.display_name like '%용인시 수지구%' then '수지구는 분당·판교 대체 주거지 성격과 신분당선 접근성이 핵심입니다. 용인 반도체 뉴스가 광역 기대를 키우더라도 수지는 산업단지 직접 배후라기보다 강남·판교 접근 주거지로 읽어야 합니다.'
            when target.display_name like '%성남시 분당구%' then '분당구는 1기 신도시 정비 기대와 판교 일자리 수요가 결합된 대표 지역입니다. 기본계획 승인 이후 기대는 커졌지만, 선도지구와 후속 단지의 사업성·이주·분담금 차이가 가격을 갈라놓을 수 있습니다.'
            when target.display_name like '%성남시 수정구%' then '수정구는 위례·판교·강남 접근성과 원도심 정비가 함께 보이는 지역입니다. 분당 재건축 기대와 같은 결론으로 묶기보다, 신흥·태평·위례 생활권의 수요 성격을 나눠 봐야 합니다.'
            when target.display_name like '%성남시 중원구%' then '중원구는 성남 원도심 정비와 산업·업무 접근성이 핵심입니다. 신축 공급 기대보다 재개발 단계, 전세 흡수, 생활 인프라 개선을 먼저 확인해야 합니다.'
            when target.display_name like '%수원시 영통구%' then '영통구는 광교·영통·망포 축과 삼성디지털시티 배후 수요가 강합니다. 경기남부 일자리 축의 방어력은 기대 지점이지만, 준신축과 구축 단지 사이 가격 차이가 큽니다.'
            when target.display_name like '%수원시 팔달구%' then '팔달구는 수원역·매교·화서 등 원도심 정비와 광역교통이 핵심입니다. 재개발 입주 이후 전세 흡수와 상권 회복을 함께 봐야 합니다.'
            when target.display_name like '%수원시 장안구%' then '장안구는 북수원 생활권과 GTX-C 기대, 노후 주거지 개선 이슈가 맞물립니다. 교통 기대는 장기 변수이고 단지별 연식과 학교·상권 접근성이 체감을 가릅니다.'
            when target.display_name like '%수원시 권선구%' then '권선구는 서수원 개발과 산업·물류 접근성이 주요 변수입니다. 신규 택지와 기존 구축 주거지의 가격 논리가 달라 평균 지표를 그대로 쓰기 어렵습니다.'
            when target.display_name like '%고양시%' then '고양은 일산 1기 신도시 정비와 고양창릉 3기 신도시가 동시에 존재합니다. 일산동·서구는 노후계획도시 정비 단계가 핵심이고, 덕양구는 창릉 공급과 서울 서북권 접근성을 따로 봐야 합니다.'
            when target.display_name like '%안양시 동안구%' then '동안구는 평촌 1기 신도시 정비 기대와 범계·평촌 학원가 수요가 결합됩니다. 사업 단계가 빨라질수록 기대는 커지지만 이주와 전세 부담도 같이 봐야 합니다.'
            when target.display_name like '%안양시 만안구%' then '만안구는 안양 원도심 정비와 관악·광명·군포 접근성이 핵심입니다. 평촌 기대를 그대로 가져오기보다 정비구역별 사업성과 역세권 생활권을 따로 봐야 합니다.'
            when target.display_name like '%군포시%' then '군포는 산본 1기 신도시 선도지구 특별정비구역 지정 흐름이 가장 직접적인 이슈입니다. 경기도는 산본 선도지구를 시작으로 노후계획도시 정비가 본격화됐다고 설명하지만, 실제 주거 판단은 분담금·이주·통합심의 속도에 달려 있습니다.'
            when target.display_name like '%부천시%' then '부천은 중동 1기 신도시 정비와 부천대장 3기 신도시 공급을 같이 봐야 합니다. 부천대장은 서울 서부와 김포공항·마곡 인접성이 강점이지만, 중동 1기 신도시는 노후 단지 정비의 시간표가 가격 기대를 가릅니다.'
            when target.display_name like '%남양주시%' then '남양주는 왕숙·왕숙2 3기 신도시와 다산·별내·진접 생활권이 겹칩니다. 왕숙은 대규모 공급과 자족 기능을 내세우지만 입주 전까지는 교통 체감과 기존 단지 전세 흐름을 분리해야 합니다.'
            when target.display_name like '%하남시%' then '하남은 교산 3기 신도시, 미사 신도시, 강동·송파 접근성이 핵심입니다. 공급 기대와 서울 접근 수요가 동시에 강하지만 교산의 실제 입주 시간표가 체감 가격을 좌우합니다.'
            when target.display_name like '%화성시%' then '화성은 동탄2, GTX-A, 삼성·반도체 배후 수요가 결합됩니다. 동탄은 자족도시 기대가 강하지만 대규모 입주와 광역교통 개통 시차가 전세와 매매를 다르게 흔들 수 있습니다.'
            when target.display_name like '%평택시%' then '평택은 삼성전자 평택캠퍼스, 고덕국제신도시, 항만·미군기지 수요가 함께 움직입니다. 산업 배후 수요는 뚜렷하지만 공급이 많아 전세 흡수력을 먼저 봐야 합니다.'
            when target.display_name like '%과천시%' then '과천은 준강남 입지와 재건축·지식정보타운 공급이 핵심입니다. 희소성과 서울 접근성은 강하지만 작은 표본의 신고가가 전체 시장 판단으로 과장될 수 있습니다.'
            when target.display_name like '%광명시%' then '광명은 광명시흥 공공주택지구, 철산·하안 재건축, 서울 서남권 접근성이 겹칩니다. 공급 기대와 구축 정비 기대가 동시에 있어 단기 가격보다 사업 단계별 검증이 중요합니다.'
            when target.display_name like '%김포시%' then '김포는 한강신도시, 서울 서부 접근성, 광역교통 개선 기대가 핵심입니다. 교통 호재는 기대 요인이지만 실제 통근 시간과 신규 공급 부담을 함께 확인해야 합니다.'
            when target.display_name like '%파주시%' then '파주는 운정신도시와 GTX-A 기대가 중심입니다. 서울 접근성이 개선될수록 관심은 커지지만 대규모 신도시 공급과 전세 흡수 속도를 분리해야 합니다.'
            when target.display_name like '%시흥시%' then '시흥은 배곧·은계·장현 신도시와 시화·반월 산업 배후 수요가 같이 움직입니다. 월곶판교선 기대와 산업 수요가 있지만 생활권별 가격 차이가 큽니다.'
            when target.display_name like '%안산시%' then '안산은 반월·시화 산업단지와 신안산선 기대, 노후 주거지 정비가 핵심입니다. 산업 회복과 교통 기대가 긍정적이나 구축 비중과 인구 흐름을 함께 봐야 합니다.'
            when target.display_name like '%이천시%' then '이천은 SK하이닉스와 물류·산업 수요가 주거 시장을 설명하는 핵심입니다. 산업 뉴스가 임대차 수요로 이어지는 힘은 있지만 외곽 신규 공급과 통근권 경쟁을 확인해야 합니다.'
            when target.display_name like '%오산시%' then '오산은 동탄·평택 사이의 가격대 접근성과 세교 공급이 핵심입니다. 경기남부 산업축의 중간 입지지만 자체 일자리보다 주변 도시 의존도가 크다는 점을 봐야 합니다.'
            when target.display_name like '%광주시%' then '광주는 판교·분당 배후 주거와 도로 접근성이 핵심입니다. 저밀도 주거와 신축 단지 수요가 있지만 대중교통 접근성과 난개발 체감을 함께 봐야 합니다.'
            when target.display_name like '%구리시%' then '구리는 서울 동북권 인접성과 갈매·토평 개발 기대가 핵심입니다. 작은 면적 안에서 공급·정비 뉴스가 가격에 빠르게 반영될 수 있어 표본 수를 봐야 합니다.'
            when target.display_name like '%의왕시%' then '의왕은 인덕원·청계·백운밸리와 GTX-C 기대가 주요 변수입니다. 과천·평촌 사이 입지 장점이 있지만 신규 단지와 구축 단지의 가격 논리가 다릅니다.'
            when target.display_name like '%의정부시%' then '의정부는 경기북부 행정·상업 중심성과 GTX-C 기대가 핵심입니다. 서울 북부 접근성은 장점이나 경기남부 산업축과 다른 수요 구조를 가진다는 점을 봐야 합니다.'
            when target.display_name like '%양주시%' then '양주는 덕정 GTX-C 기대와 옥정·회천 신도시 공급이 핵심입니다. 교통 개선 기대는 크지만 공급 물량이 전세와 매매 흡수 속도를 가를 수 있습니다.'
            when target.display_name like '%동두천시%' then '동두천은 경기북부 저가 주거지와 미군기지 이전 이후 도시재생 과제가 같이 놓입니다. 가격대는 접근 가능하지만 인구와 일자리 기반을 먼저 확인해야 합니다.'
            when target.display_name like '%포천시%' then '포천은 경기북부 산업·군사·관광 수요가 섞인 외곽 생활권입니다. 개발 기대보다 상주 인구와 교통 접근성 개선 여부가 주거 판단의 핵심입니다.'
            when target.display_name like '%연천군%' then '연천은 접경·관광·군 관련 수요가 중심인 저밀도 생활권입니다. 단기 거래 표본이 적어 한두 건의 가격을 시장 방향으로 읽지 않아야 합니다.'
            when target.display_name like '%가평군%' then '가평은 관광·세컨드하우스·전원주택 수요가 강한 지역입니다. 외부 수요가 가격을 흔들 수 있지만 상주 수요와 임대차 안정성은 따로 봐야 합니다.'
            when target.display_name like '%양평군%' then '양평은 전원주택·세컨드하우스·수도권 동부 접근성이 핵심입니다. 교통 개선 기대와 생활인구 수요가 있으나 실거주 편의와 의료·교육 접근성을 확인해야 합니다.'
            when target.display_name like '%여주시%' then '여주는 수도권 동남부 외곽의 물류·전원 주거 수요가 중심입니다. 가격대는 접근 가능하지만 거래 표본과 신규 공급을 함께 봐야 합니다.'
            when target.display_name like '%안성시%' then '안성은 평택·용인 산업축의 배후와 자체 물류·제조 수요가 섞입니다. 산업 뉴스는 기대 요인이지만 통근권 경쟁과 공급 흡수를 같이 봐야 합니다.'
            when target.display_name like '%인천광역시 계양구%' then '계양구는 계양테크노밸리 3기 신도시가 핵심입니다. 인천시 중장기 계획은 계양구 귤현·동양·박촌·병방·상야동 일원의 약 335만㎡, 17천호 계획을 제시했고, 국토교통부는 A2·A3 1106호 분양과 2026년 입주 목표를 공개했습니다.'
            when target.display_name like '%인천광역시 서구%' then '서구는 검단신도시와 청라, 루원·가정 원도심 재편이 한 화면에 있습니다. 검단 공급은 가격 안정 요인이 될 수 있지만 청라·검단·원도심의 수요 성격은 다릅니다.'
            when target.display_name like '%인천광역시 연수구%' then '연수구는 송도국제도시와 GTX-B 기대, 바이오·국제업무 수요가 핵심입니다. 고급 주거 수요는 강하지만 국제업무·상업 공실과 주거 가격을 같은 방향으로 단정하면 안 됩니다.'
            when target.display_name like '%인천광역시 중구%' then '중구는 영종·공항경제권과 인천 원도심이 함께 있는 이중 구조입니다. 공항·관광 회복은 기대 요인이지만 영종과 내륙 원도심의 전세·매매 흐름은 다르게 봐야 합니다.'
            when target.display_name like '%인천광역시 부평구%' then '부평구는 GTX-B 기대, 부평역 상권, 원도심 재개발이 핵심입니다. 서울 접근 개선 기대가 강하지만 구축 비중과 정비 단계가 체감을 나눕니다.'
            when target.display_name like '%인천광역시 남동구%' then '남동구는 구월2지구 기대, 남동산단 배후, 만수·간석 원도심 정비가 같이 놓입니다. 산업·행정 수요는 안정 요인이지만 노후 단지 개선 속도를 따로 봐야 합니다.'
            when target.display_name like '%인천광역시 미추홀구%' or target.display_name like '%인천광역시 남구%' then '미추홀구는 용현·학익, 주안·도화 원도심 정비가 중심입니다. 신도시보다 정비사업 단계와 전세 안정성이 더 중요한 권역입니다.'
            when target.display_name like '%인천광역시 동구%' then '동구는 항만·원도심·노후 주거지가 중심입니다. 대형 신도시 호재보다 도시재생, 생활SOC, 산업 배후 수요가 주거 체감을 좌우합니다.'
            when target.display_name like '%인천광역시 강화군%' then '강화군은 관광·전원주택·군 단위 생활권 수요가 핵심입니다. 인천 신도시 공급 논리와 분리해 상주 수요, 교통, 생활 인프라를 봐야 합니다.'
            when target.display_name like '%인천광역시 옹진군%' then '옹진군은 섬 지역 생활권과 관광·어업 수요가 중심입니다. 거래 표본이 적어 가격 데이터의 신뢰구간을 보수적으로 봐야 합니다.'
            else concat(target.display_name, '는 수도권 광역 흐름을 받지만, 실제 판단은 지역별 교통·일자리·공급 일정으로 좁혀야 합니다.')
        end as local_signal,
        case
            when target.display_name like '경기도%' or target.display_name = '경기도' then '정책 신호는 2026년 수도권 공공택지 5만호 이상 착공, 3기 신도시 입주 시작, 경기도 1기 신도시 정비기본계획 승인, 용인 반도체(첨단시스템반도체 국가산단) 축으로 나뉩니다.'
            else '정책 신호는 인천계양 3기 신도시의 17천호 계획, A2·A3 1106호 공공분양과 2026년 입주 목표, 검단·청라·송도 공급·개발축, 원도심 정비 속도 차이로 나뉩니다.'
        end as policy_signal,
        case
            when target.display_name like '%계양구%' then '계양테크노밸리 공급이 서울 서부권 수요와 인천 원도심 수요를 동시에 흡수할 수 있는 점'
            when target.display_name like '%처인구%' then '첨단시스템반도체 국가산단이 장기 일자리와 주거 수요의 근거가 될 수 있는 점'
            when target.display_name like '%부천시%' then '부천대장 3기 신도시와 중동 1기 신도시 정비를 함께 비교할 수 있는 점'
            when target.display_name like '%분당구%' or target.display_name like '%일산%' or target.display_name like '%동안구%' or target.display_name like '%군포시%' then '1기 신도시 정비가 실제 특별정비계획과 이주 계획으로 이어질 수 있는 점'
            when target.display_name like '%송도%' or target.display_name like '%연수구%' then '국제업무·바이오·GTX-B 기대가 주거 선호를 받칠 수 있는 점'
            else '교통·일자리·공급 근거가 실거래와 전세 데이터로 검증될 수 있는 점'
        end as expectation_theme,
        case
            when target.display_name like '%계양구%' then '입주 전 기대가 주변 구축 가격에 먼저 반영되고 공급 흡수 시차가 생길 수 있다는 점'
            when target.display_name like '%처인구%' then '산업 뉴스가 실제 고용·임대차 수요로 연결되기까지 시간이 걸릴 수 있다는 점'
            when target.display_name like '%부천시%' then '부천대장 공급 기대와 중동 1기 신도시 정비 기대가 서로 다른 시간표로 움직인다는 점'
            when target.display_name like '%분당구%' or target.display_name like '%일산%' or target.display_name like '%동안구%' or target.display_name like '%군포시%' then '정비 기대가 분담금·이주·사업시행인가 검증보다 먼저 가격에 반영될 수 있다는 점'
            when target.display_name like '%인천광역시%' then '신도시와 원도심의 수요 격차가 커 광역 평균이 체감을 가릴 수 있다는 점'
            else '개발 기대와 신규 공급 부담, 전세 흡수력이 서로 다른 시차로 움직일 수 있다는 점'
        end as concern_theme
    from real_estate_regions region
    join real_estate_targets target on target.id = region.target_id
    left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
    where region.region_level in ('sido', 'sigungu')
      and (
          target.display_name like '경기도%'
          or target.display_name like '인천광역시%'
          or parent_target.display_name in ('경기도', '인천광역시')
          or region.target_id in ('region-gyeonggi', 'region-41000', 'region-incheon', 'region-28000')
      )
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
    select region.target_id
    from real_estate_regions region
    join real_estate_targets target on target.id = region.target_id
    left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
    where region.region_level in ('sido', 'sigungu')
      and (
          target.display_name like '경기도%'
          or target.display_name like '인천광역시%'
          or parent_target.display_name in ('경기도', '인천광역시')
          or region.target_id in ('region-gyeonggi', 'region-41000', 'region-incheon', 'region-28000')
      )
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
    concat('regional-report-source-', region.target_id, '-capital-01-kb-report'),
    region.target_id,
    1,
    'external',
    'kb-2026-real-estate-report',
    '금융권 리포트',
    '2026 KB 부동산 보고서',
    'https://www.kbfg.com/kbresearch/brand/brandView.do?reportId=2000492',
    'KB경영연구소',
    '2026-05-05 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or target.display_name like '인천광역시%'
      or parent_target.display_name in ('경기도', '인천광역시')
      or region.target_id in ('region-gyeonggi', 'region-41000', 'region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-capital-02-kdi-market'),
    region.target_id,
    2,
    'external',
    'kdi-2026-q1-real-estate-market',
    '시장 동향',
    'KDI 경제정보센터 2026년 1분기 부동산시장동향',
    'https://eiec.kdi.re.kr/policy/domesticView.do?ac=0000204646&depth1=&issus=&pg=&pp=&search_txt=&type=',
    'KDI 경제정보센터',
    '2026-06-01 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or target.display_name like '인천광역시%'
      or parent_target.display_name in ('경기도', '인천광역시')
      or region.target_id in ('region-gyeonggi', 'region-41000', 'region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-capital-03-cerik'),
    region.target_id,
    3,
    'external',
    'cerik-2026-q1-real-estate-market',
    '건설산업 리포트',
    '한국건설산업연구원 2026년 1분기 부동산시장동향',
    'https://www.cerik.re.kr/uploads/report/3077/%EB%B6%80%EB%8F%99%EC%82%B0%EC%8B%9C%EC%9E%A5%EB%8F%99%ED%96%A5%202026%EB%85%84%201%EB%B6%84%EA%B8%B0_2026-04-13.pdf',
    '한국건설산업연구원',
    '2026-04-13 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or target.display_name like '인천광역시%'
      or parent_target.display_name in ('경기도', '인천광역시')
      or region.target_id in ('region-gyeonggi', 'region-41000', 'region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-capital-04-rone'),
    region.target_id,
    4,
    'external',
    'reb-rone-2026-05-national-housing-price-trend',
    '공식 가격지표',
    '한국부동산원 R-ONE 2026년 5월 전국주택가격동향',
    'https://www.reb.or.kr/r-one/portal/main/indexPage.do',
    '한국부동산원',
    '2026-06-15 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or target.display_name like '인천광역시%'
      or parent_target.display_name in ('경기도', '인천광역시')
      or region.target_id in ('region-gyeonggi', 'region-41000', 'region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-capital-05-molit-2026-supply'),
    region.target_id,
    5,
    'external',
    'molit-2026-capital-public-land-50000',
    '수도권 공급정책',
    '정책브리핑 내년 수도권 공공택지 5만가구 이상 착공',
    'https://www.korea.kr/news/policyNewsView.do?newsId=148956384',
    '국토교통부',
    '2025-12-12 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or target.display_name like '인천광역시%'
      or parent_target.display_name in ('경기도', '인천광역시')
      or region.target_id in ('region-gyeonggi', 'region-41000', 'region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-gyeonggi-06-first-newtown'),
    region.target_id,
    6,
    'external',
    'gyeonggi-first-newtown-master-plan-20250528',
    '경기 1기 신도시',
    '경기도 분당·일산 기본계획 승인, 1기 신도시 5곳 정비 본격화',
    'https://gnews.gg.go.kr/briefing/brief_gongbo_view.do?BS_CODE=s017&number=66080',
    '경기도뉴스포털',
    '2025-05-28 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or parent_target.display_name = '경기도'
      or region.target_id in ('region-gyeonggi', 'region-41000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-gyeonggi-07-sanbon-special'),
    region.target_id,
    7,
    'external',
    'gyeonggi-sanbon-special-renewal-zone-20260113',
    '경기 정비사업',
    '경기도 1기 신도시 선도지구 특별정비구역 첫 지정 군포·산본',
    'https://gnews.gg.go.kr/briefing/brief_gongbo_view.do?BS_CODE=s017&number=68984',
    '경기도뉴스포털',
    '2026-01-13 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or parent_target.display_name = '경기도'
      or region.target_id in ('region-gyeonggi', 'region-41000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-gyeonggi-08-third-newtown'),
    region.target_id,
    8,
    'external',
    'third-newtown-official-notice-2026',
    '3기 신도시',
    '3기 신도시 고시·공고 목록',
    'https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Board/Board.do?mCode=MN111',
    '한국토지주택공사',
    '2026-05-21 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or parent_target.display_name = '경기도'
      or region.target_id in ('region-gyeonggi', 'region-41000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-gyeonggi-09-yongin-semicon'),
    region.target_id,
    9,
    'external',
    'molit-yongin-semiconductor-national-industrial-complex',
    '경기 산업축',
    '국토교통부 용인 반도체 국가산업단지 지정',
    'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95090534&lcmspage=7',
    '국토교통부',
    '2024-12-26 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or parent_target.display_name = '경기도'
      or region.target_id in ('region-gyeonggi', 'region-41000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-gyeonggi-10-bucheon-daejang'),
    region.target_id,
    10,
    'external',
    'third-newtown-bucheon-daejang-overview',
    '부천대장 근거',
    '3기 신도시 부천대장 지구개요',
    'https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Contents/Contents.do?mCode=MN068',
    '한국토지주택공사',
    null,
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '경기도%'
      or parent_target.display_name = '경기도'
      or region.target_id in ('region-gyeonggi', 'region-41000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-incheon-06-capital-plan'),
    region.target_id,
    6,
    'external',
    'incheon-capital-housing-supply-plan-gyeyang-tv',
    '인천 공급계획',
    '인천광역시 수도권 주택공급 계획',
    'https://www.incheon.go.kr/open/OPEN020301/view?attachFileSeq=FILE_000000000062056&curPage=9&planSeq=DOM_0000000000099714',
    '인천광역시',
    '2025-08-28 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '인천광역시%'
      or parent_target.display_name = '인천광역시'
      or region.target_id in ('region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-incheon-07-gyeyang-1106'),
    region.target_id,
    7,
    'external',
    'molit-incheon-gyeyang-1106-public-sale',
    '계양 공급',
    '정책브리핑 인천계양 공공주택 1106호 분양',
    'https://www.korea.kr/news/policyNewsView.do?newsId=148933414',
    '국토교통부',
    '2024-09-03 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '인천광역시%'
      or parent_target.display_name = '인천광역시'
      or region.target_id in ('region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-incheon-08-gyeyang-change'),
    region.target_id,
    8,
    'external',
    'third-newtown-incheon-gyeyang-plan-change-20260105',
    '계양 지구계획',
    '3기 신도시 인천계양테크노밸리 지구계획 변경 승인',
    'https://xn--3-3u6ey6lv7rsa.kr/kor/CMS/Board/Board.do?board_seq=445&mCode=MN111&mgr_seq=13&mode=view',
    '한국토지주택공사',
    '2026-01-05 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '인천광역시%'
      or parent_target.display_name = '인천광역시'
      or region.target_id in ('region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-incheon-09-ih-news'),
    region.target_id,
    9,
    'external',
    'incheon-housing-city-corporation-news-2026',
    '인천 개발사업',
    '인천도시공사 보도자료 목록',
    'https://www.ih.co.kr/main/public/news_data.jsp',
    '인천도시공사',
    '2026-06-22 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '인천광역시%'
      or parent_target.display_name = '인천광역시'
      or region.target_id in ('region-incheon', 'region-28000')
  )
union all
select
    concat('regional-report-source-', region.target_id, '-incheon-10-third-newtown'),
    region.target_id,
    10,
    'external',
    'third-newtown-official-notice-2026',
    '3기 신도시',
    '3기 신도시 고시·공고 목록',
    'https://www.xn--3-3u6ey6lv7rsa.kr/kor/CMS/Board/Board.do?mCode=MN111',
    '한국토지주택공사',
    '2026-05-21 00:00:00',
    'ok',
    '2026-06-24 23:45:00',
    '2026-06-24 23:45:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_targets parent_target on parent_target.id = region.parent_region_id
where region.region_level in ('sido', 'sigungu')
  and (
      target.display_name like '인천광역시%'
      or parent_target.display_name = '인천광역시'
      or region.target_id in ('region-incheon', 'region-28000')
  );
