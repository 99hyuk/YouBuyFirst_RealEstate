# 현재 작업 인수인계

마지막 갱신: 2026-05-16

이 문서는 새 채팅이 방향을 잡는 짧은 요약입니다. 전문 읽기를 기본값으로 두지 말고, 필요한 섹션만 확인합니다. 자세한 규칙은 `docs/DOCUMENTATION_GUIDE.md`, 작업 방식은 `docs/WORKFLOW.md`, PR 규칙은 `docs/GIT_CONVENTION.md`, 트랙 경계는 `docs/workstreams/`를 봅니다.

## 현재 상태

- Repository: `99hyuk/YouBuyFirst`
- Default branch: `main`
- 루트 checkout: `C:\agents\YouBuyFirst`는 main/조율용
- 병렬 작업 위치: `C:\agents\YouBuyFirst\.worktrees\<task>`
- 현재 열려 있는 최적화 PR: PR #52 `[ops][docs] 채팅 안정성 규칙`
- 최근 핵심 기반: Spring Boot backend, Python pipeline, MySQL, Docker Compose, Vue 3 front mock shell

## 제품/구현 스냅샷

- MVP는 네이버 종토방과 에펨코리아 주식 게시판 글을 수집하고, 종목 언급과 반응 방향을 분석해 backend에 저장합니다.
- backend에는 ingestion/admin API, crawl run 조회, posts 조회, stock metrics 조회가 있습니다.
- pipeline에는 source policy gate, skip run 기록, crawl backoff 정책, AI mention resolver/mock provider 흐름이 있습니다.
- backend에는 `CrawlTarget` queue API와 구조화된 skip/backoff 필드가 들어갔고, pipeline 연결은 후속 작업입니다.
- front는 `front/`의 Vue 3 + Vite + TypeScript mock 와이어프레임 shell 상태입니다. 실제 backend API 연결은 후속 작업입니다.
- front 와이어프레임 복구 정본은 `docs/workstreams/front/WIREFRAME_HANDOFF.md`입니다. 현재 dashboard는 `Briefing + Terminal` 방향입니다.

## 최근 결정

- 문서는 길게 누적하지 않습니다. `AGENTS.md`, 이 문서, 스킬 문서, Notion, 세션 로그는 필요한 섹션만 봅니다.
- 채팅이 `앗, 오류가 발생했습니다`로 막히면 제품 코드보다 대화 컨텍스트/도구 출력 과다를 먼저 의심합니다.
- 스킬 문서, gstack, Notion fetch, 세션 로그 검색은 시작 루틴이 아닙니다.
- gstack은 front/UI 변경처럼 실제 브라우저 확인 가치가 있을 때 사용하고, 콘솔/DOM 전문은 대화에 누적하지 않습니다.
- 시작 문서나 트랙 문서를 바꾸는 PR은 컨텍스트 예산을 점검하되, 미완료 작업과 필수 검증은 줄이지 않습니다.
- 제품 용어는 사용자 화면에서 `커뮤니티 반응`, 단일 분석값은 `반응 방향`, 내부 후보 필드는 `reactionDirection`을 씁니다.
- 소스 상태는 `enabled`, `public-demo-only`, `local-research-only`, `disabled`로 나눕니다. 새 소스는 기본 `disabled`입니다.
- 공개 배포 전에는 원문 재게시, 작성자 추적, 닉네임 랭킹을 하지 않습니다.
- PR 제목은 `[트랙][타입] 명사형 요약`, 브랜치는 `codex/<task>`를 씁니다.
- 한국어 PR 본문은 UTF-8 no BOM 파일과 `gh --body-file`을 사용합니다.

## 트랙별 바로 보기

- `crawl`: source policy, crawl target queue, backoff, source adapter
- `data`: stock alias, mention resolver, reaction direction, 30분 집계
- `market`: quote snapshot/cache/WebSocket 계약
- `trade`: 가상 계좌, 주문, 체결, 포트폴리오
- `agent`: AI 매매 판단, 커뮤니티별 성과 비교, 결정 로그
- `front`: dashboard shell, mock/API 연결, 브라우저 QA
- `ops`: 문서, Notion, PR/CI, 배포 정책, 작업 조율

## 현재 Notion 정본

- Project hub: https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77
- Archive & Admin: https://www.notion.so/360df321bd8981a6a60df71bca8bad5d
- 제품 기획과 작업 맥락: https://www.notion.so/360df321bd89815c9767e703058990db
- 작업 로그 DB: `collection://be609137-1bd8-4b22-989e-a987a8185135`
- 개발자 기술 경험 DB: `collection://7f052514-c585-4621-ad28-b54bb2eac5a8`
- 에이전트 운영 로그 DB: `collection://8646042e-8ea0-4dd5-a056-c01a8ec096ec`
- 다음 작업 DB: `collection://ecdda994-6376-489d-bd83-4cfbadb6de70`

Notion 구조 변경은 전체 fetch가 아니라 대상 page/database 하나씩 확인합니다. 루트/Archive/주요 DB를 바꾸면 child link 보존 여부를 먼저 봅니다.

## 다음 에이전트 규칙

1. `AGENTS.md`, 이 문서, `docs/DOCUMENTATION_GUIDE.md`는 필요한 섹션만 확인합니다.
2. 트랙이 명확하면 담당 트랙 README를 우선 확인하고, 트랙 경계가 헷갈릴 때만 `docs/workstreams/README.md`를 봅니다.
3. 루트 checkout에서 병렬 작업하지 말고 `.worktrees/<task>`에 worktree를 만듭니다.
4. 작업 트랙, 수정 대상, 기록 위치, 주요 위험을 먼저 선언합니다.
5. 한 PR에는 한 기능, 한 버그 수정, 한 문서 정리, 또는 한 CI/runtime 설정 변경만 담습니다.
6. 모순, 리스크, 더 나은 대안이 보이면 구현보다 질문/반박을 먼저 합니다.
7. 관련 테스트와 `git diff --check`를 실행합니다.
8. PR 생성/수정 후 본문 한글 깨짐과 `??` 치환 문자열을 확인합니다.
9. 완료 보고에는 Superpowers/gstack 사용 여부와 이유를 짧게 적습니다.
10. 제품 개발/운영 문제는 개발자 기술 경험 DB, 에이전트/도구 운영 사고는 에이전트 운영 로그 DB에 분리합니다.

## 가까운 다음 작업 후보

- pipeline이 backend `CrawlTarget` API를 사용하되 static target fallback 유지
- admin target pause/resume/clear-backoff API와 화면 액션 연결
- front shell 브라우저 QA와 기획자 확인 필요 항목 정리
- market quote snapshot 계약 설계
- 실제 `OPENAI_API_KEY` 기반 AI mention resolver 샘플 품질 확인
- pipeline이 backend readiness를 기다리도록 개선
- admin API Swagger 예시와 validation 오류 응답 정리
- backend 도메인 패키지를 `stock`, `analysis`, `indicator` 목표 이름으로 리네임
