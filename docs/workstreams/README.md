# 병렬 작업 트랙 안내

너나사 (YouBuyFirst)는 여러 채팅과 에이전트가 동시에 일할 수 있도록 다섯 개의 작업 트랙으로 나눕니다. 실제 MSA로 바로 분리하지는 않지만, 문서, 브랜치, PR, 파일 소유권은 서비스 경계처럼 명확히 나눕니다.

## 공통 시작 절차

다른 채팅에서 작업을 시작할 때는 아래 문장을 그대로 붙여 넣어도 됩니다.

```text
너는 너나사 (YouBuyFirst)의 <트랙명> 담당 에이전트야.
먼저 AGENTS.md, docs/CURRENT_HANDOFF.md, docs/FINAL_PRODUCT_PLAN.md를 읽고,
docs/workstreams/<트랙명>/README.md도 읽어.
이 채팅에서는 <작업 범위>만 다루고, 다른 트랙 파일은 건드리지 마.
작업 하나는 브랜치 하나와 PR 하나로 만들어줘.
PR 설명과 작업 기록은 한국어로 작성해줘.
```

새 채팅은 이전 채팅의 기억을 자동으로 이어받지 못할 수 있습니다. 그래서 담당 에이전트가 계속 참고해야 할 기억은 채팅 안의 약속이 아니라 저장소 문서에 둡니다. 각 에이전트는 시작할 때 `AGENTS.md`, `docs/CURRENT_HANDOFF.md`, 이 문서, 담당 트랙 README를 읽고 자기 역할을 복원합니다.

## 트랙 목록

| 트랙 | 역할 | 브랜치 예시 |
| --- | --- | --- |
| `community-data-platform` | 커뮤니티 수집, 소스 어댑터, 종목별 수집 타깃, 수집 정책 | `codex/data-naver-target-scheduler` |
| `signal-intelligence` | 종목 인식, 감성 분석, 열기 지수, 커뮤니티별 수익률 비교 | `codex/signal-community-alpha-agent` |
| `market-simulation-engine` | 시세/호가, Redis quote cache, 모의투자, AI 에이전트 | `codex/market-quote-cache` |
| `frontend-experience` | 사용자 대시보드, UI 상태, mock data, API 연동, 차트 | `codex/frontend-dashboard-shell` |
| `product-planning-ops` | 기획 조율, 작업 분리, 문서, Notion, PR/CI, 배포 정책 | `codex/product-track-branch-strategy` |

`frontend-experience`는 별도 구현 트랙입니다. 프론트는 완전 후반에 몰아서 하지 않고, fixture/mock 기반 화면 골격을 일찍 만들고 API 계약이 생길 때마다 연결합니다.

`product-planning-ops`는 구현이 전혀 없는 트랙이 아닙니다. 다만 이 트랙의 구현은 문서, 자동화, CI, Notion, 배포 정책, 작업 조율에 한정합니다. 사용자 화면 구현은 `frontend-experience`가 맡습니다.

`market-simulation-engine` 안에는 `market-data`, `simulation-core`, `agent-runtime` lane이 있습니다. 시세 수집, 모의투자 체결, AI 에이전트 실행은 같은 트랙 안에 있지만 같은 PR에 섞지 않습니다.

## 충돌 방지 규칙

- 한 PR은 한 트랙만 소유합니다.
- 다른 트랙의 파일을 바꿔야 하면 먼저 계약 문서나 이슈를 남깁니다.
- 공통 schema, OpenAPI, DB migration은 충돌이 잦으므로 작은 계약 PR로 먼저 분리합니다.
- `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`는 작업 상태를 바꿀 때만 갱신합니다.
- 파일 소유권이 애매하면 구현보다 먼저 문서 PR로 경계를 정합니다.

## 브랜치 전략

기본은 작은 PR을 `main`에 자주 통합하는 방식입니다.

- 의존이 적은 작업은 `codex/<prefix>-<task>` 브랜치에서 작업하고, 테스트 통과 후 바로 `main`으로 PR을 보냅니다.
- 공통 계약 PR은 가능한 한 먼저 `main`에 넣습니다. 예: API schema, DB migration, fixture, mock response, 이벤트 payload.
- 기능이 아직 화면에 드러나면 안 되면 feature flag, mock mode, disabled default로 숨깁니다.

결합이 강한 작업만 짧은 수명의 `track/*` 통합 브랜치를 씁니다.

- 예: `track/frontend-dashboard`, `track/market-quotes`
- 하위 작업은 `codex/<prefix>-<task>` 브랜치에서 만들고, PR base를 해당 `track/*` 브랜치로 둡니다.
- `track/*` 브랜치는 2-4개 PR, 3-5일 안에 `main`으로 통합하는 것을 목표로 합니다.
- `track/*`가 길어지면 통합 리스크가 뒤로 밀리므로 쪼개거나 계약 PR을 먼저 `main`에 넣습니다.
- 통합 전에는 해당 트랙의 테스트와 Docker/수동 smoke test를 실행합니다.

## PR 라벨

기존 `type:*`, `area:*`, `size:*` 라벨에 더해 `stream:*` 라벨을 반드시 붙입니다.

| 트랙 | GitHub 라벨 | 브랜치 prefix | Notion 트랙 |
| --- | --- | --- | --- |
| `community-data-platform` | `stream:data` | `codex/data-*` | `community-data-platform` |
| `signal-intelligence` | `stream:signal` | `codex/signal-*` | `signal-intelligence` |
| `market-simulation-engine` | `stream:market` | `codex/market-*` | `market-simulation-engine` |
| `frontend-experience` | `stream:frontend` | `codex/frontend-*` | `frontend-experience` |
| `product-planning-ops` | `stream:product` | `codex/product-*` | `product-planning-ops` |

예시:

```text
트랙: community-data-platform
변경 범위: worker crawler scheduler, docs/workstreams/community-data-platform
```

## Notion 구분

작업 로그 DB와 다음 작업 DB에는 `트랙` select 속성을 둡니다. 새 작업 카드는 담당 트랙을 반드시 채웁니다.

기획, 운영 기준 정리, 다른 트랙 조율 작업은 기본적으로 `product-planning-ops`로 둡니다. 실제 기능 구현은 각 기능 트랙으로 분리합니다.
