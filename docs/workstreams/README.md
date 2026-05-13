# 병렬 작업 트랙 안내

너나사 (YouBuyFirst)는 여러 채팅과 에이전트가 동시에 일할 수 있도록 네 개의 작업 트랙으로 나눕니다. 실제 MSA로 바로 분리하지는 않지만, 문서, 브랜치, PR, 파일 소유권은 MSA에 가깝게 분리합니다.

## 공통 시작 절차

다른 채팅에서 작업을 시작할 때는 아래 문장을 그대로 붙여 넣어도 됩니다.

```text
너는 너나사 (YouBuyFirst)의 <트랙명> 담당 에이전트야.
먼저 AGENTS.md, docs/CURRENT_HANDOFF.md, docs/FINAL_PRODUCT_PLAN.md를 읽고,
docs/workstreams/<트랙명>/README.md가 있으면 그것도 읽어.
이 채팅에서는 <작업 범위>만 다루고, 다른 트랙 파일은 건드리지 마.
작업 하나는 브랜치 하나와 PR 하나로 만들어줘.
PR 설명과 작업 기록은 한국어로 작성해줘.
```

## 트랙 목록

| 트랙 | 역할 | 브랜치 예시 |
| --- | --- | --- |
| `community-data-platform` | 커뮤니티 수집, 소스 어댑터, 종목별 수집 타깃, 수집 정책 | `codex/data-naver-target-scheduler` |
| `signal-intelligence` | 종목 인식, 감성 분석, 열기 지수, 커뮤니티별 수익률 비교 | `codex/signal-community-alpha-agent` |
| `market-simulation-engine` | 시세/호가, Redis quote cache, 모의투자, AI 에이전트 | `codex/market-quote-cache` |
| `product-ops-experience` | 대시보드, 관리자 경험, 문서, Notion, PR/CI, 배포 정책 | `codex/product-dashboard-shell` |

## 충돌 방지 규칙

- 한 PR은 한 트랙만 소유합니다.
- 다른 트랙의 파일을 바꿔야 하면 먼저 계약 문서나 이슈를 남깁니다.
- 공통 schema, OpenAPI, DB migration은 충돌이 잦으므로 작은 계약 PR로 먼저 분리합니다.
- `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`는 작업 상태를 바꿀 때만 갱신합니다.
- 파일 소유권이 애매하면 구현보다 먼저 문서 PR로 경계를 정합니다.

## PR 라벨

기존 `type:*`, `area:*`, `size:*` 라벨에 더해 `stream:*` 라벨을 반드시 붙입니다.

| 트랙 | GitHub 라벨 | 브랜치 prefix | Notion 트랙 |
| --- | --- | --- | --- |
| `community-data-platform` | `stream:data` | `codex/data-*` | `community-data-platform` |
| `signal-intelligence` | `stream:signal` | `codex/signal-*` | `signal-intelligence` |
| `market-simulation-engine` | `stream:market` | `codex/market-*` | `market-simulation-engine` |
| `product-ops-experience` | `stream:product` | `codex/product-*` | `product-ops-experience` |

예시:

```text
트랙: community-data-platform
변경 범위: worker crawler scheduler, docs/workstreams/community-data-platform
```

## Notion 구분

작업 로그 DB와 다음 작업 DB에는 `트랙` select 속성을 둡니다. 새 작업 카드는 담당 트랙을 반드시 채웁니다.

기획/운영 기준 정리처럼 여러 트랙을 조율하는 작업은 기본적으로 `product-ops-experience`로 둡니다. 단, 실제 구현은 각 기능 트랙으로 분리합니다.
