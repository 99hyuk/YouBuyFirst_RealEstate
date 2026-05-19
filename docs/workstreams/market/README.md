# market

## 역할

가격 데이터와 시세 전달 경로를 담당합니다. 너나사가 유머 반, 진지 반의 서비스여도 투자 참고 사이트로 납득되려면 커뮤니티 반응 지표와 시장 시세가 함께 있어야 합니다.

이 트랙은 시세/호가와 quote cache만 소유합니다. 주문/체결은 `trade`, 매매 판단은 `agent`가 맡습니다.

## 담당 범위

- quote provider adapter
- 실시간 또는 지연 시세 수집
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

1. 30분 지연 quote snapshot 직접 표시 정책과 provider 이용 조건 정리
2. quote snapshot 최소 모델 설계
3. Redis quote cache와 stale quote 정책 설계
4. WebSocket/STOMP 가격 브로드캐스트 경계 설계
5. 종목 상세 팩트폭격 헤드라인에 필요한 가격/추세 evidence 필드 후보 정리

## 공개 시세 표시 정책

- 공개 화면은 종목별 현재가, 등락률, 거래량 일부 같은 제한된 quote snapshot을 직접 표시할 수 있습니다.
- 직접 표시하는 quote에는 `30분 지연`, provider, `asOf`, `stale` 상태를 함께 내려야 합니다.
- 차트 전체는 우선 TradingView 같은 외부 위젯을 사용하고, 내부 에이전트/모의투자 계산은 별도 quote snapshot을 참조합니다.
- 원시 분봉, 호가, 대량 OHLC, 다운로드/API 형태의 재배포는 별도 계약이나 명확한 허용 조건 전까지 만들지 않습니다.

## 하지 않는 일

- 원문 크롤링
- 커뮤니티 반응 방향 분류
- OCR 자산 연동
- 모의 주문 체결
- AI 매매 판단
- 실제 증권사 주문 실행
