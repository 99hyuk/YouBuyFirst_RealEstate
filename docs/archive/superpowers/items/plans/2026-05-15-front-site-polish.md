# Front Site Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the `/dashboard` wireframe so it reads like a user-facing service page, using the approved `Briefing + Terminal` direction.

**Architecture:** Keep the existing Vue 3 route shell. Update only the dashboard-facing fixture, dashboard page, app header copy, CSS, and shell test so the route contract remains stable while the first screen gains a briefing hero and dense reaction board.

**Tech Stack:** Vue 3, Vite, TypeScript, Vue Router, Vitest, Vue Test Utils, jsdom, CSS.

---

## File Structure

- Modify `front/src/__tests__/shell.spec.ts`: add assertions for the approved briefing/terminal copy and planning boundary.
- Modify `front/src/fixtures/dashboard-summary.json`: change dashboard copy from internal shell language to briefing-oriented copy; keep `confirmationNeeded`.
- Modify `front/src/fixtures/reaction-ranking.json`: add small display metadata used by the reaction board, without pretending this is a backend API contract.
- Modify `front/src/App.vue`: make the header subtitle more product-facing while preserving navigation test IDs.
- Modify `front/src/pages/DashboardPage.vue`: replace the plain grid with briefing hero, reaction board, feature rail, quote status, and planning boundary sections.
- Modify `front/src/styles.css`: add responsive site-like layout primitives and keep mobile stacking stable.

## Task 1. Test the Approved Dashboard Direction

**Files:**

- Modify: `front/src/__tests__/shell.spec.ts`

- [x] **Step 1: Add a failing assertion for the new first-screen direction**

Add the assertions below to the existing `renders navigation for every planned route` test after the navigation checks.

```ts
expect(wrapper.text()).toContain('오늘 커뮤니티 브리핑');
expect(wrapper.text()).toContain('투자자들이 먼저 떠드는 종목을 읽습니다');
expect(wrapper.text()).toContain('반응 터미널');
expect(wrapper.text()).toContain('기획자 확인 필요');
```

- [x] **Step 2: Run the test and verify RED**

Run from `front/`:

```powershell
$npmCli = Join-Path $env:TEMP 'codex-npm-10.9.2\package\bin\npm-cli.js'
node $npmCli test
```

Expected: FAIL because the current dashboard does not render `오늘 커뮤니티 브리핑` or `반응 터미널`.

Observed: after installing dependencies in this worktree, Vitest failed on `오늘 커뮤니티 브리핑`, which confirmed the test was RED for the intended missing behavior.

## Task 2. Implement Briefing + Terminal Dashboard Markup

**Files:**

- Modify: `front/src/fixtures/dashboard-summary.json`
- Modify: `front/src/fixtures/reaction-ranking.json`
- Modify: `front/src/App.vue`
- Modify: `front/src/pages/DashboardPage.vue`

- [x] **Step 1: Update dashboard summary fixture**

Set `front/src/fixtures/dashboard-summary.json` to:

```json
{
  "productName": "너나사",
  "title": "오늘 커뮤니티 브리핑",
  "headline": "투자자들이 먼저 떠드는 종목을 읽습니다",
  "description": "커뮤니티 반응이 커진 종목을 mock 데이터로 빠르게 훑어보고, 실제 API 계약 전까지 필요한 기획 질문을 남깁니다.",
  "notice": "투자 자문이 아니라 커뮤니티 반응을 관찰하는 참고 화면입니다.",
  "confirmationNeeded": ["열기 지수 용어 확정", "기본 시간창 1h, 24h, 30m 중 선택", "AI 3줄 요약 placeholder 문구 확정"]
}
```

- [x] **Step 2: Add minimal display metadata to ranking fixture**

In each `reactionRanking.items[]`, add:

```json
"priceStatus": "mock quote"
```

For stale/mock distinction, use `"stale quote"` on the Tesla item. Do not add provider or endpoint fields.

- [x] **Step 3: Update app header copy**

In `front/src/App.vue`, change the eyebrow copy to:

```vue
<p class="eyebrow">커뮤니티 반응으로 시장의 먼저 흔들리는 지점을 관찰합니다.</p>
```

Keep all `data-testid` attributes and route links unchanged.

- [x] **Step 4: Replace dashboard page markup**

Use the existing imports and replace the template with sections for:

- `briefing-hero`
- `terminal-board`
- `feature-rail`
- `planning-boundary`

The board must render each ranking item, direction percentages, keywords, and `priceStatus`.

- [x] **Step 5: Run test and verify GREEN**

Run from `front/`:

```powershell
$npmCli = Join-Path $env:TEMP 'codex-npm-10.9.2\package\bin\npm-cli.js'
node $npmCli test
```

Expected: PASS, 1 test file and 3 tests.

Observed: Vitest passed with 1 test file and 3 tests.

## Task 3. Add Responsive Site-Like Styling

**Files:**

- Modify: `front/src/styles.css`

- [x] **Step 1: Add CSS for the briefing and terminal layout**

Add classes for `.briefing-hero`, `.briefing-copy`, `.hero-card`, `.terminal-board`, `.terminal-row`, `.direction-stack`, `.direction-bar`, `.feature-rail`, `.feature-card`, and `.planning-boundary`.

Keep cards at `8px` radius or less. Avoid decorative gradients/orbs. Use restrained greens, dark text, white panels, and small pills.

- [x] **Step 2: Add mobile stacking rules**

Inside `@media (max-width: 760px)`, stack the briefing hero, terminal rows, direction bars, and feature rail into one column. Keep `word-break: keep-all` on headings.

- [x] **Step 3: Run tests and build**

Run from `front/`:

```powershell
$npmCli = Join-Path $env:TEMP 'codex-npm-10.9.2\package\bin\npm-cli.js'
node $npmCli test
node $npmCli run build
```

Expected: both commands pass.

Observed: Vitest passed with 3 tests and production build passed.

## Task 4. Browser QA and PR Finish

**Files:**

- Modify: `docs/superpowers/plans/2026-05-15-front-site-polish.md`

- [x] **Step 1: Start or reuse a Vite server**

Run from `front/`:

```powershell
$npmCli = Join-Path $env:TEMP 'codex-npm-10.9.2\package\bin\npm-cli.js'
node $npmCli run dev -- --port 5174
```

Use `5174` to avoid the older preview on `5173`.

- [x] **Step 2: Verify in browser**

Check:

- `/` redirects to `/dashboard`.
- Desktop first viewport shows briefing hero and reaction board.
- Mobile 390px has no incoherent overlap.
- Console error count is zero.

Observed: `http://127.0.0.1:5174/` redirected to `/dashboard`; desktop and 390px mobile DOM checks found the briefing hero, terminal board, ranking content, and navigation; console error count was 0. In-app screenshot capture timed out, so verification used the live browser tab plus DOM and console checks.

- [x] **Step 3: Run final verification**

Run:

```powershell
$npmCli = Join-Path $env:TEMP 'codex-npm-10.9.2\package\bin\npm-cli.js'
node $npmCli test
node $npmCli run build
git diff --check origin/main...HEAD
```

Observed after rebasing onto latest `origin/main`: Vitest passed with 1 test file and 3 tests, production build passed, and `git diff --check origin/main...HEAD` passed.

- [ ] **Step 4: Commit, push, PR**

Commit title:

```text
[front][feat] 사이트형 대시보드 와이어프레임
```

PR labels:

- `track:front`
- `type:feat`
- `part:front`
- `part:asset`
- `part:docs`
- `size:M`

PR body must state this is still a wireframe, not a final design.
