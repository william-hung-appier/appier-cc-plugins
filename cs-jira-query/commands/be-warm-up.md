---
description: "Pull [BE] backlog Tasks+Bugs, inspect codebases on staging, assess actionability with FACT/ASSUME analysis"
allowed-tools: ["Bash", "Read", "Agent"]
---

# BE Warm-Up

Pull backend backlog tasks (Tasks and Bugs only), inspect each task's codebase on staging, and assess whether each task is actionable or needs clarification.

## Steps

1. Fetch backlog tasks via Bash:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py backlog CR --sp 10 --prefix "[BE]" --type "Task,Bug"
   ```

2. Parse the output to extract all ticket keys (e.g., CR-456, CR-789).

3. For each ticket key, spawn a `task-assessor` agent in parallel. Each agent independently:
   - Fetches full ticket details
   - Parses the repo name from the title
   - Inspects the codebase on `origin/staging`
   - Returns an actionable/unclear/flagged verdict

   Use the Agent tool with one call per ticket, all in a single message for parallel execution.

4. Once all agents return, aggregate results into this report format:

---

## BE Warm-Up Report

### Actionable Tasks
For each task where the assessor returned actionable:
```
✓ <KEY>: <Title> (SP: N)
  Code area: <files/modules from assessor>
  Ready to implement.
```

### Tasks Needing Clarification
For each task where the assessor returned needs clarification:
```
✗ <KEY>: <Title> (SP: N)
<FACT>
<from assessor output>
</FACT>
<ASSUME>
<from assessor output>
</ASSUME>
Questions for reporter:
<from assessor output>
```

### Flagged
For each task where the assessor returned flagged:
```
⚠ <KEY>: <Title> (SP: N)
  <reason from assessor>
  → <action needed>
```

**Summary:**
- Total: N tasks | X SP
- Actionable: N | Needs clarification: N | Flagged: N

---

## Rules

- Always fetch the backlog first before spawning agents
- Spawn all task-assessor agents in parallel (one Agent tool call per ticket, all in the same message)
- If the backlog returns zero tasks, report that clearly and stop
- Preserve the assessor's FACT/ASSUME output exactly — do not rewrite or summarize it
- Include story points in each task's header line
- Group results by verdict type (actionable, unclear, flagged) for easy scanning
