#!/usr/bin/env python3
"""The Crucible TODO executor.

Reads `crucible-web/TODO.md` or `crucible-web/TODO-PLAN.md`, executes unchecked tasks
one at a time using local models, and updates `crucible-web/TODO.md` with success or
failure status. Logs execution history to `todo_executor.log`.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import subprocess
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parent
CRUCIBLE_WEB = ROOT / "crucible-web"
LOG_FILE = ROOT / "todo_executor.log"
PREFERRED_OLLAMA_MODELS = ["gemma4", "openclaw", "qwen3:8b"]
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

TASK_LINE_RE = re.compile(
    r"^(?P<prefix>\s*[-*]\s*\[(?P<checked>[ xX])\]\s*)(?P<body>.*)$"
)

META_SPLIT_RE = re.compile(r"\s*[;,]\s*")
META_ITEM_RE = re.compile(r"^(?P<key>[A-Za-z0-9_ -]+)\s*:\s*(?P<value>.+)$")
STATUS_TAG_RE = re.compile(r"\s*⚠️\s*(FAILED|NEED HUMAN INPUT)(?:\s*:\s*(.+))?\s*$")


@dataclass
class Task:
    line_index: int
    prefix: str
    checked: bool
    text: str
    metadata: Dict[str, str]
    route: Optional[str]
    type: Optional[str]
    status: Optional[str]
    reason: Optional[str]
    raw_line: str

    @property
    def normalized_line(self) -> str:
        meta_items = []
        if self.type:
            meta_items.append(f"type: {self.type}")
        if self.route:
            meta_items.append(f"route: {self.route}")
        meta = ", ".join(meta_items)
        line = f"{self.prefix}{self.text.strip()}"
        if meta:
            line += f" — {meta}"
        if self.status:
            if self.reason:
                line += f" ⚠️ {self.status}: {self.reason}"
            else:
                line += f" ⚠️ {self.status}"
        return line


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def find_todo_file() -> Optional[Path]:
    for name in ["TODO.md", "TODO-PLAN.md"]:
        candidate = CRUCIBLE_WEB / name
        if candidate.exists():
            return candidate
    return None


def strip_status_tags(text: str) -> str:
    return STATUS_TAG_RE.sub("", text).strip()


def parse_metadata(text: str) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    for item in META_SPLIT_RE.split(text):
        item = item.strip()
        if not item:
            continue
        m = META_ITEM_RE.match(item)
        if m:
            key = m.group("key").strip().lower()
            value = m.group("value").strip().lower()
            metadata[key] = value
    return metadata


def infer_route(task_type: Optional[str], metadata_route: Optional[str]) -> Optional[str]:
    if metadata_route:
        return metadata_route
    if not task_type:
        return None
    task_type = task_type.lower()
    if task_type == "qa":
        return "llama-cli"
    if task_type == "reasoning":
        return "ollama"
    if task_type in {"human", "manual", "need human", "needs human"}:
        return "human"
    return None


def needs_human(task: Task) -> bool:
    if task.route == "human":
        return True
    if task.type and task.type.lower() in {"human", "manual", "need human", "needs human"}:
        return True
    if "need human" in task.text.lower() or "human input" in task.text.lower():
        return True
    return False


def parse_tasks(lines: Sequence[str]) -> Tuple[List[Task], List[str]]:
    tasks: List[Task] = []
    for index, line in enumerate(lines):
        match = TASK_LINE_RE.match(line)
        if not match:
            continue
        prefix = match.group("prefix")
        checked = match.group("checked").strip().lower() == "x"
        body = match.group("body").strip()
        body = strip_status_tags(body)
        text, metadata_text = split_body_and_metadata(body)
        metadata = parse_metadata(metadata_text)
        task = Task(
            line_index=index,
            prefix=prefix,
            checked=checked,
            text=text.strip(),
            metadata=metadata,
            route=infer_route(metadata.get("type"), metadata.get("route")),
            type=metadata.get("type"),
            status=None,
            reason=None,
            raw_line=line,
        )
        tasks.append(task)
    return tasks, list(lines)


def split_body_and_metadata(body: str) -> Tuple[str, str]:
    if "—" in body:
        left, right = body.split("—", 1)
        return left.strip(), right.strip()
    if "--" in body:
        left, right = body.split("--", 1)
        return left.strip(), right.strip()
    if "-" in body:
        # preserve hyphens inside the task text if the left part seems more descriptive
        parts = body.split("-", 1)
        return body.strip(), ""
    return body.strip(), ""


def run_llama_cli(task: Task) -> Tuple[bool, str]:
    llama_cli = find_llama_cli()
    model = os.environ.get("LLAMA_MODEL")
    if not llama_cli:
        return False, "llama-cli binary not found on PATH and LLAMA_CLI is not set"
    if not model:
        return False, "LLAMA_MODEL is not set; cannot run llama-cli task"

    prompt = (
        f"The Crucible repo development task:\n{task.text}\n\n"
        "Respond with a short, practical answer for a developer."
    )
    cmd = [llama_cli, "-m", model, "-p", prompt, "--temp", "0.1", "-n", "200", "--no-mmap"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        return False, f"llama-cli binary not found: {llama_cli}"
    except subprocess.TimeoutExpired:
        return False, "llama-cli timed out"

    if result.returncode != 0:
        return False, result.stderr.strip() or "llama-cli failed with no stderr"
    return True, result.stdout.strip()


def fetch_ollama_models() -> List[str]:
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return models
    except Exception as exc:
        logging.debug("Ollama model list failed: %s", exc)
        return []


def choose_ollama_model() -> Tuple[Optional[str], str]:
    available = fetch_ollama_models()
    if not available:
        return None, f"Cannot reach Ollama at {OLLAMA_URL} or no models available"
    for model in PREFERRED_OLLAMA_MODELS:
        if model in available:
            return model, ""
    return None, f"No preferred Ollama model installed; available models: {', '.join(available)}"


def run_ollama(task: Task) -> Tuple[bool, str]:
    model, err = choose_ollama_model()
    if not model:
        return False, err

    prompt = (
        f"The Crucible repo development task:\n{task.text}\n\n"
        "Respond with a short, practical developer-level answer."
    )
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 512},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            if "response" in data:
                return True, data["response"].strip()
            if "text" in data:
                return True, data["text"].strip()
            return False, "Ollama response missing expected fields"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, f"Ollama HTTP error {exc.code}: {body}"
    except urllib.error.URLError as exc:
        return False, f"Ollama connection error: {exc.reason}"
    except Exception as exc:
        return False, f"Ollama request failed: {exc}"


def find_llama_cli() -> str:
    if env := os.environ.get("LLAMA_CLI"):
        return env
    binary = "llama-cli.exe" if sys.platform == "win32" else "llama-cli"
    local = ROOT / binary
    if local.exists():
        return str(local)
    return binary


def execute_task(task: Task, dry_run: bool = False) -> Task:
    logging.info("Processing task: %s", task.text)

    if needs_human(task):
        task.status = "NEED HUMAN INPUT"
        task.reason = "Task requires explicit human input"
        logging.info("Task marked as needing human input")
        return task

    if dry_run:
        task.status = None
        logging.info("Dry run: would execute task with route=%s", task.route)
        return task

    if not task.route:
        task.status = "FAILED"
        task.reason = "Missing task type or route metadata"
        logging.error("Task failed: %s", task.reason)
        return task

    if task.route == "llama-cli":
        ok, result = run_llama_cli(task)
    elif task.route == "ollama":
        ok, result = run_ollama(task)
    else:
        task.status = "FAILED"
        task.reason = f"Unsupported route: {task.route}"
        logging.error("Task failed: %s", task.reason)
        return task

    if not ok:
        task.status = "FAILED"
        task.reason = result
        logging.error("Task failed: %s", task.reason)
        return task

    task.checked = True
    task.status = None
    task.reason = None
    logging.info("Task completed successfully")
    return task


def patch_lines(lines: List[str], tasks: List[Task]) -> List[str]:
    updated = list(lines)
    for task in tasks:
        if task.line_index < 0 or task.line_index >= len(updated):
            continue
        if task.status == "NEED HUMAN INPUT":
            updated[task.line_index] = task.normalized_line
        elif task.status == "FAILED":
            updated[task.line_index] = task.normalized_line
        elif task.checked:
            updated[task.line_index] = task.normalized_line
        else:
            updated[task.line_index] = task.normalized_line
    return updated


def write_lines(path: Path, lines: List[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    configure_logging()
    args = argv or sys.argv[1:]
    dry_run = "--dry-run" in args

    todo_file = find_todo_file()
    if not todo_file:
        logging.error("No TODO.md or TODO-PLAN.md found in crucible-web/")
        print("No TODO.md or TODO-PLAN.md found in crucible-web/")
        return 1

    lines = todo_file.read_text(encoding="utf-8").splitlines()
    tasks, _ = parse_tasks(lines)
    if not tasks:
        logging.info("No markdown checkbox tasks found in %s", todo_file)
        print(f"No markdown checkbox tasks found in {todo_file}")
        return 0

    for task in tasks:
        if task.checked:
            continue
        execute_task(task, dry_run=dry_run)
        if not dry_run:
            write_lines(todo_file, patch_lines(lines, [task]))
            lines = todo_file.read_text(encoding="utf-8").splitlines()

    if dry_run:
        logging.info("Dry run completed")
        print("Dry run completed. No changes were written.")
    else:
        logging.info("Execution completed")
        print("Task execution complete. Updated", todo_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
