# `/jira-details` Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/jira-details <KEY>` command that deep-dives a Jira ticket — full description, linked issues, subtasks — with parallel subagents and FACT/ASSUME analysis.

**Architecture:** Extend `jira.py` with a `details` subcommand that fetches full ticket data including `issuelinks` and `subtasks` fields. A `ticket-reader` agent fetches individual related tickets in parallel. The `jira-details.md` command orchestrates: fetch target via `details`, spawn one subagent per related ticket, aggregate results into FACT/ASSUME output.

**Tech Stack:** Python 3 (stdlib only), Claude Code plugin system (AGENT.md, command .md with YAML frontmatter)

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `cs-jira-query/scripts/jira.py` | Modify | Add `cmd_details` + `format_details` — fetches ticket with full desc, issuelinks, subtasks |
| `cs-jira-query/agents/ticket-reader/AGENT.md` | Create | Lightweight subagent: given a ticket key, calls `jira.py get`, returns output |
| `cs-jira-query/commands/jira-details.md` | Create | Orchestrator command: calls `details`, spawns subagents, assembles FACT/ASSUME report |
| `cs-jira-query/.claude-plugin/plugin.json` | Modify | Bump version 1.0.0 → 1.1.0 |
| `.claude-plugin/marketplace.json` | Modify | Bump cs-jira-query version 1.0.0 → 1.1.0 |

---

### Task 1: Add `cmd_details` to `jira.py`

**Files:**
- Modify: `cs-jira-query/scripts/jira.py:219-256` (HELP string, COMMANDS dict, main block)

- [ ] **Step 1: Add `format_details` function**

Insert after the `format_search` function (after line 133) in `cs-jira-query/scripts/jira.py`:

```python
def format_details(fields, key):
    """Format a ticket with full description, linked issues, and subtasks."""
    print(f"Key: {key}")
    print(f"Title: {fields.get('summary', '')}")
    print(f"Status: {fields.get('status', {}).get('name', 'Unknown')}")

    assignee = fields.get("assignee")
    print(f"Assignee: {assignee['displayName'] if assignee else 'Unassigned'}")

    sp = fields.get(STORY_POINTS_FIELD)
    if sp is not None:
        print(f"Story Points: {sp}")

    desc_raw = fields.get("description")
    if desc_raw:
        desc = extract_text(desc_raw) if isinstance(desc_raw, dict) else str(desc_raw)
    else:
        desc = "No description"
    print(f"\nDescription:\n{desc}")

    links = fields.get("issuelinks", [])
    if links:
        print("\nLinked Issues:")
        for link in links:
            link_type = link.get("type", {})
            if "outwardIssue" in link:
                issue = link["outwardIssue"]
                rel = link_type.get("outward", "relates to")
            elif "inwardIssue" in link:
                issue = link["inwardIssue"]
                rel = link_type.get("inward", "relates to")
            else:
                continue
            issue_key = issue.get("key", "?")
            issue_summary = issue.get("fields", {}).get("summary", "")
            print(f"- {rel} {issue_key}: {issue_summary}")
    else:
        print("\nLinked Issues: None")

    subtasks = fields.get("subtasks", [])
    if subtasks:
        print("\nSubtasks:")
        for st in subtasks:
            st_key = st.get("key", "?")
            st_summary = st.get("fields", {}).get("summary", "")
            st_status = st.get("fields", {}).get("status", {}).get("name", "?")
            print(f"- {st_key}: {st_summary} | {st_status}")
    else:
        print("\nSubtasks: None")
```

- [ ] **Step 2: Add `cmd_details` function**

Insert after `cmd_backlog` (after line 216) in `cs-jira-query/scripts/jira.py`:

```python
def cmd_details(cfg, args):
    if not args:
        print("Usage: jira.py details <KEY>")
        sys.exit(1)

    key = args[0]
    req_fields = f"{BASE_FIELDS},description,issuelinks,subtasks"
    data = api_get(cfg, f"/rest/api/3/issue/{key}", {"fields": req_fields})
    format_details(data["fields"], data["key"])
```

- [ ] **Step 3: Update HELP string and COMMANDS dict**

Update the `HELP` string to include the `details` command. Replace the existing `HELP` and `COMMANDS`:

```python
HELP = """\
Jira Query — token-efficient CLI (API v3)

Commands:
  jira.py get <KEY>                    Single ticket details
  jira.py get <KEY> --comments         Include last 5 comments
  jira.py details <KEY>               Full details with linked issues & subtasks
  jira.py search "<JQL>" [--max N]     JQL search (default 20 results)
  jira.py backlog <PROJECT> [--sp N] [--prefix "[BE]"]
                                       Backlog tasks up to N SP, filtered by title prefix

Examples:
  jira.py get CR-123
  jira.py get CR-123 --comments
  jira.py details CR-123
  jira.py search "assignee = currentUser() AND status != Done"
  jira.py backlog BE --sp 15
  jira.py backlog CR --sp 10 --prefix "[BE]"

Env vars required: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN"""

COMMANDS = {
    "get": cmd_get,
    "search": cmd_search,
    "backlog": cmd_backlog,
    "details": cmd_details,
}
```

- [ ] **Step 4: Update the module docstring**

Replace the docstring at the top of the file (lines 2-8):

```python
"""Jira Query — token-efficient CLI for agents (API v3)

Usage:
  jira.py get <KEY>                                    # single ticket
  jira.py get <KEY> --comments                         # with last 5 comments
  jira.py details <KEY>                                # full details + links + subtasks
  jira.py search "<JQL>" [--max N]                     # JQL search (default 20)
  jira.py backlog <PROJECT> [--sp N] [--prefix "[BE]"] # backlog up to N story points
"""
```

- [ ] **Step 5: Manually test the script**

Run with `--help` to verify the new command appears:

```bash
python3 cs-jira-query/scripts/jira.py --help
```

Expected: Output includes `jira.py details <KEY>` line.

Run with no args to verify `details` usage:

```bash
python3 cs-jira-query/scripts/jira.py details
```

Expected: `Usage: jira.py details <KEY>` then exit code 1.

- [ ] **Step 6: Commit**

```bash
git add cs-jira-query/scripts/jira.py
git commit -m "feat: add details subcommand to jira.py

Fetches ticket with full untruncated description, linked issues
with relationship types, and subtasks."
```

---

### Task 2: Create `ticket-reader` agent

**Files:**
- Create: `cs-jira-query/agents/ticket-reader/AGENT.md`

- [ ] **Step 1: Create the agent directory**

```bash
mkdir -p cs-jira-query/agents/ticket-reader
```

- [ ] **Step 2: Write AGENT.md**

Create `cs-jira-query/agents/ticket-reader/AGENT.md`:

```markdown
---
name: ticket-reader
description: Fetch a single Jira ticket and return a compact summary with key, title, status, assignee, and short description
tools: ["Bash"]
---

# Ticket Reader

You are a lightweight agent that fetches a single Jira ticket.

## Instructions

1. You will receive a Jira ticket key (e.g., CR-123).
2. Run this command:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py get <KEY>
   ```
3. Return the full output exactly as printed by the script. Do not summarize, reformat, or add commentary.
```

- [ ] **Step 3: Commit**

```bash
git add cs-jira-query/agents/ticket-reader/AGENT.md
git commit -m "feat: add ticket-reader subagent

Lightweight agent that fetches a single Jira ticket via jira.py get
and returns the output for the orchestrator to aggregate."
```

---

### Task 3: Create `jira-details` command

**Files:**
- Create: `cs-jira-query/commands/jira-details.md`

- [ ] **Step 1: Write the command file**

Create `cs-jira-query/commands/jira-details.md`:

```markdown
---
description: "Deep-dive into a Jira ticket — full description, linked issues, subtasks with FACT/ASSUME analysis"
allowed-tools: ["Bash", "Read", "Agent"]
---

# Jira Details

Deep-dive into a single Jira ticket with full context and analysis.

## Steps

1. Extract the ticket key from the user's input (e.g., `CR-123` from `/jira-details CR-123`).

2. Fetch the target ticket with full details:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py details <KEY>
   ```

3. Parse the output to identify all linked issue keys and subtask keys.

4. For each linked issue key and subtask key, spawn a `ticket-reader` agent in parallel. Each agent fetches one ticket independently. Use the Agent tool with one call per ticket, all in a single message for parallel execution.

5. Once all agents return, aggregate the target ticket data and all related ticket summaries. Present the report using this format:

---

## <KEY>: <Title>

**Status:** X | **Assignee:** Y | **SP:** N

### Description
<full untruncated description from the details output>

### Linked Issues
For each linked issue (using data returned by its subagent):
- **<LINK-KEY>: <Title>** | <Status> | <Assignee> | Relationship: <relationship type from details output>

### Subtasks
For each subtask (using data returned by its subagent):
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

---

## Rules

- Always fetch the target ticket first before spawning subagents
- Spawn all subagents in parallel (one Agent tool call per ticket, all in the same message)
- If there are no linked issues and no subtasks, skip the subagent step and just present the target ticket with FACT/ASSUME analysis
- FACT must only contain what is directly observable from the ticket data — no interpretation
- ASSUME should focus on actionable insights: blockers, risks, scope gaps
- Do not include comments — this command is for structural context, not discussion history
```

- [ ] **Step 2: Commit**

```bash
git add cs-jira-query/commands/jira-details.md
git commit -m "feat: add /jira-details command

Orchestrator command that fetches full ticket details, spawns
parallel subagents for linked issues and subtasks, then assembles
a FACT/ASSUME analysis report."
```

---

### Task 4: Bump version and update manifests

**Files:**
- Modify: `cs-jira-query/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Update plugin.json version**

In `cs-jira-query/.claude-plugin/plugin.json`, change version from `"1.0.0"` to `"1.1.0"`:

```json
{
  "name": "cs-jira-query",
  "description": "Query Jira tickets and warm-up commands for BE/FE backlog spec clarification",
  "version": "1.1.0",
  "author": {
    "name": "William Hung"
  }
}
```

- [ ] **Step 2: Update marketplace.json version**

In `.claude-plugin/marketplace.json`, change the cs-jira-query version from `"1.0.0"` to `"1.1.0"`:

```json
{
  "name": "appier-cc-plugins",
  "description": "Appier Claude Code plugins — Jira integration and developer productivity tools",
  "owner": {
    "name": "William Hung"
  },
  "plugins": [
    {
      "name": "cs-jira-query",
      "description": "Query Jira tickets and warm-up commands for BE/FE backlog spec clarification",
      "version": "1.1.0",
      "source": "./cs-jira-query",
      "category": "productivity"
    }
  ]
}
```

- [ ] **Step 3: Commit**

```bash
git add cs-jira-query/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore: bump cs-jira-query version to 1.1.0

Adds /jira-details command with ticket-reader subagent."
```

---

### Task 5: Update jira-query skill to mention `details` command

**Files:**
- Modify: `cs-jira-query/skills/jira-query/SKILL.md`

- [ ] **Step 1: Add `details` to the skill's command table**

In `cs-jira-query/skills/jira-query/SKILL.md`, add a row to the Commands table:

```markdown
| User wants | Command |
|---|---|
| Single ticket | `jira.py get CR-123` |
| Ticket with comments | `jira.py get CR-123 --comments` |
| Full details + links + subtasks | `jira.py details CR-123` |
| JQL search | `jira.py search "assignee = currentUser() AND status != Done"` |
| Backlog up to N story points | `jira.py backlog CR --sp 10` |
| Backlog filtered by title prefix | `jira.py backlog CR --sp 10 --prefix "[BE]"` |
```

- [ ] **Step 2: Commit**

```bash
git add cs-jira-query/skills/jira-query/SKILL.md
git commit -m "docs: add details command to jira-query skill reference"
```

---

### Task 6: End-to-end validation

- [ ] **Step 1: Verify script help**

```bash
python3 cs-jira-query/scripts/jira.py --help
```

Expected: `details` command listed in help output.

- [ ] **Step 2: Verify script error handling**

```bash
python3 cs-jira-query/scripts/jira.py details
```

Expected: `Usage: jira.py details <KEY>` then exit code 1.

- [ ] **Step 3: Verify plugin file structure**

```bash
tree cs-jira-query/
```

Expected structure:
```
cs-jira-query/
├── .claude-plugin/
│   └── plugin.json          (version 1.1.0)
├── agents/
│   └── ticket-reader/
│       └── AGENT.md
├── commands/
│   ├── be-warm-up.md
│   ├── fe-warm-up.md
│   └── jira-details.md
├── scripts/
│   └── jira.py
└── skills/
    └── jira-query/
        └── SKILL.md
```

- [ ] **Step 4: Verify all files are committed**

```bash
git status
```

Expected: clean working tree.

- [ ] **Step 5: Install locally and test**

```bash
claude plugins marketplace update local && claude plugins update cs-jira-query@local
```

Then test the command:
```
/cs-jira-query:jira-details CR-123
```

Expected: Full ticket details with linked issues, subtasks, and FACT/ASSUME analysis.
