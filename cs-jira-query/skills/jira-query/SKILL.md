---
name: jira-query
description: Query Jira tickets via CLI script. Use whenever the user mentions a Jira ticket key (CR-123, BE-456, PROJ-789), asks to find tasks in backlog, search by prefix/project, check assignees, or get ticket details. Also trigger for story point queries, sprint lookups, or any "get me Jira tickets" request. Even casual mentions like "what's CR-123" or "pull up the BE backlog" should trigger this.
---

# Jira Query

Run via Bash: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py <command>`

## Commands

| User wants | Command |
|---|---|
| Single ticket | `jira.py get CR-123` |
| Ticket with comments | `jira.py get CR-123 --comments` |
| Full details + links + subtasks | `jira.py details CR-123` |
| JQL search | `jira.py search "assignee = currentUser() AND status != Done"` |
| Backlog up to N story points | `jira.py backlog CR --sp 10` |
| Backlog filtered by title prefix | `jira.py backlog CR --sp 10 --prefix "[BE]"` |

## Rules

- **Never include `--comments` unless the user explicitly asks for comments.**
- When the user says tickets "starting with [BE]" or "with prefix [BE]", use `--prefix "[BE]"` to filter by title.
- For complex filters, use `search` with JQL.
- If env vars are missing, the script tells the user what to set — just run it and relay the message.

## Requires

Env vars: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
