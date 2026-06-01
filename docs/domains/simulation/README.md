# simulation

> Legacy stock reference: 부동산 1차 범위에서는 모의투자/주문/원장 도메인을 활성 기능으로 보지 않습니다.

## 역할

모의투자 도메인을 담당합니다. `market`에서 받은 가격 snapshot을 기준으로 가상 계좌, 주문, 체결, 포트폴리오, 수익률을 계산합니다.

이 도메인은 실제 증권사 주문이나 결제를 만들지 않습니다. 사용자와 에이전트가 같은 규칙의 모의 환경에서 경쟁할 수 있도록 주문, 체결, 정산, 원장, 포지션의 트랜잭션 정합성을 지키는 데 집중합니다.

금융권 포트폴리오 관점에서 이 도메인의 핵심은 실사용자 주문 동시성보다 거래성 데이터의 원장 무결성입니다. 에이전트 판단 job이나 체결 worker가 재시도되어도 같은 주문이 중복 체결되지 않고, 현금/보유 수량/손익이 원장에서 다시 설명 가능해야 합니다.

## 담당 범위

- 가상 계좌와 예수금
- 포트폴리오
- 주문과 체결
- 주문 예약, 체결, 정산 트랜잭션
- 거래 원장과 포지션 평균단가
- 주문/체결 idempotency key
- 에이전트 배치 재시도와 중복 체결 방지
- 거래 내역
- 수익률 계산
- 에이전트 주문 요청 수락 contract
- 사용자/에이전트 리더보드용 성과 snapshot

추천 브랜치 예시:

- `codex/trade-order-domain`
- `codex/trade-ledger-transaction`
- `codex/trade-performance-snapshot`

## 파일 소유권

주로 담당:

- backend account/order/execution domain
- portfolio domain
- trade history domain
- ledger entry domain
- order reservation and idempotency test

공유 전 협의:

- quote snapshot contract
- agent order request contract
- dashboard API contract
- DB migration

## 현재 우선순위

1. 모의 계좌, 주문, 예약, 체결, 원장 최소 도메인 설계
2. 주문 생성/체결 처리 트랜잭션 경계 정의
3. 주문/체결 idempotency key와 중복 체결 방지 테스트 설계
4. 수익률 계산 기준과 원장 기반 재계산 방식 문서화
5. 에이전트 주문 요청 contract 설계

## 하지 않는 일

- quote provider 직접 호출
- 커뮤니티 반응 방향 분류
- AI 매매 판단
- 실제 증권사 주문 실행
- 실제 결제, 입출금, 증권사 API 연동
- UI 레이아웃 구현
