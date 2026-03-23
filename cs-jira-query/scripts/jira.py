#!/usr/bin/env python3
"""Jira Query — token-efficient CLI for agents (API v3)

Usage:
  jira.py get <KEY>                                    # single ticket
  jira.py get <KEY> --comments                         # with last 5 comments
  jira.py search "<JQL>" [--max N]                     # JQL search (default 20)
  jira.py backlog <PROJECT> [--sp N] [--prefix "[BE]"] # backlog up to N story points
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from base64 import b64encode

# --- Config ---

REQUIRED_VARS = ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")
STORY_POINTS_FIELD = os.environ.get("JIRA_STORY_POINTS_FIELD", "customfield_10005")
BASE_FIELDS = f"summary,assignee,status,{STORY_POINTS_FIELD}"
DESC_MAX_CHARS = 500
COMMENT_MAX_CHARS = 300
COMMENT_SHOW_LAST = 5


def get_config():
    missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
    if missing:
        print("ERROR: Missing env vars: " + ", ".join(missing))
        print("Set these:")
        print("  JIRA_BASE_URL=https://yourcompany.atlassian.net")
        print("  JIRA_EMAIL=you@company.com")
        print("  JIRA_API_TOKEN=<from https://id.atlassian.com/manage-profile/security/api-tokens>")
        sys.exit(1)
    return {
        "base": os.environ["JIRA_BASE_URL"].rstrip("/"),
        "auth": b64encode(f"{os.environ['JIRA_EMAIL']}:{os.environ['JIRA_API_TOKEN']}".encode()).decode(),
    }


def api_get(cfg, path, params=None):
    url = f"{cfg['base']}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {cfg['auth']}",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
            msgs = body.get("errorMessages", []) + [str(v) for v in body.get("errors", {}).values()]
            print("ERROR: " + "; ".join(msgs))
        except (json.JSONDecodeError, UnicodeDecodeError):
            print(f"ERROR: HTTP {e.code} — {e.reason}")
        sys.exit(1)


# --- ADF text extraction ---

def extract_text(node):
    """Extract plain text from Atlassian Document Format JSON."""
    if not node or not isinstance(node, dict):
        return str(node) if node else ""
    if node.get("type") == "text":
        return node.get("text", "")
    return " ".join(extract_text(c) for c in node.get("content", []))


# --- Formatters ---

def format_issue(fields, key, show_comments=False):
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
        if len(desc) > DESC_MAX_CHARS:
            desc = desc[:DESC_MAX_CHARS] + "..."
    else:
        desc = "No description"
    print(f"Description: {desc}")

    if show_comments:
        comments = fields.get("comment", {}).get("comments", [])
        if comments:
            print(f"\n--- Comments ({len(comments)}, showing last {COMMENT_SHOW_LAST}) ---")
            for c in comments[-COMMENT_SHOW_LAST:]:
                author = c.get("author", {}).get("displayName", "Unknown")
                body_raw = c.get("body", "")
                body = extract_text(body_raw) if isinstance(body_raw, dict) else str(body_raw or "")
                print(f"[{author}]: {body[:COMMENT_MAX_CHARS]}")
        else:
            print("\nNo comments.")


def format_search(issues, target_sp=0):
    total_sp = 0
    results = []
    for issue in issues:
        fields = issue["fields"]
        sp = fields.get(STORY_POINTS_FIELD) or 0
        try:
            sp = float(sp)
        except (ValueError, TypeError):
            sp = 0
        total_sp += sp
        assignee = fields.get("assignee")
        name = assignee["displayName"] if assignee else "Unassigned"
        status = fields.get("status", {}).get("name", "?")
        sp_display = int(sp) if sp == int(sp) else sp
        results.append(f"{issue['key']}: {fields.get('summary', '')} | {name} | {status} | SP: {sp_display}")
        if target_sp > 0 and total_sp >= target_sp:
            break

    total_display = int(total_sp) if total_sp == int(total_sp) else total_sp
    print(f"Found {len(results)} tasks (total SP: {total_display})\n")
    for r in results:
        print(r)


# --- Arg parsing ---

def parse_opts(args, spec):
    """Parse optional flags from args list. spec is a dict of flag -> (type, default).
    Returns (positional_args, parsed_opts). Unknown flags cause an error."""
    opts = {k: v[1] for k, v in spec.items()}
    positional = []
    i = 0
    while i < len(args):
        if args[i] in spec:
            if i + 1 >= len(args):
                print(f"ERROR: {args[i]} requires a value")
                sys.exit(1)
            try:
                opts[args[i]] = spec[args[i]][0](args[i + 1])
            except (ValueError, TypeError):
                print(f"ERROR: Invalid value for {args[i]}: {args[i + 1]}")
                sys.exit(1)
            i += 2
        elif args[i].startswith("--"):
            print(f"ERROR: Unknown flag: {args[i]}")
            sys.exit(1)
        else:
            positional.append(args[i])
            i += 1
    return positional, opts


# --- Commands ---

def cmd_get(cfg, args):
    if not args:
        print("Usage: jira.py get <KEY> [--comments]")
        sys.exit(1)

    key = args[0]
    show_comments = "--comments" in args

    req_fields = f"{BASE_FIELDS},description"
    if show_comments:
        req_fields += ",comment"

    data = api_get(cfg, f"/rest/api/3/issue/{key}", {"fields": req_fields})
    format_issue(data["fields"], data["key"], show_comments)


def cmd_search(cfg, args):
    positional, opts = parse_opts(args, {"--max": (int, 20)})
    if not positional:
        print('Usage: jira.py search "<JQL>" [--max N]')
        sys.exit(1)

    data = api_get(cfg, "/rest/api/3/search/jql", {
        "jql": positional[0],
        "fields": BASE_FIELDS,
        "maxResults": opts["--max"],
    })
    format_search(data.get("issues", []))


def cmd_backlog(cfg, args):
    positional, opts = parse_opts(args, {
        "--sp": (int, 10),
        "--prefix": (str, ""),
    })
    if not positional:
        print('Usage: jira.py backlog <PROJECT> [--sp N] [--prefix "[BE]"]')
        sys.exit(1)

    project = positional[0]
    jql = f"project = {project} AND status = Backlog"
    if opts["--prefix"]:
        jql += f' AND summary ~ "\\"{opts["--prefix"]}\\""'
    jql += " ORDER BY rank ASC"

    data = api_get(cfg, "/rest/api/3/search/jql", {
        "jql": jql,
        "fields": BASE_FIELDS,
        "maxResults": 50,
    })
    format_search(data.get("issues", []), opts["--sp"])


HELP = """\
Jira Query — token-efficient CLI (API v3)

Commands:
  jira.py get <KEY>                    Single ticket details
  jira.py get <KEY> --comments         Include last 5 comments
  jira.py search "<JQL>" [--max N]     JQL search (default 20 results)
  jira.py backlog <PROJECT> [--sp N] [--prefix "[BE]"]
                                       Backlog tasks up to N SP, filtered by title prefix

Examples:
  jira.py get CR-123
  jira.py get CR-123 --comments
  jira.py search "assignee = currentUser() AND status != Done"
  jira.py backlog BE --sp 15
  jira.py backlog CR --sp 10 --prefix "[BE]"

Env vars required: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN"""

COMMANDS = {
    "get": cmd_get,
    "search": cmd_search,
    "backlog": cmd_backlog,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help", "-h"):
        print(HELP)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(HELP)
        sys.exit(1)

    cfg = get_config()
    COMMANDS[cmd](cfg, sys.argv[2:])
