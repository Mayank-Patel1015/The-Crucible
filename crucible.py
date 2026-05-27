import sqlite3, subprocess, time, matplotlib.pyplot as plt, os, sys
from pathlib import Path
from cqr import compute_cqr
from meter import sample_hardware_power

DB = "literacy.db"
MODEL = "models/Phi-3-mini-4k-instruct-q4.gguf"

# Cross-platform llama-cli binary resolution.
# 1. Honour LLAMA_CLI env var if set (lets CI/CD or users override).
# 2. Look for the binary next to this script.
# 3. Fall back to searching PATH.
def _find_llama_cli() -> str:
    if env := os.environ.get("LLAMA_CLI"):
        return env
    binary = "llama-cli.exe" if sys.platform == "win32" else "llama-cli"
    local = Path(__file__).parent / binary
    if local.exists():
        return str(local)
    return binary  # hope it's on PATH

LLAMA_CLI = _find_llama_cli()

MISSIONS = {
    1: {
        "topic": "Day 1 - Build a 1-Neuron Perceptron",
        "prompt": (
            "From first principles, implement a 1-neuron perceptron in pure Python "
            "that computes weighted sum + sigmoid. Explain every single symbol as if "
            "teaching a 12-year-old. No libraries, no copy-paste."
        ),
    }
}


def run_llama(prompt: str) -> str:
    system_prompt = (
        "<|system|>You are a strict Socratic crucible. Point out ONLY logical faults, "
        "missing definitions, or unstated assumptions in the user's attempt. NEVER give "
        "code, answers, or hints. Ask ONE sharp question that forces deeper human "
        "generation. Under 80 words.<|end|>\n"
        f"<|user|>Topic: {prompt}<|end|>\n"
        "<|assistant|>"
    )
    cmd = [LLAMA_CLI, "-m", MODEL, "-p", system_prompt,
           "--temp", "0.1", "-n", "100", "--no-mmap"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


def record_attempt(day, topic, human, ai, joules, secs):
    metrics = compute_cqr(human, ai)
    conn = sqlite3.connect(DB)
    conn.execute(
        """INSERT INTO socratic_sessions
           (mission_day, topic, human_attempt, ai_response,
            human_word_count, ai_word_count, cqr, energy_joules, duration_seconds)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            day, topic, human, ai,
            metrics["breakdown"]["human_words"],
            metrics["breakdown"]["ai_words"],
            metrics["cqr"], joules, secs,
        ),
    )
    conn.commit()
    conn.close()
    return metrics["cqr"]


def plot_progress():
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT mission_day, cqr FROM socratic_sessions ORDER BY mission_day"
    ).fetchall()
    conn.close()
    if rows:
        days, scores = zip(*rows)
        plt.figure(figsize=(8, 5))
        plt.plot(days, scores, marker="o", linewidth=2)
        plt.title("The Crucible — Your AI Creation Mastery (CQR)")
        plt.xlabel("Mission Day")
        plt.ylabel("Creation Quality Ratio (0–1)")
        plt.grid(True)
        plt.show()


def main():
    print("=== THE CRUCIBLE v0.1 — Live ===")
    print(f"[llama-cli] {LLAMA_CLI}")
    try:
        day = int(input("\nEnter mission day [1]: ") or 1)
    except (ValueError, EOFError):
        day = 1

    if day not in MISSIONS:
        print("Mission not ready yet. Starting Day 1.")
        day = 1

    mission = MISSIONS[day]
    print(f"\n=== MISSION {day}: {mission['topic']} ===")
    print(mission["prompt"])

    human = input("\n>>> Your original attempt (from first principles):\n")
    if len(human.strip()) < 30:
        print("Too short. Try again with real effort.")
        return

    print("\nThinking + metering...")
    start = time.time()
    joules, watts = sample_hardware_power(40)
    ai_resp = run_llama(f"{mission['topic']}\nUser attempt:\n{human}")
    duration = time.time() - start

    cqr = record_attempt(day, mission["topic"], human, ai_resp, joules, duration)
    print(f"\n=== SOCRATIC FEEDBACK ===\n{ai_resp}")
    print(f"\nCQR: {cqr:.3f} | Energy: {joules:.1f}J | Avg Power: {watts:.1f}W")
    plot_progress()


if __name__ == "__main__":
    main()
