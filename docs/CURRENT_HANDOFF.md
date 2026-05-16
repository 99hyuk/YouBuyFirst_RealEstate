# 현재 작업 인수인계

마지막 갱신: 2026-05-16

새 채팅이 방향을 잡는 짧은 요약입니다. 전문 읽기를 기본값으로 두지 말고 필요한 섹션만 확인합니다.

## 현재 상태

- Repository: `99hyuk/YouBuyFirst`
- Default branch: `main`
- 루트 checkout: `C:\agents\YouBuyFirst`는 main/조율용, 병렬 작업은 `.worktrees/<task>`에서 진행합니다.
- 현재 열려 있는 front/ops 복구 PR: PR #53 `[ops][docs] 프론트 와이어프레임 복구 정리`
- 기반: Spring Boot backend, Python pipeline, MySQL, Docker Compose, Vue 3 front mock shell

## 구현 스냅샷

- MVP는 커뮤니티 글 수집, 종목 언급 인식, 반응 방향 분석, backend 저장까지 연결된 ingestion 기반입니다.
- backend에는 ingestion/admin API, crawl run/posts/stock metrics 조회, `CrawlTarget` queue API가 있습니다.
- pipeline에는 source policy gate, skip run 기록, crawl backoff, AI mention resolver/mock provider 흐름이 있습니다.
- front는 `front/`의 Vue 3 + Vite + TypeScript mock 와이어프레임 shell입니다. 대시보드 정본은 `docs/workstreams/front/WIREFRAME_HANDOFF.md`, Stitch 프롬프트는 `docs/workstreams/front/STITCH_DASHBOARD_PROMPT.md`입니다.

## 최근 결정

- 문서는 길게 누적하지 않습니다. `AGENTS.md`, 이 문서, 스킬 문서, Notion, 세션 로그는 필요한 섹션만 봅니다.
- 채팅이 `앗, 오류가 발생했습니다`로 막히면 제품 코드보다 대화 컨텍스트/도구 출력 과다를 먼저 의심합니다.
- 스킬 문서, gstack, Notion fetch, 세션 로그 검색은 시작 루틴이 아닙니다.
- 큰 스킬 문서와 `docs/superpowers/` archive는 전문 출력하지 않습니다. Browser/gstack 검증은 필요할 때 한 번에 모아 실행합니다.
- gstack은 front/UI 변경처럼 실제 브라우저 확인 가치가 있을 때 사용하고, 콘솔/DOM 전문은 대화에 누적하지 않습니다.
- 로그/세션 분석은 JSONL 전문 검색이 아니라 `token_count` 같은 필요한 이벤트만 파싱해 수치로 요약합니다.
- 제품 용어는 사용자 화면에서 `커뮤니티 반응`, 단일 분석값은 `반응 방향`, 내부 후보 필드는 `reactionDirection`을 씁니다.
- 소스 상태는 `enabled`, `public-demo-only`, `local-research-only`, `disabled`로 나누며 새 소스는 기본 `disabled`입니다.
- 공개 배포 전에는 원문 재게시, 작성자 추적, 닉네임 랭킹을 하지 않습니다.

## 바로 가기

- 트랙 경계: `docs/workstreams/`
- 문서/컨텍스트 예산: `docs/DOCUMENTATION_GUIDE.md`
- 작업 방식: `docs/WORKFLOW.md`
- Git/PR 규칙: `docs/GIT_CONVENTION.md`
- 라벨: `docs/LABEL_GUIDE.md`
- Notion 정본 위치: `docs/DOCUMENTATION_GUIDE.md`, `docs/ENGINEERING_EVIDENCE_GUIDE.md`

## 다음 작업 후보

- pipeline이 backend `CrawlTarget` API를 사용하되 static target fallback 유지
- admin target pause/resume/clear-backoff API와 화면 액션 연결
- front shell 브라우저 QA와 기획자 확인 필요 항목 정리
- market quote snapshot 계약 설계
- 실제 `OPENAI_API_KEY` 기반 AI mention resolver 샘플 품질 확인
- pipeline이 backend readiness를 기다리도록 개선
- admin API Swagger 예시와 validation 오류 응답 정리
- backend 도메인 패키지를 `stock`, `analysis`, `indicator` 목표 이름으로 리네임
