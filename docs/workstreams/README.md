# 병렬 작업 트랙 안내

너나사 (YouBuyFirst)는 여러 채팅과 에이전트가 동시에 일할 수 있도록 일곱 개의 짧은 작업 트랙으로 나눕니다. 실제 MSA로 바로 분리하지는 않지만, 문서, 브랜치, PR, 파일 소유권은 서비스 경계처럼 명확히 나눕니다.

## 공통 시작 절차

다른 채팅에서 작업을 시작할 때 긴 문장을 매번 붙여 넣을 필요는 없습니다. `front 작업해`, `crawl 쪽 맡아줘`, `ops로 Notion 정리해`처럼 짧게 말하면 에이전트가 역할 프롬프트를 자동 확장합니다.

작업 범위 없이 `뭐 해야 해?`라고 물으면 에이전트는 바로 구현하지 않고 트랙 설명과 다음 작업 후보를 보여준 뒤 사용자가 트랙을 고르게 도와야 합니다.

필요하면 아래 문장을 그대로 붙여 넣어도 됩니다.

```text
너는 너나사 (YouBuyFirst)의 <트랙명> 담당 에이전트야.
먼저 AGENTS.md, docs/CURRENT_HANDOFF.md, docs/DOCUMENTATION_GUIDE.md를 읽고,
docs/workstreams/<트랙명>/README.md도 읽어.
이 채팅에서는 <작업 범위>만 다루고, 다른 트랙 파일은 건드리지 마.
작업 하나는 브랜치 하나와 PR 하나로 만들어줘.
PR 설명과 작업 기록은 한국어로 작성해줘.
```

새 채팅은 이전 채팅의 기억을 자동으로 이어받지 못할 수 있습니다. 그래서 담당 에이전트가 계속 참고해야 할 기억은 채팅 안의 약속이 아니라 저장소 문서에 둡니다. 각 에이전트는 시작할 때 `AGENTS.md`, `docs/CURRENT_HANDOFF.md`, 이 문서, 담당 트랙 README를 읽고 자기 역할을 복원합니다.

상세한 채팅 시작 규칙과 응답 틀은 `docs/CHAT_START_GUIDE.md`를 기준으로 봅니다.

## 트랙 목록

| 트랙 | 한국어 의미 | 역할 | 브랜치 예시 |
| --- | --- | --- | --- |
| `crawl` | 수집 | 커뮤니티 글 수집, 소스 어댑터, 종목별 게시판 타깃, 수집 정책 | `codex/crawl-naver-targets` |
| `data` | 분석 데이터 | 종목 인식, 별칭 매칭, 반응 방향 분류, 열기 지수, 30분 집계 | `codex/data-alias-matcher` |
| `market` | 시세 | 실시간/지연 시세, 호가, quote cache, WebSocket | `codex/market-quote-cache` |
| `trade` | 모의투자 | 가상 계좌, 주문, 체결, 포트폴리오, 수익률 | `codex/trade-order-domain` |
| `agent` | 전략 에이전트 | AI 매매 판단, 커뮤니티별 성과 비교, 페르소나, 결정 로그 | `codex/agent-contrarian-log` |
| `front` | 화면 | 대시보드, 차트, 관리자 화면, mock/API 연동 | `codex/front-dashboard-shell` |
| `ops` | 운영/조율 | 기획, 문서, Notion, PR/CI, 배포 정책, 트랙 조율 | `codex/ops-track-names` |

`crawl`은 외부 커뮤니티에서 제한 원문과 메타데이터를 가져오는 입력 파이프라인입니다.

`data`는 `crawl`이 넘긴 글을 투자 신호로 쓸 수 있는 분석 데이터로 바꿉니다. 종목 인식과 반응 방향 분류, 30분 집계는 여기까지입니다. 매수/매도 판단은 `agent`가 맡습니다.

`market`은 시세/호가 데이터만 소유합니다. 모의 계좌, 주문, 체결은 `trade`가 맡습니다.

`agent`는 `data`, `market`, `trade`의 상태를 읽어 전략적 판단을 만들지만, 크롤링/시세 수집/체결 로직을 직접 소유하지 않습니다.

`front`는 별도 구현 트랙입니다. 프론트는 완전 후반에 몰아서 하지 않고, fixture/mock 기반 화면 골격을 일찍 만들고 API 계약이 생길 때마다 연결합니다.

`ops`는 구현이 전혀 없는 트랙이 아닙니다. 다만 이 트랙의 구현은 문서, 자동화, CI, Notion, 배포 정책, 작업 조율에 한정합니다.

## 트랙과 코드 패키지

트랙 이름과 코드 패키지 이름은 다릅니다. 트랙은 PR/Notion/브랜치의 작업 구분이고, 패키지는 제품 도메인 구분입니다.

패키지는 사용자가 이해하기 쉬운 도메인 이름을 씁니다.

| 트랙 | 주 소유 도메인 패키지 |
| --- | --- |
| `crawl` | `crawlers`, `crawl`, `ingestion` 일부 |
| `data` | `stock`, `analysis`, `indicator` |
| `market` | `market` |
| `trade` | `trade` |
| `agent` | `agent` |
| `front` | frontend app |
| `ops` | `docs`, `.github`, Notion, CI/운영 문서 |

상세 기준은 `docs/DOMAIN_PACKAGE_GUIDE.md`를 봅니다.

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

- 예: `track/front-dashboard`, `track/market-quotes`
- 하위 작업은 `codex/<prefix>-<task>` 브랜치에서 만들고, PR base를 해당 `track/*` 브랜치로 둡니다.
- `track/*` 브랜치는 2-4개 PR, 3-5일 안에 `main`으로 통합하는 것을 목표로 합니다.
- `track/*`가 길어지면 통합 리스크가 뒤로 밀리므로 쪼개거나 계약 PR을 먼저 `main`에 넣습니다.
- 통합 전에는 해당 트랙의 테스트와 Docker/수동 smoke test를 실행합니다.

## PR 라벨

PR에는 작업 트랙 `track:*`, 작업 타입 `type:*`, 크기 `size:*` 라벨을 반드시 붙입니다. 변경 파트 `part:*`는 실제 파일이나 리뷰 경로를 드러낼 때만 붙이는 보조 라벨입니다.

라벨과 Notion 태그의 상세 의미는 `docs/LABEL_GUIDE.md`를 기준으로 봅니다.

| 트랙 | GitHub 라벨 | 브랜치 prefix | Notion 트랙 |
| --- | --- | --- | --- |
| `crawl` | `track:crawl` | `codex/crawl-*` | `crawl` |
| `data` | `track:data` | `codex/data-*` | `data` |
| `market` | `track:market` | `codex/market-*` | `market` |
| `trade` | `track:trade` | `codex/trade-*` | `trade` |
| `agent` | `track:agent` | `codex/agent-*` | `agent` |
| `front` | `track:front` | `codex/front-*` | `front` |
| `ops` | `track:ops` | `codex/ops-*` | `ops` |

예시:

```text
트랙: crawl
변경 범위: pipeline crawler scheduler, docs/workstreams/crawl
```

## Notion 구분

작업 로그 DB와 다음 작업 DB에는 `트랙` select 속성을 둡니다. 새 작업 카드는 담당 트랙을 반드시 채웁니다.

기획, 운영 기준 정리, 다른 트랙 조율 작업은 기본적으로 `ops`로 둡니다. 실제 기능 구현은 각 기능 트랙으로 분리합니다.

Notion 작업 카드는 PR 본문과 같은 카드형 흐름을 따릅니다. 트랙은 카드 제목, 아이콘, `트랙` 속성 중 적어도 두 곳에서 드러나야 합니다.

각 트랙 에이전트는 자기 PR과 작업 로그를 갱신합니다. `ops`는 루트 대시보드, 트랙별 진행판, 제품 기획과 작업 맥락을 주기적으로 점검하고 정리합니다.
