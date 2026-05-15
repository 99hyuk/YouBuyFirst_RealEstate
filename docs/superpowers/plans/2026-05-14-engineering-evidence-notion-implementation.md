# Engineering Evidence Notion Implementation Plan

> Superseded note: 이 계획은 2026-05-14 당시의 단일 `기술 경험 기록 DB` 구현 계획입니다. 현재 정본은 제품 개발/운영 경험을 `개발자 기술 경험 DB`, Codex/Notion/PR/문서 운영 사고를 `에이전트 운영 로그 DB`에 분리하는 구조입니다. 새 작업자는 최신 기준으로 `docs/ENGINEERING_EVIDENCE_GUIDE.md`, `docs/TROUBLESHOOTING_GUIDE.md`, `docs/CURRENT_HANDOFF.md`를 먼저 확인합니다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Notion recording system so it captures developer-facing engineering evidence, not only ad-hoc troubleshooting, while keeping the root dashboard readable.

**Architecture:** Keep a single Notion database for technical experience records and classify each entry by type, portfolio strength, and measurable improvement fields. Keep the root Notion page as a compact command center with recent summaries and links to full databases. Mirror the new rules in repository docs so future agents follow the same operating model.

**Tech Stack:** Notion MCP tools, GitHub CLI, repository Markdown docs, Superpowers planning workflow, gstack only for browser/visual verification when a Notion or frontend visual check needs it.

---

## File And Notion Surface Map

**Notion surfaces:**

- Root dashboard page: `https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77`
- Existing troubleshooting data source: `collection://ca06b075-a60d-4740-a5a6-7fb6eee29dde`
- Existing work log data source: `collection://8e877781-3fbd-4a2e-99e7-84fac6aad303`
- Existing next work data source: `collection://cf61f402-dfb8-4140-97f8-b8858f64ac26`
- Existing label dictionary page: `https://www.notion.so/35fdf321bd8981a89c8ae4442d5a8da7`

**Repository files:**

- Create: `docs/ENGINEERING_EVIDENCE_GUIDE.md`
- Modify: `AGENTS.md`
- Modify: `docs/WORKFLOW.md`
- Modify: `docs/DOCUMENTATION_GUIDE.md`
- Modify: `docs/CURRENT_HANDOFF.md`
- Modify: `docs/TASKS.md`
- Modify: `docs/TROUBLESHOOTING_GUIDE.md`
- Create: `docs/work-units/2026-05-14-engineering-evidence-notion.md`

**Why this split:** Notion holds the user-facing operating dashboard and records. Repository docs hold durable agent instructions so new chats keep the same classification and quality bar.

---

### Task 1: Reclassify The Existing Notion Troubleshooting Database

**Files:**
- Notion schema only.
- No repository files in this task.

- [ ] **Step 1: Fetch the current data source schema**

Use the Notion fetch tool on:

```text
collection://ca06b075-a60d-4740-a5a6-7fb6eee29dde
```

Expected: schema includes `문제`, `상태`, `심각도`, `영역`, `원인`, `해결`, `재발 방지`, `링크`, `발생일`.

- [ ] **Step 2: Rename the data source**

Use Notion `update_data_source`:

```text
data_source_id: ca06b075-a60d-4740-a5a6-7fb6eee29dde
title: 기술 경험 기록 DB
```

Expected: the data source title changes from `트러블슈팅 DB` to `기술 경험 기록 DB`.

- [ ] **Step 3: Add classification columns**

Use Notion `update_data_source` with these statements:

```sql
ADD COLUMN "종류" SELECT('문제해결':red, '성능개선':green, '품질개선':blue, '기술결정':purple, '도구/운영':yellow);
ADD COLUMN "포트폴리오 후보" SELECT('대표':red, '보조':yellow, '기록':gray)
```

Expected: `종류` and `포트폴리오 후보` appear in the schema.

- [ ] **Step 4: Add measurable-improvement columns**

Use Notion `update_data_source` with these statements:

```sql
ADD COLUMN "측정 지표" RICH_TEXT;
ADD COLUMN "개선 전" RICH_TEXT;
ADD COLUMN "개선 후" RICH_TEXT;
ADD COLUMN "개선율" RICH_TEXT;
ADD COLUMN "측정 방법" RICH_TEXT;
ADD COLUMN "근거 링크" URL
```

Expected: all six performance/quality evidence fields appear in the schema.

- [ ] **Step 5: Add a user-facing description**

Use Notion `update_data_source`:

```text
description: 개발/운영 문제 해결, 성능 개선, 품질 개선, 기술 의사결정을 포트폴리오 후보와 함께 기록하는 DB입니다. 단순 작업 로그가 아니라 근거와 검증을 남기는 공간입니다.
```

Expected: future fetch output includes the description.

- [ ] **Step 6: Initial classification for existing known records**

Update the existing PR body/Notion/Docker/GitHub tool-related records as:

```text
종류: 도구/운영
포트폴리오 후보: 기록
```

If a record is clearly about Docker/Pipeline setup failure with technical root cause, use:

```text
종류: 문제해결
포트폴리오 후보: 보조
```

Expected: old records remain visible but are no longer mistaken for strong portfolio cases.

- [ ] **Step 7: Verify schema and sample records**

Fetch:

```text
collection://ca06b075-a60d-4740-a5a6-7fb6eee29dde
```

Expected: schema includes `종류`, `포트폴리오 후보`, `측정 지표`, `개선 전`, `개선 후`, `개선율`, `측정 방법`, `근거 링크`.

---

### Task 2: Create The Product Planning And Work Context Page

**Files:**
- Notion page only.
- No repository files in this task.

- [ ] **Step 1: Create a Notion child page under the root dashboard**

Use Notion `create_pages` with parent:

```text
page_id: 35fdf321bd89809b87e4fc8eae4c2e77
```

Properties:

```json
{"title": "제품 기획과 작업 맥락"}
```

Icon:

```text
🧭
```

Content:

```md
> 너나사 (YouBuyFirst)를 지금 어떤 제품으로 이해하고, 왜 이 순서로 작업하는지 보는 요약 지도입니다.

## 제품 한 줄 정의

커뮤니티 심리, 종목 언급량, 시세/호가, 모의투자 에이전트를 결합해 개미 심리를 읽는 투자 참고 서비스입니다.

## 현재 MVP 목표

- 네이버 종토방과 에펨코리아 글을 수집합니다.
- 국내 주식과 미국 상장 주식/ETF 언급을 인식합니다.
- 종목별 bullish, bearish, neutral 심리를 저장합니다.
- 30분 집계 기반의 데이터 파이프라인을 안정화합니다.

## 최종 제품 방향

- 커뮤니티별 감성과 언급량을 투자 판단 보조 지표로 보여줍니다.
- 시세/호가와 커뮤니티 지표를 함께 보여주는 대시보드를 만듭니다.
- 모의투자와 AI 에이전트로 커뮤니티 신호의 성과를 검증합니다.

## 현재 우선순위

1. 수집 타깃과 소스 정책 정리
2. 프론트 대시보드 shell과 mock 경험
3. 시세 snapshot 계약
4. 기술 경험 기록 체계 정리

## 보류 중인 것

- OCR 자산 연동
- 실거래
- 로그인/보안
- 운영 배포 자동화
- CAPTCHA 우회, 프록시 회전, fingerprint 위장

## Codex가 이해한 판단 기준

- 작게 PR을 나눕니다.
- 포트폴리오가 될 만한 기술 경험은 근거와 검증을 남깁니다.
- 사용자의 요청도 모순, 리스크, 더 나은 대안이 있으면 질문하거나 반박합니다.
- Superpowers는 기획/설계/구현/검증의 게이트로 쓰고, gstack은 브라우저 QA나 시각 확인이 실제로 필요할 때 씁니다.

## 트랙별 현재 상태

| 트랙 | 상태 |
| --- | --- |
| crawl | CrawlTarget과 소스별 수집 정책 설계가 다음 후보 |
| data | 종목 인식, 감성 분류, 30분 집계 MVP 기반 존재 |
| market | quote snapshot 계약 설계 전 |
| trade | 모의 계좌/주문 도메인 설계 전 |
| agent | 전략 에이전트 입력 계약 설계 전 |
| front | dashboard shell과 mock 화면 설계 전 |
| ops | Notion, PR, 문서 운영 기준 정리 중 |

## 다음 의사결정 후보

- 종목 게시판형 소스를 어떻게 우선순위 큐로 수집할지
- 공개 배포 시 어떤 커뮤니티 소스를 켤지
- 시세 provider를 실시간, 지연, 사용자 개인 API 중 무엇으로 시작할지
```

Expected: a new page URL is returned.

- [ ] **Step 2: Save the page URL for later tasks**

Record the returned URL in a scratch note for Task 3 and Task 4.

Expected: the root dashboard can link to this page.

---

### Task 3: Rebuild The Root Dashboard Into A Compact Command Center

**Files:**
- Notion root page only.
- No repository files in this task.

- [ ] **Step 1: Fetch the root page and preserve child links**

Use Notion fetch:

```text
https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77
```

Expected: output includes links to `라벨/태그 사전`, `Archive & Admin`, and inline databases.

- [ ] **Step 2: Replace root content with compact sections**

Use Notion `update_page` with `replace_content`. Preserve these child links:

```text
<page url="https://www.notion.so/35fdf321bd8981a89c8ae4442d5a8da7">라벨/태그 사전</page>
<page url="[Task 2 returned URL]">제품 기획과 작업 맥락</page>
<page url="https://www.notion.so/35fdf321bd89818783d0c587e0bba319">Archive & Admin</page>
```

Use this content, replacing `[Task 2 returned URL]` with the actual page URL:

```md
> 커뮤니티 크롤링/감성 ingestion MVP 운영판. 루트는 전체 기록을 길게 읽는 곳이 아니라 현재 상태, 최근 기록, 다음 이동 경로를 보는 대시보드입니다.

## 오늘의 상태

**GitHub**: `main` 최신, 열린 PR 없음
**최신 작업**: 기술 경험 기록 체계 설계 및 구현 준비
**다음 초점**: `crawl`의 `CrawlTarget`, `front`의 dashboard shell, `market`의 quote snapshot
**기록 방식**: 작업은 작업 로그, 기술 경험은 기술 경험 기록 DB, 후보는 다음 작업 DB에 남깁니다.

## 빠른 이동

<table header-row="true">
<tr><td>이동</td><td>용도</td></tr>
<tr><td><page url="[Task 2 returned URL]">제품 기획과 작업 맥락</page></td><td>현재 제품 이해, 우선순위, 트랙 상태</td></tr>
<tr><td><page url="https://www.notion.so/35fdf321bd8981a89c8ae4442d5a8da7">라벨/태그 사전</page></td><td>GitHub 라벨과 Notion 태그 의미</td></tr>
<tr><td><database url="https://www.notion.so/35fdf321bd89814aad25e37811f18703" inline="false" data-source-url="collection://8e877781-3fbd-4a2e-99e7-84fac6aad303">작업 로그 DB</database></td><td>전체 PR 작업 기록</td></tr>
<tr><td><database url="https://www.notion.so/35fdf321bd89818b8829fcb8c8bc2f39" inline="false" data-source-url="collection://ca06b075-a60d-4740-a5a6-7fb6eee29dde">기술 경험 기록 DB</database></td><td>문제해결, 성능개선, 품질개선, 기술결정</td></tr>
<tr><td><database url="https://www.notion.so/35fdf321bd8981c88a36cfeba9d708ab" inline="false" data-source-url="collection://cf61f402-dfb8-4140-97f8-b8858f64ac26">다음 작업 DB</database></td><td>다가오는 작업 후보</td></tr>
</table>

## 최근 작업

- PR #18 · GitHub PR 본문 UTF-8 규칙
- PR #17 · part 라벨과 pipeline 명명 정리
- PR #16 · 짧은 병렬 트랙명 정리

## 최근 기술 경험

- PR 본문 한글 깨짐 원인 분석과 UTF-8 파일 방식 재발 방지
- Pipeline `pyproject.toml` BOM으로 인한 pip install 실패 해결
- Notion schema rename 중 suffix 컬럼 생성 문제 해결

## 트랙 지도

| 트랙 | 라벨 | 역할 |
| --- | --- | --- |
| 🕸️ crawl | `track:crawl` | 커뮤니티 글 수집과 수집 정책 |
| 📊 data | `track:data` | 종목 인식, 감성, 열기 지수, 30분 집계 |
| 💹 market | `track:market` | 시세, 호가, quote cache, WebSocket |
| 💰 trade | `track:trade` | 가상 계좌, 주문, 체결, 수익률 |
| 🧠 agent | `track:agent` | AI 전략 판단과 결정 로그 |
| 🖥️ front | `track:front` | 대시보드와 사용자 화면 |
| 🧭 ops | `track:ops` | 기획, 문서, Notion, PR 운영 |

## 운영 원칙

루트에는 전체 DB를 펼쳐 두지 않습니다. 최근 기록은 3-5개만 보여주고, 전체 기록은 DB 링크에서 봅니다.

<page url="https://www.notion.so/35fdf321bd89818783d0c587e0bba319">Archive & Admin</page>
```

Expected: root page no longer embeds full inline DBs.

- [ ] **Step 3: Verify root page readability**

Fetch the root page again.

Expected:

- It contains `최근 작업`, `최근 기술 경험`, `빠른 이동`.
- It does not include inline database blocks for every row-heavy database.
- It links to `제품 기획과 작업 맥락`.

If the user explicitly asks for visual confirmation, use gstack/browser to open the Notion URL and inspect the first viewport.

---

### Task 4: Update Repository Documentation For Engineering Evidence

**Files:**
- Create: `docs/ENGINEERING_EVIDENCE_GUIDE.md`
- Modify: `AGENTS.md`
- Modify: `docs/WORKFLOW.md`
- Modify: `docs/DOCUMENTATION_GUIDE.md`
- Modify: `docs/CURRENT_HANDOFF.md`
- Modify: `docs/TASKS.md`
- Modify: `docs/TROUBLESHOOTING_GUIDE.md`
- Create: `docs/work-units/2026-05-14-engineering-evidence-notion.md`

- [ ] **Step 1: Create `docs/ENGINEERING_EVIDENCE_GUIDE.md`**

Create this exact file:

```md
# 기술 경험 기록 가이드

기술 경험 기록은 개발자로서 설명할 수 있는 문제 해결, 성능 개선, 품질 개선, 기술 의사결정을 모으는 공간입니다. 단순 작업 로그와 다릅니다.

## 기록 종류

| 종류 | 기록 대상 |
| --- | --- |
| `문제해결` | 개발/운영 중 막힌 문제를 원인까지 파고 해결한 기록 |
| `성능개선` | 전후 수치가 있는 개선 기록 |
| `품질개선` | 안정성, 테스트, 검증, 에러 처리, 운영 안전성 개선 |
| `기술결정` | 여러 선택지 중 왜 이 구조를 택했는지 남기는 기록 |
| `도구/운영` | GitHub, Notion, CI, Docker 같은 개발 운영 도구 문제 |

## 포트폴리오 후보

| 값 | 의미 |
| --- | --- |
| `대표` | 면접이나 자기소개서의 메인 사례로 쓸 만한 강한 경험 |
| `보조` | 필요하면 언급할 수 있지만 주력 사례는 아닌 경험 |
| `기록` | 프로젝트 운영상 필요하지만 포트폴리오 소재는 아닌 기록 |

## 대표 사례 기준

- 시스템 영향이 분명합니다.
- 원인을 직접 조사해 좁혀간 과정이 있습니다.
- 해결 전후 검증이 있습니다.
- 가능하면 정량 지표나 재발 방지 장치가 있습니다.

## 성능/품질 개선 기록 필드

- `측정 지표`: p95 응답시간, batch 처리 시간, 쿼리 실행 시간, 테스트 시간 등
- `개선 전`: 변경 전 수치
- `개선 후`: 변경 후 수치
- `개선율`: 퍼센트 또는 배수
- `측정 방법`: 어떤 명령, 로그, benchmark로 측정했는지
- `근거 링크`: PR, CI log, benchmark 결과, 관련 문서

## 작성 원칙

- 억지로 성능 개선을 만들지 않습니다.
- 단순 도구 사고는 `도구/운영`과 `기록`으로 둡니다.
- 개발자 포트폴리오 후보는 `대표` 또는 `보조`로 표시합니다.
- 명령어만 쓰지 않고, 어떤 판단과 검증을 했는지 씁니다.
```

Expected: guide exists and is Korean-first.

- [ ] **Step 2: Update `AGENTS.md`**

Add these bullets under working/PR rules:

```md
- Codex는 사용자의 요구를 무조건 수용하지 않습니다. 모순, 리스크, 더 나은 대안이 보이면 질문하거나 반박합니다.
- Superpowers는 기획, 설계, 구현 계획, 검증, 디버깅 게이트로 사용합니다.
- gstack은 브라우저 QA, 시각 확인, 성능/품질 검증처럼 실제 확인 가치가 있을 때 사용합니다.
- 개발/운영 문제 해결, 성능 개선, 품질 개선, 기술 의사결정은 `docs/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 Notion 기술 경험 기록 DB에 남깁니다.
```

Expected: new agents see debate, Superpowers/gstack, and engineering evidence expectations.

- [ ] **Step 3: Update `docs/WORKFLOW.md`**

Replace the troubleshooting-only Notion wording with:

```md
기술 경험 기록은 작업일지보다 깊게 씁니다. 문제를 조사했거나, 성능/품질을 개선했거나, 중요한 기술 결정을 내렸다면 Notion 기술 경험 기록 DB에 `문제해결`, `성능개선`, `품질개선`, `기술결정`, `도구/운영` 중 하나로 남깁니다. 작성 구조는 `docs/ENGINEERING_EVIDENCE_GUIDE.md`와 `docs/TROUBLESHOOTING_GUIDE.md`를 함께 봅니다.
```

Expected: workflow points to the broader concept.

- [ ] **Step 4: Update `docs/DOCUMENTATION_GUIDE.md`**

Add `docs/ENGINEERING_EVIDENCE_GUIDE.md` to the "need only when relevant" table:

```md
| `docs/ENGINEERING_EVIDENCE_GUIDE.md` | 문제 해결, 성능 개선, 품질 개선, 기술 결정 기록 기준을 확인할 때 |
```

Expected: new agents can find the guide without reading all docs.

- [ ] **Step 5: Update `docs/CURRENT_HANDOFF.md`**

Add recent decisions:

```md
- Notion의 기존 트러블슈팅 DB는 `기술 경험 기록 DB`로 확장합니다.
- 기술 경험 기록은 `문제해결`, `성능개선`, `품질개선`, `기술결정`, `도구/운영`으로 구분합니다.
- 포트폴리오 후보는 `대표`, `보조`, `기록`으로 나누며, 단순 도구 운영 이슈는 기본적으로 `기록`으로 둡니다.
```

Expected: handoff explains the new Notion purpose.

- [ ] **Step 6: Update `docs/TROUBLESHOOTING_GUIDE.md`**

Add a short boundary section near the top:

```md
## 기술 경험 기록과의 관계

트러블슈팅은 `기술 경험 기록 DB` 안의 `문제해결` 유형입니다. 모든 기술 경험이 트러블슈팅은 아닙니다. 성능 개선, 품질 개선, 기술 의사결정은 `docs/ENGINEERING_EVIDENCE_GUIDE.md` 기준으로 기록합니다.
```

Expected: troubleshooting no longer claims the whole evidence space.

- [ ] **Step 7: Update `docs/TASKS.md`**

Add completed item:

```md
- [x] Notion 기술 경험 기록 체계 설계
```

Add near-term item if implementation is not fully complete:

```md
- [ ] 기술 경험 기록 DB의 기존 카드 분류 보정
```

Expected: task list reflects the new operating system.

- [ ] **Step 8: Create work-unit note**

Create `docs/work-units/2026-05-14-engineering-evidence-notion.md`:

```md
# 2026-05-14 기술 경험 기록 Notion 재구성

## 한눈에 보기

Notion의 기존 트러블슈팅 중심 기록을 기술 경험 기록 체계로 확장합니다. 목적은 취업 준비에 쓸 수 있는 문제 해결, 성능 개선, 품질 개선, 기술 의사결정 근거를 쌓는 것입니다.

## 바뀐 기준

- `트러블슈팅 DB`는 `기술 경험 기록 DB`로 확장합니다.
- 기록 종류는 `문제해결`, `성능개선`, `품질개선`, `기술결정`, `도구/운영`입니다.
- 포트폴리오 후보는 `대표`, `보조`, `기록`으로 나눕니다.
- 루트 대시보드는 전체 DB를 펼치지 않고 최근 3-5개와 링크만 보여줍니다.

## 다음 작업자 메모

성능 개선은 억지로 만들지 않습니다. 실제 병목이나 반복 비용이 보일 때 먼저 측정 기준을 잡고, 개선 전후 수치를 남깁니다.
```

Expected: work unit captures the change context.

---

### Task 5: Verify, Publish, And Record The Implementation PR

**Files:**
- All files changed in Tasks 1-4.

- [ ] **Step 1: Run local markdown hygiene**

Run:

```bash
git diff --check
```

Expected: exit code 0 and no output.

- [ ] **Step 2: Search for stale wording**

Run:

```bash
rg -n "트러블슈팅 DB|기술 경험 기록|성능개선|포트폴리오 후보|gstack|Superpowers" AGENTS.md docs
```

Expected:

- Stale `트러블슈팅 DB` references only remain where explaining the old name or specific troubleshooting guide.
- `기술 경험 기록` appears in `AGENTS.md`, `docs/WORKFLOW.md`, `docs/CURRENT_HANDOFF.md`, and `docs/ENGINEERING_EVIDENCE_GUIDE.md`.
- `gstack` and `Superpowers` usage principles appear in `AGENTS.md` or the new guide.

- [ ] **Step 3: Verify Notion schema**

Fetch:

```text
collection://ca06b075-a60d-4740-a5a6-7fb6eee29dde
```

Expected: title is `기술 경험 기록 DB`, and schema includes `종류`, `포트폴리오 후보`, `측정 지표`, `개선 전`, `개선 후`, `개선율`, `측정 방법`, `근거 링크`.

- [ ] **Step 4: Verify Notion root**

Fetch:

```text
https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77
```

Expected: root page has compact recent sections and links to full DBs.

- [ ] **Step 5: Commit**

Run:

```bash
git add AGENTS.md docs/ENGINEERING_EVIDENCE_GUIDE.md docs/WORKFLOW.md docs/DOCUMENTATION_GUIDE.md docs/CURRENT_HANDOFF.md docs/TASKS.md docs/TROUBLESHOOTING_GUIDE.md docs/work-units/2026-05-14-engineering-evidence-notion.md
git commit -m "[ops][docs] 기술 경험 기록 Notion 체계"
```

Expected: commit succeeds.

- [ ] **Step 6: Push**

Run:

```bash
git push -u origin codex/ops-engineering-evidence-notion
```

Expected: branch is pushed.

- [ ] **Step 7: Create PR using UTF-8 no BOM body file**

Create the PR body as a UTF-8 no BOM temp file. Do not pipe Korean text to `gh`.

PowerShell pattern:

```powershell
$body = @'
## 🧭 한눈에 보기

> Notion 기록 체계를 작업 로그/기술 경험/다음 작업으로 나누고, 기술 경험 기록에 문제해결·성능개선·품질개선·기술결정을 담을 수 있게 정리합니다.

| 항목 | 내용 |
| --- | --- |
| 작업 트랙 | `track:ops` |
| 작업 타입 | `type:docs` |
| 변경 파트 | `part:rule`, `part:docs` |
| 크기 | `size:L` |
| Notion 기록 | PR 생성 후 반영 |

## 🧩 바뀐 내용

- 기존 트러블슈팅 중심 DB를 기술 경험 기록 DB로 재정의했습니다.
- 성능/품질 개선 전후 수치를 남길 필드를 추가했습니다.
- 루트 대시보드를 최근 3-5개 중심으로 정리했습니다.
- 제품 기획과 작업 맥락 페이지를 추가했습니다.
- 사용자와 토론하며 반박하는 Codex 협업 원칙과 Superpowers/gstack 사용 원칙을 문서화했습니다.

## ✅ 검증 결과

- Notion schema에서 기술 경험 기록 필드를 확인했습니다.
- Notion root가 전체 DB 대신 최근 요약과 링크를 보여주는지 확인했습니다.
- `git diff --check`가 통과했습니다.

## 🗂️ Notion 기록

- 작업일지: PR 생성 후 링크 반영
- 기술 경험 기록: 해당 없음
'@
$tmp = Join-Path $env:TEMP 'engineering-evidence-pr.md'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tmp, $body, $utf8NoBom)
gh pr create --repo 99hyuk/YouBuyFirst --base main --head codex/ops-engineering-evidence-notion --title "[ops][docs] 기술 경험 기록 Notion 체계" --body-file $tmp --label track:ops --label type:docs --label size:L --label part:rule --label part:docs
Remove-Item -LiteralPath $tmp
```

Expected: PR URL is returned.

- [ ] **Step 8: Verify PR body encoding**

Run:

```powershell
gh pr view <number> --repo 99hyuk/YouBuyFirst --json body --jq .body
```

Expected: Korean text and emoji render normally in terminal output.

- [ ] **Step 9: Wait for CI**

Run:

```bash
gh pr checks <number> --repo 99hyuk/YouBuyFirst --watch --interval 10
```

Expected: Backend and Pipeline pass.

- [ ] **Step 10: Update Notion work log**

Create a work log card in `collection://8e877781-3fbd-4a2e-99e7-84fac6aad303` with:

```json
{
  "작업": "PR #<number> · 기술 경험 기록 Notion 체계",
  "상태": "Open",
  "트랙": "ops",
  "변경 파트": "[\"rule\", \"docs\"]",
  "크기": "L",
  "PR": "https://github.com/99hyuk/YouBuyFirst/pull/<number>",
  "검증": "Notion schema 확인, root dashboard 확인, git diff --check 통과, CI 확인",
  "다음 메모": "기술 경험 기록은 문제해결, 성능개선, 품질개선, 기술결정, 도구/운영으로 구분합니다."
}
```

Expected: work log card appears.

- [ ] **Step 11: Merge after CI**

Run:

```bash
gh pr merge <number> --repo 99hyuk/YouBuyFirst --squash --delete-branch --subject "[ops][docs] 기술 경험 기록 Notion 체계" --body "Notion과 문서의 기록 체계를 기술 경험 중심으로 재구성한다."
```

Expected: PR is merged and remote branch is deleted.

- [ ] **Step 12: Sync local main**

Run:

```bash
git fetch --prune origin
git checkout main
git pull --ff-only
```

Expected: local `main` is up to date and clean.

---

## Plan Self-Review

**Spec coverage:** The plan covers the `기술 경험 기록 DB`, portfolio candidate field, performance/quality metric fields, compact root dashboard, product planning page, Codex debate principle, Superpowers/gstack usage principle, repository docs, PR/Notion records, and verification.

**Placeholder scan:** No `TBD`, `TODO`, or unspecified steps remain. Task 2 has one required substitution, `[Task 2 returned URL]`, because Notion returns the page URL only at runtime; the step explicitly explains how to replace it.

**Type consistency:** Notion properties use the same names throughout: `종류`, `포트폴리오 후보`, `측정 지표`, `개선 전`, `개선 후`, `개선율`, `측정 방법`, `근거 링크`, `변경 파트`.
