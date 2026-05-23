# 기술 리스크 레지스터

마지막 갱신: 2026-05-22

이 문서는 너나사 최종 기획을 구현하면서 생길 수 있는 기술, 제품, 운영 이슈를 미리 모아두는 목록입니다. 실제 장애가 발생한 뒤의 상세 복구 기록은 `docs/governance/TROUBLESHOOTING_GUIDE.md`와 PR/Notion 작업 로그에 남기고, 이 문서에는 "무엇을 조심해야 하는지"와 "어떻게 방어할지"를 계속 추가합니다.

새 이슈가 보이면 아래 형식으로 추가합니다.

```text
### RISK-000. 짧은 제목

- 관련 영역: community, indicator, market, simulation, agent, layers/ui, layers/ops
- 상태: 후보/발생/완화/닫힘
- 증상: 사용자가 보거나 운영자가 발견할 현상
- 영향: 제품 신뢰, 데이터 정합성, 법적 리스크, 비용, 성능 중 무엇이 흔들리는지
- 방어: 설계, 제약 조건, 테스트, 모니터링, 문구 처리
- 확인: 재현 명령, 검증 쿼리, 화면, 로그, PR
```

## 핵심 원칙

- 실제 투자 자문, 실거래 지시, 수익 보장처럼 보이면 제품 리스크입니다.
- 커뮤니티 반응 지표는 원문 재게시가 아니라 제한 메타데이터와 집계로 보여줍니다.
- 화면은 `커뮤니티 반응`을 먼저 설명하고, 관심종목은 개인화 필터로 둡니다.
- 모의투자는 실제 결제가 아니라 paper trading입니다. 그래도 주문, 체결, 정산, 원장, 포지션은 트랜잭션 정합성을 지켜야 합니다.
- 에이전트는 통계 윈도우를 보고 판단합니다. 같은 윈도우, 종목, 전략 버전으로 중복 판단/중복 주문이 생기지 않아야 합니다.
- 대시보드와 리더보드는 가능한 한 published snapshot 또는 원장 기반 재계산으로 설명 가능해야 합니다.

## 발생 이슈 로그

아직 실제 발생 이슈는 없습니다. 발생하면 이 섹션에 시간순으로 추가하고, 아래 후보 리스크와 연결합니다.

## 후보 리스크

### RISK-001. 에이전트 판단 중복

- 관련 영역: agent, simulation
- 상태: 후보
- 증상: 같은 30분 집계 윈도우에서 같은 에이전트가 같은 종목 주문을 두 번 생성합니다.
- 영향: 전략 수익률, 리더보드, 포지션이 부풀어 제품 신뢰가 깨집니다.
- 방어: `agentId + windowStart + symbol + strategyVersion` 판단 key를 unique로 둡니다. scheduler 재시도는 idempotent하게 처리합니다.
- 확인: 같은 window를 두 번 실행하는 테스트에서 `AgentDecision`과 `SimulatedOrder`가 하나만 생기는지 검증합니다.

### RISK-002. 주문, 체결, 원장 불일치

- 관련 영역: simulation
- 상태: 후보
- 증상: 주문은 체결됐는데 현금, 포지션, 거래 원장 중 일부만 갱신됩니다.
- 영향: 포트폴리오와 리더보드가 서로 다른 숫자를 보여줍니다.
- 방어: 주문 예약, 체결, 정산, `LedgerEntry`, `Position` 갱신을 트랜잭션 경계 안에 둡니다. 체결은 `orderId + executionType` 같은 idempotency key로 중복을 막습니다.
- 확인: 체결 중간 예외를 주입한 테스트에서 모든 변경이 롤백되는지 확인합니다.

### RISK-003. 조회 화면의 부분 최신 상태

- 관련 영역: simulation, layers/ui
- 상태: 후보
- 증상: 사용자가 포트폴리오를 볼 때 현금은 최신인데 포지션이나 수익률은 이전 snapshot으로 보입니다.
- 영향: 사용자가 손익과 잔고를 신뢰하지 못합니다.
- 방어: 조회용 `PerformanceSnapshot`에 `asOf`, `sourceSnapshotId`, `settlementStatus`를 둡니다. 실시간 계산 화면은 같은 기준 시점의 데이터만 묶어 응답합니다.
- 확인: 체결 직후 포트폴리오 API가 같은 `asOf` 기준으로 현금, 포지션, 수익률을 반환하는지 테스트합니다.

### RISK-004. 게시글 재수집으로 언급량 부풀림

- 관련 영역: community, indicator
- 상태: 후보
- 증상: 같은 커뮤니티 글이 여러 번 저장되어 언급량과 반응 지표가 과대 계산됩니다.
- 영향: 라이징 스타, 열기 지수, 에이전트 판단이 잘못됩니다.
- 방어: `source + sourcePostId` 또는 `source + normalizedUrl/contentHash` unique를 둡니다. 삭제/수정 글은 별도 상태로 처리합니다.
- 확인: 같은 fixture를 반복 수집했을 때 저장 row와 집계가 증가하지 않는지 검증합니다.

### RISK-005. LLM 분석 재시도 중복과 버전 혼합

- 관련 영역: indicator
- 상태: 후보
- 증상: 같은 글에 대해 다른 prompt/model version 분석이 섞이거나, 재시도 결과가 중복 반영됩니다.
- 영향: 반응 방향 분포와 confidence가 재현되지 않습니다.
- 방어: `postId + modelVersion + promptVersion + analysisType` key를 둡니다. 새 모델 실험은 기존 published snapshot과 분리합니다.
- 확인: 같은 입력을 같은 버전으로 재분석해도 published 집계가 중복 증가하지 않는지 확인합니다.

### RISK-006. 집계 윈도우 부분 publish

- 관련 영역: indicator, layers/ui, agent
- 상태: 후보
- 증상: 30분 집계가 계산 중인데 화면이나 에이전트가 중간 결과를 읽습니다.
- 영향: 랭킹이 흔들리고 에이전트가 불완전한 데이터로 주문합니다.
- 방어: aggregate 상태를 `calculating`, `published`, `failed`로 나누고 화면/에이전트는 `published`만 읽습니다.
- 확인: 집계 중에는 dashboard API와 agent job이 이전 published snapshot을 읽는지 테스트합니다.

### RISK-007. 작은 표본과 소스 편중

- 관련 영역: indicator, layers/ui, agent
- 상태: 후보
- 증상: 글 2-3개짜리 급등 반응이 큰 신호처럼 표시됩니다.
- 영향: 사용자와 에이전트가 노이즈를 의미 있는 흐름으로 오해합니다.
- 방어: 표본 수, 커뮤니티 편중, 작성자 다양성, 시세 지연을 `SignalReliability` 배지로 노출합니다. 낮은 신뢰도는 에이전트 주문 후보에서 제외하거나 작은 가중치로 반영합니다.
- 확인: 낮은 표본 fixture에서 경고 배지가 표시되고 agent decision이 `WATCH` 또는 `SKIP`으로 남는지 확인합니다.

### RISK-008. 시세 snapshot과 체결 가격 설명 불가

- 관련 영역: market, simulation
- 상태: 후보
- 증상: 에이전트가 어떤 가격으로 체결됐는지 나중에 설명할 수 없습니다.
- 영향: 손익 계산과 전략 검증이 재현되지 않습니다.
- 방어: `SimulatedExecution`에 `quoteSnapshotId`, provider, delay status, currency, market session을 저장합니다.
- 확인: 체결 로그에서 가격, 시각, snapshot id로 원본 quote를 역추적합니다.

### RISK-009. 시세 재배포와 실시간 표현 리스크

- 관련 영역: market, layers/ui, layers/ops
- 상태: 후보
- 증상: provider 기준 지연 시세나 mock data를 `실시간`처럼 보여줍니다.
- 영향: 데이터 제공자 약관, 사용자 신뢰, 투자 자문 오해가 생깁니다.
- 방어: MVP 단계에서는 `yfinance` + FinanceDataReader 조합을 기본 provider 전략으로 둡니다. `yfinance`는 국내/미국 시세와 거래량의 1차 adapter, FinanceDataReader는 국내 종목 메타데이터, 일봉/스냅샷 보강, 국내 수급 후보 adapter로 사용합니다. `pykrx`는 기본 조합에서 빼고, FinanceDataReader로 부족한 KRX 수급 검증이 필요할 때만 보조 후보로 둡니다. 공개 화면에는 제한된 quote snapshot만 직접 표시하고, 직접 표시하는 시세에는 `지연 데이터`, provider, `asOf`, `stale`, `참고용` 상태를 항상 붙입니다. 원시 분봉, 호가, 대량 OHLC, 다운로드/API 형태의 재배포는 별도 계약 전까지 만들지 않습니다. 서비스 트래픽이나 수익화 가능성이 커지면 국내는 KRX/KOSCOM, 미국은 public display 권한이 있는 데이터 벤더 계약을 재검토합니다.
- 확인: 모든 market UI에 `asOf`, 지연 시간, 출처, stale 상태가 있는지 화면 QA로 확인합니다. provider 구현 전에는 `YFinanceQuoteProvider`, `FinanceDataReaderKoreaProvider`처럼 adapter 경계를 분리하고, 공개 표출 가능 범위와 교체 경로를 문서화합니다.

### RISK-010. 커뮤니티 원문/작성자 노출 과다

- 관련 영역: community, layers/ui, layers/ops
- 상태: 후보
- 증상: 원문 전체, 닉네임 랭킹, 작성자 추적처럼 보이는 화면이 생깁니다.
- 영향: 개인정보, 저작권, 플랫폼 약관 리스크가 커집니다.
- 방어: 저장 원문은 제목, 본문 일부, URL, 작성자 해시, 작성 시각, 원문 해시로 제한합니다. 공개 화면은 집계와 원문 링크 중심으로 둡니다.
- 확인: UI와 API 응답에 원문 전문, 닉네임, 작성자별 랭킹이 없는지 확인합니다.

### RISK-011. 크롤링 소스 정책 변경과 차단

- 관련 영역: community, layers/ops
- 상태: 후보
- 증상: 특정 소스가 robots, 약관, DOM, rate limit을 바꿔 수집 실패나 차단이 발생합니다.
- 영향: 데이터 공백, IP 차단, 공개 배포 리스크가 생깁니다.
- 방어: source activation state를 `disabled` 기본값으로 두고, source policy gate와 backoff를 적용합니다. CAPTCHA 우회, 로그인 세션 크롤링, 프록시 회전은 하지 않습니다.
- 확인: source별 run status, skip reason, backoff reason이 admin API에서 보이는지 확인합니다.

### RISK-012. 디시 계열 board 이름/주소 혼동

- 관련 영역: community, indicator
- 상태: 후보
- 증상: 미국 주식 갤러리, 주식갤러리, 국내주식 계열을 코드에 잘못 매핑합니다.
- 영향: marketScope가 섞여 미국 주식/국내 주식 지표와 전략이 오염됩니다.
- 방어: `source`, `boardId`, `displayName`, `marketScope`, `crawlPolicy`를 source/board registry에 둡니다. 이름 변경은 registry migration으로 처리합니다.
- 확인: 각 board fixture가 올바른 marketScope와 종목 universe로 분류되는지 테스트합니다.

### RISK-013. 종목 인식 alias 충돌

- 관련 영역: indicator
- 상태: 후보
- 증상: `Apple`, `현대`, `삼성`, `LG`처럼 일반 단어나 그룹명이 특정 종목으로 잘못 매핑됩니다.
- 영향: 잘못된 종목 랭킹과 에이전트 판단으로 이어집니다.
- 방어: alias confidence, market context, ticker hint, source board context를 함께 사용합니다. 애매한 mention은 `needsReview` 또는 낮은 confidence로 둡니다.
- 확인: 충돌 alias fixture와 회귀 테스트를 유지합니다.

### RISK-014. 뉴스/공시와 커뮤니티 반응 연결 오류

- 관련 영역: indicator, layers/ui
- 상태: 후보
- 증상: 특정 뉴스가 실제 관련 없는 종목 반응의 원인 후보로 표시됩니다.
- 영향: AI 3줄 요약이 허위 인과처럼 보입니다.
- 방어: 원인 표현은 `확인된 원인`이 아니라 `함께 관찰된 후보`로 씁니다. 시간 근접성, 종목 태그, 키워드 overlap, source reliability를 함께 기록합니다.
- 확인: 화면 문구가 단정 대신 후보/관찰 표현인지 리뷰합니다.

### RISK-015. AI 요약의 투자 자문 오해

- 관련 영역: agent, layers/ui, layers/ops
- 상태: 후보
- 증상: AI 3줄 요약이 매수/매도 추천, 수익 보장, 따라 사기처럼 읽힙니다.
- 영향: 법적/제품 리스크가 큽니다.
- 방어: 요약은 `원인 후보`, `커뮤니티가 기대/우려하는 포인트`, `주의점`으로 제한합니다. 매수/매도는 `매수 언급`, `매도 언급`, `순매수`, `호가 잔량`처럼 출처가 있는 관찰 데이터로만 표시하고, CTA는 `관찰`, `확인`, `타임라인 보기`로 둡니다.
- 확인: fixture 문구와 화면 텍스트에서 `추천`, `사라`, `팔아라`, `수익 보장`, 단정적 판단을 검색합니다. `매수/매도` 단어는 데이터 라벨인지 서비스 판단인지 함께 확인합니다.

### RISK-016. 리더보드 캐시와 원장 불일치

- 관련 영역: simulation, agent, layers/ui
- 상태: 후보
- 증상: 에이전트 리더보드 수익률이 원장 재계산 결과와 다릅니다.
- 영향: 커뮤니티별 성과 비교가 신뢰를 잃습니다.
- 방어: 리더보드는 cache를 쓰더라도 `LedgerEntry`, `SimulatedExecution`, `QuoteSnapshot`으로 재계산 가능해야 합니다. snapshot에는 생성 기준과 input range를 남깁니다.
- 확인: reconciliation job이 캐시 수익률과 원장 기반 수익률 차이를 감지합니다.

### RISK-017. 알림 중복과 threshold flapping

- 관련 영역: indicator, layers/ui, layers/ops
- 상태: 후보
- 증상: 같은 종목 급등 알림이 재시도나 경계값 진동으로 여러 번 발송됩니다.
- 영향: 사용자 피로도와 신뢰 저하가 생깁니다.
- 방어: `userId + eventType + symbol + windowStart` notification key, cooldown, hysteresis를 둡니다.
- 확인: 같은 event를 여러 번 publish해도 알림이 한 번만 생성되는지 테스트합니다.

### RISK-018. 프론트 mock/real 상태 혼동

- 관련 영역: layers/ui
- 상태: 후보
- 증상: 사용자가 mock, stale, 지연 데이터를 실제 실시간 데이터로 오해합니다.
- 영향: 제품 신뢰와 투자 자문 오해가 생깁니다.
- 방어: 모든 mock/fixture 영역에 source state와 asOf를 표시합니다. 실제 API 전환 시에도 disabled/empty/error 상태를 별도로 둡니다.
- 확인: `/dashboard`, `/stocks/:symbol`, `/portfolio`, `/agents`에서 mock/stale/asOf 표시를 화면 QA합니다.

### RISK-019. 빈 데이터와 source disabled 상태의 화면 붕괴

- 관련 영역: layers/ui, community, indicator
- 상태: 후보
- 증상: 공개 배포에서 특정 소스가 disabled라 데이터가 없을 때 화면이 빈 카드나 오류로 보입니다.
- 영향: 첫인상과 데모 안정성이 떨어집니다.
- 방어: empty state, disabled source 설명, fixture fallback, 공개 demo mode를 분리합니다.
- 확인: 모든 source disabled fixture로 dashboard가 정상 렌더링되는지 테스트합니다.

### RISK-020. worktree/브랜치 간 최신 화면 유실

- 관련 영역: layers/ops, layers/ui
- 상태: 후보
- 증상: front 작업이 별도 worktree에 남고 main 또는 현재 브랜치에 반영되지 않습니다.
- 영향: 사용자는 최신 화면을 봤다고 생각하지만 PR/문서에는 반영되지 않을 수 있습니다.
- 방어: ops는 열린 브랜치를 active, review, blocked, stale, close-candidate로 분류합니다. dirty worktree는 자동 병합/삭제하지 않고 보고합니다. PR이 merge/close/대체되면 살릴 조각만 새 작은 PR로 옮기고 기존 브랜치와 worktree를 정리합니다.
- 확인: `git branch -vv`, `git worktree list`, `gh pr list --state open`, dev server cwd/파일 경로를 요약 확인합니다.

### RISK-021. PR/문서/Notion 상태 불일치

- 관련 영역: layers/ops
- 상태: 후보
- 증상: PR은 머지됐는데 `docs/current/HANDOFF.md`, `docs/current/TASKS.md`, Notion 작업 로그가 다른 상태를 가리킵니다.
- 영향: 새 채팅과 병렬 에이전트가 오래된 전제를 따릅니다.
- 방어: PR 머지 후 ops가 주요 handoff와 task list를 확인합니다. 큰 구조 변경은 문서 PR로 먼저 남깁니다.
- 확인: PR 종료 시 `docs/current/HANDOFF.md`, `docs/current/TASKS.md`, 관련 도메인/layer `AGENTS.md`/`README.md`의 다음 작업이 맞는지 확인합니다.

### RISK-022. 토큰/도구 출력 과다로 채팅 중단

- 관련 영역: layers/ops, layers/ui
- 상태: 후보
- 증상: 긴 문서, DOM, console, Notion, 세션 로그 출력으로 채팅이 `앗, 오류가 발생했습니다`로 끊깁니다.
- 영향: 작업 복구와 최신 상태 반영이 어려워집니다.
- 방어: `rg`, 섹션 읽기, 요약 출력, Browser/gstack 검증 일괄 실행을 유지합니다. 로그는 전문이 아니라 수치 집계로 봅니다.
- 확인: 큰 작업 후 input token 최대/평균을 비교하고 `docs/layers/ops/DOCUMENTATION_GUIDE.md`의 예산을 지킵니다.

### RISK-023. 외부 링크와 favicon 장애

- 관련 영역: layers/ui
- 상태: 후보
- 증상: 뉴스/영상/블로그 외부 링크가 깨지거나 favicon 요청 실패로 UI가 지저분해집니다.
- 영향: 화면 완성도와 신뢰감이 떨어집니다.
- 방어: favicon fallback, broken image hide, 링크 source/type 표시, `rel="noreferrer noopener"`를 유지합니다.
- 확인: 네트워크 실패 fixture와 화면 QA에서 레이아웃이 깨지지 않는지 확인합니다.

### RISK-024. 시간대와 시장 세션 처리 오류

- 관련 영역: market, indicator, agent, simulation
- 상태: 후보
- 증상: KST, 미국 장, 프리마켓, 휴장일 기준이 섞여 잘못된 window와 수익률을 계산합니다.
- 영향: 커뮤니티 신호와 forward return 검증이 틀어집니다.
- 방어: 모든 snapshot과 aggregate에 timezone, market, session을 저장합니다. KRX/US market calendar를 분리합니다.
- 확인: 장전, 장중, 장후, 휴장일 fixture로 window와 체결 가능 여부를 테스트합니다.

### RISK-025. 종목 이벤트 타임라인 순서와 중복

- 관련 영역: indicator, layers/ui
- 상태: 후보
- 증상: 뉴스, 공시, 가격, 커뮤니티 반응 이벤트가 시간순으로 섞이지 않거나 같은 이벤트가 반복 표시됩니다.
- 영향: 사용자가 원인 흐름을 잘못 이해합니다.
- 방어: `StockEvent`에 event type, occurredAt, source id, dedupe key를 둡니다. 화면은 같은 이벤트 묶음을 하나로 압축합니다.
- 확인: 같은 기사/게시글/가격 이벤트 fixture에서 타임라인 중복이 없는지 확인합니다.

### RISK-026. OCR 자산 연동의 개인정보 노출

- 관련 영역: layers/ui, simulation, layers/ops
- 상태: 후보
- 증상: 증권사 잔고 캡처에 계좌번호, 이름, 보유금액 등 민감 정보가 포함됩니다.
- 영향: 개인정보와 보안 리스크가 큽니다.
- 방어: OCR 자산 연동은 후순위로 두고, 도입 시 로컬 redaction, 업로드 최소화, presigned URL 만료, 원본 즉시 삭제 정책을 먼저 설계합니다.
- 확인: 샘플 이미지 처리 후 민감 영역이 저장/로그에 남지 않는지 확인합니다.

### RISK-027. 성과 비교가 "맞히는 커뮤니티"처럼 보임

- 관련 영역: agent, layers/ui, layers/ops
- 상태: 후보
- 증상: 커뮤니티별 수익률 비교가 특정 커뮤니티의 우월성이나 매매 추천처럼 보입니다.
- 영향: 제품 메시지와 법적 리스크가 커집니다.
- 방어: 화면 문구는 `최근 반응 이후 흐름`, `모의 실험`, `표본 수`, `기간 제한`을 함께 표시합니다. `늘 맞는다`, `따라 하기` 표현을 금지합니다.
- 확인: 리더보드와 에이전트 설명 문구에서 단정 표현을 검색합니다.

### RISK-028. 전략 버전 변경 후 성과 비교 오염

- 관련 영역: agent, simulation
- 상태: 후보
- 증상: 에이전트 전략 로직을 바꾼 뒤 과거 성과와 새 성과가 같은 계정에 섞입니다.
- 영향: 전략 평가가 재현되지 않습니다.
- 방어: 모든 `AgentDecision`, `SimulatedOrder`, `PerformanceSnapshot`에 `strategyVersion`을 남깁니다. 새 전략은 별도 계정 또는 별도 성과 series로 봅니다.
- 확인: 전략 버전 변경 후 리더보드가 버전별로 분리되는지 테스트합니다.

### RISK-029. 데이터 품질 관측 부족

- 관련 영역: community, indicator, layers/ops
- 상태: 후보
- 증상: 수집량, 분석 실패율, stale 비율, source별 편중을 모른 채 화면만 봅니다.
- 영향: 지표가 왜 이상한지 설명하기 어렵습니다.
- 방어: source별 수집 수, dedupe 수, 분석 실패율, confidence 분포, published snapshot 수를 admin/로그로 남깁니다.
- 확인: 일별 data quality report 또는 admin endpoint에서 핵심 수치가 보이는지 확인합니다.

### RISK-030. API 계약 없이 front mock이 앞서감

- 관련 영역: layers/ui, indicator, market, simulation, agent
- 상태: 후보
- 증상: front mock 화면이 실제 backend/API가 제공하기 어려운 필드와 상태를 전제합니다.
- 영향: API 연동 때 대규모 재작업이 생깁니다.
- 방어: front-first discovery는 유지하되, mock field마다 소유 도메인/layer와 계약 후보를 기록합니다. 실제 API 전환 전에는 fixture와 contract test를 맞춥니다.
- 확인: dashboard fixture 필드를 `indicator/market/simulation/agent` contract 후보로 역추적합니다.

### RISK-031. 조회수/추천수 기반 인기글 지표 왜곡

- 관련 영역: community, indicator, layers/ui
- 상태: 후보
- 증상: 디시 개념글 추천수, 뽐뿌 추천수, FM 조회수, 블로그 노출 순위처럼 서로 다른 지표를 같은 기준으로 비교합니다.
- 영향: 특정 소스의 구조적 특성이 종목 반응이나 열기 지수처럼 오해됩니다.
- 방어: raw 조회수/추천수를 직접 합산하지 않고 source 내부 percentile, 시간 대비 증가율, 댓글/추천/조회 가중치, 종목 관련도, 중복/낚시 패널티를 분리합니다. 화면에는 `해당 커뮤니티 기준 상위 N%`처럼 표시합니다.
- 확인: 서로 다른 소스 fixture에서 같은 raw 수치가 같은 popularity score로 처리되지 않는지 테스트합니다.

### RISK-032. 부동산 버티컬 확장으로 주식 MVP 범위가 흐려짐

- 관련 영역: layers/ops, layers/ui, indicator
- 상태: 후보
- 증상: 부동산, 음식, 여행 같은 별도 주제를 주식 대시보드 안에 함께 넣으려 하면서 화면과 데이터 모델이 재테크 종합 포털처럼 넓어집니다.
- 영향: 주식/ETF 커뮤니티 반응 분석, 시세 연결, 모의투자 원장이라는 핵심 포트폴리오 메시지가 약해집니다.
- 방어: 부동산은 후순위 별도 버티컬로만 기록하고, 주식 MVP 안에는 넣지 않습니다. 상단 스위치나 공통 디자인 시스템은 검토할 수 있지만, 지역/단지/실거래가/정책 도메인은 별도 모델로 분리합니다.
- 확인: `docs/product/FINAL_PRODUCT_PLAN.md`와 front navigation에서 부동산이 주식 MVP의 필수 탭이나 데이터 계약으로 들어가지 않았는지 확인합니다.

### RISK-033. 서비스 한줄평이 투자 자문이나 조롱으로 읽힘

- 관련 영역: layers/ui, agent, layers/ops
- 상태: 후보
- 증상: `"이거 매수하는 건 돈에 대한 모독임"`처럼 강한 문구가 커뮤니티 원문이 아니라 서비스의 직접 판단처럼 노출됩니다.
- 영향: 직접 `사라/팔아라`라고 말하지 않아도 특정 종목의 매수 행위를 평가하거나 조롱하는 표현으로 읽혀 투자 자문, 평판 훼손, 시장 조작 오해, 서비스 신뢰 저하 리스크가 생깁니다.
- 방어: 금융 사이트의 매수/매도 흐름처럼 관찰 데이터는 표시할 수 있습니다. 짠맛/팩트폭격 톤도 사용할 수 있지만, 농담의 대상은 사용자 행동이 아니라 커뮤니티 반응과 지표의 차이로 둡니다. 예를 들어 `커뮤니티 온도는 90도, 7일 수익률은 냉장고`처럼 기간/지표가 있는 표현은 가능하고, `이걸 매수하는 건 바보다`처럼 행동 평가로 읽히는 표현은 피합니다. 과격한 표현은 원문 인용 또는 커뮤니티 톤으로만 다루고, 출처/표본 수/서비스 판단 아님 표시를 함께 둡니다.
- 확인: 화면 문구와 fixture에서 `사라`, `팔아라`, `확정`, `수익 보장`, `모독`, `바보` 같은 행동 지시/조롱형 표현이 서비스 결론으로 쓰이지 않는지 검색합니다. `매수/매도` 단어는 흐름 데이터인지 행동 평가인지 구분해 리뷰합니다.

### RISK-034. 종목 상태 팩트폭격 헤드라인의 근거 부족

- 관련 영역: layers/ui, market, indicator, agent
- 상태: 후보
- 증상: 종목 상세 상단의 강한 헤드라인이 실제 시황, 기술 지표, 재무, 뉴스/공시 근거보다 먼저 확정되어 단순 조롱 문구처럼 보입니다.
- 영향: 재미는 있지만 금융 서비스 신뢰도가 떨어지고, 특정 종목이나 사용자 판단을 공격하는 화면처럼 보일 수 있습니다.
- 방어: `docs/domains/agent/STOCK_DETAIL_HEADLINE.md` 기준으로 최소 2개 이상의 근거 묶음이 같은 방향일 때만 `spicy`/`roast` 톤을 씁니다. 헤드라인 아래에는 기준일, 기간, 근거 지표 3-5개를 함께 표시합니다.
- 확인: fixture의 `headline`, `subtitle`, `evidence`, `asOf`, `headlineTone`이 서로 맞는지 리뷰하고, 보유 종목 개인화 화면에서는 `roast` 단계가 기본으로 노출되지 않는지 확인합니다.

### RISK-035. 개미 심리 지수가 매매 신호처럼 오해됨

- 관련 영역: indicator, layers/ui, agent
- 상태: 후보
- 증상: 0-100 점수의 `개미 심리 지수`가 높으면 사야 하고 낮으면 팔아야 하는 신호처럼 표시됩니다.
- 영향: 커뮤니티 반응 관찰 지표가 투자 자문이나 시장 조작성 신호처럼 읽힐 수 있고, 작은 표본이나 특정 소스 편중이 과장됩니다.
- 방어: 화면에서는 `매수/매도 신호`가 아니라 `커뮤니티 반응 온도` 또는 `개미 심리 지수`로 표시합니다. 점수 옆에 표본 수, 기간, 소스 수, 신뢰도 배지, `관찰 지표` 라벨을 함께 둡니다. 낮은 표본 수나 소스 편중이 크면 점수를 숨기거나 흐리게 표시합니다.
- 확인: fixture와 화면 문구에서 `추천`, `진입`, `탈출`, `신호 확정` 같은 행동 유도 문구가 지수와 함께 쓰이지 않는지 검색하고, 낮은 표본 fixture에서 warning 상태가 노출되는지 확인합니다.

### RISK-036. 네이버 금융 수급 표 구조 변경

- 관련 영역: market, layers/ui, layers/ops
- 상태: 후보
- 증상: `naver-finance` 수급 provider가 네이버 금융 HTML 표 구조 변경, 차단, 빈 응답 때문에 거래일별 수급 row를 만들지 못합니다.
- 영향: 종목 상세 수급 표가 비거나, 개인 잔차 추정값이 직접 관찰값처럼 오해될 수 있습니다.
- 방어: provider 실패 때 0값을 저장하지 않고 public history는 빈 배열을 반환합니다. 외국인/기관은 관찰 수량, 개인은 잔차 추정값으로 `derived=true`를 내려 프론트가 `개인(잔차)` 또는 `개인 추정`으로 표시하게 합니다. pykrx, KRX OpenAPI, 권한이 명확한 vendor를 대체 후보로 유지합니다.
- 확인: provider fixture와 live smoke에서 row parsing을 검증하고, 프론트는 `netAmount=null`을 0원으로 표시하지 않는지 확인합니다.
