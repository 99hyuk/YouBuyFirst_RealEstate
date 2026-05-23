# Notion + GitHub PR UI Design

## Decision

Adopt a B + A hybrid structure:

- B, the work logbook model, is the default information unit.
- A, the project command center model, is used for the Notion hub top section.

The result should feel like a small operating room for the project: the first screen answers "what is the state right now?", and each PR/work unit answers "what changed, why, how was it verified, and what should the next agent know?"

## Goals

- Make Notion useful at a glance, not just an archive of plain text.
- Make PR bodies easy for a human reviewer to scan before reading details.
- Keep the structure conservative enough that future agents can reproduce it without design drift.
- Keep all content Korean-first, while preserving code identifiers and commands in their original form.

## Notion Hub Structure

The project hub should use a command-center layout:

1. Project header
   - Page icon and concise project identity.
   - One short paragraph describing what the hub is for.
2. Status snapshot
   - Current branch/PR state.
   - Latest merged PR.
   - Next recommended work.
   - Current verification posture.
3. Quick navigation
   - Work log.
   - Troubleshooting.
   - GitHub PR operation notes.
   - Repository/docs references.
4. Latest work cards
   - Each card follows the PR card model below.
5. Next work queue
   - Small list of concrete next work units.

Notion page icons should be used consistently:

- Project hub: compass or dashboard icon.
- Work log: calendar or notebook icon.
- Troubleshooting: rescue/safety icon.
- PR operation notes: branch or checklist icon.
- Individual PR log entries: merged/check icon when done, warning icon when blocked.

## Notion Work Log Card Model

Each work log entry should be written as a compact PR card:

1. Header
   - PR number and title.
   - Status.
   - Labels or changed part.
   - Date.
2. Why
   - One sentence explaining the reason for the work.
3. What changed
   - Three to five bullets grouped by user-visible intent, not file-by-file noise.
4. Verification
   - Natural-language result first.
   - Commands only when useful.
5. Links
   - GitHub PR.
   - Related local docs.
   - Troubleshooting page if applicable.
6. Next agent memo
   - One to three bullets about what to watch next.

## Notion Troubleshooting Model

Troubleshooting entries should use a clear incident card:

1. Symptom
2. Impact
3. Root cause
4. Fix
5. Verification
6. Prevention

Use visual separators and callouts when the issue is likely to recur. Avoid long raw logs unless they are essential.

## GitHub PR Body Structure

The PR template should mirror the work log card so a merged PR can be copied into Notion with minimal editing.

Recommended sections:

1. At-a-glance summary
   - One sentence.
   - Small metadata table for type, part, size, status.
2. Reviewer path
   - What to read first.
   - What can be skimmed.
3. What changed
   - Grouped bullets.
4. Why this PR size
   - Especially important for size M/L.
5. Verification
   - Human-readable result bullets first.
   - Command block hidden in `<details>`.
6. Risk and follow-up
   - Remaining risk.
   - Data/runtime impact.
   - Next task candidate.

Use GitHub Markdown affordances:

- Tables for metadata.
- `<details>` for commands and verbose evidence.
- Task lists only for reviewer checklist items.
- GitHub callout blocks such as `[!NOTE]`, `[!WARNING]`, and `[!TIP]` when they improve scanning.

## Implementation Scope

MVP polish should update:

- The existing Notion project hub and child pages.
- The current PR template.
- Workflow and Git convention docs so future agents follow the same structure.
- Current handoff with Notion page links and logging rules.

Out of scope:

- Creating a complex Notion database unless the user requests it.
- Automating Notion updates from GitHub Actions.
- Requiring screenshots in every PR.

## Acceptance Criteria

- The Notion hub is visually scannable on first open.
- Work log and troubleshooting pages use icons and structured sections.
- The GitHub PR template reads like a review aid, not a form dump.
- Verification is written as outcomes first and commands second.
- A future agent can follow the docs without asking how PR/Notion logging should look.

## Open Questions

- Whether to add real Notion databases later for PR logs and troubleshooting entries.
- Whether to add a bot workflow that posts PR summaries into Notion automatically.
