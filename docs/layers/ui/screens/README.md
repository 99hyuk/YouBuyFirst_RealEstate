# Front Screen Brief Registry

프론트 작업 중 기획과 디자인이 함께 바뀌는 화면은 이 폴더에서 화면별로 관리합니다. 목적은 화면을 예쁘게 설명하는 것이 아니라, route, 화면 목적, 섹션, mock data, API 후보, 기획자 확인 필요 항목을 잃어버리지 않는 것입니다.

반복 UI 기준은 `../DESIGN_SYSTEM.md`를 먼저 따릅니다. Screen Brief에는 화면별 구조와 계약만 두고, 공통 색상/타이포/컴포넌트 설명을 중복해서 붙이지 않습니다.

## 원칙

- 탭 하나만 기준으로 보지 않고, 사용자가 실제로 이동하는 화면 트리 기준으로 정리합니다.
- route를 가진 페이지는 Screen Brief를 둡니다.
- 단순 화면은 `screens/<screen>.md`로 둡니다.
- route가 없어도 독립 데이터 계약, 독립 상태, 공유 가능한 상세 UI를 가진 drawer/modal/detail panel은 Screen Brief 후보입니다.
- 단순 버튼, 카드, 표 셀처럼 독립 기획이 없는 component는 별도 brief를 만들지 않습니다.
- 화면을 만들며 바뀐 기획은 먼저 해당 Screen Brief에 남기고, 안정화된 것만 `docs/product/FINAL_PRODUCT_PLAN.md`, API 명세, 관련 도메인/layer `AGENTS.md`/`README.md`로 승격합니다.
- `docs/current/HANDOFF.md`에는 세부 화면 내용을 늘리지 않고, 이 registry 위치만 안내합니다.
- 사용자가 따로 "기록해"라고 말하지 않아도, 프론트 작업자가 화면 구조, route, child screen, fixture/API 후보, 화면 문구 기준을 바꾸면 해당 Screen Brief를 갱신합니다.
- Screen Brief는 최신 기준 문서입니다. 완료된 시행착오, 긴 피드백 전문, 과거 스크린샷 설명을 계속 누적하지 않습니다.

## 화면 트리

| Screen ID | Route 후보 | Brief | 상태 | 비고 |
| --- | --- | --- | --- | --- |
| `realestate-dashboard` | `/dashboard` 또는 `/realestate` | `realestate-dashboard.md` | active | 메인 대시보드, 언급 많은 지역/단지, 이슈, market fact 상태 |
| `realestate-target-detail` | `/realestate/targets/:targetId` | `realestate-target-detail.md` | active | 지역/단지 상세, 반응 지표, 타임라인, 유사 과거, 근거 로그 |
| `newsroom` | `/newsroom?feed=&page=` | `newsroom.md` | refactor-needed | 뉴스, 컬럼, 커뮤니티 링크를 부동산 이슈룸으로 전환 필요 |
| `indicators` | `/indicators` | `indicators.md` | refactor-needed | 시장 지표와 지역/단지 반응 괴리로 전환 필요 |
| `agents` | `/agents` | `agents.md` | refactor-needed | 에이전트 근거 로그 화면으로 전환 필요 |
| `dashboard` | `/dashboard` | `dashboard.md` | legacy-stock-reference | 기존 주식 대시보드 참고 |
| `stocks` | `/stocks` | `stocks.md` | legacy-stock-reference | 기존 종목 목록 참고 |
| `stock-detail` | `/stocks/:symbol` | `stock-detail/README.md` | legacy-stock-reference | 기존 종목 상세 참고 |
| `human-indicator` | `/communities?view=` | `human-indicator.md` | legacy-stock-reference | 기존 인간 지표 참고 |
| `portfolio` | `/portfolio` | `portfolio.md` | legacy-stock-reference | 기존 모의 포트폴리오 참고 |

## Screen Brief 템플릿

```md
# 화면명

## Route

- Parent:
- Route 후보:
- Child screens:

## 화면 목적

사용자가 이 화면에서 무엇을 판단하거나 확인하는지 적습니다.

## 현재 섹션

- 섹션 1
- 섹션 2

## 상태와 빈 화면

- loading:
- empty:
- error:
- stale/mock:

## API 후보

| 필드 | 소유 도메인/layer | 설명 |
| --- | --- | --- |

## 기획자 확인 필요

- 아직 확정하지 않은 질문

## 변경 로그

- YYYY-MM-DD: 무엇이 바뀌었는지 한 줄
```

## PR 완료 조건

프론트 PR이 화면 구조나 기획을 바꾸면 다음 중 해당하는 항목을 같이 갱신합니다.

- route나 navigation 변경: 이 registry의 화면 트리
- 화면 섹션 변경: 해당 Screen Brief의 `현재 섹션`
- fixture/mock field 추가: 해당 Screen Brief의 `API 후보`
- 새 상세 drawer/modal 추가: 별도 Screen Brief 후보 여부 판단
- 사용자 확인이 필요한 결정: 해당 Screen Brief의 `기획자 확인 필요`

화면 변경이 있었는데 Screen Brief 갱신이 필요 없다고 판단했다면 PR 본문에 `Screen Brief 미갱신: 이유`를 남깁니다.
