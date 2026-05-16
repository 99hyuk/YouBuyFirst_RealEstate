# 병렬 작업 트랙 안내

너나사 (YouBuyFirst)는 여러 채팅과 에이전트가 동시에 일할 수 있도록 일곱 작업 트랙으로 나눕니다. 트랙은 PR/Notion/브랜치의 작업 구분이고, 코드 패키지 이름과 항상 같지는 않습니다.

## 시작 원칙

- `front 작업해`, `crawl 쪽 맡아줘`, `ops로 Notion 정리해`처럼 짧게 시작해도 됩니다.
- 범위 없이 `뭐 해야 해?`라고 물으면 바로 구현하지 않고 트랙 설명과 다음 작업 후보를 보여줍니다.
- 각 에이전트는 `AGENTS.md`, `docs/CURRENT_HANDOFF.md`, `docs/DOCUMENTATION_GUIDE.md`, 담당 트랙 README의 필요한 섹션만 확인합니다.
- 이미 대화에 주입된 긴 문서는 다시 전문 출력하지 않습니다.

```text
너는 너나사 (YouBuyFirst)의 <트랙명> 담당 에이전트야.
필요한 섹션만 확인하고, 이 채팅에서는 <작업 범위>만 다뤄줘.
작업 하나는 브랜치 하나와 PR 하나로 만들고, PR 설명과 작업 기록은 한국어로 작성해줘.
```

## 트랙 목록

| 트랙 | 역할 | 브랜치 예시 |
| --- | --- | --- |
| `crawl` | 커뮤니티 글 수집, 소스 어댑터, 종목별 게시판 타깃, 수집 정책 | `codex/crawl-naver-targets` |
| `data` | 종목 인식, 별칭 매칭, 반응 방향, 열기 지수, 30분 집계 | `codex/data-alias-matcher` |
| `market` | 실시간/지연 시세, 호가, quote cache, WebSocket | `codex/market-quote-cache` |
| `trade` | 가상 계좌, 주문, 체결, 포트폴리오, 수익률 | `codex/trade-order-domain` |
| `agent` | AI 매매 판단, 커뮤니티별 성과 비교, 페르소나, 결정 로그 | `codex/agent-contrarian-log` |
| `front` | 대시보드, 차트, 관리자 화면, mock/API 연동 | `codex/front-dashboard-shell` |
| `ops` | 기획, 문서, Notion, PR/CI, 배포 정책, 트랙 조율 | `codex/ops-track-names` |

핵심 경계:

- `crawl`은 외부 커뮤니티 입력 파이프라인입니다.
- `data`는 글을 분석 데이터로 바꿉니다. 매수/매도 판단은 `agent`입니다.
- `market`은 시세/호가만 소유합니다. 주문/체결은 `trade`입니다.
- `front`는 fixture/mock 기반 화면 골격을 일찍 만들고 API 계약이 생길 때 연결합니다.
- `ops`는 문서, 자동화, CI, Notion, 배포 정책, 작업 조율에 한정합니다.

## 패키지 기준

| 트랙 | 주 소유 영역 |
| --- | --- |
| `crawl` | `crawlers`, `crawl`, `ingestion` 일부 |
| `data` | `stock`, `analysis`, `indicator` |
| `market` | `market` |
| `trade` | `trade` |
| `agent` | `agent` |
| `front` | frontend app |
| `ops` | `docs`, `.github`, Notion, CI/운영 문서 |

상세 기준은 `docs/DOMAIN_PACKAGE_GUIDE.md`를 봅니다.

## 충돌 방지

- 한 PR은 한 트랙만 소유합니다.
- 다른 트랙 파일을 바꿔야 하면 먼저 계약 문서나 이슈를 남깁니다.
- 공통 schema, OpenAPI, DB migration은 작은 계약 PR로 먼저 분리합니다.
- `docs/CURRENT_HANDOFF.md`와 `docs/TASKS.md`는 작업 상태를 바꿀 때만 갱신합니다.
- 파일 소유권이 애매하면 구현보다 먼저 문서 PR로 경계를 정합니다.

## 브랜치 전략

- 기본은 `codex/<prefix>-<task>` 브랜치에서 작은 PR을 만들어 `main`으로 보냅니다.
- 공통 계약 PR은 가능한 한 먼저 `main`에 넣습니다.
- 기능이 아직 드러나면 안 되면 feature flag, mock mode, disabled default로 숨깁니다.
- 결합이 강한 작업만 짧은 수명의 `track/*` 통합 브랜치를 씁니다.
- `track/*`는 2-4개 PR, 3-5일 안에 `main` 통합을 목표로 합니다.
- 통합 전에는 해당 트랙의 테스트와 Docker/수동 smoke test를 실행합니다.

## 라벨과 Notion

PR에는 `track:*`, `type:*`, `size:*` 라벨을 붙입니다. 실제 파일이나 리뷰 경로가 필요할 때만 `part:*`를 추가합니다.

| 트랙 | 라벨 | 브랜치 prefix | Notion 트랙 |
| --- | --- | --- | --- |
| `crawl` | `track:crawl` | `codex/crawl-*` | `crawl` |
| `data` | `track:data` | `codex/data-*` | `data` |
| `market` | `track:market` | `codex/market-*` | `market` |
| `trade` | `track:trade` | `codex/trade-*` | `trade` |
| `agent` | `track:agent` | `codex/agent-*` | `agent` |
| `front` | `track:front` | `codex/front-*` | `front` |
| `ops` | `track:ops` | `codex/ops-*` | `ops` |

Notion 작업 카드는 PR 본문과 같은 카드형 흐름을 따릅니다. 각 트랙 에이전트는 자기 PR과 작업 로그를 갱신하고, `ops`는 루트 대시보드와 트랙별 진행판 정합성을 점검합니다.
