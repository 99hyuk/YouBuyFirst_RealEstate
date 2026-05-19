# Front Minimal Design System

## 기준 화면

- 1차 기준 화면은 `/dashboard`입니다. 현재 프론트 화면 중 완성도가 가장 높으므로 새 화면과 컴포넌트는 대시보드의 정보 밀도, 간격, panel header, feed/table/chart 톤을 먼저 따릅니다.
- 대시보드처럼 한 화면에 여러 정보가 읽히게 하되, 큰 네모 카드 반복보다 작은 제목, 짧은 badge, 얇은 구분선, 촘촘한 리스트로 위계를 만듭니다.
- 다른 화면 brief와 충돌하면 이 문서와 현재 대시보드 구현을 우선 확인합니다. 새 UI 패턴이 필요하면 페이지 안에 숨기지 말고 아래 `디자인 시스템 후보 기록`에 남깁니다.
- 종목 상세의 팩트폭격 배너는 예외적인 특수 컴포넌트이며 `docs/STOCK_DETAIL_COPY_GUIDE.md`와 `docs/workstreams/front/screens/stock-detail.md`를 함께 따릅니다.

현재 화면에서 반복되는 UI만 기준으로 둔 최소 디자인 시스템입니다. 새 화면을 만들 때는 이 기준을 먼저 적용하고, 새 패턴이 필요하면 해당 페이지에만 숨기지 말고 `디자인 시스템 후보`로 남깁니다.

## 색상 토큰

| 용도 | 토큰 | 값 | 기준 |
| --- | --- | --- | --- |
| 배경 | `--bg` | `#f3f6f8` | 전체 앱 배경 |
| 본문 글자 | `--ink` | `#17212b` | 제목, 숫자, 주요 텍스트 |
| 보조 글자 | `--muted` | `#6b7788` | 설명, 메타 |
| 약한 보조 | `--muted-2` | `#9aa5b3` | timestamp, 비활성 설명 |
| 선 | `--line` | `#dfe5ec` | panel/table 구분선 |
| 강한 선 | `--line-strong` | `#cdd6e1` | graph axis, 강조 border |
| 표면 | `--surface` | `#ffffff` | panel, table, card |
| 약한 표면 | `--surface-soft` | `#f8fafc` | table head, inner card |
| 상단/강조 어두움 | `--nav` | `#1d1f23` | topbar, roast banner |
| 브랜드 | `--brand` | `#4f7fee` | active tab, link, rank number |

## 타이포

Pretendard Variable을 기본으로 씁니다. 숫자는 굵게, 설명은 작게 둡니다.

| 용도 | 크기 | 굵기 | 예 |
| --- | --- | --- | --- |
| 화면 제목 | `21-24px` | `900` | page header, 종목 거래량 순위 |
| 섹션 제목 | `14-17px` | `850-920` | panel header, table title |
| 핵심 숫자 | `17-38px` | `900` | KPI, 가격, 스코어 |
| 본문/행 제목 | `13px` | `800-850` | table row stock name |
| 보조 설명 | `11-12px` | `650-780` | meta, timestamp, source |
| badge/tab | `10.5-12px` | `780-860` | status pill, filter |

## 간격, Radius, Elevation

- 페이지 gutter: `24px`, 좁은 화면에서는 `12px`까지 축소합니다.
- 화면/큰 섹션 gap: `14-18px`.
- 카드 내부 padding: 일반 `12-16px`, 고밀도 데이터 카드 `8-12px`.
- radius: panel/table `8px`, 작은 카드 `7px`, pill/tab `999px`, 원형 버튼 `50%`.
- elevation: 기본 panel은 `0 16px 36px rgba(39, 51, 67, 0.07)`, 강조 overlay/right panel은 더 강한 그림자만 씁니다.
- 카드 중첩은 피하고, 반복 항목은 table row, strip, band로 처리합니다.

## 공통 컴포넌트 패턴

| 패턴 | 기준 |
| --- | --- |
| `topbar` | `--nav` 배경, 중앙 nav, 오른쪽 로그인/상태. 아래 live ticker는 별도 얇은 band로 둡니다. |
| `right rail` | 오른쪽 고정 rail, 아이콘/짧은 라벨. 확장 패널은 본문을 덮는 overlay 성격이며 별도 카드 중첩을 피합니다. |
| `page header` | label + H2 + 짧은 설명 + 상태 badge/search. 긴 기능 설명을 넣지 않습니다. |
| `panel` | 흰 배경, 8px radius, 얇은 border. 반복되는 큰 영역의 기본 컨테이너입니다. |
| `data card` | 고밀도 숫자/상태용. `label`, `strong`, `em` 3단 구조를 기본으로 합니다. |
| `badge` | `status-pill`. mock/stale/warning/subtle 상태를 짧게 표시합니다. |
| `tab` | pill 형태, 활성 상태는 brand 계열 border/background. 많은 탭은 filter strip으로 처리합니다. |
| `table` | header band + row. 행 높이는 `42-52px`, 숫자와 상태는 작고 굵게. 좁은 화면에서는 가로 스크롤 허용. |
| `chart shell` | 축/범례/기간 버튼을 그래프 안쪽 또는 헤더 오른쪽에 붙입니다. PPT식 단일 선만 두지 않습니다. 가격 차트는 quote snapshot과 데이터 출처 라벨을 분리합니다. |

## 상승/하락/긍정/부정

- 한국 주식/금융 관습 기준으로 상승은 빨강 `--market-up`, 하락은 파랑 `--market-down`을 씁니다.
- 커뮤니티 반응도 긍정은 빨강, 부정은 파랑으로 맞춰 `매수/매도 의견처럼 읽히는 색상 혼선`을 줄입니다.
- 중립/미분류는 `--neutral-slate`.
- 위험/주의는 `--orange` 또는 warning badge, 성공/정상은 `--green`.
- 서비스 결론처럼 보이는 `추천`, `매수`, `매도` 표현은 쓰지 않고, 관찰 데이터 라벨로만 씁니다.

## 특수 컴포넌트

### 종목 상세 팩트폭격 배너

- 기준 문서: `docs/STOCK_DETAIL_COPY_GUIDE.md`, 화면 brief: `docs/workstreams/front/screens/stock-detail.md`.
- 위치: 종목 상세 최상단, 종목명/티커와 닫기 이후 바로 노출.
- 시각: `--nav` 계열 검은 배너, 작은 radius, 중앙 큰 헤드라인.
- 내용: `mood`, `headline`, `subtitle`, `scoreLine`, `riskNote`, 근거 chip.
- 헤드라인은 커뮤니티 요약이 아니라 시황/기술/재무/뉴스/컨센서스 기반 종목 상태 한줄평입니다.
- `roast` 톤은 공개 데모/검색 상세에 우선 적용하고, 보유 종목/개인화 화면에서는 순화 기준을 따릅니다.

## 디자인 시스템 후보 기록

새 페이지에서 다음이 필요하면 바로 공통화하지 말고 PR 또는 Screen Brief의 `기획자 확인 필요`에 후보로 남깁니다.

- 새 table variant
- 새 chart shell
- Lightweight Charts 외 다른 차트 provider shell
- 새 drawer/modal/detail panel
- 새 상태 badge
- 새 데이터 카드 밀도
- roast banner 외 특수 hero 패턴
