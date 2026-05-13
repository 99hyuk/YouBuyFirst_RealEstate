# market-simulation-engine

## 역할

가격 데이터와 모의투자 엔진을 담당합니다. 너나사가 유머 반, 진지 반의 서비스여도 투자 참고 사이트로 납득되려면 감성 지표와 시장 시세가 함께 있어야 합니다.

## 담당 범위

- quote provider adapter
- 실시간 또는 지연 시세 수집
- Redis latest quote cache
- WebSocket/STOMP 가격 브로드캐스트
- stale quote fallback
- 가상 예수금과 포트폴리오
- 모의 주문과 체결
- 잔고 동시성 제어
- AI 에이전트 매매 입력 데이터
- 에이전트별 수익률 리더보드

## 파일 소유권

주로 담당:

- quote collector 관련 runtime
- Redis cache contract
- backend simulation domain
- backend order/execution domain
- WebSocket gateway

공유 전 협의:

- sentiment metric schema
- community signal schema
- dashboard API contract
- external quote provider 이용 조건 문서

## 현재 우선순위

1. 공개 배포 가능한 시세 제공 방식 조사
2. quote snapshot 최소 모델 설계
3. Redis quote cache와 stale quote 정책 설계
4. 모의투자 주문/체결 엔진의 트랜잭션 경계 설계

## 하지 않는 일

- 원문 크롤링
- 커뮤니티 감성 분류
- OCR 자산 연동
- 실제 증권사 주문 실행
