# 너나사 부동산 작업 지도

이 문서는 다음 작업을 고르기 위한 현재 기준입니다. 완료 상세 이력은 PR, Notion 작업 로그, `docs/archive/work-units/items/`에서 찾습니다.

## 기준

너나사 부동산은 수요자 반응 기반 부동산 시장 해석 서비스입니다. 지역과 단지에 대한 실제 사람들의 반응, 뉴스/컬럼 이슈, 실거래/전세/매물 같은 시장 사실 데이터를 함께 보여주는 관찰형 분석 서비스이며, 완제품 기준은 `docs/product/FINAL_PRODUCT_PLAN.md`, 전환 원칙은 `docs/product/REAL_ESTATE_PRODUCT_DIRECTION.md`입니다.

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
- 부동산에 맞지 않는 레거시 코드는 active runtime에서 제거하고, 필요한 맥락은 git history로만 확인합니다.
- 기존 프로젝트에서 이미 부동산으로 가져오거나 변형한 기능은 active runtime에 별도로 보존하지 않습니다.

## 다음 실행 순서

1. 공공데이터 원천 확정: 공공데이터 API/CSV별 응답 필드, 갱신 주기, provider/asOf/stale 기준을 실제 샘플로 확인합니다.
2. 대량 DB 백필: 실거래가, 전월세, 공시가격 CSV, 미분양, 공급/인허가, 정책 이벤트를 raw -> staging -> market fact 흐름으로 적재합니다.
3. 지역/단지 매핑 보강: 법정동 코드, 지역 target, 단지 provider key를 연결하고 누락/중복 target을 검수합니다.
4. 지도 연결: 전국~동 단위 자체 heatmap API를 실제 region target 데이터로 연결하고, 동/단지 상세부터는 카카오맵 SDK 내장 prototype을 붙입니다.
5. 레거시 정리: backend, pipeline, front의 active runtime을 부동산 target/region/complex 기준으로 정리합니다.
6. 크롤링과 alias 고도화: 네이버/다음 카페를 포함한 공개 source 후보를 승인하고, 별칭/은어/생활권 표현을 matcher 입력으로 보강합니다.
7. SerpApi 최근 이슈 보강: 검색 결과는 관심도 점수가 아니라 뉴스/정책/개발/교통/금리 이슈 후보와 근거 링크 저장용으로 연결합니다.
8. AI 평가 로그와 유사 과거 검색: reaction snapshot, market fact, timeline event, 검색 후보, 유사 과거를 묶어 EvidenceLog와 평가 출력 schema를 확정합니다.

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
- [x] 공공데이터 매매/전월세 응답을 `real_estate_market_facts`로 정규화하고 백엔드 저장 API 연결
- [x] 지역 target registry와 국토부 공공데이터 수집대상 registry 1차 구현
- [x] 법정동코드 CSV를 지역 정본으로 import하고 시군구별 MOLIT 매매/전월세 수집대상 자동 생성
- [x] 법정동코드 CSV import 전 지역 계층/시군구 수집대상/실거래·전월세 백필 manifest를 검수하는 `realestate-regions-inspect` 명령 구현
- [x] 실거래/전월세 raw-push 실행 결과 manifest 출력 구현
- [x] 실거래/전월세 API 백필이 `pageNo`/`numOfRows` 기반 페이지 반복 수집을 하도록 보강
- [x] 완료된 실거래/전월세 import run을 백필 계획/실행에서 제외하는 재시도 옵션 구현
- [x] 실제 API 호출 전 서비스키, 남은 run, 완료 run skip, page 설정을 확인하는 공공데이터 preflight 명령 구현
- [x] 대량 백필 전 샘플 run만 선택하는 `--realestate-run-limit` 실행 가드 구현
- [x] 선택 run 수가 threshold를 넘는 raw-push는 명시 확인 전 provider 생성 전에 중단하도록 보호
- [x] 실거래/전월세 백필 계획을 JSON manifest 파일로 저장하고 preflight/raw-push에서 재사용하는 경로 구현
- [x] 실거래/전월세 대량 백필 계획을 chunk manifest로 나누고 chunk manifest를 다시 raw-push 입력으로 읽는 경로 구현
- [x] 확정 provider catalog를 JSON/SQL seed 출력으로 검수할 수 있게 하고 Windows CLI 한글 출력 깨짐 방지
- [x] 공시가격 대용량 CSV의 적재 전 manifest inspect 명령 구현
- [x] 한국부동산원/미분양/인허가용 공통 지역 통계 CSV adapter 구현
- [x] `serve` 모드에서 부동산 market fact 주기 갱신 job 옵션 추가
- [x] 대시보드 주요 지표 카드가 공공데이터 market fact 요약 API를 우선 사용하도록 연결
- [x] `/indicators` 주요 지표 화면이 `GET /api/realestate/indicators?period=month`를 우선 조회하고 가격·거래량 그룹의 provider/asOf/mock fallback 상태를 표시
- [x] 뉴스룸 화면이 content/news API 응답을 우선 사용하고 정적 데모에서는 mock fallback을 표시하도록 연결
- [x] 지역/단지 반응 ranking용 `real_estate_reaction_snapshots` 저장 API와 최신 window 조회 API 구현
- [x] 분류된 커뮤니티 관측치 JSONL을 지역/단지 반응 snapshot으로 집계하고 내부 API에 전송하는 pipeline 명령 구현
- [x] 부동산 source registry 1차 후보와 30개 확장 슬롯 정리 (`docs/domains/community/REAL_ESTATE_SOURCE_CANDIDATES.md`)
- [x] 부동산 커뮤니티 분산성 가설과 대표 source 공개 접근성 1차 검토
- [x] 부동산 source registry 후보 30개 내외 실명/URL과 1차 공개 접근성 분류 확정
- [x] 부동산 alias DB와 approved/non-ambiguous matcher export API 구현
- [x] pipeline matcher가 백엔드 alias export를 선택적으로 읽도록 연결
- [x] region/complex/living_area/policy_area 공통 target과 target graph 저장/조회 API 구현
- [x] pipeline active CLI와 기본 serve/crawl 경로에서 부동산에 맞지 않는 시장 데이터, 차트, 수급, 게시판 의존 제거
- [x] backend 기본 context에서 부동산에 맞지 않는 시장 데이터, 차트, 수급, 기술지표 API 제거
- [x] 부동산 가격 차트의 기존 금융형 막대 표현과 이전 프로젝트 상세 참고 이미지 자산 제거
- [ ] 정책/교통/공급/대출/청약/학군/재건축 이벤트 taxonomy 정리
- [x] SerpApi/search API 기반 최근 이슈 후보 discovery contract 정리
- [x] `pipeline/src/youbuyfirst_pipeline/realestate_matcher.py` matcher 초안과 파일 입력 CLI 구현
- [x] 부동산에 맞지 않는 backend/pipeline/front 코드와 fixture를 active runtime에서 제거
- [x] `/communities`, `/agents` 같은 과거 호환 route와 별도 legacy Screen Brief를 제거하고 `/realestate/reactions`를 단일 정본으로 고정
- [x] backend alias 저장과 pipeline matcher의 공백/기호 제거 정규화 규칙 통일
- [x] 커뮤니티 게시글에서 승인 alias 주변 괄호형 은어를 `candidate` alias로 추출/전송하는 pipeline 명령 구현
- [x] source별 alias coverage 리포트 CLI 구현
- [x] 로컬 secret 예시에 Kakao 지도 SDK 환경변수 이름을 추가하고 실제 key는 `.env`/`front/.env.local`에만 보관
- [x] 지도 Screen Brief에 전국~동 자체 heatmap, 동/단지 상세 카카오맵 SDK 내장 기준 반영
- [x] 실제 market fact와 reaction snapshot을 `map_layer_snapshots`로 집계하는 지도 refresh API와 daily scheduler step 구현

## 제품 세로 Slice

### Slice A. 부동산 대시보드

- [x] 요즘 언급 많은 지역/단지 ranking API 후보 설계
- [x] 기대/우려/중립, mention count, issueMix, 표본 신뢰도 표시 기준 정리
- [x] stale, provider/asOf 상태 badge와 dashboard mock fallback 기준 정리
- [ ] source skew 표시 기준 정리

### Slice B. 지역/단지 상세

- [ ] region/complex 기본 정보와 alias 표시 기준 정리
- [x] 동/단지 상세 카카오맵 SDK prototype 구현
- [x] 실제 단지 좌표/주소 DB 필드와 `nearby-complexes` API 응답으로 내장 지도 marker 1차 승격
- [ ] 법정동 코드/provider key 검증과 실제 단지 좌표 보강
- [x] 상위 지역/생활권/정책 영향권과 하위 대상 연결용 target graph API 작성
- [x] `approved contains` target graph를 반응 snapshot 상위 roll-up 산식에 반영
- [x] target graph 기반 drill-down/관련 target snapshot 응답 API 구현
- [ ] `nearby`, `same_living_area`, `policy_impacts` 관련 영향권 weighting 산식 정리
- [x] reaction snapshot과 주요 쟁점 비율 응답 shape 설계
- [x] target 상세용 market fact timeline 조회 API 구현
- [x] 정책/뉴스/공급 이벤트 timeline 저장/조회 계약과 API 구현
- [x] market fact를 `timeline_events`의 `sourceRefType=market_fact` 구조로 materialize
- [x] reaction snapshot을 `timeline_events`의 `sourceRefType=reaction_snapshot` 구조로 materialize
- [x] content/news raw source를 `timeline_events`의 `sourceRefType=content` 구조로 병합
- [x] 지역/단지 상세 근거 링크 후보가 target content API 응답을 우선 사용하도록 연결
- [ ] 데이터 실패 시 0값처럼 보이지 않게 empty/stale/error 상태 표시

### Slice C. 수집과 matcher

- [x] 부동산 커뮤니티/뉴스/컬럼 source registry 1차 후보와 30개 확장 슬롯 정리
- [x] 부동산 source가 전국 카페/지역 카페/앱 후기/일반 게시판으로 분산된다는 가설 검토
- [x] 부동산 커뮤니티/뉴스/컬럼 source registry 후보 30개 내외 실명/URL 확정
- [ ] 네이버 카페/다음 카페 후보 중 비로그인 공개 목록 접근 가능 source만 분리
- [ ] 공개 HTTP 우선, Playwright fallback, 금지 행위 기준 재확인
- [x] 지역/단지 alias DB JSONL 입력과 matcher 초안 작성
- [x] 지역/단지 alias DB 백엔드 저장/조회 API 작성
- [x] `--realestate-use-backend-aliases`로 백엔드 alias registry를 matcher 입력으로 사용
- [x] 공백/기호가 섞인 커뮤니티식 별칭을 같은 alias로 매칭하고 실제 원문 매칭 문자열을 근거로 보존
- [x] 승인 alias 옆 괄호형 은어를 `community_slang` 후보 alias로 만들고, 운영자 승인 전에는 ranking/snapshot에 쓰지 않도록 분리
- [x] source별 `matchRate`, `topTargets`, `unmatchedExamples`, `candidateAliases`를 확인하는 alias coverage 리포트 구현
- [x] source 후보 JSONL을 실행 가능한 crawl target manifest와 skip 사유로 분리하는 `realestate-crawl-target-manifest` 명령 구현
- [x] `contains` edge 기반 지역 단위 언급 roll-up 규칙 구현
- [ ] 단지 단위 drill-down과 정책/생활권 edge 적용 규칙 정의
- [x] matched=false, confidence, reviewState 1차 기준 정리

### Slice D. 반응 지표와 유사 과거

- [x] RealEstateReactionSnapshot contract 설계
- [x] issueMix 후보: 교통, 학군, 전세, 재건축, 청약, 대출, 공급, 정책
- [x] 매칭된 지역/단지 게시글을 `reactionDirection`과 `issues`가 있는 observation payload로 바꾸는 룰 기반 pipeline 구현
- [x] 분류된 관측치 기준 expectation/concern/neutral, issueMix, source skew, sample confidence 1차 집계 구현
- [x] 제한 게시글 JSONL과 alias JSONL에서 reaction snapshot 생성/전송까지 가는 end-to-end pipeline 명령 구현
- [x] `serve` 모드에서 reaction snapshot refresh job 옵션 추가
- [x] 표본 수, source 다양성, source skew, 수집 지연을 confidence에 반영
- [x] pipeline active CLI에서 부동산에 맞지 않는 시장 데이터, 차트, 수급 명령을 제거하고 기본 crawl/serve 경로를 부동산 seed target 중심으로 전환
- [x] 유사 과거 상황 검색 후보 데이터 모델 정리
- [x] 벡터DB 도입 전 batch similarity 기준과 이후 market fact 비교 shape 정리
- [x] `realestate-similar-windows` 명령으로 reaction snapshot 기반 유사 과거 후보와 이후 market fact 흐름 요약 출력

### Slice E. 에이전트 근거 로그

- [x] EvidenceLog contract 설계
- [x] EvidenceLog 저장/조회 DB/API 구현 (`POST /internal/realestate/evidence-logs`, `GET /api/realestate/targets/{targetId}/evidence-logs`)
- [x] 평가 입력: reaction snapshot, market fact, 유사 과거 상황
- [x] 평가 입력: timeline event
- [x] 평가 입력: SerpApi/search API 기반 최근 이슈 후보
- [x] `realestate-evidence-logs(-push)`로 reaction snapshot, market fact, timeline event, 최근 이슈 후보, 유사 과거 후보를 EvidenceLog payload로 조립/전송
- [x] GMS OpenAI-compatible LLM provider로 EvidenceLog summary/subtitle를 선택 보강하고 forbidden copy guardrail 적용
- [ ] 사용자용 summary/caveat 문구 기준 정리
- [x] Langfuse trace와 DB evidence log 정본의 경계 정리
- [ ] 내부 추론 전문 비노출 기준 정리

## 작업 영역별 백로그

### realestate

- [x] `DATA_CONTRACT.md` 생성
- [x] region/complex/alias/mention/market fact/evidence log 모델 초안 정의
- [x] target graph 모델/API 확장
- [ ] policy event 모델 확장
- [ ] 국토교통부 실거래가/전월세 API와 건축HUB 응답 필드 샘플 저장
- [ ] API 후보 endpoint와 응답 shape 정리
- [x] 서울 종로구 seed 기준 `legalDongCode` -> region target 자동 매핑 연결
- [x] `real_estate_aliases` 저장소와 public/internal alias API 구현
- [x] `real_estate_target_edges` 저장소와 public/internal graph API 구현
- [ ] 부동산 source별 provider/asOf/stale 기준 정리

### community

- [x] 부동산 게시판/커뮤니티/뉴스/컬럼 source registry 1차 후보와 30개 확장 슬롯 정리 (`docs/domains/community/REAL_ESTATE_SOURCE_CANDIDATES.md`)
- [x] 대표 P0/P1 source 공개 접근성, robots 단서, 로그인 필요성 1차 실측
- [x] source registry 30개 내외 실명/URL에 대해 1차 공개 접근성, robots 단서, 로그인 필요 여부 분류
- [x] P0 후보 board-level robots 단서와 live parser smoke 확인
- [ ] adapter 활성화 전 source별 약관/게시판 단위 최종 정책 승인
- [x] P0 후보 2곳(`PPOMPPU:house`, `DCINSIDE:immovables`) 최신글 list parser/target spike
- [x] P0 후보 sanitized HTML fixture 저장과 parser 회귀 테스트 보강
- [ ] 다음 카페 공개 `bbs_list` 후보 1곳 source-specific 확인
- [ ] 네이버 카페/다음 카페 후보의 공개 접근성, robots/약관, 로그인 필요 여부 기록
- [ ] 일반 게시판형과 부동산 대상형 source 분리
- [ ] 제목, 제한 snippet, URL, 작성자 hash, 작성 시각, 원문 hash 저장 정책 점검
- [ ] 추천수/조회수/댓글수는 source별 의미가 다르므로 raw 비교하지 않는 기준 유지

### indicator

- [x] RealEstateReactionSnapshot 응답 shape 설계
- [x] expectation/concern/neutral baseline 1차 산식 구현
- [x] issueMix, source skew, sample confidence 1차 pipeline 집계 구현
- [x] `realestate-reaction-snapshots-from-posts(-push)` end-to-end 명령 구현
- [x] `serve --enable-realestate-reaction-snapshots-refresh` 주기 refresh job 구현
- [x] `serve --enable-realestate-daily-refresh`로 market fact, reaction snapshot, 최근 이슈 refresh를 하루 단위 step으로 묶는 scheduler job 구현
- [ ] 1일/1주/1개월 window 집계 후보 정리

### agent

- [x] AI 실행 위치와 LangGraph 도입 기준 정리 (`docs/domains/agent/REAL_ESTATE_AI_WORKFLOW.md`)
- [ ] `realestate-eval-v1` 입력/출력 JSON schema 확정
- [x] Python pipeline의 부동산 반응 분류 baseline command 구현 (`realestate-reaction-observations`)
- [ ] 부동산 target mention prompt와 OpenAI provider 분리
- [x] forbidden copy guardrail 테스트 추가
- [x] 지역/단지 평가와 evidence log 입력 필드 정의
- [x] 룰 기반 EvidenceLog 생성/전송 command 구현 (`realestate-evidence-logs`, `realestate-evidence-logs-push`)
- [x] 유사 과거 상황 설명 방식 정리
- [x] GMS `gemini-embedding-2` 임베딩 client와 `realestate-embeddings` command 구현
- [x] GMS `gpt-5-mini` EvidenceLog summary 보강 client와 `--evidence-use-gms-llm` 옵션 구현
- [x] 최근 이슈 후보 검색 provider/query/keyword 저장 기준 정리
- [x] 최신 DB snapshot 기반 EvidenceLog 일일 자동 생성 job 구현
- [x] 임베딩 결과를 Qdrant에 적재하고 유사 window 검색 결과를 EvidenceLog `similar_window` 입력 shape로 출력
- [x] Qdrant 검색 결과에 이후 market fact 흐름을 자동 join하고 EvidenceLog `similar_window` 입력 shape에 반영
- [x] Qdrant 검색을 `realestate-similar-windows --similar-engine qdrant` 내부 검색 엔진 선택지로 통합
- [ ] 실제 Qdrant runtime smoke와 운영 collection health check 정리
- [ ] 행동 지시처럼 보이는 평가 문구 금지 기준 정리
- [x] evaluationVersion과 skipReason 관리 기준 정리

### ui

- [x] realestate dashboard Screen Brief 생성
- [x] realestate target detail Screen Brief 생성
- [x] realestate map Screen Brief를 API 우선 + fixture fallback 기준으로 분리
- [x] Kakao map SDK 내장 컴포넌트와 key missing fallback 상태 구현
- [ ] 너나사 시리즈 공통 shell을 유지하면서 부동산 brand accent를 warm orange 계열로 전환
- [ ] front CSS에서 브랜드 blue와 의미색 blue를 분리
- [ ] accent token 변경 후 dashboard/detail screenshot QA
- [ ] 기존 dashboard 디자인 시스템을 부동산 화면에 맞춰 적용
- [ ] loading/empty/stale/error 상태 구현 기준 정리

### ops

- [ ] 새 GitHub remote 연결 전까지 `origin` 없음 상태 유지
- [ ] PR/Notion 라벨은 작업 영역 값으로 맞추되 기존 형식 유지
- [x] 오래된 레거시 중심 문서 표현을 active docs에서 부동산 전용 표현으로 정리
- [x] 이전 금융 도메인 전용 화면/API/seed/test는 active runtime 보존 대상에서 제외하고 부동산 target/region/complex 기준으로 정리
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
