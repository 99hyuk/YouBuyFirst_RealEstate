# Front Minimal Design System

기준 화면은 부동산 대시보드입니다. 새 화면은 대시보드의 정보 밀도, 작은 헤더, Pretendard 타이포, 얇은 선, 절제된 그림자를 먼저 따릅니다.

## 너나사 시리즈 원칙

너나사 부동산은 너나사 시리즈의 공통 shell, 정보 밀도, 컴포넌트 패턴을 따르되 대표 accent는 warm orange 계열로 둡니다.

| 버티컬 | accent 기준 | 사용 위치 |
| --- | --- | --- |
| 너나사 부동산 | warm orange 계열 | 부동산 active 화면의 브랜드 포인트 |

유지할 것:

- topbar, 검색, 오른쪽 rail, dashboard grid, dense card, timeline, table, badge 패턴
- Pretendard 기반 타이포와 작은 header rhythm
- 흰 surface, 옅은 회색 배경, 얇은 border, 절제된 그림자
- 정보 구조: 첫 화면은 landing이 아니라 실제 dashboard

바꿀 것:

- `--brand`, active tab, 주요 CTA, 선택 상태, 핵심 포인트 line/icon
- 부동산 전용 강조 chip과 link hover
- visual history 신규 캡처의 accent 설명

바꾸지 말 것:

- 상승/하락, 기대/우려, warning/error 같은 의미색
- chart series color와 market up/down color를 브랜드색으로 억지 통일
- 카드 모양, nav 위치, 검색 위치, 오른쪽 rail 구조

## UI 표현 원칙

긴 설명문을 많이 쌓기보다 정보를 시각 구조로 바꿔 보여줍니다.

| 정보 성격 | 우선 표현 |
| --- | --- |
| 순위, 급증, 주목 대상 | rank tile, signal mosaic, compact list |
| 기대/우려, 쟁점 비율 | 막대, split meter, 색상 chip |
| 시간 흐름, 시장 사실 변화 | 선 그래프, sparkline, timeline |
| 이유, 근거, 상태 | 짧은 chip 2-3개, badge, 상태 pill |
| 비교, 로그, 원천성 데이터 | 표, ledger row, dense grid |

문장은 보조 설명으로만 씁니다. 카드 안에 긴 문단이 필요해지면 숫자, 축, 범례, chip, 표 row로 쪼갤 수 있는지 먼저 봅니다. 이 기준은 부동산 대시보드, 지역/단지 상세, 뉴스/컬럼 이슈룸, 반응 지표, 에이전트 근거 로그 화면에 공통 적용합니다.

탭 첫 화면은 `핵심 요약 허브`로 설계합니다. 사용자가 탭에 들어오자마자 봐야 하는 정보만 카드, 타일, 그래프, 표로 보여주고, 상세한 지표 묶음은 별도 route나 하위 상세 화면으로 보냅니다.

## 색상 토큰

| 용도 | 토큰 | 값 |
| --- | --- | --- |
| 배경 | `--bg` | `#f3f6f8` |
| 본문 | `--ink` | `#17212b` |
| 보조 글씨 | `--muted` | `#6b7788` |
| 구분선 | `--line` | `#dfe5ec` |
| 표면 | `--surface` | `#ffffff` |
| 상단/강조 어두운 면 | `--nav` | `#1d1f23` |
| 너나사 부동산 accent | `--series-realestate` | `#f08a2b` |
| 너나사 부동산 strong text/CTA | `--series-realestate-strong` | `#b45309` |
| 너나사 부동산 soft bg | `--series-realestate-soft` | `#fff7ed` |
| 너나사 부동산 border | `--series-realestate-line` | `#fed7aa` |
| 현재 버티컬 브랜드 | `--brand` | 부동산에서는 `var(--series-realestate)` |
| 기대 관찰 | `--expectation` | 빨강 계열 |
| 우려 관찰 | `--concern` | 파랑 계열 |
| 확인 필요 | `--warning` | 주황 계열 |

부동산 accent는 경고색과 겹치지 않게 씁니다. 큰 면이나 CTA에는 `--series-realestate-strong`, 옅은 배경에는 `--series-realestate-soft`, 포인트 아이콘/얇은 line에는 `--series-realestate`를 우선 씁니다. 텍스트 대비가 필요한 곳에서 밝은 주황을 본문색으로 직접 쓰지 않습니다.

## 타이포

- 페이지 제목: 21-24px, 900
- 섹션 제목: 14-17px, 850-920
- 핵심 숫자: 17-38px, 900
- 표/카드 이름: 13px, 800-850
- 설명/메타: 11-12px, 650-780
- badge/tab: 10.5-12px, 780-860

## 간격과 형태

- 페이지 gutter: 24px, 좁은 화면에서는 12px까지 축소
- 섹션 gap: 14-18px
- 카드 padding: 12-16px, 고밀도 카드는 8-12px
- radius: panel 8-18px, small card 7-14px, pill 999px
- elevation: 기본 panel은 약한 그림자만 사용
- 카드 안에 또 카드가 중첩되는 구조는 피합니다.

## 공통 컴포넌트

| 패턴 | 기준 |
| --- | --- |
| topbar | 어두운 배경, 중앙 nav, 오른쪽 로그인/상태. 데이터 상태 band는 별도 얇은 band. |
| right rail | 오른쪽 고정 rail. 확장 panel은 overlay 성격으로 다루며 버튼 상태가 눌린 채 남지 않게 합니다. |
| page header | label + H2 + 짧은 설명 + 보조 tab/search. 긴 기능 설명은 넣지 않습니다. |
| panel | 흰 배경, 얇은 border, 작은 header band. |
| data card | `label`, `strong`, `em` 구조를 기본으로 숫자와 상태를 먼저 읽게 합니다. |
| badge | mock/stale/warning/subtle 상태를 짧게 표시합니다. |
| tab | pill 형태. 활성 상태는 브랜드 계열 또는 어두운 배경. |
| table | header band + row. 좁은 화면에서는 가로 스크롤 허용. |
| chart shell | 그래프, 범례, 기간 버튼, 데이터 출처와 상태를 한 shell 안에서 정리합니다. 축과 grid를 넣어 전문적인 느낌을 유지하고, market fact와 raw source 상태는 시각적으로 분리합니다. |
| signal mosaic | 상단 핵심 신호를 `2칸+1칸 / 1칸+2칸` 모자이크로 배치합니다. |
| issue mix | 쟁점 비율은 stacked bar, split meter, compact legend로 보여줍니다. |
| timeline | 커뮤니티 반응, 뉴스/컬럼, market fact, 정책 이벤트를 같은 축에서 구분합니다. |

## 부동산 색상과 문구

- 기대/우려는 관찰 데이터로만 표시합니다. 행동 지시나 미래 단정처럼 보이지 않게 라벨을 명확히 둡니다.
- `추천`, `사라`, `팔아라`, `수익 보장`, `진입`, `시그널 확정`, `오를 지역`, `청약 넣어라`, `대출 받아라` 같은 표현은 서비스 문구로 쓰지 않습니다.
- `대출 규제 언급`, `청약 관련 글 증가`, `전세 우려 증가`처럼 출처가 있는 관찰 데이터 라벨은 사용할 수 있습니다.
- provider, `asOf`, `stale`, `mock`, `확인 필요` 상태는 카드나 그래프 근처에 붙입니다.

## 특수 컴포넌트

### 지역/단지 평가 배너

- 생성 기준: `docs/domains/agent/REAL_ESTATE_EVALUATION_COPY.md`
- 표현 기준: `docs/layers/ui/screens/realestate-target-detail.md`
- 위치: 지역/단지 상세 최상단
- 시각: 어두운 헤더 또는 고밀도 summary band
- 내용: 커뮤니티 반응, market fact, issueMix, source coverage 기반의 관찰 요약

### Market Fact Timeline

- 실거래, 전세, 매물, 정책, 공급, 뉴스/컬럼 이벤트를 같은 시간축에서 보여줍니다.
- 모든 fact는 provider, `asOf`, `stale`, dataStatus를 함께 표시합니다.
- 실제 데이터가 없으면 fixture를 실제처럼 보이게 늘리지 않고 API 필요 상태를 표시합니다.
- 정책/뉴스 이벤트와 market fact는 색상과 icon으로 구분합니다.

## 후보 기록

새 패턴이 필요하면 페이지 안에서만 임시로 끝내지 말고 여기에 후보로 남깁니다. 오래된 설명을 누적하지 않고 최신 기준만 유지합니다.
