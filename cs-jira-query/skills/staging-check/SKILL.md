---
name: staging-check
description: Check what's on the staging branch for a specific repo. Use this skill whenever the user asks about staging status, what's deployed, what's on staging, staging vs main, or says things like "what's on staging for creative-studio?", "staging status for media-center", "what's been deployed to staging?", "diff between staging and main for X". Trigger for any mention of checking a staging branch state in any repo under the plaxie project directory.
---

# Staging Check

Quick check of what's on `origin/staging` for a given repo — recent commits, diff from main, deploy readiness.

## Steps

1. Extract the repo name from the user's input (e.g., "creative-studio" from "what's on staging for creative-studio?").

2. Validate the repo exists at `$PLAXIE_PROJECT_ROOT/<repo-name>`. If `PLAXIE_PROJECT_ROOT` is not set, tell the user to set it:
   ```
   export PLAXIE_PROJECT_ROOT=/path/to/your/plaxie
   ```
   If the repo doesn't exist, list available repos and ask the user to pick.

3. Fetch latest remote state:
   ```bash
   cd "${PLAXIE_PROJECT_ROOT}/<repo-name>" && git fetch origin
   ```

4. Gather staging info (all read-only):

   **Recent staging commits:**
   ```bash
   git log origin/staging --oneline -15
   ```

   **Commits on staging but not on main:**
   ```bash
   git log origin/main..origin/staging --oneline
   ```

   **Commits on main but not on staging:**
   ```bash
   git log origin/staging..origin/main --oneline
   ```

   **Diff summary (staging vs main):**
   ```bash
   git diff origin/main...origin/staging --stat
   ```

5. Present the report:

---

## Staging Report: <repo-name>

### Recent Activity (last 15 commits on staging)
```
<git log output>
```

### Staging Ahead of Main
<N commits on staging not yet on main>
```
<commit list or "None — staging and main are in sync">
```

### Main Ahead of Staging
<N commits on main not yet on staging>
```
<commit list or "None — staging has everything from main">
```

### Changed Files (staging vs main)
```
<diff stat output>
```

<FACT>
- Number of commits ahead/behind
- Files changed between branches
- Last commit date on staging
</FACT>

<ASSUME>
- Whether staging appears stable (few recent changes) or active (many recent commits)
- Whether a merge from main to staging might be needed
- Any potential conflicts based on files changed on both branches
</ASSUME>

---

## Rules

- All operations are read-only — never modify the repo
- Always fetch before checking — ensure data is current
- If `origin/staging` doesn't exist, check for common alternatives: `origin/stage`, `origin/develop`, and report what branches are available
- Keep the output concise — this is a quick status check, not a deep analysis
