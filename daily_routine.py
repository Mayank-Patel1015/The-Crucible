#!/usr/bin/env python3
"""
The Sound — Daily Development Routine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Compares local vs remote repos, reads READMEs for unimplemented
features, then uses Claude to surface the top 10 highest-leverage
tasks for the day.

Run manually:
  python daily_routine.py

Schedule (macOS launchd):
  Copy com.crucible.daily_routine.plist → ~/Library/LaunchAgents/
  launchctl load ~/Library/LaunchAgents/com.crucible.daily_routine.plist

Schedule (Windows Task Scheduler):
  schtasks /create /tn "TheSoundDaily" /tr "python \"%USERPROFILE%\\Desktop\\The-Crucible\\daily_routine.py\"" /sc DAILY /st 08:00
"""

import subprocess
import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CROSS-PLATFORM BASE PATH
# Resolves to ~/Desktop on both macOS and Windows.
# Override with env var CRUCIBLE_BASE if your layout differs.
# ─────────────────────────────────────────────
_BASE = Path(os.environ.get("CRUCIBLE_BASE", Path.home() / "Desktop"))

# ─────────────────────────────────────────────
# CONFIG — repo list (paths are relative to _BASE)
# ─────────────────────────────────────────────
REPOS = [
    {
        "name": "Creating-Using-Effective-AI",
        "remote": "https://github.com/Mayank-Patel1015/Creating-Using-Effective-AI",
        "local":  str(_BASE / "Creating-Using-Effective-AI"),
    },
    {
        "name": "Crucible_Tools",
        "remote": "https://github.com/Mayank-Patel1015/Crucible_Tools",
        "local":  str(_BASE / "Crucible_Tools"),
    },
    {
        "name": "Home",
        "remote": "https://github.com/Mayank-Patel1015/Home",
        "local":  str(_BASE / "Home"),
    },
    {
        "name": "My-Crucible",
        "remote": "https://github.com/Mayank-Patel1015/My-Crucible",
        "local":  str(_BASE / "My-Crucible"),
    },
    {
        "name": "The-Crucible",
        "remote": "https://github.com/Mayank-Patel1015/The-Crucible",
        "local":  str(_BASE / "The-Crucible"),
    },
]

# Log directory — Desktop/TheSound_Logs on both platforms
LOG_DIR = _BASE / "TheSound_Logs"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def run_git(args: list[str], cwd: str) -> tuple[str, str, int]:
    """Run a git command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        return "", "git not found — is Git installed and on PATH?", 1
    except subprocess.TimeoutExpired:
        return "", "git command timed out", 1
    except Exception as e:
        return "", str(e), 1


def read_readme(local_path: str) -> str:
    """Read README.md (or CLAUDE.md as fallback) from the local repo."""
    for name in ["README.md", "readme.md", "CLAUDE.md"]:
        p = Path(local_path) / name
        if p.exists():
            try:
                return p.read_text(encoding="utf-8", errors="replace")[:6000]
            except Exception:
                pass
    return "(no README found)"


def check_repo(repo: dict) -> dict:
    """Gathers full sync status for one repo."""
    name         = repo["name"]
    local        = repo["local"]
    remote       = repo["remote"]
    local_exists = Path(local).exists()

    result = {
        "name":               name,
        "remote":             remote,
        "local":              local,
        "local_exists":       local_exists,
        "fetch_ok":           False,
        "ahead":              0,
        "behind":             0,
        "uncommitted":        [],
        "untracked":          [],
        "last_local_commit":  "(unknown)",
        "last_remote_commit": "(unknown)",
        "readme":             "(repo not cloned locally)",
        "errors":             [],
    }

    if not local_exists:
        result["errors"].append(f"Local path does not exist: {local}")
        return result

    _, err, rc = run_git(["fetch", "--quiet"], local)
    if rc != 0:
        result["errors"].append(f"fetch failed: {err}")
    else:
        result["fetch_ok"] = True

    out, _, _ = run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"], local)
    if out:
        parts = out.split()
        if len(parts) == 2:
            result["ahead"]  = int(parts[0])
            result["behind"] = int(parts[1])

    out, _, _ = run_git(["status", "--porcelain"], local)
    for line in out.splitlines():
        if line.startswith("??"):
            result["untracked"].append(line[3:])
        elif line.strip():
            result["uncommitted"].append(line.strip())

    out, _, _ = run_git(["log", "-1", "--pretty=format:%h %s (%ar)"], local)
    if out:
        result["last_local_commit"] = out

    for ref in ["origin/HEAD", "origin/main", "origin/master"]:
        out, _, rc2 = run_git(["log", "-1", "--pretty=format:%h %s (%ar)", ref], local)
        if rc2 == 0 and out:
            result["last_remote_commit"] = out
            break

    result["readme"] = read_readme(local)
    return result


def call_claude(prompt: str) -> str:
    """Call the Anthropic API and return the response text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return (
            "⚠  ANTHROPIC_API_KEY environment variable not set.\n"
            "   macOS:   export ANTHROPIC_API_KEY=your-key  (add to ~/.zshrc)\n"
            "   Windows: setx ANTHROPIC_API_KEY your-key    (restart terminal after)\n"
        )

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1800,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return f"API error {e.code}: {body}"
    except Exception as e:
        return f"Request failed: {e}"


def build_prompt(repo_data: list[dict]) -> str:
    """Construct the analysis prompt from all repo data."""
    sections = []
    for r in repo_data:
        sync_lines = []
        if not r["local_exists"]:
            sync_lines.append("  ❌ NOT CLONED LOCALLY")
        else:
            if r["behind"] > 0:
                sync_lines.append(f"  ⬇  {r['behind']} commit(s) behind remote — needs pull")
            if r["ahead"] > 0:
                sync_lines.append(f"  ⬆  {r['ahead']} commit(s) ahead of remote — needs push")
            if r["uncommitted"]:
                sync_lines.append(f"  📝 {len(r['uncommitted'])} uncommitted change(s): {', '.join(r['uncommitted'][:5])}")
            if r["untracked"]:
                sync_lines.append(f"  ❓ {len(r['untracked'])} untracked file(s)")
            if not r["behind"] and not r["ahead"] and not r["uncommitted"]:
                sync_lines.append("  ✅ In sync with remote")
            sync_lines.append(f"  Local commit:  {r['last_local_commit']}")
            sync_lines.append(f"  Remote commit: {r['last_remote_commit']}")
        if r["errors"]:
            sync_lines.append(f"  ⚠  Errors: {'; '.join(r['errors'])}")

        readme_excerpt = r["readme"][:2000] if r["readme"] else "(no README)"
        sections.append(
            f"### {r['name']}\nRemote: {r['remote']}\n"
            + "\n".join(sync_lines)
            + f"\n\nREADME (excerpt):\n{readme_excerpt}\n"
        )

    return f"""You are a sharp technical advisor helping a solo developer prioritize their day.

Today is {datetime.now().strftime('%A, %B %d, %Y')}.

Below is the current state of 5 GitHub repositories. For each you'll see:
- Sync status (ahead/behind remote, uncommitted changes)
- README excerpt (which often describes planned but unimplemented features)

Your job: Produce exactly **10 numbered action items** for today.

Scoring criteria (in order of priority):
1. **Unblocking** — things stopping other work (missing clones, failed syncs, broken CI)
2. **Core feature gap** — simplest unimplemented feature that directly moves the core user experience forward
3. **Momentum** — easiest win that builds streak/habit/progress (under 30 min each)
4. **Hygiene** — commits/pushes that reduce risk

Rules:
- Each item must be SPECIFIC and ACTIONABLE — a human must be able to start it in 5 minutes.
- State which repo it belongs to.
- Estimate time: (5 min), (15 min), (30 min), (1 hr), etc.
- NO vague suggestions like "improve UX" or "refactor code". Say exactly WHAT to do.
- Prioritize shipping working code over perfect code.
- If a repo isn't cloned, make cloning it item #1.

Format each item as:
N. [REPO] Task description — why it matters. ⏱ (estimated time)

---

{chr(10).join(sections)}
"""


def format_report(repo_data: list[dict], ai_output: str) -> str:
    """Format the final terminal output."""
    now = datetime.now().strftime("%A, %B %d %Y — %I:%M %p")
    sep = "━" * 60

    summary_lines = []
    for r in repo_data:
        if not r["local_exists"]:
            status = "❌ not cloned"
        elif r["errors"] and not r["fetch_ok"]:
            status = "⚠  fetch error"
        elif r["behind"] > 0 and r["ahead"] > 0:
            status = f"⬇{r['behind']} ⬆{r['ahead']} diverged"
        elif r["behind"] > 0:
            status = f"⬇  {r['behind']} behind"
        elif r["ahead"] > 0:
            status = f"⬆  {r['ahead']} ahead"
        elif r["uncommitted"]:
            status = f"📝 {len(r['uncommitted'])} uncommitted"
        else:
            status = "✅ synced"
        summary_lines.append(f"  {r['name']:<35} {status}")

    summary = "\n".join(summary_lines)

    return f"""
{sep}
  THE SOUND — Daily Dev Routine
{sep}
  {now}
  Base path: {_BASE}
{sep}

REPOSITORY STATUS
{sep}
{summary}

{sep}
  TOP 10 THINGS TO DO TODAY
{sep}

{ai_output}

{sep}
"""


def save_log(content: str) -> Path:
    """Save today's report to a log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    filename = LOG_DIR / f"sound_{datetime.now().strftime('%Y-%m-%d')}.txt"
    filename.write_text(content, encoding="utf-8")
    return filename


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"\n⏳ Base path: {_BASE}")
    print("⏳ Checking repositories...", end="", flush=True)

    repo_data = []
    for repo in REPOS:
        print(f"\r⏳ Fetching: {repo['name']:<40}", end="", flush=True)
        repo_data.append(check_repo(repo))

    print(f"\r⏳ Asking Claude for today's top 10...              ", end="", flush=True)

    prompt    = build_prompt(repo_data)
    ai_output = call_claude(prompt)
    report    = format_report(repo_data, ai_output)

    print("\r" + " " * 55 + "\r", end="")
    print(report)

    log_path = save_log(report)
    print(f"\n📄 Report saved → {log_path}\n")


if __name__ == "__main__":
    main()
