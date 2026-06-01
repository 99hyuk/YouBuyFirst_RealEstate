# market 작업 지침

> Legacy stock reference: 이 부동산 전용 프로젝트에서는 새 market 작업을 열지 않습니다. 부동산 market fact는 `realestate`에서 다룹니다.

market은 시세, 차트 캔들, 투자자 수급, provider/cache/stale 기준을 소유합니다.

## 시작

- quote snapshot 변경이면 `QUOTE_SNAPSHOT.md`를 봅니다.
- chart candle, 일봉/분봉, 날짜 key가 걸리면 `CHART_CANDLES.md`를 봅니다.
- 투자자 수급, 개인/외국인/기관 흐름이면 `INVESTOR_FLOWS.md`를 봅니다.
- provider 역할과 전체 색인이 필요할 때만 `README.md`를 봅니다.

## 경계

- 종목 master와 symbol/alias 정규화는 `stock`이 소유합니다.
- 지표 산식과 커뮤니티 기반 snapshot은 `indicator`가 소유합니다.
- 주문/체결/가상 계좌는 `simulation`이 소유합니다.
- 매매 판단과 종목 상태 한줄평 생성은 `agent`가 소유합니다.
- 차트 UI 표현은 `layers/ui`가 소유합니다.

## 기록

- provider를 바꾸거나 추가하면 출처, 지연 시간, 호출 제한, 재배포 가능성, stale 표시 기준을 함께 남깁니다.
- `bars[].date` 같은 거래일 key는 거래소 현지 날짜 기준을 유지합니다.
- 공개 화면에 노출되는 데이터는 mock/stale/asOf/provider 표시가 누락되지 않게 합니다.
