# 너나사 부동산 프로젝트 기획 요약

## 제품 방향

너나사 부동산은 지역과 단지에 대한 실제 사람들의 반응, 뉴스/컬럼 이슈, 실거래/전세/매물 같은 시장 사실 데이터를 함께 보여주는 관찰형 분석 서비스입니다. 완제품 기준은 `docs/product/FINAL_PRODUCT_PLAN.md`이고, 핵심 구현 범위는 `docs/product/CORE_IMPLEMENTATION_SCOPE.md`와 `docs/product/real-estate-one-page-plan.html`입니다. 부동산 전환의 핵심 원칙은 `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`입니다.

이 프로젝트는 커뮤니티 수집, 반응 분석, 지표화, 유사 과거 비교, 에이전트 근거 로그 구조를 부동산 target 기준으로 구현합니다. 부동산이 이 repo의 주 도메인입니다.

부동산은 대상이 지역, 단지, 생활권, 정책 영향권으로 잘게 나뉘고 지역 단위 상승과 정책 이벤트에 민감합니다. 그래서 target graph, 별칭 DB, policy timeline, source registry를 1차 구현 범위에 포함합니다.

## 현재 구현 기반

- Spring Boot가 중심 시스템이며 저장, 검증, 중복 제거, admin/public API를 담당합니다.
- Python pipeline은 공개 수집, Playwright fallback, LLM 분석, provider adapter를 담당합니다.
- MySQL은 커뮤니티 글, 지역/단지 mention, reaction snapshot, market fact, evidence log를 저장하는 방향으로 정리합니다.
- Vue 3 + Vite + TypeScript front는 mock 화면과 API 후보를 먼저 세우고, backend/pipeline 계약을 역으로 도출합니다.
- 기존 금융 서비스 전용 구현은 active runtime에서 제거하고, 부동산 구현에 필요한 공통 패턴만 남깁니다.

## 완제품 사용 루프

1. 사용자는 요즘 언급이 늘어난 지역과 단지를 봅니다.
2. 지역/단지 상세에서 기대와 우려, 주요 쟁점, 표본 신뢰도를 확인합니다.
3. 뉴스/컬럼, 정책/개발/교통 이벤트, 실거래/전세/매물 흐름을 같은 시간축에서 봅니다.
4. 비슷한 과거 반응 상황과 이후 시장 흐름을 비교합니다.
5. 에이전트 평가와 근거 로그로 어떤 데이터가 판단에 쓰였는지 확인합니다.

## 우선 완성할 세로 Slice

- 부동산 대시보드: 요즘 언급 많은 지역/단지, 실시간 이슈, 주요 쟁점, 데이터 상태를 보여줍니다.
- 지역/단지 상세: reaction snapshot, market fact timeline, 뉴스/컬럼 링크, 유사 과거 상황을 연결합니다.
- 지역/단지 matcher: 글 제목과 제한 snippet에서 지역/단지 별칭을 찾고 confidence를 남깁니다.
- target graph: 지역, 생활권, 정책 영향권, 단지의 roll-up/drill-down 관계를 관리합니다.
- 반응 지표: 기대/우려/중립, 쟁점 비율, 표본 신뢰도, 소스 편중 주의를 계산합니다.
- 에이전트 근거 로그: 지역/단지 평가, 근거, caveat, provider/asOf/stale 상태를 기록합니다.

## 데이터 전략

- 커뮤니티는 일반 게시판형, 부동산 게시판형, 뉴스/컬럼 링크형으로 나눕니다.
- 공개 HTTP 수집을 우선하고, Playwright는 렌더링 fallback으로만 사용합니다.
- 로그인, CAPTCHA, 프록시 회전, fingerprint 위장은 하지 않습니다.
- 원문은 제목, 일부 snippet, URL, 작성자 해시, 작성 시각, 원문 해시 정도로 제한 저장합니다.
- 실거래/전세/매물/정책 데이터는 provider, `asOf`, `stale`, 지연 여부를 반드시 분리합니다.
- 확인되지 않은 값은 `unknown`, `null`, `확인 필요`, `mock`으로 구분합니다.

## 정책 경계

- 특정 매수, 매도, 청약, 대출 행동을 권유하지 않습니다.
- 특정 단지나 지역의 가격 상승을 단정하지 않습니다.
- 커뮤니티 반응은 시장 관찰 데이터이며 서비스 결론처럼 표현하지 않습니다.
- 뉴스/컬럼은 원문 전문이 아니라 제목, 출처, 링크, 키워드 중심으로 표시합니다.
- AI는 내부 추론 전문을 노출하지 않고 사용자용 짧은 근거와 caveat만 남깁니다.

## 후순위 확장

- 지역/단지 alias 후보 review UI
- 정책/개발/교통 이벤트 provider 확장
- 유사 과거 상황 검색용 임베딩/벡터 저장소
- 질문형 분석
- 사용자 관심 지역/단지 알림
