# The Crucible — CLAUDE.md

Daily AI skill forge. Trains humans to think clearly *with* AI rather than outsource to it.

## Repo Layout

```
The-Crucible/
├── crucible.py          # CLI entry point — local llama-cli + SQLite sessions
├── cqr.py               # Creation Quality Ratio scorer (originality/depth/conciseness)
├── meter.py             # Apple Silicon power metering (sudo powermetrics)
├── autogen_crucible.py  # AutoGen multi-agent swarm → Ollama (qwen3:8b)
├── schema.sql           # SQLite schema: socratic_sessions table
├── tests/               # pytest suite (test_cqr.py, test_schema.py)
├── crucible-web/        # Next.js 15 + Supabase web app
│   ├── app/             # App Router: dashboard, login, signup, api/submit
│   ├── components/      # MissionCard, SubmissionForm, StreakDisplay, CountdownTimer
│   ├── lib/missions.ts  # Mission definitions + getTodaysMission()
│   ├── lib/supabase/    # client.ts / server.ts SSR helpers
│   ├── supabase/schema.sql  # Supabase: profiles, missions, submissions + streak fn
│   └── middleware.ts    # Auth guard (redirects unauthenticated → /login)
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

```bash
# Python
pip install ruff pytest
ruff check .
pytest tests/ -v

# Web
cd crucible-web
npm install
npm run dev       # localhost:3001/dashboard
npm run build
npm run lint

# Ollama (host machine)
ollama list
ollama serve
curl -s http://localhost:11434/api/tags

# AutoGen swarm
pip install pyautogen
python autogen_crucible.py
```

## Data Models

**SQLite** (`literacy.db`) — `socratic_sessions`
- mission_day, topic, human_attempt, ai_response
- cqr REAL, energy_joules, duration_seconds
- autonomy_ratio + watts_average (generated columns)

**Supabase** — `profiles | missions | submissions`
- profiles: current_streak, longest_streak, total_completions, last_completed_date
- submissions: unique(user_id, mission_day)
- `record_submission_and_update_streak()` RPC handles atomic streak logic

## CQR Formula (`cqr.py`)
```
originality = (unique_word_ratio × 0.7 + filler_penalty × 0.3) ^ 1.5
depth       = keyword_hits/8 × structure_score(0.6)
conciseness = min(1.0, target_words / word_count)
CQR         = originality×0.60 + depth×0.25 + conciseness×0.15
```
Keyword markers: `from first principles, define, axiom, assume, counterexample, derive, debug, iterate`

## Missions (lib/missions.ts)

5 missions, difficulty: INITIATE → OPERATIVE → SPECIALIST → ELITE
- Day 1: THE INTERROGATOR — structured 5-point output
- Day 2: PERSONA FORGE — system-prompt persona
- Day 3: THE CONTRARIAN — steelman opposite view (3 counterargs)
- Day 4: CHAIN ARCHITECT — 3-step prompt chain
- Day 5: THE COMPRESSOR — full task in <25 words

`getTodaysMission()` rotates by `Date.now() / 86_400_000 % missions.length`

## Conventions

- Python: ruff linting, no type hints required but preferred
- TS: strict TypeScript, no `any`, Tailwind utility-only (no custom CSS classes)
- Supabase: all DB writes go through RLS policies or security-definer RPCs
- Auth: middleware.ts protects `/dashboard` — always SSR-check user before render
- No mocking DB in tests (real SQLite fixture only)
- `meter.py` requires macOS + `sudo` — skip on Linux CI

## Env Vars (crucible-web/.env.local)

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

## Token-Saving Conventions for Claude

1. Use `/ollama` skill for: boilerplate generation, test fixtures, first-pass docs, mission drafts
2. Read only the specific file needed — don't load full directories
3. `cqr.py` and `meter.py` are pure utilities — rarely need editing
4. Supabase schema is stable — check `supabase/schema.sql` before writing any DB query
5. Store session notes in `The-Crucible-Data/sessions/` not in code comments

## Active Development Notes

- AutoGen swarm (`autogen_crucible.py`) is experimental — not wired to web app yet
- `llama-cli` binary path is hardcoded (`./llama-cli`) — needs to exist locally
- Web app runs on port 3001 (not 3000 — check `next.config.ts` if changed)
- Streak logic is server-side only (Supabase RPC) — do not replicate client-side
