# 부동산 커뮤니티/source 후보

작성일: 2026-06-11

## 결론

부동산 반응 수집은 처음부터 30개 adapter를 만들지 않는다.

먼저 공개 접근성이 높고 글 흐름이 빠른 게시판형 source 2-3곳을 P0로 검증하고, 규모가 큰 네이버/다음 카페와 앱 커뮤니티는 `disabled` 또는 `local-research-only` 상태로 source registry에 올린 뒤 공개 목록 접근성, robots/약관, 로그인 필요 여부를 확인한다.

초기 운영 기준:

1. P0: 공개 게시판형 최신글 목록을 확인할 수 있는 source
2. P1: 이용자 규모나 영향력은 크지만 카페/앱/로그인 검증이 필요한 source
3. P2: 뉴스, 컬럼, 앱 정보, 공공/시장 fact처럼 반응 분석을 보조하는 source

이 문서는 "수집 승인 목록"이 아니라 "후보 목록"이다. `crawlPolicyCandidate`가 `public-http-candidate`여도 adapter 구현 전에는 source별 정책 검토가 필요하다.

## 분산성 검토

사용자의 "부동산 커뮤니티는 주식보다 특정 커뮤니티 한 곳에 덜 몰려 있을 것 같다"는 가설은 현재 확인 가능한 공개 근거 기준으로는 맞는 방향이다. 다만 아직 전체 글 수를 source별로 센 것이 아니므로 통계적 확정이 아니라 제품/수집 설계 가설로 둔다.

판단 근거:

1. 부동산은 대상 자체가 종목 코드처럼 하나의 표준 namespace로 묶이지 않는다. 지역, 단지, 생활권, 학군, 전세, 청약, 재건축, 경매, 상가, 정책처럼 관심 단위가 나뉜다.
2. 대형 전국 카페만 보아도 부동산스터디, 피터팬, 아름다운 내집갖기, 월급쟁이부자들, 행복재테크처럼 목적과 이용자층이 다르다.
3. 네이버는 지역 기반 카페 이용 증가와 지역 단위 카페 노출을 별도 기능으로 설명했다. 부동산 체감 반응은 이런 지역/맘카페 층에 많이 묻힐 가능성이 크다.
4. 호갱노노처럼 단지 실거주 후기와 앱 내부 커뮤니티가 따로 존재한다. 이는 투자 커뮤니티와 다른 신호다.
5. 뽐뿌, 디시인사이드, 블라인드처럼 일반 게시판형 source에도 부동산 전용 흐름이 있다.
6. 반대로 주식은 커뮤니티가 늘었어도 "종목토론방"이라는 강한 공통 패턴이 있다. 2024년 기사 기준 네이버페이 증권 종목토론실은 국내 최대 증권 커뮤니티로 월간 이용자와 일 게시물 수가 매우 크고, 토스증권 커뮤니티도 같은 종목토론방 구조로 경쟁한다.

따라서 부동산은 "대표 커뮤니티 몇 개의 언급량"보다 "source category coverage"를 먼저 봐야 한다. 화면과 지표에서도 단순 언급량보다 다음 값을 함께 저장해야 한다.

| 필드 | 이유 |
| --- | --- |
| `sourceCategory` | 전국 투자 카페, 지역/맘카페, 일반 게시판, 앱 후기, 뉴스/컬럼을 분리 |
| `geoScope` | 전국, 시도, 시군구, 읍면동, 단지 단위 신호를 구분 |
| `topicScope` | 전세, 매매, 청약, 재건축, 교통, 학군, 정책, 경매 등 관심사를 구분 |
| `sourceSkew` | 한 source에 몰린 급증을 시장 전체 관심처럼 보이지 않게 함 |
| `coverageStatus` | 공개 접근 실패, 로그인 필요, 정책 차단, 부분 수집을 화면 caveat로 연결 |

## 1차 공개 접근성 점검

2026-06-11에 대표 후보 URL과 robots.txt를 직접 확인했다. 아래 결과는 "접근 가능성 점검"이지 "수집 승인"이 아니다.

| sourceId | 페이지 확인 | robots/정책 단서 | 1차 판단 |
| --- | --- | --- | --- |
| `ppomppu_house` | 모바일 부동산포럼 목록 HTTP 200, 제목/목록 확인 | `Crawl-delay: 1`, 부동산포럼 목록은 명시 차단 목록에 없음 | P0 parser spike 가능. 지연 준수와 낮은 빈도 필요 |
| `dc_immovables` | PC 부동산 갤러리 목록 HTTP 200, 글번호/작성일/조회/추천 확인 | `User-agent: *`는 Allow지만 AI bot 차단과 개별 차단 경로 존재 | P0 후보 유지. 정책 리뷰 후 목록 중심 저빈도 수집만 검토 |
| `hogangnono_community` | 커뮤니티 페이지 HTTP 200 | robots 첫 줄에서 명시적 허가 없는 crawling 금지 고지 | 자동 수집 제외. 링크/수동 조사/제휴 후보 |
| `blind_realestate_topic` | 부동산 토픽 HTTP 200 | 일반 history 경로 외 대부분 공개이나 AI bot 차단, 앱/로그인 의존성 큼 | 자동 수집 제외에 가깝다. 공개 링크 연구 후보 |
| `naver_cafe_sources` | 카페 robots 확인 | `User-agent: * Disallow: /` | 자동 수집 제외. 공식 API/허가/수동 조사 없이는 adapter 금지 |
| `daum_cafe_sources` | 카페 robots 확인 | PC `_c21_/bbs_list`, `_c21_/bbs_read` 등 일부 Allow. 모바일은 다수 관리 경로 Disallow | source별 공개 게시판이면 검토 가능. 개별 카페 단위 확인 필요 |
| `asil_app` | 사이트/앱 정보 확인 | robots에서 일반 bot `Disallow: /`, 일부 검색봇만 Allow | 자동 수집 제외. 앱/시장 fact 연구 후보 |

## 우선 검증 후보

| sourceId | 이름 | 유형 | 후보 정책 | 신호 | 우선순위 | 확인 근거 |
| --- | --- | --- | --- | --- | --- | --- |
| `ppomppu_house` | 뽐뿌 부동산포럼 | 공개 게시판 | `public-http-candidate` | 내집마련, 계약, 이사, 대출, 전세 이슈 | P0 | 공식 목록에 부동산포럼과 최신글 노출 |
| `dc_immovables` | 디시인사이드 부동산 갤러리 | 공개 게시판 | `public-http-candidate` | 빠른 감정 반응, 지역/정책 논쟁, 과열/우려 신호 | P0 | 공식 갤러리 목록에 게시글 번호, 작성일, 조회/추천 노출. 정책 리뷰 필요 |
| `hogangnono_community` | 호갱노노 이야기 | 앱/웹 커뮤니티 | `local-research-only` | 실거주 후기, 아파트 단지 단위 체감 | P1 | 공식 커뮤니티 페이지와 직방 보도자료에서 이야기 탭 운영 확인. robots상 자동 수집 제외 |
| `blind_realestate_topic` | 블라인드 부동산 토픽 | 직장인 커뮤니티 | `local-research-only` | 직장인 실수요, 고소득권역, 대출/갈아타기 고민 | P1 | 공개 토픽 페이지와 게시글 일부 확인. 앱/로그인 의존성 검토 필요 |
| `naver_boodongsan_study` | 부동산스터디 | 네이버 카페 | `disabled` | 시장 심리, 정책 반응, 지역별 논쟁 | P1 | 언론에서 대형 부동산 카페 영향력과 회원 규모 언급 |
| `naver_peterpanz` | 피터팬의 좋은방 구하기 | 네이버 카페/앱 | `disabled` | 전월세, 직거래, 거주 후기, 임차 수요 | P1 | 카페 회원 300만 돌파와 거주/거래 후기 제공 언급 |
| `naver_rainup` | 아름다운 내집갖기 | 네이버 카페 | `disabled` | 내집마련, 재테크, 지역/단지 관심 | P1 | 카페 소개와 100만 회원 관련 공개 근거 확인 |
| `wolbu_cafe` | 월급쟁이부자들 | 네이버 카페/교육 커뮤니티 | `disabled` | 투자 학습 커뮤니티, 유튜브/카페 기반 관심 흐름 | P1 | 2026년 언론에서 유튜브 210만, 온라인 카페 64만 언급 |
| `daum_happytech` | 행복재테크 | 다음 카페 | `disabled` | 경매, 공매, 재테크, 투자자 반응 | P1 | 다음 프리미엄 우수카페 선정과 회원 규모 관련 언론 근거 |
| `asil_app` | 아실 | 앱/웹 정보 서비스 | `local-research-only` | 실거래, 순위, 개발정보, 사용자 관심 지역 | P2 | Google Play/App Store 설명에서 다운로드와 기능 확인 |

## 30개 seed 후보

아래 목록은 source registry에 먼저 `disabled` 또는 `local-research-only`로 넣을 seed 후보입니다. `public-http-candidate`는 parser spike 후보일 뿐이고, adapter 활성화 전에는 board별 robots/약관과 저장 범위를 다시 확인해야 합니다.

| # | sourceId | 이름 | URL | 분류 | 1차 접근성 | 우선순위 | 쓰임 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `ppomppu_house` | 뽐뿌 부동산포럼 | https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1 | general_board | `public-http-candidate` | P0 | 전세, 대출, 계약, 실수요 고민 |
| 2 | `dc_immovables` | 디시인사이드 부동산 갤러리 | https://gall.dcinside.com/board/lists/?id=immovables | general_board | `public-http-candidate` | P0 | 빠른 감정 반응, 과열/우려 신호 |
| 3 | `blind_realestate_topic` | 블라인드 부동산 토픽 | https://www.teamblind.com/kr/topics/%EB%B6%80%EB%8F%99%EC%82%B0 | general_board | `local-research-only` | P1 | 직장인 실수요, 갈아타기, 대출 고민 |
| 4 | `clien_park_realestate` | 클리앙 모두의공원 부동산 글 | https://m.clien.net/service/board/park | general_board | `public-http-review` | P2 | 정책/시장 일반 여론 보조 |
| 5 | `theqoo_realestate_posts` | 더쿠 부동산 관련 공개글 | https://theqoo.net/stock | general_board | `public-http-review` | P2 | 2030 체감, 정책/거주 팁 보조 |
| 6 | `cook82_freeboard_realestate` | 82cook 자유게시판 부동산 글 | https://www.82cook.com/entiz/enti.php?bn=15 | general_board | `public-http-review` | P2 | 전월세, 생활형 실거주 고민 |
| 7 | `hogangnono_community` | 호갱노노 이야기 | https://hogangnono.com/community | proptech_review | `excluded-permission-required` | P1 | 단지 실거주 후기, 지역 경험 |
| 8 | `hogangnono_expert_columns` | 호갱노노 전문가 칼럼 | https://hogangnono.com/community/expert-columns | news_content | `excluded-permission-required` | P2 | 정책/시장 해설 링크 근거 |
| 9 | `naver_boodongsan_study` | 부동산스터디 | https://cafe.naver.com/jaegebal | national_investment | `excluded-naver-cafe` | P1 | 전국 투자 심리, 정책 반응 |
| 10 | `naver_peterpanz` | 피터팬의 좋은방 구하기 | https://cafe.naver.com/kig | national_investment | `excluded-naver-cafe` | P1 | 전월세, 직거래, 거주 후기 |
| 11 | `naver_rainup` | 아름다운 내집갖기 | https://cafe.naver.com/rainup | national_investment | `excluded-naver-cafe` | P1 | 내집마련, 임차/매도자 반응 |
| 12 | `naver_wolbu` | 월급쟁이부자들 | https://cafe.naver.com/wecando7 | national_investment | `excluded-naver-cafe` | P1 | 임장, 투자 학습, 지역 분석 |
| 13 | `daum_happytech` | 행복재테크 | https://cafe.daum.net/happy-tech | national_investment | `daum-cafe-review` | P1 | 경매, 공매, 투자자 경험 |
| 14 | `naver_ishift` | 내집장만 아카데미 | https://cafe.naver.com/ishift | national_investment | `excluded-naver-cafe` | P1 | 청약, 공공분양, 신혼부부 주거 |
| 15 | `naver_bsinveststory` | 투자놀이터 | https://cafe.naver.com/bsinveststory | national_investment | `excluded-naver-cafe` | P2 | 토지, 특수경매, 투자자 담론 |
| 16 | `naver_arcadestudy` | 살모사의 커피하우스 | https://cafe.naver.com/arcadestudy | national_investment | `excluded-naver-cafe` | P2 | 상가, 건물, 고액 투자 담론 |
| 17 | `naver_bujilearn` | 부룡/부동산 노포 관련 카페 | https://cafe.naver.com/bujilearn | national_investment | `excluded-naver-cafe` | P2 | 가치투자, 시장 해설 |
| 18 | `naver_2008bunsamo` | 분따 - 분당·판교·위례 따라잡기 | https://cafe.naver.com/2008bunsamo | local_living | `excluded-naver-cafe` | P1 | 분당/판교/위례 생활권, 학군, 실거주 |
| 19 | `naver_dongtanmom` | 동탄맘들 모여라 | https://cafe.naver.com/dongtanmom | local_living | `excluded-naver-cafe` | P1 | 동탄 생활권, 신도시 수요 |
| 20 | `naver_dongtantwomom` | 동탄2신도시맘 | https://cafe.naver.com/dongtantwomom | local_living | `excluded-naver-cafe` | P1 | 동탄2 생활권, 입주/학군 |
| 21 | `naver_bbbx` | 송파맘·위례맘홀릭 | https://cafe.naver.com/bbbx | local_living | `excluded-naver-cafe` | P1 | 송파/위례 생활권 |
| 22 | `naver_school_bundang` | 분당 학군지 카페 후보 | https://cafe.naver.com/endudfun | local_living | `excluded-naver-cafe` | P2 | 학군지 수요 신호 |
| 23 | `naver_school_mokdong` | 목동 학군지 카페 후보 | https://cafe.naver.com/studymokdong | local_living | `excluded-naver-cafe` | P2 | 목동 학군/전세 수요 |
| 24 | `naver_school_gwanggyo` | 광교 학군지 카페 후보 | https://cafe.naver.com/greatgwanggyo | local_living | `excluded-naver-cafe` | P2 | 광교 생활권/학군 |
| 25 | `naver_school_songdo` | 송도신도시 학군지 카페 후보 | https://cafe.naver.com/songdoeduall | local_living | `excluded-naver-cafe` | P2 | 송도 신도시/학군 |
| 26 | `naver_school_sejong` | 세종신도시 학군지 카페 후보 | https://cafe.naver.com/sjmaengmo | local_living | `excluded-naver-cafe` | P2 | 세종 생활권/학군 |
| 27 | `asil_app` | 아실 | https://asil.kr/ | official_data | `excluded-robots-blocked` | P2 | 실거래, 순위, 개발정보 참고 |
| 28 | `aptgin` | 부동산지인 | https://aptgin.com/ | official_data | `local-research-only` | P2 | 지역/거래량/아파트 TOP 흐름 |
| 29 | `richgo` | 리치고 | https://m.richgo.ai/ | official_data | `local-research-only` | P2 | 학군, 청약, 개발정보, 통계 |
| 30 | `kb_land_datahub` | KB부동산 데이터허브 | https://data.kbland.kr/ | official_data | `official-data-candidate` | P0 | 주간/월간 가격지수, 매매/전세 지표 |
| 31 | `reb_rone` | 한국부동산원 R-ONE | https://www.reb.or.kr/r-one/portal/main/indexPage.do | official_data | `official-data-candidate` | P0 | 가격지수, 거래현황, 공표 일정 |
| 32 | `data_go_apt_trade` | 국토교통부 아파트 매매 실거래가 API | https://www.data.go.kr/data/15126469/openapi.do | official_data | `official-api-candidate` | P0 | 실거래 fact |
| 33 | `r114` | 부동산R114 | https://r114.com/ | news_content | `local-research-only` | P2 | 시세/분양/입주 분석 |
| 34 | `ddangzipgo` | 땅집고 | https://realty.chosun.com/ | news_content | `link-snippet-only` | P2 | 정책/개발/지역 뉴스 |
| 35 | `realcast` | 리얼캐스트 | https://www.rcast.co.kr/ | news_content | `link-snippet-only` | P2 | 분양, 정책, 시장 해설 |

1차 결론:

- 실제 crawler spike는 `ppomppu_house`, `dc_immovables`, `kb_land_datahub`, `reb_rone`, `data_go_apt_trade`부터 시작한다.
- 네이버 카페 seed는 source registry에는 남기되 자동 수집은 하지 않는다. 공식 API/제휴/수동 리서치 또는 검색 노출 범위가 확인될 때만 별도 검토한다.
- 지역/학군/맘카페는 부동산 반응 분산성의 중요한 근거지만 개인정보와 가입형 커뮤니티 리스크가 커서 화면 지표에는 source coverage caveat를 반드시 붙인다.
- 일반 커뮤니티(클리앙, 더쿠, 82cook)는 부동산 전용 source가 아니므로 지표 가중치를 낮추고 정책/생활형 반응 보조로만 쓴다.

## 30개 내외 registry 확장 슬롯

아래는 바로 크롤러를 만들 목록이 아니라 source registry의 `disabled` 후보를 채우기 위한 슬롯이다. 실제 이름과 URL은 공개 접근성 확인 뒤 확정한다.

| 그룹 | 슬롯 | 목적 | 초기 상태 | 확인할 것 |
| --- | --- | --- | --- | --- |
| 공개 게시판형 | 3-5개 | 최신글 기반 반응 흐름 | `disabled` | 목록 URL, page/cursor, 작성시각, 조회/댓글 필드 |
| 대형 부동산 카페 | 8-10개 | 투자/내집마련 심리 | `disabled` | 비로그인 공개 목록 여부, 검색 노출, 카페별 게시판 구조 |
| 지역/맘카페 | 8-10개 | 생활권, 학군, 전세, 신축 선호 | `disabled` | 지역별 공개 게시판 여부, 부동산 글 비중, 운영 정책 |
| 앱/프롭테크 커뮤니티 | 3-5개 | 단지 후기와 거주자 체감 | `local-research-only` | 웹 공개 페이지 여부, deep link, 원문 저장 제한 |
| 뉴스/컬럼/공식 공지 | 6-8개 | 정책/교통/공급 이벤트 보조 | `disabled` | 제목/link/snippet 저장 가능성, 원문 재게시 금지 |
| 공공/시장 fact | 5-8개 | 실거래, 전월세, 지수, 미분양 | `local-research-only` | 공식 API, 갱신 지연, provider/asOf/stale 기준 |

## 수집 정책 메모

- 네이버/다음 카페는 규모가 커도 로그인, 가입 승인, 검색 제한이 있으면 자동 수집 대상에서 제외한다.
- 블라인드는 공개 웹으로 일부 글과 토픽이 보이지만 앱/로그인 의존성이 크므로 P0 crawler가 아니라 P1 검토 source로 둔다.
- 호갱노노/아실 같은 앱 기반 source는 웹 공개 범위가 좁을 수 있으므로, 원문 수집보다 단지/지역 관심 신호와 링크 근거 중심으로 검토한다.
- 지역/맘카페는 생활권 신호가 강하지만 사적 대화와 개인정보 리스크가 커서 공개 게시판 확인 전까지 adapter를 만들지 않는다.
- 뉴스/컬럼은 커뮤니티 반응이 아니라 정책/이벤트/쟁점 근거로만 쓴다.

## P0 spike 순서

1. `ppomppu_house` 최신글 목록 parser spike
2. `dc_immovables` 최신글 목록 parser spike
3. 다음 카페 중 공개 `bbs_list`가 허용되는 부동산 카페 1곳 source-specific 확인
4. 위 3곳의 source registry 필드 확정
5. source별 `blocked`, `failed`, `partial`, `complete` coverage 샘플 작성

## source registry 필드 후보

```json
{
  "sourceId": "ppomppu_house",
  "displayName": "뽐뿌 부동산포럼",
  "sourceType": "general_board",
  "primaryUrl": "https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1",
  "targetScope": ["region", "complex", "policy_area"],
  "crawlPolicy": "disabled",
  "policyReviewState": "pending",
  "requiresLogin": false,
  "publicListObserved": true,
  "allowedStorage": ["title", "contentSnippet", "url", "authorHash", "publishedAt", "contentHash"],
  "adapterStatus": "not_started",
  "priority": "P0"
}
```

## 다음 작업

1. 위 후보를 `crawl_sources` seed 후보로 옮긴다.
2. P0 2-3곳만 실제 HTML 샘플을 저장하고 parser 테스트를 만든다.
3. 네이버/다음 카페는 공개 목록 접근성 확인 결과에 따라 `excluded-login-required` 또는 `local-research-only`로 분리한다.
4. 지역/단지 alias DB 초안과 연결해, source별로 어떤 별칭이 많이 필요한지 기록한다.
5. source skew가 큰 source는 지표 산식에서 가중치를 낮추거나 별도 caveat를 붙인다.
6. 부동산 dashboard/지역 반응 지표에는 source category coverage를 표시할지 결정한다.

## 외부 확인 근거

- 뽐뿌 부동산포럼: https://m.ppomppu.co.kr/new/bbs_list.php?id=house&page=1
- 디시인사이드 부동산 갤러리: https://gall.dcinside.com/board/lists/?id=immovables
- 블라인드 부동산 토픽: https://www.teamblind.com/kr/topics/%EB%B6%80%EB%8F%99%EC%82%B0
- 호갱노노 커뮤니티: https://hogangnono.com/community
- 호갱노노 이야기 개편 보도자료: https://company.zigbang.com/newsroom/view?idx=339
- 부동산스터디 관련 언론: https://www.sedaily.com/article/12892140
- 피터팬 카페 회원 300만 관련 언론: https://www.sentv.co.kr/article/view/sentv202402190072?d=pc
- 월급쟁이부자들 관련 언론: https://realty.chosun.com/site/data/html_dir/2026/02/20/2026022002804.html
- 아름다운 내집갖기 소개: https://eparajoo.com/real_estate-blog/?bmode=view&idx=7379356
- 행복재테크 관련 언론: https://www.lawissue.co.kr/view.php?ud=20180303021621903107f28b58b8_12
- 아실 Google Play: https://play.google.com/store/apps/details?hl=ko&id=kr.co.koreachart.city
- 국토교통부 실거래가 공개시스템 자료제공: https://rt.molit.go.kr/pt/xls/xls.do?mobileAt=
- 네이버 지역 기반 카페 기능 보도자료: https://navercorp.com/media/pressReleasesDetail?seq=30319
- 네이버/다음 부동산 카페 목록 규모 참고: https://kmong.com/gig/137951
- 부동산 카페 URL 참고: https://www.teamblind.com/kr/post/%EC%9E%90%EC%A3%BC%EA%B0%80%EB%8A%94-%EB%B6%80%EB%8F%99%EC%82%B0%EC%B9%B4%ED%8E%98-%EC%A0%95%EB%B3%B4-%EA%B3%B5%EC%9C%A0-otYWq1nS
- 분당·판교·위례 지역 카페 참고: https://borathis.com/entry/%EB%B6%84%EB%94%B0
- 학군지 지역 카페 URL 참고: https://investment-ai.tistory.com/entry/%ED%95%99%EA%B5%B0%EC%A7%80-%EB%B3%84-%EB%84%A4%EC%9D%B4%EB%B2%84-%EA%B9%8C%ED%8E%98-%EB%AA%A8%EC%9E%84-List
- 동탄맘 카페 URL 참고: https://www.i-boss.co.kr/ab-1958-61179
- 일반 커뮤니티 부동산 글 예시: https://www.82cook.com/entiz/read.php?bn=15&num=4168009
- 일반 커뮤니티 부동산 글 예시: https://theqoo.net/stock/3984082614
- 일반 커뮤니티 부동산 글 예시: https://m.clien.net/service/board/park/19077823?type=recommend
- 부동산지인: https://aptgin.com/
- 리치고: https://m.richgo.ai/
- KB부동산 데이터허브: https://data.kbland.kr/
- 한국부동산원 R-ONE: https://www.reb.or.kr/r-one/portal/main/indexPage.do
- 부동산R114: https://r114.com/
- 땅집고: https://realty.chosun.com/
- 리얼캐스트: https://www.rcast.co.kr/
- 주식 종목토론방 규모 비교 기사: https://v.daum.net/v/HVDlD6ZwUB
- 네이버 카페 robots: https://cafe.naver.com/robots.txt
- 다음 카페 robots: https://cafe.daum.net/robots.txt
- 호갱노노 robots: https://hogangnono.com/robots.txt
- 블라인드 robots: https://www.teamblind.com/robots.txt
- 아실 robots: https://asil.kr/robots.txt
