# Front Wireframe Handoff Archive - 2026-05-17

이 문서는 2026-05-17 프론트 와이어프레임 작업의 상세 로그를 보존한 archive입니다.
새 프론트 세션 시작 문서가 아니며, 필요한 경우에만 키워드로 검색해서 봅니다.

권장 검색 예시:

```powershell
rg -n -m 20 "검색어" docs\workstreams\front\archive\WIREFRAME_HANDOFF_2026-05-17.md
```

---

# Front Wireframe Handoff

Last update: 2026-05-17 20:24 KST

## 2026-05-17 20:24 KST - Netlify 정적 공유 설정 추가

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 결정:
  - 지금 단계의 목적은 백엔드 없는 프론트 mock shell을 다른 사람이 URL로 확인하는 것입니다.
  - Vue/Vite 정적 배포 기준으로 Vercel과 Netlify의 preview 기능 차이는 크지 않으므로, 무료 한도/단순 설정이 더 명확한 Netlify를 우선 선택합니다.
- 반영:
  - repo root에 `netlify.toml`을 추가했습니다.
  - Netlify가 GitHub repo root에서 `front`를 base로 잡아 `npm run build` 후 `front/dist`를 publish하도록 설정했습니다.
  - `createWebHistory()` 라우팅 때문에 `/dashboard` 직접 접속/새로고침이 404가 나지 않도록 SPA fallback redirect를 추가했습니다.
- Netlify import 설정:
  - Base directory: `front`
  - Build command: `npm run build`
  - Publish directory: `dist`
  - 위 값은 `netlify.toml`에 들어 있어 Netlify가 자동 인식하는 것을 기대합니다.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과

## 2026-05-17 19:38 KST - 뉴스/리포트/영상/블로그 피드 카드 타이트 정리

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백:
  - 실시간 뉴스, 애널리스트 리포트, 증권 영상 새 글, 블로그와 커뮤니티 링크 카드가 세로로 너무 길어 보입니다.
  - 네 카드가 같은 포맷이므로 카드 높이도 같아야 합니다.
  - 각 행에서 자세히 보기나 전문 링크로 넘어갈 수 있어야 합니다.
- 반영:
  - 네 카드 모두 `.content-feed-card` + `.feed-list` + `.feed-row` 구조로 통일했습니다.
  - 각 카드 목록은 4개 행만 노출하고, 행 높이/제목 말줄임/출처 메타/우측 `전문 ->` 또는 `보기 ->` 액션을 같은 규격으로 맞췄습니다.
  - 뉴스/리포트 mock data에 `url`을 추가하고, 리포트/영상/블로그 카드 헤더에도 외부 자세히 보기 링크를 달았습니다.
  - `.news-macro-grid`는 `grid-auto-rows: 246px`로 맞춰 네 피드 카드의 실제 높이가 동일하게 나오도록 했습니다.
- 시각 기록:
  - `artifacts/front-dashboard-compact-feed-cards.png`
  - `artifacts/front-visual-history/FV-20260517-1938-compact-feed-cards-dashboard.png`
  - `front/public/visual-history/2026-05-17/FV-20260517-1938-compact-feed-cards-dashboard.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - Chrome headless CDP: 네 카드 모두 높이 `246px`, 각 4행, 각 4개 외부 링크 확인

## 먼저 읽기

이 파일은 프론트 작업 로그입니다. 새 세션에서 전문을 처음부터 끝까지 읽는 용도가 아닙니다.

- 처음에는 이 `먼저 읽기` 섹션과 바로 아래 최신 항목 1-2개만 봅니다.
- 예전 화면을 비교해야 할 때만 `rg "<키워드>" docs/workstreams/front/WIREFRAME_HANDOFF.md`로 필요한 항목을 찾습니다.
- 캡처 목록은 `docs/workstreams/front/VISUAL_CHANGELOG.md`를 먼저 봅니다.
- 현재 브랜치/worktree는 `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`입니다.
- 현재 확인 URL은 `http://127.0.0.1:5174/dashboard`입니다.
- Notion의 `Front Visual Versions`는 HTML 갤러리 바로가기 카드입니다. DB, 긴 토글, 전문 로그, 이미지 본문을 넣지 않습니다.
- 자세한 기록의 원본은 이 repo 문서이고, 필요한 부분만 키워드로 찾아봅니다.

## 이미지 기록 방식

용어를 간단히 정리하면 아래와 같습니다.

- `front/public/visual-history/index.html`: 날짜별 갤러리 입구입니다. 여기에는 날짜 목록만 둡니다.
- `front/public/visual-history/YYYY-MM-DD/index.html`: 해당 날짜의 대표 스크린샷을 카드처럼 보여주는 페이지입니다.
- `front/public/visual-history/YYYY-MM-DD/*.png`: 그 날짜에 사용자가 비교할 만한 대표 스크린샷입니다.
- `artifacts/`: 작업 중 찍은 캡처를 넉넉히 보관하는 폴더입니다. 작은 수정, 실패한 시도, 중간 비교 이미지도 여기에 둘 수 있습니다.
- `artifacts/front-visual-history/`: Notion/갤러리에 연결할 대표 버전 원본을 따로 모아두는 폴더입니다.
- Notion에는 모든 이미지를 다 올리지 않고, 주요 화면 변화만 요약합니다. 세부 캡처는 repo의 `artifacts/`와 `VISUAL_CHANGELOG.md`에서 찾습니다.

즉, 사용자가 빠르게 볼 곳은 `front/public/visual-history/index.html`에서 날짜를 고른 뒤 들어가는 날짜별 갤러리이고, 작업자가 오래된 근거를 찾을 곳은 `VISUAL_CHANGELOG.md`와 `artifacts/`입니다.

## 메모리 보호 원칙

- 긴 문서는 시작 루틴으로 전문 출력하지 않습니다.
- Notion은 HTML 갤러리 링크와 짧은 규칙만 유지합니다.
- Notion DB는 쓰지 않습니다. 사용자가 직접 보기에는 HTML 갤러리가 더 낫기 때문입니다.
- 새 세션은 `WIREFRAME_HANDOFF.md` 상단과 최신 항목 1-2개만 보고, 과거 맥락은 `rg`로 좁혀 찾습니다.
- 오래된 캡처는 Notion에 복사하지 않고 `VISUAL_CHANGELOG.md`와 `artifacts/` 경로로 추적합니다.

## Codex 디자인/구현 기준

프론트 디자인과 구현은 기본적으로 Codex가 `front/` 코드에서 함께 진행합니다. 정본은 외부 디자인 파일이 아니라 merge된 코드, fixture, 화면 문구, API 후보, 검증 기록입니다.

Figma AI, Stitch 같은 외부 디자인 도구는 기본 작업 흐름이 아닙니다. 사용자가 명시적으로 요청할 때만 참고 시안 탐색용으로 쓰고, 선택한 방향은 Codex가 작은 front PR로 다시 코드에 반영합니다. 외부 도구 산출물은 정본이 아니며, 그대로 구현하지 않습니다.

Codex가 디자인을 다듬을 때는 먼저 현재 `/dashboard` 화면과 fixture를 보고, 화면 밀도, 정보 우선순위, 색/타이포/간격, 카드/차트 형태를 코드에서 조정합니다. 디자인 변경은 가능한 한 한 화면 또는 한 컴포넌트 단위의 작은 PR로 끊습니다.

## 2026-05-17 15:20 KST - 검색창 결합감, 비율 보존 그래프, 다크 글래스 카드, 풀폭 피드 헤더 보정

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백:
  - 검색 아이콘과 검색칸이 서로 다른 박스처럼 끊겨 보이면 안 됩니다.
  - 커뮤니티 그래프를 단순히 세로로 늘리면 글자와 선까지 찌그러져 보입니다.
  - 반응 카드는 밝은 흰 박스가 아니라 약간 어두운 계열의 글래스 느낌이어야 합니다.
  - 피드 제목 영역은 카드 안쪽에 작은 직사각형이 아니라 카드 위쪽 전체 폭을 칠해야 합니다.
- 반영:
  - 검색 아이콘을 입력창 내부의 작은 회색 아이콘 버튼처럼 바꾸고, 왼쪽 전체 칸을 칠하던 형태를 제거했습니다.
  - 커뮤니티 그래프 SVG를 `viewBox="0 0 1200 520"`로 재구성하고 `preserveAspectRatio="xMidYMid meet"`로 바꿔 비율이 찌그러지지 않게 했습니다.
  - `wideY()` 좌표 매핑과 grid/axis 좌표를 새 viewBox에 맞게 다시 잡고, CSS 높이는 `232px`로 낮춰 과도한 세로 확대를 되돌렸습니다.
  - 반응 TOP3 카드는 다크 글래스 패널로 조정했습니다. 흰 카드 대신 반투명 다크 면, 얇은 빨강/파랑 액센트, 밝은 텍스트를 사용합니다.
  - 피드 패널은 `.panel.content-feed-card`로 specificity를 올려 기존 `.panel` padding이 다시 먹지 않게 했고, 헤더 밴드가 카드 맨 위 전체 폭을 차지하도록 수정했습니다.
- 최신 캡처:
  - `artifacts/front-dashboard-search-chart-darkglass-feed-fixed.png`
  - `artifacts/front-dashboard-feed-header-fullwidth-fixed.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 15:08 KST - 검색 아이콘, 커뮤니티 그래프 확대, 글래스 반응 카드, 피드 헤더 밴드

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백:
  - 검색창의 `KR`은 깨져 보이기도 하고 한국 주식만 검색하는 것처럼 읽히므로 검색 아이콘이 낫습니다.
  - 커뮤니티 지표 비교 그래프의 글씨와 축이 너무 작아 잘 안 보이고, 박스 높이도 주변 카드와 맞추는 편이 좋습니다.
  - 종목 반응 한눈에는 어두운 다크 카드가 과하고 올드해 보여서 심플한 글래시 카드가 낫습니다.
  - 종목 반응은 전체 1~6위보다 `언급+긍정 TOP 3`, `언급+부정 TOP 3`로 나누는 편이 좋습니다.
  - 실시간 뉴스/리포트/증권 영상/블로그 카드 간격을 더 벌리고, 제목 영역은 색이 다른 헤더 밴드로 실험해볼 수 있습니다.
- 반영:
  - 검색창 왼쪽 `KR` pseudo text를 제거하고 `.search-icon` CSS 아이콘으로 바꿨습니다.
  - 종목 반응 데이터는 기존 mock을 유지하되 `mentionCount * bullish/bearish ratio`로 긍정/부정 TOP 3를 계산해 렌더링합니다.
  - 반응 카드는 딥 다크 카드에서 밝은 글래스 패널로 되돌리고, 그룹별 빨강/파랑 액센트만 얇게 남겼습니다.
  - 카드 내부에서 종목명이 잘리지 않도록 점수 영역을 오른쪽 고정 칸에서 종목명 아래 한 줄로 내렸습니다.
  - 커뮤니티 그래프 박스는 `min-height: 410px`, SVG는 `348px`로 키워 주변 반응 카드 높이와 더 맞췄고, 축/레이블/선 굵기를 키웠습니다.
  - 뉴스/리포트/영상/블로그 4개 패널에 `.content-feed-card` 헤더 밴드를 추가하고, 카드 간 grid gap을 `34px 30px`로 넓혔습니다.
- 최신 캡처:
  - `artifacts/front-dashboard-glass-reaction-feed-headers-desktop.png`
  - `artifacts/front-dashboard-feed-headers-tall.png`
- 브라우저 확인:
  - Chrome headless `1410x980` 및 `1410x1800`에서 `http://127.0.0.1:5174/dashboard` 캡처 확인
  - 검색 아이콘 표시, 커뮤니티 그래프 확대, 긍정/부정 TOP3 카드 구분, 피드 헤더 밴드 표시 확인
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 14:51 KST - 종목 반응 카드 다크톤, 반응 비율 막대 대비 강화

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백:
  - 종목 반응 카드 색감이 더 세련되어야 하고, 어두운 색 계열도 괜찮습니다.
  - 매수/매도처럼 보이는 반응 막대는 차이가 더 눈에 띄고 세련되어야 합니다.
- 반영:
  - `종목 반응 한눈에` 카드 6개를 밝은 흰 박스에서 딥 네이비/딥 틸/딥 브라운 계열의 어두운 카드로 변경했습니다.
  - 카드마다 `--rank-accent`, `--rank-glow`, `--rank-base` 변수를 두어 같은 박스 반복처럼 보이지 않게 톤 변주를 만들었습니다.
  - 순위 숫자는 큰 워터마크와 우측 상단 랭크 배지로 나뉘어 보이게 유지했습니다.
  - 긍정/부정/중립 비율 막대는 `5px`에서 `11px`로 키우고, 긍정은 국내 주식 UI에 가까운 빨강, 부정은 파랑, 중립은 슬레이트로 조정했습니다.
  - UI 문구는 투자 자문처럼 보이지 않도록 계속 `긍정 반응`, `부정 반응`, `중립·기타` 기준으로 남겼습니다.
- 최신 캡처:
  - `artifacts/front-dashboard-reaction-dark-bars-desktop.png`
- 브라우저 확인:
  - Chrome headless `1410x980`에서 `http://127.0.0.1:5174/dashboard` 캡처 확인
  - 반응 카드 6개가 3x2로 유지되고, 반응 비율 막대가 카드 내부에 정상 표시됨
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 00:10 KST - 토스식 오른쪽 레일/로그인/탭 화면, 그래프 컨트롤 재배치

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백:
  - 좌우 여백을 더 줄이고, 다른 항목끼리의 간격은 더 벌려야 합니다.
  - 커뮤니티 지표 비교의 상위/하위/격차 KPI 박스는 그래프와 중복되므로 제거해야 합니다.
  - `일/주/월/년` 컨트롤은 그래프 박스 안으로 들어가야 합니다.
  - 오른쪽 탭의 `지표`, `관심` 화면이 필요합니다.
  - 상단 메뉴는 사이트 중앙에 와야 하고, 오른쪽 상단 로그인, 오른쪽 끝 확장 레일, 오른쪽 하단 라이트/다크 토글이 필요합니다.
  - 로고/브랜드 클릭 시 대시보드로 돌아가야 합니다.
- 반영:
  - `return-kpi-row` DOM을 제거했습니다. 그래프 아래/위에 반복되던 네이버 종토방 `+4.8%`, 디시 주식 `-1.2%` KPI 박스는 더 이상 렌더링되지 않습니다.
  - `일/주/월/년` 탭을 `.community-graph` 내부 `.in-graph-tabs`로 이동했습니다. `1D/7D/1M/3M/1Y` 기간 버튼은 그래프 밖 우측 컨트롤로 유지했습니다.
  - `.dashboard-content-flow`는 세로/가로 gap을 `24px`로 조정해 항목끼리 붙는 느낌을 줄였습니다.
  - 오른쪽 drawer에 `drawer-metric-panel`과 `drawer-watch-panel`을 추가해 `지표`/`관심` 탭 화면에 해당하는 mock preview를 만들었습니다.
  - 상단 브랜드를 `RouterLink to="/dashboard"`로 변경했습니다. `너나사 YouBuyFirst` 클릭 시 대시보드로 이동합니다.
  - 상단 nav는 `1fr / auto / 1fr` 구조로 다시 잡아 중앙에 배치했습니다. 데스크톱 측정 기준 nav center는 `690`, 오른쪽 레일 제외 작업영역 중심과 맞습니다.
  - 상단 오른쪽에 `로그인` 버튼을 추가했습니다.
  - Toss 스타일의 오른쪽 끝 `edge-rail`을 추가했습니다. 확장 버튼, 내 투자, 관심, 최근 본, 실시간, 하단 theme toggle이 있습니다.
  - edge rail과 topbar action이 겹치지 않도록 topbar width/margin을 조정했습니다. theme toggle은 rail 하단에 위치합니다.
- 최신 캡처:
  - `artifacts/front-dashboard-toss-rail-final-desktop.png`
  - `artifacts/front-dashboard-toss-rail-dense-desktop.png`
  - `artifacts/front-dashboard-toss-rail-dense-scrolled.png`
  - `artifacts/front-dashboard-toss-rail-dense-mobile.png`
- 브라우저 측정:
  - desktop: `clientWidth=1410`, document horizontal overflow 없음
  - top nav: `left=484 right=896 center=690`
  - topbar actions: `right=1368`, rail `left=1372`, overlap 없음
  - rail: `left=1372 right=1410 width=38`
  - theme toggle: `bottom=968`, rail bottom `980`, 하단 배치 확인
  - content: `left=4 right=1090 width=1086`
  - graph: `left=4 right=1090 width=1086`, legend graph 밖 초과 없음
  - `returnKpi=false`, `drawerMetric=true`, `drawerWatch=true`, `.community-graph .graph-legend em=0`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
- 서버 상태: Chrome CDP `9230`은 종료했고, `5174` Vite dev server만 listen 중입니다.

## 2026-05-16 23:51 KST - 그래프 overflow 방지, 범례 내부 이동, 좌우 여백 축소

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백: 그래프가 박스 밖으로 초과했고, 커뮤니티 수익률 숫자는 그래프 안에도 있으니 아래 반복 표시는 제거해야 합니다. 색상 범례는 그래프 박스 안으로 들어가야 하며, `종목 반응 한눈에`와 `실시간 주요 지표`는 너무 붙어 보였습니다. 사이트 전체 좌우 여백은 더 줄여도 됩니다.
- 반영:
  - 커뮤니티 그래프 SVG에 `preserveAspectRatio="none"`을 적용해 박스 안을 꽉 채우되, `.community-graph`와 `svg` 모두 `overflow: hidden`으로 닫았습니다.
  - 오른쪽 y축 숫자와 series end label 좌표를 박스 안쪽으로 당겼고, `endLabelX()`로 끝값 라벨이 우측 경계를 넘지 않도록 제한했습니다.
  - 그래프 아래에 있던 커뮤니티별 수익률 숫자 반복 표시는 제거했습니다.
  - 색상 범례는 `.community-graph` 내부 오른쪽 위 pill로 이동했고, 범례 안 `em` 수익률 값은 없습니다.
  - 페이지 프레임 좌우 여백을 데스크톱 기준 약 6px 수준까지 줄였습니다: `width: min(1410px, calc(100% - 12px))`.
  - 본문 max width를 `1120px`로 넓혔고, `종목 반응 한눈에`와 `실시간 주요 지표` 사이 column gap은 `24px`로 벌렸습니다.
- 최신 캡처:
  - `artifacts/front-dashboard-contained-legend-tight-desktop.png`
  - `artifacts/front-dashboard-contained-legend-desktop.png`
  - `artifacts/front-dashboard-contained-legend-scrolled.png`
  - `artifacts/front-dashboard-contained-legend-mobile.png`
- 브라우저 측정:
  - desktop frame: `left=6 right=1404 width=1398`
  - content: `left=6 right=1116 width=1110`
  - graph: `left=6 right=1116 width=1110 height=286`
  - svg: `left=8 right=1114 width=1106 height=282`
  - legend: `left=762 right=1105 width=343`, graph 밖 초과 없음
  - `.return-area=0`, `.community-graph .graph-legend em=0`, document horizontal overflow 없음
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
- 서버 상태: Chrome CDP `9230`은 종료했고, `5174` Vite dev server만 listen 중입니다.

## 2026-05-16 23:36 KST - 큰 카드 프레임 제거, 와이드 그래프 viewBox, 밀도형 2열 배치

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백: 커뮤니티 지표 비교 그래프 박스 좌우 여백이 아직 많고, 본문 전체 크기를 더 줄여 한눈에 많은 지표가 보여야 합니다. `실시간 주요 지표`처럼 `커뮤니티 지표 비교`와 `종목 반응 한눈에`도 큰 박스 밖으로 빼야 하며, 한 줄에 박스 하나일 필요는 없습니다.
- 반영:
  - `커뮤니티 지표 비교`의 `panel` 외곽 프레임을 제거했습니다. 제목/컨트롤은 `실시간 주요 지표`처럼 섹션 바깥에 놓고, 그래프/KPI만 얇은 데이터 블록으로 남겼습니다.
  - `종목 반응 한눈에`도 `panel` 프레임을 제거했습니다.
  - 커뮤니티 그래프는 `viewBox="0 0 1200 320"`으로 바꿔 SVG 자체 비율에서 생기던 좌우 여백을 줄였습니다. line plot bbox는 `x=71 width=1106`으로, 이전보다 훨씬 넓게 박스를 씁니다.
  - 본문 폭을 `1080px`, 오른쪽 drawer를 `274px`로 유지해 왼쪽 작업 영역을 더 크게 씁니다.
  - 데스크톱에서 `종목 반응 한눈에`와 `실시간 주요 지표`가 같은 행에 놓이도록 `dashboard-content-flow`를 2열 grid로 바꿨습니다. 모바일/좁은 화면에서는 1열로 내려갑니다.
  - 종목 원, 지표 카드, 섹션 제목, pill, detail link, indicator sparkline을 더 작게 조정했습니다.
- 최신 캡처:
  - `artifacts/front-dashboard-wide-viewbox-dense-desktop.png`
  - `artifacts/front-dashboard-wide-viewbox-dense-scrolled.png`
  - `artifacts/front-dashboard-wide-viewbox-dense-mobile.png`
  - 이전 비교용: `artifacts/front-dashboard-unframed-dense-grid-desktop.png`
- 브라우저 측정:
  - desktop: `clientWidth=1410`, `scrollWidth=1410`, content `left=21 width=1080`, drawer `left=1121 width=274`
  - graph: box `width=1080 height=286`, svg `width=1076 height=282`, viewBox `0 0 1200 320`, line bbox `x=71 width=1106`, `.return-area=0`
  - desktop dense row: reaction panel `left=21 width=470`, indicator section `left=507 width=594`, same row
  - mobile: `clientWidth=390`, `scrollWidth=390`, content `left=12 width=366`, horizontal overflow 없음
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
- 서버 상태: Chrome CDP `9230`은 종료했고, `5174` Vite dev server만 listen 중입니다.

## 2026-05-16 23:21 KST - 그래프 밀도/전체 컴팩트 조정

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백: 커뮤니티 비교 지표 그래프 박스에 그래프가 더 꽉 차야 하고, 전반적으로 크기와 간격이 작아져 한눈에 여러 내용이 보여야 합니다. 왼쪽 여백은 더 채워도 됩니다.
- 반영:
  - `dashboard-content-flow`를 `max-width: 1020px`로 넓혀 본문 왼쪽 여백을 더 채웠습니다.
  - 오른쪽 패널은 이전 grid/sticky 구성을 유지하면서 `292px`에서 `286px`로 살짝 줄였습니다.
  - 커뮤니티 그래프 SVG 좌표계를 더 넓게 사용하도록 `wideX`/`wideY`와 축 좌표를 조정했습니다.
  - 커뮤니티 그래프 박스는 `min-height: 326px`, padding `8px 8px 2px`, svg height `306px`로 줄여 plot이 더 꽉 차 보이게 했습니다.
  - 카드 padding, dashboard gap, KPI box gap, bubble size, indicator card height, mobile page padding을 줄였습니다.
- 최신 캡처:
  - `artifacts/front-dashboard-compact-graph-desktop.png`
  - `artifacts/front-dashboard-compact-graph-scrolled.png`
  - `artifacts/front-dashboard-compact-graph-mobile-top.png`
  - `artifacts/front-dashboard-compact-graph-mobile-graph.png`
- 브라우저 측정:
  - desktop: `clientWidth=1410`, `scrollWidth=1410`, content `left=44 width=1020 center=554`, drawer `left=1099 width=286`, drawer position `sticky`
  - graph: box `width=986 height=326`, svg `width=968 height=306`, `.return-area=0`, `.spark-area=5`, `.series-end-label=4`, `.y-axis-right=3`
  - mobile: `clientWidth=390`, `scrollWidth=390`, content `left=12 width=366`, graph `width=336 height=226`, horizontal overflow 없음
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
- 서버 상태: Chrome CDP `9230`은 종료했고, `5174` Vite dev server만 listen 중입니다.

## 2026-05-16 23:13 KST - 본문/오른쪽 패널 위치 되돌림, 커뮤니티 그래프 축 정리

- 작업 브랜치/worktree: `codex/front-dashboard-content` / `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자가 "정석 중앙정렬보다 이전처럼 살짝 왼쪽에 본문, 오른쪽 패널이 grid 안에 붙는 구도가 더 낫다"고 판단해서, 본문/오른쪽 패널 배치만 이전 상태로 되돌렸습니다.
- 되돌린 것: `.dashboard-main-layout`을 `minmax(0, 1fr) 292px` grid로 복구, `.dashboard-content-flow`를 `max-width: 960px` + `justify-self: center`로 복구, `.side-drawer`를 `position: sticky; top: 96px`로 복구했습니다. fixed drawer와 viewport 정확 중앙 정렬은 제거했습니다.
- 유지한 것: sticky top ticker, `라이징 스타` 오른쪽 패널 이동, `종목 반응 한눈에` reaction panel, 주요 지표 sparkline의 상승 red/하락 blue 면적, 커뮤니티 그래프 기간 탭(`일/주/월/년`, `1D/7D/1M/3M/1Y`)은 유지했습니다.
- 커뮤니티 지표 비교 그래프는 사용자의 피드백대로 면적 채움을 제거했습니다. 대신 y축/x축, zero line, 우측 numeric tick label, tabular number, 얇아진 line/dot 스타일을 추가해 더 차트 툴 같은 느낌으로 정리했습니다.
- 최신 캡처:
  - `artifacts/front-dashboard-layout-revert-chart-axis-desktop.png`
  - `artifacts/front-dashboard-layout-revert-chart-axis-desktop-scrolled.png`
  - `artifacts/front-dashboard-layout-revert-chart-axis-mobile.png`
  - `artifacts/front-dashboard-layout-revert-chart-axis-mobile-graph.png`
- 브라우저 측정:
  - desktop: `clientWidth=1410`, `scrollWidth=1410`, content `left=70 width=960 center=550`, drawer `left=1073 width=292`, drawer position `sticky`, horizontal overflow 없음
  - chart: `.return-area=0`, `.spark-area=5`, `.series-end-label=4`, `.chart-y-axis=true`, `.y-axis-right=3`
  - mobile: `clientWidth=390`, `scrollWidth=390`, drawer position `static`, horizontal overflow 없음
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
- 서버 상태: Chrome CDP `9230`은 종료했고, `5174` Vite dev server만 listen 중입니다. `52341`은 listen 중이 아닙니다.

마지막 갱신: 2026-05-16 22:57 KST

이 문서는 front 작업 채팅이 끊겨도 바로 이어 하기 위한 현재 정본입니다. 새 front 세션은 이 파일을 먼저 보고, 과거 `docs/superpowers/` archive는 필요한 근거가 있을 때만 파일 1개와 키워드 1개로 좁혀 봅니다.

## 현재 정본

- 현재 작업 worktree: `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 현재 브랜치: `codex/front-dashboard-content`
- 확인 URL: `http://127.0.0.1:5174/dashboard`
- 유지할 dev server: `5174`, command line이 `.worktrees\front-dashboard-content\front`를 가리키는 Vite
- 종료 대상: `52341` Superpowers visual companion server는 이전에 종료했음
- 현재 front 방향: YASUN.GG처럼 검은 상단바, 밝은 작업면, 얇은 구분선, 작은 보조 텍스트, Pretendard 기반의 깔끔한 금융/커뮤니티 반응 대시보드

주의:

- `C:\agents\YouBuyFirst` 루트 worktree는 현재 `codex/front-dark-dashboard-design`이며 이번 dashboard 구현 정본이 아닙니다.
- `5174` 화면 기준 작업은 반드시 위 worktree에서만 이어갑니다.
- 다른 서버가 열려 있으면 먼저 `Get-NetTCPConnection`과 process command line으로 어느 worktree가 띄운 서버인지 확인합니다.

## 최근 사용자 피드백

- 네모 박스가 많고 AI가 만든 것 같은 UI를 줄여야 합니다.
- 글씨체가 촌스럽고 글자 크기가 전반적으로 커 보여 Pretendard 기반으로 정리해야 합니다.
- YASUN.GG를 많이 참고하되, 투자 자문처럼 보이는 표현이나 실거래 유도 UI는 피합니다.
- 종목 비교는 한 종목이 큰 영역을 차지하지 않고 여러 종목을 한 축에서 원형으로 비교해야 합니다.
- 커뮤니티 지표 비교는 그래프로 한 번에 비교하는 구조를 유지해야 합니다. 막대/리스트로 바꾸면 안 됩니다.
- 와이어프레임 구조를 무조건 유지할 필요는 없습니다.
- 검색창과 필터 chip이 상단에서 뜬금없이 떠 보이면 안 됩니다. 중앙 hero를 억지로 둘 필요도 없습니다.
- 우상단에는 `지금 언급 급상승 종목`이 눈에 띄게 보여야 합니다.
- 아래에는 `실시간 주요 지표`, `실시간 뉴스`, YASUN 매크로 페이지처럼 여러 지표를 자세히 보는 파트가 필요합니다.
- `커뮤니티 반응 대시보드` 큰 제목과 급상승 종목은 상단에서 내용이 겹치므로 큰 제목 hero는 제거합니다.
- 검색창은 어떤 카드 안에 넣지 않고 야선처럼 독립 배치합니다.
- 각 주요 섹션에는 `자세히 보기 →` 링크가 있어야 합니다.
- 종목 원형 그래프에는 `긍정 반응`, `부정 반응`, `중립·기타` 색상 범례가 필요합니다. 빨강/파랑 색은 쓰되 매수/매도 행동 지시처럼 보이는 라벨은 쓰지 않습니다.
- Toss screener처럼 오른쪽에서 탭으로 여는 느낌의 `라이브 패널`을 둡니다.
- 사이트가 정적인 mock처럼 보이지 않도록 live ticker와 pulse animation을 둡니다.
- 상단 nav에 `주요 지표`와 `내 포트폴리오` 탭이 필요합니다. `포트폴리오 준비 중` 문구는 제거합니다.
- 홈의 매크로 상세는 `주요 지표` 페이지와 겹치므로 홈에서는 빼고, `/indicators`에서만 자세히 봅니다.
- 오른쪽 패널의 `뉴스` 탭은 홈의 `실시간 뉴스`와 겹치므로 제거하고, 패널 탭은 `반응`/`지표`/`관심`으로 정리합니다.
- `자세히 보기 →`는 작은 글씨로 낮춰야 합니다.
- 긴 뉴스 문장과 큰 텍스트는 줄이고, 중앙 종목 반응 원형 그래프는 더 심플하게 둡니다.
- `라이징 스타`와 `커뮤니티 지표 비교`는 사이트 첫 인상을 잡는 정보이므로 본문 최상단으로 올립니다.
- `전체 언급`/`지연 시세`/`관찰 범위`는 설명 없이 큰 박스로 뜨면 의미가 약하므로 작은 메타 chip으로 줄입니다.
- 지표 슬라이드는 본문 중간이 아니라 상단 메뉴 바로 아래에 붙이고, 스크롤 시 메뉴와 함께 sticky로 따라오게 둡니다.
- 오른쪽 탭은 sticky로 따라다니지만, 본문은 오른쪽 탭을 제외한 작업 영역 안에서 중앙 정렬되어야 합니다.
- `커뮤니티 지표 비교`는 본문에서 더 넓고 전문적인 그래프처럼 보여야 합니다.
- `라이징 스타`는 본문보다 오른쪽 탭/패널 쪽으로 빼는 방향이 좋습니다.
- 지표 그래프는 선만 두지 말고 상승은 빨강, 하락은 파랑, 내부 면적은 연한 색으로 채운 sparkline이 좋습니다.
- 커뮤니티 수익 비교는 단순 선보다 상세한 선/면적 그래프로 만들고, `일`/`주`/`월`/`년`과 `1D`/`7D`/`1M`/`3M` 같은 기간 버튼이 필요합니다.
- `종목 반응 한눈에`는 단독으로 떠 보이면 안 되고, 패널 안에 담겨야 합니다.

## YASUN.GG 확인 결과

2026-05-16 21:14 KST에 실제 렌더링을 9초 기다린 뒤 내부 스크롤 컨테이너를 찾아 스크롤별로 캡처했습니다.

- YASUN은 `body`가 아니라 `absolute inset-0 overflow-y-auto flex flex-col` 내부 컨테이너가 스크롤됩니다.
- 상단 구조: 검은 nav bar, 큰 중앙 hero, 작은 pill, 긴 검색창, 시장/야간 시세/뉴스 리스트
- 하단 구조: `주요 기능` 3x2 카드, `실시간 종목 랭킹` 테이블, 넓은 footer
- 참고 캡처:
  - `artifacts/yasun-reference-wait-top-scroll-y0.png`
  - `artifacts/yasun-reference-wait-mid-scroll-y760.png`
  - `artifacts/yasun-reference-wait-lower-scroll-y1320.png`
  - `artifacts/yasun-reference-wait-bottom-scroll-y1609.png`

2026-05-16 21:43 KST에는 `https://yasun.gg/macro`도 9초 기다린 뒤 내부 스크롤 컨테이너로 확인했습니다.

- 매크로 페이지 구조: 작은 페이지 헤더, 핵심 지표, 지수/금리/환율/원자재 미니 차트, 카테고리 필터, 상세 지표 그리드, 히트맵
- 참고 캡처:
  - `artifacts/yasun-macro-reference-macro-top-y0.png`
  - `artifacts/yasun-macro-reference-macro-mid-y760.png`
  - `artifacts/yasun-macro-reference-macro-lower-y1500.png`
  - `artifacts/yasun-macro-reference-macro-bottom-y2400.png`

## 현재 구현 상태

- 위치: `front/`
- 기술: Vue 3 + Vite + TypeScript + Vue Router
- 상태: fixture/mock 기반 dashboard content shell
- 실제 backend API 연결: 아직 없음
- 차트 라이브러리: 아직 확정하지 않음. 현재 커뮤니티 비교는 SVG line graph fixture입니다.

주요 변경:

- `front/src/styles.css`를 기존 dark override 누적 구조에서 Pretendard 기반 light/YASUN 스타일로 정리했습니다.
- `front/src/App.vue` 상단바를 검은 nav bar + 작은 상태 pill 구조로 바꿨습니다.
- `DashboardPage.vue` 상단을 좌측 workbench와 우측 `지금 언급 급상승 종목` 패널로 재배치했습니다.
- 이후 상단 중복 피드백에 따라 큰 `커뮤니티 반응 대시보드` 제목 카드는 제거했고, 검색창/필터는 독립 검색 영역으로 분리했습니다.
- Toss screener를 참고한 오른쪽 `라이브 패널`을 추가했고, 반응/지표/관심 tab mock을 둡니다.
- live ticker와 pulse animation을 추가해 실시간으로 값이 변하는 느낌을 냅니다.
- `실시간 주요 지표`, `실시간 뉴스` mock 섹션을 홈에 두고, 매크로 상세는 `/indicators` page로 분리했습니다.
- `주요 지표` route/page와 `내 포트폴리오` route label/content를 추가했습니다.
- 각 주요 섹션에는 `자세히 보기 →` 링크를 추가했습니다.
- 종목 원형 비교에는 빨강/파랑 기반 `긍정 반응`/`부정 반응`/`중립·기타` 범례를 추가했습니다.
- 이후 홈 중복 피드백에 따라 `macro-detail`과 홈의 `macro-metric-card`는 제거했고, live news 문장은 짧은 headline 중심으로 줄였습니다.
- `자세히 보기 →` 링크는 11px/24px로 낮추고, 종목 원형 bubble은 112px의 얇은 링과 약한 그림자로 단순화했습니다.
- 이후 첫 화면 흡인력 피드백에 따라 `라이징 스타`와 `커뮤니티 지표 비교`를 `dashboard-content-flow`의 첫 섹션으로 올렸습니다.
- 기존 큰 `signal-strip`은 제거하고 `dashboard-meta-strip` chip으로 축소했습니다. `언급 합계`는 현재 fixture 종목들의 언급수 합계, `지연 시세`는 stale quote 수, `관찰`은 ranking 대상 종목 수입니다.
- `live-ticker`는 `DashboardPage.vue`에서 `App.vue` 상단바 내부로 이동했습니다. `topbar`는 sticky이며 ticker가 메뉴 바로 아래에 붙습니다.
- 이후 본문 정렬/그래프 피드백에 따라 `라이징 스타` 리스트는 오른쪽 `drawer-rising-stars` 카드로 이동했습니다.
- `dashboard-content-flow`는 오른쪽 sticky drawer를 제외하고 viewport 중심에 맞도록 `max-width: 920px`로 중앙 정렬됩니다.
- `커뮤니티 지표 비교`는 본문 첫 와이드 카드가 되었고, SVG viewBox를 `0 0 720 320`으로 키웠으며 KPI 3개, 세로/가로 grid, x축 라벨을 추가했습니다.
- 이후 화면 중심 피드백에 따라 `dashboard-content-flow`를 `max-width: 920px`로 조정하고, 오른쪽 패널을 fixed `right: 4px`로 이동해 본문 중심이 viewport 중심과 일치하도록 했습니다.
- 주요 지표 카드의 sparkline은 상승 `--market-up` 빨강, 하락 `--market-down` 파랑으로 바꾸고, `.spark-area` 면적 채움을 추가했습니다.
- 커뮤니티 그래프에는 `.return-area`, `.series-end-label`, `return-range-tabs`(`일`/`주`/`월`/`년`)와 기간 버튼(`1D`/`7D`/`1M`/`3M`/`1Y`)을 추가했습니다.
- `종목 반응 한눈에`는 `reaction-panel` 카드 안으로 넣었습니다.
- 종목 비교 원형 bubble rail과 커뮤니티 line graph 구조는 유지했습니다.
- 모바일에서는 문서 전체 가로 overflow가 생기지 않고, 종목 원형 rail만 내부 가로 스크롤됩니다.
- 테스트에 Pretendard, `--surface` 토큰, 오래된 dark radial background 제거, 신규 지표/뉴스/오른쪽 패널/홈 매크로 중복 제거/상단 insight 순서/sticky ticker/와이드 커뮤니티 그래프/라이징 스타 drawer 이동/면적 그래프/중앙 정렬 기대값을 추가했습니다.

## 주요 파일

- `front/src/App.vue`: 상단 nav bar, 서비스 상태 pill, sticky live ticker
- `front/src/router/routes.ts`: `/indicators` route 추가
- `front/src/pages/DashboardPage.vue`: 독립 검색, 오른쪽 live drawer, drawer 라이징 스타, 주요 지표, 뉴스, 종목 원형 비교, 와이드 커뮤니티 지표 그래프
- `front/src/pages/IndicatorsPage.vue`: 주요 지표/매크로 상세 mock page
- `front/src/pages/PortfolioPage.vue`: `내 포트폴리오` mock page
- `front/src/fixtures/dashboard-summary.json`: 주요 지표, live news, macro metrics, rising stars, 커뮤니티 mock series, 확인 필요 항목
- `front/src/fixtures/portfolio-disabled.json`: 내 포트폴리오 mock holdings
- `front/src/fixtures/reaction-ranking.json`: 종목별 원형 비교 mock ranking
- `front/src/fixtures/quote-snapshots.json`: 가격 상태 placeholder
- `front/src/__tests__/shell.spec.ts`: 라우트, mock data, dashboard 구조, Pretendard/YASUN 스타일 회귀 테스트
- `front/src/styles.css`: Pretendard 기반 light/YASUN dashboard 스타일

## 최신 캡처

- 이전 상태 참고: `artifacts/front-dashboard-before-yasun-pass.png`
- YASUN 대기/스크롤 참고: `artifacts/yasun-reference-wait-*.png`
- 현재 desktop: `artifacts/front-dashboard-yasun-pass-desktop-final.png`
- 현재 mobile: `artifacts/front-dashboard-yasun-pass-mobile-fixed.png`
- 현재 full page: `artifacts/front-dashboard-yasun-pass-full-final.png`
- 최신 desktop: `artifacts/front-dashboard-macro-news-pass-desktop.png`
- 최신 mobile: `artifacts/front-dashboard-macro-news-pass-mobile.png`
- 최신 full page: `artifacts/front-dashboard-macro-news-pass-full.png`
- 최신 drawer/tabs desktop: `artifacts/front-dashboard-drawer-tabs-pass-desktop.png`
- 최신 drawer/tabs mobile: `artifacts/front-dashboard-drawer-tabs-pass-mobile.png`
- 최신 중복 정리 desktop: `artifacts/front-dashboard-dedupe-polish-desktop.png`
- 최신 중복 정리 mobile: `artifacts/front-dashboard-dedupe-polish-mobile.png`
- 최신 상단 insight desktop: `artifacts/front-dashboard-top-insights-desktop.png`
- 최신 상단 insight scrolled: `artifacts/front-dashboard-top-insights-desktop-scrolled.png`
- 최신 상단 insight mobile: `artifacts/front-dashboard-top-insights-mobile.png`
- 최신 와이드 커뮤니티 desktop: `artifacts/front-dashboard-wide-community-final-desktop.png`
- 최신 와이드 커뮤니티 mobile: `artifacts/front-dashboard-wide-community-final-mobile.png`
- 최신 면적 그래프 desktop: `artifacts/front-dashboard-area-graphs-final-desktop.png`
- 최신 면적 그래프 scrolled: `artifacts/front-dashboard-area-graphs-final-desktop-scrolled.png`
- 최신 면적 그래프 mobile: `artifacts/front-dashboard-area-graphs-final-mobile.png`
- 주요 지표 page: `artifacts/front-indicators-page-pass-desktop.png`
- 내 포트폴리오 page: `artifacts/front-portfolio-page-pass-desktop.png`

## 최신 검증 상태

2026-05-16 22:57 KST 기준:

- `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
- `npm.cmd test --prefix front`: 통과, 1 test file / 4 tests
- `npm.cmd run build --prefix front`: 통과, Vite production build 생성
- `git diff --check`: 통과
- 브라우저 캡처 확인:
  - desktop: `scrollWidth` 1425, `clientWidth` 1425, viewport center 713, content center 713, `.dashboard-content-flow` width 920, drawer fixed right edge, `.community-graph` width 878, graph viewBox `0 0 720 320`
  - scrolled desktop: `scrollY` 760에서 topbar/ticker와 right drawer fixed 유지, indicator sparkline 면적 그래프 확인
  - mobile: `scrollWidth` 390, `clientWidth` 390, 문서 전체 가로 overflow 없음, content center 195, graph viewBox `0 0 720 320`, graph height 250, side drawer static
  - chart style: `.spark-area` 5개, `.return-area` 4개, `.series-end-label` 4개, 상승선 red `rgb(240, 68, 82)`, 하락선 blue `rgb(47, 111, 237)`
  - `/indicators` desktop page 캡처 완료
  - `/portfolio` desktop page 캡처 완료
- 서버 상태: 캡처용 Chrome remote debugging `9230`은 종료했고, `5174` dev server만 listen 중입니다.

## 다음 작업

1. 필요하면 하단 가격 상태와 확인 필요 영역을 YASUN의 ranking/table 흐름처럼 더 얇은 table/list 구조로 다듬습니다.
2. 주요 지표/뉴스/매크로 fixture는 실제 API 계약 전까지 mock임을 유지합니다.
3. PR 전에는 `codex/front-dashboard-content` 변경만 검토하고, 루트 worktree 또는 다른 front 브랜치와 섞지 않습니다.

## 브랜치/worktree 정리 메모

- 유지: `codex/front-dashboard-content` - 현재 dashboard content 작업 정본
- 유지 후보: `codex/front-shell-qa` - 별도 QA/fix 브랜치 상태 확인 필요
- 혼동 주의: `codex/front-dark-dashboard-design` - 루트 worktree checkout 브랜치이며 현재 구현 정본 아님
- 정리 후보: upstream이 `gone`인 오래된 local branch들. PR/기록 보존 여부 확인 전 일괄 삭제하지 않습니다.

## 기획자 확인 필요

- `열기 지수` 용어 확정
- 종목별 심리 비교의 원형 지표와 반응 막대 산식 확정
- 커뮤니티 수익률 비교 산식과 기간 확정
- AI 3줄 요약 placeholder 문구 확정

## 2026-05-17 00:27 KST 레이아웃 중심/탭 상호작용 보정

- 기준 브랜치: `codex/front-dashboard-content`
- 기준 worktree: `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- 사용자 피드백: 전체가 왼쪽으로 붙어 보이고, `메인페이지 + 오른쪽 스크롤 패널` 덩어리가 중앙이어야 하며, 맨오른쪽 레일 텍스트는 가로로 읽혀야 하고 클릭 상호작용이 필요함.
- 반영:
  - `.page-frame`, `.dashboard-main-layout`, `.topbar-inner`, 상단 ticker를 동일한 중앙 기준폭으로 맞춤.
  - `.dashboard-main-layout`을 `메인 콘텐츠 + 오른쪽 패널` 전체 단위로 중앙 정렬.
  - 본문/오른쪽 패널 간격을 28px로 늘리고, 주요 콘텐츠 섹션 간 grid gap을 늘림.
  - 오른쪽 레일 폭을 88px로 넓혀 글자가 가로로 보이게 변경.
  - 레일 펼침 버튼, active 상태, `aria-pressed` 상호작용 추가.
  - 대시보드 오른쪽 패널의 `반응 / 지표 / 관심` 탭을 실제 클릭 가능한 tab screen으로 변경.
  - 레일 확장 폭은 104px로 제한해 오른쪽 패널을 덮지 않게 조정.
- 브라우저 실측:
  - `clientWidth`: 1379
  - `page-frame` center: 690
  - `dashboard-main-layout` center: 690
  - `main-nav` center: 689
  - `clientWidth / 2`: 690
  - `edge-rail` expanded left/right: 1275 / 1379
  - `page-frame` right: 1275
  - 수평 overflow 없음.
- 최신 캡처:
  - `artifacts/front-dashboard-centered-rail-no-overlap-desktop.png`
  - `artifacts/front-dashboard-centered-rail-interactive-desktop.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 00:39 KST 토스형 오른쪽 레일/패널 보정

- 사용자 피드백:
  - 중앙 정렬은 맨오른쪽 고정 탭 레일을 제외한 영역 기준이어야 함.
  - 상단 슬라이드 지표는 화면 끝까지 움직이는 형태가 맞음.
  - 오른쪽 탭은 아이콘 위, 글씨 아래 구조여야 함.
  - 확장 시 다크모드 버튼이 같이 늘어나면 안 됨.
  - 확장 시 본문이 자연스럽게 왼쪽으로 밀려야 함.
  - 오른쪽 확장 패널은 토스증권처럼 레일 왼쪽에 별도 패널이 뜨는 방식이어야 함.
- 반영:
  - `.edge-rail`은 64px 고정 레일로 유지하고, 확장 UI는 별도 `.edge-panel`로 분리.
  - `.app-shell.edge-panel-open`에서 `--edge-panel-width`를 켜서 상단 메뉴와 `.page-frame`을 왼쪽으로 이동.
  - 중앙 기준은 `viewport - edge rail - edge panel`의 available area로 계산.
  - 상단 ticker는 page width 제한을 제거하고 `width: 100%`로 화면 전체를 지나가게 변경.
  - 레일 버튼은 icon + label 세로 배치로 변경.
  - theme toggle은 36px 고정으로 유지.
  - `관심` 패널은 토스형 관심 주식 리스트, 통화 토글, AI notice, 추가 버튼 구조로 구성.
- 브라우저 실측:
  - 접힘: availableRight 1315, availableCenter 658, `.page-frame` center 658, `.main-nav` center 657, ticker width 1379.
  - 펼침: availableRight 995, availableCenter 498, `.page-frame` center 498, `.main-nav` center 497, `.edge-panel` 995-1315, `.edge-rail` 1315-1379.
  - 레일 label은 모두 icon below text 구조 확인, theme toggle 36x36 유지, 수평 overflow 없음.
- 최신 캡처:
  - `artifacts/front-dashboard-rail-excluded-centered-collapsed.png`
  - `artifacts/front-dashboard-toss-like-expanded-panel.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 00:44 KST 오른쪽 탭 아이콘/ticker edge test

- 사용자 피드백:
  - 오른쪽 고정 탭 아이콘을 더 키워야 함.
  - 상단 슬라이드 지표가 맨오른쪽 탭 바로 옆에서 나오는지 확인할 수 있게 테스트 데이터를 넣어야 함.
- 반영:
  - `.edge-rail span` 아이콘 크기를 `21px`로 키움.
  - 오른쪽 탭 버튼 높이를 `64px`로 늘려 아이콘/라벨 간격을 안정화.
  - theme toggle은 `36px` 고정 유지, 아이콘만 `18px`로 조정.
  - ticker 테스트 데이터 `RAIL EDGE TEST · 오른쪽 탭 옆에서 시작`을 선두/후미에 추가.
  - `.topbar-ticker`에 `padding-right: var(--edge-rail-width)`를 적용해 ticker viewport 오른쪽 끝이 레일 왼쪽과 맞도록 조정.
  - `live-shift` 시작점을 `translateX(calc(100vw - var(--edge-rail-width)))`로 바꿔 슬라이드가 오른쪽 탭 바로 왼쪽 경계에서 들어오게 함.
- 브라우저 실측:
  - ticker viewport right: `1315`
  - edge rail left: `1315`
  - railLeftMinusTickerRight: `0`
  - rail icon font: `21px`
  - theme toggle: `36x36`
  - 수평 overflow 없음.
- 최신 캡처:
  - `artifacts/front-dashboard-ticker-rail-edge-test.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 00:56 KST 레일 active reset / 외부 콘텐츠 링크 섹션

- 사용자 피드백:
  - `열기/닫기` 버튼이 눌린 상태처럼 유지되면 안 됨.
  - 닫힌 뒤에도 `내 투자/관심/최근 본/실시간` 버튼이 눌린 상태로 남으면 안 됨.
  - 한국 증권/주식 유튜브 최신 영상, 커뮤니티 인기/추천 글 링크, 메르 블로그 같은 외부 칼럼 링크를 메인에 두면 좋겠음.
  - 원문 내용을 복제하지 말고 제목만 링크로 연결해야 함.
  - 유튜브/블로그/커뮤니티/뉴스 등 출처를 아이콘성 배지로 구분해야 함.
- 반영:
  - 닫힌 상태에서는 `.edge-rail button.active`가 하나도 남지 않게 변경.
  - 닫힌 상태에서는 레일 버튼 `aria-pressed`도 모두 `false`가 되도록 변경.
  - `rail-expand` 상시 강조 스타일 제거.
  - `dashboard-summary.json`에 `externalContent.videos`와 `externalContent.links` 추가.
  - 최신 영상은 공개 YouTube RSS에서 제목/URL만 확인해 fixture에 반영:
    - 삼프로TV, 김작가TV, 슈카월드, 달란트투자
  - 메르 블로그는 Naver RSS에서 제목/URL만 확인해 fixture에 반영.
  - 커뮤니티는 원문 게시판/커뮤니티 링크만 연결:
    - 네이버 종목토론 한미반도체, 네이버 종목토론 삼성전자, 토스증권 커뮤니티
  - dashboard 메인에 `증권 영상 새 글`, `블로그와 커뮤니티 링크` 패널 추가.
  - 각 링크는 `target="_blank"`와 `rel="noreferrer noopener"`로 연결.
- 브라우저 실측:
  - 초기 닫힘: activeCount 0, pressedTrue 없음, panelOpen false.
  - 열림: activeCount 1, pressedTrue `관심`, panelOpen true.
  - 다시 닫힘: activeCount 0, pressedTrue 없음, panelOpen false.
  - 외부 링크 rows: 9개, YouTube badge 4개, blog badge 2개.
  - 첫 외부 링크: `https://www.youtube.com/watch?v=X9YDHxlQbpI`
- 최신 캡처:
  - `artifacts/front-dashboard-external-links-rail-reset.png`
  - `artifacts/front-dashboard-external-link-section.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd test --prefix front`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 01:02 KST 외부 콘텐츠 출처 아이콘화

- 사용자 피드백:
  - 실시간 뉴스, 증권 영상 새 글, 블로그/커뮤니티 링크의 `FJ`, `YT`, `블로` 같은 글자 배지를 각 사이트/출처 아이콘으로 바꿔야 함.
- 반영:
  - `DashboardPage.vue`에 `newsIconClass`, `externalIconClass` helper 추가.
  - 뉴스 행은 `tag` 기준으로 카테고리 아이콘을 표시:
    - macro, stock, index, community
  - 외부 링크 행은 source/type 기준으로 사이트 아이콘 표시:
    - YouTube, Naver Blog, Naver, Toss, community fallback
  - visible text badge는 제거하고 `aria-label`만 남김.
  - CSS only icon으로 구현해 별도 이미지 의존성 없이 동작.
- 브라우저 실측:
  - news icons: 5
  - YouTube icons: 4
  - Naver Blog icons: 2
  - Naver icons: 2
  - Toss icons: 1
  - visibleIconTexts: empty
- 최신 캡처:
  - `artifacts/front-dashboard-site-icons-content-section.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 01:07 KST 실제 favicon 이미지 적용

- 사용자 피드백:
  - CSS로 만든 아이콘보다 실제 아이콘 이미지를 가져와 쓰는 편이 나아 보임.
- 반영:
  - `dashboard-summary.json`의 `liveNews`, `externalContent.videos`, `externalContent.links` 항목에 `iconDomain` 추가.
  - `DashboardPage.vue`에서 `https://www.google.com/s2/favicons?domain=<domain>&sz=64` 기반 favicon 이미지를 렌더링.
  - 이미지가 로드 실패하면 `hideBrokenIcon`으로 숨기고 기존 CSS fallback 아이콘으로 되돌아가게 처리.
  - `.site-icon.real-icon img` 스타일 추가.
  - 뉴스 mock source도 `FJ/KR/US/FX/CM` 대신 실제 출처명과 iconDomain을 사용.
- 브라우저 실측:
  - `.site-icon.real-icon img`: 14개
  - loadedCount: 14
  - hiddenCount: 0
  - visibleIconTexts: empty
- 최신 캡처:
  - `artifacts/front-dashboard-real-favicon-icons.png`
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 01:18 KST 네이버 계열 전용 favicon 직링크 적용

- 사용자 피드백:
  - 네이버 블로그와 네이버 종토방이 실제 네이버 서비스 아이콘처럼 보이지 않음.
  - 네이버 블로그는 `b` 모양, 네이버 종토방/금융은 `N` 계열 아이콘을 직접 쓰는 편이 더 자연스러움.
- 확인:
  - `https://section.blog.naver.com/` 문서에 `https://ssl.pstatic.net/static/blog/icon/favicon.ico`가 favicon으로 지정되어 있음.
  - `https://finance.naver.com/` 문서에 `https://ssl.pstatic.net/imgstock/favi/favicon-96x96.png`가 favicon으로 지정되어 있음.
  - 두 아이콘 URL 모두 `HEAD 200` 응답 확인.
- 반영:
  - `DashboardPage.vue`에 `directIconUrls` 매핑 추가.
  - `blog.naver.com`은 `https://ssl.pstatic.net/static/blog/icon/favicon.ico`를 직접 사용.
  - `finance.naver.com`은 `https://ssl.pstatic.net/imgstock/favi/favicon-96x96.png`를 직접 사용.
  - 그 외 도메인은 기존 `https://www.google.com/s2/favicons?domain=<domain>&sz=64` fallback 유지.
  - 외부 링크 아이콘 클래스 판별을 source 문자열이 아니라 `iconDomain` 기준으로 변경.
  - `.site-icon.naver-blog img`, `.site-icon.naver img` 크기를 YouTube와 맞춰 24px로 조정.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 01:45 KST 커뮤니티 비교 차트 컨트롤 정리 / 급상승 이유 요약

- 사용자 피드백:
  - `커뮤니티 지표 비교` 제목과 그래프 박스 사이 간격이 다른 영역보다 커 보임.
  - 그래프 안 `일/주/월/년` 컨트롤이 내부 텍스트와 겹침.
  - 그래프 오른쪽 커뮤니티 범례가 선과 겹쳐 보임.
  - `일/주/월/년`을 쓸 거면 `1D/7D/1M/3M` 컨트롤은 중복이므로 제거해야 함.
  - 오른쪽 `지금 언급 급상승 종목`은 기사, 공시, 커뮤니티 키워드, 가격 변동을 "이 종목 반응이 왜 움직였는가"로 연결하되 긴 문장보다 키워드와 3줄 요약 중심이 좋음.
- 반영:
  - `DashboardPage.vue`에서 차트 바깥 `1D/7D/1M/3M/1Y` 툴바 제거.
  - 그래프 박스 안 상단에 `community-graph-topline`을 추가해 `일/주/월/년`과 커뮤니티 범례를 한 줄로 배치.
  - SVG 차트는 상단 컨트롤 아래로 내려 겹침을 줄임.
  - x축 레이블은 중복 버튼처럼 보이는 `1D/7D/1M` 대신 `D-30/D-21/D-14/D-7/D-3/현재`로 변경.
  - 사용하지 않게 된 `.return-toolbar`, `.return-chart .period-tabs` CSS 제거.
  - `dashboard-summary.json` 첫 라이징 스타에 `reactionDrivers`와 `movementReasons` 추가.
  - 오른쪽 핫 종목 패널에 `왜 움직였나` 영역 추가:
    - 기사: HBM 장비 수요
    - 공시: 수주 확인 대기
    - 커뮤니티: HBM·수급·급등 부담
    - 가격: +3.2% 변동
  - 3줄 요약은 투자 권유가 아니라 mock 관찰 근거 흐름으로 제한.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 02:12 KST YASUN 스타일 하단 사이트 소개 푸터 추가

- 사용자 피드백:
  - YASUN.GG 맨 아래처럼 사이트 소개/문의/주의사항/데이터 출처를 정리한 푸터가 필요함.
  - 이메일은 `yh99cho1@gmail.com`.
  - 투자 권유나 법적 리스크처럼 보이지 않도록 참고용, 비제휴, 책임 제한, 공개 데이터 기준을 명시해야 함.
- 반영:
  - `App.vue`에 전역 `site-footer` 추가.
  - 푸터 구성:
    - `너나사 YouBuyFirst` 소개
    - 문의 메일 `mailto:yh99cho1@gmail.com`
    - 서비스 특징: 반응 흐름 대시보드, 종목별 언급량/반응 방향, 커뮤니티별 모의 성과 비교, AI 에이전트 모의 판단 로그
    - 유의사항: 가격/등락률/수익률/커뮤니티 반응 지표는 참고용 추정치, 정보 제공/학습/모의 실험 목적, 종목 매매 권유 아님, 손실 책임 제한
    - 데이터 출처: KRX, 네이버 금융, Yahoo Finance, NASDAQ Trader, 업비트, 공개 커뮤니티 게시판, 비공개/유료 데이터 미사용
  - `styles.css`에 YASUN 하단처럼 얇은 흰 배경, 4열 정보 그리드, 하단 build/meta 라인 스타일 추가.
  - 오른쪽 레일/확장 패널 구조와 맞게 푸터 폭과 transform을 `page-frame`과 동일하게 맞춤.
  - 모바일에서는 1열로 접히도록 반응형 추가.
  - 예전 제거 규칙과 충돌하지 않도록 푸터 특징 문구는 `커뮤니티 반응 대시보드` 대신 `반응 흐름 대시보드` 사용.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 14:00 KST 애널리스트 리포트 피드 / 오른쪽 레일 상단 정렬

- 사용자 피드백:
  - 애널리스트들이 올리는 분석/리포트도 실시간 뉴스처럼 리스트업하면 좋겠음.
  - 맨오른쪽 여는 탭 위쪽이 사진처럼 색이 다르게 비어 있어 보이므로 통일감 있게 정리해야 함.
- 반영:
  - `dashboard-summary.json`에 `analystReports` mock 피드 4개 추가.
  - `DashboardPage.vue`의 `news-macro-grid`에 `애널리스트 리포트` 패널 추가.
  - 리포트는 본문 복제 없이 제목, 출처, 시간만 표시.
  - 리포트 피드 아이콘은 기존 favicon 렌더링 구조를 재사용.
  - `research`, `strategy`, `disclosure` 태그를 `newsIconClass`에 연결.
  - `.news-macro-grid`는 4열로 조정해 실시간 뉴스, 리포트, 영상, 블로그/커뮤니티가 한 줄에 보이도록 변경.
  - 오른쪽 `edge-rail`과 `edge-panel`은 `--topbar-height: 88px` 아래에서 시작하도록 변경.
  - 레일/패널의 빈 상단 padding을 줄이고, 탑바 영역과 레일 영역이 섞여 보이지 않게 정리.
  - `.site-icon.news-research` fallback 스타일 추가.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 14:10 KST 상단 티커 시작 위치 / 뉴스 피드 2열 정리

- 사용자 피드백:
  - 상단 슬라이드 영역을 오른쪽 끝까지 연장했으면 글씨도 맨 끝에서부터 들어와야 함.
  - 뉴스, 리포트, 증권 영상, 블로그/커뮤니티가 4개 한 줄에 있어 빽빽하므로 2개씩 2줄로 놓는 편이 나음.
- 반영:
  - `.topbar-ticker`의 `padding-right: var(--edge-rail-width)`를 제거하고 `padding-right: 0`으로 변경.
  - `@keyframes live-shift` 시작점을 `translateX(calc(100vw - var(--edge-rail-width)))`에서 `translateX(calc(100vw + 24px))`로 변경.
  - 티커 첫 글자가 오른쪽 끝 안쪽이 아니라 화면 바깥 오른쪽에서부터 들어오도록 조정.
  - `.news-macro-grid`를 `repeat(4, ...)`에서 `repeat(2, ...)`로 변경.
  - 980px 이하에서도 2열을 유지하고, 760px 이하 모바일에서는 1열로 접히도록 조정.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 14:17 KST 상단 인사이트 2분할 / 지표 가로 스트립

- 사용자 피드백:
  - 커뮤니티 지표 그래프 크기를 절반 정도로 줄이고, 나머지 절반에 `종목 반응 한눈에`를 옮기는 편이 좋음.
  - 실시간 주요 지표는 한 줄로 쭉 쓰고, 지표를 더 추가하면 좋겠음.
  - 각 주제를 담당하는 박스끼리의 공간이 더 필요함.
  - 애널리스트 리포트만 박스 크기가 다른 것도 아쉬움.
- 반영:
  - `DashboardPage.vue`에서 `종목 반응 한눈에` 섹션을 `insight-grid` 안으로 이동.
  - `insight-grid`를 2열로 바꿔 `커뮤니티 지표 비교`와 `종목 반응 한눈에`를 같은 줄 1:1 배치.
  - 커뮤니티 그래프 높이를 줄여 첫 줄에서 너무 큰 면적을 먹지 않도록 조정.
  - `dashboard-content-flow`를 단일 컬럼 흐름으로 정리하고 섹션 간 gap을 44px로 확대.
  - `marketIndicators` fixture를 5개에서 9개로 확장:
    - KOSPI, KOSDAQ, NASDAQ100F, USD/KRW, VIX, S&P500F, US10Y, WTI, BTC/KRW
  - `.indicator-grid`를 grid에서 horizontal flex strip으로 변경하고 `overflow-x: auto` 적용.
  - 애널리스트 리포트/뉴스/영상/블로그 피드 패널은 같은 grid row 안에서 높이를 맞추도록 `.news-macro-grid > .panel` 높이 규칙 추가.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 14:24 KST 주요 지표 스크롤 제거 / 종목 반응 랭킹화

- 사용자 피드백:
  - `실시간 주요 지표`에 가로 슬라이드가 생기는 건 별로임. 그럴 거면 지표 몇 개를 빼는 편이 나음.
  - `종목 반응 한눈에`는 원형 버블 디자인보다 종목 순위 1~6위 느낌의 랭킹 UI가 좋아 보임.
- 반영:
  - `dashboard-summary.json`의 `marketIndicators`를 9개에서 6개로 축소.
    - 유지: KOSPI, KOSDAQ, NASDAQ100F, USD/KRW, VIX, S&P500F
    - 제거: US10Y, WTI, BTC/KRW
  - `.indicator-grid`를 horizontal flex/overflow 구조에서 `repeat(6, minmax(0, 1fr))` grid로 되돌림.
  - `DashboardPage.vue`에서 종목 반응 원형 bubble rail 제거.
  - `reaction-ranking.json`에 6위 mock 종목 `셀트리온` 추가.
  - `종목 반응 한눈에`는 `.reaction-rank-row` 기반 1~6위 랭킹 리스트로 변경.
  - 각 랭킹 row에는 순위, 종목명/심볼/시장, 언급 증가율, 언급 수, 키워드, 긍정/부정/중립 비율 bar를 표시.
  - 더 이상 쓰지 않는 `priceStatusLabel`과 bubble 관련 렌더링 제거.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 14:28 KST 종목 반응 랭킹 카드 3열화

- 사용자 피드백:
  - 종목 반응을 일렬 리스트로 길게 놓지 말고, 정사각형에 가까운 사각형 6개를 한 줄에 3개씩 배치하는 편이 좋아 보임.
- 반영:
  - `.reaction-rank-list`를 3열 grid로 변경.
  - `.reaction-rank-row`는 row형 리스트에서 카드형 타일로 변경.
  - 카드 비율은 `aspect-ratio: 1.08 / 1`, 최소 높이 118px.
  - 각 카드에 순위, 종목명/심볼/시장, 언급 증가율/언급 수, 키워드, 긍정/부정/중립 bar 유지.
  - 980px 이하에서는 3열 유지, 760px 이하에서는 2열로 접히도록 반응형 조정.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 14:36 KST 종목 반응 카드 순위 강조 / 배경 변주

- 사용자 피드백:
  - 꼭 정사각형일 필요는 없고 크기감을 맞추자는 의도였음.
  - `종목 반응 한눈에`는 순위와 종목이 더 부각되어야 함.
  - 순위 숫자는 더 크고, 약간 배경처럼 왼쪽 위에 깔리는 느낌이면 좋음.
  - 현재 박스들이 전부 같은 흰 배경이라 진부하므로 중간중간 색감 변주가 필요함.
- 반영:
  - `.reaction-rank-row`의 고정 정사각형 느낌을 풀고 자연스러운 카드 높이로 변경.
  - 각 카드에 `data-rank`를 추가하고 `::before`로 왼쪽 위 대형 순위 워터마크 표시.
  - 실제 `rank-number`도 22px로 키워 카드 내부에서 순위가 먼저 보이도록 조정.
  - `rank-tone-0/1/2` 순환 class를 적용해 카드마다 브랜드 블루, 그린, 오렌지 계열의 약한 gradient 변주 추가.
  - 종목명 font weight/size를 올려 순위와 종목명이 먼저 읽히도록 조정.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과

## 2026-05-17 15:36 KST 검색 키캡 / 차트 비율 유지 확대 / 반응 카드 대비 / 피드 헤더 대비

- 사용자 피드백:
  - 검색칸은 사진처럼 돋보기, `/` 키캡, 검색 문구가 한 덩어리로 자연스럽게 보여야 함.
  - 커뮤니티 지표 비교는 밑의 빈 공간을 활용하되, 글씨나 그래프가 늘어난 사진처럼 찌그러지면 안 됨.
  - `종목 반응 한눈에`는 기존 카드 디자인이 올드하고 과해서, 더 심플하면서 대비가 있는 글래스 계열로 정리해야 함.
  - 뉴스/리포트/영상/블로그 카드의 제목 영역은 본문과 더 대비되어야 함.
- 반영:
  - `DashboardPage.vue` 검색 mock을 `돋보기 + / 키캡 + 검색 문구` 구조로 정리하고 `KR`, `mock search` 텍스트 제거.
  - 커뮤니티 지표 SVG를 `viewBox="0 0 1200 900"`과 `preserveAspectRatio="xMidYMid meet"`로 변경해 비율을 유지하면서 세로 공간을 더 사용하도록 조정.
  - 커뮤니티 지표 축, grid, 라벨 좌표를 900 높이에 맞게 다시 배치하고 그래프 점/선 굵기는 비율 왜곡 없이 유지.
  - 반응 카드 그룹을 어두운 glass tone으로 재조정하고 카드 내부 대비, 종목명, 수치, 키워드 chip 가독성을 보강.
  - 콘텐츠 feed 헤더 band를 카드 상단 전체 폭에 붙이고, 헤더 배경색을 본문보다 더 진하게 조정.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
  - 브라우저 캡처: `artifacts/front-dashboard-search-natural-chart-balanced.png`

## 2026-05-17 15:47 KST 검색 pill 복구 / 피드 4박스 간격 / 종목 반응 재정리 / 상단 슬라이드 색 보강

- 사용자 피드백:
  - 검색칸은 원래 큰 pill 형태가 더 나았고, 거기에 돋보기만 자연스럽게 들어가면 됨.
  - 실시간 뉴스, 리포트, 증권 영상 새 글, 블로그/커뮤니티 링크 네 박스가 너무 붙어 있으므로 가로 폭을 줄이고 좌우/상하 간격을 더 둬야 함.
  - `종목 반응 한눈에`는 기존 디자인을 갈아엎고, 더 심플하면서 대비가 확실한 구조가 필요함.
  - 맨 위 슬라이드 strip은 본문 배경과 색이 너무 비슷하므로 분리감 있는 색으로 바꾸되 글자색도 맞춰야 함.
- 반영:
  - 검색 mock을 `640px` 너비의 흰색 rounded pill로 복구하고, 돋보기 아이콘과 `/` keycap을 내부에 자연스럽게 배치.
  - `.news-macro-grid`의 최대 폭을 줄이고 `gap: 48px 56px`로 조정해 2x2 feed 카드 사이 여백을 키움.
  - 상단 ticker strip을 딥 블루 gradient로 변경하고 ticker 글자/라이브 dot/edge test badge 색을 어두운 배경에 맞게 재조정.
  - 반응 패널은 어두운 단일 glass surface로 유지하되, 긍정/부정 그룹을 2열에서 위아래 1열로 재배치해 종목명 truncation과 chip 세로 쌓임을 제거.
  - 반응 row는 순위, 종목명, 점수, 핵심 키워드 2개, sentiment bar만 남겨 더 얇고 읽히는 구조로 재정리.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - Chrome headless 캡처: `artifacts/front-dashboard-search-feed-reaction-ticker-refine-2.png`

## 2026-05-17 15:58 KST 속보형 상단 슬라이드 / 정사각형 반응 카드 / 피드 전체폭 복구

- 사용자 피드백:
  - 상단 슬라이드의 딥 블루 색이 사이트와 어울리지 않으며, `속보 + 핫한 주제`가 바로 보이는 띠가 필요함.
  - `종목 반응 한눈에`는 큰 세로 리스트가 아니라 한 종목당 정사각형에 가까운 카드로, 긍정 3개와 부정 3개를 심플하고 대비 있게 보여줘야 함.
  - 뉴스/리포트/증권 영상/블로그 카드들은 본문 좌우 끝에 맞아야 하며, 중앙에 모여 있으면 안 됨. 카드 간격만 조정해야 함.
- 반영:
  - `App.vue` 상단 ticker 내용을 `속보`, `핫토픽`, `이슈`, `관심` 주제 중심으로 교체.
  - ticker 애니메이션 시작점을 `translateX(0)`으로 바꿔 첫 화면부터 속보 텍스트가 보이게 조정.
  - ticker 색상은 밝은 크림/오렌지 alert strip으로 변경하고 badge와 텍스트 색을 맞춤.
  - `종목 반응 한눈에`은 긍정 TOP 3 한 줄, 부정 TOP 3 한 줄의 3열 square-like card 구조로 재설계.
  - 각 종목 카드는 순위, 종목명, 점수, 핵심 키워드 2개, 얇은 sentiment bar만 남겨 단순화.
  - `.news-macro-grid`는 `width: 100%`와 `justify-self: stretch`로 본문 좌우 끝을 유지하고, `gap: 48px 44px`로 카드 사이 간격만 확대.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
  - Chrome headless 캡처: `artifacts/front-dashboard-alert-topics-square-reactions-full-feed.png`

## 2026-05-17 17:42 KST 상단 속보 띠 톤 다운 / 종목 반응 outer box 제거

- 사용자 피드백:
  - 상단 슬라이드가 너무 튀고 사이트 색과 안 맞음. 튀는 것 자체보다 디자인 톤이 맞아야 하며, mock 데이터도 속보 위주가 좋음.
  - `종목 반응 한눈에`의 맨 바깥 큰 박스는 제거하고 다시 정렬하는 편이 좋음.
- 반영:
  - `App.vue`의 상단 ticker mock을 `속보` 중심 문구 4개와 `핫토픽` 1개로 교체.
  - ticker 배경을 크림/오렌지 alert strip에서 흰색 기반 + 옅은 레드 accent로 낮춰 본문/상단 nav와 더 자연스럽게 연결.
  - ticker edge test badge도 회색 계열로 낮춰 속보 badge보다 덜 튀게 조정.
  - `reaction-panel.stock-bubble-section`의 border, dark background, shadow, blur를 제거해 outer box를 없앰.
  - 반응 카드 자체는 어두운 square-like card로 유지하고, section heading/legend/tab 색은 밝은 페이지 배경에 맞게 되돌림.
- 검증:
  - `npm.cmd test --prefix front -- shell.spec.ts`: 통과, 4 tests
  - `npm.cmd run build --prefix front`: 통과
  - `git diff --check`: 통과
  - Chrome headless 캡처: `artifacts/front-dashboard-subtle-breaking-ticker-unboxed-reactions.png`

## 2026-05-17 17:49 KST visual changelog 도입

- 사용자 피드백:
  - 바뀌는 버전마다 사진과 버전을 연동해 이전 UI도 확인할 수 있어야 함.
- 반영:
  - `docs/workstreams/front/VISUAL_CHANGELOG.md` 추가.
  - 기존 주요 dashboard 캡처들을 버전별 표로 연결.
  - 최신 화면을 `artifacts/front-visual-history/FV-20260517-1742-subtle-breaking-ticker-unboxed-reactions-dashboard.png`로 별도 보존.
  - 앞으로 UI 변경 시 `FV-YYYYMMDD-HHMM-짧은-변경명` 형식으로 캡처와 handoff를 같이 갱신하는 규칙 명시.

## 2026-05-17 18:00 KST Notion 홈 카드에 visual versions 추가

- 사용자 피드백:
  - Notion 루트 홈카드에 카드 하나를 추가해서 버전 하나당 토글 하나, 사진과 작업 내용을 볼 수 있으면 좋겠음.
- 반영:
  - 루트 대시보드의 `홈 카드 DB`에 `Front Visual Versions` 카드/page 추가.
  - Notion URL: `https://www.notion.so/363df321bd898150bb70fa161f1285fa`
  - 페이지 내부에 최신 주요 4개 버전을 `<details>` toggle 형태로 작성.
  - 각 toggle에는 로컬 갤러리 링크, 직접 이미지 링크, 작업 요약, 검증, 로컬 원본 경로를 포함.
  - 캡처 4개를 `front/public/visual-history/`에도 복사하고 `http://127.0.0.1:5174/visual-history/` 갤러리로 묶음.
- 2026-05-17 18:08 KST 보정:
  - Notion에서 로컬 이미지 block이 전부 깨지는 것을 확인.
  - Notion page에서 inline 이미지 markdown을 제거하고 로컬 갤러리/직접 열기 링크 방식으로 변경.
- 2026-05-17 18:17 KST 보정:
  - `visual-history/`가 어디에 쓰이는지 불명확하다는 피드백 반영.
  - Notion 상단에 로컬 저장 위치를 추가.
  - 갤러리 HTML은 `front/public/visual-history/index.html`, 갤러리 이미지 복사본은 `front/public/visual-history/*.png`, 원본 캡처는 `artifacts/front-visual-history/`와 `artifacts/`에 둔다고 명시.
- 2026-05-17 18:28 KST 보정:
  - Notion 카드의 `바로가기`를 `http://127.0.0.1:5174/visual-history/index.html`로 변경.
  - Notion과 로컬 갤러리 상단에 `file:///C:/agents/YouBuyFirst/.worktrees/front-dashboard-content/front/public/visual-history/index.html` 및 이미지 폴더 URL `file:///C:/agents/YouBuyFirst/.worktrees/front-dashboard-content/front/public/visual-history/` 추가.
  - `front/public/visual-history/index.html` 상단에 서버 index, 로컬 index, 이미지 폴더 열기 버튼을 추가.
  - 갤러리는 대표 비교 버전만 두고, 원본/세부 캡처는 `artifacts/` archive로 분리하는 규모 관리 규칙을 추가.
- 2026-05-17 18:43 KST 보정:
  - `index.html` 하나에 화면이 계속 쌓일 수 있다는 피드백 반영.
  - `front/public/visual-history/index.html`은 날짜 목록 페이지로 변경.
  - 2026-05-17 캡처 4개와 기존 카드형 갤러리를 `front/public/visual-history/2026-05-17/`로 이동.
  - 날짜별 서버 URL은 `http://127.0.0.1:5174/visual-history/2026-05-17/index.html`.
- 2026-05-17 19:12 KST 보정:
  - Notion 기록을 본문 표가 아니라 실제 database 형태로 전환.
  - `Front Visual Version Log` DB 생성: `https://www.notion.so/37ba7cf74d534755a88b00bcccaca275`
  - DB 속성: `버전`, `화면`, `날짜`, `상태`, `요약`, `갤러리`, `로컬 경로`, `원본 경로`, `상세 문서`.
  - 화면별 DB를 여러 개 만들지 않고 `화면` 속성과 필터 뷰로 구분. 현재 `Dashboard`, `Indicators`, `Portfolio` 뷰 생성.
  - 2026-05-17 대표 Dashboard 버전 4개를 DB row로 추가.
  - `Front Visual Versions` 페이지 본문은 빠른 링크, 기록 방식, 메모리 보호 규칙, DB embed만 남기도록 축소.
- 2026-05-17 19:20 KST 보정:
  - 사용자가 Notion DB가 보기 어렵고 HTML 갤러리만으로 충분하다고 판단.
  - `Front Visual Version Log` DB를 휴지통 처리.
  - `Front Visual Versions` 페이지에서 DB embed 제거.
  - 앞으로 Notion은 HTML 갤러리 바로가기 카드로만 유지.
- 주의:
  - Notion 도구는 로컬 PNG를 직접 업로드하지 못하고, Notion은 `localhost`/`127.0.0.1` 이미지를 inline preview로 안정적으로 렌더링하지 못함.
  - Notion 안에서 실제 이미지 미리보기가 필요하면 GitHub raw 같은 외부 접근 가능한 이미지 URL로 전환해야 함.
  - 원본은 계속 `artifacts/`와 `docs/workstreams/front/VISUAL_CHANGELOG.md`에 보존.
