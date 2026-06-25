# 실거래 화면

## Route

- Parent: root
- Route 정보: `/realestate/transactions`
- Legacy route 후보: `/realestate/reactions`는 전환 기간 동안 redirect
- Child screens:
  - `region-detail`: `/realestate/targets/:targetId`

> 기존 `지역 반응` 화면은 정본에서 내립니다. 커뮤니티 반응 랭킹은 핵심 화면이 아니라 필요할 때 지역 상세나 근거 로그 안에서 보조 관찰 신호로만 사용합니다.

## 화면 목적

사용자가 공식 실거래와 전월세 데이터를 지역, 기간, 거래유형, 가격대, 면적 조건으로 탐색합니다. 이 화면은 특정 단지나 거래를 추천하지 않고, 실제 공공데이터의 범위와 공개 지연 상태를 분명히 보여줍니다.

지도 화면이 지역별 흐름을 공간적으로 보여준다면, 실거래 화면은 사용자가 조건을 좁혀 실제 거래 row와 지역 집계를 비교하는 도구입니다.

## 현재 섹션

- 네비게이션 문구는 `실거래`, 정본 route는 `/realestate/transactions`로 둡니다.
- 기존 `/realestate/reactions`는 북마크 호환용 redirect로만 둡니다.
- 상단 필터바: 지역, 매물 유형, 거래 방식, 검색, 정렬, 가격 비교 기간을 제공합니다.
- 상단 필터바에는 `국토교통부 실거래`, `실좌표 n/n` 같은 provider/좌표 상태 pill을 두지 않습니다.
- 지도 stage: 실좌표가 확인된 거래 후보 marker를 보여주고, 좌측에는 실거래 목록 overlay를 둡니다.
- 상세 패널: marker나 목록 row를 선택하면 거래 요약, 비교 기간별 가격 흐름, 주변 시설, provider 상태를 보여줍니다.

## 상태와 빈 화면

- loading: 필터 skeleton과 거래 table skeleton을 먼저 보여줍니다.
- empty: 조건에 맞는 공식 거래가 없으면 `공식 거래 없음`과 공개 지연 가능성을 표시합니다.
- error: 실거래, 전월세, 지역 정본, provider별 실패 상태를 분리합니다.
- stale/insufficient: 거래일과 공개/적재 시각 차이를 보여주고, 오래된 bootstrap 데이터는 최신 거래처럼 표시하지 않습니다.

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |
| `filters.regions[]` | realestate/backend | 검색 가능한 지역/생활권/법정동 후보 |
| `summary.totalTrades` | realestate/backend | 현재 조건의 거래 수 |
| `summary.medianPrice` | realestate/backend | 현재 조건의 중위 거래가 또는 보증금 |
| `summary.latestObservedAt` | realestate/backend | 가장 최근 거래 관측 시각 |
| `rows[].targetId` | realestate/backend | `real_estate_targets.id`와 같은 내부 target id |
| `rows[].regionName` | realestate/backend | 시군구·읍면동·생활권 표시명 |
| `rows[].complexName` | realestate/backend | 공식 단지명이 확인된 경우만 표시 |
| `rows[].tradeType` | realestate/backend | `apt_trade`, `apt_rent` 등 거래유형 |
| `rows[].contractDate` | realestate/backend | 계약일 |
| `rows[].areaM2` | realestate/backend | 전용면적 |
| `rows[].priceText` | realestate/backend | 매매가 또는 보증금/월세 사용자 표시값 |
| `rows[].floor` | realestate/backend | 층 |
| `rows[].provider` | realestate/backend | 국토교통부 등 원천 |
| `rows[].asOf` | realestate/backend | 기준월 또는 원천 기준 시각 |
| `rows[].stale` | backend | 공개/적재 지연 여부 |
| `regionAggregates[]` | realestate/backend | 거래 많은 지역, 가격 변화 큰 지역 등 조건별 집계 |

예상 endpoint:

- `GET /api/realestate/transactions?regionId=&tradeType=&from=&to=&priceMin=&priceMax=&areaMin=&areaMax=&page=&pageSize=`
- `GET /api/realestate/transactions/summary?regionId=&tradeType=&from=&to=`

## 결정된 기준과 확인 필요

- route는 `/realestate/transactions`를 새 정본으로 둔다. 기존 `/realestate/reactions`는 전환 기간 redirect로만 사용한다.
- 필터 기본값을 최근 1개월, 3개월, 6개월 중 무엇으로 둘지.
- 매매와 전월세를 한 테이블에서 함께 보여줄지, segmented control로 나눌지.
- 실거래 row에서 단지명을 어느 수준까지 노출할지. 공식 단지명이 불명확하면 지역명만 보여줍니다.

## 변경 로그

- 2026-06-22: `지역 반응` 정본 화면을 내리고, 실거래/전월세 공식 데이터 기반 탐색 화면으로 전환.
- 2026-06-22: 팀원 구현 전까지 페이지 내부 UI 없이 빈 shell만 제공하고, 네비게이션 문구는 `실거래`로 확정.
- 2026-06-24: 실거래 지도 상단의 provider/좌표 상태 pill을 제거하고 필터 조작만 남김.
- 2026-06-24: 지역 선택 목록은 DB `real_estate_regions` 중 9개 MOLIT 실거래 market-data target이 모두 있는 시군구 275개를 기준으로 생성한다.
- 2026-06-25: 지역 선택 UI는 시도 select와 시군구 select를 분리하고, 시도 변경 시 해당 시군구 목록의 첫 지역으로 전환한다.
- 2026-06-25: 지역 select는 밝은 청록 계열로 유지하고, 오른쪽 필터 chip/search/sort는 따뜻한 주황 계열로 분리한다. 선택된 chip은 주황 그라데이션 배경으로 눌림 상태를 더 강하게 표시한다.
- 2026-06-25: 실거래 단지 지오코딩은 `시군구+동+공식명` 단일 쿼리에만 의존하지 않고, `블록 -> 단지` 별칭 후보와 지역 거리 검증을 함께 적용한다. 카카오가 너무 넓은 별칭을 다른 지역으로 매칭하면 기본 근사좌표 상태를 유지한다.
