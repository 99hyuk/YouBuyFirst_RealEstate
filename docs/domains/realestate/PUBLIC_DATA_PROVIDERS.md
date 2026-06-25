# 부동산 공공데이터 Provider 기준

확인일: 2026-06-12

이 문서는 너나사 부동산이 시장 사실 데이터로 사용할 공공데이터 원천을 정합니다. 공공데이터는 커뮤니티 반응과 달리 가격, 거래, 공급, 지수의 기준값으로 쓰지만, 원천별 기준일과 공개 지연이 다르므로 항상 `provider`, `providerDataset`, `observedAt`, `asOf`, `ingestedAt`, `stale`을 함께 저장합니다.

## 1차 확정 Provider

| 우선순위 | dataset id | 원천 | 용도 | 수집 방식 | 백필 |
| --- | --- | --- | --- | --- | --- |
| 10 | `molit_apt_trade` | 국토교통부 아파트 매매 실거래가 | 지역/단지 매매 실거래 market fact | 공공데이터포털 OpenAPI, XML | 예 |
| 20 | `molit_apt_rent` | 국토교통부 아파트 전월세 실거래가 | 전세/월세 흐름, 전세가율 보조 | 공공데이터포털 OpenAPI, XML | 예 |
| 21 | `molit_offi_trade` | 국토교통부 오피스텔 매매 실거래가 | 오피스텔 매매 실거래 market fact | 공공데이터포털 OpenAPI, XML | 예 |
| 22 | `molit_offi_rent` | 국토교통부 오피스텔 전월세 실거래가 | 오피스텔 전월세 흐름 | 공공데이터포털 OpenAPI, XML | 예 |
| 23 | `molit_rh_trade` | 국토교통부 연립다세대 매매 실거래가 | 연립·다세대 매매 실거래 market fact | 공공데이터포털 OpenAPI, XML | 예 |
| 24 | `molit_rh_rent` | 국토교통부 연립다세대 전월세 실거래가 | 연립·다세대 전월세 흐름 | 공공데이터포털 OpenAPI, XML | 예 |
| 25 | `molit_sh_trade` | 국토교통부 단독다가구 매매 실거래가 | 단독·다가구 매매 실거래 market fact | 공공데이터포털 OpenAPI, XML | 예 |
| 26 | `molit_sh_rent` | 국토교통부 단독다가구 전월세 실거래가 | 단독·다가구 전월세 흐름 | 공공데이터포털 OpenAPI, XML | 예 |
| 27 | `molit_silv_trade` | 국토교통부 분양권 매매 실거래가 | 분양권 매매 실거래 market fact | 공공데이터포털 OpenAPI, XML | 예 |
| 30 | `molit_official_apartment_price_csv` | 국토교통부 공동주택 호별 공시가격 | 공시가격, 단지/호 단위 기준 가격 | 공공데이터포털 대용량 CSV ZIP | 예 |
| 40 | `reb_real_estate_statistics` | 한국부동산원 부동산통계 조회 서비스 | 가격지수, 실거래가격지수, 거래현황 | 공공데이터포털 OpenAPI, JSON/XML | 예 |
| 50 | `molit_unsold_housing_stat` | 국토교통 통계누리 미분양주택현황보고 | 미분양/준공 후 미분양 공급 압력 | 통계누리 파일/API 후보 | 예 |
| 60 | `molit_housing_permit_stat` | 국토교통부 주택 인허가 실적 | 공급 선행지표 | 공공데이터포털 파일 | 예 |
| 70 | `molit_buildinghub_housing_approval` | 국토교통부 건축HUB 주택건설사업계획승인 정보 | 프로젝트/공급 이벤트 후보 | 공공데이터포털 OpenAPI | 보류 |

## 원천별 기준

### `molit_apt_trade`

- 공식 페이지: https://www.data.go.kr/data/15126469/openapi.do
- 요청 기준: `LAWD_CD`, `DEAL_YMD`
- 저장 기준: `factType=apt_trade`
- 1차 stale 기준: 72시간
- 주의: 공개 시점과 실제 계약일이 다르므로 `observedAt`은 계약일, `asOf`는 조회 기준월 1일로 둡니다.

### `molit_apt_rent`

- 공식 페이지: https://www.data.go.kr/data/15126474/openapi.do
- 요청 기준: `LAWD_CD`, `DEAL_YMD`
- 저장 기준: `factType=apt_rent`
- 1차 stale 기준: 72시간
- 주의: 보증금/월세, 계약구분, 계약기간을 원천 raw와 함께 저장합니다.

### `molit_official_apartment_price_csv`

- 공식 페이지: https://www.data.go.kr/data/3073746/fileData.do
- 저장 기준: `factType=official_apartment_price`
- 1차 stale 기준: 370일
- 확인된 규모: 2025년 기준 CSV 전체 행 15,580,435건
- 구현 상태: `realestate-official-apartment-prices-inspect`로 대용량 CSV를 적재 전 streaming 점검하고, `realestate-official-apartment-prices-raw-push` 명령으로 batch 단위 raw/staging 적재가 가능합니다.
- 주의: 스프레드시트로 열 수 없는 대용량 CSV이므로 raw landing -> staging -> 정규화 승격 흐름으로 처리합니다.

### `reb_real_estate_statistics`

- 공식 페이지: https://www.data.go.kr/data/15134761/openapi.do
- 저장 기준: `factType=price_index`, `real_transaction_price_index`, `transaction_volume` 등으로 세분화 예정
- 1차 stale 기준: 45일
- 구현 상태: `realestate-regional-stat-csv-inspect` / `realestate-regional-stat-csv-raw-push` 공통 CSV adapter로 정규화된 지역 통계 CSV를 raw/staging에 적재할 수 있습니다.
- 주의: 한국부동산원 지수는 개별 실거래 원장이 아니라 통계/지수입니다. 실거래가처럼 표현하지 않습니다.

### `molit_unsold_housing_stat`

- 공식 페이지: https://stat.molit.go.kr/portal/cate/statMetaView.do?hRsId=32
- 저장 기준: `factType=unsold_housing`
- 1차 stale 기준: 65일
- 구현 상태: `기준월`, `지역코드`, `지역명`, `항목`, `값`, `단위` 형태의 통계 CSV를 공통 regional stat adapter로 적재할 수 있습니다.
- 주의: 통계누리 설명상 매월 조사하고 익월 말 공표됩니다. 화면에서는 최신 실시간 데이터처럼 말하지 않습니다.

### `molit_housing_permit_stat`

- 공식 페이지: https://www.data.go.kr/data/15068726/fileData.do
- 저장 기준: `factType=housing_permit`
- 1차 stale 기준: 65일
- 구현 상태: `기준월`, `지역코드`, `지역명`, `항목`, `값`, `단위` 형태의 통계 CSV를 공통 regional stat adapter로 적재할 수 있습니다.
- 주의: 공급 선행지표입니다. 이후 `housing_start`, `housing_completion`과 분리할 수 있게 staging에 원천 컬럼을 보존합니다.

### `molit_buildinghub_housing_approval`

- 공식 페이지: https://www.data.go.kr/data/15136560/openapi.do
- 저장 기준: `factType=supply_event`
- 상태: 보조/검증 대상
- 주의: 프로젝트/건축물 PK 체계와 단지 target 연결 규칙이 검증되기 전까지 정식 백필 대상에서 제외합니다.

## DB 적재 구조

대량 데이터는 바로 `real_estate_market_facts`에 넣지 않습니다.

```text
provider 원천
-> real_estate_public_data_import_runs
-> real_estate_public_data_raw_items
-> real_estate_market_fact_staging
-> real_estate_market_facts
-> 화면/AI 평가/집계 snapshot
```

역할:

- `real_estate_public_data_datasets`: 사용하기로 확정한 provider/dataset catalog입니다.
- `real_estate_public_data_import_runs`: 백필/갱신 실행 단위입니다. 실패, 부분 성공, 재시도 기준을 남깁니다.
- `real_estate_public_data_raw_items`: 원천 행 또는 원천 item의 제한된 raw JSON입니다. provider object id와 payload hash로 중복을 막습니다.
- `real_estate_market_fact_staging`: market fact로 승격하기 전 검증 단계입니다.
- `real_estate_market_facts`: 화면과 AI 평가에서 참조하는 정규화된 시장 사실입니다.
- `real_estate_complexes`: 단지 target의 주소, 법정동, 상위 지역 연결을 보관합니다.
- `real_estate_complex_provider_keys`: 공시가격/실거래/건축HUB 같은 provider별 단지 외부키를 연결합니다.

실거래/전월세 백필 명령은 실행 후 JSON manifest를 출력합니다. 운영자는 `taskCount`, `publishedRuns`, `publishedItems`, `emptyRuns`, `promotedRuns`, run별 `rawItems`를 보고 수집 결과가 실제 데이터 없음인지, 일부 적재인지, 승격까지 이어졌는지 확인합니다.

provider catalog의 코드 정본은 `pipeline/src/youbuyfirst_pipeline/realestate_provider_catalog.py`입니다. 사람이 읽는 확인은 `realestate-public-data-providers` JSON 출력으로 하고, DB seed 검수는 `realestate-public-data-providers --realestate-provider-output sql` 출력과 `V27__real_estate_public_data_catalog_and_raw_ingestion.sql`의 INSERT를 대조합니다.

통계성 CSV adapter는 한국부동산원 지수, 미분양, 인허가처럼 지역/기간/지표값으로 구성되는 데이터를 위한 공통 경로입니다. 원본 CSV를 `기준월`, `지역코드`, `지역명`, `항목`, `값`, `단위` 중심의 정규화 CSV로 맞추면 inspect와 raw-push를 같은 방식으로 사용할 수 있습니다. 실제 원천별 다운로드 파일의 컬럼명 차이는 원천별 샘플 검증에서 보정합니다.

대용량 파일은 실제 적재 전에 manifest를 먼저 확인합니다. 공시가격 CSV inspect 결과에는 `totalRows`, `validRows`, `invalidRows`, `batchCount`, 첫/마지막 `runKey`, 일부 `providerObjectId`, 오류 샘플이 포함됩니다. 이 결과로 배치 수와 오류율을 확인한 뒤 raw-push를 실행합니다.

실거래/전월세처럼 `LAWD_CD + DEAL_YMD + providerDataset` run이 많아지는 백필은 chunk manifest로 나눕니다. `realestate-market-facts-backfill-plan --realestate-backfill-chunk-size 100 --realestate-backfill-plan-output molit-plan.json`처럼 실행하면 `chunks[].items`에 재개 가능한 실행 묶음이 생깁니다. chunk manifest도 `--realestate-backfill-plan-json` 입력으로 다시 읽을 수 있으므로, 실패한 chunk만 다시 preflight/raw-push하는 식으로 운영합니다.

## 인증키 보관

실제 공공데이터 인증키는 git에 올리지 않습니다.

```env
DATA_GO_SERVICE_KEY=...
```

보관 위치:

- 로컬: repo 루트 `.env`
- Docker/운영: 환경변수 또는 배포 Secret
- Spring: `application.yml`에는 `${DATA_GO_SERVICE_KEY:}` 참조만 둡니다.
- 예시: `.env.example`, `application-local.example.yml`

금지:

- 실제 키를 `application.yml`, 테스트 fixture, 문서, 프론트 환경변수에 직접 저장
- 브라우저에서 공공데이터 API를 직접 호출

## 다음 구현 순서

1. `realestate-public-data-providers` CLI로 provider catalog를 확인하고, `--realestate-provider-output sql`로 DB seed INSERT와 불일치가 없는지 검수합니다.
2. 실제 한국부동산원 통계, 미분양, 인허가 원본 파일을 내려받아 공통 regional stat CSV adapter에 맞는 컬럼 매핑을 검증합니다.
3. 실제 공시가격 CSV 원본을 내려받아 `realestate-official-apartment-prices-inspect`로 row 수, 오류 샘플, batch 수를 확인합니다.
4. inspect 결과가 정상 범위이면 샘플/부분 백필을 실행합니다.
5. staging 검증을 통과한 데이터만 `real_estate_market_facts`로 승격합니다.
6. 법정동 코드와 단지 provider key를 기준으로 `real_estate_targets`와 연결합니다.
