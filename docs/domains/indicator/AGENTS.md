# indicator 작업 지침

indicator는 커뮤니티 기반 핵심 지표를 소유합니다. 열기 지수, 개미 심리 지수, 30분 snapshot, 토픽 클러스터, 임베딩/벡터 기반 유사 상황 검색 후보가 여기에 속합니다.

## 시작

- 지표 정의, snapshot, 점수 산식, 입력/출력 contract가 걸리면 `README.md`의 해당 섹션만 봅니다.
- 커뮤니티 원문 수집이나 반응 라벨 자체가 문제면 `community`를 먼저 봅니다.
- 시세/수급 provider나 stale 기준이 문제면 `market`을 먼저 봅니다.

## 경계

- 원문 수집과 반응 분류는 `community`가 소유합니다.
- 종목 식별자, alias, ticker 정규화는 `stock`이 소유합니다.
- AI가 지표를 읽고 판단하는 전략과 결정 로그는 `agent`가 소유합니다.
- 화면에서 지표를 어떻게 보여줄지는 `layers/ui`가 소유합니다.

## 기록

- 새 지표, 새 snapshot key, 새 집계 주기가 생기면 정본 이름, 식별자, source/asOf, stale 기준을 함께 남깁니다.
- 임베딩/벡터 DB는 기본 matcher가 아니라 확장 분석 레이어입니다. collect -> match -> classify -> aggregate 기본 흐름을 뒤집지 않습니다.
- 지표가 제품 방향을 바꾸면 `docs/product/PRODUCT_DECISION_NOTES.md`에도 짧게 남깁니다.
