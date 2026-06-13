# 핵심 구현 범위

이 문서는 `real-estate-one-page-plan.html`의 내용을 실제 구현 단위로 풀어쓴 기준입니다. HTML 한페이지 기획안은 제출/시각화용 정본이고, 이 문서는 backend, pipeline, UI, agent가 구현할 기능 범위를 맞추는 정본입니다.

## 기준 아티팩트

- 시각 기획안: `docs/product/real-estate-one-page-plan.html`
- 제품 방향: `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`
- 데이터 계약: `docs/domains/realestate/DATA_CONTRACT.md`

## 한 줄 구현 목표

수요자 반응 기반 부동산 시장 해석 서비스로서, 사람들이 커뮤니티, 댓글, 뉴스, 컬럼에서 남긴 부동산 반응을 지역과 단지 기준 지표로 만들고, 실거래/전세/매물/정책 흐름 및 비슷한 과거 상황과 함께 보여준다.

## 핵심 구현 흐름

부동산 서비스의 핵심 구현 흐름은 다음과 같습니다.

1. 공개 source에서 글, 댓글, 뉴스, 컬럼을 수집합니다.
2. 원문을 제한 저장하고 source, board, external id, 작성 시각, snippet을 남깁니다.
3. 대상 언급을 찾고 반응 방향과 쟁점을 분류합니다.
4. window 단위 snapshot으로 언급량, 기대/우려, issueMix, confidence를 만듭니다.
5. 시장 사실 데이터와 같은 시간축에 붙입니다.
6. 비슷한 과거 window를 찾아 이후 흐름을 비교합니다.
7. SerpApi 같은 검색 API로 최근 정책/개발/교통/금리 이슈 후보와 근거 링크를 보강합니다.
8. agent가 지표, 시장 사실, 유사 과거, 최근 이슈, 근거를 읽고 사용자용 평가 로그를 남깁니다.
8. dashboard와 target detail API로 노출합니다.

## 부동산이라 달라지는 점

### 1. 대상은 쪼개진 지역/단지 우주다

부동산은 시/구/동, 생활권, 역세권, 학군, 재건축 구역, 단지처럼 대상이 계층적이고 계속 쪼개집니다.

구현 기준:

- `region`, `complex`, `living_area`, `policy_area`를 구분합니다.
- region hierarchy와 complex-to-region 매핑을 먼저 둡니다.
- target discovery와 alias review를 별도 작업으로 둡니다.
- 단지 언급은 상위 지역 지표에도 roll-up될 수 있어야 합니다.
- 지역 언급은 영향권 단지 후보로 drill-down될 수 있어야 합니다.

### 2. 별칭 DB가 수집의 필수 입력이다

부동산 커뮤니티는 공식명보다 줄임말, 별칭, 오타, 생활권 표현이 자주 나올 수 있습니다. 별칭 DB 없이 crawler를 늘리면 수집량만 늘고 지표 품질은 떨어집니다.

구현 기준:

- `real_estate_aliases`는 1차 모델입니다.
- alias는 `official`, `short_name`, `nickname`, `typo`, `nearby_area`, `community_slang`로 시작합니다.
- `candidate` alias는 저장하되 `approved` 전에는 ranking과 정식 snapshot에 섞지 않습니다.
- alias collision, 짧은 별칭, 일반 단어 오탐 fixture를 반드시 둡니다.

### 3. 지역 단위 상승과 정책 이벤트에 민감하다

부동산은 개별 단지보다 지역 흐름, 정책, 교통, 공급, 대출, 청약, 학군, 재건축 이슈에 민감합니다. 따라서 뉴스/정책은 보조 링크가 아니라 market fact와 timeline의 1차 입력입니다.

구현 기준:

- `policy_event`, `transport_event`, `supply_event`, `loan_event`, `education_event`, `redevelopment_event`를 first-class timeline event로 둡니다.
- 이벤트는 영향 범위를 `targetScope`로 남깁니다: `national`, `sido`, `sigungu`, `dong`, `living_area`, `complex`.
- 지역 단위 이벤트가 하위 단지 snapshot에 영향을 줄 수 있도록 target graph를 둡니다.
- 화면에서는 "정책 영향 후보", "함께 관찰된 변화", "확인 필요"처럼 표현하고 원인 단정은 피합니다.

### 4. 시장 사실은 지연과 기준시각이 있는 데이터다

실거래, 전세, 매물, 공공데이터, 지수는 각각 지연과 기준시각이 다릅니다. 화면과 API는 이를 실시간 가격처럼 단정하지 않습니다.

구현 기준:

- `observedAt`, `asOf`, `sourceUpdatedAt`, `ingestedAt`, `stale`, `dataStatus`를 분리합니다.
- 공공데이터포털의 업데이트 주기가 `실시간`이어도 사용자 화면에는 매일 확정 공시처럼 표현하지 않습니다.
- 값 없음은 `0`이 아니라 `empty`, `unknown`, `partial`, `stale`, `error`, `mock`으로 분리합니다.

### 5. source가 훨씬 분산되어 있다

부동산은 공개 게시판, 카페, 뉴스, 컬럼, 공식 공지, 공공데이터가 흩어져 있습니다. 30개 내외 후보를 한 번에 adapter로 만들지 않고, source registry로 먼저 관리합니다.

구현 기준:

- 모든 source는 `crawl_sources` registry에 먼저 들어갑니다.
- 기본 상태는 `disabled`입니다.
- 공개 접근성, robots/약관, 로그인 필요 여부, 신호 품질, parser 난이도를 검토한 뒤 올립니다.
- 네이버 카페와 다음 카페는 비로그인 공개 목록과 공개 글만 검토합니다.
- 로그인, CAPTCHA, 프록시, fingerprint 우회가 필요한 source는 구현하지 않습니다.

## 한페이지 기획안의 4개 구현 축

| 축 | 입력 | 기술 흐름 | 사용자 산출물 |
| --- | --- | --- | --- |
| 커뮤니티 반응 | 글, 댓글, 컬럼, 뉴스 | 크롤링 수집 -> DB 저장 -> 임베딩/쟁점 묶기 -> 지표화 | 관심 지수, 쟁점 비율, 표본 신뢰도 |
| 시장 사실 | 실거래, 전세, 매물, 정책 | 공공데이터/API -> 시점별 저장 -> 이벤트 타임라인 -> 변화 감지 | 시장 흐름, 뉴스/정책 연결 |
| 비슷한 과거 | 과거 분위기와 이후 결과 | 과거 사례 저장 -> 유사 사례 DB -> 유사 패턴 검색 -> 결과 비교 | 과거 비교 리포트 |
| 최근 이슈 | 검색 API, 뉴스/정책 링크 | SerpApi/search 후보 탐색 -> 링크/키워드 제한 저장 -> target 후보 연결 | 최근 이슈 후보와 근거 링크 |
| 에이전트 판단 | 지표, 시장 사실, 과거 비교, 최근 이슈 | 지표 입력 -> AI 근거 검색 -> 맥락 종합 -> 근거 로그 | 지역/단지 평가와 caveat |

## 첫 구현 Definition of Done

- 대시보드에서 요즘 언급 많은 지역/단지를 보여줍니다.
- target detail에서 reaction snapshot과 주요 쟁점 비율을 보여줍니다.
- 실거래/전세/매물/정책 timeline이 `provider/asOf/stale`와 함께 나옵니다.
- 비슷한 과거 window와 이후 market fact 흐름을 최소 1개 이상 연결합니다.
- agent evidence log가 summary, evidence, caveats, dataStatus를 남깁니다.
- 낮은 표본, source 편중, stale, partial coverage가 화면과 API에 드러납니다.
- 행동 지시, 가격 상승 단정, 청약/대출 권유 문구가 없습니다.
