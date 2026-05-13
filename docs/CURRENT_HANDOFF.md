# 현재 작업 인수인계

마지막 갱신: 2026-05-13

이 문서는 새 채팅, 병렬 에이전트, 또는 다음 작업자가 가장 먼저 읽는 요약입니다. 자세한 제품 방향은 `docs/FINAL_PRODUCT_PLAN.md`, 현재 MVP 범위는 `docs/PROJECT_BRIEF.md`, 작업 방식은 `docs/WORKFLOW.md`를 기준으로 봅니다.

## 지금까지 한 일

- 인간지표 MVP 저장소를 초기 구성했습니다.
- Spring Boot 백엔드, Python worker, MySQL, Docker Compose 기반 로컬 실행 구성을 만들었습니다.
- 네이버 종토방과 에펨코리아 게시글 수집, 종목 매칭, LLM provider 추상화, mock sentiment fallback, ingestion API, admin 조회 API를 구현했습니다.
- 제한 원문 저장 정책을 반영했습니다: 제목, 본문 일부, URL, 작성 시각, 작성자 표시명 해시, 원문 해시만 저장합니다.
- Swagger에서 crawl run, posts, stock metrics를 확인할 수 있게 했습니다.
- 작업 단위를 작게 쪼개기 위해 GitHub PR 자동화 문서와 스크립트를 추가했습니다.

## 최근 추가한 작업 관리 장치

- `.github/pull_request_template.md`: PR 설명 템플릿
- `.github/workflows/ci.yml`: backend/worker 테스트용 GitHub Actions
- `scripts/new-work-unit.ps1`: 작업 단위 문서와 `codex/<task>` 브랜치 생성
- `scripts/open-pr.ps1`: 검증, stage, commit, push, draft PR 생성
- `scripts/setup-github.ps1`: GitHub remote와 `gh` 인증 상태 확인, 연결 가이드 출력
- `docs/WORKFLOW.md`: 보수적 PR 단위 개발 규칙
- `docs/PR_AUTOMATION.md`: GitHub 연동과 PR 생성 절차
- `docs/work-units/`: 작업 단위별 결정과 검증 기록

## 현재 로컬 상태

- 브랜치: `codex/human-indicator-mvp`
- GitHub remote: `origin` 연결 완료, `https://github.com/99hyuk/YouBuyFirst.git`
- GitHub CLI: 설치와 인증 확인 완료, Codex PATH에는 없을 수 있어 스크립트가 `C:\Program Files\GitHub CLI\gh.exe`를 fallback으로 찾습니다
- Bootstrap draft PR: https://github.com/99hyuk/YouBuyFirst/pull/1
- Docker Compose: 이전 실행에서 backend, worker, MySQL까지 구동 확인
- Swagger: `http://localhost:8080/swagger-ui.html`
- MySQL host port: `3307`

## 마지막 검증 기록

- Backend Docker test: 통과, 2 tests
- Worker Docker test: 통과, 4 tests
- `git diff --check`: 통과
- PowerShell script parse check: `scripts/open-pr.ps1`, `scripts/new-work-unit.ps1` 통과
- `scripts/setup-github.ps1` 실행 확인: `99hyuk/YouBuyFirst` remote 연결 완료
- 문서/자동화 변경 뒤 Docker 상태 조회는 Windows Docker 권한 문제로 막혔습니다

## 다음 에이전트가 지켜야 할 규칙

1. 먼저 `AGENTS.md`, 이 파일, `docs/FINAL_PRODUCT_PLAN.md`, `docs/PROJECT_BRIEF.md`, `docs/TASKS.md`를 읽습니다.
2. 새 작업은 반드시 `docs/work-units/`에 작업 단위 문서를 만들거나 갱신합니다.
3. 한 PR에는 한 기능, 한 버그 수정, 또는 한 인프라 변경만 담습니다.
4. dashboard, OCR, 모의투자, 인증, 보안, 운영 배포는 현재 MVP에 섞지 않습니다.
5. PR 전에는 관련 테스트와 `git diff --check`를 실행합니다.

## 가장 가까운 다음 작업 후보

- PR #1 CI 결과 확인 후 리뷰/머지 여부 결정
- 네이버 종토방 실제 HTML 변화에 맞춘 parser 보강
- 에펨코리아 게시판 parser 보강
- worker가 backend readiness를 기다리도록 개선
- admin API Swagger 예시와 validation 오류 응답 정리
