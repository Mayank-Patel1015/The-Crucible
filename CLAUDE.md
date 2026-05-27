# The Crucible — CLAUDE.md

Daily AI skill forge. Trains humans to think clearly *with* AI rather than outsource to it.

## Repo Layout

```
The-Crucible/
├── crucible.py          # CLI entry point — cross-platform llama-cli + SQLite
├── cqr.py               # Creation Quality Ratio scorer
├── meter.py             # Power metering — macOS (powermetrics) + Windows (psutil)
├── autogen_crucible.py  # AutoGen multi-agent swarm → Ollama (qwen3:8b)
├── daily_routine.py     # Daily repo-sync + Claude top-10 briefing (cross-platform)
├── schema.sql           # SQLite schema: socratic_sessions
├── tests/               # pytest suite (test_cqr.py, test_schema.py)
├── crucible-web/        # Next.js 15 + Supabase web app
│   ├── app/             # App Router: dashboard, login, signup, api/submit
│   ├── components/      # MissionCard, SubmissionForm, StreakDisplay, CountdownTimer
│   ├── lib/missions.ts  # Mission definitions + getTodaysMission()
│   ├── lib/supabase/    # client.ts / server.ts SSR helpers
│   ├── supabase/schema.sql  # Supabase: profiles, missions, submissions + streak fn
│   └── middleware.ts    # Auth guard → /login
└── .claude/skills/ollama/SKILL.md  # Local Ollama delegation skill
```

## Stack

| Layer | Tech |
|-------|------|
| CLI | Python 3.11, sqlite3, llama-cli (Phi-3-mini-4k q4 GGUF) |
| Local LLM | Ollama @ localhost:11434, model: qwen3:8b |
| Web | Next.js 15 (App Router), TypeScript, Tailwind v4, React 19 |
| Auth + DB | Supabase (Postgres + RLS + SSR auth) |
| CI | GitHub Actions: ruff + pytest (Python), eslint (web) |

## Key Commands

### Python (macOS use `python3`, Windows use `python`)

```bash
# macOS
pip3 install ruff pytest psutil
python3 -m ruff check .
python3 -m pytest tests/ -v

# Windows (PowerShell or cmd)
pip install ruff pytest psutil
python -m ruff check .
python -m pytest tests/ -v
```

### Web (identical on both platforms)

```bash
cd crucible-web
npm install
npm run dev       # localhost:3001/dashboard
npm run build
npm run lint
```

### Ollama

```bash
# Both platforms
ollama list
ollama serve

# macOS/Linux
curl -s http://localhost:11434/api/tags

# Windows PowerShell
Invoke-RestMethod http://localhost:11434/api/tags
```

### llama-cli binary

```bash
# macOS — place binary as: ./llama-cli
# Windows — place binary as: ./llama-cli.exe
# Override either: set LLAMA_CLI=/path/to/binary
```

### AutoGen swarm

```bash
pip install pyautogen        # macOS: pip3
python autogen_crucible.py   # macOS: python3
```

### Daily routine

```bash
# Both platforms (set ANTHROPIC_API_KEY first)
python daily_routine.py

# macOS — set key
export ANTHROPIC_API_KEY=sk-...

# Windows — set key (restart terminal after)
setx ANTHROPIC_API_KEY sk-...
```

## Data Models

**SQLite** (`literacy.db`) — `socratic_sessions`
- mission_day, topic, human_attempt, ai_response
- cqr REAL, energy_joules, duration_seconds
- autonomy_ratio + watts_average (generated columns)

**Supabase** — `profiles | missions | submissions`
- profiles: current_streak, longest_streak, total_completions, last_completed_date
- submissions: unique(user_id, mission_day)
- `record_submission_and_update_streak()` RPC — atomic streak logic

## CQR Formula (`cqr.py`)

```
originality = (unique_word_ratio × 0.7 + filler_penalty × 0.3) ^ 1.5
depth       = keyword_hits/8 × structure_score(0.6)
conciseness = min(1.0, target_words / word_count)
CQR         = originality×0.60 + depth×0.25 + conciseness×0.15
```
Keywords: `from first principles, define, axiom, assume, counterexample, derive, debug, iterate`

## Missions (`lib/missions.ts`)

5 missions, difficulty: INITIATE → OPERATIVE → SPECIALIST → ELITE
- Day 1: THE INTERROGATOR — structured 5-point output
- Day 2: PERSONA FORGE — system-prompt persona
- Day 3: THE CONTRARIAN — steelman opposite view (3 counterargs)
- Day 4: CHAIN ARCHITECT — 3-step prompt chain
- Day 5: THE COMPRESSOR — full task in <25 words

`getTodaysMission()` rotates by `Date.now() / 86_400_000 % missions.length`

## Conventions

- Python: ruff linting, type hints preferred but not required
- TS: strict, no `any`, Tailwind utility-only (no custom CSS)
- Supabase: all DB writes through RLS or security-definer RPCs
- Auth: middleware.ts guards `/dashboard` — always SSR-check user
- No mocking DB in tests (real SQLite fixture only)
- `meter.py`: macOS → powermetrics (accurate); Windows → psutil TDP proxy; Linux → 0.0

## Platform-Specific Notes

| Concern | macOS | Windows |
|---------|-------|---------|
| Python binary | `python3` / `pip3` | `python` / `pip` |
| llama-cli binary | `./llama-cli` | `./llama-cli.exe` |
| LLAMA_CLI override | `export LLAMA_CLI=...` | `set LLAMA_CLI=...` |
| API key | `export ANTHROPIC_API_KEY=...` | `setx ANTHROPIC_API_KEY ...` |
| Power metering | `sudo powermetrics` | `psutil` (install required) |
| curl | Built-in | Built-in (Win 10+) or use PowerShell `Invoke-RestMethod` |
| Repo base path | `~/Desktop` | `%USERPROFILE%\Desktop` |
| Log path | `~/Desktop/TheSound_Logs` | `%USERPROFILE%\Desktop\TheSound_Logs` |
| Schedule daily_routine | launchd plist | `schtasks` |

## Env Vars

```bash
# crucible-web/.env.local
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# Shell (for daily_routine.py)
ANTHROPIC_API_KEY=

# Optional override
LLAMA_CLI=/path/to/llama-cli        # override binary location
CRUCIBLE_BASE=/path/to/Desktop      # override repo base path
```

## Token-Saving Conventions for Claude

1. Use `/ollama` skill for: boilerplate, test fixtures, first-pass docs, mission drafts
2. Read only the specific file needed — don't load full directories
3. `cqr.py` and `meter.py` are stable utilities — rarely need editing
4. Supabase schema is stable — check `supabase/schema.sql` before any DB query
5. Store session notes in `The-Crucible-Data/sessions/` not in code comments

## Active Development Notes

- AutoGen swarm (`autogen_crucible.py`) — experimental, not wired to web app yet
- `llama-cli` must be present locally; path resolved by `_find_llama_cli()` in crucible.py
- Web app runs on port 3001 (not 3000 — check `next.config.ts` if changed)
- Streak logic is server-side only (Supabase RPC) — do not replicate client-side
- `daily_routine.py` uses `Path.home() / "Desktop"` as base; override with `CRUCIBLE_BASE`
