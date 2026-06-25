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
    concat('regional-report-', rewritten.target_id, '-financial-outlook-20260625'),
    'regional-report-financial-outlook-v3',
    'codex-financial-outlook-rewrite-prompt-20260625',
    'codex-gpt-5-financial-outlook',
    'codex-quality-rewrite:financial-outlook-20260625',
    concat(rewritten.display_name, ' 시장 판단 리포트'),
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
    '2026-06-25 01:30:00',
    coalesce(existing.created_at, '2026-06-25 01:30:00'),
    '2026-06-25 01:30:00'
from (
    select
        region.target_id,
        region.region_level,
        target.display_name,
        case
            when region.target_id = 'region-seoul' then '서울은 전세 압력과 핵심지 정비 기대가 동시에 작동하는 시장'
            when region.target_id = 'region-seoul-gangnam' then '강남구는 학군·업무·정비사업 가격이 분리되는 핵심지'
            when region.target_id = 'region-seoul-seocho' then '서초구는 서리풀2지구와 정비 기대가 선반영되기 쉬운 시장'
            when region.target_id = 'region-seoul-songpa' then '송파구는 잠실·가락·문정 수요를 나눠 봐야 하는 동남권 핵심지'
            when region.target_id = 'region-seoul-yongsan' then '용산구는 개발 기대와 실입주 수요의 간극이 큰 고가 시장'
            when region.target_id = 'region-seoul-mapo' then '마포구는 상암·공덕·홍대 수요가 분산된 강북 핵심지'
            when region.target_id = 'region-seoul-nowon' then '노원구는 노후 단지 정비 기대와 실수요 가격대가 충돌하는 시장'
            when region.target_id in ('region-gyeonggi', 'region-41000') then '경기도는 정비·공급·산업축을 분리해야 하는 복합 시장'
            when region.target_id = 'region-gyeonggi-yonginsicheoingu' then '용인 처인구는 반도체 국가산단 기대의 주거 전환이 핵심'
            when region.target_id = 'region-gyeonggi-bucheon' then '부천은 부천대장 공급과 중동 정비가 동시에 작동하는 시장'
            when region.target_id = 'region-incheon-gyeyang' then '계양구는 계양테크노밸리와 대규모 공급 흡수가 핵심'
            when target.display_name = '충청남도' then '충남은 천안·아산과 서해안 산업벨트를 분리해야 하는 시장'
            when target.display_name like '충청남도 아산시%' then '아산은 탕정·배방 산업 배후와 천안 연계 수요가 핵심'
            when target.display_name like '충청남도 천안시 서북구%' then '천안 서북구는 신축 선호와 수도권 남부 출퇴근 수요가 핵심'
            when target.display_name like '충청남도 천안시 동남구%' then '천안 동남구는 원도심·대학·역세권 수요의 확인 구간'
            when target.display_name like '충청남도 당진시%' then '당진은 제철·항만 고용과 임대 수요가 가격 하방을 결정'
            when target.display_name like '충청남도 서산시%' then '서산은 대산 산업단지와 자족 생활권 수요가 핵심'
            when target.display_name like '충청남도 홍성군%' or target.display_name like '충청남도 예산군%' then '내포권은 행정수요보다 공급 흡수력이 우선'
            when target.display_name like '충청남도 보령시%' or target.display_name like '충청남도 태안군%' then '충남 해안권은 관광 수요와 상주 수요의 분리가 핵심'
            when target.display_name like '부산광역시 해운대구%' then '해운대는 북항보다 동부산 고급 주거와 센텀 수요가 직접 변수'
            when target.display_name like '부산광역시%' then '부산은 북항·가덕도 기대와 생활권별 전세 회복이 분리되는 시장'
            when target.display_name like '대구광역시 수성구%' then '수성구는 대구 미분양 부담 속 핵심지 방어력의 시험대'
            when target.display_name like '대구광역시%' then '대구는 미분양과 준공 후 미분양 부담이 가격 상단을 제한'
            when target.display_name like '세종특별자치시%' then '세종은 행정수도 기대와 5생활권 공급 흡수가 함께 필요한 시장'
            when target.display_name like '제주특별자치도%' then '제주는 관광·이주 수요와 주택 통계의 신호가 갈리는 시장'
            when target.display_name like '광주광역시%' then '광주는 첨단산단 기대와 생활권별 신축 수요가 분리되는 시장'
            when target.display_name like '대전광역시 유성구%' then '유성구는 연구개발 수요와 도안권 공급 부담이 함께 작동'
            when target.display_name like '대전광역시%' then '대전은 유성·서구 중심 수요와 도안권 공급 부담이 핵심'
            when target.display_name like '울산광역시%' then '울산은 자동차·조선·석유화학 업황이 주거 수요를 좌우'
            when target.display_name like '강원도%' then '강원은 춘천·원주 상주 수요와 영동 관광 수요가 분리되는 시장'
            when target.display_name like '충청북도 청주시%' then '청주는 오송·오창 산업축과 도심 생활수요가 함께 작동'
            when target.display_name like '충청북도%' then '충북은 청주권 산업 수요와 중부내륙 거래 깊이의 차이가 핵심'
            when target.display_name like '전라북도 전주시%' then '전주는 전북 실거주 수요의 중심축'
            when target.display_name like '전라북도 군산시%' then '군산은 새만금·산단 기대의 주거 수요 전환이 핵심'
            when target.display_name like '전라북도%' then '전북은 전주 생활수요와 새만금 산업 기대를 분리해야 하는 시장'
            when target.display_name like '전라남도 여수시%' or target.display_name like '전라남도 순천시%' or target.display_name like '전라남도 광양시%' then '여수·순천·광양권은 산업단지와 생활권 수요가 겹치는 전남 핵심축'
            when target.display_name like '전라남도%' then '전남은 산업도시·혁신도시·해안 관광권의 거래 성격이 분리되는 시장'
            when target.display_name like '경상북도 포항시%' then '포항은 철강·배터리 기대와 산업 경기 변동성이 공존'
            when target.display_name like '경상북도 구미시%' then '구미는 전자·첨단산업 회복의 전세 전환이 핵심'
            when target.display_name like '경상북도%' then '경북은 포항·구미 산업축과 안동·예천 행정수요가 분리되는 시장'
            when target.display_name like '경상남도 창원시%' then '창원은 제조업 경기와 노후 주거지 정비가 함께 작동'
            when target.display_name like '경상남도 김해시%' or target.display_name like '경상남도 양산시%' then '김해·양산은 부산권 배후 주거와 자체 산업 수요가 혼재'
            when target.display_name like '경상남도 거제시%' or target.display_name like '경상남도 통영시%' then '거제·통영은 조선업과 관광 수요에 민감한 해안 생활권'
            when target.display_name like '경상남도%' then '경남은 창원 제조업과 부산권 배후, 남해안 산업권이 분리되는 시장'
            when region.region_level = 'sido' then concat(target.display_name, '는 하위 생활권별 수급 차이가 큰 광역 시장')
            when target.display_name like '%군' then concat(target.display_name, '는 거래 표본과 상주 수요 확인이 우선인 저유동성 시장')
            when target.display_name like '%구' then concat(target.display_name, '는 역세권·학군·신축 선호가 가격을 가르는 세부 시장')
            else concat(target.display_name, '는 자체 생활권 수요와 광역 흐름을 분리해야 하는 시장')
        end as headline,
        case
            when region.region_level = 'sido' then '광역 평균보다 생활권별 수급 차이를 먼저 본 단기 시장 판단입니다.'
            when target.display_name like '%군' then '거래 표본이 얇은 지역은 확인 지표 중심으로 압축한 리포트입니다.'
            else '실거래·전세·공급·정책 변수를 금융권 리포트 문체로 압축한 지역 판단입니다.'
        end as summary,
        case
            when region.target_id = 'region-seoul' then '서울은 강남3구와 용산이 가격 발견을 주도하고 전세 압력은 강북 노후 단지까지 확산될 수 있는 시장이다. 단기 판단: 상승 지속 가능성 우위. 다만 서리풀2지구 2,000호는 장기 공급 변수라 착공·분양 일정 전까지 단기 가격 논리로 쓰기 어렵다.'
            when region.target_id = 'region-seoul-gangnam' then '강남구는 대치·청담·삼성·개포·압구정이 각각 다른 가격표를 갖는 시장이다. 단기 판단: 상승 지속 가능성 우위. 학군과 업무 접근성은 강하지만 전세가율, 토지거래허가, 정비사업 속도가 함께 확인돼야 한다.'
            when region.target_id = 'region-seoul-seocho' then '서초구는 서리풀2지구, 반포·잠원 정비 기대, 토지거래허가 부담이 공존한다. 단기 판단: 선별 관망. 핵심 신축은 방어력이 있으나 기대 선반영 구간은 전세 확인 없이는 추격 논리가 약하다.'
            when region.target_id = 'region-seoul-songpa' then '송파구는 잠실의 상징성, 가락·문정의 실거주, 위례·거여의 공급 성격이 다르다. 단기 판단: 선별 접근. 대장 단지와 주변 구축의 실거래가 동행할 때 상승 지속성의 신뢰도가 높다.'
            when region.target_id = 'region-seoul-yongsan' then '용산구는 국제업무지구와 한남·이촌 정비 기대가 강하지만 실입주 수요의 가격대가 얇다. 단기 판단: 보수적 선별. 정책 기대가 거래량 없이 가격만 끌어올리는 구간은 변동성 확대 가능성이 높다.'
            when region.target_id = 'region-seoul-mapo' then '마포구는 상암·공덕·홍대 수요가 분산된 시장이다. 단기 판단: 선별 접근. 강남권 대체재 논리는 공덕·아현 전세와 상암 업무 수요가 같이 버틸 때만 유효하다.'
            when region.target_id = 'region-seoul-nowon' then '노원구는 노후 단지 비중이 높고 재건축 기대와 실수요 가격대가 자주 충돌한다. 단기 판단: 관망 우위. 전세가 먼저 회복되지 않으면 정비 기대만으로 상승 지속성을 설명하기 어렵다.'
            when region.target_id in ('region-gyeonggi', 'region-41000') then '경기도는 1기 신도시 정비, 3기 신도시, 용인 반도체가 각각 다른 가격 변수를 만든다. 단기 판단: 선별 접근. 성남·과천·하남은 서울 대체재, 평택·용인·화성은 산업 배후로 나눠 봐야 한다.'
            when region.target_id = 'region-gyeonggi-yonginsicheoingu' then '용인 처인구는 첨단시스템반도체 국가산단 이슈가 핵심 프리미엄이다. 단기 판단: 선별 관망. 산업 뉴스가 주거 수요로 전환되는 속도는 원삼·남사 전세와 입주 흡수에서 확인해야 한다.'
            when region.target_id = 'region-gyeonggi-bucheon' then '부천은 부천대장 공급과 중동 1기 신도시 정비가 동시에 작동한다. 단기 판단: 보수적 선별. 새 아파트 선호와 구축 재건축 프리미엄이 충돌해 동일 생활권 안에서도 가격 설명력이 갈린다.'
            when region.target_id = 'region-incheon-gyeyang' then '계양구는 계양테크노밸리와 17천호 공급이 함께 들어오는 구간이다. 단기 판단: 보수적 관망. 서울 접근성보다 입주 시점 전세 방어와 검단·부천대장 수요 중복이 더 중요하다.'
            when target.display_name = '충청남도' then '충남은 천안·아산의 수도권 남부 수요, 내포 행정수요, 당진·서산의 서해안 산업축이 분리되는 시장이다. 단기 판단: 선별 관망. 광역 평균보다 어느 축에서 전세와 실거래가 같이 버티는지 확인해야 한다.'
            when target.display_name like '충청남도 아산시%' then '아산은 천안과 붙어 있는 수요, 탕정·배방 산업 배후, 새 아파트 선호가 핵심이다. 단기 판단: 선별 접근. 입주 물량이 겹치면 전세가 먼저 압박받을 수 있어 상승 논리는 전세 방어 확인 뒤가 더 깔끔하다.'
            when target.display_name like '충청남도 천안시 서북구%' then '천안 서북구는 불당·성성·두정 신축 선호와 수도권 남부 출퇴근 수요가 가격을 만든다. 단기 판단: 상승 지속 가능성 일부 우위. 전세 방어가 유지되는 단지 중심으로만 회복 신뢰도가 높다.'
            when target.display_name like '충청남도 천안시 동남구%' then '천안 동남구는 원도심, 대학가, 역세권 수요가 중심이다. 단기 판단: 관망 우위. 서북구 신축 흐름을 그대로 가져오기보다 저가 실거주와 정비 기대의 실제 거래 전환을 확인해야 한다.'
            when target.display_name like '충청남도 당진시%' then '당진은 제철·항만 산업 경기와 임대 수요가 가격 하방을 결정한다. 단기 판단: 보수적 관망. 산업 회복은 긍정적이나 고용 확인 전 산업 뉴스만으로 상승 지속성을 보기 어렵다.'
            when target.display_name like '충청남도 서산시%' then '서산은 대산 산업단지와 자족 생활권이 가격을 설명한다. 단기 판단: 선별 관망. 산업 배후 수요가 뚜렷한 단지와 외곽 택지의 거래 깊이를 분리해야 한다.'
            when target.display_name like '충청남도 홍성군%' or target.display_name like '충청남도 예산군%' then '내포권은 행정기관 수요가 장점이지만 신규 공급 흡수력이 더 중요하다. 단기 판단: 관망 우위. 전세 공실과 입주 속도 확인 전까지 가격 회복 판단은 보수적으로 보는 편이 맞다.'
            when target.display_name like '충청남도 보령시%' or target.display_name like '충청남도 태안군%' then '충남 해안권은 관광과 세컨드하우스 수요가 보조 변수이고 상주 수요는 얇다. 단기 판단: 보수적 관망. 성수기 분위기보다 연중 거래 빈도와 임대 안정성이 우선이다.'
            when target.display_name like '충청남도 %시%' then concat(target.display_name, '는 천안·아산 축과 자체 생활권 수요를 분리해 봐야 하는 시장이다. 단기 판단: 선별 관망. 전세와 거래 빈도가 같이 늘 때만 회복 신뢰도가 높다.')
            when target.display_name like '충청남도 %군%' then concat(target.display_name, '는 거래 표본이 얇고 행정·산업·관광 수요의 영향이 제한적인 시장이다. 단기 판단: 관망 우위. 한두 건의 실거래보다 전세 유지와 인구 흐름 확인이 우선이다.')
            when target.display_name like '부산광역시 해운대구%' then '해운대는 북항 이슈보다 해운대·센텀·마린시티의 전세 회복과 고가 주거 선호가 직접 변수다. 단기 판단: 선별 접근. 해안 고가 단지와 내륙 구축의 회복 속도 차이가 커질 수 있다.'
            when target.display_name like '부산광역시%' then '부산은 북항·가덕도 기대가 도시 심리를 만들지만 가격은 해운대·수영·동래, 원도심, 서부산이 다르게 움직인다. 단기 판단: 선별 관망. 개발 뉴스보다 전세 회복과 입주 물량 충돌을 먼저 봐야 한다.'
            when target.display_name like '대구광역시 수성구%' then '수성구는 대구 미분양 부담 속에서도 학군·핵심지 선호가 남아 있다. 단기 판단: 보수적 선별. 수성구 프리미엄은 전세가 회복되는 신축·준신축에서만 방어력이 높다.'
            when target.display_name like '대구광역시%' then '대구는 미분양과 준공 후 미분양 부담이 아직 가격 상단을 제한한다. 단기 판단: 관망 우위. 핵심지 회복과 외곽 공급지 조정이 동시에 나타날 가능성이 높다.'
            when target.display_name like '세종특별자치시%' then '세종은 행정수도 기대와 5생활권 공급 흡수가 동시에 확인돼야 한다. 단기 판단: 관망 우위. 정책 기대만 앞서면 변동성이 커지고, 입주 흡수가 확인되면 회복 논리가 생긴다.'
            when target.display_name like '제주특별자치도%' then '제주는 관광 회복, 이주 수요, 주택 통계가 서로 다른 신호를 낸다. 단기 판단: 보수적 관망. 제주시와 서귀포·읍면을 섞어 보면 표본 착시가 커진다.'
            when target.display_name like '광주광역시%' then '광주는 첨단산단과 도심 정비 기대가 있지만 생활권별 차이가 크다. 단기 판단: 선별 관망. 광산·북구 신축 수요와 동구·남구 정비 기대를 분리해야 한다.'
            when target.display_name like '대전광역시 유성구%' then '유성구는 연구개발, 대학, 도안권 공급이 가격을 설명한다. 단기 판단: 선별 접근. 좋은 입지라도 입주 물량이 겹치면 전세가 먼저 약해질 수 있다.'
            when target.display_name like '대전광역시%' then '대전은 유성·서구 중심 수요와 동구·대덕 정비·산업 수요가 다르다. 단기 판단: 선별 관망. 세종 연계 기대는 보조 변수이고 실제 판단은 전세와 입주 물량에 둬야 한다.'
            when target.display_name like '울산광역시%' then '울산은 자동차·조선·석유화학 업황이 주거 수요를 직접 흔든다. 단기 판단: 선별 접근. 산업 회복이 전세 수요로 확인되면 긍정적이나 단일 기업 뉴스만으로는 부족하다.'
            when target.display_name like '강원도%' then '강원은 춘천·원주의 상주 수요와 강릉·속초의 관광 수요가 다르다. 단기 판단: 보수적 관망. 세컨드하우스 분위기보다 연중 전세 수요와 거래 빈도를 확인해야 한다.'
            when target.display_name like '충청북도 청주시%' then '청주는 오송·오창 산업축과 도심 생활수요가 충북에서 가장 두껍다. 단기 판단: 선별 접근. 산업 기대가 강할수록 분양가와 입주 물량도 같이 올라오므로 전세 방어가 우선이다.'
            when target.display_name like '충청북도%' then '충북은 청주권 산업 수요와 충주·제천·군 단위 생활권의 거래 깊이가 다르다. 단기 판단: 관망 우위. 산업 뉴스가 약한 지역은 가격보다 거래 빈도와 전세 안정성이 더 중요하다.'
            when target.display_name like '전라북도 전주시%' then '전주는 전북 실거주 수요의 중심이다. 단기 판단: 선별 관망. 새만금 기대를 전주 가격에 바로 붙이기보다 혁신도시·도심·신축 선호의 전세 확인이 필요하다.'
            when target.display_name like '전라북도 군산시%' then '군산은 새만금과 산업단지 기대가 있지만 주택 수요 전환에는 시간이 걸린다. 단기 판단: 보수적 관망. 산업 뉴스보다 고용과 임대 수요가 먼저 움직이는지 확인해야 한다.'
            when target.display_name like '전라북도%' then '전북은 전주 실거주, 군산·익산 산업축, 새만금 기대가 다르게 작동한다. 단기 판단: 관망 우위. 개발 기대보다 실제 거래와 전세 회복이 붙은 곳을 따로 봐야 한다.'
            when target.display_name like '전라남도 여수시%' or target.display_name like '전라남도 순천시%' or target.display_name like '전라남도 광양시%' then '여수·순천·광양권은 산업단지와 생활권 수요가 전남에서 가장 뚜렷하다. 단기 판단: 선별 접근. 산업 경기와 상주 수요가 같이 받쳐주는 단지의 방어력이 높다.'
            when target.display_name like '전라남도%' then '전남은 산업도시, 혁신도시, 해안 관광권의 거래 성격이 서로 다르다. 단기 판단: 보수적 관망. 군 단위는 한두 건의 실거래보다 인구와 임대 수요를 더 보수적으로 봐야 한다.'
            when target.display_name like '경상북도 포항시%' then '포항은 철강·배터리 기대가 있지만 산업 경기 변동에 민감하다. 단기 판단: 선별 관망. 일자리 회복이 전세와 거래 수요로 같이 확인될 때 의미가 있다.'
            when target.display_name like '경상북도 구미시%' then '구미는 전자·첨단산업 기반이 강하지만 경기 변동에 민감하다. 단기 판단: 선별 관망. 공장 증설 뉴스보다 임대 수요와 전입 흐름이 먼저 확인돼야 한다.'
            when target.display_name like '경상북도%' then '경북은 포항·구미 산업축, 안동·예천 행정수요, 경주 관광권이 서로 다르다. 단기 판단: 관망 우위. 대구경북신공항 기대는 장기 변수로 보되 단기 판단은 거래와 전세가 우선이다.'
            when target.display_name like '경상남도 창원시%' then '창원은 제조업 경기와 노후 주거지 정비가 같이 움직인다. 단기 판단: 선별 접근. 산업 회복이 전세 수요를 받쳐주면 긍정적이나 구축 정비 기대만으로는 부족하다.'
            when target.display_name like '경상남도 김해시%' or target.display_name like '경상남도 양산시%' then '김해·양산은 부산권 배후 주거와 자체 산업 수요가 섞인다. 단기 판단: 선별 관망. 부산 접근성 기대와 신규 공급 부담을 분리해야 한다.'
            when target.display_name like '경상남도 거제시%' or target.display_name like '경상남도 통영시%' then '거제·통영은 조선업과 관광 수요에 민감하다. 단기 판단: 보수적 관망. 업황 회복이 전세 안정으로 이어지는지 확인해야 한다.'
            when target.display_name like '경상남도%' then '경남은 창원 제조업, 김해·양산 부산 배후, 거제·통영 조선·관광권이 다르다. 단기 판단: 선별 관망. 광역 평균보다 산업과 전세 수요가 붙는 생활권을 먼저 봐야 한다.'
            when region.region_level = 'sido' then concat(target.display_name, '는 광역 평균만으로 판단하기 어려운 시장이다. 단기 판단: 관망 우위. 하위 시군구의 전세, 입주 물량, 산업 수요가 같은 방향인지 먼저 확인해야 한다.')
            when target.display_name like '%군' then concat(target.display_name, '는 거래 표본이 얇은 지역이다. 단기 판단: 보수적 관망. 가격 방향보다 실거래 빈도, 전세 수요, 인구 흐름 유지 여부가 핵심이다.')
            when target.display_name like '%구' then concat(target.display_name, '는 같은 광역시 안에서도 역세권, 학군, 신축 선호가 가격을 가른다. 단기 판단: 선별 관망. 단기 등락률보다 전세와 실거래가 함께 움직이는 단지를 봐야 한다.')
            else concat(target.display_name, '는 자체 생활권 수요와 상위 광역권 흐름을 분리해야 하는 시장이다. 단기 판단: 관망 우위. 개발 뉴스보다 전세, 거래 빈도, 입주 물량의 균형이 우선이다.')
        end as body,
        case
            when target.display_name like '서울특별시 서초구%' then '서리풀2지구 공급 시차'
            when target.display_name like '서울특별시%' then '전세 압력 지속'
            when target.display_name like '경기도 용인시 처인구%' then '국가산단 수요 전환'
            when target.display_name like '경기도 부천시%' then '정비·공급 동시 모멘텀'
            when target.display_name like '인천광역시 계양구%' then '계양테크노밸리 입주 흡수'
            when target.display_name like '충청남도 아산시%' then '탕정·배방 직주근접 수요'
            when target.display_name like '충청남도 천안시 서북구%' then '신축 전세 방어력'
            when target.display_name like '충청남도 천안시 동남구%' then '역세권·대학가 실거주 수요'
            when target.display_name like '충청남도 당진시%' then '제철·항만 고용 안정'
            when target.display_name like '충청남도 서산시%' then '대산 산업단지 배후 수요'
            when target.display_name like '충청남도%' then '천안·아산 전세 동행'
            when target.display_name like '부산광역시%' then '동부산 전세 회복'
            when target.display_name like '대구광역시%' then '미분양 축소 확인'
            when target.display_name like '세종특별자치시%' then '5생활권 공급 흡수'
            when target.display_name like '제주특별자치도%' then '상주 수요 회복'
            when target.display_name like '울산광역시%' then '산업 업황 전세 전환'
            when target.display_name like '전라남도 여수시%' or target.display_name like '전라남도 순천시%' or target.display_name like '전라남도 광양시%' then '산업단지 상주 수요'
            when target.display_name like '경상남도 창원시%' then '제조업 전세 수요'
            else '전세·실거래 동행'
        end as expectation_1,
        case
            when region.region_level = 'sido' then '하위 생활권 차별화'
            when target.display_name like '%군' then null
            when target.display_name like '서울특별시%' then '정비사업 일정 구체화'
            when target.display_name like '경기도%' or target.display_name like '인천광역시%' then '교통·산업축 실수요 확인'
            when target.display_name like '충청남도%' then '산업·행정 수요 확인'
            else '공급 일정 가시화'
        end as expectation_2,
        case
            when target.display_name like '서울특별시 서초구%' then '토지거래허가 부담'
            when target.display_name like '서울특별시%' then '기대 선반영 부담'
            when target.display_name like '경기도 용인시 처인구%' then '산업 뉴스 선반영 위험'
            when target.display_name like '경기도 부천시%' then '공급·정비 기대 충돌'
            when target.display_name like '인천광역시 계양구%' then '대규모 공급 흡수 부담'
            when target.display_name like '충청남도 아산시%' then '입주 물량 부담'
            when target.display_name like '충청남도 천안시 서북구%' then '신축 분양가 부담'
            when target.display_name like '충청남도 당진시%' then '산업 경기 의존도'
            when target.display_name like '충청남도%' then '광역 평균 착시'
            when target.display_name like '부산광역시%' then '개발 뉴스 선반영'
            when target.display_name like '대구광역시%' then '준공 후 미분양 부담'
            when target.display_name like '세종특별자치시%' then '공급 흡수 전 변동성'
            when target.display_name like '제주특별자치도%' then '관광 수요 과대평가'
            when target.display_name like '%군' then '거래 표본 부족'
            else '입주 물량 부담'
        end as concern_1,
        case
            when target.display_name like '%군' then null
            when region.region_level = 'sido' then '약한 하위 지역 잔존'
            when target.display_name like '서울특별시%' then '거래량 없는 신고가'
            when target.display_name like '경기도%' or target.display_name like '인천광역시%' then '입주 시점 전세 약세'
            when target.display_name like '충청남도%' then '축별 수요 편차'
            else '전세 약세 전이'
        end as concern_2,
        case
            when region.region_level = 'sido' then 0.83
            else 0.79
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
