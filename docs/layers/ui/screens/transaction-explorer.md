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
- 상단 필터바: 지역, 정렬, 매물 유형, 거래 방식, 검색, 가격 비교 기간을 제공합니다. 기본 진입값은 `아파트`, `전체`, `MoM`입니다.
- 상단 필터바에는 `국토교통부 실거래`, `실좌표 n/n` 같은 provider/좌표 상태 pill을 두지 않습니다.
- 지도 stage: 실좌표가 확인된 거래 후보 marker를 보여주고, 좌측에는 실거래 목록 overlay를 둡니다.
- 상세 패널: marker나 목록 row를 선택하면 거래 요약, 비교 기간별 가격 흐름, 주변 시설, provider 상태를 보여줍니다. 단지명 바로 오른쪽에는 로그인 사용자용 하트 버튼을 둬 `complex` 관심 저장/해제를 지원하고, 그 옆 말풍선 버튼은 현재 단지를 채팅 입력창에 `complex` 첨부 카드로 올립니다. 커뮤니티 반응, 관련 뉴스/콘텐츠, 정책 타임라인은 이 패널에서 조회하거나 표시하지 않습니다. 선택한 항목은 `/realestate/transactions?region=:legalDongCode&property=:propertyType&deal=:dealType&selected=:transactionId` 형태의 복귀 URL로 오른쪽 `최근 본` 탭과 채팅 첨부 카드에 기록하고, 관심 저장 항목은 `/realestate/transactions?region=:legalDongCode&selected=:transactionId` 복귀 URL로 오른쪽 `관심` 탭에 기록합니다. 상세 패널이 열린 상태에서는 지도 중심을 선택 항목 좌표로 두며, route `q` 검색 진입으로 자동 선택된 첫 결과도 같은 기준을 적용합니다. 상세 비교 기간은 패널을 열 때 상단 가격 비교 기간을 한 번 복사하지만, 이후 상세 패널 안에서 바꿔도 상단 지도/목록 비교 기간은 바꾸지 않습니다.

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
- `POST /api/realestate/watch-targets` / `DELETE /api/realestate/watch-targets?targetType=complex&targetId=`: 로그인 사용자의 실거래 상세 관심 저장/해제

오른쪽 `최근 본` 복귀용 query:

- `region`: 법정동/시군구 코드. 없으면 기본 지역으로 진입합니다.
- `property`: `apt`, `offi`, `rh`, `silv`, `sh` 중 하나. 없으면 `apt`를 사용합니다.
- `deal`: `trade`, `rent`, `all` 중 하나. 최근 본 부동산 링크는 실제 선택 항목의 거래 유형을 넣습니다.
- `selected`: 실거래 목록에서 선택했던 `TransactionItem.id`. 목록 로드 후 같은 id가 있으면 상세 패널을 바로 엽니다.
- `q`: 대시보드 검색에서 넘어온 단지명/동명 필터. 목록 로드 후 첫 매칭 항목이 있으면 상세 패널을 바로 열고 지도 중심을 해당 좌표로 둡니다.

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
- 2026-06-25: 실거래 단지 지오코딩과 검색 필터는 `시군구+동+공식명` 단일 문자열에만 의존하지 않는다. 지번이 있으면 `시군구+동+지번`을 먼저 시도하고, `블록 -> 단지` 별칭 후보와 지역 거리 검증을 함께 적용한다. 카카오가 너무 넓은 별칭을 다른 지역으로 매칭하면 기본 근사좌표 상태를 유지한다.
- 2026-06-25: 실거래 지도 기준월을 `202606`으로 맞추고 비교월을 `202605`(MoM), `202512`(6개월), `202506`(YoY)로 전환한다. 비교월 데이터가 없으면 마커는 중립색으로 남는다.
- 2026-06-25: 상세 패널 하단의 커뮤니티 반응, 관련 뉴스/콘텐츠, 정책 타임라인 블록과 해당 target lookup/fetch 흐름을 제거한다. 상세 패널은 거래 요약, 가격 흐름, 주변 시설, provider 상태만 유지한다.
- 2026-06-25: 실거래 화면 기본 필터를 `아파트`, `전체`, `MoM`으로 두고, 가격 비교 기간 버튼은 `MoM`, `6개월`, `YoY` 순서로 배치한다. 정렬 select는 매물 유형 chip 묶음 왼쪽에 배치한다.
- 2026-06-25: 실거래 marker/목록 row 선택 시 오른쪽 `최근 본` 탭에 부동산을 기록하고, `region/property/deal/selected` query로 같은 상세 패널을 복구하는 기준을 추가.
- 2026-06-25: 대시보드 검색의 route `q` 진입에서 첫 매칭 단지를 자동 선택하고, 상세 패널이 열릴 때 지도 중심을 선택 단지 좌표로 맞추는 기준을 추가.
- 2026-06-25: 상단 가격 비교 기간과 상세 패널 비교 기간을 분리한다. 상세 패널은 열릴 때만 현재 상단 기간을 기본값으로 받고, 이후 상세 내부 변경은 선택 단지 가격 흐름에만 적용한다.
- 2026-06-25: 상세 패널의 단지명 바로 오른쪽 하트로 로그인 사용자 기반 `complex` 관심 저장/해제를 지원하고, 오른쪽 `관심` 탭에서 저장된 실거래 상세 경로로 복귀하는 기준 추가.
- 2026-06-25: 상세 패널 하트 옆 말풍선 버튼으로 선택 단지를 채팅 입력창에 첨부한다. 첨부에는 단지명, 위치/가격, 상세 비교 기간 등락률 또는 `비교데이터 없음`, `region/property/deal/selected` 복귀 URL을 포함한다.
