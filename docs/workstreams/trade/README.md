# trade

## 역할

모의투자 도메인을 담당합니다. `market`에서 받은 가격 snapshot을 기준으로 가상 계좌, 주문, 체결, 포트폴리오, 수익률을 계산합니다.

이 트랙은 실제 증권사 주문을 만들지 않습니다. 사용자와 에이전트가 같은 규칙의 모의 환경에서 경쟁할 수 있도록 거래 장부의 정합성을 지키는 데 집중합니다.

## 담당 범위

- 가상 예수금
- 포트폴리오
- 주문과 체결
- 잔고 동시성 제어
- 거래 내역
- 수익률 계산
- 에이전트 주문 요청 수락 contract
- 사용자/에이전트 리더보드용 성과 snapshot

추천 브랜치 예시:

- `codex/trade-order-domain`
- `codex/trade-balance-locking`
- `codex/trade-performance-snapshot`

## 파일 소유권

주로 담당:

- backend account/order/execution domain
- portfolio domain
- trade history domain
- balance locking test

공유 전 협의:

- quote snapshot contract
- agent order request contract
- dashboard API contract
- DB migration

## 현재 우선순위

1. 모의 계좌와 주문/체결 최소 도메인 설계
2. 잔고 동시성 제어 테스트 설계
3. 수익률 계산 기준 문서화
4. 에이전트 주문 요청 contract 설계

## 하지 않는 일

- quote provider 직접 호출
- 커뮤니티 감성 분류
- AI 매매 판단
- 실제 증권사 주문 실행
- UI 레이아웃 구현
