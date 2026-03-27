---
description: "Start working on an actionable Jira task — create feature branch from staging, generate implementation plan"
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
---

# Task Kickoff

Start working on an actionable Jira task by setting up the workspace and generating an implementation plan.

## Steps

1. Extract the ticket key from the user's input (e.g., CR-456 from `/task-kickoff CR-456`).

2. Fetch full ticket details:
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/jira.py details <KEY>
   ```

3. Parse the repo name from the title pattern `[BE][<repo-name>] ...`. If the pattern doesn't match, ask the user which repo this ticket belongs to.

4. Validate the repo exists at `$PLAXIE_PROJECT_ROOT/<repo-name>`. If `PLAXIE_PROJECT_ROOT` is not set or the repo doesn't exist, ask the user for the correct path.

5. Set up the workspace in the repo directory:
   ```bash
   cd "${PLAXIE_PROJECT_ROOT}/<repo-name>"
   git fetch origin
   ```

6. Create a feature branch from `origin/staging`:
   ```bash
   git checkout -b feat/<KEY-lowercase>-<short-description> origin/staging
   ```
   Use the ticket key and a slugified version of the title (e.g., `feat/cr-456-add-export-endpoint`).

7. Explore the codebase to understand the relevant code area. Use read-only operations:
   - Browse the directory structure with `ls` and `tree`
   - Read relevant source files with the Read tool
   - Search for related code with Grep/Glob
   - Check recent staging commits with `git log --oneline -20`

8. Generate an implementation plan based on the ticket description and codebase analysis:

---

## Implementation Plan: <KEY> — <Title>

**Branch:** `feat/<branch-name>`
**Repo:** `<repo-name>`

### Context
<FACT>
- What the ticket explicitly requires
- Relevant code files found and their current state
- Existing patterns in the codebase that this change should follow
</FACT>

<ASSUME>
- Inferred approach based on codebase patterns
- Estimated scope and complexity
</ASSUME>

### Steps
1. [First change — specific file, specific modification]
2. [Second change — specific file, specific modification]
3. [Tests to add/modify]
4. [Any config or migration changes needed]

### Files to Modify
- `path/to/file.py` — [what to change]
- `path/to/other.py` — [what to change]

### Testing
- [How to verify the changes work]
- [Edge cases to consider]

---

9. Ask the user: "Ready to start implementing? I can begin with step 1."

## Rules

- Always fetch origin before creating the branch — ensure you're branching from latest staging
- The branch name must include the ticket key for traceability
- Be thorough in codebase exploration — read enough files to understand the architecture before proposing changes
- The implementation plan should be specific enough that someone could follow it without additional context
- FACT/ASSUME discipline applies to all analysis
- Do not start implementing until the user confirms the plan
- If the ticket description is too vague to create a plan, say so and suggest using `/jira-clarify` instead
