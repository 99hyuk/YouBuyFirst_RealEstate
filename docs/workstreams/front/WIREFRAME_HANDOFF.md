# Front Wireframe Handoff

Last update: 2026-05-20 KST

이 파일은 새 front 세션이 처음 보는 현재 기준입니다. 과거 디자인 대화와 긴 로그는 archive에 있고, 시작 루틴으로 읽지 않습니다.

## 현재 작업 기준

- 기준 브랜치는 최신 `main`입니다.
- 실제 화면 작업은 별도 front worktree/branch에서 진행합니다.
- 현재 제품 톤은 대시보드(`/dashboard`) 기준입니다.
- 디자인 시스템은 `docs/workstreams/front/DESIGN_SYSTEM.md`를 따릅니다.
- 화면 구조가 바뀌면 `docs/workstreams/front/screens/`의 해당 Screen Brief를 최신 기준으로 갱신합니다.

## 현재 디자인 우선순위

1. 검색창과 상단 메뉴 위치를 흔들지 않습니다.
2. 대시보드처럼 한 화면에 많은 지표가 들어오게 합니다.
3. Pretendard 기준으로 숫자, 제목, 보조 설명의 크기 차이를 분명히 둡니다.
4. 카드 남발 대신 헤더, 선, 간격, 배경 톤으로 영역을 나눕니다.
5. 긴 설명문은 도형, 막대, 선 그래프, 칩, 표, timeline으로 치환합니다.
6. 탭 첫 화면은 핵심 요약 허브로 만들고, 상세 정보는 하위 route로 분리합니다.
7. 커뮤니티 반응과 가격/뉴스/공시 변화가 함께 읽히게 합니다.
8. 투자 자문형 표현은 피하고, 관찰 데이터 라벨로만 다룹니다.

## 최근 결정

- 대시보드 검색창 왼쪽에는 `개미 심리 지수`를 둡니다.
- 넓은 화면에서는 왼쪽 보조 카드, 반폭 QHD 같은 중간 폭에서는 검색창 위의 얇은 정보 바로 전환합니다.
- 종목 상세의 상단 팩트폭격 배너는 커뮤니티 요약이 아니라 시황/기술 지표/재무/뉴스 기반의 짧은 한줄평입니다.
- 뉴스룸은 대시보드의 네 개 리스트 패턴을 확장해 뉴스, 리포트, 영상, 블로그/커뮤니티를 따로 볼 수 있게 합니다.
- 인간 지표는 커뮤니티 비교와 에이전트 판단 기록을 함께 다루는 방향입니다.

## 시각 기록

- 대표 갤러리: `front/public/visual-history/index.html`
- 날짜별 갤러리: `front/public/visual-history/YYYY-MM-DD/index.html`
- 최근 변경 요약: `docs/workstreams/front/VISUAL_CHANGELOG.md`

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
rg -n -m 20 "검색어" docs\workstreams\front\archive\WIREFRAME_HANDOFF_2026-05-17.md
```
