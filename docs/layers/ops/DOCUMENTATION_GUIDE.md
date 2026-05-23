# 문서 구조 가이드

문서는 두 역할을 분리합니다.

1. 새 채팅이 빠르게 시작하기 위한 짧은 운영 문서
2. 나중에 원인과 맥락을 찾기 위한 긴 기록 문서

`AGENTS.md`, `docs/current/HANDOFF.md`, `docs/current/TASKS.md`는 현재 작업자가 방향을 잡는 문서입니다. 오래된 상세 이력은 작업 단위 문서, PR, Notion 기록으로 넘깁니다.

## AGENTS.md와 README.md 기준

`AGENTS.md`는 자동으로 적용되어야 하는 작업 규칙, 금지 사항, 읽기 순서를 담는 파일입니다. `README.md`는 사람이 보거나 에이전트가 필요할 때 여는 도메인/layer 색인입니다.

모든 폴더의 README를 AGENTS로 바꾸지 않습니다. 자동 적용이 꼭 필요한 코드 실행 경계나 하위 워크스페이스에만 짧은 `AGENTS.md`를 두고, 일반 도메인 설명과 문서 색인은 `README.md`를 유지합니다.

## 읽기 우선순위

새 채팅은 전문 출력이 아니라 필요한 섹션 확인을 기본으로 합니다.

| 문서 | 읽는 경우 |
| --- | --- |
| `AGENTS.md` | 공통 규칙, 금지 사항, PR 게이트가 필요할 때 |
| `docs/current/HANDOFF.md` | 현재 상태, 최근 결정, 다음 후보 확인 |
| `docs/layers/ops/CHAT_START_GUIDE.md` | 빈 채팅, 짧은 트랙 지시, 시작 응답 틀 확인 |
| `docs/layers/ops/TRACKS.md` | 트랙 경계가 헷갈릴 때 |
| 담당 도메인/layer README | 새 도메인 작업을 시작할 때 |
| `docs/product/FINAL_PRODUCT_PLAN.md` | 제품 방향이나 최종 범위가 필요할 때 |
| `docs/product/PROJECT_BRIEF.md` | 현재 MVP 범위가 필요할 때 |
| `docs/layers/ops/GIT_CONVENTION.md` | PR, 커밋, 라벨 작업 직전 |
| `docs/layers/ops/LABEL_GUIDE.md` | GitHub/Notion 라벨 의미가 헷갈릴 때 |
| `docs/layers/ops/DOMAIN_PACKAGE_GUIDE.md` | 트랙과 코드 패키지 경계가 헷갈릴 때 |
| `docs/domains/community/REACTION_GUIDE.md` | 커뮤니티 반응 용어와 수집 전략 확인 |
| `docs/domains/agent/STOCK_DETAIL_HEADLINE.md` | 종목 상세 상단의 시황/기술지표/재무 기반 팩트폭격 한줄평 기준 확인 |
| `docs/layers/ui/screens/` | 화면별 기획, route, child screen, API 후보 확인 |
| `docs/governance/LEGAL_RISK_CASES.md` | 크롤링/공개 배포 리스크 확인 |
| `docs/governance/TECHNICAL_RISK_REGISTER.md` | 최종 기획상 생길 수 있는 기술/제품/운영 이슈 확인 |
| `docs/layers/ops/ENGINEERING_EVIDENCE_GUIDE.md` | 문제 해결, 개선, 기술 결정 기록 기준 확인 |
| `docs/governance/TROUBLESHOOTING_GUIDE.md` | 버그, 장애, 반복 이슈 기록 |

## 검색해서 보는 기록

아래 위치는 매번 읽지 않습니다. 필요한 키워드로 `rg` 검색합니다.

| 위치 | 역할 |
| --- | --- |
| `docs/archive/work-units/items/` | PR 단위 작업 이력 |
| `docs/archive/superpowers/items/README.md` | 큰 spec/plan 기록을 읽기 전 안내 |
| `docs/archive/superpowers/items/specs/`, `docs/archive/superpowers/items/plans/` | 승인된 설계와 상세 실행 계획 |
| `docs/archive/front/wireframe/` | 과거 front 와이어프레임 세부 로그 |
| Notion 작업일지 | 사람이 보는 PR 카드 로그 |
| Notion 개발자 기술 경험 DB | 제품 개발/운영 문제, 개선 근거, 기술 결정 |
| Notion 에이전트 운영 로그 DB | Codex, Notion, GitHub PR, 문서 운영 사고 |

## 정본과 인덱스 원칙

정본은 현재 판단의 기준입니다. 채팅, 메모리, 과거 archive는 정본을 찾기 위한 색인일 뿐입니다.

| 대상 | 정본 |
| --- | --- |
| 제품 범위와 결정 | `docs/product/FINAL_PRODUCT_PLAN.md`, `docs/product/PRODUCT_DECISION_NOTES.md` |
| 현재 작업 상태 | `docs/current/HANDOFF.md`, `docs/current/TASKS.md` |
| 화면 구조와 API 후보 | `docs/layers/ui/screens/`, 현재 `front/` 코드 |
| 시세/커뮤니티/지표/에이전트/원장 데이터 | 해당 도메인 README, API contract, DB entity/snapshot |
| 장애와 기술 결정 근거 | `docs/governance/TECHNICAL_RISK_REGISTER.md`, Notion 개발자 기술 경험 DB |

새 인덱스 문서는 같은 lookup을 여러 트랙이 반복할 때만 만듭니다. 인덱스는 상세 설명을 복제하지 않고 정본 위치, ID/key, 상태, source/asOf만 짧게 가리킵니다.

## 채팅 안정성 규칙

- 이미 주입된 `AGENTS.md`나 긴 문서는 터미널로 다시 전문 출력하지 않습니다.
- 트랙이 명확하면 관련 도메인/layer README와 `docs/current/HANDOFF.md`의 관련 줄을 우선합니다.
- `docs/current/HANDOFF.md` 전문 읽기는 기본값이 아닙니다. 현재 상태, 다음 후보, 해당 트랙 관련 줄만 확인합니다.
- 메모리와 과거 대화 요약은 색인으로만 사용합니다. 현재 결정은 repo 문서, 현재 코드, 필요한 경우 공식 문서로 재확인합니다.
- 객관성은 확인된 사실, 추론, 결정, 남은 불확실성을 구분해 보고하는 방식으로 유지합니다. 근거 없는 낙관이나 과장된 포트폴리오 표현은 피합니다.
- 스킬 문서는 적용할 스킬이 정해진 뒤 설명, 체크리스트, 이번 절차만 읽습니다.
- 큰 스킬 문서는 전문 출력하지 않습니다. Browser/Figma/Stitch/gstack/Superpowers는 `-TotalCount 120` 안팎이나 관련 섹션 검색으로 시작하고, 같은 세션에서 반복해서 읽지 않습니다.
- `docs/archive/superpowers/items/specs/`, `docs/archive/superpowers/items/plans/`, `docs/archive/front/wireframe/`는 현재 작업 시작 문서가 아니라 archive입니다. 현재 handoff가 부족할 때만 `rg -n -m 20 <키워드> <파일>`처럼 제한해 확인합니다.
- 세션 로그는 파일 하나와 키워드 하나로 좁혀 검색합니다. `C:\Users\JYH\.codex` 전체에 넓은 `rg`를 돌리지 않습니다.
- 로그/JSONL은 본문 출력 대신 parser로 필요한 필드만 집계합니다. 예: `token_count`의 `last_token_usage.input_tokens` 최대/평균.
- Notion은 필요한 page/database 하나씩 fetch합니다. 루트, Archive, 전체 DB를 연달아 전문 fetch하지 않습니다.
- front/gstack은 화면 변경, 라우팅, 콘솔 오류, 반응형처럼 실제 확인 가치가 있을 때 사용합니다. 결과는 요약합니다.
- 토큰 최적화는 필수 행동을 없애는 근거가 아닙니다. PR, 테스트, 라벨, Notion 기록 필요성 판단, gstack 검증 필요성 판단은 유지합니다.

## 최적화 해결 원칙

토큰 문제는 필수 작업을 줄여 해결하지 않습니다. 같은 일을 하되 큰 입력과 큰 출력을 막습니다.

1. 시작 입력을 줄입니다. 트랙이 명확하면 `AGENTS.md`, `docs/current/HANDOFF.md`, 관련 도메인/layer README의 관련 줄만 봅니다.
2. 스킬 입력을 줄입니다. 큰 스킬 파일은 필요한 절차만 읽고, Browser/gstack 검증은 구현 후 한 번에 모아 실행합니다.
3. 도구 출력을 줄입니다. `Get-Content -TotalCount`, `Select-Object -First/-Skip`, `rg -n -m 20 <키워드> <좁은 경로>`처럼 출력량을 먼저 제한합니다.
4. 로그는 집계합니다. 세션 JSONL, 브라우저 콘솔, DOM, Notion 페이지 전문은 대화에 붙이지 않고 오류명, 파일명, 수치만 남깁니다.
5. 검증은 유지합니다. 테스트, `git diff --check`, PR 라벨/본문 확인, 필요한 브라우저 QA는 생략하지 않고 결과만 짧게 보고합니다.
6. 문서를 늘리지 않습니다. 새 규칙은 기존 시작 문서에 짧게 합치고, 세부 이력은 archive나 PR/Notion 기록으로 보냅니다.
7. 수치로 확인합니다. 채팅 오류가 났거나 최적화 PR을 낸 뒤에는 이전/현재 세션의 `last input` 최대/평균을 비교합니다.

## 컨텍스트 예산 점검

아래 상황에서는 문서/도구 출력 예산을 다시 봅니다.

- `AGENTS.md`, `docs/current/HANDOFF.md`, `docs/current/TASKS.md`, `docs/layers/ops/`, `docs/domains/`, `docs/layers/ui/`를 바꾸는 PR
- 채팅이 일반 오류로 끊겼거나 한 작업에서 로그/Notion/gstack 출력이 크게 늘어난 경우
- ops 문서 PR 3개가 쌓였거나, 일주일 이상 문서 정리를 하지 않은 경우
- 열린 브랜치/worktree가 5개 이상이거나, close-candidate 브랜치가 생긴 경우

목표 예산:

- 트랙이 명확한 새 채팅의 시작 확인은 3k-5k 토큰 안에 끝냅니다.
- 항상 후보가 되는 시작 문서는 파일당 1.5k 토큰 아래를 목표로 합니다.
- `docs/current/HANDOFF.md`는 1.2k 토큰 안팎을 유지합니다.
- `docs/current/TASKS.md`는 미완료 체크박스를 보존하고, 완료 상세 이력만 요약합니다.
- front Screen Brief는 일반 화면 150줄 이하, 복잡한 부모 화면 220줄 이하를 목표로 하고 변경 로그는 최근 5개만 유지합니다.

초과하면 전체 삭제가 아니라 `rg` 검색, 섹션 읽기, 완료 이력 요약, 출력 요약으로 줄입니다.

## 상황별 읽기 게이트

| 대상 | 방식 |
| --- | --- |
| 시작 문서 | `rg` 또는 관련 섹션 |
| 담당 도메인/layer README | 작업 범위와 파일 소유권 섹션 |
| PR/라벨 문서 | PR 직전 필요한 섹션 |
| 스킬 문서 | 실제 적용 절차만 |
| `docs/archive/superpowers/items/` archive | 현재 handoff가 부족할 때만 파일 1개, 키워드 1개 |
| front archive | 현재 front handoff가 부족할 때만 파일 1개, 키워드 1개 |
| gstack/browse 출력 | 결과 요약, 핵심 오류 |
| 세션/로그 JSONL | 파일명, 날짜, 키워드 제한 |
| Notion page/database | 대상 하나씩, 바꿀 섹션 중심 |

## 업데이트 규칙

작업이 끝났다고 모든 문서를 고치지 않습니다.

| 상황 | 갱신할 곳 |
| --- | --- |
| 제품 방향이나 범위 변경 | `docs/product/FINAL_PRODUCT_PLAN.md`, `docs/current/HANDOFF.md` |
| front 화면 구조, route, child detail, 화면별 API 후보 변경 | `docs/layers/ui/screens/` |
| 커뮤니티 분석 용어/수집 전략 변경 | `docs/domains/community/REACTION_GUIDE.md`, `docs/product/FINAL_PRODUCT_PLAN.md`, `docs/product/PROJECT_BRIEF.md` |
| 최종 기획상 새 기술/제품/운영 리스크 발견 | `docs/governance/TECHNICAL_RISK_REGISTER.md`, 필요 시 관련 도메인 README |
| 작업 방식이나 라벨 기준 변경 | `docs/layers/ops/WORKFLOW.md`, `docs/layers/ops/GIT_CONVENTION.md`, `docs/layers/ops/LABEL_GUIDE.md` |
| 브랜치 생명주기나 worktree 정리 기준 변경 | `docs/layers/ops/GIT_CONVENTION.md`, `docs/layers/ops/WORKFLOW.md`, `docs/current/HANDOFF.md` |
| 다음 작업 후보 변경 | `docs/current/TASKS.md`, `docs/current/HANDOFF.md` |
| 새 트랙 경계 | `docs/layers/ops/TRACKS.md` |
| 제품 개발/운영 문제, 개선, 기술 결정 | Notion 개발자 기술 경험 DB, 필요 시 관련 가이드 |
| Codex/Notion/PR/문서 운영 사고 | Notion 에이전트 운영 로그 DB |
| PR 종료 | Notion 작업일지, 필요 시 `docs/archive/work-units/items/` |
| 채팅 시작 방식 변경 | `docs/layers/ops/CHAT_START_GUIDE.md`, `docs/layers/ops/WORKFLOW.md`, `docs/current/HANDOFF.md` |

front 화면 작업은 사용자가 별도로 기록을 지시하지 않아도 Screen Brief를 갱신합니다. 다만 Screen Brief는 현재 기준 문서이므로 긴 작업 과정, 폐기된 시안, 전체 피드백 전문을 누적하지 않고 최신 결론과 열린 질문만 남깁니다.
