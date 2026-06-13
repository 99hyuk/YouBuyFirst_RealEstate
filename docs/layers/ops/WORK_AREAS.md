# 작업 영역 안내

이 문서는 부동산 전용 프로젝트의 domain/layer 작업 영역 기준입니다. 작업 영역은 새 채팅 시작, 문서 정본 위치, PR 범위 판단의 1차 단위입니다.

GitHub 라벨 family는 `track:*`를 유지하되 값은 작업 영역 이름을 씁니다. Notion도 `트랙` 속성 구조를 유지하고 값만 작업 영역 기준으로 분류합니다.

## 기본 원칙

- 새 작업은 domain 또는 layer 작업 영역으로 시작합니다.
- 한 PR은 하나의 primary work area를 가집니다.
- 여러 영역을 건드려야 하면 계약 문서, 작은 선행 PR, 사용자 확인 중 하나를 먼저 둡니다.
- PR 제목은 기존 `[값][타입]` 형식을 유지하되 값에는 작업 영역 이름을 씁니다.

## 작업 영역

| 작업 영역 | 종류 | 담당 | legacy alias | 먼저 볼 곳 | 브랜치 예시 |
| --- | --- | --- | --- | --- | --- |
| `realestate` | domain | 지역/단지, alias, 실거래/전세/매물, 정책/개발/교통 이벤트, 부동산 market fact | `data` 일부 | `docs/domains/realestate/AGENTS.md` | `codex/realestate-target-contract` |
| `community` | domain | 커뮤니티 수집, 원문 제한 저장, source policy, 반응 후보 | `crawl` | `docs/domains/community/AGENTS.md` | `codex/community-source-registry` |
| `indicator` | domain | 지역/단지 반응 방향 집계, 쟁점 비율, snapshot, 유사 상황 검색 후보 | `data` 일부 | `docs/domains/indicator/AGENTS.md` | `codex/indicator-reaction-snapshot` |
| `agent` | domain | 지역/단지 평가, 근거 로그, 유사 과거 비교 설명 | `agent` | `docs/domains/agent/AGENTS.md` | `codex/agent-evidence-log` |
| `ui` | layer | front 화면, 디자인 시스템, fixture, API 후보, Screen Brief | `front` | `docs/layers/ui/AGENTS.md` | `codex/ui-realestate-dashboard` |
| `ops` | layer | 문서 구조, Git/PR, Notion, branch/worktree, 컨텍스트 예산 | `ops` | `docs/layers/ops/AGENTS.md` | `codex/ops-doc-rules` |

## alias 해석

| legacy track | primary work area | 메모 |
| --- | --- | --- |
| `crawl` | `community` | 공개 수집과 source registry는 community 영역입니다. |
| `data` | `realestate`, `indicator`, 필요 시 `community` | `data`는 너무 넓습니다. 지역/단지 식별은 realestate, 지표화는 indicator로 나눕니다. |
| `market` | `realestate` | 부동산 market fact는 realestate가 소유합니다. |
| `agent` | `agent` | 평가 근거 로그와 유사 과거 비교 설명 영역입니다. |
| `front` | `ui` | 화면 구현과 디자인 시스템은 ui layer입니다. |
| `ops` | `ops` | 운영/문서/PR layer입니다. |

## 전환 규칙

- 새 문서에는 `작업 영역`을 기본 표현으로 씁니다.
- `track:*` 라벨 prefix와 Notion `트랙` 속성명은 유지합니다. 값은 `realestate`, `community`, `indicator`, `agent`, `ui`, `ops`를 우선 사용합니다.
- 새 영역이 필요해 보이면 먼저 이 문서를 바꾸기보다 기존 영역에 둘 수 있는지 확인합니다. 정말 필요할 때만 ops 문서 PR로 추가합니다.
