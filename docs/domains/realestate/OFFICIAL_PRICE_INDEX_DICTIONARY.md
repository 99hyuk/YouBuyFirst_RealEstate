# 공식 가격 지표 사전

작성일: 2026-06-23

이 문서는 지역 지도, 대시보드, 지역 상세 리포트에서 쓰는 한국부동산원 가격 지표의 기준 이름과 수집 방식을 정리합니다. 목표는 비슷한 이름의 지표를 섞어 쓰지 않고, 화면에 보이는 상승/하락 색상이 실제 지표값에 비례하도록 만드는 것입니다.

## 결론

- 지역 분석 지도 색상은 한국부동산원 R-ONE 매매가격지수 원천값을 `price_index` fact로 저장한 뒤, period별 기준 시점과 최신 시점을 비교해 계산합니다.
- DB 적재 dataset 이름은 주간 `reb_rone_weekly_apt_sale_price_index_region`, 월간 `reb_rone_monthly_apt_sale_price_index`입니다.
- 이 지표의 공식 이름은 `전국주택가격동향조사_주간아파트동향_매매가격지수(지역별)`입니다.
- 1주/1개월/3개월/6개월/1년 period는 별도 변동률 fact를 만들지 않고 저장된 지수값으로 `latestIndex / baselineIndex - 1`을 계산합니다.
- 주간 운영 수집은 Spring Batch, 월간 운영 수집은 R-ONE Open API 기반 pipeline 수집기로 구현합니다. R-ONE 지역 현황 지도 응답은 최신 월과 지역 코드 매핑 보조로만 씁니다.
- 지도에서 검게 처리되는 지역은 `DB 미적재`, `지역 매핑 실패`, `공식 원천 미공표`를 분리해서 판정합니다. 가평, 양평처럼 실제 존재 가능성이 높은 시군구는 공식 원천 파일/API 행 존재 여부를 먼저 검증해야 합니다.

## 지표 목록

| metricCode | 공식명 | 주기 | 대상 | 차원 | 우선순위 | 용도 |
| --- | --- | --- | --- | --- | --- | --- |
| `reb_weekly_apt_sale_price_index_region` | 전국주택가격동향조사_주간아파트동향_매매가격지수(지역별) | 주간 | 아파트 | 지역 | P0 | 지역 지도 색상 중 1주 변화율, 지역 상세 리포트 최신 신호 |
| `reb_weekly_apt_sale_price_index_size` | 전국주택가격동향조사_주간아파트동향_매매가격지수(규모별) | 주간 | 아파트 | 규모 | P2 | 상세 분석 보조. 지역 대표값으로 쓰지 않음 |
| `reb_weekly_apt_sale_price_index_age` | 전국주택가격동향조사_주간아파트동향_매매가격지수(연령별) | 주간 | 아파트 | 건축연령 | P2 | 상세 분석 보조. 지역 대표값으로 쓰지 않음 |
| `reb_monthly_apt_sale_price_index_region` | 전국주택가격동향조사_월간아파트동향_매매가격지수(지역별) | 월간 | 아파트 | 지역 | P1 | 1개월/3개월/6개월/1년 변화율. `reb_rone_monthly_apt_sale_price_index` 지수값으로 계산 |
| `reb_common_housing_sale_price_index_region` | 전국주택가격동향조사 매매가격지수 중 종합/주택 유형 계열 | 월간 또는 주간 | 지표별 상이 | 지역/유형 | P3 | 아파트 지표와 섞지 않고 별도 검증 후 사용 |
| `reb_real_transaction_price_index_apt_region` | 공동주택 실거래가격지수 중 아파트 매매 | 월간 또는 분기 | 실제 신고 거래 기반 공동주택/아파트 | 지역 | P3 | 사후 검증 지표. 주간 지도 대표값으로 쓰지 않음 |

## 비슷한 지표의 차이

### 주간 아파트 매매가격지수

- 아파트 시장의 주간 흐름을 보는 지표입니다.
- 공표가 빠르기 때문에 지도와 대시보드의 최신 지역 흐름에는 이 지표가 가장 맞습니다.
- 1주 변화율은 최신 주간 지수값과 직전 주간 지수값을 비교해 계산합니다.
- 원천이 제공하는 지수값은 `factType=price_index`, `valueJson.indexValue`, `unit=지수`로 적재합니다.
- 1개월, 3개월, 6개월, 1년 변화율은 주간 지표를 누적하지 않고 월간 아파트 매매가격지수 원천값을 기준으로 계산합니다.

### 월간 아파트 매매가격지수

- 아파트 시장의 월간 흐름을 보는 지표입니다.
- 월간은 1주 최신 흐름에는 늦지만, 1개월 이상 기간을 적은 row 수로 안정적으로 표현할 수 있습니다.
- 지도 상단 period 기준은 `1주=최신 주간 지수/직전 주간 지수`, `1개월/3개월/6개월/1년=최신 월간 지수/N개월 전 월간 지수`입니다.
- 월별 원표/Open API에서 내려오는 지수값은 원천 fact로 저장하고, 계산된 변동률은 `map_layer_snapshots.changePct`에만 저장합니다.

### 규모별/연령별 매매가격지수

- 전체 지역 대표값이 아니라 면적 규모 또는 건축연령으로 나눈 세부 지표입니다.
- 지도 색상 대표값으로 쓰면 사용자가 지역 전체 상승/하락으로 오해할 수 있습니다.
- 지역 상세 리포트에서 "어느 규모/연식이 더 민감한지"를 보여줄 때만 사용합니다.

### 주택 매매가격지수와 아파트 매매가격지수

- `주택` 또는 `종합`이 붙은 지표는 아파트 외 주택 유형이 섞일 수 있습니다.
- `아파트` 지표와 같은 그래프나 지도 색상에 섞으면 기준 대상이 달라집니다.
- DB에는 `housingScope`를 반드시 저장해 `apartment`, `all_housing`, `row_house`, `detached` 같은 범위를 구분합니다.

## 수집 구조

운영 수집은 Spring Batch로 구현합니다.

권장 Job 이름:

- `RebWeeklyAptSalePriceIndexJob`
- `RebMonthlyAptSalePriceIndexJob`
- `RebPriceIndexCoverageAuditJob`

기본 step:

1. provider catalog에서 dataset 메타데이터를 읽습니다.
2. 공공데이터포털 파일데이터 URL 또는 부동산통계 조회 OpenAPI에서 원천을 가져옵니다.
3. 원본 응답을 raw item으로 저장합니다.
4. staging table에서 지표명, 지역명, 기준일, index, 변동률을 정규화합니다.
5. `real_estate_market_facts` 또는 가격 지표 전용 fact table로 promote합니다.
6. 최신 fact 기준으로 `map_layer_snapshots`를 갱신합니다.

idempotent key:

```text
provider + providerDataset + metricCode + regionCode + observedAt + frequency + housingScope + dimension
```

필수 저장 필드:

| 필드 | 설명 |
| --- | --- |
| `provider` | `reb` |
| `providerDataset` | 예: `reb_rone_weekly_apt_sale_price_index_region`, `reb_rone_monthly_apt_sale_price_index` |
| `metricCode` | 서비스 내부 지표 코드 |
| `frequency` | `weekly`, `monthly`, `quarterly` |
| `housingScope` | `apartment`, `all_housing` 등 |
| `dimension` | `region`, `size`, `age`, `housing_type` 등 |
| `regionCode` | 공식 원천 지역 코드 또는 서비스 매핑 코드 |
| `regionTargetId` | 서비스 내부 `real_estate_targets.id` |
| `observedAt` | 해당 지표의 기준 주차/월 |
| `asOf` | 서비스가 이 값을 최신값으로 본 기준 시각 |
| `sourceUpdatedAt` | provider가 갱신한 시각 또는 파일 기준일 |
| `ingestedAt` | 우리 DB에 적재한 시각 |
| `indexValue` | 가격지수 원값. 지도 대표 `changePct` 산출용으로 새로 파생 적재하지 않습니다. |
| `changePct` | 원천 fact에는 저장하지 않습니다. 지도 snapshot 생성 시 저장된 `indexValue` 비교로 산출합니다. |
| `dataStatus` | `ok`, `partial`, `official_missing`, `mapping_unresolved`, `ingestion_missing` |
| `stale` | 화면 표시 기준 최신성 |

## 기존 Python/R-ONE 코드에서 참고할 것

기존 수집 코드를 운영 스케줄러로 유지하지 않습니다. 대신 아래만 Spring Batch 구현 시 참고합니다.

- R-ONE 화면/통계 API에서 확인한 `statblId`, `dtacycleCd`, item id, 지역 코드 파라미터
- CSV/HTML/JSON 파싱 예외와 한글 인코딩 처리 방식
- 지역명 정규화, 시군구명 중복, 구 통합/분리 같은 매핑 테스트 케이스
- API 호출 smoke test와 fixture

즉, "일부만 이식"은 코드를 그대로 들고 온다는 뜻이 아니라 운영 구현에 필요한 발견 사항을 Java/Spring Batch 기준으로 재작성한다는 뜻입니다.

## 지도 색상 계산 기준

- 빨강: 상승, 파랑: 하락
- 진하기: `abs(changePct)`에 비례
- 기준값이 없으면 임의 색을 넣지 않습니다.
- 공식 원천에는 있는데 우리 DB에 없으면 `ingestion_missing`
- DB에는 있는데 target 매핑이 안 되면 `mapping_unresolved`
- 공식 원천에도 없으면 `official_missing`
- `official_missing`은 폐기된 듯한 짙은 회색으로 표시하되, 리포트는 제공하지 않습니다.

## 커버리지 검증

가평, 양평, 서천처럼 화면에서 미공표처럼 보이는 지역은 아래 순서로 확인합니다.

1. `reb_rone_weekly_apt_sale_price_index_region` 원천 CSV/API에 해당 지역 행이 있는지 확인합니다.
2. 행이 있으면 공식 미공표가 아니라 우리 수집/매핑 문제입니다.
3. 행이 없으면 월간 아파트 지표 또는 실거래가격지수에서 대체 가능 여부를 별도 검토합니다.
4. 대체 지표를 쓰더라도 `metricCode`, `frequency`, `housingScope`가 다르므로 같은 색상 스케일에 섞지 않습니다.

## 공식 근거

- 공공데이터포털: `한국부동산원_전국주택가격동향조사_주간아파트동향_매매가격지수(지역별)` 파일데이터
  - https://www.data.go.kr/data/15069873/fileData.do
- 공공데이터포털: `한국부동산원_전국주택가격동향조사_월별동향_아파트_매매가격지수(지역별)` 파일데이터
  - https://www.data.go.kr/data/15069821/fileData.do
- 한국부동산원: 전국주택가격동향조사 설명
  - https://www.reb.or.kr/reb/cm/cntnts/cntntsView.do?cntntsId=1033&mi=10333&statId=S234820263
- 공공데이터포털: 한국부동산원 부동산통계 조회 서비스
  - https://www.data.go.kr/data/15134761/openapi.do

## 현재 구현 기준

- Spring Batch job: `rebWeeklyPriceIndexRefreshJob`
- 원천 URL/env: `REALESTATE_REB_WEEKLY_PRICE_INDEX_URL`
- 기본 스케줄: `REALESTATE_REB_WEEKLY_PRICE_INDEX_BATCH_CRON`, 기본값 `0 30 8 * * THU`
- 적재 위치: `real_estate_market_facts`
- 적재 factType: `price_index`
- 적재 providerDataset: 주간 `reb_rone_weekly_apt_sale_price_index_region`, 월간 `reb_rone_monthly_apt_sale_price_index`
- snapshot 갱신: `map_layer_snapshots`의 `sido`, `sigungu` layer와 `week`, `month`, `quarter`, `halfYear`, `year` period. `week`는 주간 지수 2개, 나머지는 월간 지수 2/4/7/13개가 있어야 생성합니다.
- 프론트 갱신 이벤트: batch 완료 후 SSE `topic=map-layers`를 발행하고, 지도 화면은 `/api/realestate/map/layers`를 다시 조회합니다.
