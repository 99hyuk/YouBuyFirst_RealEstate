# 작업 영역 안내

이 문서는 기존 track 중심 작업을 domain/layer 중심 작업 영역으로 전환하기 위한 기준입니다. 작업 영역은 새 채팅 시작, 문서 정본 위치, PR 범위 판단의 1차 단위입니다.

GitHub 라벨 family는 기존 형식인 `track:*`를 유지하되 값은 작업 영역 이름을 씁니다. Notion도 기존 `트랙` 속성 구조를 유지하고 값만 작업 영역 기준으로 분류합니다. 기존 `crawl`, `data`, `trade`, `front` 값은 과거 기록 해석용 alias입니다.

## 기본 원칙

- 새 작업은 domain 또는 layer 작업 영역으로 시작합니다.
- 한 PR은 하나의 primary work area를 가집니다.
- 여러 영역을 건드려야 하면 계약 문서, 작은 선행 PR, 사용자 확인 중 하나를 먼저 둡니다.
- 기존 `crawl`, `data`, `trade`, `front` 같은 track 이름은 아래 표의 alias로 해석합니다.
- PR 제목은 기존 `[값][타입]` 형식을 유지하되 값에는 작업 영역 이름을 씁니다.

## 작업 영역

| 작업 영역 | 종류 | 담당 | legacy alias | 먼저 볼 곳 | 브랜치 예시 |
| --- | --- | --- | --- | --- | --- |
| `community` | domain | 커뮤니티 수집, 원문 제한 저장, source policy, 반응 후보 | `crawl` | `docs/domains/community/AGENTS.md` | `codex/community-source-registry` |
| `stock` | domain | 종목 master, symbol, alias, 종목 식별 | `data` 일부 | `docs/domains/stock/AGENTS.md` | `codex/stock-alias-match` |
| `indicator` | domain | 반응 방향 집계, 열기 지수, 개미 심리 지수, snapshot | `data` 일부 | `docs/domains/indicator/AGENTS.md` | `codex/indicator-retail-index` |
| `market` | domain | quote, chart candle, provider, stale/asOf, 국내 수급 | `market` | `docs/domains/market/AGENTS.md` | `codex/market-chart-cache` |
| `simulation` | domain | 가상 계좌, 주문, 체결, 원장, 포지션, 수익률 | `trade` | `docs/domains/simulation/AGENTS.md` | `codex/simulation-ledger` |
| `agent` | domain | AI 판단, paper trading decision, 커뮤니티별 성과 비교, 헤드라인 | `agent` | `docs/domains/agent/AGENTS.md` | `codex/agent-decision-key` |
| `ui` | layer | front 화면, 디자인 시스템, fixture, API 후보, Screen Brief | `front` | `docs/layers/ui/AGENTS.md` | `codex/ui-dashboard-shell` |
| `ops` | layer | 문서 구조, Git/PR, Notion, branch/worktree, 컨텍스트 예산 | `ops` | `docs/layers/ops/AGENTS.md` | `codex/ops-doc-rules` |

## alias 해석

| legacy track | primary work area | 메모 |
| --- | --- | --- |
| `crawl` | `community` | 수집과 source registry는 community 영역입니다. |
| `data` | `stock`, `indicator`, 필요 시 `community` | `data`는 너무 넓습니다. 종목 식별은 stock, 지표화는 indicator로 나눕니다. |
| `market` | `market` | 이름은 유지하지만 domain 작업 영역입니다. |
| `trade` | `simulation` | 실제 투자/결제가 아니라 가상 원장과 체결 domain입니다. |
| `agent` | `agent` | 판단 로그와 paper trading 결정 영역입니다. |
| `front` | `ui` | 화면 구현과 디자인 시스템은 ui layer입니다. |
| `ops` | `ops` | 운영/문서/PR layer입니다. |

## 전환 규칙

- 새 문서에는 `작업 영역`을 기본 표현으로 씁니다.
- `track:*` 라벨 prefix와 Notion `트랙` 속성명은 유지합니다. 값은 `community`, `stock`, `indicator`, `market`, `simulation`, `agent`, `ui`, `ops`를 씁니다.
- 과거 `track:crawl`, `track:data`, `track:trade`, `track:front`는 닫힌 PR이나 과거 Notion 카드 해석용으로만 봅니다.
- 새 영역이 필요해 보이면 먼저 이 문서를 바꾸기보다 기존 영역에 둘 수 있는지 확인합니다. 정말 필요할 때만 ops 문서 PR로 추가합니다.
