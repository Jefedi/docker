# Hermes Worker Integration — Adapter Code Analysis

This covers the internals of how Paperclip invokes Hermes Agent as a worker subprocess.

## Key Files

The `hermes-paperclip-adapter` npm package is located at:

```
~/.npm/_npx/<hash>/node_modules/hermes-paperclip-adapter/dist/
```

Key files:
- `server/execute.js` — spawns `hermes chat` as child process
- `server/test.js` — environment checks (CLI, API keys, provider)
- `server/index.js` — exports, session codec
- `server/detect-model.js` — reads `~/.hermes/config.yaml` for provider/model
- `shared/constants.js` — default CLI path, timeout, model

## Environment Propagation Chain

```
Hermes Agent (Python)          # ~/.hermes/.env → os.environ (Python only)
  └─ terminal tool spawns bash  # inherits shell env, NOT Python os.environ
       └─ npx paperclipai run   # npx sanitizes env further
            └─ Node.js process  # process.env has only shell-inherited vars
                 └─ hermes chat -q "..."  # subprocess of Node
```

**Key insight:** `process.env` in execute.js (line 328):
```javascript
const env = {
    ...process.env,
    ...buildPaperclipEnv(ctx.agent),
};
```

This means only shell environment vars plus Paperclip's own env helpers reach the Hermes subprocess. The API keys from `~/.hermes/.env` never arrive.

## testEnvironment flow

`test.js` runs these checks:
1. CLI installed — runs `hermes --version`
2. CLI version — logs version string
3. Python available — runs `python3 --version`
4. Model config — checks adapter config for model override
5. **API keys** — checks `config.env` (Paperclip secrets) then `process.env`:
   ```javascript
   const has = (key) => !!(resolvedEnv[key] ?? process.env[key]);
   ```
6. Provider consistency — warns if adapter config provider mismatches `~/.hermes/config.yaml`

The `testEnvironment` API returns HTTP 200 even with warnings. Status is `"warn"` not `"fail"`.

## execute flow

1. Resolves model, provider, timeout from config
2. Detects provider from `~/.hermes/config.yaml` via `detectModel()`
3. Builds prompt from template (task/comment/heartbeat variants)
4. Spawns: `hermes chat -q "<prompt>" -Q --yolo --source tool`
5. Parses stdout for session ID, token usage, cost
6. Returns structured result to Paperclip

## Prompt Templates

The adapter has 3 prompt variants:
- **Task prompt** — issue assigned to agent, includes workflow instructions (mark complete via curl, post comments)
- **Comment prompt** — someone commented on an issue the agent is working on
- **Heartbeat/no-task prompt** — wake-up check: list open issues, pick highest priority, do the work

## Environment in execute

```javascript
const env = {
    ...process.env,
    ...buildPaperclipEnv(ctx.agent),
};
if (ctx.runId)
    env.PAPERCLIP_RUN_ID = ctx.runId;
if (taskId)
    env.PAPERCLIP_TASK_ID = taskId;
const userEnv = config.env;
if (userEnv && typeof userEnv === "object") {
    Object.assign(env, userEnv);  // adapter-configured secrets override
}
```

To pass API keys, set them via Paperclip's agent adapter config (the `env` field in the adapter config) which Paperclip resolves from its secret store before calling execute.

## Session Persistence

The adapter persists sessions across agent heartbeats:
- Session ID is extracted from Hermes' quiet-mode output: `session_id: <uuid>`
- Stored in `executionResult.sessionParams.sessionId`
- Passed back on next run via `--resume <sessionId>` CLI flag