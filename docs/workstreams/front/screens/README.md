# Front Screen Brief Registry

프론트 작업 중 기획과 디자인이 함께 바뀌는 화면은 이 폴더에서 화면별로 관리합니다. 목적은 화면을 예쁘게 설명하는 것이 아니라, route, 화면 목적, 섹션, mock data, API 후보, 기획자 확인 필요 항목을 잃어버리지 않는 것입니다.

## 원칙

- 탭 하나만 기준으로 보지 않고, 사용자가 실제로 이동하는 화면 트리 기준으로 정리합니다.
- route를 가진 페이지는 Screen Brief를 둡니다.
- route가 없어도 독립 데이터 계약, 독립 상태, 공유 가능한 상세 UI를 가진 drawer/modal/detail panel은 Screen Brief 후보입니다.
- 단순 버튼, 카드, 표 셀처럼 독립 기획이 없는 component는 별도 brief를 만들지 않습니다.
- 화면을 만들며 바뀐 기획은 먼저 해당 Screen Brief에 남기고, 안정화된 것만 `FINAL_PRODUCT_PLAN.md`, API 명세, 트랙 README로 승격합니다.
- `CURRENT_HANDOFF.md`에는 세부 화면 내용을 늘리지 않고, 이 registry 위치만 안내합니다.
- 사용자가 따로 "기록해"라고 말하지 않아도, 프론트 작업자가 화면 구조, route, child screen, fixture/API 후보, 화면 문구 기준을 바꾸면 해당 Screen Brief를 갱신합니다.
- Screen Brief는 최신 기준 문서입니다. 완료된 시행착오, 긴 피드백 전문, 과거 스크린샷 설명을 계속 누적하지 않습니다.

## 크기 관리

Screen Brief가 커지면 새 채팅이 느려지고, 화면 기준도 흐려집니다. 각 파일은 다음 예산을 목표로 합니다.

| 항목 | 목표 |
| --- | --- |
| 일반 화면 brief | 150줄 이하 |
| 복잡한 부모 화면 brief | 220줄 이하 |
| 변경 로그 | 최근 5개만 유지 |
| 기획자 확인 필요 | 열린 질문만 유지 |
| 이미지 | 직접 붙이지 않고 필요한 경우 `docs/assets/` 링크만 사용 |

오래된 결정 과정은 Screen Brief에 계속 붙이지 않습니다. 필요한 경우 `docs/workstreams/front/archive/` 또는 PR/Notion 작업 로그로 넘기고, Screen Brief에는 현재 결론만 남깁니다.

## 화면 트리

| Screen ID | Route 후보 | Brief | 상태 | 비고 |
| --- | --- | --- | --- | --- |
| `dashboard` | `/dashboard` | 예정 | active | 메인 대시보드, 종목/커뮤니티/뉴스 요약 |
| `stock-detail` | `/stocks/:symbol` | `stock-detail.md` | active | 종목 상세, 팩트폭격 배너, 차트, 지표, 근거 |
| `stock-news-detail` | `/stocks/:symbol/news/:newsId` 또는 drawer | 예정 | candidate | 뉴스/공시 상세 링크와 원문 이동 전 요약 |
| `stock-filing-detail` | `/stocks/:symbol/filings/:filingId` 또는 drawer | 예정 | candidate | 공시 상세, 관련 지표 영향 |
| `stock-community-post` | `/stocks/:symbol/community/:postId` 또는 drawer | 예정 | candidate | 커뮤니티 원문 snippet, 출처, 관련 종목 |
| `stock-indicator-detail` | `/stocks/:symbol/indicators/:indicatorId` 또는 panel | 예정 | candidate | RSI, VWAP, PER 등 개별 지표 설명 |
| `community` | `/community` | 예정 | candidate | 커뮤니티별 반응/성과 비교 |
| `agents` | `/agents` | 예정 | candidate | 에이전트 판단 로그와 리더보드 |
| `portfolio` | `/portfolio` | 예정 | candidate | 모의 포트폴리오와 원장 기반 손익 |

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

| 필드 | 소유 트랙 | 설명 |
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
