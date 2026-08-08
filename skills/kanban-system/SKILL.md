---
name: kanban-system
description: "Hermes Kanban system — orchestrator decomposition playbook and worker pitfalls/examples. Covers the full lifecycle: discover profiles, create linked task graphs, fan-out+fan-in, handle handoffs, and recover stuck workers."
version: 3.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing, workflow, collaboration]
    related_skills: [hermes-agent, hermes-profile-authoring]
---

# Kanban — Multi-Agent Orchestration & Worker Guide

The Hermes Kanban system enables multi-profile collaboration via a durable SQLite task board. This umbrella skill covers both the **orchestrator** role (decompose, route, don't execute) and the **worker** role (lifecycle, handoffs, retries, pitfalls).

> The core lifecycle (6 steps: orient → work → heartbeat → block/complete) and the `KANBAN_GUIDANCE` block are auto-injected into every kanban process's system prompt. This skill provides deeper detail for both roles.

---

## Part 1: Orchestrator — Decomposition Playbook

### Step 0: Discover Available Profiles

Before fanning out, discover the profiles that actually exist on this machine. The dispatcher silently fails to spawn unknown assignee names.

```bash
hermes profile list
```

Cache the result. Never invent profile names.

### When to Use Kanban (vs. delegate_task)

Create Kanban tasks when:
1. **Multiple specialists** are needed
2. **Work should survive** a crash or restart
3. **Human-in-the-loop** may be needed
4. **Parallel subtasks** can run in parallel
5. **Review/iteration** is expected
6. **Audit trail** matters

If none apply, use `delegate_task` instead or answer directly.

### Anti-Temptation Rules (Orchestrator)

- **Do NOT execute the work yourself** — create a task for the right specialist
- **Split multi-lane requests** before creating cards
- **Run independent lanes in parallel** with no parent links
- **Link only true dependencies** with `parents=[...]`
- **Discover profiles first** — never invent assignee names

### Decomposition Playbook

1. Understand the goal (ask clarifying questions if needed)
2. Sketch the task graph:
   - Extract lanes from the request
   - Map each lane to a discovered profile
   - Decide independent vs gated
3. Create cards with `kanban_create(...)` — parent cards first
4. Complete your own orchestrator task with a summary
5. Report back to the user

```python
t1 = kanban_create(title="research: cost comparison", assignee="<profile-A>")["task_id"]
t2 = kanban_create(title="research: performance comparison", assignee="<profile-A>")["task_id"]
t3 = kanban_create(title="synthesize recommendation", assignee="<profile-B>", parents=[t1, t2])["task_id"]
```

### Common Patterns

- **Fan-out + fan-in**: N research cards (no parents), one synthesis card (all parents)
- **Pipeline with gates**: `planner → implementer → reviewer`
- **Same-profile queue**: N tasks, same assignee, no deps
- **Human-in-the-loop**: `kanban_block()` to wait for input
- **Goal-mode cards**: `goal_mode=True` for open-ended tasks where one turn rarely finishes

### Recovering Stuck Workers

When a worker keeps crashing:
1. **Reclaim** — abort the running worker, reset to `ready`
2. **Reassign** — switch to a different profile
3. **Change model** — `hermes -p <profile> model`

See full details in `references/orchestrator.md`.

---

## Part 2: Worker — Lifecycle, Handoffs & Pitfalls

### Workspace Handling

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir | Read/write freely |
| `dir:<path>` | Shared persistent dir | Treat like long-lived state |
| `worktree` | Git worktree | Commit work here |

### Good Summary + Metadata Shapes

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — 14 tests pass",
    metadata={"changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"], "tests_passed": 14},
)
```

**Coding task needing review:** Block with `review-required` prefix, leave structured handoff in a comment first:
```python
kanban_comment(body="review-required handoff: " + json.dumps({"changed_files": [...], "tests_passed": 14}))
kanban_block(reason="review-required: rate limiter shipped, needs eyes before merging")
```

**Research task:**
```python
kanban_complete(
    summary="3 libraries reviewed; vLLM wins on throughput",
    metadata={"sources_read": 12, "recommendation": "vLLM", "benchmarks": {"vllm": 1.0, "sglang": 0.87}},
)
```

### Claiming Cards You Created

Pass `created_cards=[...]` on `kanban_complete`. The kernel verifies each id exists and was created by your profile. **Only list ids captured from successful `kanban_create` return values.**

### Block Reasons That Get Answered Fast

Bad: `"stuck"` — no context. Good: `"Rate limit key choice: IP (simple, NAT-unsafe) or user_id (requires auth)?"`

### Heartbeats Worth Sending

Good: `"epoch 12/50, loss 0.31"`, `"uploaded 47/120 videos"`. Bad: `"still working"` every few seconds.

### Retry Scenarios

When `kanban_show` shows previous runs:
- `timed_out` — previous attempt hit `max_runtime_seconds`
- `crashed` — OOM or segfault
- `spawn_failed` — config issue, ask human via `kanban_block`
- `reclaimed` — operator archived the task

### Do NOT (Worker)

- Call `delegate_task` as a substitute for `kanban_create` (use `kanban_create` for cross-agent handoffs)
- Call `clarify` (no live user — use `kanban_comment` + `kanban_block`)
- Modify files outside `$HERMES_KANBAN_WORKSPACE` unless the task body says to
- Complete a task you didn't finish — block it instead

### Pitfalls

- **Task state can change between dispatch and startup** — always `kanban_show` first
- **Workspace may have stale artifacts** — read the comment thread
- **Don't rely on CLI in containerized backends** — use `kanban_*` tools instead
- **`kanban_link(parent_id, child_id)`** — parent first; mixing up demotes wrong task

See full details in `references/worker.md`.

---

## CLI Fallback (for human operators)

```
kanban_show      ↔ hermes kanban show <id> --json
kanban_complete  ↔ hermes kanban complete <id> --summary "..." --metadata '{...}'
kanban_block     ↔ hermes kanban block <id> "reason"
kanban_create    ↔ hermes kanban create "title" --assignee <profile>
```
