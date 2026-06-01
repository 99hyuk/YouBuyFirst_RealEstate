# indicator 작업 지침

indicator는 부동산 반응 지표를 소유합니다. 지역/단지별 언급량, 기대/우려, 쟁점 비율, 표본 신뢰도, window snapshot, 유사 상황 검색 후보가 여기에 속합니다.

## 시작

- 지표 정의, snapshot, 점수 산식, 입력/출력 contract가 걸리면 `README.md`의 해당 섹션만 봅니다.
- 지역/단지 식별자나 alias가 문제면 `realestate`를 먼저 봅니다.
- 커뮤니티 원문 수집이나 반응 라벨 자체가 문제면 `community`를 먼저 봅니다.
- 실거래/전세/매물 provider나 stale 기준이 문제면 `realestate`의 market fact contract를 먼저 봅니다.

## 경계

- 원문 수집과 제한 저장은 `community`가 소유합니다.
- 지역/단지 식별자, alias, 법정동 코드, 단지 id 정규화는 `realestate`가 소유합니다.
- AI가 지표를 읽고 사용자용 평가와 근거 로그를 남기는 구조는 `agent`가 소유합니다.
- 화면에서 지표를 어떻게 보여줄지는 `layers/ui`가 소유합니다.

## 기록

- 새 지표, 새 snapshot key, 새 집계 주기가 생기면 정본 이름, 식별자, source/asOf, stale 기준을 함께 남깁니다.
- 임베딩/벡터DB는 기본 matcher가 아니라 확장 분석 레이어입니다. collect -> match target -> classify -> aggregate 기본 흐름을 뒤집지 않습니다.
- 지표가 제품 방향을 바꾸면 `docs/product/PRODUCT_DECISION_NOTES.md`에도 짧게 남깁니다.
