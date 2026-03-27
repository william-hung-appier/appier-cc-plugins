# Design: BE Warm-Up v2 — Codebase-Aware Task Assessment

**Date:** 2026-03-28
**Plugin:** cs-jira-query
**Status:** Draft

## Summary

Enhance the `/cs-jira-query:be-warm-up` command to filter by issue type (Task + Bug, not Story), fetch full ticket descriptions via an updated `ticket-reader` agent, and deeply inspect each task's corresponding codebase on `origin/staging` to assess whether the task is actionable or needs clarification. Uses a new `task-assessor` subagent per task for context isolation and parallel execution.

## Motivation

The current `be-warm-up` command fetches backlog tasks and provides FACT/ASSUME analysis based solely on ticket text. Engineers still need to manually check the codebase to know if a task is actionable. This upgrade automates that step — the agent goes into each repo, reads the staging branch, and tells you whether you can start implementing or need to ask the reporter questions first.

## Components

### 1. `jira.py backlog` — Add `--type` filter

**Usage:**
```bash
jira.py backlog CR --sp 10 --prefix "[BE]" --type "Task,Bug"
```

Adds an optional `--type` flag that appends `AND issuetype in (Task, Bug)` to the JQL query. Default: no type filter (backward compatible).

**Implementation:** Add `--type` to the `parse_opts` spec in `cmd_backlog`. If provided, split by comma and build the `issuetype in (...)` clause.

### 2. `ticket-reader` agent — Full description output

Change from `jira.py get` to `jira.py details` so the agent returns:
- Full untruncated description (not 500-char truncated)
- Linked issues with relationship types
- Subtasks with status

This benefits both `be-warm-up` (needs full description for actionability assessment) and `/jira-details` command (richer subagent data).

### 3. New `task-assessor` agent

The core new component. Each instance receives a ticket key and performs deep analysis.

**Frontmatter:**
```yaml
name: task-assessor
description: Deep-analyze a Jira task against its codebase on origin/staging to assess if it's actionable or needs clarification
tools: ["Bash"]
```

**Flow:**

1. **Fetch ticket** — runs `jira.py details <KEY>` for full description
2. **Parse repo name** — extracts `<repo-name>` from title pattern `[BE][<repo-name>] ...`
3. **Validate repo** — checks if `$PLAXIE_PROJECT_ROOT/<repo-name>` exists
   - If not found: return early with flag asking user for correct path
4. **Inspect codebase** — read-only operations on `origin/staging`:
   - `git fetch origin` (once per repo)
   - `git ls-tree --name-only -r origin/staging <path>` to browse structure
   - `git show origin/staging:<file>` to read relevant source files
   - `git log origin/staging --oneline -20` for recent activity
5. **Deep analysis** — map ticket requirements to actual code locations, understand the architecture around the change area, identify insertion points
6. **Return structured verdict:**
   - **Actionable**: confirmed code locations, brief implementation direction
   - **Unclear**: FACT/ASSUME breakdown + specific questions for reporter
   - **Flagged**: repo not found or other blocker

**Tools rationale:** `Bash` only. All codebase inspection goes through git commands targeting `origin/staging` (read-only, no working tree changes). `Read`/`Grep`/`Glob` operate on the working tree and would not see staging branch content.

**Environment:** Requires `PLAXIE_PROJECT_ROOT` env var. Validated at agent start; clear error if missing.

### 4. `be-warm-up` command — Reworked as orchestrator

**Updated flow:**

1. Fetch backlog: `jira.py backlog CR --sp 10 --prefix "[BE]" --type "Task,Bug"`
2. Parse ticket keys from output
3. Spawn one `task-assessor` agent per task (all in parallel via Agent tool)
4. Aggregate results into structured report

**Output format:**

```markdown
## BE Warm-Up Report

### Actionable Tasks
✓ CR-456: [BE][creative-studio] Add export endpoint
  Code area: src/api/export.py, src/services/export_service.py
  Ready to implement.

✓ CR-457: [BE][media-center] Add retry logic to upload
  Code area: src/upload/handler.py
  Ready to implement.

### Tasks Needing Clarification
✗ CR-789: [BE][media-center] Optimize query performance
<FACT>
- Title says "optimize query performance" but no specific table/endpoint named
- media-center staging has 12 query files across 3 services
</FACT>
<ASSUME>
- Likely related to the media listing endpoint based on recent staging commits
</ASSUME>
Questions for reporter:
- [ ] Which queries specifically need optimization?
- [ ] What's the current latency vs target?

### Flagged
⚠ CR-800: [BE][unknown-repo] Fix auth flow
  Repo "unknown-repo" not found under $PLAXIE_PROJECT_ROOT
  → Provide correct repo path to continue

**Summary:**
- Total: 4 tasks | 12 SP
- Actionable: 2 | Needs clarification: 1 | Flagged: 1
```

**Frontmatter:**
```yaml
description: "Pull [BE] backlog tasks, inspect codebases on staging, assess actionability with FACT/ASSUME analysis"
allowed-tools: ["Bash", "Read", "Agent"]
```

### 5. Environment variable

New required env var for codebase inspection:

```bash
export PLAXIE_PROJECT_ROOT=/Users/yourname/Projects/appier/plaxie
```

Validated only in the `task-assessor` agent (not in `jira.py` — the script doesn't need it).

### 6. README update

Add `PLAXIE_PROJECT_ROOT` to the env vars section and update the components table to reflect the enhanced `be-warm-up` capabilities and new `/jira-details` command.

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `cs-jira-query/scripts/jira.py` | Modify | Add `--type` flag to `cmd_backlog` |
| `cs-jira-query/agents/ticket-reader/AGENT.md` | Modify | Change from `jira.py get` to `jira.py details` |
| `cs-jira-query/agents/task-assessor/AGENT.md` | Create | Deep codebase analysis agent |
| `cs-jira-query/commands/be-warm-up.md` | Modify | Rework as orchestrator with task-assessor agents |
| `README.md` | Modify | Add `PLAXIE_PROJECT_ROOT` env var and updated feature list |
| `cs-jira-query/.claude-plugin/plugin.json` | Modify | Bump version 1.1.0 → 1.2.0 |
| `.claude-plugin/marketplace.json` | Modify | Bump cs-jira-query version 1.1.0 → 1.2.0 |

## Non-Goals

- No changes to `fe-warm-up` (separate command, may get similar treatment later)
- No changes to `/jira-details` command behavior (but benefits from `ticket-reader` improvement)
- No changes to `jira-query` skill auto-trigger behavior
- No actual branch switching or working tree modifications in inspected repos
