# market

## 역할

가격 데이터와 시세 전달 경로를 담당합니다. 너나사가 유머 반, 진지 반의 서비스여도 투자 참고 사이트로 납득되려면 감성 지표와 시장 시세가 함께 있어야 합니다.

이 트랙은 시세/호가와 quote cache만 소유합니다. 주문/체결은 `trade`, 매매 판단은 `agent`가 맡습니다.

## 담당 범위

- quote provider adapter
- 실시간 또는 지연 시세 수집
- Redis latest quote cache
- WebSocket/STOMP 가격 브로드캐스트
- stale quote fallback
- 시세 provider 이용 조건과 공개 노출 정책

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
- external quote provider 이용 조건 문서
- trade execution price contract
- agent market input contract

## 현재 우선순위

1. 공개 배포 가능한 시세 제공 방식 조사
2. quote snapshot 최소 모델 설계
3. Redis quote cache와 stale quote 정책 설계
4. WebSocket/STOMP 가격 브로드캐스트 경계 설계

## 하지 않는 일

- 원문 크롤링
- 커뮤니티 감성 분류
- OCR 자산 연동
- 모의 주문 체결
- AI 매매 판단
- 실제 증권사 주문 실행
