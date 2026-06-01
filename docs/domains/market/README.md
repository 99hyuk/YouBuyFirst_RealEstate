# market

> Legacy stock reference: 주식 quote/chart 참고 영역입니다. 부동산 실거래/전세/매물/정책 market fact는 `realestate`가 소유합니다.

## 역할

가격 데이터, 차트 캔들, 투자자 수급, provider/cache/stale 기준을 담당합니다. 주문/체결은 `simulation`, 매매 판단과 종목 상태 한줄평은 `agent`, 차트 UI 표현은 `layers/ui`가 소유합니다.

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

- indicator schema
- community signal schema
- dashboard API contract
- stock detail roast headline API contract
- stock detail chart candle display contract
- external quote provider 이용 조건 문서
- simulation execution price contract
- agent market input contract

## 현재 우선순위

1. 프론트 종목 상세에서 `GET /api/market/chart-candles` 차트 blocker 해제 확인
2. 국내 전체 종목 대상 전 거래일 개인/외국인/기관 수급 slice provider spike
3. front 브랜치에 최신 market API와 scheduler 반영
4. Redis quote cache와 WebSocket/STOMP 가격 브로드캐스트 경계 설계
5. provider 공개 표시 조건과 상용화 전 vendor 전환 기준 재검토

## 구현된 세로 슬라이스

- Quote snapshot: 국내/미국 가격, 거래량, 전일 종가 기준 등락률을 display cache로 제공합니다. 정본 계약은 `QUOTE_SNAPSHOT.md`입니다.
- Chart candles: bounded daily OHLC bars를 프론트 차트용 display-only 응답으로 제공합니다. 정본 계약은 `CHART_CANDLES.md`입니다.
- Investor flows: 국내 종목/ETF 전 거래일 개인/외국인/기관 수급 history를 quote snapshot과 분리합니다. 정본 계약은 `INVESTOR_FLOWS.md`입니다.
- Pipeline `serve` runtime은 quote/chart refresh job과 수급 refresh job을 등록합니다. 주기와 실패 처리 기준은 각 contract 문서를 봅니다.

## 공개 시세 표시 정책

- MVP 기본 조합은 quote/chart `yfinance` + FinanceDataReader, 국내 수급 `naver-finance` provider입니다.
- 공개 화면에는 `지연 데이터`, provider, `asOf`, `stale`, `참고용` 상태를 함께 표시합니다.
- `.KS`/`.KQ` quote는 Yahoo Finance 원천 20분 지연과 pipeline 10분 갱신 주기를 합쳐 최대 30분 지연으로 표시합니다. 미국 quote는 지연 시간을 단정하지 않고 refresh snapshot으로 표시합니다.
- 종목별 개인/외국인/기관 수급은 quote snapshot과 분리하고 거래일별 확정 관찰 데이터로만 다룹니다. 개인 수급이 잔차 계산이면 `derived=true`로 표시합니다.
- 원시 분봉, 호가, 대량 OHLC, 다운로드/API 형태의 재배포는 별도 계약이나 명확한 허용 조건 전까지 만들지 않습니다.
- 서비스 트래픽이 커지거나 수익화/상용화 단계로 넘어가면 국내는 KRX/KOSCOM, 미국은 public display 권한이 있는 데이터 벤더 계약을 다시 검토합니다.

## 종목별 수급 history slice

현재 수급 상세 기준은 `INVESTOR_FLOWS.md`가 소유합니다. 이 README에는 중복 API 필드와 scheduler 세부값을 복제하지 않습니다.

## 하지 않는 일

- 원문 크롤링
- 커뮤니티 반응 방향 분류
- OCR 자산 연동
- 모의 주문 체결
- AI 매매 판단
- 실제 증권사 주문 실행
