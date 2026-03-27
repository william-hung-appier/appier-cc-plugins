# Appier Claude Code Plugins

A Claude Code plugin marketplace for Appier developer tools.

## Installation

```bash
claude plugins marketplace add william-hung-appier/appier-cc-plugins
```

## Available Plugins

### cs-jira-query

Query Jira tickets and backlog warm-up commands for BE/FE spec clarification.

**Install:**

```bash
claude plugins install cs-jira-query@appier-cc-plugins
```

**Required env vars** (set in your shell profile):

```bash
export JIRA_BASE_URL=https://yourcompany.atlassian.net
export JIRA_EMAIL=you@company.com
export JIRA_API_TOKEN=<from https://id.atlassian.com/manage-profile/security/api-tokens>
```

**Optional:**

```bash
export JIRA_STORY_POINTS_FIELD=customfield_10005  # default
export PLAXIE_PROJECT_ROOT=/path/to/your/plaxie    # required for /be-warm-up codebase inspection
```

**What it provides:**

| Component | Description |
|---|---|
| **Skill: jira-query** | Auto-triggers on ticket key mentions (e.g. "what's CR-123") |
| **Command: /cs-jira-query:be-warm-up** | Pull [BE] Tasks+Bugs, inspect codebases on staging, assess actionability |
| **Command: /cs-jira-query:fe-warm-up** | Pull [FE] backlog tasks with FACT/ASSUME analysis |
| **Command: /cs-jira-query:jira-details** | Deep-dive a ticket with linked issues, subtasks, FACT/ASSUME analysis |

**CLI usage** (also works standalone):

```bash
python3 scripts/jira.py get CR-123
python3 scripts/jira.py get CR-123 --comments
python3 scripts/jira.py details CR-123
python3 scripts/jira.py search "assignee = currentUser() AND status != Done"
python3 scripts/jira.py backlog CR --sp 10 --prefix "[BE]"
python3 scripts/jira.py backlog CR --sp 10 --prefix "[BE]" --type "Task,Bug"
```
