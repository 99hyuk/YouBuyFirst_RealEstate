# 너나사 부동산 작업 지도

이 문서는 다음 작업을 고르기 위한 현재 기준입니다. 완료 상세 이력은 PR, Notion 작업 로그, `docs/archive/work-units/items/`에서 찾습니다.

## 기준

너나사 부동산은 지역과 단지에 대한 실제 사람들의 반응, 뉴스/컬럼 이슈, 실거래/전세/매물 같은 시장 사실 데이터를 함께 보여주는 관찰형 분석 서비스입니다. 완제품 기준은 `docs/product/FINAL_PRODUCT_PLAN.md`, 전환 원칙은 `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`입니다.

최종 사용 루프는 다음 순서입니다.

1. 대시보드에서 요즘 언급 많은 지역과 단지를 확인합니다.
2. 지역/단지 상세에서 기대/우려, 쟁점 비율, 표본 신뢰도를 봅니다.
3. 뉴스/컬럼, 정책/개발/교통 이벤트, 실거래/전세/매물 흐름을 같은 시간축에서 봅니다.
4. 비슷한 과거 반응 상황과 이후 시장 흐름을 비교합니다.
5. 에이전트 평가와 근거 로그로 어떤 데이터가 판단에 쓰였는지 확인합니다.

## 운영 원칙

- 업무는 부동산 완제품을 구성하는 세로 slice 기준으로 뽑습니다.
- 한 PR은 하나의 primary work area를 가집니다. 영역 기준은 `docs/layers/ops/WORK_AREAS.md`를 따릅니다.
- UI가 먼저 발견한 API 후보는 Screen Brief에 남기고, backend/pipeline은 그 계약을 실제 데이터로 채웁니다.
- 특정 매수, 매도, 청약, 대출 행동을 권유하는 표현은 쓰지 않습니다.
- 원문 재게시, 로그인/CAPTCHA/프록시/fingerprint 우회는 하지 않습니다.
- 기존 stock/market/simulation 코드는 즉시 삭제하지 않고 참고/비활성 영역으로 분류합니다.

## 지금 우선순위

- [x] root `AGENTS.md`를 부동산 프로젝트 라우터로 전환
- [x] `docs/domains/realestate/AGENTS.md`와 `README.md` 생성
- [x] `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md` 생성
- [x] `docs/product/real-estate-one-page-plan.html`을 현재 repo로 이관
- [x] `docs/product/CORE_IMPLEMENTATION_SCOPE.md` 생성
- [x] `WORK_AREAS.md`와 `DOMAIN_PACKAGE_GUIDE.md`에 realestate 작업 영역/패키지 방향 추가
- [x] `docs/domains/realestate/DATA_CONTRACT.md` 작성
- [x] `docs/layers/ui/screens/realestate-dashboard.md` 작성
- [x] `docs/layers/ui/screens/realestate-target-detail.md` 작성
- [ ] 공공데이터 API 응답 필드와 실제 갱신 지연 기준 확인
- [x] 부동산 source registry 1차 후보와 30개 확장 슬롯 정리 (`docs/domains/community/REAL_ESTATE_SOURCE_CANDIDATES.md`)
- [x] 부동산 커뮤니티 분산성 가설과 대표 source 공개 접근성 1차 검토
- [x] 부동산 source registry 후보 30개 내외 실명/URL과 1차 공개 접근성 분류 확정
- [ ] region/complex/living_area/policy_area target graph 설계
- [ ] 정책/교통/공급/대출/청약/학군/재건축 이벤트 taxonomy 정리
- [ ] `pipeline/src/youbuyfirst_pipeline/realestate/` matcher 초안 설계
- [ ] 기존 stock/market/simulation 문서와 코드를 legacy reference로 표시하고 후속 삭제 후보 목록 작성

## 제품 세로 Slice

### Slice A. 부동산 대시보드

- [ ] 요즘 언급 많은 지역/단지 ranking API 후보 설계
- [ ] 기대/우려/중립, mention count, issueMix, 표본 신뢰도 표시 기준 정리
- [ ] source skew, stale, provider/asOf 상태 badge 정리
- [ ] dashboard mock fixture와 실제 API 전환 기준 정리

### Slice B. 지역/단지 상세

- [ ] region/complex 기본 정보와 alias 표시 기준 정리
- [ ] 상위 지역/생활권/정책 영향권과 하위 단지 roll-up/drill-down 기준 정리
- [ ] reaction snapshot과 주요 쟁점 비율 응답 shape 설계
- [ ] 실거래/전세/매물/정책 이벤트 timeline 계약 정리
- [ ] 데이터 실패 시 0값처럼 보이지 않게 empty/stale/error 상태 표시

### Slice C. 수집과 matcher

- [x] 부동산 커뮤니티/뉴스/컬럼 source registry 1차 후보와 30개 확장 슬롯 정리
- [x] 부동산 source가 전국 카페/지역 카페/앱 후기/일반 게시판으로 분산된다는 가설 검토
- [x] 부동산 커뮤니티/뉴스/컬럼 source registry 후보 30개 내외 실명/URL 확정
- [ ] 네이버 카페/다음 카페 후보 중 비로그인 공개 목록 접근 가능 source만 분리
- [ ] 공개 HTTP 우선, Playwright fallback, 금지 행위 기준 재확인
- [ ] 지역/단지 alias DB와 matcher 초안 작성
- [ ] 지역 단위 언급과 단지 단위 언급의 roll-up/drill-down 규칙 정의
- [ ] matched=false, confidence, reviewState 기준 정리

### Slice D. 반응 지표와 유사 과거

- [ ] RealEstateReactionSnapshot contract 설계
- [ ] issueMix 후보: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책
- [ ] 표본 수, source 다양성, source skew, 수집 지연을 confidence에 반영
- [ ] 유사 과거 상황 검색 후보 데이터 모델 정리

### Slice E. 에이전트 근거 로그

- [ ] EvidenceLog contract 설계
- [ ] 평가 입력: reaction snapshot, market fact, timeline event, 유사 과거 상황
- [ ] 사용자용 summary/caveat 문구 기준 정리
- [ ] 내부 추론 전문 비노출 기준 정리

## 작업 영역별 백로그

### realestate

- [x] `DATA_CONTRACT.md` 생성
- [x] region/complex/alias/mention/market fact/evidence log 모델 초안 정의
- [ ] target graph와 policy event 모델 확장
- [ ] 국토교통부 실거래가/전월세 API와 건축HUB 응답 필드 샘플 저장
- [ ] API 후보 endpoint와 응답 shape 정리
- [ ] 부동산 source별 provider/asOf/stale 기준 정리

### community

- [x] 부동산 게시판/커뮤니티/뉴스/컬럼 source registry 1차 후보와 30개 확장 슬롯 정리 (`docs/domains/community/REAL_ESTATE_SOURCE_CANDIDATES.md`)
- [x] 대표 P0/P1 source 공개 접근성, robots 단서, 로그인 필요성 1차 실측
- [x] source registry 30개 내외 실명/URL에 대해 1차 공개 접근성, robots 단서, 로그인 필요 여부 분류
- [ ] adapter 활성화 전 source별 robots/약관/게시판 단위 최종 정책 리뷰
- [x] P0 후보 2곳(`PPOMPPU:house`, `DCINSIDE:immovables`) 최신글 list parser/target spike
- [ ] P0 후보 실제 HTML fixture 저장과 source별 최종 정책 리뷰
- [ ] 네이버 카페/다음 카페 후보의 공개 접근성, robots/약관, 로그인 필요 여부 기록
- [ ] 일반 게시판형과 부동산 대상형 source 분리
- [ ] 제목, 제한 snippet, URL, 작성자 hash, 작성 시각, 원문 hash 저장 정책 점검
- [ ] 추천수/조회수/댓글수는 source별 의미가 다르므로 raw 비교하지 않는 기준 유지

### indicator

- [ ] RealEstateReactionSnapshot 응답 shape 설계
- [ ] expectation/concern/neutral baseline 산식 정리
- [ ] issueMix, source skew, sample confidence 기준 정리
- [ ] 1일/1주/1개월 window 집계 후보 정리

### agent

- [x] AI 실행 위치와 LangGraph 도입 기준 정리 (`docs/domains/agent/REAL_ESTATE_AI_WORKFLOW.md`)
- [ ] `realestate-eval-v1` 입력/출력 JSON schema 확정
- [ ] Python pipeline의 stock mention prompt와 부동산 target mention prompt 분리
- [ ] forbidden copy guardrail 테스트 추가
- [ ] 지역/단지 평가와 evidence log 입력 필드 정의
- [ ] 유사 과거 상황 설명 방식 정리
- [ ] 행동 지시처럼 보이는 평가 문구 금지 기준 정리
- [ ] evaluationVersion과 skipReason 관리 기준 정리

### ui

- [ ] realestate dashboard Screen Brief 생성
- [ ] realestate target detail Screen Brief 생성
- [ ] 너나사 시리즈 공통 shell을 유지하면서 부동산 brand accent를 warm orange 계열로 전환
- [ ] front CSS에서 브랜드 blue와 의미색 blue를 분리
- [ ] accent token 변경 후 dashboard/detail screenshot QA
- [ ] 기존 dashboard 디자인 시스템을 부동산 화면에 맞춰 적용
- [ ] loading/empty/stale/error 상태 구현 기준 정리

### ops

- [ ] 새 GitHub remote 연결 전까지 `origin` 없음 상태 유지
- [ ] PR/Notion 라벨은 작업 영역 값으로 맞추되 기존 형식 유지
- [ ] 오래된 주식 중심 문서 표현을 active docs에서 제거
- [ ] archive는 과거 근거로 보존하고 시작 루틴에서 읽지 않음

## 후순위

- [ ] 유사 과거 상황 검색용 벡터 저장소
- [ ] 질문형 분석
- [ ] 사용자 관심 지역/단지 알림
- [ ] 인증/인가
- [ ] 운영 배포와 모니터링

## 현재 완료 기반

- 원본 `C:\agents\YouBuyFirst`를 복제한 새 워크스페이스
- 원본 remote 제거
- `codex/realestate-bootstrap` 브랜치
- 부동산 전용 root 라우터와 realestate 도메인 문서
- 부동산 제품 방향 문서
- 작업 영역/패키지 가이드의 realestate 기준 반영

## 작업 메모

- 작업 단위는 하나의 체크박스 또는 강하게 묶인 2-3개 체크박스로 제한합니다.
- 작업을 시작하면 `codex/<task-name>` 브랜치에서 진행합니다.
- 구현 전에 관련 테스트를 먼저 추가하거나 기존 테스트를 확장합니다.
- 문서만 바꿔도 `git diff --check`를 실행합니다.
- PR 설명에는 변경 범위, 사람이 읽기 쉬운 검증 결과, 남은 리스크를 포함합니다.
