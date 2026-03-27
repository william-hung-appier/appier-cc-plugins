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
