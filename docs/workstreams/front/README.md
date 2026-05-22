# front

너나사(YouBuyFirst)의 사용자 화면을 담당합니다. `front/`는 Vue 3 + Vite + TypeScript 기반 mock UI이며, 커뮤니티 반응과 종목/시장 데이터를 투자 참고용으로 보여주는 제품 화면을 만듭니다.

## 먼저 읽을 것

프론트 작업을 시작할 때는 아래만 먼저 봅니다.

1. `docs/workstreams/front/WIREFRAME_HANDOFF.md`
2. 바꾸려는 화면의 `docs/workstreams/front/screens/*.md`
3. 디자인 판단이 필요하면 `docs/workstreams/front/DESIGN_SYSTEM.md`

아래는 시작 루틴이 아닙니다.

- `docs/workstreams/front/archive/`
- `docs/superpowers/specs/`, `docs/superpowers/plans/`
- `front/public/visual-history/YYYY-MM-DD/index.html`
- Browser/gstack/Playwright 스킬 전문

필요할 때만 파일 1개와 키워드 1개로 좁혀 검색합니다.

## 현재 디자인 기준

대시보드(`/dashboard`)가 현재 가장 완성도가 높은 기준 화면입니다. 새 화면은 대시보드의 정보 밀도, Pretendard 기반 타이포 위계, 작은 링크/태그, 얇은 구분선, 카드 간격을 먼저 따릅니다.

우선순위는 다음 순서입니다.

1. 검색창, 상단 메뉴, 오른쪽 rail의 위치를 안정적으로 유지합니다.
2. 한 화면에 많은 정보를 넣되, 숫자와 상태가 먼저 읽히게 합니다.
3. 사각 카드 반복을 줄이고, 헤더 색/간격/선/배경 톤으로 영역을 구분합니다.
4. 긴 설명문은 도형, 막대, 선 그래프, 칩, 표, timeline 같은 UI 구조로 치환합니다.
5. 탭 첫 화면은 핵심 요약 허브로 만들고, 상세 정보는 별도 route나 하위 상세 화면으로 분리합니다.
6. 금융 차트는 축, 범례, 선 두께, 색 대비를 정돈해 PPT처럼 보이지 않게 합니다.
7. 커뮤니티 반응, 뉴스/공시, 가격 변화가 왜 같이 움직였는지 짧게 연결합니다.
8. 외부 글 제목이 아닌 서비스 문구에서는 `추천`, `사라`, `팔아라`, `수익 보장`, `진입`, `시그널 확정` 같은 투자 자문형 표현을 쓰지 않습니다.

## 담당 화면

- 대시보드
- 종목 목록과 종목 상세
- 뉴스룸
- 인간 지표
- 주요 지표
- 내 포트폴리오
- 오른쪽 rail과 검색/상단 메뉴

화면 구조, route, child detail, fixture/API 후보가 바뀌면 해당 Screen Brief를 최신 기준으로 갱신합니다. 긴 변경 이력은 Screen Brief에 누적하지 않습니다.

## 시각 기록

Visual History는 기본적으로 읽는 자료가 아니라 등록용 산출물입니다. 화면이 의미 있게 바뀌면 캡처와 짧은 설명을 추가해 사용자가 이전 버전과 비교할 수 있게 합니다.

에이전트는 복구, 회귀 비교, 사용자가 특정 과거 버전을 지목한 경우가 아니면 visual history HTML과 이미지 목록을 읽지 않습니다. 새 변경을 기록할 때는 기존 갤러리를 훑지 말고 새 캡처 파일, 날짜별 index, `docs/workstreams/front/VISUAL_CHANGELOG.md`의 상단 대표 행만 갱신합니다.

## 검증

프론트 UI를 바꾸면 가능한 범위에서 확인합니다.

```powershell
npm.cmd run build --prefix front
npm.cmd test --prefix front
git diff --check
```

레이아웃 변경은 Playwright나 Browser로 실제 viewport를 확인합니다. 단, DOM/콘솔 전문을 출력하지 말고 좌표, 스크린샷 경로, 실패 지점만 짧게 남깁니다.

## PR 기준

- 한 PR은 한 front 작업만 소유합니다.
- PR 제목은 `[front][type] 명사형 요약` 형태를 따릅니다.
- PR 본문은 사람이 이해할 수 있게 `무슨 문제를 해결했는지`, `현재 상태`, `검증`, `남은 리스크` 중심으로 씁니다.
- 작업 중 확인한 화면은 visual history 또는 PR 스크린샷으로 추적 가능하게 남깁니다.

## 하지 않는 일

- 실거래, 로그인/보안, OCR 계좌 연동, 운영 배포는 명시 요청 없이 구현하지 않습니다.
- 크롤러 정책, API 계약, 투자 자문처럼 보이는 문구는 임의로 확정하지 않습니다.
- archive 문서, 긴 세션 로그, Browser/gstack 전문을 시작 루틴으로 읽지 않습니다.
