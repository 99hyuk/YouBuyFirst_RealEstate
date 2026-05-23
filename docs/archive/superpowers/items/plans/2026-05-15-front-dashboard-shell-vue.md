# front dashboard shell Vue 실행 계획

> **에이전트 작업자 필수 지시:** 이 계획을 실행할 때는 `superpowers:executing-plans`를 사용한다. 체크박스(`- [ ]`)를 하나씩 처리하고, 루트 checkout이 아니라 `C:\agents\YouBuyFirst\.worktrees\front-dashboard-shell-vue` 안에서만 작업한다.

**목표:** `front` 패키지를 만들고, Vue 3 + Vite + TypeScript + Vue Router 기반 저충실도 화면 shell을 route inventory 문서 기준으로 구현한다.

**방식:** 실제 API 연결, 차트 라이브러리, 고충실도 디자인은 하지 않는다. mock fixture와 route shell을 먼저 만들고, 테스트가 그 구조를 보증하게 한다.

**사용 도구:** Vue 3, Vite, TypeScript, Vue Router, Vitest, Vue Test Utils, jsdom, GitHub CLI.

---

## 현재 상황 요약

- 기준 루트: `C:\agents\YouBuyFirst`
- 작업 위치: `C:\agents\YouBuyFirst\.worktrees\front-dashboard-shell-vue`
- 작업 브랜치: `codex/front-dashboard-shell-vue`
- 기존 `codex/front-dashboard-shell` 브랜치는 오래된 ops 문서 브랜치라 이번 작업에 쓰지 않는다.
- 이번 작업은 `docs/superpowers/specs/2026-05-15-front-route-inventory-design.md`를 구현 입력으로 삼는다.

## 이번 PR에 포함할 것

- `front/package.json`
- `front/package-lock.json`
- `front/index.html`
- `front/vite.config.ts`
- `front/tsconfig.json`
- `front/src/main.ts`
- `front/src/App.vue`
- `front/src/router/routes.ts`
- `front/src/fixtures/*.json`
- `front/src/pages/*.vue`
- `front/src/styles.css`
- `front/src/__tests__/shell.spec.ts`
- `.gitignore`
- `docs/superpowers/plans/2026-05-15-front-dashboard-shell-vue.md`

## 이번 PR에서 제외할 것

- 실제 backend API 호출
- 차트 라이브러리 확정
- 최종 브랜드 디자인
- 인증, OCR, 실거래, 주문/체결
- backend, pipeline, crawl, data, market, trade, agent 코드 변경

---

## 작업 1. 패키지 설정과 테스트 기반 만들기

**파일:**

- 추가: `front/package.json`
- 추가: `front/index.html`
- 추가: `front/vite.config.ts`
- 추가: `front/tsconfig.json`

- [x] **1-1. front 패키지 설정 파일 추가**

`front/package.json`에는 아래 스크립트를 둔다.

```json
{
  "name": "youbuyfirst-front",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "vue": "^3.5.13",
    "vue-router": "^4.5.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.3",
    "@types/node": "^22.15.19",
    "@vue/test-utils": "^2.4.6",
    "jsdom": "^26.1.0",
    "typescript": "^5.8.3",
    "vite": "^6.3.5",
    "vitest": "^3.1.4",
    "vue-tsc": "^2.2.10"
  }
}
```

- [x] **1-2. Vite 기본 파일 추가**

`front/index.html`, `front/vite.config.ts`, `front/tsconfig.json`을 추가한다. `vite.config.ts`는 Vue plugin과 Vitest jsdom 환경을 설정한다.

- [x] **1-3. 의존성 설치**

실행:

```powershell
npm install --prefix front
```

기대 결과: `front/package-lock.json`이 생성되고 오류 없이 종료.

현재 실행 환경에서는 `npm`이 PATH에 없어 임시 npm CLI로 `front` 디렉터리에서 설치했다.

---

## 작업 2. 테스트 먼저 작성하기

**파일:**

- 추가: `front/src/__tests__/shell.spec.ts`

- [x] **2-1. 실패해야 하는 테스트 작성**

테스트는 아직 없는 `routes`, fixture, `App.vue`를 import한다.

검증할 내용:

- route는 `/`, `/dashboard`, `/stocks/:symbol`, `/communities`, `/agents`, `/portfolio`를 포함한다.
- `/`는 `/dashboard`로 redirect한다.
- dashboard fixture에는 ranking, quote, confirmation items가 있다.
- App shell은 주요 navigation label을 렌더링한다.

- [x] **2-2. RED 확인**

실행:

```powershell
npm test --prefix front
```

기대 결과: import 대상이 없어서 실패한다. 이 실패를 확인한 뒤 구현으로 넘어간다.

확인 결과: 구현 전 `App.vue` import 실패로 RED를 확인했다.

---

## 작업 3. route와 fixture 구현

**파일:**

- 추가: `front/src/router/routes.ts`
- 추가: `front/src/fixtures/dashboard-summary.json`
- 추가: `front/src/fixtures/reaction-ranking.json`
- 추가: `front/src/fixtures/quote-snapshots.json`
- 추가: `front/src/fixtures/stock-detail-samsung.json`
- 추가: `front/src/fixtures/community-overview.json`
- 추가: `front/src/fixtures/community-performance.json`
- 추가: `front/src/fixtures/agent-leaderboard.json`
- 추가: `front/src/fixtures/portfolio-disabled.json`

- [x] **3-1. route 정의 추가**

route inventory 문서와 같은 route를 `routes.ts`에 둔다.

- [x] **3-2. fixture JSON 추가**

실제 API 계약이 아니라 mock 화면용 데이터임을 값에서 드러낸다. `portfolio-disabled.json`은 준비 중 상태를 나타낸다.

---

## 작업 4. Vue page shell 구현

**파일:**

- 추가: `front/src/main.ts`
- 추가: `front/src/App.vue`
- 추가: `front/src/pages/DashboardPage.vue`
- 추가: `front/src/pages/StockDetailPage.vue`
- 추가: `front/src/pages/CommunitiesPage.vue`
- 추가: `front/src/pages/AgentsPage.vue`
- 추가: `front/src/pages/PortfolioPage.vue`
- 추가: `front/src/styles.css`

- [x] **4-1. App shell 구현**

상단 navigation과 `<RouterView />`를 둔다. 화면 설명 문구는 투자 자문처럼 보이지 않게 “관찰”, “mock”, “준비 중”을 명시한다.

- [x] **4-2. Dashboard page 구현**

ranking, reaction ratio, quote stale 여부, 기획자 확인 필요 항목을 표시한다.

- [x] **4-3. 나머지 route page 구현**

종목 상세, 커뮤니티 비교, 에이전트 리더보드, 포트폴리오 준비 중 화면을 fixture 기반으로 만든다.

- [x] **4-4. GREEN 확인**

실행:

```powershell
npm test --prefix front
npm run build --prefix front
```

기대 결과: 테스트와 build 모두 통과.

확인 결과: `@types/node`와 ESNext lib 설정을 보정한 뒤 테스트와 build가 통과했다.

---

## 작업 5. 브라우저 확인

**파일:**

- 수정 없음

- [x] **5-1. 개발 서버 실행**

실행:

```powershell
npm run dev --prefix front -- --port 5173
```

기대 결과: `http://127.0.0.1:5173/`에서 앱이 열린다.

- [x] **5-2. Browser로 확인**

확인할 것:

- `/`가 `/dashboard`로 이동한다.
- navigation으로 다섯 화면에 접근한다.
- 모바일 폭에서도 navigation과 카드 텍스트가 겹치지 않는다.
- 화면이 고충실도 디자인처럼 과하게 확정되어 보이지 않는다.

확인 결과: `http://127.0.0.1:5173/`에서 라우트와 모바일 390px 화면을 확인했고, 제목 단어 중간 줄바꿈을 CSS로 보정했다.

---

## 작업 6. PR 마무리

**파일:**

- 필요 시 추가: `docs/work-units/2026-05-15-front-dashboard-shell-vue.md`

- [x] **6-1. 최종 검증**

실행:

```powershell
npm test --prefix front
npm run build --prefix front
git diff --check
```

확인 결과: Vitest 1개 파일 3개 테스트 통과, production build 통과, `git diff --check` 통과.

- [ ] **6-2. 커밋**

실행:

```powershell
git add front docs/superpowers/plans/2026-05-15-front-dashboard-shell-vue.md
git commit -m "[front][feat] Vue 와이어프레임 shell"
```

- [ ] **6-3. PR 생성**

PR 제목:

```text
[front][feat] Vue 와이어프레임 shell
```

라벨:

- `track:front`
- `type:feat`
- `part:front`
- `part:asset`
- `part:docs`
- `size:L`

첫 front 패키지 scaffold라 package, route, fixture, page shell, 테스트, 문서가 함께 들어가 `size:L`로 둔다. PR 본문에는 브라우저 확인 결과와 `기획자 확인 필요`가 mock 화면에 남아 있음을 적는다.
