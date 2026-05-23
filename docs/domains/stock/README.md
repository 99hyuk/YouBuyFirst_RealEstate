# stock

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
| 종목 key | 시장 suffix를 포함한 provider-safe symbol을 우선 사용합니다. 예: `005930.KS`, `AAPL` |
| 별칭 | 승인된 alias registry와 후보 alias를 구분합니다. |
| 불확실한 매칭 | 추측으로 확정하지 않고 confidence와 후보 상태를 둡니다. |

## 다른 도메인과의 접점

- `community`: 글에서 종목 후보를 찾을 때 stock 기준을 씁니다.
- `market`: quote/chart/investor flow provider symbol과 매핑합니다.
- `indicator`: 30분 snapshot과 지표를 같은 symbol 기준으로 집계합니다.
- `agent`: 판단 key와 결정 로그의 symbol 기준으로 씁니다.
- `layers/ui`: 검색창, 종목 카드, 상세 route에서 표시 이름과 symbol을 사용합니다.

## 하지 않는 일

- 커뮤니티 반응 방향 분류
- 시세 provider 호출
- 지표 산식 계산
- 에이전트 매매 판단
