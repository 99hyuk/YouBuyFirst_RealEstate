# agent 작업 지침

agent는 지표와 시세를 읽어 paper trading 판단, 커뮤니티별 성과 비교, 페르소나, 결정 로그, 종목 상태 한줄평 생성을 소유합니다.

## 시작

- 종목 상세 상단 한줄평, 톤, evidence contract가 걸리면 `STOCK_DETAIL_HEADLINE.md`를 봅니다.
- 전략, decision key, 성과 비교, 판단 로그가 걸리면 `README.md`의 해당 섹션만 봅니다.
- 입력 지표가 문제면 `indicator`, 시세/수급이 문제면 `market`, 가상 계좌 반영이 문제면 `simulation`을 먼저 봅니다.

## 경계

- 실제 투자 자문, 실거래 지시, 수익 보장처럼 보이는 표현은 만들지 않습니다.
- 장부 수정과 체결 정합성은 `simulation` contract를 통합니다.
- 화면 배너의 시각 표현은 `layers/ui/STOCK_DETAIL_BANNER.md`가 소유합니다.
- 커뮤니티 원문 분석 기준은 `community`, 핵심 지표 산식은 `indicator`가 소유합니다.

## 기록

- 판단 key는 `agentId + windowStart + symbol + strategyVersion`처럼 중복 실행을 막을 수 있게 설계합니다.
- 새 전략이나 판단 로그 필드가 생기면 input, output, skip reason, source/asOf, strategyVersion을 함께 남깁니다.
- 확정된 제품 표현은 `docs/product/FINAL_PRODUCT_PLAN.md`, 고민 단계는 `docs/product/PRODUCT_DECISION_NOTES.md`로 보냅니다.
