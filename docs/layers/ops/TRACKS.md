# Legacy track alias

`track`은 과거 PR/라벨/Notion에서 쓰던 작업 구분입니다. 현재 작업 판단의 1차 기준은 `docs/layers/ops/WORK_AREAS.md`의 domain/layer 작업 영역입니다.

이 파일은 오래된 링크와 기존 라벨을 해석하기 위한 호환 문서입니다. 새 문서와 새 작업 설명은 `작업 영역`을 기본 표현으로 씁니다.

| legacy track | primary work area | 비고 |
| --- | --- | --- |
| `crawl` | `community` | 커뮤니티 수집, source policy, 원문 제한 저장 |
| `data` | `realestate`, `indicator`, 필요 시 `community` | 지역/단지 식별과 지표화를 나눠 봅니다. |
| `market` | `realestate` 또는 legacy `market` | 부동산 market fact는 realestate가 소유합니다. |
| `trade` | legacy `simulation` | 부동산 1차 범위에서는 거래/원장을 활성 작업으로 보지 않습니다. |
| `agent` | `agent` | 지역/단지 평가와 근거 로그 |
| `front` | `ui` | 화면, 디자인 시스템, fixture/API 후보 |
| `ops` | `ops` | 문서 구조, PR/라벨/Notion, 브랜치/worktree |

새 PR과 새 Notion 카드는 `track:<작업영역>` 값과 Notion `트랙=<작업영역>` 값을 씁니다. 이 파일의 legacy track 값은 과거 기록 해석용입니다.
