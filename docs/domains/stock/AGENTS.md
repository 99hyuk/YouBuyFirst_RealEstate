# stock 작업 지침

> Legacy stock reference: 이 부동산 전용 프로젝트에서는 새 작업 영역으로 선택하지 않습니다. 기존 구조 참고나 후속 삭제 후보 정리에만 사용합니다.

stock은 종목 master, symbol, market code, ticker, alias, 검색/매칭 기준을 소유합니다.

## 시작

- 종목 식별자, alias, ticker, 국내/미국 market code가 걸리면 `README.md`의 관련 섹션만 봅니다.
- 커뮤니티에서 종목을 어떻게 언급했는지 분류하는 문제는 `community`와 함께 봅니다.
- 시세 provider symbol 변환은 `market`과 함께 봅니다.

## 경계

- stock은 종목을 식별하고 정규화합니다. 반응 방향, 지표 산식, 매매 판단은 각각 `community`, `indicator`, `agent`가 소유합니다.
- alias를 추가할 때는 source, confidence, 충돌 가능성을 함께 남깁니다.
- 종목명이 사람/일반명사/밈과 충돌할 수 있으면 자동 확정하지 말고 후보 상태를 둡니다.

## 기록

- 새 식별자나 상태값은 API/DB에서 같은 이름으로 쓰일 수 있게 명확히 정의합니다.
- 확인할 수 없는 값은 `unknown`, `null`, `확인 필요`, `mock`처럼 구분합니다.
