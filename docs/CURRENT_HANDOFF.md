# 현재 작업 인수인계

마지막 갱신: 2026-05-14

이 문서는 새 채팅, 병렬 에이전트, 또는 다음 작업자가 가장 먼저 읽는 요약입니다. 자세한 제품 방향은 `docs/FINAL_PRODUCT_PLAN.md`, 현재 MVP 범위는 `docs/PROJECT_BRIEF.md`, 작업 방식은 `docs/WORKFLOW.md`, Git/PR 규칙은 `docs/GIT_CONVENTION.md`를 기준으로 봅니다. 크롤링/공개 배포 리스크는 `docs/LEGAL_RISK_CASES.md`, 병렬 작업 트랙은 `docs/workstreams/README.md`를 기준으로 봅니다.

## 지금까지 한 일

- 너나사 (YouBuyFirst) MVP 저장소를 초기 구성했습니다.
- Spring Boot 백엔드, Python worker, MySQL, Docker Compose 기반 로컬 실행 구성을 만들었습니다.
- 네이버 종토방과 에펨코리아 게시글 수집, 종목 매칭, LLM provider 추상화, mock sentiment fallback, ingestion API, admin 조회 API를 구현했습니다.
- 제한 원문 저장 정책을 반영했습니다: 제목, 본문 일부, URL, 작성 시각, 작성자 표시명 해시, 원문 해시만 저장합니다.
- Swagger에서 crawl run, posts, stock metrics를 확인할 수 있게 했습니다.
- GitHub Actions CI와 PR 템플릿을 추가했습니다.
- 최종 기획안, MVP 범위, 작업 목록, 에이전트 인수인계 문서를 추가했습니다.
- 문서의 제품명은 `너나사 (YouBuyFirst)`로 정리했고, 런타임 식별자도 `com.youbuyfirst`, `youbuyfirst-worker`, `youbuyfirst` DB 이름 기준으로 맞췄습니다.
- 최종 기획에 커뮤니티별 수익률 비교 에이전트, 시세/호가 중심 투자 참고 화면, 소스별 수집 활성화 정책을 반영했습니다.
- 크롤링 분쟁 사례와 공개 배포 리스크를 별도 문서로 정리했습니다.
- 여러 채팅이 동시에 일할 수 있도록 다섯 개의 병렬 작업 트랙 문서를 추가했습니다.

## 최근 결정

- 사용자용 PowerShell 스크립트는 두지 않습니다.
- PR 생성, 라벨 지정, CI 확인, merge는 Codex/에이전트가 `git`과 `gh`로 직접 처리합니다.
- PR 설명과 커밋 본문은 한국어로 작성합니다.
- PR 제목은 `[타입][영역] 한국어 요약` 형식을 사용합니다.
- PR 본문은 결과 중심으로 씁니다. 검증 섹션에는 명령어 나열보다 사람이 읽을 수 있는 통과 결과와 확인 사실을 먼저 적습니다.
- PR 본문과 Notion 작업일지는 같은 카드 구조를 씁니다: 한눈에 보기, 변경 내용, 검증 결과, 리스크, 다음 에이전트 메모.
- Notion 허브는 B + A 하이브리드 구조를 씁니다: 첫 화면은 command center, 세부 기록은 PR 카드 로그입니다.
- 너무 큰 PR을 피하기 위해 5개 파일 이하를 선호하고, 10개 파일을 넘으면 분리 가능성을 먼저 검토합니다.
- 30분 커뮤니티 집계는 제품 핵심으로 유지합니다.
- 공개 배포 시 원문 재게시, 작성자 추적, 닉네임 랭킹은 하지 않고 집계 지표와 AI 재서술 근거 중심으로 표시합니다.
- 소스별 상태는 `enabled`, `public-demo-only`, `local-research-only`, `disabled`로 나눕니다.
- 네이버/에펨코리아/디시/토스는 약관과 robots 정책 리스크가 있으므로 공개 운영 전에 소스별 검토가 필요합니다.
- 병렬 작업은 `community-data-platform`, `signal-intelligence`, `market-simulation-engine`, `frontend-experience`, `product-planning-ops` 다섯 트랙으로 나눕니다.
- 병렬 작업 PR에는 `stream:data`, `stream:signal`, `stream:market`, `stream:frontend`, `stream:product` 중 하나를 붙이고, Notion 작업 카드의 `트랙` 속성도 채웁니다.
- 프론트 작업은 `frontend-experience` 트랙으로 시작하고 `stream:frontend`, `area:frontend` 라벨을 함께 붙입니다.
- 기획/조율/문서/Notion/PR 운영은 `product-planning-ops` 트랙이 맡습니다.
- `market-simulation-engine`은 `market-data`, `simulation-core`, `agent-runtime` lane으로 나눠 시세 수집, 모의 체결, AI 에이전트 작업을 같은 PR에 섞지 않습니다.
- 의존이 적은 작업은 단위 테스트 후 `main`으로 바로 PR을 보냅니다. 결합이 강한 작업만 짧은 수명의 `track/*` 브랜치에서 통합 테스트 후 `main`으로 보냅니다.

## 현재 GitHub 상태

- Repository: `99hyuk/YouBuyFirst`
- Default branch: `main`
- Bootstrap PR: https://github.com/99hyuk/YouBuyFirst/pull/1
- PR #1 상태: CI 통과 후 squash merge 완료
- GitHub labels: `type:*`, `area:*`, `size:*` 라벨 생성 완료
- 현재 checkout은 작업자별로 달라질 수 있으므로 `git status --short --branch`로 확인합니다.

## 현재 Notion 상태

- Project hub: https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77
- 작업일지: https://www.notion.so/35fdf321bd898183bd4ec871623d8917
- 트러블슈팅: https://www.notion.so/35fdf321bd8981559e31e55584337cea
- GitHub PR 운영 메모: https://www.notion.so/35fdf321bd89815c9808ff01a683f4bc
- 작업이 끝나면 핵심 변경, 검증 결과, PR 링크, 다음 작업자 메모를 Notion 작업일지에 남깁니다.
- 트러블슈팅이 반복될 가능성이 있으면 트러블슈팅 페이지에 incident card 형태로 증상, 영향, 원인, 해결, 검증, 재발 방지를 남깁니다.

## 마지막 검증 기록

- Runtime identifier rename branch: Backend Docker test 통과, 2 tests
- Runtime identifier rename branch: Worker Docker test 통과, 4 tests
- Runtime identifier rename branch: Docker Compose 기동 및 Swagger `200` 확인
- Runtime identifier rename branch: 옛 프로젝트명/패키지명 검색 결과 없음
- Runtime identifier rename branch: `git diff --check` 통과

## 다음 에이전트가 지켜야 할 규칙

1. 먼저 `AGENTS.md`, 이 파일, `docs/FINAL_PRODUCT_PLAN.md`, `docs/PROJECT_BRIEF.md`, `docs/TASKS.md`, `docs/GIT_CONVENTION.md`를 읽습니다.
2. 병렬 작업이면 `docs/workstreams/README.md`와 담당 트랙 문서를 읽습니다.
3. 한 PR에는 한 기능, 한 버그 수정, 한 문서 정리, 또는 한 인프라 변경만 담습니다.
4. 제목과 GitHub 라벨로 타입, 영역, 크기를 구분합니다.
5. dashboard, OCR, 모의투자, 인증, 보안, 운영 배포는 현재 MVP 작업에 섞지 않습니다.
6. PR 전에는 관련 테스트와 `git diff --check`를 실행합니다.
7. PR 본문에는 검증 결과를 자연어로 요약하고, 명령어는 보조 정보로 둡니다.
8. CI가 통과하면 squash merge하고 브랜치를 삭제합니다.

## 가장 가까운 다음 작업 후보

- 네이버 종토방 실제 HTML 변화에 맞춘 parser 보강
- 에펨코리아 게시판 parser 보강
- 종목 게시판형 소스를 위한 `CrawlTarget` 최소 설계
- 소스별 활성화 상태 설계
- worker가 backend readiness를 기다리도록 개선
- admin API Swagger 예시와 validation 오류 응답 정리
