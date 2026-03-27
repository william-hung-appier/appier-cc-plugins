# Design: `/jira-details <KEY>` Command

**Date:** 2026-03-27
**Plugin:** cs-jira-query
**Status:** Draft

## Summary

Add a `/jira-details <KEY>` command to the `cs-jira-query` plugin that provides a deep-dive view of a single Jira ticket — full untruncated description, linked issues, and subtasks — with FACT/ASSUME analysis. Uses parallel subagents (one per related ticket) to keep each ticket's context isolated and enable concurrent fetching.

## Motivation

The existing `jira-query` skill auto-triggers on ticket mentions and returns a compact view (500-char truncated description, no linked issues, no subtasks). Users need a deliberate, richer command for understanding a ticket's full context before starting work.

## Components

### 1. `jira.py details` subcommand (new)

**Purpose:** Fetch a single ticket with full description, linked issues list, and subtasks list in one API call.

**Usage:**
```bash
jira.py details <KEY>
```

**API fields requested:**
- `summary`, `assignee`, `status`, `{STORY_POINTS_FIELD}` (existing)
- `description` — full, no truncation (unlike `get` which caps at 500 chars)
- `issuelinks` — linked issues with relationship type (inward/outward)
- `subtasks` — child issues

**Output format:**
```
Key: CR-123
Title: Implement user auth flow
Status: In Progress
Assignee: Jane Doe
Story Points: 5

Description:
<full untruncated description, ADF extracted to plain text>

Linked Issues:
- blocks CR-124: Payment gateway integration
- is blocked by CR-100: Database migration
- relates to CR-130: Session management

Subtasks:
- CR-123-1: Add login endpoint
- CR-123-2: Add token refresh logic
- CR-123-3: Add logout endpoint
```

**Implementation notes:**
- Reuses existing `api_get`, `extract_text`, `get_config` functions
- New `cmd_details` function added to `COMMANDS` dict
- Description uses `extract_text` but without the `DESC_MAX_CHARS` truncation
- Linked issues extracted from `issuelinks` field — each has `inwardIssue` or `outwardIssue` with a `type` containing `inward`/`outward` relationship names
- Subtasks extracted from `subtasks` field — each has `key`, `fields.summary`, `fields.status.name`

### 2. `agents/ticket-reader/AGENT.md` (new)

**Purpose:** Lightweight subagent that fetches a single ticket and returns a compact summary. One ticket per agent instance — clean context isolation.

**Frontmatter:**
```yaml
name: ticket-reader
description: Fetch a single Jira ticket and return a compact summary with key, title, status, assignee, and short description
tools: ["Bash"]
```

**Behavior:**
1. Receives a ticket key as input
2. Runs `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py get <KEY>`
3. Returns the output as-is (key, title, status, assignee, SP, description truncated to 500 chars)

**Design rationale:** Each subagent has its own context window, preventing cross-contamination between tickets. The orchestrator can spawn multiple agents in parallel for concurrent fetching.

### 3. `commands/jira-details.md` (new command)

**Purpose:** Orchestrator command that assembles the full picture and produces FACT/ASSUME analysis.

**Frontmatter:**
```yaml
description: "Deep-dive into a Jira ticket — full description, linked issues, subtasks with FACT/ASSUME analysis"
allowed-tools: ["Bash", "Read", "Agent"]
```

**Orchestration steps:**

1. **Fetch target ticket:**
   Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py details <KEY>` to get the target ticket with full description + linked issue keys + subtask keys.

2. **Spawn subagents in parallel:**
   For each linked issue key and subtask key found in step 1, spawn a `ticket-reader` agent. All agents run concurrently.

3. **Aggregate and analyze:**
   Combine the target ticket data with all subagent results. Produce the structured output below.

**Output format:**

```markdown
## <KEY>: <Title>

**Status:** X | **Assignee:** Y | **SP:** N

### Description
<full untruncated description>

### Linked Issues
For each linked issue (data from subagent):
- **<LINK-KEY>: <Title>** | <Status> | <Assignee> | Relationship: <blocks/blocked-by/relates-to>

### Subtasks
For each subtask (data from subagent):
- **<SUB-KEY>: <Title>** | <Status> | <Assignee>

<FACT>
- What the ticket description explicitly states (scope, requirements, constraints)
- Concrete relationships: what it blocks, what blocks it, what it relates to
- Subtask breakdown: N total, N done, N in progress, N todo
- Any acceptance criteria or technical constraints mentioned
</FACT>

<ASSUME>
- Inferred scope or risk based on the relationship graph
- Potential blockers: linked issues in non-done states that block this ticket
- Gaps between subtask coverage and the scope described in the description
- Dependencies that may not be explicitly linked but are implied
</ASSUME>
```

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `cs-jira-query/scripts/jira.py` | Modify | Add `cmd_details` function and register in `COMMANDS` |
| `cs-jira-query/agents/ticket-reader/AGENT.md` | Create | Lightweight subagent for single ticket fetch |
| `cs-jira-query/commands/jira-details.md` | Create | Orchestrator command with FACT/ASSUME output |
| `cs-jira-query/.claude-plugin/plugin.json` | Modify | Bump version to 1.1.0 |
| `.claude-plugin/marketplace.json` | Modify | Bump cs-jira-query version to 1.1.0 |

## Non-Goals

- No changes to the existing `jira-query` skill or `get` subcommand behavior
- No changes to `be-warm-up` or `fe-warm-up` commands
- No comment fetching in `/jira-details` (users can still use the skill with `--comments` for that)
