# Notion PR UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved B + A hybrid information design to the Notion project hub and GitHub PR workflow.

**Architecture:** Notion becomes the visual project command center plus card-style work log. GitHub PR bodies mirror the same card model so merged PRs can be copied into Notion with minimal editing.

**Tech Stack:** Notion MCP tools, GitHub Markdown, repository markdown docs.

---

### Task 1: Update Repository PR Documentation

**Files:**
- Modify: `.github/pull_request_template.md`
- Modify: `docs/GIT_CONVENTION.md`
- Modify: `docs/WORKFLOW.md`
- Modify: `docs/CURRENT_HANDOFF.md`
- Modify: `docs/TASKS.md`
- Create: `docs/work-units/2026-05-13-notion-pr-ui-polish.md`

- [ ] **Step 1: Replace PR template with a card-style reviewer flow**

Use a small metadata table, outcome-first verification, details blocks for commands, and explicit Notion logging prompt.

- [ ] **Step 2: Update workflow docs**

Document that PRs should use the same structure as Notion work cards: at-a-glance, changed parts, verification outcomes, risks, next agent memo.

- [ ] **Step 3: Update handoff and task list**

Record the Notion command-center decision and the new work-unit file.

- [ ] **Step 4: Verify markdown hygiene**

Run: `git diff --check`

Expected: no output and exit code 0.

### Task 2: Polish Notion Pages

**Pages:**
- Project hub: `https://www.notion.so/35fdf321bd89809b87e4fc8eae4c2e77`
- Work log: `https://www.notion.so/35fdf321bd898183bd4ec871623d8917`
- Troubleshooting: `https://www.notion.so/35fdf321bd8981559e31e55584337cea`
- Daily log: `https://www.notion.so/35fdf321bd8981e8bf8bcbdf85f47fbb`
- PR operations: `https://www.notion.so/35fdf321bd89815c9808ff01a683f4bc`

- [ ] **Step 1: Preserve child-page links**

Fetch the project hub and include existing child page links when replacing or restructuring hub content.

- [ ] **Step 2: Add icons and structured sections**

Use Notion page icons and structured markdown sections. The hub should show status snapshot, quick navigation, latest work, and next work queue.

- [ ] **Step 3: Rewrite work log and troubleshooting content**

Use compact PR-card and incident-card structures with clear headings, status markers, and concise summaries.

- [ ] **Step 4: Add current PR operation guidance**

Make the GitHub PR operations page mirror the repository PR template.

### Task 3: Publish PR

**Files:**
- All files changed in Task 1 and the plan/spec docs.

- [ ] **Step 1: Review staged diff**

Run: `git status -sb` and `git diff --stat`.

- [ ] **Step 2: Commit with Korean convention**

Commit title: `[ops][docs] Notion과 PR 문서 UI 개선`

- [ ] **Step 3: Push and open PR**

Use branch `codex/notion-pr-ui-design`, add `type:docs`, `part:rule`, `part:docs`, `size:M` or `size:L` depending on final file count.

- [ ] **Step 4: Verify CI and merge**

Wait for Backend and Pipeline checks. If both pass, squash merge and delete the remote branch.
