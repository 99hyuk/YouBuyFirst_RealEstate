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
- external quote provider 이용 조건 문서
- trade execution price contract
- agent market input contract

## 현재 우선순위

1. `yfinance` + FinanceDataReader 기반 quote snapshot 정책과 provider 이용 조건 정리
2. quote snapshot 최소 모델 설계
3. Redis quote cache와 stale quote 정책 설계
4. WebSocket/STOMP 가격 브로드캐스트 경계 설계
5. 종목 상세 팩트폭격 헤드라인에 필요한 가격/추세 evidence 필드 후보 정리

## 공개 시세 표시 정책

- MVP와 포트폴리오 단계의 기본 조합은 `yfinance` + FinanceDataReader입니다.
- `yfinance`는 국내/미국 시세와 거래량의 1차 provider로 둡니다.
- FinanceDataReader는 국내 종목 메타데이터, 일봉/스냅샷 보강, 국내 투자자별 수급 후보 provider로 둡니다.
- `pykrx`는 기본 조합에서 빼고, FinanceDataReader로 부족한 KRX 수급 검증이 필요할 때만 보조 후보로 남깁니다.
- 공개 화면은 종목별 현재가, 등락률, 거래량 일부 같은 제한된 quote snapshot만 직접 표시할 수 있습니다.
- 직접 표시하는 quote에는 `지연 데이터`, provider, `asOf`, `stale`, `참고용` 상태를 함께 내려야 합니다.
- 차트 전체는 우선 TradingView 같은 외부 위젯을 사용하거나, 자체 차트는 내부 quote snapshot 기반으로 제한된 범위에서 구성합니다.
- 원시 분봉, 호가, 대량 OHLC, 다운로드/API 형태의 재배포는 별도 계약이나 명확한 허용 조건 전까지 만들지 않습니다.
- 서비스 트래픽이 커지거나 수익화/상용화 단계로 넘어가면 국내는 KRX/KOSCOM, 미국은 public display 권한이 있는 데이터 벤더 계약을 다시 검토합니다.

## 하지 않는 일

- 원문 크롤링
- 커뮤니티 반응 방향 분류
- OCR 자산 연동
- 모의 주문 체결
- AI 매매 판단
- 실제 증권사 주문 실행
