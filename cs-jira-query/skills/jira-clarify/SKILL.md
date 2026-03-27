---
name: jira-clarify
description: Format clarification questions for a Jira ticket reporter. Use this skill whenever the user wants to ask about a ticket, clarify a ticket, send questions about a ticket, or says things like "ask about CR-123", "clarify CR-456", "what should I ask for CR-789", "questions for CR-123". Also trigger after a be-warm-up report when the user references a ticket that needs clarification. Even casual mentions like "CR-123 is unclear, help me ask" should trigger this.
---

# Jira Clarify

Format clarification questions for a Jira ticket into a clean, copy-pasteable message for the reporter (via Jira comment or Slack).

## Steps

1. Extract the ticket key from the user's input (e.g., CR-789).

2. Check if there is already a warm-up report or task assessment in the current conversation that contains FACT/ASSUME analysis and questions for this ticket. If so, use those questions directly — do not re-fetch.

3. If no prior analysis exists, fetch the ticket details:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py details <KEY>
   ```
   Then analyze the ticket and generate clarification questions using FACT/ASSUME:
   - What the description says vs. what's missing
   - Ambiguous scope, undefined requirements, missing acceptance criteria
   - Dependencies or integration points that aren't specified

4. Present the formatted output in two formats:

### Jira Comment Format

```
--- Copy for Jira ---
Hi,

I'm picking up <KEY> and have a few questions before starting:

<FACT>
Based on the ticket, I understand:
- [what the ticket clearly states]
- [concrete requirements mentioned]
</FACT>

<ASSUME>
I'm assuming:
- [inference about scope]
- [inference about approach]
</ASSUME>

Could you clarify:
1. [specific question]
2. [specific question]
3. [specific question]

Thanks!
--- End ---
```

### Slack Format

```
--- Copy for Slack ---
Hey, picking up `<KEY>: <Title>` — a few questions:
• [question 1]
• [question 2]
• [question 3]
--- End ---
```

## Rules

- Reuse existing analysis from the conversation when available — do not re-fetch if questions already exist
- FACT must contain only what the ticket explicitly states
- ASSUME must contain only inferences, clearly marked as assumptions
- Questions must be specific and actionable — not vague ("can you clarify the scope?") but pointed ("should the export endpoint return CSV or JSON?")
- Keep the Slack format short — 3-5 bullet points max, no FACT/ASSUME blocks
- Keep the Jira format structured — include FACT/ASSUME so the reporter understands your reasoning
- Always present both formats so the user can pick which to use
