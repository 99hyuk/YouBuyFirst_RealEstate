# Front Wireframe Handoff

Last update: 2026-05-18 09:15 KST

이 문서는 새 front 세션이 처음 보는 짧은 현재 기준입니다. 상세 변경 이력은 archive로 분리했습니다.
전문을 길게 읽지 말고, 필요한 경우에만 키워드로 archive를 검색합니다.

## 먼저 읽기

- 이 파일만 먼저 읽고 작업을 시작합니다.
- 과거 디자인 조정 로그는 `docs/workstreams/front/archive/WIREFRAME_HANDOFF_2026-05-17.md`에서 `rg`로 검색합니다.
- 시각 캡처 목록은 `docs/workstreams/front/VISUAL_CHANGELOG.md`를 먼저 봅니다.
- 현재 정본은 `main`의 `front/` 코드와 이 문서입니다.
- 오래된 dev server나 예전 worktree 경로를 그대로 믿지 않습니다. 새 front 작업은 최신 `main`에서 새 worktree를 열어 시작합니다.

## 현재 작업 상태

- 열린 GitHub PR은 없습니다.
- 현재 활성 front worktree는 없습니다.
- 이전 `codex/front-dashboard-content` 작업은 정리되었으므로, 예전 `http://127.0.0.1:5174/dashboard` 서버가 떠 있다는 가정으로 시작하지 않습니다.
- `codex/front-dark-dashboard-design` 브랜치는 아직 로컬/원격에 남아 있습니다. main에 없는 디자인 설계 조각이 있을 수 있으므로 삭제 전 front 트랙이 살릴 내용을 확인합니다.

## 현재 화면 방향

- 제품 핵심은 관심종목 앱 자체가 아니라 `커뮤니티 반응 지표`입니다. 관심종목은 커뮤니티 반응을 매일 쓰게 만드는 필터/개인화 레이어로 둡니다.
- 대시보드는 종목별 커뮤니티 언급량, 반응 방향, 최신 기사/리포트/영상/블로그/커뮤니티 링크를 한 화면에서 비교할 수 있어야 합니다.
- 실시간 뉴스, 애널리스트 리포트, 증권 유튜브, 신뢰 블로그, 인기 커뮤니티 글은 초기 매매 판단값이 아니라 근거 확인과 이슈 확산 확인 레이어로 둡니다.
- 실제 투자 자문, 실거래 지시, 수익 보장, 개인화 투자 권유처럼 읽히는 문구는 피합니다.

## 최근 디자인 결정 요약

- 피드 카드는 뉴스/리포트/영상/블로그가 같은 높이와 같은 행 규격으로 보이게 합니다.
- 각 피드 행은 제목, 출처/시간, 외부 링크 액션을 짧고 촘촘하게 보여줍니다.
- 검색창은 `KR` 같은 텍스트 배지보다 검색 아이콘 중심이 낫습니다.
- 커뮤니티 비교 그래프는 단순 세로 확대가 아니라 비율 보존과 축/라벨 가독성을 함께 봅니다.
- 종목 반응은 전체 순위보다 `언급+긍정 TOP 3`, `언급+부정 TOP 3`처럼 투자자가 바로 비교할 묶음이 좋습니다.
- 다크톤은 과하면 올드해 보이므로, 어두운 배경에서도 카드 내부 대비와 정보 밀도를 우선합니다.

## Codex 디자인/구현 기준

프론트 디자인과 구현은 기본적으로 Codex가 `front/` 코드에서 함께 진행합니다. 정본은 외부 디자인 파일이 아니라 merge된 코드, fixture, 화면 문구, API 후보, 검증 기록입니다.

Figma AI, Stitch 같은 외부 디자인 도구는 기본 작업 흐름이 아닙니다. 사용자가 명시적으로 요청할 때만 참고 시안 탐색용으로 쓰고, 선택한 방향은 Codex가 작은 front PR로 다시 코드에 반영합니다. 외부 도구 산출물은 정본이 아니며, 그대로 구현하지 않습니다.

디자인 변경은 가능한 한 한 화면 또는 한 컴포넌트 단위의 작은 PR로 끊습니다.

## 이미지 기록 방식

- `front/public/visual-history/index.html`: 날짜별 갤러리 입구입니다.
- `front/public/visual-history/YYYY-MM-DD/index.html`: 해당 날짜의 대표 스크린샷 페이지입니다.
- `front/public/visual-history/YYYY-MM-DD/*.png`: 날짜별 대표 스크린샷입니다.
- `artifacts/`: 작업 중 찍은 캡처와 중간 비교 이미지를 둘 수 있는 로컬 산출물 폴더입니다.
- `docs/workstreams/front/VISUAL_CHANGELOG.md`: 대표 시각 변경 목록입니다.

Notion에는 모든 이미지를 다 올리지 않고, 주요 화면 변화와 갤러리 링크만 요약합니다.

## 검증 기준

front/UI를 바꾸면 가능하면 아래를 확인합니다.

- `npm.cmd test --prefix front -- shell.spec.ts`
- `npm.cmd run build --prefix front`
- 브라우저로 `/dashboard` 화면, 콘솔 오류, 주요 반응형 상태 확인
- PR 본문에는 스크린샷 또는 브라우저 검증 결과를 짧게 남김

문서만 바꾸는 작업은 `git diff --check`를 실행합니다.

## 다음 front 후보

- 현재 `main`의 `/dashboard`를 다시 띄워 실제 최신 화면을 확인합니다.
- `codex/front-dark-dashboard-design`에서 main에 없는 디자인 결정이나 문서 조각이 있는지 확인합니다.
- 메인 대시보드 와이어프레임을 커뮤니티 반응 중심으로 계속 다듬습니다.
- 관심종목 브리핑과 종목 이벤트 타임라인 화면 후보를 mock으로 추가합니다.
- 최신 기사/공시/유튜브/신뢰 블로그/인기 커뮤니티 글 카드의 API field 후보를 정리합니다.

## archive 검색

상세 과거 로그가 필요할 때만 아래처럼 검색합니다.

```powershell
rg -n -m 20 "검색어" docs\workstreams\front\archive\WIREFRAME_HANDOFF_2026-05-17.md
```

예전 로그를 현재 사실로 바로 받아들이지 말고, 현재 `main` 코드와 열린 브랜치 상태를 먼저 확인합니다.