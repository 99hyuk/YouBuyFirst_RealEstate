# agent 작업 지침

agent는 지역/단지 반응 지표와 시장 사실 데이터를 읽어 사용자용 평가, 유사 과거 비교 설명, 근거 로그를 소유합니다.

## 시작

- 지역/단지 평가 문구, 톤, evidence contract가 걸리면 `REAL_ESTATE_EVALUATION_COPY.md`를 봅니다.
- 평가 입력, evidence log, evaluation key가 걸리면 `README.md`의 해당 섹션만 봅니다.
- 입력 지표가 문제면 `indicator`, 지역/단지 식별자가 문제면 `realestate`, 수집 원문이 문제면 `community`를 먼저 봅니다.

## 경계

- 특정 매수, 매도, 청약, 대출 행동을 권유하지 않습니다.
- 가격 상승, 청약 성공, 수익을 단정하지 않습니다.
- 커뮤니티 원문 분석 기준은 `community`, 핵심 지표 산식은 `indicator`, market fact 정본은 `realestate`가 소유합니다.
- 화면 배너와 레이아웃은 `layers/ui`가 소유합니다.

## 기록

- evaluation key는 `targetType + targetId + windowStart + evaluationVersion`처럼 중복 실행을 막을 수 있게 설계합니다.
- 새 평가나 근거 로그 필드가 생기면 input, output, skip reason, source/asOf, evaluationVersion을 함께 남깁니다.
- 확정된 제품 표현은 `docs/product/FINAL_PRODUCT_PLAN.md`, 고민 단계는 `docs/product/PRODUCT_DECISION_NOTES.md`로 보냅니다.
