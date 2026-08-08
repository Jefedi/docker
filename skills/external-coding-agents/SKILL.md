---
name: external-coding-agents
description: "Delegate coding tasks to external AI coding CLI tools — Claude Code, Codex (OpenAI), OpenCode. Covers PTY orchestration, print vs interactive mode, parallel worktrees, and PR review for each tool."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agents, claude-code, codex, opencode, automation, refactoring, PR-review]
    related_skills: [hermes-agent, github]
---

# External Coding Agents — Unified Orchestration Guide

Delegate coding tasks to external AI coding agent CLIs. This umbrella covers three tools: **Claude Code** (Anthropic), **Codex** (OpenAI), and **OpenCode** (provider-agnostic). Each has its own section below with specific invocation patterns, but the general approach is shared.

## When to Use External Coding Agents

- Building features or fixing bugs in a codebase
- Reviewing PRs or local changes
- Batch issue fixing with parallel worktrees
- Long-running refactoring sessions
- Tasks outside Hermes's native tool capabilities

## Prerequisites (All Tools)

```bash
# Check what's installed
claude --version 2>/dev/null || echo "Claude Code not installed"
codex --version 2>/dev/null || echo "Codex not installed"
opencode --version 2>/dev/null || echo "OpenCode not installed"
```

**Must run inside a git repository** — all three tools require one.

## General Patterns

### Print Mode (One-Shot, Preferred for Simple Tasks)
```bash
# Claude Code
claude -p "Fix the auth bug" --allowedTools "Read,Edit" --max-turns 10

# Codex
codex exec "Add dark mode toggle"

# OpenCode
opencode run "Add retry logic to API calls"
```

### Interactive PTY Mode (Multi-Turn via tmux)
```bash
terminal(command="tmux new-session -d -s agent -x 140 -y 40")
terminal(command="sleep 3 && tmux send-keys -t agent 'claude -w refactor' Enter")
terminal(command="sleep 30 && tmux capture-pane -t agent -p -S -50")
terminal(command="tmux send-keys -t agent '/exit' Enter && sleep 2 && tmux kill-session -t agent")
```

### Parallel Worktrees
```bash
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="codex exec --full-auto 'Fix issue #78'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="claude -p 'Fix issue #79' --allowedTools 'Read,Edit'", workdir="/tmp/issue-79", background=true)
```

### PTY Dialog Handling
All three tools present confirmation dialogs on first launch. Handle via tmux send-keys:
- **Workspace trust**: `Enter` for default "Yes"
- **Permissions bypass**: `Down` then `Enter` (dialog defaults to "No")

See per-tool references for full dialog handling sequences.

---

## Section A: Claude Code

### Auth
```bash
claude auth login              # OAuth (Pro/Max subscription)
claude auth login --console    # API key billing
claude auth status             # Verify
```

### Key Print Mode Patterns
```bash
# JSON output
claude -p "Analyze auth.py" --output-format json --max-turns 5

# Piped input
cat src/auth.py | claude -p "Review this code"

# Schema-constrained output
claude -p "List all functions" --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}}}'

# CI mode (fast startup, no plugins)
claude --bare -p "Run all tests" --allowedTools "Read,Bash" --max-turns 10
```

### PR Review
```bash
claude -p "Review this PR thoroughly" --from-pr 42 --max-turns 10
```

### Slash Commands (Interactive Only)
`/review`, `/plan`, `/compact`, `/model`, `/effort`, `/memory`, `/agents`, `/mcp`

### Cost & Performance
- Use `--max-turns` (start with 5-10) to prevent runaway
- Use `--model haiku` for simple tasks, `opus` for complex
- Use `--effort low` for faster, cheaper tasks
- Use `/compact` when context gets large (>70% window)

See full reference in `references/claude-code.md`.

---

## Section B: Codex (OpenAI)

### Auth
```bash
# OAuth (via Codex CLI login flow)
# Or set OPENAI_API_KEY
```

### Key Patterns
```bash
# One-shot
codex exec "Build a snake game in Python"

# Background for long tasks
terminal(command="codex exec --full-auto 'Refactor auth module'", workdir="~/project", background=true, pty=true)

# Sandbox modes
codex exec --full-auto "task"    # Sandbox with auto-approve
codex exec --yolo "task"         # No sandbox, no approvals
codex exec --sandbox danger-full-access "task"  # No sandbox for gateway context
```

### PR Review
```bash
REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW
cd $REVIEW && codex exec "Review this PR vs main"
```

### Hermes Gateway Caveat
Codex's bubblewrap sandboxing may fail in gateway contexts. Use `--sandbox danger-full-access` with process-level safety boundaries instead.

### Session Continuation
```bash
codex exec "Start task" > /tmp/session.json
# Resume with --resume
```

See full reference in `references/codex.md`.

---

## Section C: OpenCode

### Auth
```bash
opencode auth list   # Should show at least one provider
```

### Key Patterns
```bash
# One-shot (no PTY needed)
opencode run 'Add retry logic to API calls'

# With context files
opencode run 'Review this config' -f config.yaml -f .env.example

# Force specific model
opencode run 'Refactor auth' --model openrouter/anthropic/claude-sonnet-4

# Interactive TUI (background, pty=true)
terminal(command="opencode", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow")
```

### PR Review
```bash
opencode pr 42
```

### Session & Model Management
```bash
opencode -c                      # Continue last session
opencode -s ses_abc123           # Specific session
opencode session list            # List past sessions
opencode stats                   # Token/cost stats
opencode run 'task' --variant max  # Max reasoning effort
```

### Exit
**Do NOT use `/exit`** — it opens an agent selector. Use Ctrl+C (`\x03`) or `process(action="kill")`.

See full reference in `references/opencode.md`.

---

## Quick Command Comparison

| Action | Claude Code | Codex | OpenCode |
|--------|-------------|-------|----------|
| One-shot | `claude -p "task"` | `codex exec "task"` | `opencode run "task"` |
| Interactive | tmux + `claude` | tmux + `codex` | `opencode` (bg, pty) |
| PR Review | `--from-pr N` | `codex exec "Review PR"` | `opencode pr N` |
| JSON output | `--output-format json` | — | `--format json` |
| Cost cap | `--max-budget-usd` | — | `opencode stats` |
| Model override | `--model` | (env-based) | `--model provider/model` |
| Reasoning depth | `--effort` | — | `--variant` |
| PTY needed | Print: no; TUI: yes | Yes | `run`: no; TUI: yes |
| Parallel-safe | Worktrees | Worktrees | Separate workdirs |

## Pitfalls (All Tools)

1. **PTY required for interactive** — Non-print mode TUI hangs without `pty=true` or tmux
2. **Git repo required** — None run outside a git directory; use `mktemp -d && git init` for scratch
3. **Don't share workdirs** — Use separate git worktrees or temp dirs for parallel sessions
4. **Clean up tmux** — `tmux kill-session -t <name>` after each interactive session
5. **PATH mismatches** — `which -a <tool>` to verify correct binary; pin with absolute path if needed
