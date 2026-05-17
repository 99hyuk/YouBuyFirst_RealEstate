# Front Visual Changelog

프론트 UI를 바꿀 때마다 캡처와 변경 버전을 연결해 이전 화면을 다시 확인하기 위한 기록입니다.

## 캡처 규칙

- 버전 ID는 `FV-YYYYMMDD-HHMM-짧은-변경명` 형식으로 둔다.
- 기본 캡처는 `dashboard` desktop 기준 `1440 x 1800` 이상으로 남긴다.
- 필요하면 mobile, scrolled, expanded drawer 캡처를 같은 버전 ID 뒤에 suffix로 추가한다.
- 캡처 파일은 `artifacts/front-visual-history/`에 저장하고, 임시 비교 캡처는 기존 `artifacts/`에 둘 수 있다.
- UI 피드백 반영 후에는 이 파일과 `docs/workstreams/front/WIREFRAME_HANDOFF.md`에 최신 캡처를 함께 적는다.

## Latest

| Version | Time | Screenshot | What Changed |
| --- | --- | --- | --- |
| `FV-20260517-1938-compact-feed-cards` | 2026-05-17 19:38 KST | [dashboard](../../../artifacts/front-visual-history/FV-20260517-1938-compact-feed-cards-dashboard.png) | 뉴스, 리포트, 증권 영상, 블로그 링크를 4행 동일 높이 카드로 줄이고 각 행에 전문/보기 링크를 둠 |
| `FV-20260517-1742-subtle-breaking-ticker-unboxed-reactions` | 2026-05-17 17:42 KST | [dashboard](../../../artifacts/front-visual-history/FV-20260517-1742-subtle-breaking-ticker-unboxed-reactions-dashboard.png) | 상단 속보 띠 톤 다운, 속보 mock 문구 정리, `종목 반응 한눈에` outer box 제거 |

## Notion Mirror

- Home card page: [Front Visual Versions](https://www.notion.so/363df321bd898150bb70fa161f1285fa)
- Home card DB: `홈 카드 DB`
- Notion cannot reliably render local PNG files or `localhost`/`127.0.0.1` URLs as inline image blocks.
- The Notion page is only a shortcut card for the HTML visual gallery.
- Do not add databases, long toggles, full work logs, or image bodies to Notion.
- The temporary `Front Visual Version Log` database was removed because the HTML gallery is easier to inspect.
- Server gallery: `http://127.0.0.1:5174/visual-history/index.html`
- Local file gallery: `file:///C:/agents/YouBuyFirst/.worktrees/front-dashboard-content/front/public/visual-history/index.html`
- Date gallery example: `http://127.0.0.1:5174/visual-history/2026-05-17/index.html`
- Local image folder example: `file:///C:/agents/YouBuyFirst/.worktrees/front-dashboard-content/front/public/visual-history/2026-05-17/`
- Notion may rewrite `file:///` markdown links, so keep local file URLs as plain copyable text there.
- If the local gallery does not open, start the front dev server and open `http://127.0.0.1:5174/dashboard`.
- Inline Notion image previews require externally reachable URLs such as GitHub raw assets.
- Source images are also kept in `artifacts/` and `artifacts/front-visual-history/`.

## Local Storage

- Worktree: `C:\agents\YouBuyFirst\.worktrees\front-dashboard-content`
- Gallery root HTML: `front/public/visual-history/index.html`
- Date gallery HTML: `front/public/visual-history/YYYY-MM-DD/index.html`
- Gallery image copies: `front/public/visual-history/YYYY-MM-DD/*.png`
- Local image folder example: `file:///C:/agents/YouBuyFirst/.worktrees/front-dashboard-content/front/public/visual-history/2026-05-17/`
- Versioned original captures: `artifacts/front-visual-history/`
- Full capture archive: `artifacts/`
- Handoff note: `docs/workstreams/front/WIREFRAME_HANDOFF.md`

## 많이 쌓일 때의 운영 방식

스크린샷은 두 종류로 나눕니다.

- `front/public/visual-history/index.html`: 날짜 목록입니다. 화면이 많아져도 루트 페이지가 길어지지 않게 합니다.
- `front/public/visual-history/YYYY-MM-DD/`: 해당 날짜의 대표 화면 모음입니다. "이전 버전과 지금 버전 비교"에 필요한 것만 넣습니다.
- `artifacts/`: 작업 중 생긴 캡처를 넉넉히 보관하는 창고입니다. 작은 수정, 실패한 시도, 중간 점검 캡처도 여기에 둡니다.

Notion에는 대표 화면 5-10개 정도만 남기고, 오래된 세부 캡처는 이 문서의 표와 `artifacts/` 경로로 찾습니다. 이렇게 해야 Notion과 갤러리가 너무 무거워지지 않습니다.

## Key Dashboard Snapshots

| Version | Time | Screenshot | What To Compare |
| --- | --- | --- | --- |
| `legacy-simple-redesign` | 2026-05-16 20:51 KST | [desktop](../../../artifacts/front-dashboard-after-simple-redesign-desktop.png) | 초기 단순 redesign 기준 |
| `bubble-graph` | 2026-05-16 21:00 KST | [desktop](../../../artifacts/front-dashboard-bubble-graph-desktop.png) | 여러 종목을 원형/버블로 배치하던 시점 |
| `before-yasun-pass` | 2026-05-16 21:07 KST | [desktop](../../../artifacts/front-dashboard-before-yasun-pass.png) | 야선 스타일 적용 전 비교용 |
| `yasun-pass-final` | 2026-05-16 21:17 KST | [desktop](../../../artifacts/front-dashboard-yasun-pass-desktop-final.png) | Pretendard/YASUN 계열 첫 정리 |
| `macro-news-pass` | 2026-05-16 21:50 KST | [full](../../../artifacts/front-dashboard-macro-news-pass-full.png) | 뉴스/매크로/지표 섹션 추가 |
| `drawer-tabs-pass` | 2026-05-16 22:10 KST | [desktop](../../../artifacts/front-dashboard-drawer-tabs-pass-desktop.png) | 오른쪽 탭/주요 지표/포트폴리오 탭 추가 |
| `wide-community-final` | 2026-05-16 22:44 KST | [desktop](../../../artifacts/front-dashboard-wide-community-final-desktop.png) | 커뮤니티 지표 비교를 넓게 배치 |
| `area-graphs-final` | 2026-05-16 22:56 KST | [desktop](../../../artifacts/front-dashboard-area-graphs-final-desktop.png) | 지표 sparkline 면적 그래프 반영 |
| `layout-revert-chart-axis` | 2026-05-16 23:10 KST | [desktop](../../../artifacts/front-dashboard-layout-revert-chart-axis-desktop.png) | 본문/오른쪽 패널 위치 이전 상태로 복구, 차트 축 정리 |
| `wide-viewbox-dense` | 2026-05-16 23:34 KST | [desktop](../../../artifacts/front-dashboard-wide-viewbox-dense-desktop.png) | 인포그래픽형 조밀 레이아웃 시도 |
| `toss-rail-final` | 2026-05-17 00:08 KST | [desktop](../../../artifacts/front-dashboard-toss-rail-final-desktop.png) | 토스증권식 오른쪽 rail 정리 |
| `rail-excluded-centered` | 2026-05-17 00:37 KST | [collapsed](../../../artifacts/front-dashboard-rail-excluded-centered-collapsed.png) / [expanded](../../../artifacts/front-dashboard-toss-like-expanded-panel.png) | rail 제외 본문 정렬, 확장 패널 비교 |
| `external-links-rail-reset` | 2026-05-17 00:54 KST | [dashboard](../../../artifacts/front-dashboard-external-links-rail-reset.png) | 유튜브/블로그/커뮤니티 링크 섹션 추가 전후 |
| `real-favicon-icons` | 2026-05-17 01:07 KST | [dashboard](../../../artifacts/front-dashboard-real-favicon-icons.png) | 실제 사이트 favicon 기반 아이콘 적용 |
| `reaction-dark-bars` | 2026-05-17 14:51 KST | [desktop](../../../artifacts/front-dashboard-reaction-dark-bars-desktop.png) | 어두운 종목 반응 카드/막대 대비 시도 |
| `glass-feed-headers` | 2026-05-17 15:08 KST | [desktop](../../../artifacts/front-dashboard-glass-reaction-feed-headers-desktop.png) | glass 반응 카드와 feed header band 시도 |
| `search-natural-chart-balanced` | 2026-05-17 15:33 KST | [desktop](../../../artifacts/front-dashboard-search-natural-chart-balanced.png) | 검색 keycap, 차트 비율 유지 확대, feed header contrast |
| `search-feed-reaction-ticker-refine-2` | 2026-05-17 15:47 KST | [dashboard](../../../artifacts/front-dashboard-search-feed-reaction-ticker-refine-2.png) | 큰 검색 pill, 피드 gap 확대, 큰 dark reaction panel |
| `alert-topics-square-reactions-full-feed` | 2026-05-17 15:58 KST | [dashboard](../../../artifacts/front-dashboard-alert-topics-square-reactions-full-feed.png) | 속보형 ticker, 3+3 정사각형 반응 카드, feed full width |
| `subtle-breaking-ticker-unboxed-reactions` | 2026-05-17 17:42 KST | [dashboard](../../../artifacts/front-dashboard-subtle-breaking-ticker-unboxed-reactions.png) | 속보 띠 톤 다운, reaction outer box 제거 |
| `compact-feed-cards` | 2026-05-17 19:38 KST | [dashboard](../../../artifacts/front-visual-history/FV-20260517-1938-compact-feed-cards-dashboard.png) | 뉴스/리포트/영상/블로그 카드 4행 동일 높이, 전문 링크 노출 |

## Full Capture Archive

전체 캡처 원본은 `artifacts/`에 남아 있습니다. 위 표는 주요 비교 지점만 뽑은 index입니다.
