---
name: okr-constructor
description: Build OKRs (Objectives and Key Results) from Jira tasks with SMART-principle quality scoring. Use when the user asks to construct OKRs, generate objectives from their tasks, review quarterly work, evaluate task quality, build a quarterly summary, or wants to turn Jira tickets into structured OKRs. Trigger on "build OKRs", "construct OKRs from my tasks", "generate objectives", "quarterly OKR review", "evaluate my Q1/Q2 tasks", "SMART evaluation", "turn my tasks into OKRs", "what did I accomplish this quarter", or any request combining Jira task querying with OKR construction, goal-setting, or SMART-based quality assessment. Even casual phrasing like "help me write OKRs from my tickets" or "score and organize my Q1 work" should trigger this skill.
---

# OKR Constructor

Build well-formed OKRs from Jira tasks by first SMART-scoring each task, then grouping by theme and synthesizing Objectives with measurable Key Results. This gives the user both a quality assessment of their tasks and a structured OKR output they can use for planning, reporting, or retrospectives.

## Workflow

### 1. Parse and confirm time range

Extract the date range from the user's request and convert to concrete dates:

| User says | Start | End |
|-----------|-------|-----|
| "Q1 2026" or "2026 Q1" | 2026-01-01 | 2026-03-31 |
| "Q2 2026" | 2026-04-01 | 2026-06-30 |
| "Q3 2026" | 2026-07-01 | 2026-09-30 |
| "Q4 2026" | 2026-10-01 | 2026-12-31 |
| "H1 2026" | 2026-01-01 | 2026-06-30 |
| "H2 2026" | 2026-07-01 | 2026-12-31 |
| "March 2026" | 2026-03-01 | 2026-03-31 |
| "last month" | first of previous month | last of previous month |
| "this month" | first of current month | today |
| "last quarter" | first of previous quarter | last of previous quarter |

**Always confirm before querying:**

> I'll query CR tasks assigned to you between **{start_date}** and **{end_date}**. Sound right?

If the user corrects the dates, use their corrected values.

### 2. Query Jira

Once the user confirms:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py search "project = CR AND assignee = currentUser() AND updated >= \"{start_date}\" AND updated <= \"{end_date}\" ORDER BY updated DESC" --max 30
```

If the query returns zero tasks, report that clearly and stop.

### 3. SMART-evaluate each task in parallel

For each ticket key from the search results, spawn an `okr-task-evaluator` agent using the Agent tool. Each agent independently:

- Fetches full ticket details via `jira.py details`
- Parses repo name from the title and inspects git logs for related commits (best-effort)
- Scores the task on all five SMART dimensions (0-2 scale each, max 10)
- Identifies the task's theme/domain (from repo name, epic links, or description keywords)
- Returns a structured evaluation with FACT/ASSUME tags

Spawn all agents in a single message for parallel execution.

### 4. Compile SMART Report

Once all agents return, build the SMART summary table and per-task breakdowns (see Report Format below).

### 5. Construct OKRs

Group the evaluated tasks by theme (the agent returns a `Theme:` field). For each theme group:

**Formulate an Objective** — a qualitative, inspiring goal that captures the intent behind the tasks in this group. Good objectives are:
- Aspirational but grounded in what the tasks actually accomplished or aimed for
- Written as outcomes, not activities ("Improve export reliability" not "Work on export bugs")
- Concise — one sentence

**Derive Key Results** — 2-4 measurable outcomes extracted from the tasks in the group. Each KR should:
- Be quantifiable where possible (use story points completed, subtask counts, or task completion rates)
- Map to specific tickets so the user can trace back
- Have a clear target and current state

**Rate the OKR quality** — use the average SMART score of the constituent tasks as a quality signal. If average SMART < 5, flag the OKR as needing stronger task definitions.

---

## Report Format

### Part 1: SMART Evaluation

#### Summary Table

```
| Ticket | Title | SP | S | M | A | R | T | Score | Theme |
|--------|-------|----|---|---|---|---|---|-------|-------|
```

Symbols: `●` Strong (2) | `◐` Partial (1) | `○` Weak (0)

#### Per-Task Breakdown

Include each agent's full output (FACT, ASSUME, scoring table, SUGGEST) verbatim.

#### SMART Health Summary

```
- Average score: X.X / 10
- Strongest dimension: <which> — <pattern>
- Weakest dimension: <which> — <pattern>
- Total tasks: N | Total SP: N
```

### Part 2: Constructed OKRs

For each theme group:

```
## Objective: <Aspirational one-sentence goal>

Theme: <theme name> | Tasks: N | Total SP: N | Avg SMART: X.X/10

### Key Results

1. **KR1**: <Measurable outcome> — <target>
   Evidence: <ticket keys that support this KR>

2. **KR2**: <Measurable outcome> — <target>
   Evidence: <ticket keys>

3. **KR3**: <Measurable outcome> — <target>
   Evidence: <ticket keys>

### OKR Quality Assessment

<FACT>
- N tasks in this group, average SMART score X.X/10
- <key observations about the task quality feeding this OKR>
</FACT>

<ASSUME>
- <interpretation of how well this OKR represents the actual work>
- <whether the KRs are truly measurable given the task definitions>
</ASSUME>
```

### Part 3: Recommendations

```
## Recommendations

### For Task Quality
1. <Most impactful improvement based on SMART weakness patterns>
2. <Second recommendation>

### For OKR Strength
1. <How to make the constructed OKRs more robust — e.g., missing themes, unmeasurable KRs>
2. <Suggestions for next quarter's task definition to produce stronger OKRs>
```

## Rules

- Always confirm date range with the user before querying
- Spawn all okr-task-evaluator agents in parallel (one per ticket, all in the same message)
- If search returns zero tasks, report that and stop
- Preserve each agent's FACT/ASSUME output verbatim — do not rewrite
- Use the scoring legend consistently (● ◐ ○)
- OKR Objectives must be outcome-oriented, not activity descriptions
- Key Results must reference specific ticket keys as evidence
- Recommendations should be specific and actionable, referencing actual patterns observed

## Requires

Env vars: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
Optional: `PLAXIE_PROJECT_ROOT` (enables git log inspection for richer Achievable scoring)
