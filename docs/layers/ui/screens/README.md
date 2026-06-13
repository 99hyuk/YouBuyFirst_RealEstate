# Front Screen Brief Registry

화면을 바꿀 때 기획과 구현이 따로 움직이지 않도록 화면별 목적, route, 주요 섹션, mock/API 후보를 이 폴더에서 관리합니다.

공통 UI 규칙은 `../DESIGN_SYSTEM.md`를 먼저 따릅니다. Screen Brief에는 화면별 구조와 계약만 적고, 공통 색상·타이포·컴포넌트 설명은 반복하지 않습니다.

## 원칙

- 문서는 사용자가 실제로 이동하는 화면 단위로 씁니다.
- route가 있는 페이지는 Screen Brief를 둡니다.
- 과거 금융 서비스 route는 현재 화면 목록에 남기지 않고, 부동산 표준 route만 기록합니다.
- drawer, modal, detail panel처럼 공유 가능한 상세 UI는 필요할 때 별도 brief로 분리합니다.
- 화면 변경이 있으면 PR에서 해당 Screen Brief도 함께 갱신합니다.

## 화면 목록

| Screen ID | Route 정보 | Brief | 상태 | 비고 |
| --- | --- | --- | --- | --- |
| `dashboard` | `/dashboard` | `dashboard.md` | active | 메인 대시보드, 지역 반응, 주요 부동산 지표, 뉴스/리포트 |
| `realestate-map` | `/realestate/map`, `/realestate/map/:regionId` | `realestate-screen-definition.md` | active | 전국 heat map, 시군구 drill-down, 지역 선택 리포트, 향후 단지 drill-down |
| `newsroom` | `/newsroom?feed=` | `newsroom.md` | active | 뉴스, 리포트, 영상, 블로그·커뮤니티 링크 |
| `indicators` | `/indicators`, `/indicators/:category` | `indicators.md` | active | 가격·거래량, 공급·수급, 수요·심리, 거시·금융 지표 |
| `region-reactions` | `/realestate/reactions?view=` | `region-reactions.md` | active | 지역·단지 순위, 커뮤니티 반응, 근거 로그를 합친 표준 화면 |
| `region-detail` | `/realestate/targets/:targetId` | `region-detail/README.md` | active | 지역/단지 상세 리포트 |
| `watchlist` | `/realestate/watchlist` | `watchlist.md` | active | 관심 지역, 알림, alias/source DB 연결 |

## Screen Brief 템플릿

```md
# 화면명

## Route

- Parent:
- Route 정보:
- Child screens:

## 화면 목적

사용자가 이 화면에서 무엇을 판단하고 확인하는지 적습니다.

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

## 기획 확인 필요

- 아직 확정되지 않은 질문

## 변경 로그

- YYYY-MM-DD: 무엇이 바뀌었는지 한 줄
```

## PR 완료 조건

화면 구조나 기획이 바뀌면 다음 중 해당 항목을 함께 갱신합니다.

- route/navigation 변경: 이 registry의 화면 목록
- 화면 섹션 변경: 해당 Screen Brief의 `현재 섹션`
- fixture/mock field 추가: 해당 Screen Brief의 `API 후보`
- 상세 drawer/modal 추가: 별도 Screen Brief 필요 여부 판단
- 사용자 확인이 필요한 결정: 해당 Screen Brief의 `기획 확인 필요`
