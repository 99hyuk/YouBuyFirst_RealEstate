# 보수적 개발 워크플로

## 원칙

기능 하나, 버그 하나, 문서 정리 하나, 인프라 변경 하나는 PR 하나로 끝냅니다.

무관한 작업을 묶지 않습니다. 여러 subsystem을 건드리는 일이면, 함께 배포되어야 앱이 동작하는 경우를 제외하고 나눕니다.

## 작업 순서

1. `docs/CONTEXT.md`, `docs/CURRENT_HANDOFF.md`, `docs/PROJECT_BRIEF.md`, `docs/TASKS.md`를 읽습니다.
2. `docs/GIT_CONVENTION.md`의 제목, 라벨, 크기 규칙을 확인합니다.
3. 병렬 작업이면 `docs/workstreams/README.md`와 담당 트랙 문서를 읽습니다.
4. 작업이 크거나 병렬화될 수 있으면 `docs/work-units/`에 짧은 작업 단위 문서를 직접 추가합니다.
5. 해당 작업만 구현합니다.
6. 관련 검증을 실행합니다.
7. 필요하면 `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`를 갱신합니다.
8. `codex/<작업명>` 브랜치를 push하고 PR을 엽니다.
9. `type:*`, `area:*`, `stream:*`, `size:*` GitHub 라벨을 붙이고 CI를 확인합니다.
10. CI가 통과하면 squash merge하고 브랜치를 삭제합니다.
11. Notion 작업일지에 핵심 변경, 검증 결과, PR 링크, 다음 작업자 메모를 남깁니다.

## PR 크기 기준

- 선호: 5개 파일 이하
- 허용: 10개 파일 이하
- 11개 이상: 원칙적으로 나눕니다
- 예외: 초기 bootstrap, schema와 코드가 반드시 함께 가야 하는 작은 계약 변경

## 브랜치 이름

형식:

```text
codex/<short-task-name>
```

예시:

- `codex/crawler-parser-hardening`
- `codex/add-ci`
- `codex/instrument-master-import`

트랙이 분명하면 브랜치 이름 앞부분에 트랙을 드러냅니다.

예시:

- `codex/data-naver-target-scheduler`
- `codex/signal-community-alpha-agent`
- `codex/market-quote-cache`
- `codex/product-dashboard-shell`

## 병렬 작업 트랙

여러 채팅에서 동시에 작업할 때는 아래 네 트랙 중 하나를 고릅니다.

- `community-data-platform`: 커뮤니티 수집, 소스 어댑터, 종목별 수집 타깃, 수집 정책
- `signal-intelligence`: 종목 인식, 감성 분석, 열기 지수, 커뮤니티별 수익률 비교
- `market-simulation-engine`: 시세/호가, Redis quote cache, 모의투자, AI 에이전트
- `product-ops-experience`: 대시보드, 관리자 경험, 문서, Notion, PR/CI, 배포 정책

각 트랙의 상세 범위와 파일 소유권은 `docs/workstreams/` 아래 문서를 따릅니다. 한 채팅은 가능한 한 한 트랙만 담당합니다.

프론트 작업은 `product-ops-experience`의 `frontend lane`으로 시작합니다. 화면 골격과 mock 데이터 작업은 API 구현 전에도 진행할 수 있고, 실제 API 연결은 각 기능 트랙의 계약이 생긴 뒤 별도 PR로 진행합니다.

`market-simulation-engine`은 내부적으로 `market-data`, `simulation-core`, `agent-runtime` lane으로 나눕니다. 시세 수집, 모의 체결, 에이전트 판단은 기술 성격이 다르므로 같은 PR에 섞지 않습니다.

트랙별 GitHub 라벨:

- `stream:data`: `community-data-platform`
- `stream:signal`: `signal-intelligence`
- `stream:market`: `market-simulation-engine`
- `stream:product`: `product-ops-experience`

## PR에 반드시 포함할 내용

- 한국어 요약
- `[타입][영역]` 제목
- 타입/영역/트랙/크기 라벨
- 리뷰 가이드
- 사람이 읽기 쉬운 검증 결과
- 남은 리스크
- 후속 작업
- Notion 기록 링크

PR 본문은 Notion 작업 카드와 같은 구조로 씁니다. 첫 화면에서 의도와 상태를 보고, 중간에서 변경 범위를 이해하고, 마지막에서 검증과 다음 작업을 확인할 수 있어야 합니다.

검증은 명령어 자체보다 확인한 사실을 먼저 씁니다. 예를 들어 "Backend Docker test 통과, 2 tests"처럼 결과를 요약하고, 실제 명령어는 PR 본문의 접힌 영역이나 보조 설명에 둡니다.

## Notion 기록

- Project hub: https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77
- 작업일지: https://www.notion.so/35fdf321bd898183bd4ec871623d8917
- 트러블슈팅: https://www.notion.so/35fdf321bd8981559e31e55584337cea
- GitHub PR 운영 메모: https://www.notion.so/35fdf321bd89815c9808ff01a683f4bc

Notion은 B + A 하이브리드 구조를 씁니다. 프로젝트 허브는 현재 상태를 빠르게 보는 command center 역할을 하고, 작업일지는 PR별 카드 로그 역할을 합니다.

Notion 작업일지는 PR마다 길게 쓰지 않습니다. 작업 요약, 변경 범위, 검증 결과, PR 링크, 다음 작업자 메모가 있으면 충분합니다. 장애나 반복될 가능성이 있는 문제는 트러블슈팅 문서에 증상, 원인, 해결, 재발 방지 순서로 남깁니다.
