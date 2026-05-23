# 문서 구조 가이드

문서는 두 역할을 분리합니다.

1. 새 채팅이 빠르게 시작하기 위한 짧은 운영 문서
2. 나중에 원인과 맥락을 찾기 위한 긴 기록 문서

`AGENTS.md`, `docs/current/HANDOFF.md`, `docs/current/TASKS.md`는 현재 작업자가 방향을 잡는 문서입니다. 오래된 상세 이력은 작업 단위 문서, PR, Notion 기록으로 넘깁니다.

## 문서 구조 핵심 원칙

문서 구조 변경은 아래 원칙을 깨지 않는 선에서만 합니다.

1. 트리 구조를 유지합니다. 현재 상태는 `current`, 제품 방향은 `product`, 도메인 정본은 `domains`, 공통 구현/운영 레이어는 `layers`, 정책/리스크/장애는 `governance`, 과거 기록은 `archive`에 둡니다. 트러블슈팅 본문은 장애와 재발 방지 지식이므로 `governance`가 정본이고, Notion/PR에 어떻게 기록할지는 `layers/ops`가 소유합니다.
2. 도메인별 인접성을 유지합니다. 한 도메인의 판단 근거, contract, 정책은 가능한 한 `docs/domains/<domain>/` 안에 모읍니다. 여러 도메인에 걸치는 화면/운영 규칙은 `layers`, 제품 전체 결정은 `product`, 위험과 사고 기록은 `governance`로 보냅니다.
3. 대표파일을 먼저 봅니다. 루트 `AGENTS.md`는 전체 라우터이고, 도메인/layer `AGENTS.md`는 에이전트용 읽기 게이트입니다. `README.md`는 사람용 설명과 세부 문서 색인입니다.
4. 새 문서는 먼저 소유권을 정합니다. 어느 도메인/layer/product/governance/current/archive에 속하는지 애매하면 새 파일을 만들기 전에 `docs/layers/ops/WORK_AREAS.md`나 관련 도메인 `AGENTS.md`를 확인합니다.
5. 중복 설명을 만들지 않습니다. 같은 내용을 여러 곳에 길게 복제하지 말고, 대표파일에는 위치와 읽기 기준만 두고 상세는 정본 문서 하나에 둡니다.
6. 현재 문서와 archive를 섞지 않습니다. 현재 판단에 쓰는 내용은 정본 문서로 승격하고, 폐기된 시안, 긴 작업 로그, 과거 계획은 archive나 PR/Notion 기록에 둡니다.
7. 문서의 신호 밀도를 유지합니다. 에이전트가 실제 행동을 바꾸지 않는 추상적 다짐, 반복되는 설명, 의미가 흐린 문장은 핵심 판단을 희석시켜 작업 품질과 컨텍스트 효율을 떨어뜨립니다. 문장은 되도록 `판단`, `행동`, `위치`, `예외`, `검증 기준` 중 하나를 담아야 합니다.

## AGENTS.md와 README.md 기준

`AGENTS.md`는 자동으로 적용되어야 하는 작업 규칙, 금지 사항, 읽기 순서를 담는 파일입니다. `README.md`는 사람이 보거나 에이전트가 필요할 때 여는 도메인/layer 색인입니다.

도메인/layer 폴더는 `AGENTS.md`와 `README.md`를 함께 둘 수 있습니다. `AGENTS.md`는 "이 작업자가 무엇을 먼저 읽고 무엇을 건드리면 안 되는지"만 짧게 담고, `README.md`는 도메인 설명과 문서 색인을 유지합니다.

모든 하위 폴더에 AGENTS를 뿌리지는 않습니다. 자동 적용이 필요한 도메인/layer 경계에만 짧은 `AGENTS.md`를 두고, 세부 설명은 README와 개별 contract 문서에 둡니다.

## 읽기 우선순위

새 채팅은 전문 출력이 아니라 필요한 섹션 확인을 기본으로 합니다.

| 문서 | 읽는 경우 |
| --- | --- |
| `AGENTS.md` | 공통 규칙, 금지 사항, PR 게이트가 필요할 때 |
| `docs/current/HANDOFF.md` | 현재 상태, 최근 결정, 다음 후보 확인 |
| `docs/layers/ops/CHAT_START_GUIDE.md` | 빈 채팅, 짧은 작업 영역 지시, 시작 응답 틀 확인 |
| `docs/layers/ops/WORK_AREAS.md` | 작업 영역 경계나 legacy track alias가 헷갈릴 때 |
| 담당 도메인/layer `AGENTS.md` | 새 도메인/layer 작업을 시작할 때 |
| 담당 도메인/layer `README.md` | 도메인 설명, 세부 문서 색인, 다른 도메인 접점이 필요할 때 |
| `docs/product/FINAL_PRODUCT_PLAN.md` | 제품 방향이나 최종 범위가 필요할 때 |
| `docs/product/PROJECT_BRIEF.md` | 제품 요약과 현재 build strategy가 필요할 때 |
| `docs/layers/ops/GIT_CONVENTION.md` | PR, 커밋, 라벨 작업 직전 |
| `docs/layers/ops/LABEL_GUIDE.md` | GitHub/Notion 라벨 의미가 헷갈릴 때 |
| `docs/layers/ops/DOMAIN_PACKAGE_GUIDE.md` | 작업 영역과 코드 패키지 경계가 헷갈릴 때 |
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
| `docs/archive/ui/wireframe/` | 과거 UI 와이어프레임 세부 로그 |
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
| 시세/커뮤니티/지표/에이전트/원장 데이터 | 해당 도메인 `AGENTS.md`, `README.md`, API contract, DB entity/snapshot |
| 장애와 기술 결정 근거 | `docs/governance/TECHNICAL_RISK_REGISTER.md`, Notion 개발자 기술 경험 DB |

새 인덱스 문서는 같은 lookup을 여러 작업 영역이 반복할 때만 만듭니다. 인덱스는 상세 설명을 복제하지 않고 정본 위치, ID/key, 상태, source/asOf만 짧게 가리킵니다.

## 핵심 위주 작성 기준

문서는 많이 쓸수록 좋은 것이 아니라, 다음 작업자가 더 정확히 움직이게 할 때만 가치가 있습니다.

- 추상적인 페르소나, 좋은 태도 선언, 이미 다른 문서에 있는 설명은 반복하지 않습니다.
- 새 문장을 추가할 때는 "이 문장이 다음 에이전트의 선택, 수정 위치, 금지선, 검증 방법 중 무엇을 바꾸는가?"를 확인합니다.
- 답이 없으면 문장을 줄이거나, 결정 전 고민은 `docs/product/PRODUCT_DECISION_NOTES.md`, 작업 이력은 archive/PR/Notion 기록으로 보냅니다.
- 대표파일에는 요약과 링크만 둡니다. 상세 근거, 예시, 과거 맥락은 담당 도메인/layer 정본 문서에 둡니다.

## 읽기와 출력 게이트

토큰 문제는 필수 작업을 줄여 해결하지 않습니다. 같은 일을 하되 큰 입력과 큰 출력을 막습니다.

- 시작 입력: 작업 영역이 명확하면 루트 `AGENTS.md`, `docs/current/HANDOFF.md`, 담당 도메인/layer `AGENTS.md`의 관련 줄만 봅니다. 세부 색인이 필요할 때만 README를 봅니다.
- 스킬 입력: 적용할 스킬이 정해진 뒤 필요한 절차만 읽습니다. Browser/Figma/Stitch/gstack/Superpowers 전문은 시작 루틴이 아닙니다.
- archive 입력: archive는 현재 handoff가 부족할 때만 파일 1개와 키워드 1개로 좁혀 검색합니다.
- 로그 출력: 세션 JSONL, 브라우저 콘솔, DOM, Notion 페이지 전문은 대화에 붙이지 않고 오류명, 파일명, 수치만 남깁니다.
- 도구 출력: `Get-Content -TotalCount`, `Select-Object -First/-Skip`, `rg -n -m 20 <키워드> <좁은 경로>`처럼 출력량을 먼저 제한합니다.
- 검증 출력: 테스트, `git diff --check`, PR 라벨/본문 확인, 필요한 브라우저 QA는 생략하지 않고 결과만 짧게 보고합니다.
- 재확인: 메모리와 과거 대화 요약은 색인으로만 쓰고, 현재 결정은 repo 문서와 현재 코드로 확인합니다.

## 컨텍스트 예산 점검

아래 상황에서는 문서/도구 출력 예산을 다시 봅니다.

- `AGENTS.md`, `docs/current/HANDOFF.md`, `docs/current/TASKS.md`, `docs/layers/ops/`, `docs/domains/`, `docs/layers/ui/`를 바꾸는 PR
- 채팅이 일반 오류로 끊겼거나 한 작업에서 로그/Notion/gstack 출력이 크게 늘어난 경우
- ops 문서 PR 3개가 쌓였거나, 일주일 이상 문서 정리를 하지 않은 경우
- 열린 브랜치/worktree가 5개 이상이거나, close-candidate 브랜치가 생긴 경우

목표 예산:

- 작업 영역이 명확한 새 채팅의 시작 확인은 3k-5k 토큰 안에 끝냅니다.
- 항상 후보가 되는 시작 문서는 파일당 1.5k 토큰 아래를 목표로 합니다.
- `docs/current/HANDOFF.md`는 1.2k 토큰 안팎을 유지합니다.
- `docs/current/TASKS.md`는 미완료 체크박스를 보존하고, 완료 상세 이력만 요약합니다.
- ui Screen Brief는 일반 화면 150줄 이하, 복잡한 부모 화면 220줄 이하를 목표로 하고 변경 로그는 최근 5개만 유지합니다.

초과하면 전체 삭제가 아니라 `rg` 검색, 섹션 읽기, 완료 이력 요약, 출력 요약으로 줄입니다.

## 업데이트 규칙

작업이 끝났다고 모든 문서를 고치지 않습니다.

| 상황 | 갱신할 곳 |
| --- | --- |
| 제품 방향이나 범위 변경 | `docs/product/FINAL_PRODUCT_PLAN.md`, `docs/current/HANDOFF.md` |
| ui 화면 구조, route, child detail, 화면별 API 후보 변경 | `docs/layers/ui/screens/` |
| 커뮤니티 분석 용어/수집 전략 변경 | `docs/domains/community/REACTION_GUIDE.md`, `docs/product/FINAL_PRODUCT_PLAN.md`, `docs/product/PROJECT_BRIEF.md` |
| 최종 기획상 새 기술/제품/운영 리스크 발견 | `docs/governance/TECHNICAL_RISK_REGISTER.md`, 필요 시 관련 도메인 `AGENTS.md`/`README.md` |
| 작업 방식이나 라벨 기준 변경 | `docs/layers/ops/WORKFLOW.md`, `docs/layers/ops/GIT_CONVENTION.md`, `docs/layers/ops/LABEL_GUIDE.md` |
| 브랜치 생명주기나 worktree 정리 기준 변경 | `docs/layers/ops/GIT_CONVENTION.md`, `docs/layers/ops/WORKFLOW.md`, `docs/current/HANDOFF.md` |
| 다음 작업 후보 변경 | `docs/current/TASKS.md`, `docs/current/HANDOFF.md` |
| 새 작업 영역 경계 | `docs/layers/ops/WORK_AREAS.md` |
| 제품 개발/운영 문제, 개선, 기술 결정 | Notion 개발자 기술 경험 DB, 필요 시 관련 가이드 |
| Codex/Notion/PR/문서 운영 사고 | Notion 에이전트 운영 로그 DB |
| PR 종료 | Notion 작업일지, 필요 시 `docs/archive/work-units/items/` |
| 채팅 시작 방식 변경 | `docs/layers/ops/CHAT_START_GUIDE.md`, `docs/layers/ops/WORKFLOW.md`, `docs/current/HANDOFF.md` |

ui 화면 작업은 사용자가 별도로 기록을 지시하지 않아도 Screen Brief를 갱신합니다. 다만 Screen Brief는 현재 기준 문서이므로 긴 작업 과정, 폐기된 시안, 전체 피드백 전문을 누적하지 않고 최신 결론과 열린 질문만 남깁니다.
