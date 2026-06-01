# 기술/제품 리스크 등록부

이 문서는 부동산 전용 프로젝트에서 반복적으로 확인해야 할 기술, 제품, 운영 리스크를 모읍니다. 오래된 주식/모의투자 리스크는 archive나 legacy reference로만 봅니다.

## RISK-001. 부동산 서비스가 행동 지시처럼 보임

- 관련 영역: product, ui, agent
- 증상: 특정 지역/단지에 대해 "오른다", "청약 넣어라", "대출 받아라", "지금 사야 한다"처럼 보이는 문구가 노출됩니다.
- 영향: 법적/평판 리스크와 사용자 오해가 생깁니다.
- 방어: 화면 문구는 관찰, 분석, 반응 지표, 쟁점 비율, 표본 신뢰도, 근거 로그 중심으로 제한합니다.
- 확인: 화면/fixture/docs에서 행동 지시형 표현을 검색합니다.

## RISK-002. 커뮤니티 원문 재게시와 개인정보 노출

- 관련 영역: community, governance, ui
- 증상: 원문 전문, 닉네임, 프로필, 작성자별 추적 정보가 저장되거나 노출됩니다.
- 영향: 저작권, 개인정보, 약관 리스크가 생깁니다.
- 방어: 제목, 일부 snippet, URL, 작성자 해시, 작성 시각, 원문 해시 정도만 제한 저장합니다.
- 확인: ingestion payload와 화면 근거 카드에 원문 전문이나 식별자가 없는지 확인합니다.

## RISK-003. 수집 정책 위반

- 관련 영역: community, pipeline, governance
- 증상: 로그인 세션 크롤링, CAPTCHA 우회, 프록시 회전, fingerprint 위장을 시도합니다.
- 영향: 약관 위반, 차단, 법적 리스크가 커집니다.
- 방어: 공개 HTTP 수집을 우선하고, Playwright는 정책상 허용되는 렌더링 fallback으로만 사용합니다.
- 확인: source policy와 crawler adapter에서 금지 행위가 없는지 리뷰합니다.

## RISK-004. 지역/단지 alias 오탐

- 관련 영역: realestate, community, indicator
- 증상: 일반 단어, 브랜드명, 동명이 지역/단지로 잘못 매칭됩니다.
- 영향: 잘못된 ranking, 반응 지표, 에이전트 평가로 이어집니다.
- 방어: alias confidence, source context, 행정구역/단지 후보, reviewState를 함께 사용합니다.
- 확인: matcher fixture에 동명이/일반명/짧은 별칭 충돌 사례를 넣습니다.

## RISK-005. market fact freshness 오해

- 관련 영역: realestate, ui, agent
- 증상: 지연된 실거래/전세/매물/정책 데이터를 실시간처럼 보여줍니다.
- 영향: 사용자 신뢰와 제품 리스크가 생깁니다.
- 방어: provider, `asOf`, `stale`, dataStatus를 항상 함께 표시합니다.
- 확인: market fact를 노출하는 모든 카드와 timeline에 freshness 배지가 있는지 확인합니다.

## RISK-006. 표본 부족 또는 source 편중 과장

- 관련 영역: indicator, ui, agent
- 증상: 글 수가 적거나 한 source에 편중된 데이터를 강한 결론처럼 보여줍니다.
- 영향: 작은 표본이 지역/단지 상태처럼 과장됩니다.
- 방어: mention count, sourceCount, sourceSkew, confidence를 함께 계산하고 낮은 신뢰도는 흐리게 표시합니다.
- 확인: 낮은 표본 fixture와 source skew fixture를 화면에서 확인합니다.

## RISK-007. 뉴스/컬럼 원인 단정

- 관련 영역: community, realestate, agent
- 증상: 시간상 가까운 뉴스/컬럼을 실제 원인처럼 단정합니다.
- 영향: 잘못된 설명과 신뢰도 저하가 생깁니다.
- 방어: "함께 관찰된 후보", "확인 필요" 표현을 사용하고, 원인 단정은 하지 않습니다.
- 확인: timeline과 summary 문구에서 원인 단정 표현을 검색합니다.

## RISK-008. 유사 과거 상황을 예측처럼 오해

- 관련 영역: indicator, agent, ui
- 증상: 비슷한 과거 상황 비교가 미래 가격 예측처럼 보입니다.
- 영향: 행동 지시와 투자 판단 오해가 생깁니다.
- 방어: "유사 과거", "이후 시장 흐름", "차이점", "caveat"를 함께 표시합니다.
- 확인: similar history 화면에 미래 단정 문구가 없는지 확인합니다.

## RISK-009. AI 평가 근거 부족

- 관련 영역: agent, indicator, realestate
- 증상: 근거 없이 강한 평가 문구가 생성됩니다.
- 영향: 서비스 신뢰도와 법적 리스크가 떨어집니다.
- 방어: 최소 2개 이상의 독립 근거와 dataQuality가 있을 때만 강한 톤을 허용합니다.
- 확인: `summary`, `evidence`, `caveats`, `asOf`, `dataQuality`가 서로 맞는지 리뷰합니다.

## RISK-010. legacy stock 코드와 부동산 모델 혼합

- 관련 영역: realestate, ops, backend, pipeline, ui
- 증상: `stock`, `symbol`, `quote`, `simulation` 모델을 부동산에 그대로 일반화합니다.
- 영향: 도메인 모델이 오염되고 나중에 리팩터링 비용이 커집니다.
- 방어: region/complex/market fact/evidence log를 별도 모델로 두고, legacy 영역은 참고/비활성으로 분리합니다.
- 확인: 새 코드와 문서에서 주식 모델명이 active contract로 들어가지 않았는지 검색합니다.

## RISK-011. 공공데이터 실시간 표기 오해

- 관련 영역: realestate, ui, agent
- 증상: 공공데이터포털의 `업데이트 주기: 실시간` 문구를 사용자 화면에서 매일 확정 공시 또는 즉시 반영 데이터처럼 표현합니다.
- 영향: 실거래 신고 지연, 확정일자 지연, provider 공개 지연을 사용자가 오해합니다.
- 방어: `observedAt`, `asOf`, `sourceUpdatedAt`, `ingestedAt`, `stale`, `dataStatus`를 분리합니다.
- 확인: 공공데이터 카드와 timeline에서 원천 기준 시각과 우리 수집 시각이 구분되는지 확인합니다.

## RISK-012. source 30개 분산으로 인한 crawler 불안정

- 관련 영역: community, pipeline, ops
- 증상: 네이버 카페, 다음 카페, 공개 게시판, 뉴스/컬럼을 한 번에 adapter로 만들다가 차단, 파싱 실패, 중복 저장, 빈 데이터가 늘어납니다.
- 영향: 운영 비용이 커지고 지표 신뢰도가 떨어집니다.
- 방어: 30개 내외 후보를 먼저 `crawl_sources` registry에 `disabled`로 넣고, 공개 접근성/정책/신호 품질/파서 난이도 검토 후 단계적으로 활성화합니다.
- 확인: source별 `status`, `parserStatus`, `coverageStatus`, backoff가 기록되는지 확인합니다.

## 업데이트 규칙

- 새 리스크가 발견되면 원인, 영향, 방어, 확인 방법을 함께 추가합니다.
- 실제 장애 복구 기록은 `docs/governance/TROUBLESHOOTING_GUIDE.md`와 PR/Notion 작업 로그에 남깁니다.
- 오래된 주식 리스크는 이 문서에 계속 누적하지 않고 archive나 legacy reference로 분리합니다.
