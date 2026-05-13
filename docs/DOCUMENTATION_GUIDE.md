# 문서 구조 가이드

이 프로젝트의 문서는 두 가지 목적을 분리합니다.

1. 새 채팅이 빠르게 시작하기 위한 짧은 운영 문서
2. 나중에 원인과 맥락을 찾기 위한 긴 기록 문서

문제가 생기는 지점은 1번 문서가 2번 역할까지 떠안는 순간입니다. `AGENTS.md`, `CURRENT_HANDOFF.md`, `TASKS.md`는 길게 쌓는 문서가 아니라 현재 작업자가 방향을 잡는 문서로 유지합니다.

## 읽기 우선순위

### 매번 읽는 문서

새 채팅이나 새 에이전트는 아래 문서만 먼저 읽습니다.

| 문서 | 역할 | 길이 원칙 |
| --- | --- | --- |
| `AGENTS.md` | 공통 작업 규칙과 금지 사항 | 짧게 유지 |
| `docs/CURRENT_HANDOFF.md` | 현재 상태, 최근 결정, 다음 후보 | 오래된 내용 제거 |
| `docs/workstreams/README.md` | 트랙 선택 기준 | 표 중심 |
| 담당 트랙 README | 맡은 트랙의 파일 소유권과 범위 | 트랙별로 유지 |

### 필요할 때 읽는 문서

아래 문서는 작업 성격에 맞을 때만 읽습니다.

| 문서 | 읽는 경우 |
| --- | --- |
| `docs/FINAL_PRODUCT_PLAN.md` | 제품 방향이나 최종 범위를 확인할 때 |
| `docs/PROJECT_BRIEF.md` | 현재 MVP 범위를 확인할 때 |
| `docs/GIT_CONVENTION.md` | PR/커밋/라벨 규칙을 확인할 때 |
| `docs/LABEL_GUIDE.md` | GitHub/Notion 라벨 의미가 헷갈릴 때 |
| `docs/LEGAL_RISK_CASES.md` | 크롤링/공개 배포 리스크를 다룰 때 |
| `docs/TROUBLESHOOTING_GUIDE.md` | 버그, 장애, 반복 이슈를 기록할 때 |

### 검색해서 보는 기록

아래는 매번 읽지 않습니다. 필요한 키워드로 `rg` 검색해서 찾습니다.

| 위치 | 역할 |
| --- | --- |
| `docs/work-units/` | PR 단위 작업 이력 |
| `docs/superpowers/specs/` | 승인된 설계 기록 |
| `docs/superpowers/plans/` | 상세 실행 계획 기록 |
| Notion 작업일지 | 사람이 보는 PR 카드 로그 |
| Notion 트러블슈팅 DB | 문제 원인과 재발 방지 기록 |

## 문서 길이 관리

- `CURRENT_HANDOFF.md`는 최신 결정과 다음 행동만 남깁니다.
- 오래된 완료 내역은 `TASKS.md`나 `docs/work-units/`로 넘기고, 인수인계 문서에 반복하지 않습니다.
- `TASKS.md`는 앞으로 할 일을 먼저 보여줍니다. 완료 목록이 길어지면 묶어서 요약합니다.
- `docs/work-units/`는 짧게 씁니다. 자세한 조사 과정은 트러블슈팅 DB나 별도 가이드에 둡니다.
- PR 본문은 사람이 리뷰하기 좋은 카드형으로 쓰고, 명령어 덩어리는 접힌 영역에 둡니다.

## 업데이트 규칙

작업이 끝났을 때 모든 문서를 고치지 않습니다. 아래 기준으로 필요한 문서만 갱신합니다.

| 상황 | 갱신할 곳 |
| --- | --- |
| 제품 방향이나 범위가 바뀜 | `FINAL_PRODUCT_PLAN.md`, `CURRENT_HANDOFF.md` |
| 작업 방식이나 라벨 기준이 바뀜 | `WORKFLOW.md`, `GIT_CONVENTION.md`, `LABEL_GUIDE.md` |
| 다음 작업 후보가 바뀜 | `TASKS.md`, `CURRENT_HANDOFF.md` |
| 새 트랙 경계가 생김 | `docs/workstreams/` |
| 문제를 조사하거나 해결함 | Notion 트러블슈팅 DB, 필요하면 `TROUBLESHOOTING_GUIDE.md` |
| PR 하나가 끝남 | Notion 작업일지, 필요한 경우 `docs/work-units/` |

## 에이전트 메모

긴 문서를 많이 읽는 것은 성실함이 아니라 비용일 수 있습니다. 먼저 짧은 문서로 방향을 잡고, 필요한 정보만 검색해서 읽습니다. 특히 `docs/work-units/`와 `docs/superpowers/`는 전체를 훑지 않습니다.
