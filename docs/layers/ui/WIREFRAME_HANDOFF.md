# Front Wireframe Handoff

Last update: 2026-06-01 KST

이 파일은 새 front 세션이 처음 보는 현재 기준입니다. 과거 디자인 대화와 긴 로그는 archive에 있고, 시작 루틴으로 읽지 않습니다.

## 현재 작업 기준

- 기준 브랜치는 `codex/realestate-bootstrap`입니다.
- 실제 화면 작업은 별도 front branch에서 진행합니다.
- 이 프로젝트는 부동산 서비스만 담당합니다.
- 첫 화면은 랜딩 페이지가 아니라 실제 부동산 대시보드입니다.
- 디자인 시스템은 `docs/layers/ui/DESIGN_SYSTEM.md`를 따릅니다.
- 화면 구조가 바뀌면 `docs/layers/ui/screens/`의 해당 Screen Brief를 최신 기준으로 갱신합니다.

## 현재 디자인 우선순위

1. 검색창과 상단 메뉴 위치를 흔들지 않습니다.
2. 대시보드처럼 한 화면에 많은 지표가 들어오게 합니다.
3. Pretendard 기준으로 숫자, 제목, 보조 설명의 크기 차이를 분명히 둡니다.
4. 카드 남발 대신 헤더, 선, 간격, 배경 톤으로 영역을 나눕니다.
5. 긴 설명문은 도형, 막대, 선 그래프, 칩, 표, timeline으로 치환합니다.
6. 탭 첫 화면은 핵심 요약 허브로 만들고, 상세 정보는 하위 route로 분리합니다.
7. 지역/단지 반응, 뉴스/컬럼, 실거래/전세/매물, 정책 이벤트가 함께 읽히게 합니다.
8. 행동 지시형 표현은 피하고, 관찰 데이터 라벨로만 다룹니다.

## 최근 결정

- 삭제된 레거시 화면은 active 기준에서 제거되었습니다.
- 신규 active 화면은 `realestate-dashboard`와 `realestate-target-detail`입니다.
- 너나사 부동산은 너나사 시리즈의 공통 UI shell, nav, 검색, dashboard grid, rail, card 패턴을 따르고, 대표 accent는 warm orange 계열로 둡니다.
- 부동산 화면은 dashboard 스타일을 유지하되, 핵심 정보는 지역/단지, 쟁점 비율, market fact timeline, evidence log입니다.
- 화면 문구는 "관찰", "분석", "반응 지표", "표본 신뢰도", "근거 로그", "데이터 지연"을 기본으로 씁니다.

## 색상 적용 기준

- `--brand`는 부동산 active 화면에서 warm orange 계열로 둡니다.
- blue는 우려/하락/정보 의미색으로만 남깁니다.
- 의미색을 브랜드색과 섞지 않습니다. warning/error, 기대/우려, market up/down은 기존 의미를 우선합니다.
- 첫 front 변경은 전체 리디자인이 아니라 token 교체와 주요 brand usage 정리로 제한합니다.

## 시각 기록

- 대표 갤러리: `front/public/visual-history/index.html`
- 날짜별 갤러리: `front/public/visual-history/YYYY-MM-DD/index.html`
- 최근 변경 요약: `docs/layers/ui/VISUAL_CHANGELOG.md`

Visual History는 작업 참고 문서가 아니라 변경 등록용 갤러리입니다. 새 화면 변경이 있으면 캡처를 추가하고 날짜별 index와 changelog 대표 행만 갱신합니다. 복구, 회귀 비교, 사용자가 특정 버전을 지목한 경우가 아니면 과거 HTML과 이미지 목록을 읽지 않습니다.

## 검증 기준

```powershell
npm.cmd run build --prefix front
npm.cmd test --prefix front
git diff --check
```

레이아웃 변경은 실제 viewport에서 확인합니다. 긴 DOM/콘솔 출력 대신 좌표, 스크린샷 경로, 확인 결과만 남깁니다.

## archive 검색

과거 근거가 꼭 필요할 때만 아래처럼 좁혀 봅니다.

```powershell
rg -n -m 20 "검색어" docs\archive\ui
```
