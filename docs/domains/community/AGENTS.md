# community 작업 지침

community는 커뮤니티 글 수집 범위, 원문 제한 저장, 종목 언급 후보, 반응 방향 분류를 소유합니다.

## 시작

- 수집 대상, robots/약관, 원문 저장 범위가 걸리면 `COLLECTION.md`를 봅니다.
- 반응 용어, `reactionDirection`, 긍정/부정/중립 분류가 걸리면 `REACTION_GUIDE.md`를 봅니다.
- 도메인 전체 색인이나 다른 도메인 접점이 필요할 때만 `README.md`를 봅니다.

## 경계

- 종목 alias와 symbol 정본은 `stock`이 소유합니다.
- 개미 심리 지수, 열기 지수, 토픽 클러스터, 유사 상황 검색은 `indicator`가 소유합니다.
- 투자 판단, paper trading 결정, 종목 상세 한줄평 생성은 `agent`가 소유합니다.
- 화면 문구와 배치는 `layers/ui`가 소유합니다.

## 기록

- 수집 정책이나 저장 범위가 바뀌면 `COLLECTION.md`와 필요한 governance 문서를 갱신합니다.
- 반응 분류 기준이 바뀌면 `REACTION_GUIDE.md`를 갱신하고, 제품 표현이 바뀌면 `docs/product/FINAL_PRODUCT_PLAN.md`로 승격합니다.
- 오래된 조사 과정은 README에 누적하지 않고 PR/Notion/archive로 보냅니다.
