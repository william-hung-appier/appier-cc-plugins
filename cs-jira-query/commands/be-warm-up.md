---
description: "Pull [BE] backlog tasks up to 10 story points with FACT/ASSUME spec clarification insights"
allowed-tools: ["Bash", "Read"]
---

# BE Warm-Up

Pull backend backlog tasks and help the user understand what needs clarification before starting work.

## Steps

1. Run via Bash:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py backlog CR --sp 10 --prefix "[BE]"
   ```

2. For each task returned, get its full details (with description):
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py get <KEY>
   ```

3. Present a warm-up report using this format for each task:

---

### <KEY>: <Title> (SP: N)

**Assignee:** <name or Unassigned>

<FACT>
- State what the ticket title and description explicitly say
- What is concretely defined: endpoints, components, services named
- Any acceptance criteria or constraints mentioned
</FACT>

<ASSUME>
- What the task likely involves based on the title/description context
- Potential dependencies or blockers not explicitly stated
- Scope boundaries that seem implied but aren't confirmed
</ASSUME>

<SUGGEST>
Questions to clarify before starting:
- [ ] <specific question about ambiguous scope>
- [ ] <question about dependencies or integration points>
- [ ] <question about acceptance criteria if missing>
</SUGGEST>

---

4. End with a summary:

**Warm-Up Summary:**
- Total tasks: N | Total SP: X
- Tasks with clear scope: list keys
- Tasks needing clarification: list keys with one-line reason each

## Rules

- Keep each task analysis concise — 3-5 bullet points per section max
- Focus FACT on what the ticket *actually says*, not what you infer
- Focus ASSUME on what a backend engineer would need to know
- SUGGEST should be actionable questions the user can take to a PM or tech lead
- If a task has no description, flag it prominently — that's a red flag for scope clarity
