# realestate 작업 지침

realestate는 부동산 프로젝트의 주 도메인입니다. 지역, 단지, alias, 실거래/전세/매물, 정책/개발/교통 이벤트, 부동산 market fact를 소유합니다.

## 시작

- 제품 방향이 필요하면 `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`를 먼저 봅니다.
- 도메인 전체 색인과 데이터 후보가 필요하면 `README.md`를 봅니다.
- region/complex/alias/source/market fact 필드 기준이 필요하면 `DATA_CONTRACT.md`를 봅니다.
- 수집 정책이나 원문 저장 범위가 걸리면 `docs/domains/community/AGENTS.md`와 `docs/domains/community/COLLECTION.md`를 봅니다.
- 반응 지표, window snapshot, 쟁점 비율이 걸리면 `docs/domains/indicator/AGENTS.md`를 봅니다.
- 지역/단지 평가, 유사 과거 비교, 근거 로그가 걸리면 `docs/domains/agent/AGENTS.md`를 봅니다.

## 경계

- 지역/단지 식별자와 alias 정본은 `realestate`가 소유합니다.
- 공공데이터 provider, source registry, market fact freshness 필드의 정본은 `DATA_CONTRACT.md`가 소유합니다.
- 공개 커뮤니티 수집과 제한 원문 저장은 `community`가 소유합니다.
- 반응 방향 판단과 쟁점 분류는 `analysis`/`indicator` 쪽 contract를 따릅니다.
- window 단위 반응 지표와 유사 상황 검색 후보는 `indicator`가 소유합니다.
- AI가 지표와 market fact를 읽고 사용자용 평가를 남기는 구조는 `agent`가 소유합니다.
- 화면 문구와 배치는 `layers/ui`가 소유합니다.
- 기존 `stock`, `market`, `simulation`은 참고 영역이며 부동산 모델 안으로 직접 끌어오지 않습니다.

## 문구와 데이터 원칙

- 서비스는 지역과 단지에 대한 반응, 뉴스/컬럼 이슈, 시장 사실 데이터를 함께 보여주는 관찰형 분석 서비스로 설명합니다.
- 특정 매수, 매도, 청약, 대출 행동을 권유하거나 가격 상승을 단정하는 표현은 쓰지 않습니다.
- 확인되지 않은 데이터는 `unknown`, `null`, `확인 필요`, `mock`으로 구분합니다.
- 실거래/전세/매물/정책 데이터는 provider, `asOf`, `stale`, 지연 여부를 함께 둡니다.
- 커뮤니티 반응은 시장 관찰 데이터이며 서비스 결론처럼 표현하지 않습니다.

## 기록

- 새 대상 모델이 생기면 `README.md`와 `DATA_CONTRACT.md`에 식별자, source, stale 기준을 함께 남깁니다.
- 새 API 후보가 생기면 endpoint, 응답 shape, mock/실데이터 구분, provider/asOf/stale 필드를 함께 남깁니다.
- 수집 정책이나 저장 범위가 바뀌면 community 문서와 governance 문서를 같이 갱신합니다.
