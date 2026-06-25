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
    rewritten.target_id,
    concat('regional-report-', rewritten.target_id, '-investor-column-20260625'),
    'regional-report-investor-column-v2',
    'codex-investor-column-rewrite-prompt-20260625',
    'codex-gpt-5-investor-column',
    'codex-quality-rewrite:investor-column-20260625',
    concat(rewritten.display_name, ' 투자 판단 리포트'),
    rewritten.headline,
    rewritten.summary,
    rewritten.body,
    case
        when rewritten.expectation_2 is null then concat('["', rewritten.expectation_1, '"]')
        else concat('["', rewritten.expectation_1, '","', rewritten.expectation_2, '"]')
    end,
    case
        when rewritten.concern_2 is null then concat('["', rewritten.concern_1, '"]')
        else concat('["', rewritten.concern_1, '","', rewritten.concern_2, '"]')
    end,
    'deep_researched',
    rewritten.confidence,
    '2026-06-25 00:00:00',
    '2026-06-25 09:40:00',
    coalesce(existing.created_at, '2026-06-25 09:40:00'),
    '2026-06-25 09:40:00'
from (
    select
        region.target_id,
        region.region_level,
        region.parent_region_id,
        target.display_name,
        case
            when region.target_id = 'region-seoul' then '서울은 강남3구와 용산, 한강권, 재건축 후보지가 서로 다른 시장입니다.'
            when region.target_id = 'region-seoul-gangnam' then '강남구는 신고가보다 학군·업무·정비사업 가격을 분리해서 봐야 합니다.'
            when region.target_id = 'region-seoul-seocho' then '서초구는 서리풀2지구와 정비사업 기대가 가격에 먼저 반영되기 쉬운 지역입니다.'
            when region.target_id = 'region-seoul-songpa' then '송파구는 잠실·가락·문정의 수요가 다르게 움직이는 동남권 핵심 지역입니다.'
            when region.target_id = 'region-seoul-yongsan' then '용산구는 국제업무·정비 기대와 실입주 수요를 따로 봐야 합니다.'
            when region.target_id = 'region-seoul-mapo' then '마포구는 상암·공덕·홍대 수요가 강남권 대체재로 읽히는지 확인할 지역입니다.'
            when region.target_id = 'region-seoul-nowon' then '노원구는 노후 단지와 재건축 기대가 실수요 가격대와 충돌하는 지역입니다.'
            when region.target_id in ('region-gyeonggi', 'region-41000') then '경기도는 1기 신도시 정비, 3기 신도시, 용인 반도체 축을 한 결론으로 묶으면 안 됩니다.'
            when region.target_id = 'region-gyeonggi-yonginsicheoingu' then '용인 처인구는 첨단시스템반도체 국가산단 기대가 실제 주거 수요로 바뀌는지 봐야 합니다.'
            when region.target_id = 'region-gyeonggi-bucheon' then '부천은 부천대장 공급과 중동 1기 신도시 정비가 동시에 가격을 흔드는 지역입니다.'
            when region.target_id = 'region-incheon-gyeyang' then '계양구는 계양테크노밸리와 17천호 공급이 실제 흡수되는지가 핵심입니다.'
            when target.display_name = '충청남도' then '충남은 천안·아산, 내포, 서해안 산업축을 서로 다른 시장으로 나눠 봐야 합니다.'
            when target.display_name like '충청남도 아산시%' then '아산은 천안과 붙어 있는 수요, 탕정 산업 배후, 새 아파트 선호를 같이 봐야 합니다.'
            when target.display_name like '충청남도 천안시 서북구%' then '천안 서북구는 수도권 남부 출퇴근과 산업단지 배후 수요가 가격을 설명하는 지역입니다.'
            when target.display_name like '충청남도 천안시 동남구%' then '천안 동남구는 원도심·대학·역세권 수요와 서북구 신축 선호를 비교해야 합니다.'
            when target.display_name like '충청남도 당진시%' then '당진은 제철·항만 산업 경기와 임대 수요가 같이 움직이는 서해안 산업도시입니다.'
            when target.display_name like '충청남도 서산시%' then '서산은 대산 산업단지와 서해안 생활권 수요가 핵심인 지역입니다.'
            when target.display_name like '충청남도 홍성군%' or target.display_name like '충청남도 예산군%' then '내포권은 행정수요와 신규 공급 흡수력이 먼저 확인돼야 합니다.'
            when target.display_name like '충청남도 보령시%' or target.display_name like '충청남도 태안군%' then '충남 해안권은 관광 수요와 상주 주거 수요를 구분해야 합니다.'
            when target.display_name like '부산광역시 해운대구%' then '해운대는 북항보다 동부산 고급 주거, 센텀 업무, 전세 수요가 먼저 가격을 설명합니다.'
            when target.display_name like '부산광역시%' then '부산은 북항·가덕도 기대와 동부산·원도심·서부산의 실수요가 다르게 움직입니다.'
            when target.display_name like '대구광역시 수성구%' then '수성구는 대구 미분양 부담 속에서도 학군·핵심지 선호가 얼마나 버티는지가 관건입니다.'
            when target.display_name like '대구광역시%' then '대구는 미분양 감소보다 준공 후 미분양과 입주 부담을 먼저 봐야 합니다.'
            when target.display_name like '세종특별자치시%' then '세종은 행정수도 기대와 5생활권 공급이 같은 방향으로 흡수되는지 봐야 합니다.'
            when target.display_name like '제주특별자치도%' then '제주는 관광 회복, 이주 수요, 주택 통계를 분리해서 읽어야 합니다.'
            when target.display_name like '광주광역시%' then '광주는 첨단산단·도심 정비·전세 수요가 같은 속도로 움직이지 않는 시장입니다.'
            when target.display_name like '대전광역시 유성구%' then '유성구는 연구개발 수요와 도안권 공급이 같이 움직이는 대전의 핵심 지역입니다.'
            when target.display_name like '대전광역시%' then '대전은 연구개발·공공기관 수요와 도안권 공급 부담을 함께 봐야 합니다.'
            when target.display_name like '울산광역시%' then '울산은 자동차·조선·석유화학 업황이 주거 수요에 바로 연결되는 산업도시입니다.'
            when target.display_name like '강원도%' then '강원은 춘천·원주 상주 수요와 영동 관광 수요를 같은 시장으로 보면 안 됩니다.'
            when target.display_name like '충청북도 청주시%' then '청주는 오송·오창 산업축과 도심 생활수요가 같이 움직이는 충북 핵심 지역입니다.'
            when target.display_name like '충청북도%' then '충북은 청주권 산업 수요와 중부내륙 생활권의 거래 깊이가 크게 다릅니다.'
            when target.display_name like '전라북도 전주시%' then '전주는 전북 실거주 수요의 중심이지만 새만금 기대와는 분리해서 봐야 합니다.'
            when target.display_name like '전라북도 군산시%' then '군산은 새만금·산단 뉴스가 주거 수요로 전환되는 속도를 확인해야 합니다.'
            when target.display_name like '전라북도%' then '전북은 전주 생활수요와 새만금·군산·익산 산업축을 따로 읽어야 합니다.'
            when target.display_name like '전라남도 여수시%' or target.display_name like '전라남도 순천시%' or target.display_name like '전라남도 광양시%' then '여수·순천·광양권은 산업단지와 생활권 수요가 같이 움직이는 전남 핵심축입니다.'
            when target.display_name like '전라남도%' then '전남은 산업도시, 혁신도시, 해안 관광권의 거래 성격이 서로 다릅니다.'
            when target.display_name like '경상북도 포항시%' then '포항은 철강·배터리 기대와 인구 흐름을 같이 확인해야 하는 산업도시입니다.'
            when target.display_name like '경상북도 구미시%' then '구미는 전자·첨단산업 회복이 전세 수요로 이어지는지가 핵심입니다.'
            when target.display_name like '경상북도%' then '경북은 포항·구미 산업축과 안동·예천 행정수요, 관광권을 분리해야 합니다.'
            when target.display_name like '경상남도 창원시%' then '창원은 제조업 경기와 노후 주거지 정비가 함께 가격을 움직입니다.'
            when target.display_name like '경상남도 김해시%' or target.display_name like '경상남도 양산시%' then '김해·양산은 부산권 배후 주거와 자체 산업 수요가 섞인 지역입니다.'
            when target.display_name like '경상남도 거제시%' or target.display_name like '경상남도 통영시%' then '거제·통영은 조선업과 관광 수요에 민감한 해안 생활권입니다.'
            when target.display_name like '경상남도%' then '경남은 창원 제조업, 부산권 배후, 남해안 산업·관광권을 나눠 봐야 합니다.'
            when region.region_level = 'sido' then concat(target.display_name, ': 하위 생활권별 수요와 공급이 달라 광역 평균만으로 판단하기 어렵습니다.')
            when target.display_name like '%군' then concat(target.display_name, ': 거래 표본이 얇아 한두 건의 실거래보다 전세와 인구 흐름을 먼저 봐야 합니다.')
            when target.display_name like '%구' then concat(target.display_name, ': 같은 광역시 안에서도 역세권·학군·신축 선호가 가격을 갈라놓는 지역입니다.')
            else concat(target.display_name, ': 자체 생활권 수요와 상위 광역권 흐름을 분리해서 봐야 합니다.')
        end as headline,
        case
            when region.region_level = 'sido' then '광역 평균보다 하위 생활권의 수요·공급 차이를 먼저 보는 리포트입니다.'
            when target.display_name like '%군' then '거래 표본이 얇은 지역은 짧게, 확인할 지표만 남긴 리포트입니다.'
            else '실거래·전세·공급·정책을 투자 판단 순서로 압축한 지역 리포트입니다.'
        end as summary,
        case
            when region.target_id = 'region-seoul' then '서울은 강남3구와 용산이 가격 발견을 주도하지만, 전세 압력은 강북·노후 단지까지 넓게 번질 수 있습니다. 서리풀2지구 2,000호 같은 공급 뉴스는 장기 심리에는 영향을 주지만 단기 매수 판단에서는 착공·분양 시점을 따로 봐야 합니다.'
            when region.target_id = 'region-seoul-gangnam' then '강남구는 대치·청담·삼성·개포·압구정이 각각 다른 가격표를 갖습니다. 학군과 업무 접근성은 강하지만 신고가 한두 건보다 전세가율, 토지거래허가, 정비사업 속도를 함께 봐야 합니다.'
            when region.target_id = 'region-seoul-seocho' then '서초구는 반포·잠원·서초·양재가 같은 구 안에서도 다르게 움직입니다. 서리풀2지구 2,000호는 장기 공급 신호지만, 현재 가격은 정비사업 기대와 토지거래허가 부담이 먼저 반영될 수 있습니다.'
            when region.target_id = 'region-seoul-songpa' then '송파구는 잠실의 상징성, 가락·문정의 실거주, 위례·거여의 공급 성격이 다릅니다. 대장 단지 신고가와 주변 구축의 실거래가 같이 움직이는지를 봐야 합니다.'
            when region.target_id = 'region-seoul-yongsan' then '용산구는 국제업무지구와 한남·이촌 정비 기대가 강하지만 실입주 수요는 가격대가 매우 얇습니다. 정책 기대가 거래량 없이 가격만 밀어 올리는 구간은 조심해야 합니다.'
            when region.target_id = 'region-seoul-mapo' then '마포구는 상암·공덕·홍대가 서로 다른 수요를 갖습니다. 강남권 대체재로 읽히려면 공덕·아현 전세와 상암 업무 수요가 함께 버텨야 합니다.'
            when region.target_id = 'region-seoul-nowon' then '노원구는 노후 단지 비중이 높아 재건축 기대와 실수요 가격대가 자주 충돌합니다. 전세가 먼저 회복되지 않으면 정비 기대만으로 매매가를 설명하기 어렵습니다.'
            when region.target_id in ('region-gyeonggi', 'region-41000') then '경기도는 1기 신도시 정비, 3기 신도시, 용인 반도체를 한 방향으로 해석하면 안 됩니다. 성남·과천·하남은 서울 대체재, 평택·용인·화성은 산업 배후, 김포·파주·양주는 교통 기대의 검증 구간입니다.'
            when region.target_id = 'region-gyeonggi-yonginsicheoingu' then '용인 처인구는 첨단시스템반도체 국가산단 기대가 가장 큰 변수입니다. 다만 산업 뉴스가 바로 주택 수요가 되는 것은 아니어서, 원삼·남사 주변 입주와 전세 수요가 실제로 붙는지 확인해야 합니다.'
            when region.target_id = 'region-gyeonggi-bucheon' then '부천은 부천대장 3기 신도시와 중동 1기 신도시 정비가 동시에 존재합니다. 공급 기대와 정비 기대가 섞여 있어, 새 아파트 선호와 구축 재건축 프리미엄을 분리해야 합니다.'
            when region.target_id = 'region-incheon-gyeyang' then '계양구는 계양테크노밸리와 17천호 공급이 핵심입니다. 서울 접근성 기대보다 중요한 것은 입주 시점에 전세가 받쳐주는지, 검단·부천대장과 수요가 겹치는지입니다.'
            when target.display_name = '충청남도' then '충남은 천안·아산의 수도권 남부 수요, 내포신도시의 행정수요, 당진·서산의 서해안 산업축이 서로 다른 시장입니다. 광역 평균을 보기보다 어느 축의 수요를 사는지 먼저 정해야 합니다.'
            when target.display_name like '충청남도 아산시%' then '아산은 천안과 붙어 있는 수요, 탕정·배방의 산업 배후, 새 아파트 선호가 함께 움직입니다. 투자자는 천안 생활권으로 보는 단지와 아산 자체 산업수요로 보는 단지를 나눠야 합니다.'
            when target.display_name like '충청남도 천안시 서북구%' then '천안 서북구는 불당·성성·두정처럼 신축과 직장 접근성이 가격을 가르는 지역입니다. 수도권 남부 출퇴근 수요와 산업단지 임대수요가 전세를 받쳐줄 때 매매 판단이 쉬워집니다.'
            when target.display_name like '충청남도 천안시 동남구%' then '천안 동남구는 원도심, 대학가, 역세권 수요가 중심입니다. 서북구 신축 흐름을 그대로 가져오기보다 저가 실거주와 정비 기대가 실제 거래로 이어지는지 봐야 합니다.'
            when target.display_name like '충청남도 당진시%' then '당진은 제철·항만 산업 경기와 임대 수요가 핵심입니다. 산업단지 고용이 안정되면 하방은 줄지만, 공급이 한꺼번에 들어오면 매매보다 전세가 먼저 흔들릴 수 있습니다.'
            when target.display_name like '충청남도 서산시%' then '서산은 대산 산업단지와 자족 생활권이 가격을 설명합니다. 산업 배후 수요가 뚜렷한 단지와 외곽 택지의 거래 깊이를 분리해야 합니다.'
            when target.display_name like '충청남도 홍성군%' or target.display_name like '충청남도 예산군%' then '내포권은 행정기관 수요가 장점이지만 공급 흡수력이 더 중요합니다. 새 단지가 많을수록 매매보다 전세 공실과 입주 속도를 먼저 봐야 합니다.'
            when target.display_name like '충청남도 보령시%' or target.display_name like '충청남도 태안군%' then '충남 해안권은 관광과 세컨드하우스 수요가 생길 수 있지만 상주 수요는 얇습니다. 투자 판단은 성수기 분위기보다 연중 거래 빈도와 임대 안정성으로 해야 합니다.'
            when target.display_name like '부산광역시 해운대구%' then '해운대는 부산 전체 북항 기대보다 동부산 고급 주거와 센텀 업무 수요가 더 직접적입니다. 해운대 안에서도 해안 고가 단지와 내륙 구축의 전세 회복 속도를 나눠 봐야 합니다.'
            when target.display_name like '부산광역시%' then '부산은 북항·가덕도 기대가 도시 심리를 만들지만 가격은 해운대·수영·동래, 원도심, 서부산이 다르게 움직입니다. 개발 뉴스보다 전세 회복과 입주 물량의 충돌을 먼저 봅니다.'
            when target.display_name like '대구광역시 수성구%' then '수성구는 대구 미분양 부담 속에서도 학군·핵심지 선호가 남아 있는 지역입니다. 수성구라는 이름만으로 충분하지 않고, 전세가 회복되는 신축·준신축인지부터 확인해야 합니다.'
            when target.display_name like '대구광역시%' then '대구는 미분양 총량 감소보다 준공 후 미분양과 입주 부담이 더 중요합니다. 핵심지는 먼저 버틸 수 있지만 외곽 공급지는 가격 회복까지 시간이 더 걸릴 수 있습니다.'
            when target.display_name like '세종특별자치시%' then '세종은 행정수도 기대와 5생활권 공급이 동시에 움직입니다. 5생활권 분양과 입주가 실제 수요로 흡수되면 회복 근거가 되지만, 정책 기대만 앞서면 가격 변동성이 커질 수 있습니다.'
            when target.display_name like '제주특별자치도%' then '제주는 관광 회복, 이주 수요, 주택 통계를 같이 봐야 합니다. 월별 주택 통계는 필요하지만 표본이 얇아 제주시와 서귀포, 읍면 수요를 섞어 판단하면 위험합니다.'
            when target.display_name like '광주광역시%' then '광주는 첨단산단과 도심 정비 기대가 있지만 생활권별 차이가 큽니다. 광산·북구의 신축 수요와 동구·남구의 도심 정비 기대를 한 문장으로 묶으면 판단이 흐려집니다.'
            when target.display_name like '대전광역시 유성구%' then '유성구는 연구개발, 대학, 도안권 공급이 가격을 설명합니다. 좋은 입지라도 입주 물량이 겹치면 전세가 먼저 약해질 수 있어 매매보다 임대 수요를 먼저 봐야 합니다.'
            when target.display_name like '대전광역시%' then '대전은 유성·서구 중심 수요와 동구·대덕의 정비·산업 수요가 다릅니다. 세종 연계 기대는 보조 변수이고 실제 판단은 전세와 입주 물량으로 합니다.'
            when target.display_name like '울산광역시%' then '울산은 자동차·조선·석유화학 업황이 주거 수요를 직접 흔듭니다. 산업 회복이 전세 수요로 확인되면 긍정적이지만, 단일 기업 뉴스만으로 매매를 판단하기는 어렵습니다.'
            when target.display_name like '강원도%' then '강원은 춘천·원주의 상주 수요와 강릉·속초의 관광 수요가 다릅니다. 세컨드하우스 분위기보다 연중 전세 수요와 거래 빈도를 확인해야 합니다.'
            when target.display_name like '충청북도 청주시%' then '청주는 오송·오창 산업축과 도심 생활수요가 충북에서 가장 두껍습니다. 다만 산업 기대가 강할수록 분양가와 입주 물량도 같이 올라오므로 전세가 먼저 버티는지 봐야 합니다.'
            when target.display_name like '충청북도%' then '충북은 청주권 산업 수요와 충주·제천·군 단위 생활권의 거래 깊이가 다릅니다. 산업 뉴스가 없는 지역은 가격보다 거래 빈도와 전세 안정성이 더 중요합니다.'
            when target.display_name like '전라북도 전주시%' then '전주는 전북 실거주 수요의 중심입니다. 새만금 기대를 전주 가격에 바로 붙이기보다 혁신도시·도심·신축 선호가 전세로 확인되는지 봐야 합니다.'
            when target.display_name like '전라북도 군산시%' then '군산은 새만금과 산업단지 기대가 있지만, 주택 수요로 전환되는 데 시간이 걸립니다. 산업 뉴스보다 고용과 임대 수요가 먼저 움직이는지 확인해야 합니다.'
            when target.display_name like '전라북도%' then '전북은 전주 실거주, 군산·익산 산업축, 새만금 기대가 다르게 작동합니다. 개발 기대를 사기보다 실제 거래와 전세 회복이 붙은 곳을 따로 봐야 합니다.'
            when target.display_name like '전라남도 여수시%' or target.display_name like '전라남도 순천시%' or target.display_name like '전라남도 광양시%' then '여수·순천·광양권은 산업단지와 생활권 수요가 전남에서 가장 뚜렷합니다. 산업 경기와 상주 수요가 같이 받쳐주는 단지인지 확인해야 합니다.'
            when target.display_name like '전라남도%' then '전남은 산업도시, 혁신도시, 해안 관광권의 거래 성격이 서로 다릅니다. 군 단위는 한두 건의 실거래보다 인구와 임대 수요를 더 보수적으로 봐야 합니다.'
            when target.display_name like '경상북도 포항시%' then '포항은 철강·배터리 기대가 있지만 산업 경기 변동에 민감합니다. 일자리 회복이 전세와 매매 수요로 같이 확인될 때 의미가 있습니다.'
            when target.display_name like '경상북도 구미시%' then '구미는 전자·첨단산업 기반이 강하지만 경기 변동에 민감합니다. 공장 증설 뉴스보다 임대 수요와 전입 흐름이 먼저 확인돼야 합니다.'
            when target.display_name like '경상북도%' then '경북은 포항·구미 산업축, 안동·예천 행정수요, 경주 관광권이 서로 다릅니다. 대구경북신공항 기대는 장기 변수로 보되 단기 매매 판단은 거래와 전세로 해야 합니다.'
            when target.display_name like '경상남도 창원시%' then '창원은 제조업 경기와 노후 주거지 정비가 같이 움직입니다. 산업 회복이 전세 수요를 받쳐주면 긍정적이지만 구축 정비 기대만으로는 부족합니다.'
            when target.display_name like '경상남도 김해시%' or target.display_name like '경상남도 양산시%' then '김해·양산은 부산권 배후 주거와 자체 산업 수요가 섞입니다. 부산 접근성 기대와 신규 공급 부담을 분리해야 합니다.'
            when target.display_name like '경상남도 거제시%' or target.display_name like '경상남도 통영시%' then '거제·통영은 조선업과 관광 수요에 민감합니다. 업황 회복이 전세 안정으로 이어지는지 확인한 뒤 매매를 봐야 합니다.'
            when target.display_name like '경상남도%' then '경남은 창원 제조업, 김해·양산 부산 배후, 거제·통영 조선·관광권이 다릅니다. 광역 평균보다 산업과 전세 수요가 붙는 생활권을 먼저 봐야 합니다.'
            when region.region_level = 'sido' then concat(target.display_name, ': 광역 평균만으로 판단하기 어렵습니다. 하위 시군구의 전세, 입주 물량, 산업 수요가 같은 방향인지 먼저 확인해야 합니다.')
            when target.display_name like '%군' then concat(target.display_name, ': 거래 표본이 얇은 지역입니다. 가격 방향을 말하기보다 실거래 빈도, 전세 수요, 인구 흐름이 유지되는지만 확인하는 편이 낫습니다.')
            when target.display_name like '%구' then concat(target.display_name, ': 같은 광역시 안에서도 역세권, 학군, 신축 선호가 가격을 갈라놓습니다. 단기 등락률보다 전세와 실거래가 함께 움직이는 단지를 봐야 합니다.')
            else concat(target.display_name, ': 자체 생활권 수요와 상위 광역권 흐름을 분리해서 봐야 합니다. 투자 판단은 개발 뉴스보다 전세, 거래 빈도, 입주 물량의 균형에서 시작합니다.')
        end as body,
        case
            when target.display_name like '충청남도 아산시%' then '탕정·배방 산업 배후 수요가 전세로 확인되면 매매 설명력이 생깁니다.'
            when target.display_name like '충청남도 천안시 서북구%' then '직장·교통 수요가 신축 전세를 받치면 가격 방어력이 커집니다.'
            when target.display_name like '충청남도 당진시%' then '제철·항만 고용이 임대 수요로 이어지면 하방 위험이 줄어듭니다.'
            when target.display_name like '서울특별시%' then '전세 압력과 정비사업 일정이 같이 움직이면 실수요 근거가 강해집니다.'
            when target.display_name like '경기도%' or target.display_name like '인천광역시%' then '교통·산업·공급 일정이 전세 수요와 같이 확인되면 투자 근거가 생깁니다.'
            when target.display_name like '부산광역시%' then '전세 회복이 동부산과 원도심 중 어디서 먼저 나타나는지 확인할 수 있습니다.'
            when target.display_name like '대구광역시%' then '미분양 감소가 전세와 실거래 회복으로 이어지는지 확인할 수 있습니다.'
            when target.display_name like '세종특별자치시%' then '5생활권 공급이 청약·입주 수요로 흡수되면 회복 근거가 됩니다.'
            when target.display_name like '제주특별자치도%' then '관광·이주 수요와 상주 수요를 나눠 보면 과열 신호를 거를 수 있습니다.'
            else '전세와 실거래가 같은 방향으로 움직이면 단기 뉴스보다 믿을 만한 근거가 됩니다.'
        end as expectation_1,
        case
            when region.region_level = 'sido' then '하위 생활권별로 강한 곳과 약한 곳을 분리해 볼 수 있습니다.'
            when target.display_name like '%군' then null
            else '공급 일정과 기존 단지 전세를 같이 보면 무리한 진입을 줄일 수 있습니다.'
        end as expectation_2,
        case
            when target.display_name like '충청남도 아산시%' then '천안 생활권 기대만 보고 입주 물량 부담을 놓치면 위험합니다.'
            when target.display_name like '충청남도 천안시 서북구%' then '신축 선호가 강해도 분양가와 전세가 벌어지면 부담이 커집니다.'
            when target.display_name like '충청남도 당진시%' then '산업 뉴스가 고용과 전세로 확인되기 전에는 가격 기대가 앞설 수 있습니다.'
            when target.display_name like '서울특별시 서초구%' then '토지거래허가와 정비사업 기대가 실제 수요보다 앞설 수 있습니다.'
            when target.display_name like '경기도 용인시 처인구%' then '산업 뉴스만 보고 주거 수요 전환 속도를 과대평가할 수 있습니다.'
            when target.display_name like '인천광역시 계양구%' then '공급 규모가 커서 입주 시점 전세가 먼저 흔들릴 수 있습니다.'
            when target.display_name like '대구광역시%' then '미분양 감소만 보고 준공 후 미분양 부담을 과소평가할 수 있습니다.'
            when target.display_name like '세종특별자치시%' then '정책 기대가 공급 흡수력보다 먼저 가격에 반영될 수 있습니다.'
            when target.display_name like '제주특별자치도%' then '관광 수요를 상주 주거 수요로 착각하면 판단이 흔들립니다.'
            when target.display_name like '%군' then '거래 표본이 얇아 한두 건으로 흐름을 단정하기 어렵습니다.'
            else '개발 뉴스가 전세와 실거래보다 먼저 가격 기대를 만들 수 있습니다.'
        end as concern_1,
        case
            when target.display_name like '%군' then null
            when region.region_level = 'sido' then '광역 평균이 강해 보여도 약한 하위 지역은 따로 남을 수 있습니다.'
            else '입주 물량이 겹치면 매매보다 전세가 먼저 약해질 수 있습니다.'
        end as concern_2,
        case
            when region.region_level = 'sido' then 0.82
            else 0.78
        end as confidence
    from real_estate_regions region
    join real_estate_targets target on target.id = region.target_id
    where region.region_level in ('sido', 'sigungu')
) rewritten
left join real_estate_regional_reports existing on existing.target_id = rewritten.target_id
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
