---
name: todo-driven-crucible
description: "Independent background skill for The-Crucible that executes only tasks listed in TODO.md using local models and zero Claude tokens."
modelOptions:
  preferred:
    - "gemma4"
    - "openclaw"
    - "qwen3:8b"
  fallback: "llama-cli"
---

# TODO-Driven Crucible Skill

## What this skill does

This skill runs The-Crucible development workflow as a local background task. It reads only marked TODO.md tasks, routes them to local reasoning engines, executes them with no Claude API or external token usage, and records progress in the repo.

## Key principles

- **TODO-first**: only execute tasks present in `TODO.md`.
- **Marked-only**: do not act on unlisted or unmarked work.
- **Zero Claude tokens**: use local Ollama or `llama-cli` only.
- **OS background task**: designed for Windows Task Scheduler / macOS launchd, not cloud invocation.
- **Failure notifications**: annotate task failures in `TODO.md` with `⚠️ FAILED`.

## Scope

This skill is specific to the `The-Crucible` workspace and should be used for:

- `crucible-web` frontend/back-end integration work
- CLI tooling and local model orchestration
- TODO-driven task execution and local result logging
- Local QA and reasoning using Ollama, OpenClaw, Gemma4, or `llama-cli`

## Prerequisites

- Local Ollama service running at `http://localhost:11434`
- At least one local model available, preferably `gemma4`, `openclaw`, or `qwen3:8b`
- `llama-cli` available for fast local Q&A tasks
- A valid `TODO.md` file in the project root or `crucible-web/`

## Workflow

1. Parse `TODO.md` for markdown tasks and metadata.
2. Select only tasks that are explicitly marked as active.
3. Route tasks by type:
   - **Fast Q&A / small edits** → `llama-cli`
   - **Multi-step reasoning / feature design** → local Ollama model (`qwen3:8b`, `gemma4`, or `openclaw`)
4. Execute the task locally without using Claude.
5. If execution fails, mark the task in `TODO.md` with `⚠️ FAILED` and save an error note.
6. Log the result to local storage (repo DB or structured file) for auditing.

## Task format

Use **Format C**: markdown checkboxes with inline metadata. Example:

```md
- [ ] Implement auth flow — type: reasoning, route: ollama
- [ ] Fix dashboard layout bug — type: qa, route: llama-cli
```

The skill should interpret these patterns and keep execution tightly scoped to listed tasks.

## Failure handling

If a task cannot be completed locally:

- Add or update the line in `TODO.md` with `⚠️ FAILED`
- Preserve the original task text
- Optionally append a one-line reason or identifier
- Do not remove the task without user confirmation

Example:

```md
- [ ] Fix dashboard layout bug — type: qa, route: llama-cli ⚠️ FAILED
```

## Commands

Use the skill with local tooling only:

- `python todo_executor.py` — parse TODO.md and execute eligible tasks
- `python todo_executor.py --check` — validate TODO.md formatting without running tasks
- `python todo_executor.py --dry-run` — preview routes and commands

## Best practices

- Keep all actionable items in `TODO.md`.
- Do not add new tasks during execution; only run existing ones.
- Prefer `gemma4` or `openclaw` if available, else use `qwen3:8b`.
- Keep local model prompts concise and deterministic.
- Use OS-level scheduling to run the skill as a background task, not as a token-bearing external service.

## Notes

- This skill is intentionally independent from Claude and should not depend on Claude tokens or remote APIs.
- It is safe to use in a local development environment where the focus is on executing TODO-driven The-Crucible tasks.
- If you later want to expand to structured validation or cross-task memory, add a separate helper script rather than changing the core skill behavior.
