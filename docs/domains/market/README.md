# market

## 역할

가격 데이터와 시세 전달 경로를 담당합니다. 너나사가 유머 반, 진지 반의 서비스여도 투자 참고 사이트로 납득되려면 커뮤니티 반응 지표와 시장 시세가 함께 있어야 합니다.

이 트랙은 시세/호가와 quote cache만 소유합니다. 주문/체결은 `trade`, 매매 판단은 `agent`가 맡습니다.

## 담당 범위

- quote provider adapter
- 지연 시세 수집과 실시간 전환 가능성 검토
- Redis latest quote cache
- WebSocket/STOMP 가격 브로드캐스트
- stale quote fallback
- 시세 provider 이용 조건과 공개 노출 정책
- 종목 상세 팩트폭격 헤드라인의 가격/추세/거래량/호가 근거 필드

추천 브랜치 예시:

- `codex/market-quote-snapshot-contract`
- `codex/market-redis-quote-cache`

## 파일 소유권

주로 담당:

- quote collector 관련 runtime
- Redis cache contract
- WebSocket gateway

공유 전 협의:

- analysis/indicator schema
- community signal schema
- dashboard API contract
- stock detail roast headline API contract
- stock detail chart candle display contract
- external quote provider 이용 조건 문서
- trade execution price contract
- agent market input contract

## 현재 우선순위

1. 프론트 종목 상세에서 `GET /api/market/chart-candles` 차트 blocker 해제 확인
2. 국내 전체 종목 대상 전 거래일 개인/외국인/기관 수급 slice provider spike
3. front 브랜치에 최신 market API와 scheduler 반영
4. Redis quote cache와 WebSocket/STOMP 가격 브로드캐스트 경계 설계
5. provider 공개 표시 조건과 상용화 전 vendor 전환 기준 재검토

## 구현된 세로 슬라이스

- pipeline은 `yfinance`로 국내/미국 가격, 거래량, 전일 종가 기준 등락률을 조회하고 FinanceDataReader를 국내 종목 메타데이터 후보 provider로 사용합니다.
- backend는 `POST /internal/market/quote-snapshots`로 snapshot을 upsert하고, `GET /api/quotes?symbols=...`로 프론트용 응답을 제공합니다.
- 공개 응답에는 `symbol`, `name`, `market`, `currency`, `price`, `change`, `changePct`, `volume`, `asOf`, `provider`, `delayLabel`, `stale`, `dataStatus`가 포함됩니다.
- 프론트 fixture는 같은 응답 shape로 맞춰져 있어 mock에서 API 호출로 교체할 수 있습니다.
- 세부 계약과 예시 JSON은 `docs/domains/market/QUOTE_SNAPSHOT.md`를 기준으로 봅니다.
- chart candle slice는 `POST /internal/market/chart-candles`로 bounded OHLC bars를 저장하고, `GET /api/market/chart-candles?symbol=005930.KS&range=5Y&interval=1d` 같은 프론트 차트용 display-only 응답을 제공합니다. 공개 범위는 `1M/3M/6M/1Y/3Y/5Y`까지만 허용합니다.
- chart candle 응답에는 `symbol`, `name`, `market`, `currency`, `range`, `interval`, `provider`, `delayLabel`, `asOf`, `stale`, `dataStatus`, `bars`, `displayPolicy`가 포함됩니다.
- chart candle bars에는 `date`, `open`, `high`, `low`, `close`, `volume`만 포함하며 개인/외국인/기관 수급은 별도 전 거래일 수급 slice로 분리합니다.
- pipeline `serve` runtime은 market refresh job을 함께 등록해 `quote_snapshots`와 `chart_candle_sets` display cache를 기본 10분 주기로 갱신합니다.

## 공개 시세 표시 정책

- MVP와 포트폴리오 단계의 기본 조합은 `yfinance` + FinanceDataReader입니다.
- `yfinance`는 국내/미국 시세와 거래량의 1차 provider로 둡니다.
- FinanceDataReader는 국내 종목 메타데이터와 일부 스냅샷 보강 후보로 둡니다.
- 국내 전체 종목 대상 전 거래일 수급은 `naver-finance` provider를 1차 구현으로 둡니다. 네이버 금융 표에서 외국인/기관 순매수 수량을 관찰하고, 개인 수량은 잔차로 계산해 `derived=true`로 표시합니다.
- `pykrx`는 KRX 응답/세션 문제가 있어 선택 검증 provider로만 둡니다. FinanceDataReader는 종목 메타데이터 보강에 사용하고, 현재 수급 wrapper는 표 구조 호환성 문제로 1차 provider로 쓰지 않습니다.
- 공개 화면은 종목별 현재가, 등락률, 거래량 일부 같은 제한된 quote snapshot만 직접 표시할 수 있습니다.
- 직접 표시하는 quote에는 `지연 데이터`, provider, `asOf`, `stale`, `참고용` 상태를 함께 내려야 합니다.
- `.KS`/`.KQ` quote는 Yahoo Finance 원천 20분 지연과 pipeline 기본 10분 갱신 주기를 합쳐 공개 화면에서는 최대 30분 지연으로 표시합니다.
- 미국 quote는 지연 시간을 단정하지 않고 10분 주기 refresh snapshot으로 표시합니다.
- 종목별 개인/외국인/기관 수급은 quote snapshot과 분리하고 거래일별 확정 관찰 데이터로만 다룹니다.
- 차트 전체는 우선 TradingView 같은 외부 위젯을 사용하거나, 별도 chart candle display API가 있을 때만 자체 차트로 구성합니다. quote snapshot만으로 캔들을 만들거나 fixture를 실제 종목 차트처럼 보이게 하지 않습니다.
- 원시 분봉, 호가, 대량 OHLC, 다운로드/API 형태의 재배포는 별도 계약이나 명확한 허용 조건 전까지 만들지 않습니다.
- 서비스 트래픽이 커지거나 수익화/상용화 단계로 넘어가면 국내는 KRX/KOSCOM, 미국은 public display 권한이 있는 데이터 벤더 계약을 다시 검토합니다.
- quote snapshot 세부 API 계약, 캐시/stale 기준, KODEX 200 수급 후보는 `docs/domains/market/QUOTE_SNAPSHOT.md`를 기준으로 봅니다.
- 종목 상세 실제 차트용 display-only OHLC API 계약은 `docs/domains/market/CHART_CANDLES.md`를 기준으로 봅니다.
- 국내 종목/ETF 전 거래일 개인/외국인/기관 수급 API 계약은 `docs/domains/market/INVESTOR_FLOWS.md`를 기준으로 봅니다.

## 종목별 수급 history slice

- backend는 `POST /internal/market/investor-flows`로 거래일별 수급 row를 upsert하고, `GET /api/market/investor-flows/history?symbol=005930.KS&limit=20`로 프론트용 최신순 history 응답을 제공합니다.
- 공개 응답에는 `symbol`, `name`, `market`, `currency`, `tradeDate`, `provider`, `sourceLabel`, `delayLabel`, `asOf`, `stale`, `dataStatus`, `individual`, `foreign`, `institution`이 포함됩니다.
- 단일 최신 수급 public endpoint는 두지 않습니다. 최신 1건이 필요하면 history 응답의 첫 번째 row를 사용합니다.
- pipeline은 기본 `naver-finance` adapter로 네이버 금융 거래일별 수급 표를 읽습니다. 외국인/기관은 관찰 수량, 개인은 `-(외국인 + 기관)` 잔차이며, provider가 금액을 제공하지 않으면 `netAmount=null`로 내려갑니다.
- `serve` runtime은 quote/chart 10분 refresh와 별개로 한국시간 평일 18:30 수급 refresh job을 등록합니다.
- provider 실패 시 pipeline은 실패 row를 publish하지 않고 public history API는 빈 배열을 반환합니다. 프론트는 history 배열이 비면 수급 영역을 숨깁니다.

## 하지 않는 일

- 원문 크롤링
- 커뮤니티 반응 방향 분류
- OCR 자산 연동
- 모의 주문 체결
- AI 매매 판단
- 실제 증권사 주문 실행
