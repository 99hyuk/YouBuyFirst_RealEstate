# ops

## 역할

ops는 문서 구조, Git/PR, Notion 기록, 작업 영역 조율, 브랜치/worktree 생명주기, 컨텍스트 예산을 소유합니다.

세부 실행 규칙은 중복하지 않습니다. 작업 시작은 `AGENTS.md`, 문서 구조는 `DOCUMENTATION_GUIDE.md`, 브랜치/PR은 `WORKFLOW.md`와 `GIT_CONVENTION.md`, 라벨은 `LABEL_GUIDE.md`, 작업 영역 경계는 `WORK_AREAS.md`를 봅니다.

## 담당 범위

- PR 템플릿과 GitHub Actions
- Notion 작업 로그, 개발자 기술 경험, 에이전트 운영 로그
- 문서 구조와 읽기 우선순위 관리
- 공개 배포 정책
- 인증/인가 도입 시점 설계
- Docker Compose smoke test
- 운영 문서와 인수인계 문서
- 작업 영역별 PR/Notion 상태와 main 통합 시점 점검
- stale/close-candidate 브랜치와 worktree 정리 기준 운영
- 에이전트 행동 규칙 PR 머지 후 열린 worktree/main 전파 상태 점검
- 개발자 포트폴리오 관점의 문제해결, 성능개선, 품질개선, 기술결정 기록 기준
- 빈 채팅과 짧은 작업 영역 지시 처리 규칙 관리
- 루트 대시보드, 작업 영역별 진행판, 제품 기획과 작업 맥락의 정합성 점검

## 파일 소유권

주로 담당:

- `docs/`
- `.github/`
- Docker Compose 운영 문서
- Notion 기록 기준
- 기술 경험 기록 템플릿

공유 전 협의:

- backend API contract
- pipeline payload contract
- DB migration
- front package
- realestate/analysis/indicator/agent domain schema

## 현재 우선순위

- 시작 문서와 도메인/layer 문서의 신호 밀도 유지
- 열린 브랜치/worktree를 active, review, blocked, stale, close-candidate로 분류
- Notion 작업 로그, 개발자 기술 경험 DB, 에이전트 운영 로그의 목적 분리
- 공개 배포 정책, 인증/인가 도입 시점, CI/smoke test 기준 정리
- PR 본문을 사람이 먼저 이해하는 설명으로 유지

## PR 커뮤니케이션 기준

PR 규칙의 정본은 `GIT_CONVENTION.md`입니다. 이 README에는 원칙만 둡니다.

- 무엇이 달라졌는지와 왜 필요한지를 먼저 씁니다.
- 파일 경로와 내부 구현명은 보조 근거로 둡니다.
- 검증 결과는 명령어만 나열하지 않고 확인 의미를 함께 적습니다.

## 하지 않는 일

- crawler parser 구현
- 반응 지표 산식 구현
- market fact provider 내부 구현
- legacy stock/simulation 삭제 판단
- 사용자 대시보드 UI 구현
