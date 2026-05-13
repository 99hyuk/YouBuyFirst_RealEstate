# market-simulation-engine

## 역할

가격 데이터와 모의투자 엔진을 담당합니다. 너나사가 유머 반, 진지 반의 서비스여도 투자 참고 사이트로 납득되려면 감성 지표와 시장 시세가 함께 있어야 합니다.

이 트랙은 기술 성격이 다른 일을 포함하므로 내부 lane을 나눕니다. 하나의 에이전트가 모든 lane을 동시에 구현하지 않습니다.

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

## 내부 lane

### market-data lane

시세와 종목 시장 데이터를 다룹니다.

- quote provider adapter
- 실시간 또는 지연 시세 수집
- Redis latest quote cache
- WebSocket/STOMP 가격 브로드캐스트
- stale quote fallback
- 시세 provider 이용 조건과 공개 노출 정책

추천 브랜치 예시:

- `codex/market-quote-snapshot-contract`
- `codex/market-redis-quote-cache`

### simulation-core lane

모의투자 도메인을 다룹니다.

- 가상 예수금
- 포트폴리오
- 주문/체결
- 잔고 동시성 제어
- 거래 내역과 수익률 계산

추천 브랜치 예시:

- `codex/market-sim-order-domain`
- `codex/market-sim-balance-locking`

### agent-runtime lane

AI 에이전트 실행과 성과 비교를 다룹니다.

- 에이전트 페르소나
- 매매 판단 입력 데이터
- 사용자용 결정 근거
- 에이전트별 성과 리더보드

추천 브랜치 예시:

- `codex/market-agent-personas`
- `codex/market-agent-decision-log`

lane 간 계약:

- `market-data`는 quote snapshot 계약만 제공합니다.
- `simulation-core`는 quote snapshot을 읽지만 quote provider를 직접 호출하지 않습니다.
- `agent-runtime`은 sentiment metric, community signal, quote snapshot, portfolio state를 입력으로 받지만 주문 체결 로직을 직접 소유하지 않습니다.
- lane을 가로지르는 변경은 먼저 작은 계약 PR로 분리합니다.

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
