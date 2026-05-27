# stock

## Alias Registry와 후보 큐

종목 언급 집계는 raw text를 바로 세지 않고 `market + symbol` canonical key로 확정된 mention만 사용합니다.

- `instrument_aliases`: 승인된 alias registry입니다. `status=ACCEPTED`이고 `ambiguous=false`인 alias만 종목 mention 후보로 씁니다.
- `status=REVIEW` 또는 `ambiguous=true`인 alias는 종목 mention으로 확정하지 않고 후보로만 기록합니다.
- `status=BLOCKED` alias는 일반명사 충돌처럼 오탐 위험이 큰 표현입니다. 집계와 후보 큐 모두에서 제외합니다.
- `instrument_alias_candidates`: 커뮤니티에서 관찰된 은어/별칭 후보 큐입니다. 같은 `source + normalizedAlias + suggestedMarket + suggestedSymbol`은 occurrence를 누적합니다.
- pipeline은 운영/compose 환경에서 `INSTRUMENT_SNAPSHOT_URL`로 backend의 `/admin/instruments/matcher-snapshot`을 읽어 승인된 종목 master와 alias를 가져옵니다. URL이 없거나 snapshot 로드가 반복 실패하면 로컬 fixture용 `INSTRUMENT_CSV_PATH`와 `INSTRUMENT_ALIAS_CSV_PATH`를 fallback으로 씁니다.
- `INSTRUMENT_ALIAS_CSV_PATH`의 review alias는 아직 후보 탐지 fallback입니다. 정식 mention 집계는 backend snapshot에 포함된 `ACCEPTED + ambiguous=false` alias만 확정 후보로 씁니다.
- 후보 상태는 `PENDING -> SUGGESTED/REJECTED/PROMOTED` 흐름으로 봅니다. `SUGGESTED`는 AI/사람이 "그럴듯함"으로 판정한 상태일 뿐이고, `PROMOTED`가 되어 `instrument_aliases(status=ACCEPTED, ambiguous=false)`에 들어가기 전까지는 집계에 쓰지 않습니다.
- 운영용 API는 `POST /admin/alias-candidates/{candidateId}/review`로 `SUGGESTED` 또는 `REJECTED` 판정을 저장하고, `POST /admin/alias-candidates/{candidateId}/promote`로 승인 후보를 정식 alias로 승격합니다.

운영 원칙:

- 새 은어는 바로 `post_mentions`에 넣지 않습니다.
- 후보의 occurrence, sampleUrl, contextSnippet을 보고 승인할 때만 alias registry에서 `ACCEPTED`로 승격합니다.
- 승인 전 후보는 급증 종목/반응 방향/개미 심리 지수의 정식 count에 섞지 않습니다.
- 같은 normalized alias가 이미 다른 종목의 확정 alias로 있으면 자동 승격하지 않습니다.

## Instrument Identifiers

`instruments.id`는 서비스 내부의 종목 기준 ID입니다. `instrument_identifiers`는 이 종목이 외부 제공처나 수집 대상에서 어떤 값으로 불리는지 연결합니다.

- `namespace`: 식별자 체계입니다. 예: `YFINANCE`, `KRX_TICKER`, `US_TICKER`, `NAVER_STOCK_BOARD`.
- `identifier`: 제공처/게시판에서 쓰는 원문 값입니다. 예: `005930.KS`, `005930`, `TSLA`.
- `normalized_identifier`: 중복 비교용 정규화 값입니다. 대소문자와 공백 차이 때문에 같은 종목이 둘로 갈라지는 일을 막습니다.
- `purpose`: 사용 목적입니다. 예: `MARKET_DATA`, `EXCHANGE_REFERENCE`, `COMMUNITY_BOARD`.
- `source`: 이 매핑을 넣은 출처입니다. 예: `seed`, `admin`, `crawler_candidate`, `ai_review`.

식별자는 시세/차트/수급/종목형 게시판처럼 외부 시스템에 접근하기 위한 키입니다. 커뮤니티 은어와 별칭은 `instrument_aliases`와 `instrument_alias_candidates`에서 관리합니다.

## Instrument Master Seed

`backend/src/main/resources/data/instrument-master-seed.tsv`는 앱이 시작될 때 `instruments`와 `instrument_identifiers`에 반영되는 대량 종목 seed입니다.

- 현재 seed 규모: 총 15,439개입니다. KR 주식 2,808개, KR ETF 874개, US 주식 6,534개, US ETF 5,223개를 담습니다.
- loader: `InstrumentMasterSeedLoader`가 idempotent하게 실행됩니다. 같은 `market + symbol` 종목은 업데이트하고, 같은 `namespace + normalized_identifier + purpose` 식별자는 중복 저장하지 않습니다.
- 설정: `INSTRUMENT_MASTER_SEED_ENABLED=false`로 로더를 끌 수 있고, `INSTRUMENT_MASTER_SEED_PATH`로 seed 경로를 바꿀 수 있습니다.
- provider 식별자: `YFINANCE/MARKET_DATA`, `KRX_TICKER` 또는 `US_TICKER/EXCHANGE_REFERENCE`, 국내 종목은 `NAVER_STOCK_BOARD/COMMUNITY_BOARD`를 생성합니다.
- 거래소 구분: `instruments.exchange_code`에 `KOSPI`, `KOSDAQ`, `KOSDAQ GLOBAL`, `KRX_ETF`, `NASDAQ`, `NYSE`, `AMEX`, `US_ETF` 같은 값을 저장합니다.

이 seed는 정확한 종목 식별과 provider/게시판 key 연결을 위한 master입니다. seed에 있는 종목명 전체를 커뮤니티 alias로 자동 승인하지는 않습니다. 은어, 별칭, 일반명사와 충돌할 수 있는 표현은 `instrument_alias_candidates`에 쌓고 review/promote 흐름을 거친 뒤 집계에 반영합니다.

pipeline matcher는 종목 master와 alias rule을 실행 시점에 한 번 읽고, 글마다 전체 종목을 전수 대조하지 않습니다. `INSTRUMENT_SNAPSHOT_URL`이 있으면 backend DB 정본에서 생성한 snapshot을 한 번 가져오고, 없으면 CSV fixture를 읽습니다. snapshot URL이 설정되어 있어도 backend 부팅 타이밍이나 일시 장애로 실패할 수 있으므로 `INSTRUMENT_SNAPSHOT_RETRIES`, `INSTRUMENT_SNAPSHOT_RETRY_DELAY_SECONDS`, `INSTRUMENT_SNAPSHOT_FALLBACK_ON_ERROR`로 재시도와 CSV fallback을 제어합니다. 이후 ASCII 티커/영문 alias는 토큰 인덱스, 한글/비ASCII alias는 첫 글자 인덱스로 후보를 좁힌 뒤 span을 확인합니다. 따라서 1만 개 이상 master를 쓰더라도 게시글별 matching은 본문에 실제 등장한 토큰과 첫 글자 bucket 위주로 수행합니다.

matcher snapshot API:

- `GET /admin/instruments/matcher-snapshot`
- query: `market` optional. 예: `?market=US`
- 응답: `instrumentId`, `market`, `symbol`, `name`, `aliases`
- `aliases`에는 `instrument_aliases.status=ACCEPTED`이고 `ambiguous=false`인 값만 포함합니다. `REVIEW`, `BLOCKED`, `ambiguous=true` alias는 확정 mention 후보가 아닙니다.
- pipeline은 이 snapshot을 글마다 DB 조회하지 않고 시작 시 한 번 로드한 뒤 인메모리 matcher 인덱스로 씁니다.

## 역할

종목을 식별하고 여러 도메인이 같은 종목을 같은 키로 다루게 만드는 기준 도메인입니다. 커뮤니티 글, 시세 provider, 화면 검색, 에이전트 판단이 모두 이 도메인의 종목 기준을 참조합니다.

## 담당 범위

- 국내/미국 stock master
- 티커, 거래소, 시장 구분
- 종목명, 별칭, 은어 후보
- 커뮤니티 글의 종목 후보 매칭
- 검색/자동완성에 필요한 표시 이름
- 낮은 confidence 후보의 저장/검증 기준

## 주요 계약

| 항목 | 기준 |
| --- | --- |
| 내부 종목 key | `instruments.id`를 우선 사용합니다. |
| 외부 식별자 | `instrument_identifiers.namespace + normalized_identifier + purpose`로 찾습니다. |
| 별칭 | 승인된 alias registry와 후보 alias를 구분합니다. |
| 불확실한 매칭 | 추측으로 확정하지 않고 confidence와 후보 상태를 둡니다. |

## 다른 도메인과의 접점

- `community`: 글에서 종목 후보를 찾을 때 stock 기준을 씁니다.
- `market`: quote/chart/investor flow provider symbol과 `instrument_id`를 매핑합니다.
- `indicator`: 30분 snapshot과 지표를 같은 `instrument_id` 기준으로 집계합니다.
- `agent`: 판단 key와 결정 로그에서 같은 `instrument_id`를 씁니다.
- `layers/ui`: 검색창, 종목 카드, 상세 route에서 표시 이름과 symbol을 사용합니다.

## 하지 않는 일

- 커뮤니티 반응 방향 분류
- 시세 provider 호출
- 지표 산식 계산
- 에이전트 매매 판단
