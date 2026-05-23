# Legacy track alias

`track`은 과거 PR/라벨/Notion에서 쓰던 작업 구분입니다. 현재 작업 판단의 1차 기준은 `docs/layers/ops/WORK_AREAS.md`의 domain/layer 작업 영역입니다.

이 파일은 오래된 링크와 기존 라벨을 해석하기 위한 호환 문서입니다. 새 문서와 새 작업 설명은 `작업 영역`을 기본 표현으로 씁니다.

| legacy track | primary work area | 비고 |
| --- | --- | --- |
| `crawl` | `community` | 커뮤니티 수집, source policy, 원문 제한 저장 |
| `data` | `stock`, `indicator`, 필요 시 `community` | 종목 식별과 지표화를 나눠 봅니다. |
| `market` | `market` | 시세, 차트, provider, stale/asOf |
| `trade` | `simulation` | 가상 계좌, 체결, 원장, 포지션 |
| `agent` | `agent` | AI 판단, paper trading decision, 헤드라인 |
| `front` | `ui` | 화면, 디자인 시스템, fixture/API 후보 |
| `ops` | `ops` | 문서 구조, PR/라벨/Notion, 브랜치/worktree |

전환이 끝나기 전까지 `track:*` 라벨과 Notion `트랙` 값은 남을 수 있습니다. 새 PR/문서에는 primary work area를 병기합니다.
