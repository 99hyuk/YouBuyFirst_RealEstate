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
    concat('regional-report-', region.target_id, '-deep-seoul-20260624'),
    'regional-report-deep-research-v1',
    'codex-seoul-deep-research-prompt-20260624',
    'codex-gpt-5-deep-research',
    'codex-deep-research:seoul-20260624',
    concat(target.display_name, ' 심화 지역 리포트'),
    case region.target_id
        when 'region-seoul' then '서울은 공급 부족과 전세 압력, 규제지역 효과가 동시에 걸린 초양극화 시장입니다.'
        when 'region-seoul-seocho' then '서초는 서리풀2지구 공급 뉴스와 반포·잠원 정비 기대가 같은 화면에 있는 핵심 관찰지입니다.'
        when 'region-seoul-mapo' then '마포는 상암·공덕·홍대 축이 강남권 대체재 논리와 정비사업 리스크를 동시에 만듭니다.'
        when 'region-seoul-nowon' then '노원은 재건축 기대와 실수요 가격대가 충돌하는 강북권 최대 노후 단지 관찰지입니다.'
        else concat(target.display_name, '는 서울 전체 공급·전세·정비사업 구도 안에서 따로 읽어야 하는 생활권입니다.')
    end,
    case region.target_id
        when 'region-seoul' then '서울 전체 판단은 강남3구·용산의 가격 발견, 강북 전세 압력, 서울시 정비사업 속도전, 토지거래허가구역 효과를 한 번에 엮어야 합니다.'
        when 'region-seoul-mapo' then '마포는 도심 접근성과 서부권 업무·문화 수요가 강하지만, 정비구역별 속도와 전세 부담을 분리해야 합니다.'
        when 'region-seoul-seocho' then '서초는 서리풀2지구 2,000호 공급이 단기 가격 안정책이라기보다 장기 공급 신호라는 점을 봐야 합니다.'
        when 'region-seoul-nowon' then '노원은 강북권 전세 상승과 노후 단지 재건축 기대가 매수 전환 심리를 자극할 수 있지만 사업성 검증이 핵심입니다.'
        else concat(target.display_name, '는 서울권 전세 강세, 정비사업 공급, 토지거래허가 규제의 영향을 각 생활권 수요와 함께 해석해야 합니다.')
    end,
    case region.target_id
        when 'region-seoul' then concat(
            '서울 전체 리포트의 결론은 단순한 상승 또는 하락이 아니라 초양극화의 재배치입니다. KB경영연구소가 2026년 주택시장의 핵심 변수로 서울 아파트 매매 수요, 월세화, 공급시장 위축, 노후 아파트 정비시장, 정책 방향을 함께 제시한 이유가 여기 있습니다. ',
            '금융권 리포트가 말하는 2026년 서울의 핵심은 매매 수요가 사라진 것이 아니라 규제와 대출 한도 안에서 더 선별적으로 움직인다는 점입니다. 강남3구와 용산의 가격 발견은 토지거래허가와 세제 변수에 먼저 반응하고, 강북·노원·도봉·성북 같은 지역은 전세 부족과 가격대 매력이 매수 전환 압력으로 이어질 수 있습니다. ',
            'KB Think는 2026년 1월부터 5월까지 서울 아파트 평균 전세가격이 3.49% 올랐고 강북·성북·노원·도봉 등 강북 지역 전셋값 상승률이 5% 이상이었다고 설명합니다. KDI 국내연구자료도 수도권 전세 강세와 월세 비중 확대, 공급 인허가 부진과 사업장별 일정 불확실성을 함께 지적합니다. ',
            '공급 측면에서는 서울시가 신속통합기획 2.0과 2031년 31만 호 착공, 2035년 약 37.7만 호 준공을 내세우지만, 실제 체감 공급은 인허가, 이주, 조합 의사결정, 공사비를 지나야 합니다. 서리풀2지구 2,000호처럼 확정적인 공공주택 뉴스도 가격을 바로 누르는 물량이 아니라 2028년 착공 목표의 장기 공급 신호로 해석해야 합니다. ',
            '따라서 서울의 기대 지점은 정비사업 속도전과 전세 압력이 만들어내는 선호 입지의 방어력입니다. 우려 지점은 규제 완화 기대, 토지거래허가구역 해제 또는 연장 기대, 단기 신고가가 실제 거주 수요보다 먼저 가격에 반영되는 것입니다. 지도 기간별 등락률은 색상과 숫자 판단에만 쓰고, 이 심화 리포트는 정책·금융권 분석·구별 정비 이슈가 갱신될 때 최신본으로 다시 교체해야 합니다.'
        )
        when 'region-seoul-jongno' then concat(
            '종로는 광화문·종각·대학로·북촌의 업무·관광·문화 수요가 공존하지만, 주거지는 넓게 확장되기 어렵습니다. 서울 전체 전세 강세가 도심 접근 수요를 밀어 올릴 수 있으나, 종로의 핵심은 대규모 신축 공급보다 낡은 도심 주거지와 상업지 사이의 희소성입니다. ',
            'KB 2026 보고서의 월세화·공급 위축 이슈를 종로에 적용하면, 매매보다 임대차 구조 변화가 먼저 체감될 가능성이 큽니다. 정비사업은 문화재·경관·상업지 이해관계 때문에 속도가 일정하지 않아 단일 호재처럼 쓰기 어렵습니다. ',
            '기대 지점은 도심 직주근접 수요와 관광 회복에 따른 상권 안정입니다. 우려 지점은 상권 뉴스가 주거 실수요로 과장되고, 소규모 거래가 가격 방향처럼 읽히는 것입니다.'
        )
        when 'region-seoul-jung' then concat(
            '중구는 서울 도심 업무지구와 명동·을지로·동대문 상권이 겹치지만 주거 재고는 제한적인 권역입니다. 서울 전체 공급 부족과 월세화 흐름은 중구에서 주거 선택지 부족으로 더 직접적으로 나타납니다. ',
            '이 지역은 CBD 회복, 호텔·상업 수요, 노후 도심 정비가 함께 움직입니다. 다만 상업용 부동산 회복을 아파트 매매 수요로 그대로 옮겨 해석하면 안 됩니다. ',
            '기대 지점은 희소한 도심 주거와 직주근접입니다. 우려 지점은 생활형 숙박·상권 이슈와 실제 거주 선호가 다르게 움직일 수 있다는 점입니다.'
        )
        when 'region-seoul-yongsan' then concat(
            '용산은 국제업무지구, 한강변 주거 선호, 미군기지 반환부지 기대가 겹친 서울의 대표 가격 발견 지역입니다. 강남3구와 함께 정책과 규제 변화에 가장 먼저 반응하는 구간이어서, 토지거래허가구역과 세제 변수의 해석이 중요합니다. ',
            'KB 보고서가 말한 서울 아파트 매매 수요 변화는 용산에서 고자산가 선별 수요와 공급 희소성으로 나타납니다. 다만 대형 개발은 사업 기간이 길고, 기대가 거래가에 선반영되기 쉽습니다. ',
            '기대 지점은 한강·도심·광역개발의 희소 조합입니다. 우려 지점은 개발 일정 지연과 규제지역 프리미엄의 과잉 반영입니다.'
        )
        when 'region-seoul-seongdong' then concat(
            '성동은 성수·왕십리·서울숲·한강변 수요가 결합한 대표적인 한강벨트 확장 지역입니다. 업무·상권·주거 선호가 같이 붙기 때문에 강남권 대체재로 읽히지만, 이미 가격 기대가 상당 부분 반영된 구간도 많습니다. ',
            '서울시 정비사업 속도전은 성동의 노후 주거지와 준공업·상업지 재편 기대를 키우지만, 토지 가격과 공사비 부담은 사업성을 압박합니다. ',
            '기대 지점은 성수 업무지구화와 한강 접근성입니다. 우려 지점은 상권 인기와 실거주 가치가 같은 속도로 가지 않을 수 있다는 점입니다.'
        )
        when 'region-seoul-gwangjin' then concat(
            '광진은 건대입구·자양·구의·광장 생활권을 통해 강남 접근성과 한강 동부권 주거 수요를 동시에 갖습니다. 서울 전세 강세가 중상급지 대체 수요를 밀어 올릴 때 광진은 성동·송파 사이의 완충지로 움직일 수 있습니다. ',
            '다만 광진은 대규모 신축 공급이 넉넉하지 않고, 동별 주거 품질 차이가 커서 평균 지표만으로 판단하기 어렵습니다. ',
            '기대 지점은 강남 접근성과 한강 동부권 입지입니다. 우려 지점은 개발 호재보다 단지별 연식과 학군·교통 차이가 더 크게 작동하는 점입니다.'
        )
        when 'region-seoul-dongdaemun' then concat(
            '동대문은 청량리 광역환승, 이문·휘경 정비사업, 대학가 임대 수요가 함께 놓입니다. 서울 공급 부족 국면에서 동북권 신축·준신축 선택지가 늘어나는 구간이지만, 입주 물량과 정비 속도에 따라 체감은 다를 수 있습니다. ',
            'KB의 공급시장 위축 프레임을 적용하면 동대문은 서울 안에서 상대적으로 공급 후보가 보이는 지역입니다. 그래서 가격 기대보다 입주 이후 전세 흡수력을 먼저 봐야 합니다. ',
            '기대 지점은 청량리 중심성 회복과 정비사업 물량입니다. 우려 지점은 신규 공급이 한꺼번에 체감될 때 전세가 먼저 흔들릴 수 있다는 점입니다.'
        )
        when 'region-seoul-jungnang' then concat(
            '중랑은 상봉·망우 교통축과 면목 일대 정비 기대가 핵심입니다. 서울 전세 강세가 외곽 실수요를 자극할 때 중랑은 가격대 접근성 때문에 관심을 받을 수 있습니다. ',
            '그러나 중랑의 리포트는 개발 기대보다 주거 품질 개선 속도와 교통 체감 시간을 봐야 합니다. 모아타운·소규모 정비는 기대가 빠르지만 실제 주택 재고를 바꾸는 데 시간이 걸립니다. ',
            '기대 지점은 상봉 교통 거점과 중저가 실수요입니다. 우려 지점은 정비사업 초기 기대가 거래가격에 먼저 반영될 가능성입니다.'
        )
        when 'region-seoul-seongbuk' then concat(
            '성북은 길음·장위 뉴타운, 돈암·정릉·월곡 생활권, 대학가 수요가 섞인 강북 핵심 주거지입니다. KB Think가 언급한 강북권 전세 강세는 성북에서 매수 전환 압력으로 번질 수 있습니다. ',
            '다만 성북은 신축 선호 단지와 노후 구릉지 주거지가 강하게 갈립니다. 서울시 신속통합기획과 정비사업 속도전의 수혜를 말하려면 구역별 단계와 이주 리스크를 따로 봐야 합니다. ',
            '기대 지점은 강북권 실수요와 정비사업 누적입니다. 우려 지점은 전세 상승만 보고 매매 회복을 단정할 수 없다는 점입니다.'
        )
        when 'region-seoul-gangbuk' then concat(
            '강북은 미아·수유 중심의 가격대 접근성과 북서울 생활권 정비 기대가 핵심입니다. 서울 전체 공급 부족과 전세 상승이 실수요를 밀어 올릴 수 있지만, 소득·대출 한도가 더 민감하게 작용하는 지역입니다. ',
            '노후 주거지 개선은 분명한 기대 요인입니다. 그러나 정비사업은 구역 지정과 조합 단계에서 시간이 걸리고, 공사비 부담이 사업성을 흔들 수 있습니다. ',
            '기대 지점은 실수요 가격대와 정비 여지입니다. 우려 지점은 금융 규제와 전세 부담이 동시에 커질 때 매수 전환이 제한될 수 있다는 점입니다.'
        )
        when 'region-seoul-dobong' then concat(
            '도봉은 창동·상계 광역중심, GTX-C 기대, 강북권 가격대 접근성이 맞물리는 지역입니다. 서울 전세 강세가 계속되면 도봉은 임차 수요의 매수 전환 후보가 될 수 있습니다. ',
            '다만 도봉은 교통 호재의 실현 시점과 노후 단지 정비 속도가 가격 설명의 대부분입니다. 기대는 크지만 시간이 길어질수록 금융비용과 생활 인프라 체감이 변수로 남습니다. ',
            '기대 지점은 창동 중심지 재편과 저평가 인식입니다. 우려 지점은 호재 시간표가 길어질 때 단기 가격만 앞설 수 있다는 점입니다.'
        )
        when 'region-seoul-nowon' then concat(
            '노원은 서울 최대급 노후 아파트 밀집지라는 사실 하나만으로도 2026년 서울 리포트에서 따로 봐야 합니다. 최근 기사들은 중계그린 추진위 승인, 상계보람 정비계획 통과, 미미삼 정비구역 지정 기대처럼 노후 단지 재건축이 본격 궤도에 오르는 흐름을 전합니다. ',
            'KB Think가 지적한 강북·성북·노원·도봉 전세 상승은 노원에서 특히 중요합니다. 전세 부담이 커지면 중저가 대단지의 매수 전환이 빨라질 수 있지만, 재건축 기대와 실수요 가격대가 동시에 뛰면 실거주자의 부담도 커집니다. ',
            '따라서 노원의 기대 지점은 재건축 기대와 실수요 가격대가 만나는 점입니다. 우려 지점은 사업성 개선 기대가 실제 조합 단계, 이주, 공사비 검증보다 먼저 가격화되는 것입니다. 노후 단지 리포트는 반드시 단지별 연식, 용적률, 추진 단계와 함께 봐야 합니다.'
        )
        when 'region-seoul-eunpyeong' then concat(
            '은평은 수색·증산, 불광·연신내, 은평뉴타운이 서로 다른 시장을 만듭니다. GTX-A와 서북권 교통 기대는 장기 변수이고, 서울 전세 강세는 실수요 가격대의 방어력을 높일 수 있습니다. ',
            '하지만 은평은 도심 접근성 개선 기대와 실제 통근 시간이 체감에서 다르게 나타날 수 있습니다. 뉴타운과 원도심의 주거 품질 차이도 큽니다. ',
            '기대 지점은 서북권 교통 개선과 실수요 기반입니다. 우려 지점은 교통 호재가 이미 가격에 반영됐는지 확인해야 한다는 점입니다.'
        )
        when 'region-seoul-seodaemun' then concat(
            '서대문은 가재울·북아현·홍제·연희 생활권이 도심 접근성과 대학가 수요를 공유합니다. 서울 공급 부족 국면에서 도심 가까운 준신축과 정비 후보지는 꾸준히 관찰할 필요가 있습니다. ',
            '다만 서대문은 언덕 지형과 단지별 입지 차이가 커서 구 평균 지표가 사용자를 속일 수 있습니다. 정비사업은 생활권을 바꿀 수 있지만, 사업 단계별 불확실성을 분리해야 합니다. ',
            '기대 지점은 도심 접근성과 정비사업 누적입니다. 우려 지점은 지역 내 입지 격차가 크다는 점입니다.'
        )
        when 'region-seoul-mapo' then concat(
            '마포는 상암·공덕·홍대 세 축을 동시에 봐야 합니다. 상암은 DMC 업무와 미디어 산업, 공덕은 여의도·광화문 접근, 홍대는 문화상권과 임대 수요가 중심입니다. 이 조합 때문에 마포는 강남권 대체재 또는 도심 대체 주거지로 자주 읽히지만, 실제 가격은 축별로 다르게 움직입니다. ',
            '마포구 2026년 주요업무계획은 공동주택 230개 단지 7만7566세대, 주택정비사업 현황 19개소, 도화우성 추진위 구성 지원, 염리5구역 정비구역 지정 추진, 망원·아현 신통기획 후보지 정비계획 수립을 제시합니다. 즉 마포는 이미 성숙한 인기 주거지인 동시에 아직 정비 파이프라인이 남아 있는 지역입니다. ',
            '기대 지점은 상암·공덕·홍대 수요가 전세와 매매를 동시에 받치는 점입니다. 우려 지점은 상권 인기와 정비사업 기대가 강남권 대체재라는 말로 과장될 수 있다는 점입니다. 마포는 단기 신고가보다 축별 전세, 정비구역 단계, 신축 입주 일정을 나눠 봐야 합니다.'
        )
        when 'region-seoul-yangcheon' then concat(
            '양천은 목동 재건축과 학군 수요가 거의 모든 설명의 중심입니다. 서울 노후 아파트 정비시장 확대라는 KB 보고서의 이슈가 가장 직접적으로 적용되는 구 중 하나입니다. ',
            '다만 목동 재건축 기대는 이미 오랫동안 가격에 반영되어 왔고, 안전진단·정비계획·이주·공사비 단계가 모두 남아 있습니다. 신월·신정 생활권은 목동과 다른 가격대·수요를 보입니다. ',
            '기대 지점은 학군과 재건축 희소성입니다. 우려 지점은 목동 기대가 양천 전체 가격 판단으로 번지는 것입니다.'
        )
        when 'region-seoul-gangseo' then concat(
            '강서는 마곡 R&D·업무지구, 김포공항, 가양·등촌·방화 노후 주거지가 함께 움직입니다. 서울 서부권에서 일자리와 주거가 함께 있는 드문 구간이라는 점은 기대 요인입니다. ',
            '한겨레 보도처럼 강남3구·용산·한강벨트의 가격 흐름이 조정될 때 노원·강서 등 외곽 실수요 지역은 다른 흐름을 보일 수 있습니다. 그러나 강서는 신규 입주와 노후 단지의 품질 차이가 크기 때문에 평균 지표만 보면 안 됩니다. ',
            '기대 지점은 마곡 일자리와 서부권 교통입니다. 우려 지점은 외곽 실수요 회복을 개발 기대와 혼동하는 것입니다.'
        )
        when 'region-seoul-guro' then concat(
            '구로는 G밸리 업무수요, 구로·신도림 교통, 서남권 가격대 접근성이 핵심입니다. 서울 전세 강세가 이어질 때 구로는 실수요자의 대안 지역으로 기능할 수 있습니다. ',
            '다만 구로는 업무지구 인접성과 주거 선호가 동별로 크게 다릅니다. 낡은 주거지의 정비 속도와 신도림·구로디지털단지 접근성을 분리해야 합니다. ',
            '기대 지점은 일자리 접근성과 가격대입니다. 우려 지점은 직장 수요가 곧바로 매매 수요로 전환된다고 볼 수 없다는 점입니다.'
        )
        when 'region-seoul-geumcheon' then concat(
            '금천은 가산디지털단지와 독산·시흥 생활권이 중심입니다. 구로와 함께 서남권 일자리 접근성은 강하지만, 서울 평균 선호 입지와의 격차도 동시에 존재합니다. ',
            '공급 부족과 전세 상승은 금천의 가격 방어력을 높일 수 있습니다. 그러나 매매 회복은 교통·주거환경 개선과 함께 확인해야 합니다. ',
            '기대 지점은 G밸리 배후수요와 상대적 가격 접근성입니다. 우려 지점은 업무지구 임대수요와 가족 단위 주거 선호가 다를 수 있다는 점입니다.'
        )
        when 'region-seoul-yeongdeungpo' then concat(
            '영등포는 여의도 금융업무지구, 문래 준공업지역, 신길·당산 주거지가 한 구 안에서 서로 다른 리포트를 요구합니다. 서울시의 용적률·정비사업 속도전은 준공업지역 재편 기대와 연결됩니다. ',
            '여의도 업무 수요는 강하지만 주거 시장은 여의도, 당산, 신길, 대림이 다르게 움직입니다. 업무지구 호재와 주거 선호를 같은 방향으로 단정하면 안 됩니다. ',
            '기대 지점은 금융업무지구와 정비사업 파이프라인입니다. 우려 지점은 준공업지역 개발 기대가 실제 주거 공급으로 연결되기까지 시간이 필요하다는 점입니다.'
        )
        when 'region-seoul-dongjak' then concat(
            '동작은 흑석·노량진·사당을 통해 강남, 용산, 여의도 사이의 연결 입지를 갖습니다. 서울 전세 강세가 도심 접근형 중상급지로 번질 때 동작은 꾸준한 관찰 대상입니다. ',
            '다만 흑석과 노량진 정비 기대는 이미 가격에 반영된 구간이 있고, 사당·상도 생활권은 다른 가격대와 수요를 보입니다. ',
            '기대 지점은 강남·용산·여의도 접근성입니다. 우려 지점은 정비사업 기대와 실제 입주 시점의 간격입니다.'
        )
        when 'region-seoul-gwanak' then concat(
            '관악은 서울대·신림·봉천 생활권, 청년·1인가구 임대수요, 신림선 이후 교통 개선 기대가 핵심입니다. 서울 전세와 월세화 흐름은 관악에서 임대차 부담으로 먼저 나타날 가능성이 큽니다. ',
            '재개발 기대는 있지만 구릉지·노후주거·소형주택 비중 때문에 사업성이 구역마다 다릅니다. 단기 가격보다 임대차 안정과 정비구역 진척을 함께 봐야 합니다. ',
            '기대 지점은 청년 임대수요와 가격대 접근성입니다. 우려 지점은 월세화가 주거비 부담을 키울 수 있다는 점입니다.'
        )
        when 'region-seoul-seocho' then concat(
            '서초는 반포·잠원·서초·방배의 고가 주거 수요와 우면·내곡·염곡의 공공택지·녹지 이슈가 동시에 존재합니다. 국토교통부는 서초구 우면동 일원 서울 서리풀2지구 2,000호 공공주택지구 지정과 2028년 착공 목표를 발표했습니다. ',
            '이 뉴스는 서초 가격을 단기적으로 누르는 재료라기보다 강남권 공급 부족 논리에 대한 장기 보완 신호입니다. 동시에 서울부동산정보광장의 토지거래허가구역 현황은 강남·서초 자연녹지지역과 재건축 단지 규제가 여전히 시장 해석의 핵심임을 보여줍니다. ',
            '기대 지점은 최상급 주거 선호, 학군, 정비사업 희소성입니다. 우려 지점은 서리풀2지구와 토지거래허가 이슈가 단기 매매 판단으로 과장되는 것입니다. 서초는 공급 뉴스와 고가 주거 수요를 반드시 시간축으로 분리해야 합니다.'
        )
        when 'region-seoul-gangnam' then concat(
            '강남은 대치·청담·삼성·개포·압구정으로 나뉘는 서울의 가격 발견 중심입니다. KB 보고서가 말하는 서울 아파트 매매 수요 변화, 정책 방향, 노후 아파트 정비시장의 확대가 가장 먼저 가격에 반영되는 곳입니다. ',
            '그러나 강남은 토지거래허가구역, 세제, 대출 규제, 정비사업 인허가가 모두 가격에 개입합니다. 강남3구와 용산의 가격 변동은 서울 전체 심리를 움직이지만, 실제 매수 가능 수요는 더 얇고 선별적입니다. ',
            '기대 지점은 대체 불가능한 학군·업무·자산 선호입니다. 우려 지점은 신고가와 정책 기대가 실수요 체력보다 앞설 수 있다는 점입니다.'
        )
        when 'region-seoul-songpa' then concat(
            '송파는 잠실 재건축, 가락·문정 업무, 위례·거여마천 생활권이 함께 있는 동남권 핵심지입니다. 강남과 같이 토지거래허가구역과 정비사업 규제가 시장 심리를 크게 좌우합니다. ',
            '잠실권은 서울 가격 발견에 민감하지만, 송파 전체는 신축·재건축·동남권 업무수요가 섞여 평균 지표로 설명하기 어렵습니다. ',
            '기대 지점은 잠실의 상징성과 동남권 업무·교통 기반입니다. 우려 지점은 재건축 기대가 규제와 공사비 앞에서 지연될 수 있다는 점입니다.'
        )
        when 'region-seoul-gangdong' then concat(
            '강동은 둔촌·고덕·강일·암사 생활권이 다르게 움직입니다. 대규모 입주를 경험한 지역이라 서울 공급 부족 논리를 그대로 적용하기보다 입주 이후 전세 안정, 고덕 업무·산업 접근성, 동남권 확장을 함께 봐야 합니다. ',
            '서울 전체 전세 강세 속에서도 강동은 단지별 입주 연식과 공급 흡수 속도에 따라 체감이 갈릴 수 있습니다. ',
            '기대 지점은 고덕·강일 신축축과 동남권 확장성입니다. 우려 지점은 대규모 입주 영향과 주변 공급이 전세·매매를 다르게 흔들 수 있다는 점입니다.'
        )
        else concat(
            target.display_name, '는 서울 전체 공급 부족과 전세 압력 안에서 세부 생활권을 따로 봐야 합니다. ',
            'KB 2026 보고서의 서울 아파트 매매 수요 변화, 월세화, 공급시장 위축, 노후 정비시장 확대라는 프레임을 적용하되, 구별 정비사업 단계와 실제 전세 수급을 분리해야 합니다. ',
            '기대 지점은 서울 안의 희소한 생활권 수요이고, 우려 지점은 단기 뉴스가 가격 결론으로 과장되는 것입니다.'
        )
    end,
    case region.target_id
        when 'region-seoul' then '["강남3구·용산의 가격 발견과 강북 전세 압력을 나눠 보면 서울 시장의 양극화 구조를 더 정확히 읽을 수 있습니다.","서울시 신속통합기획 2.0과 2031년 31만 호 착공 목표는 장기 공급 기대를 만드는 핵심 근거입니다.","전세 상승과 월세화가 실수요 매수 전환을 자극하는지 구별로 확인할 수 있습니다."]'
        when 'region-seoul-seocho' then '["서리풀2지구 2,000호는 강남권 공급 부족 논리를 완화할 장기 신호입니다.","반포·잠원·방배의 최상급 주거 선호는 서울 핵심 수요를 계속 붙잡습니다.","공공택지와 재건축 근거를 분리하면 단기 과열과 장기 공급을 따로 볼 수 있습니다."]'
        when 'region-seoul-mapo' then '["상암·공덕·홍대의 업무·문화·교통 축이 서로 다른 수요층을 만듭니다.","마포구 정비사업 파이프라인은 성숙지 안에서도 추가 주거 개선 여지를 보여줍니다.","강남권 대체재 논리를 전세·정비 단계와 함께 검증할 수 있습니다."]'
        when 'region-seoul-nowon' then '["노후 단지 재건축 기대와 실수요 가격대가 동시에 작동합니다.","강북권 전세 상승은 노원 대단지의 매수 전환 압력을 키울 수 있습니다.","중계·상계·월계 단지별 추진 단계가 쌓이면 강북 정비시장 대표 관찰지가 됩니다."]'
        else concat('["', target.display_name, '는 서울 공급 부족과 전세 압력 안에서 생활권 수요를 확인할 수 있습니다.","정비사업 단계와 임대차 지표를 함께 보면 단기 기사보다 설명력이 높아집니다.","서울시 공급 속도전과 금융권 시장 전망을 같은 근거 묶음으로 볼 수 있습니다."]')
    end,
    case region.target_id
        when 'region-seoul' then '["토지거래허가구역과 세제 변수는 거래량과 가격을 동시에 왜곡할 수 있습니다.","정비사업 착공 목표는 장기 공급 신호이지 즉시 입주 물량이 아닙니다.","강북 전세 강세를 서울 전체 매매 상승 결론으로 단정하면 안 됩니다."]'
        when 'region-seoul-seocho' then '["토지거래허가와 고가 주거 수요가 거래량을 얇게 만들 수 있습니다.","서리풀2지구는 2028년 착공 목표라 단기 입주 물량으로 해석하면 안 됩니다.","반포·잠원 신고가를 서초 전체의 즉시 방향으로 일반화하면 위험합니다."]'
        when 'region-seoul-mapo' then '["상암·공덕·홍대의 수요 성격이 달라 구 평균 지표가 실제 체감을 가릴 수 있습니다.","정비사업 기대가 강남권 대체재 서사로 과장될 수 있습니다.","상권 인기와 주거 실수요를 같은 흐름으로 단정하지 않아야 합니다."]'
        when 'region-seoul-nowon' then '["재건축 기대가 조합·이주·공사비 검증보다 먼저 가격화될 수 있습니다.","전세 상승이 실수요 부담을 키워 매수 전환을 제한할 수도 있습니다.","노후 단지 전체를 같은 사업성으로 묶으면 오판하기 쉽습니다."]'
        else concat('["', target.display_name, '의 단기 등락을 서울 전체 방향으로 확대 해석하면 안 됩니다.","정비사업 후보지와 실제 착공 가능 물량은 시간차가 큽니다.","전세·월세 부담이 매수 전환으로 이어지는지 실거래로 확인해야 합니다."]')
    end,
    'deep_researched',
    case when region.region_level = 'sido' then 0.86 else 0.82 end,
    '2026-06-24 00:00:00',
    '2026-06-24 23:30:00',
    coalesce(existing.created_at, '2026-06-24 23:30:00'),
    '2026-06-24 23:30:00'
from real_estate_regions region
join real_estate_targets target on target.id = region.target_id
left join real_estate_regional_reports existing on existing.target_id = region.target_id
where region.target_id = 'region-seoul'
   or region.parent_region_id = 'region-seoul'
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
    where target_id = 'region-seoul'
       or parent_region_id = 'region-seoul'
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
select concat('regional-report-source-', region.target_id, '-seoul-01-kb-report'), region.target_id, 1, 'external', 'kb-2026-real-estate-report', '금융권 리포트', '2026 KB 부동산 보고서', 'https://www.kbfg.com/kbresearch/brand/brandView.do?reportId=2000492', 'KB경영연구소', '2026-05-05 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-02-kb-issues'), region.target_id, 2, 'external', 'kb-2026-seven-housing-issues', '금융권 핵심 이슈', 'KB금융 2026 부동산 보고서 발간 공지', 'https://www.kbfg.com/kbresearch/notice/noticeView.do?noticeId=2000141', 'KB경영연구소', '2026-05-05 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-03-kb-jeonse'), region.target_id, 3, 'external', 'kbthink-2026-h1-housing-market', '전세·청약 분석', 'KB의 생각 2026년 상반기 부동산 시장 총정리', 'https://kbthink.com/realestate/issue/hosing-260611.html', 'KB Think', '2026-06-11 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-04-kdi-market'), region.target_id, 4, 'external', 'kdi-2026-q1-real-estate-market', '시장 동향', 'KDI 경제정보센터 2026년 1분기 부동산시장동향', 'https://eiec.kdi.re.kr/policy/domesticView.do?ac=0000204646&depth1=&issus=&pg=&pp=&search_txt=&type=', 'KDI 경제정보센터', '2026-06-01 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-05-shintong'), region.target_id, 5, 'external', 'seoul-housing-shintong-2', '서울시 공급정책', '서울주거포털 신속통합기획 2.0', 'https://housing.seoul.go.kr/site/main/content/sh_080001', '서울특별시', null, 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-06-execution'), region.target_id, 6, 'external', 'seoul-housing-redevelopment-execution-2026', '정비사업 실행력', '서울주거포털 정비사업 실행력·공정관리 보도자료', 'https://housing.seoul.go.kr/site/main/tvReportedInfo/list?performanceType=01', '서울특별시', '2026-06-01 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-07-land-permit'), region.target_id, 7, 'external', 'seoul-land-transaction-permit-2026', '규제 근거', '서울부동산정보광장 토지거래허가구역 지정현황', 'https://land.seoul.go.kr/land/other/appointStatusSeoul.do', '서울특별시', '2026-03-12 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-08-seoripul2'), region.target_id, 8, 'external', 'molit-seoripul2-2000-units-20260611', '공급 근거', '국토교통부 서울 서초에 공공주택 2,000호 공급 추진', 'https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95092096&lcmspage=1', '국토교통부', '2026-06-11 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-09-rone'), region.target_id, 9, 'external', 'reb-rone-2026-05-national-housing-price-trend', '공식 가격지표', '한국부동산원 R-ONE 2026년 5월 전국주택가격동향', 'https://www.reb.or.kr/r-one/portal/main/indexPage.do', '한국부동산원', '2026-06-15 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-10-nowon'), region.target_id, 10, 'external', 'news-nowon-reconstruction-20260604', '구별 이슈', '외면받던 노원 재건축, 강북 정비사업 최대 격전지 될까', 'https://v.daum.net/v/20260604151704740?f=p', '뉴스1', '2026-06-04 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul'
union all
select concat('regional-report-source-', region.target_id, '-seoul-11-mapo'), region.target_id, 11, 'external', 'mapo-2026-main-business-plan', '구별 정비 근거', '마포구 2026년도 주요업무 계획', 'https://council.mapo.seoul.kr/record/appendixDownload.do?key=45280eb4321f8af67dd34fb5983674db681742583320259dbb959e67193ca769d02f2a9002da5860', '마포구', '2026-02-01 00:00:00', 'ok', '2026-06-24 23:30:00', '2026-06-24 23:30:00'
from real_estate_regions region
where region.target_id = 'region-seoul' or region.parent_region_id = 'region-seoul';
