# 문서 재분류 계획

이 문서는 2026-05 문서 재분류 당시의 임시 작업 계획입니다. 현재 실행할 계획이 아니며, archive의 과거 근거로만 봅니다. 최신 구조와 읽기 기준은 `AGENTS.md`, `docs/layers/ops/DOCUMENTATION_GUIDE.md`, `docs/layers/ops/WORK_AREAS.md`가 정본입니다.

## 결론

`INDEX.md`를 새로 만드는 것보다 root `AGENTS.md`를 얇은 라우터로 쓰는 편이 낫습니다. 에이전트가 항상 먼저 만나는 문서에 전체 지도와 읽기 게이트가 있어야 불필요한 문서 탐색을 줄일 수 있습니다.

문서 정본은 트랙이 아니라 도메인과 레이어 기준으로 정리합니다. 트랙은 PR, 브랜치, 작업 분배, 라벨에 쓰는 실행 단위로만 남깁니다.

## 목표 구조 후보

```text
docs/
  current/        # 지금 상태와 다음 작업
  product/        # 제품 방향과 결정
  domains/        # 제품 도메인 정본
  layers/         # 여러 도메인을 가로지르는 UI/운영 계층
  governance/     # 정책, 리스크, 장애/문제 대응
  archive/        # 과거 작업 기록
  assets/         # 문서에서 참조하는 이미지 등 비텍스트 자산
```

## 도메인/레이어 기준

| 구분 | 역할 | 예시 |
| --- | --- | --- |
| `current` | 오늘의 작업 상태와 다음 후보 | handoff, tasks |
| `product` | 무엇을 만들지에 대한 장기 기준 | 최종 기획, 제품 결정 메모, 프로젝트 요약 |
| `domains/stock` | 종목 기준 정보 | 종목 마스터, 티커, 별칭, 검색/매칭 |
| `domains/community` | 커뮤니티 원천/반응 데이터 | 수집 소스, 원문 제한 저장, 종목 언급, 반응 분류 |
| `domains/indicator` | 제품 핵심 지표 | 열기 지수, 개미 심리 지수, 30분 snapshot, 유사 상황 검색 |
| `domains/market` | 시장 데이터 | quote snapshot, chart candle, 수급 |
| `domains/simulation` | 모의투자 | 가상 계좌, 주문, 체결, 원장, 포트폴리오 |
| `domains/agent` | AI 판단/종합 분석 | 전략, 결정 로그, 커뮤니티별 성과 비교, 종목 상태 헤드라인 생성 |
| `layers/ui` | 화면 표현 계층 | screen brief, 디자인 시스템, 화면별 API 후보 |
| `layers/ops` | 운영 계층 | 문서 운영, Git/PR, 라벨, Notion, workflow |
| `governance` | 지켜야 할 규칙과 위험 관리 | 법적 리스크, 기술 리스크, 트러블슈팅 |
| `archive` | 현재 판단에 기본으로 읽지 않는 과거 기록 | work-units, superpowers plans/specs |

## 현재 문서 분류표

| 현재 위치 | 목표 위치 | 판단 |
| --- | --- | --- |
| `AGENTS.md` | `AGENTS.md` | root 라우터로 유지하되, 핵심 규칙과 도메인/레이어 경로만 남깁니다. |
| `docs/layers/ops/CHAT_START_GUIDE.md` | `docs/layers/ops/CHAT_START_GUIDE.md` | 채팅 시작 절차이므로 ops 레이어입니다. |
| `docs/archive/CONTEXT.md` | `docs/current/CONTEXT.md` 또는 archive | 현재 `CURRENT_HANDOFF.md`와 중복 여부 확인 후 병합/폐기 후보입니다. |
| `docs/current/HANDOFF.md` | `docs/current/HANDOFF.md` | 현재 상태 정본입니다. |
| `docs/current/TASKS.md` | `docs/current/TASKS.md` | 다음 작업 후보 정본입니다. |
| `docs/layers/ops/DOCUMENTATION_GUIDE.md` | `docs/layers/ops/DOCUMENTATION_GUIDE.md` | 문서 운영 기준입니다. |
| `docs/layers/ops/DOMAIN_PACKAGE_GUIDE.md` | `docs/layers/ops/DOMAIN_PACKAGE_GUIDE.md` 또는 domain README에 분배 | 코드 패키지 경계 안내입니다. 일부는 domain README로 흡수할 수 있습니다. |
| `docs/layers/ops/ENGINEERING_EVIDENCE_GUIDE.md` | `docs/layers/ops/ENGINEERING_EVIDENCE_GUIDE.md` | 기술 경험 기록 운영 기준입니다. |
| `docs/layers/ops/GIT_CONVENTION.md` | `docs/layers/ops/GIT_CONVENTION.md` | PR/Git 운영 기준입니다. |
| `docs/layers/ops/LABEL_GUIDE.md` | `docs/layers/ops/LABEL_GUIDE.md` | 라벨 운영 기준입니다. |
| `docs/layers/ops/WORKFLOW.md` | `docs/layers/ops/WORKFLOW.md` | 작업 흐름 운영 기준입니다. |
| `docs/product/FINAL_PRODUCT_PLAN.md` | `docs/product/FINAL_PRODUCT_PLAN.md` | 제품 장기 정본입니다. |
| `docs/product/PRODUCT_DECISION_NOTES.md` | `docs/product/PRODUCT_DECISION_NOTES.md` | 제품/기술 고민 색인입니다. |
| `docs/product/PROJECT_BRIEF.md` | `docs/product/PROJECT_BRIEF.md` | MVP 요약입니다. |
| `docs/domains/community/REACTION_GUIDE.md` | `docs/domains/community/REACTION_GUIDE.md` | 커뮤니티 반응 용어/지표 정본입니다. |
| `docs/domains/agent/STOCK_DETAIL_HEADLINE.md` | `docs/domains/agent/STOCK_DETAIL_HEADLINE.md`와 `docs/layers/ui/STOCK_DETAIL_BANNER.md`로 분리 | 헤드라인 생성 기준은 agent 도메인, 검은 배너 UI/레퍼런스는 UI 레이어가 소유합니다. |
| `docs/governance/LEGAL_RISK_CASES.md` | `docs/governance/LEGAL_RISK_CASES.md` | 정책/법적 리스크 관리 문서입니다. |
| `docs/governance/TECHNICAL_RISK_REGISTER.md` | `docs/governance/TECHNICAL_RISK_REGISTER.md` | 리스크 레지스터입니다. |
| `docs/governance/TROUBLESHOOTING_GUIDE.md` | `docs/governance/TROUBLESHOOTING_GUIDE.md` | 장애/문제 대응 기록 기준입니다. |
| `docs/layers/ops/TRACKS.md` | `docs/layers/ops/TRACKS.md` | 트랙은 실행 라벨로 유지합니다. |
| `docs/workstreams/crawl/README.md` | `docs/domains/community/COLLECTION.md` 또는 README 일부 | 커뮤니티 수집 경계로 흡수합니다. |
| `docs/workstreams/data/README.md` | `docs/domains/stock/README.md`, `docs/domains/community/README.md`, `docs/domains/indicator/README.md`로 분리 | `data`가 너무 넓어 종목 기준, 커뮤니티 반응, 핵심 지표를 분리합니다. |
| `docs/domains/market/README.md` | `docs/domains/market/README.md` | market 도메인 정본입니다. |
| `docs/domains/market/CHART_CANDLES.md` | `docs/domains/market/CHART_CANDLES.md` | market contract입니다. |
| `docs/domains/market/INVESTOR_FLOWS.md` | `docs/domains/market/INVESTOR_FLOWS.md` | market contract입니다. |
| `docs/domains/market/QUOTE_SNAPSHOT.md` | `docs/domains/market/QUOTE_SNAPSHOT.md` | market contract입니다. |
| `docs/workstreams/trade/README.md` | `docs/domains/simulation/README.md` | trade보다 simulation 도메인명이 제품 관점에 맞습니다. |
| `docs/workstreams/agent/README.md` | `docs/domains/agent/README.md` | agent 도메인 정본입니다. |
| `docs/layers/ui/README.md` | `docs/layers/ui/README.md` | UI 레이어 정본입니다. |
| `docs/layers/ui/DESIGN_SYSTEM.md` | `docs/layers/ui/DESIGN_SYSTEM.md` | UI 레이어 정본입니다. |
| `docs/layers/ui/WIREFRAME_HANDOFF.md` | `docs/layers/ui/WIREFRAME_HANDOFF.md` 또는 current 링크 | UI 현재 작업과 겹치므로 이관 시 최신성 확인이 필요합니다. |
| old front Stitch prompt | `docs/archive/ui/STITCH_DASHBOARD_PROMPT.md` | Stitch 흐름은 기본 디자인 방식에서 폐기하고 과거 참고 자료로만 보관합니다. |
| `docs/layers/ui/VISUAL_CHANGELOG.md` | `docs/layers/ui/VISUAL_CHANGELOG.md` | UI 변경 이력입니다. 최근 항목만 유지하는 후보입니다. |
| `docs/layers/ui/screens/` | `docs/layers/ui/screens/` | 화면별 Screen Brief 정본입니다. |
| old front wireframe archive | `docs/archive/ui/wireframe/` | 과거 UI 기록입니다. |
| `docs/workstreams/ops/README.md` | `docs/layers/ops/README.md` | ops 레이어 정본입니다. |
| `docs/archive/work-units/items/` | `docs/archive/work-units/` | PR/작업 단위 과거 기록입니다. |
| `docs/archive/superpowers/items/` | `docs/archive/superpowers/` | 과거 설계/실행 계획 archive입니다. |
| `docs/archive/README.md` | `docs/archive/README.md` | archive 안내로 유지합니다. |
| `docs/assets/` | `docs/assets/` | 이미지 자산입니다. 기본 읽기 대상이 아닙니다. |

## 먼저 만들 도메인 README

각 README는 80줄 이하를 목표로 합니다.

| 문서 | 담을 내용 |
| --- | --- |
| `docs/domains/stock/README.md` | 종목 마스터, 티커, 별칭, 검색/매칭 책임과 community/market/front 접점 |
| `docs/domains/community/README.md` | 커뮤니티 수집, 원문 제한 저장, 종목 언급 후보, 반응 분류 |
| `docs/domains/indicator/README.md` | 열기 지수, 개미 심리 지수, 30분 snapshot, 토픽 클러스터, 벡터 기반 유사 상황 검색 |
| `docs/domains/market/README.md` | 시세 provider, quote snapshot, chart candle, investor flow |
| `docs/domains/simulation/README.md` | 가상 계좌, 원장, 주문/체결, 포트폴리오 |
| `docs/domains/agent/README.md` | AI 판단 입력, 전략, 결정 로그, 성과 비교 |
| `docs/layers/ui/README.md` | 화면별 brief, 디자인 시스템, API 후보와 도메인 참조 규칙 |
| `docs/layers/ops/README.md` | 문서 운영, PR/Git, Notion, 브랜치/worktree 규칙 |
| `docs/governance/README.md` | 정책, 리스크, 장애 기록의 차이와 읽기 게이트 |

## 이관 순서

1. root `AGENTS.md`를 전체 라우터로 줄이고 목표 경로를 적습니다.
2. `current`, `product`, `governance`, `layers`, `domains`, `archive` 폴더를 만듭니다.
3. current/product/governance/ops처럼 경계가 명확한 문서부터 이동합니다.
4. `workstreams/data`는 바로 이동하지 않고 stock/community/indicator 분리안을 먼저 만듭니다.
5. `front` 문서는 `layers/ui`로 옮기되, 화면별 Screen Brief 링크가 깨지지 않게 한 번에 처리합니다.
6. `work-units`, `superpowers`는 archive로 이동하고 AGENTS에서 기본 읽기 금지를 다시 명시합니다.
7. 전체 repo에서 옛 경로를 `rg`로 찾아 링크를 갱신합니다.
8. `git diff --check`와 주요 시작 문서 길이를 확인합니다.

## 이동 전 확인 질문

- `CONTEXT.md`가 아직 쓰이는지, `CURRENT_HANDOFF.md`와 병합해도 되는지 확인합니다.
- `STITCH_DASHBOARD_PROMPT.md`는 archive로 보냅니다.
- `STOCK_DETAIL_COPY_GUIDE.md`는 agent 도메인의 헤드라인 생성 기준과 UI 레이어의 배너 표현 기준으로 분리합니다.
- `indicator`는 프로젝트 핵심 지표 확장성을 고려해 별도 `domains/indicator`로 둡니다.
