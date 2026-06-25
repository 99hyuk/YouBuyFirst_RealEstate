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
    concat('regional-report-', rewritten.target_id, '-regional-assessment-20260625'),
    'regional-report-assessment-v4',
    'codex-regional-assessment-rewrite-prompt-20260625',
    'codex-gpt-5-regional-assessment',
    'codex-quality-rewrite:regional-assessment-20260625',
    concat(rewritten.display_name, ' 지역 평가 리포트'),
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
    '2026-06-25 03:20:00',
    coalesce(existing.created_at, '2026-06-25 03:20:00'),
    '2026-06-25 03:20:00'
from (
    select
        base.target_id,
        base.region_level,
        base.display_name,
        case
            when base.target_id = 'region-seoul' then '서울은 전세 압력과 핵심지 정비 기대가 가격 하방을 동시에 받치는 시장'
            when base.target_id = 'region-seoul-gangnam' then '강남구는 학군·업무·정비사업 프리미엄이 분리되는 초핵심 시장'
            when base.target_id = 'region-seoul-seocho' then '서초구는 서리풀2지구와 토지거래허가 부담을 함께 봐야 하는 시장'
            when base.target_id = 'region-seoul-songpa' then '송파구는 잠실 대장 단지와 가락·문정 실수요가 갈리는 동남권 시장'
            when base.target_id = 'region-seoul-yongsan' then '용산구는 개발 기대와 실입주 수요의 가격 간극이 큰 고가 시장'
            when base.target_id = 'region-seoul-mapo' then '마포구는 상암·공덕·홍대 업무·상권 수요가 분산된 강북 핵심지'
            when base.target_id = 'region-seoul-nowon' then '노원구는 노후 단지 정비 기대와 실수요 가격대가 충돌하는 시장'
            when base.target_id in ('region-gyeonggi', 'region-41000') then '경기도는 정비·신도시 공급·산업축을 분리해야 하는 광역 시장'
            when base.target_id = 'region-gyeonggi-yonginsicheoingu' then '용인 처인구는 반도체 국가산단 기대의 주거 수요 전환이 핵심'
            when base.target_id = 'region-gyeonggi-bucheon' then '부천은 부천대장 공급과 중동 정비 기대가 동시에 작동하는 시장'
            when base.target_id = 'region-incheon-gyeyang' then '계양구는 계양테크노밸리와 17천호 공급 흡수가 핵심인 시장'
            when base.display_name = '충청남도' then '충남은 천안·아산, 내포, 서해안 산업권을 분리해야 하는 광역 시장'
            when base.display_name like '충청남도 아산시%' then '아산은 탕정·배방 산업 배후와 천안 연계 수요가 가격을 가르는 시장'
            when base.display_name like '충청남도 천안시 서북구%' then '천안 서북구는 신축 선호와 수도권 남부 출퇴근 수요가 겹친 시장'
            when base.display_name like '충청남도 천안시 동남구%' then '천안 동남구는 원도심·대학·역세권 수요의 방어력 확인 구간'
            when base.display_name like '충청남도 당진시%' then '당진은 제철·항만 고용과 임대 수요가 가격 하방을 결정하는 시장'
            when base.display_name like '충청남도 서산시%' then '서산은 대산 산업단지와 자족 생활권 수요가 가격 설명력을 갖는 시장'
            when base.display_name like '충청남도 보령시%' then '보령은 해양관광 체류 수요와 상주 주거 수요를 분리해야 하는 시장'
            when base.display_name like '충청남도 공주시%' then '공주는 세종 배후 저가 수요와 대학·원도심 수요가 얇게 겹치는 시장'
            when base.display_name like '충청남도 계룡시%' then '계룡은 대전 배후와 군 주거 수요가 시장 규모를 정하는 소형 시장'
            when base.display_name like '충청남도 논산시%' then '논산은 국방·대학 임대 수요와 원도심 노후 주거가 공존하는 시장'
            when base.display_name like '충청남도 홍성군%' then '홍성은 내포 행정수요와 홍성 원도심 수요가 분리되는 시장'
            when base.display_name like '충청남도 예산군%' then '예산은 내포 배후 기대와 예산 원도심 유동성이 갈리는 시장'
            when base.display_name like '충청남도 태안군%' then '태안은 관광·세컨드하우스 수요와 상주 수요의 괴리가 큰 시장'
            when base.display_name like '충청남도 부여군%' then '부여는 백제문화 관광 수요보다 상주 인구와 거래 유동성이 중요한 시장'
            when base.display_name like '충청남도 서천군%' then '서천은 장항·군산 연계와 해안 생활권 수요가 제한적인 시장'
            when base.display_name like '충청남도 금산군%' then '금산은 대전권 배후와 농산업 수요가 얇게 작동하는 저유동성 시장'
            when base.display_name like '충청남도 청양군%' then '청양은 소형 정주 수요와 인구 감소 압력을 함께 봐야 하는 시장'
            when base.display_name like '부산광역시 해운대구%' then '해운대는 북항보다 동부산 고급 주거와 센텀 업무 수요가 직접 변수'
            when base.display_name like '부산광역시%' then '부산은 북항·가덕도 심리와 생활권별 전세 회복이 분리되는 시장'
            when base.display_name like '대구광역시 수성구%' then '수성구는 미분양 부담 속에서도 학군·핵심지 선호가 버티는 시장'
            when base.display_name like '대구광역시%' then '대구는 미분양과 준공 후 미분양 부담이 가격 상단을 제한하는 시장'
            when base.display_name like '세종특별자치시%' then '세종은 행정수도 기대와 5생활권 공급 흡수가 동시에 필요한 시장'
            when base.display_name like '제주특별자치도%' then '제주는 관광·이주 수요와 주택 통계 신호가 갈리는 시장'
            when base.display_name like '광주광역시%' then '광주는 첨단산단 기대와 생활권별 신축 수요가 분리되는 시장'
            when base.display_name like '대전광역시 유성구%' then '유성구는 연구개발 수요와 도안권 공급 부담이 함께 작동하는 시장'
            when base.display_name like '대전광역시%' then '대전은 유성·서구 중심 수요와 도안권 공급 부담을 같이 봐야 하는 시장'
            when base.display_name like '울산광역시%' then '울산은 자동차·조선·석유화학 업황이 주거 수요를 좌우하는 시장'
            when base.display_name like '강원도%' then '강원은 춘천·원주 상주 수요와 영동 관광 수요가 분리되는 시장'
            when base.display_name like '충청북도 청주시%' then '청주는 오송·오창 산업축과 도심 생활수요가 함께 작동하는 시장'
            when base.display_name like '충청북도%' then '충북은 청주권 산업 수요와 중부내륙 거래 깊이 차이가 큰 시장'
            when base.display_name like '전라북도 전주시%' then '전주는 전북 실거주 수요의 중심축'
            when base.display_name like '전라북도 군산시%' then '군산은 새만금·산단 기대의 주거 수요 전환 속도가 핵심인 시장'
            when base.display_name like '전라북도%' then '전북은 전주 생활수요와 새만금 산업 기대를 분리해야 하는 시장'
            when base.display_name like '전라남도 여수시%' or base.display_name like '전라남도 순천시%' or base.display_name like '전라남도 광양시%' then '여수·순천·광양권은 산업단지와 생활권 수요가 겹치는 전남 핵심축'
            when base.display_name like '전라남도%' then '전남은 산업도시·혁신도시·해안 관광권의 거래 성격이 분리되는 시장'
            when base.display_name like '경상북도 포항시%' then '포항은 철강·배터리 기대와 산업 경기 변동성이 공존하는 시장'
            when base.display_name like '경상북도 구미시%' then '구미는 전자·첨단산업 회복의 전세 전환이 핵심인 시장'
            when base.display_name like '경상북도%' then '경북은 포항·구미 산업축과 안동·예천 행정수요가 분리되는 시장'
            when base.display_name like '경상남도 창원시%' then '창원은 제조업 경기와 노후 주거지 정비가 함께 작동하는 시장'
            when base.display_name like '경상남도 김해시%' or base.display_name like '경상남도 양산시%' then '김해·양산은 부산권 배후 주거와 자체 산업 수요가 혼재된 시장'
            when base.display_name like '경상남도 거제시%' or base.display_name like '경상남도 통영시%' then '거제·통영은 조선업과 관광 수요에 민감한 해안 생활권'
            when base.display_name like '경상남도%' then '경남은 창원 제조업과 부산권 배후, 남해안 산업권이 분리되는 시장'
            when base.region_level = 'sido' then concat(base.display_name, '는 하위 생활권별 수급 차이가 큰 광역 시장')
            when base.display_name like '%군' then concat(base.local_name, ' 주택시장은 거래 표본과 상주 수요 확인이 우선인 저유동성 시장')
            when base.display_name like '%구' then concat(base.local_name, ' 주택시장은 역세권·학군·신축 선호가 가격을 가르는 세부 시장')
            else concat(base.local_name, ' 주택시장은 자체 생활권 수요와 광역 흐름을 함께 봐야 하는 시장')
        end as headline,
        '실거래·전세·공급·정책 변수를 지역별 평가와 전망으로 압축한 리포트입니다.' as summary,
        case
            when base.target_id = 'region-seoul' then '평가: 서울은 강남3구와 용산이 가격 발견을 주도하고, 전세 압력은 강북 노후 단지까지 하방을 받치는 구조다. 전망: 회복 가능성 우위. 다만 서리풀2지구 2,000호는 장기 공급 변수라 단기 가격 논리보다 착공·분양 일정 확인이 우선이다.'
            when base.target_id = 'region-seoul-gangnam' then '평가: 강남구는 대치·청담·삼성·개포·압구정이 각각 다른 가격표를 가진 시장이다. 전망: 방어력 우위. 학군·업무 접근성은 강하지만 전세가율, 토지거래허가, 정비사업 속도가 같이 확인돼야 한다.'
            when base.target_id = 'region-seoul-seocho' then '평가: 서초구는 서리풀2지구, 반포·잠원 정비 기대, 토지거래허가 부담이 공존한다. 전망: 선별 관망. 핵심 신축 방어력은 높지만 기대 선반영 구간은 전세 확인 없이는 부담이 커진다.'
            when base.target_id = 'region-seoul-songpa' then '평가: 송파구는 잠실 대장 단지와 가락·문정 실거주 수요가 다른 속도로 움직인다. 전망: 선별 회복 가능성. 주변 구축까지 실거래가 동행할 때 상승 신뢰도가 높아진다.'
            when base.target_id = 'region-seoul-yongsan' then '평가: 용산구는 국제업무지구와 한남·이촌 정비 기대가 강하지만 실입주 수요의 가격대가 얇다. 전망: 보수적 관망. 거래량 없이 기대만 오른 구간은 변동성 확대 위험이 크다.'
            when base.target_id = 'region-seoul-mapo' then '평가: 마포구는 상암·공덕·홍대 수요가 분산된 시장이고, 강남권 대체재 논리는 공덕·아현 전세와 상암 업무 수요가 같이 버틸 때 유효하다. 전망: 선별 회복 가능성. 확인 지표는 전세 방어와 직주근접 거래 반복이다.'
            when base.target_id = 'region-seoul-nowon' then '평가: 노원구는 노후 단지 비중이 높고 재건축 기대와 실수요 가격대가 충돌하는 시장이다. 전망: 관망 우위. 전세가 먼저 회복되지 않으면 정비 기대만으로 매매 회복을 설명하기 어렵다.'
            when base.target_id in ('region-gyeonggi', 'region-41000') then '평가: 경기도는 1기 신도시 정비, 3기 신도시, 용인 반도체가 각각 다른 수급 경로를 만든다. 전망: 선별 회복 가능성. 서울 대체재, 산업 배후, 교통 기대 지역을 한 결론으로 묶으면 판단이 흐려진다.'
            when base.target_id = 'region-gyeonggi-yonginsicheoingu' then '평가: 용인 처인구는 첨단시스템반도체 국가산단 이슈가 핵심 프리미엄이지만, 산업 뉴스가 곧바로 주거 수요로 전환되지는 않는다. 전망: 선별 관망. 원삼·남사 전세와 입주 흡수가 먼저 확인돼야 한다.'
            when base.target_id = 'region-gyeonggi-bucheon' then '평가: 부천은 부천대장 공급과 중동 1기 신도시 정비가 동시에 작동한다. 전망: 보수적 선별. 새 아파트 선호와 구축 재건축 프리미엄이 충돌해 생활권 내부 격차가 커질 수 있다.'
            when base.target_id = 'region-incheon-gyeyang' then '평가: 계양구는 계양테크노밸리와 17천호 공급이 함께 들어오는 구간이다. 전망: 보수적 관망. 서울 접근성보다 입주 시점 전세 방어와 검단·부천대장 수요 중복이 더 중요하다.'
            when base.display_name = '충청남도' then '평가: 충남은 천안·아산의 수도권 남부 수요, 내포 행정수요, 당진·서산의 서해안 산업축이 분리되는 시장이다. 전망: 선별 관망. 광역 평균보다 축별 전세 방어와 실거래 반복 여부가 가격 판단의 핵심이다.'
            when base.display_name like '충청남도 아산시%' then '평가: 아산은 천안과 붙어 있는 수요, 탕정·배방 산업 배후, 새 아파트 선호가 핵심이다. 전망: 선별 회복 가능성. 입주 물량이 겹치면 전세가 먼저 압박받으므로 전세 방어가 확인되는 단지만 프리미엄 유지력이 있다.'
            when base.display_name like '충청남도 천안시 서북구%' then '평가: 천안 서북구는 불당·성성·두정 신축 선호와 수도권 남부 출퇴근 수요가 가격을 만든다. 전망: 회복 가능성 우위. 다만 신축 분양가와 전세가 벌어지면 상승 지속성은 약해진다.'
            when base.display_name like '충청남도 천안시 동남구%' then '평가: 천안 동남구는 원도심, 대학가, 역세권 수요가 중심이고 서북구 신축 흐름을 그대로 따라가기 어렵다. 전망: 관망 우위. 저가 실거주와 정비 기대가 실제 거래로 반복되는지 확인해야 한다.'
            when base.display_name like '충청남도 당진시%' then '평가: 당진은 제철·항만 산업 경기와 임대 수요가 가격 하방을 결정한다. 전망: 보수적 관망. 산업 회복은 긍정적이나 고용 확인 전 산업 뉴스만으로 상승 지속성을 보기 어렵다.'
            when base.display_name like '충청남도 서산시%' then '평가: 서산은 대산 산업단지와 자족 생활권이 가격을 설명한다. 전망: 선별 관망. 산업 배후 수요가 뚜렷한 단지와 외곽 택지의 거래 깊이를 분리해야 한다.'
            when base.display_name like '충청남도 보령시%' then '평가: 보령은 해양관광 체류 수요가 있으나 상주 수요의 두께는 제한적이다. 전망: 보수적 관망. 관광 뉴스보다 연중 전세 수요와 실거래 반복성이 가격 방어력을 좌우한다.'
            when base.display_name like '충청남도 공주시%' then '평가: 공주는 세종 배후 저가 수요와 대학·원도심 수요가 얇게 겹친다. 전망: 관망 우위. 세종 접근성 기대만으로는 부족하고 대학가 임대와 원도심 거래 회복이 같이 확인돼야 한다.'
            when base.display_name like '충청남도 계룡시%' then '평가: 계룡은 대전 배후 주거와 군 주거 수요가 시장 규모를 정하는 소형 시장이다. 전망: 선별 관망. 공급이 조금만 늘어도 전세가 흔들릴 수 있어 유동성 확인이 먼저다.'
            when base.display_name like '충청남도 논산시%' then '평가: 논산은 국방·대학 임대 수요가 방어 요인이지만 원도심 노후 주거 비중이 높다. 전망: 보수적 관망. 임대 수요가 매매 회복으로 전환되는 속도는 느리게 보는 편이 맞다.'
            when base.display_name like '충청남도 홍성군%' then '평가: 홍성은 내포 행정수요가 장점이지만 홍성 원도심과 내포 신축의 가격 논리가 다르다. 전망: 관망 우위. 전세 공실과 입주 흡수 속도 확인 전까지 회복 판단은 보수적이다.'
            when base.display_name like '충청남도 예산군%' then '평가: 예산은 내포 배후 기대가 있으나 예산 원도심 거래 유동성은 얇다. 전망: 관망 우위. 행정수요가 실제 전세와 매매 거래로 반복되는지가 핵심이다.'
            when base.display_name like '충청남도 태안군%' then '평가: 태안은 관광·세컨드하우스 수요가 가격 기대를 만들 수 있지만 상주 수요는 얇다. 전망: 보수적 관망. 성수기 분위기보다 연중 거래 빈도와 임대 안정성이 우선이다.'
            when base.display_name like '충청남도 부여군%' then '평가: 부여는 백제문화 관광 수요가 보조 변수지만 주택시장은 상주 인구와 거래 유동성이 더 중요하다. 전망: 보수적 관망. 고령화와 얇은 거래 표본이 가격 회복 속도를 제한한다.'
            when base.display_name like '충청남도 서천군%' then '평가: 서천은 장항·군산 연계 수요가 있으나 자체 주거 수요의 깊이는 제한적이다. 전망: 보수적 관망. 산업·해안 이슈보다 전세 유지와 실거래 빈도 확인이 우선이다.'
            when base.display_name like '충청남도 금산군%' then '평가: 금산은 대전권 배후와 농산업 수요가 얇게 작동하는 시장이다. 전망: 보수적 관망. 외부 수요 유입보다 인구 흐름과 전세 유지가 가격 방어의 핵심이다.'
            when base.display_name like '충청남도 청양군%' then '평가: 청양은 소형 정주 수요가 중심이고 거래 표본이 얇아 가격 발견력이 낮다. 전망: 보수적 관망. 인구 감소 압력과 거래 공백이 이어지면 회복 신호가 늦게 나타난다.'
            when base.display_name like '부산광역시 해운대구%' then '평가: 해운대는 북항 이슈보다 해운대·센텀·마린시티의 전세 회복과 고가 주거 선호가 직접 변수다. 전망: 선별 회복 가능성. 해안 고가 단지와 내륙 구축의 격차가 커질 수 있다.'
            when base.display_name like '부산광역시%' then '평가: 부산은 북항·가덕도 기대가 도시 심리를 만들지만 가격은 해운대·수영·동래, 원도심, 서부산이 다르게 움직인다. 전망: 선별 관망. 개발 뉴스보다 전세 회복과 입주 물량 충돌이 중요하다.'
            when base.display_name like '대구광역시 수성구%' then '평가: 수성구는 대구 미분양 부담 속에서도 학군·핵심지 선호가 남아 있다. 전망: 보수적 선별. 수성구 프리미엄은 전세가 회복되는 신축·준신축에서만 방어력이 높다.'
            when base.display_name like '대구광역시%' then '평가: 대구는 미분양과 준공 후 미분양 부담이 아직 가격 상단을 제한한다. 전망: 관망 우위. 핵심지 회복과 외곽 공급지 조정이 동시에 나타날 가능성이 높다.'
            when base.display_name like '세종특별자치시%' then '평가: 세종은 행정수도 기대와 5생활권 공급 흡수가 동시에 확인돼야 한다. 전망: 관망 우위. 정책 기대만 앞서면 변동성이 커지고, 입주 흡수가 확인되면 회복 논리가 생긴다.'
            when base.display_name like '제주특별자치도%' then '평가: 제주는 관광 회복, 이주 수요, 주택 통계가 서로 다른 신호를 낸다. 전망: 보수적 관망. 제주시와 서귀포·읍면을 섞어 보면 표본 착시가 커진다.'
            when base.display_name like '광주광역시%' then '평가: 광주는 첨단산단과 도심 정비 기대가 있지만 생활권별 차이가 크다. 전망: 선별 관망. 광산·북구 신축 수요와 동구·남구 정비 기대를 분리해야 한다.'
            when base.display_name like '대전광역시 유성구%' then '평가: 유성구는 연구개발, 대학, 도안권 공급이 가격을 설명한다. 전망: 선별 회복 가능성. 좋은 입지라도 입주 물량이 겹치면 전세가 먼저 약해질 수 있다.'
            when base.display_name like '대전광역시%' then '평가: 대전은 유성·서구 중심 수요와 동구·대덕 정비·산업 수요가 다르다. 전망: 선별 관망. 세종 연계 기대는 보조 변수이고 실제 판단은 전세와 입주 물량에 둬야 한다.'
            when base.display_name like '울산광역시%' then '평가: 울산은 자동차·조선·석유화학 업황이 주거 수요를 직접 흔든다. 전망: 선별 회복 가능성. 산업 회복이 전세 수요로 확인되면 긍정적이나 단일 기업 뉴스만으로는 부족하다.'
            when base.display_name like '강원도%' then '평가: 강원은 춘천·원주의 상주 수요와 강릉·속초의 관광 수요가 다르다. 전망: 보수적 관망. 세컨드하우스 분위기보다 연중 전세 수요와 거래 빈도를 확인해야 한다.'
            when base.display_name like '충청북도 청주시%' then '평가: 청주는 오송·오창 산업축과 도심 생활수요가 충북에서 가장 두껍다. 전망: 선별 회복 가능성. 산업 기대가 강할수록 분양가와 입주 물량도 같이 올라오므로 전세 방어가 우선이다.'
            when base.display_name like '충청북도%' then '평가: 충북은 청주권 산업 수요와 충주·제천·군 단위 생활권의 거래 깊이가 다르다. 전망: 관망 우위. 산업 뉴스가 약한 지역은 가격보다 거래 빈도와 전세 안정성이 더 중요하다.'
            when base.display_name like '전라북도 전주시%' then '평가: 전주는 전북 실거주 수요의 중심이다. 전망: 선별 관망. 새만금 기대를 전주 가격에 바로 붙이기보다 혁신도시·도심·신축 선호의 전세 확인이 필요하다.'
            when base.display_name like '전라북도 군산시%' then '평가: 군산은 새만금과 산업단지 기대가 있지만 주택 수요 전환에는 시간이 걸린다. 전망: 보수적 관망. 산업 뉴스보다 고용과 임대 수요가 먼저 움직이는지 확인해야 한다.'
            when base.display_name like '전라북도%' then '평가: 전북은 전주 실거주, 군산·익산 산업축, 새만금 기대가 다르게 작동한다. 전망: 관망 우위. 개발 기대보다 실제 거래와 전세 회복이 붙은 곳을 따로 봐야 한다.'
            when base.display_name like '전라남도 여수시%' or base.display_name like '전라남도 순천시%' or base.display_name like '전라남도 광양시%' then '평가: 여수·순천·광양권은 산업단지와 생활권 수요가 전남에서 가장 뚜렷하다. 전망: 선별 회복 가능성. 산업 경기와 상주 수요가 같이 받쳐주는 단지의 방어력이 높다.'
            when base.display_name like '전라남도%' then '평가: 전남은 산업도시, 혁신도시, 해안 관광권의 거래 성격이 서로 다르다. 전망: 보수적 관망. 군 단위는 한두 건의 실거래보다 인구와 임대 수요를 더 보수적으로 봐야 한다.'
            when base.display_name like '경상북도 포항시%' then '평가: 포항은 철강·배터리 기대가 있지만 산업 경기 변동에 민감하다. 전망: 선별 관망. 일자리 회복이 전세와 거래 수요로 같이 확인될 때 의미가 있다.'
            when base.display_name like '경상북도 구미시%' then '평가: 구미는 전자·첨단산업 기반이 강하지만 경기 변동에 민감하다. 전망: 선별 관망. 공장 증설 뉴스보다 임대 수요와 전입 흐름이 먼저 확인돼야 한다.'
            when base.display_name like '경상북도%' then '평가: 경북은 포항·구미 산업축, 안동·예천 행정수요, 경주 관광권이 서로 다르다. 전망: 관망 우위. 대구경북신공항 기대는 장기 변수로 보되 단기 판단은 거래와 전세가 우선이다.'
            when base.display_name like '경상남도 창원시%' then '평가: 창원은 제조업 경기와 노후 주거지 정비가 같이 움직인다. 전망: 선별 회복 가능성. 산업 회복이 전세 수요를 받쳐주면 긍정적이나 구축 정비 기대만으로는 부족하다.'
            when base.display_name like '경상남도 김해시%' or base.display_name like '경상남도 양산시%' then '평가: 김해·양산은 부산권 배후 주거와 자체 산업 수요가 섞인다. 전망: 선별 관망. 부산 접근성 기대와 신규 공급 부담을 분리해야 한다.'
            when base.display_name like '경상남도 거제시%' or base.display_name like '경상남도 통영시%' then '평가: 거제·통영은 조선업과 관광 수요에 민감하다. 전망: 보수적 관망. 업황 회복이 전세 안정으로 이어지는지 확인해야 한다.'
            when base.display_name like '경상남도%' then '평가: 경남은 창원 제조업, 김해·양산 부산 배후, 거제·통영 조선·관광권이 다르다. 전망: 선별 관망. 광역 평균보다 산업과 전세 수요가 붙는 생활권을 먼저 봐야 한다.'
            when base.region_level = 'sido' then concat('평가: ', base.display_name, ' 주택시장은 광역 평균만으로 판단하기 어려운 시장이다. 전망: 관망 우위. 하위 시군구의 전세, 입주 물량, 산업 수요가 같은 방향인지 먼저 확인해야 한다.')
            when base.display_name like '%군' then concat('평가: ', base.local_name, ' 주택시장은 거래 표본이 얇고 상주 수요 확인이 우선이다. 전망: 보수적 관망. 가격 방향보다 실거래 빈도, 전세 수요, 인구 흐름 유지 여부가 핵심이다.')
            when base.display_name like '%구' then concat('평가: ', base.local_name, ' 주택시장은 같은 광역시 안에서도 역세권, 학군, 신축 선호가 가격을 가른다. 전망: 선별 관망. 단기 등락률보다 전세와 실거래가 함께 움직이는 단지를 봐야 한다.')
            else concat('평가: ', base.local_name, ' 주택시장은 자체 생활권 수요와 상위 광역권 흐름을 분리해야 하는 시장이다. 전망: 관망 우위. 개발 뉴스보다 전세, 거래 빈도, 입주 물량의 균형이 우선이다.')
        end as body,
        case
            when base.display_name like '서울특별시 서초구%' then '서리풀2지구 공급 시차'
            when base.display_name like '서울특별시%' then '전세 압력 지속'
            when base.display_name like '경기도 용인시 처인구%' then '국가산단 수요 전환'
            when base.display_name like '경기도 부천시%' then '정비·공급 동시 모멘텀'
            when base.display_name like '인천광역시 계양구%' then '계양테크노밸리 입주 흡수'
            when base.display_name like '충청남도 아산시%' then '탕정·배방 직주근접 수요'
            when base.display_name like '충청남도 천안시 서북구%' then '신축 전세 방어력'
            when base.display_name like '충청남도 천안시 동남구%' then '역세권·대학가 실거주 수요'
            when base.display_name like '충청남도 당진시%' then '제철·항만 고용 안정'
            when base.display_name like '충청남도 서산시%' then '대산 산단 배후 수요'
            when base.display_name like '충청남도 보령시%' then '해양관광 체류 수요'
            when base.display_name like '충청남도 공주시%' then '세종 배후 저가 수요'
            when base.display_name like '충청남도 계룡시%' then '대전 배후 군 주거'
            when base.display_name like '충청남도 논산시%' then '국방·대학 임대 수요'
            when base.display_name like '충청남도 홍성군%' then '내포 행정수요 흡수'
            when base.display_name like '충청남도 예산군%' then '내포 배후 정주 수요'
            when base.display_name like '충청남도 태안군%' then '관광 체류 수요'
            when base.display_name like '충청남도 부여군%' then '백제문화 관광 수요'
            when base.display_name like '충청남도 서천군%' then '장항·군산 연계 수요'
            when base.display_name like '충청남도 금산군%' then '대전권 농산업 배후'
            when base.display_name like '충청남도 청양군%' then '소형 정주 수요'
            when base.display_name like '부산광역시%' then '동부산 전세 회복'
            when base.display_name like '대구광역시%' then '미분양 축소 확인'
            when base.display_name like '세종특별자치시%' then '5생활권 공급 흡수'
            when base.display_name like '제주특별자치도%' then '상주 수요 회복'
            when base.display_name like '울산광역시%' then '산업 업황 전세 전환'
            when base.display_name like '전라남도 여수시%' or base.display_name like '전라남도 순천시%' or base.display_name like '전라남도 광양시%' then '산업단지 상주 수요'
            when base.display_name like '경상남도 창원시%' then '제조업 전세 수요'
            when base.region_level = 'sido' then concat(base.local_name, ' 생활권 차별화')
            when base.display_name like '%군' then concat(base.local_name, ' 거래 회복 확인')
            when base.display_name like '%구' then concat(base.local_name, ' 전세 방어 확인')
            else concat(base.local_name, ' 실거래 회복')
        end as expectation_1,
        case
            when base.region_level = 'sido' then '하위 생활권 차별화'
            when base.display_name like '%군' then null
            when base.display_name like '서울특별시%' then '정비사업 일정 구체화'
            when base.display_name like '경기도%' or base.display_name like '인천광역시%' then '교통·산업축 실수요 확인'
            when base.display_name like '충청남도%' then concat(base.local_name, ' 전세 유지')
            else concat(base.local_name, ' 공급 일정 확인')
        end as expectation_2,
        case
            when base.display_name like '서울특별시 서초구%' then '토지거래허가 부담'
            when base.display_name like '서울특별시%' then '기대 선반영 부담'
            when base.display_name like '경기도 용인시 처인구%' then '산업 뉴스 선반영 위험'
            when base.display_name like '경기도 부천시%' then '공급·정비 기대 충돌'
            when base.display_name like '인천광역시 계양구%' then '대규모 공급 흡수 부담'
            when base.display_name like '충청남도 아산시%' then '입주 물량 부담'
            when base.display_name like '충청남도 천안시 서북구%' then '신축 분양가 부담'
            when base.display_name like '충청남도 천안시 동남구%' then '원도심 회복 지연'
            when base.display_name like '충청남도 당진시%' then '산업 경기 의존도'
            when base.display_name like '충청남도 서산시%' then '외곽 택지 유동성 부족'
            when base.display_name like '충청남도 보령시%' then '상주 수요 부족'
            when base.display_name like '충청남도 공주시%' then '원도심 거래 얇음'
            when base.display_name like '충청남도 계룡시%' then '소형 시장 유동성'
            when base.display_name like '충청남도 논산시%' then '노후 주거 비중'
            when base.display_name like '충청남도 홍성군%' then '내포 공급 흡수 부담'
            when base.display_name like '충청남도 예산군%' then '원도심 유동성 부족'
            when base.display_name like '충청남도 태안군%' then '관광 수요 과대평가'
            when base.display_name like '충청남도 부여군%' then '고령화·거래 부족'
            when base.display_name like '충청남도 서천군%' then '자체 수요 한계'
            when base.display_name like '충청남도 금산군%' then '외부 유입 제한'
            when base.display_name like '충청남도 청양군%' then '인구 감소 압력'
            when base.display_name like '부산광역시%' then '개발 뉴스 선반영'
            when base.display_name like '대구광역시%' then '준공 후 미분양 부담'
            when base.display_name like '세종특별자치시%' then '공급 흡수 전 변동성'
            when base.display_name like '제주특별자치도%' then '관광 수요 과대평가'
            when base.display_name like '%군' then concat(base.local_name, ' 유동성 부족')
            when base.display_name like '%구' then concat(base.local_name, ' 신축·구축 격차')
            else concat(base.local_name, ' 입주·전세 부담')
        end as concern_1,
        case
            when base.display_name like '%군' then null
            when base.region_level = 'sido' then '약한 하위 지역 잔존'
            when base.display_name like '서울특별시%' then '거래량 없는 신고가'
            when base.display_name like '경기도%' or base.display_name like '인천광역시%' then '입주 시점 전세 약세'
            when base.display_name like '충청남도%' then concat(base.local_name, ' 수요 편차')
            else concat(base.local_name, ' 전세 약세 전이')
        end as concern_2,
        case
            when base.region_level = 'sido' then 0.84
            else 0.80
        end as confidence
    from (
        select
            region.target_id,
            region.region_level,
            target.display_name,
            replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(target.display_name,
                '서울특별시 ', ''),
                '부산광역시 ', ''),
                '대구광역시 ', ''),
                '인천광역시 ', ''),
                '광주광역시 ', ''),
                '대전광역시 ', ''),
                '울산광역시 ', ''),
                '세종특별자치시 ', ''),
                '경기도 ', ''),
                '강원도 ', ''),
                '충청북도 ', ''),
                '충청남도 ', ''),
                '전라북도 ', ''),
                '전라남도 ', ''),
                '경상북도 ', ''),
                '경상남도 ', ''),
                '제주특별자치도 ', '') as local_name
        from real_estate_regions region
        join real_estate_targets target on target.id = region.target_id
        where region.region_level in ('sido', 'sigungu')
    ) base
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
