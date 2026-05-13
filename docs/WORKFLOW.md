# Conservative Development Workflow

## Rule

One feature, bugfix, or infrastructure change should be one PR.

Do not bundle unrelated work. If a task touches multiple subsystems, split it unless those changes must land together to keep the app working.

## Work Unit Steps

1. Read `docs/CONTEXT.md`, `docs/PROJECT_BRIEF.md`, and `docs/TASKS.md`.
2. Create a work-unit doc:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\new-work-unit.ps1 -Name "crawler-parser-hardening"
   ```

3. Implement only that work unit.
4. Run relevant verification.
5. Update the work-unit doc with what changed and what remains.
6. Open a draft PR:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\open-pr.ps1 -Title "Harden crawler parsers" -Body "See docs/work-units/..." -CommitMessage "Harden crawler parsers"
   ```

## PR Size Guide

- Preferred: fewer than 10 files changed.
- Acceptable: one subsystem plus tests and docs.
- Avoid: backend + worker + product scope + infra in one PR.

## Branch Names

Use:

```text
codex/<short-task-name>
```

Examples:

- `codex/crawler-parser-hardening`
- `codex/add-ci`
- `codex/instrument-master-import`

## Required PR Contents

- Summary of behavior change
- Link to work-unit doc
- Test commands and results
- Known risks
- Follow-up tasks
