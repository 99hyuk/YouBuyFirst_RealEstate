# Front Wireframe Handoff

마지막 갱신: 2026-05-16

이 문서는 프론트 와이어프레임 채팅이 끊겼을 때 복구하기 위한 짧은 정본입니다. 상세 plan/spec은 `docs/superpowers/`에서 키워드로 검색하고, 새 채팅 시작 루틴에서 전문 읽지 않습니다.

## 현재 구현 상태

- 위치: `front/`
- 기술: Vue 3 + Vite + TypeScript + Vue Router
- 상태: fixture/mock 기반 저충실도 와이어프레임 shell
- 실제 backend API 연결: 아직 없음
- 차트 라이브러리: 아직 확정하지 않음
- 최종 브랜드 디자인: 아직 확정하지 않음

## 현재 화면 방향

대시보드는 `Briefing + Terminal` 방향입니다.

- 첫 화면: `오늘 커뮤니티 브리핑`
- 핵심 문장: `투자자들이 먼저 떠드는 종목을 읽습니다`
- 메인 보드: `반응 터미널`
- 목적: 커뮤니티 반응이 커진 종목을 mock 데이터로 빠르게 훑고, API 계약 전까지 필요한 기획 질문을 드러냄
- 고지: 투자 자문이 아니라 커뮤니티 반응 관찰 화면

## 현재 라우트

| route | 상태 | 역할 |
| --- | --- | --- |
| `/` | `/dashboard` redirect | 기본 진입 |
| `/dashboard` | 구현됨 | 브리핑, 반응 터미널, 가격 placeholder, 기획자 확인 필요 |
| `/stocks/:symbol` | shell | 종목 상세 mock |
| `/communities` | shell | 커뮤니티 비교 mock |
| `/agents` | shell | 에이전트 실험 mock |
| `/portfolio` | disabled shell | trade 트랙 이후 활성화 |

## 주요 파일

- `front/src/App.vue`: 앱 헤더와 navigation
- `front/src/pages/DashboardPage.vue`: `Briefing + Terminal` 대시보드
- `front/src/router/routes.ts`: route inventory
- `front/src/fixtures/dashboard-summary.json`: 대시보드 문구와 기획 확인 항목
- `front/src/fixtures/reaction-ranking.json`: 반응 터미널 mock ranking
- `front/src/fixtures/quote-snapshots.json`: 가격 상태 placeholder
- `front/src/__tests__/shell.spec.ts`: route, mock data, 주요 화면 문구 테스트
- `front/src/styles.css`: 현재 저충실도 화면 스타일

## 기획자 확인 필요

현재 fixture에 남아 있는 확인 항목:

- `열기 지수` 용어 확정
- 기본 시간창 `1h`, `24h`, `30m` 중 선택
- AI 3줄 요약 placeholder 문구 확정

추가로 다음 front 작업 전에 확인하면 좋은 항목:

- `Briefing + Terminal` 방향을 계속 갈지, 더 일반적인 dashboard layout으로 바꿀지
- 가격 정보가 mock/stale일 때 사용자에게 얼마나 강하게 표시할지
- 커뮤니티별 성과 표현을 "맞았다/틀렸다"처럼 보이지 않게 어떤 문구로 둘지

## 검증 상태

2026-05-16 복구 시점 확인:

- `npm.cmd ci --prefix front`: 통과
- `npm.cmd test --prefix front`: 1개 test file, 3개 test 통과
- `npm.cmd run build --prefix front`: 통과
- dev server: `http://127.0.0.1:5174/`

PowerShell에서 `npm`이 execution policy로 막히면 `npm.cmd`를 사용합니다.

## 디자인 도구 핸드오프

Codex가 정본으로 잡는 것은 화면의 기능 구조입니다.

- routes
- 화면별 목적
- 데이터와 상태
- API 계약 후보
- 금지 표현과 리스크
- 기획자 확인 필요 항목

Figma AI, Stitch 같은 도구는 고충실도 시안 탐색에 씁니다. 텍스트 문서만 넘기면 동일하게 그려지지 않을 수 있으므로, 넘길 때는 아래를 함께 줍니다.

- 이 문서
- `/dashboard` 화면 screenshot 또는 현재 localhost URL
- 반드시 유지할 문구
- route별 화면 목적
- 색/타이포/밀도 선호
- 하지 말아야 할 것: 투자 자문처럼 보이는 문구, 실거래 CTA, 원문 재게시, 과한 마케팅 hero

정확한 구현을 원하면 디자인 툴 결과물을 다시 Codex에 넘길 때 screenshot, export asset, spacing/color/token 메모, 컴포넌트 이름을 함께 줍니다. Figma 연결 도구가 있으면 frame을 직접 읽는 방식도 가능하지만, 이 repo의 정본은 여전히 코드와 문서입니다.

## 다음 권장 작업

1. 현재 `/dashboard`를 브라우저로 보고 `Briefing + Terminal` 방향을 유지할지 결정
2. 유지한다면 dashboard polish PR을 이어서 모바일/상태 표현 보강
3. 바꾼다면 이 문서를 먼저 수정하고, Figma AI용 design brief를 별도 섹션으로 작성
4. 선택된 고충실도 시안을 Codex가 Vue 컴포넌트로 구현
