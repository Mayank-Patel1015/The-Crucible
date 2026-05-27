---
name: ollama
description: Use local Ollama models (running at localhost:11434) to handle tasks without consuming Claude API tokens. Trigger when the user types /ollama, asks to "use a local model", "run this through Ollama", or wants to save Claude tokens on a generation task. Also use proactively for: drafting boilerplate code, generating test fixtures, writing first-pass docs, brainstorming lists, or any large-volume text generation where quality beats cost. Do NOT use for tasks requiring Claude's reasoning depth, tool calls, or real-time data.
---

# Ollama Skill

Delegate generation tasks to locally running Ollama models. Zero API cost, no data leaves the machine.

## Endpoint
```
http://localhost:11434
```

## Step 1 — Discover Available Models

**macOS / Linux (bash):**
```bash
curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('models', [])
if not models:
    print('No models found. Run: ollama pull qwen3:8b')
else:
    for m in models:
        size_gb = m.get('size', 0) / 1e9
        print(f'  {m[\"name\"]}  ({size_gb:.1f} GB)')
"
```

**Windows (PowerShell):**
```powershell
$r = Invoke-RestMethod http://localhost:11434/api/tags
$r.models | ForEach-Object { "$($_.name)  ($([math]::Round($_.size/1GB,1)) GB)" }
```

**Known installed models for this project** (from `autogen_crucible.py`):
- `qwen3:8b` — primary workhorse, good for code + reasoning

## Step 2 — Select the Right Model

| Task | Best Model |
|------|-----------|
| Code generation / review | `qwen3:8b` or `codellama` if available |
| Text drafting / docs | `qwen3:8b` or any 7B+ model |
| Short Q&A / classification | smallest available model |
| Multi-step reasoning | largest available model |

Default to `qwen3:8b` unless the user specifies otherwise.

## Step 3 — Run a Generation

### macOS / Linux (bash):
```bash
curl -s http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:8b",
    "prompt": "YOUR PROMPT HERE",
    "stream": false,
    "options": { "temperature": 0.3, "num_predict": 1024 }
  }' | python3 -c "import json,sys; r=json.load(sys.stdin); print(r.get('response',''))"
```

### Windows (PowerShell):
```powershell
$body = @{
    model   = "qwen3:8b"
    prompt  = "YOUR PROMPT HERE"
    stream  = $false
    options = @{ temperature = 0.3; num_predict = 1024 }
} | ConvertTo-Json

$r = Invoke-RestMethod -Uri http://localhost:11434/api/generate `
     -Method Post -ContentType "application/json" -Body $body
$r.response
```

### OpenAI-compatible endpoint (autogen / openai SDK — same on both platforms):
```
base_url: http://localhost:11434/v1
api_key:  ollama   (dummy — Ollama ignores it)
```
Already configured in `autogen_crucible.py`.

## Step 4 — Capture and Use Output

1. Run the command for your platform via bash or PowerShell
2. Parse the `response` field
3. Present to user or pipe into next step
4. For "draft X" tasks, save output to `The-Crucible-Data/ollama-outputs/YYYY-MM-DD-taskname.md`

## Prompting Tips for Local Models

- Be explicit — local models need more instruction than Claude
- Add "Think step by step." for reasoning tasks
- For code: specify language, style, include a short example
- Keep prompts under 2000 tokens for fast response
- `temperature 0.1–0.3` for code/deterministic, `0.7–0.9` for creative

## Error Handling

| Error | Fix |
|-------|-----|
| `Connection refused` | Run `ollama serve` in a terminal first |
| `model not found` | Run `ollama pull qwen3:8b` |
| Empty response | Increase `num_predict`, check model loaded |
| Slow / timeout | Model still loading — wait 10s, retry |
| PowerShell TLS error | Run `[Net.ServicePointManager]::SecurityProtocol = 'Tls12'` first |

## Integration with The-Crucible

Project already uses Ollama in `autogen_crucible.py` for the AutoGen swarm (qwen3:8b).
Same model available for:
- Generating new mission drafts
- Running Socratic feedback offline (replaces llama-cli in `crucible.py`)
- Batch-processing session data in `The-Crucible-Data/`
- Heavy text generation without touching Claude API quota

## Quick Commands

```bash
# macOS/Linux — Is Ollama running?
curl -s http://localhost:11434/api/tags

# Windows PowerShell — Is Ollama running?
Invoke-RestMethod http://localhost:11434/api/tags

# Both platforms — list models
ollama list

# Both platforms — pull a model
ollama pull qwen3:8b

# macOS/Linux — quick test
curl -s http://localhost:11434/api/generate \
  -d '{"model":"qwen3:8b","prompt":"Say hello in 5 words.","stream":false}' \
  -H "Content-Type: application/json" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['response'])"

# Windows PowerShell — quick test
(Invoke-RestMethod -Uri http://localhost:11434/api/generate -Method Post `
  -ContentType "application/json" `
  -Body '{"model":"qwen3:8b","prompt":"Say hello in 5 words.","stream":false}').response
```
