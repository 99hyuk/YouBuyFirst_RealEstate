# 현재 작업 인수인계

마지막 갱신: 2026-05-13

이 문서는 새 채팅, 병렬 에이전트, 또는 다음 작업자가 가장 먼저 읽는 요약입니다. 자세한 제품 방향은 `docs/FINAL_PRODUCT_PLAN.md`, 현재 MVP 범위는 `docs/PROJECT_BRIEF.md`, 작업 방식은 `docs/WORKFLOW.md`, Git/PR 규칙은 `docs/GIT_CONVENTION.md`를 기준으로 봅니다.

## 지금까지 한 일

- 너나사 (YouBuyFirst) MVP 저장소를 초기 구성했습니다.
- Spring Boot 백엔드, Python worker, MySQL, Docker Compose 기반 로컬 실행 구성을 만들었습니다.
- 네이버 종토방과 에펨코리아 게시글 수집, 종목 매칭, LLM provider 추상화, mock sentiment fallback, ingestion API, admin 조회 API를 구현했습니다.
- 제한 원문 저장 정책을 반영했습니다: 제목, 본문 일부, URL, 작성 시각, 작성자 표시명 해시, 원문 해시만 저장합니다.
- Swagger에서 crawl run, posts, stock metrics를 확인할 수 있게 했습니다.
- GitHub Actions CI와 PR 템플릿을 추가했습니다.
- 최종 기획안, MVP 범위, 작업 목록, 에이전트 인수인계 문서를 추가했습니다.
- 문서의 제품명은 `너나사 (YouBuyFirst)`로 정리했고, 런타임 식별자도 `com.youbuyfirst`, `youbuyfirst-worker`, `youbuyfirst` DB 이름 기준으로 맞췄습니다.

## 최근 결정

- 사용자용 PowerShell 스크립트는 두지 않습니다.
- PR 생성, 라벨 지정, CI 확인, merge는 Codex/에이전트가 `git`과 `gh`로 직접 처리합니다.
- PR 설명과 커밋 본문은 한국어로 작성합니다.
- PR 제목은 `[타입][영역] 한국어 요약` 형식을 사용합니다.
- PR 본문은 결과 중심으로 씁니다. 검증 섹션에는 명령어 나열보다 사람이 읽을 수 있는 통과 결과와 확인 사실을 먼저 적습니다.
- PR 본문과 Notion 작업일지는 같은 카드 구조를 씁니다: 한눈에 보기, 변경 내용, 검증 결과, 리스크, 다음 에이전트 메모.
- Notion 허브는 B + A 하이브리드 구조를 씁니다: 첫 화면은 command center, 세부 기록은 PR 카드 로그입니다.
- 너무 큰 PR을 피하기 위해 5개 파일 이하를 선호하고, 10개 파일을 넘으면 분리 가능성을 먼저 검토합니다.

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
2. 한 PR에는 한 기능, 한 버그 수정, 한 문서 정리, 또는 한 인프라 변경만 담습니다.
3. 제목과 GitHub 라벨로 타입, 영역, 크기를 구분합니다.
4. dashboard, OCR, 모의투자, 인증, 보안, 운영 배포는 현재 MVP 작업에 섞지 않습니다.
5. PR 전에는 관련 테스트와 `git diff --check`를 실행합니다.
6. PR 본문에는 검증 결과를 자연어로 요약하고, 명령어는 보조 정보로 둡니다.
7. CI가 통과하면 squash merge하고 브랜치를 삭제합니다.

## 가장 가까운 다음 작업 후보

- 네이버 종토방 실제 HTML 변화에 맞춘 parser 보강
- 에펨코리아 게시판 parser 보강
- worker가 backend readiness를 기다리도록 개선
- admin API Swagger 예시와 validation 오류 응답 정리
