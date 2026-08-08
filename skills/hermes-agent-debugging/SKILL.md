---
name: hermes-agent-debugging
description: "Comprehensive debugging guide for Hermes Agent: logs, error patterns, command diagnostics, state snapshots, and tool usage pitfalls. Designed to quickly pinpoint failures in gateway, cron, profiles, or skill execution and to provide step‑by‑step work‑arounds."
version: 1.0.0
author: Hermes core devs
license: MIT
---

# Overview

When something goes wrong in Hermes you often see three kinds of evidence:

1. **Logs** – the contextual history of the running process.
2. **State snapshots** – saved files where the model or one of the tools left a trace.
3. **Error messages** – the LLM’s natural‑language description or the tool’s return value.

With this skill we provide a one‑stop checklist of the most common failure modes, how to replicate them, and how to solve or avoid them.

---

## 1. Logging

Hermes writes a structured log per profile in `~/.hermes/logs/${profile}.log`. The log uses plain JSON lines, so you can tail it with `journalctl -f -o cat` or `tail -f`.

Typical fields:

| name | type | purpose |
|------|------|---------|
| `timestamp` | ISO8601 | When it happened |
| `level` | `INFO/DEBUG/WARN/ERROR` | Severity |
| `category` | `core/gateway/skill/cron/delegate` | Source |
| `message` | string | Human‑readable text |
| `details` | dict | Optional structured payload |

#### Common log patterns

- `"Model prompt exceeds limit"` – Breach token budget.
- `"Tool call id 12345 failed"` – Either the LLM sent a malformed function call or the tool returned non‑JSON.
- `"Context compression terminated early"` – Likely an `dict` overload or memory-limited profile.
- `"AUTIL / platform backend leak"` – Long‑running process that didn't exit.

You can parse the log with the bundled `log_parser.py`::

```bash
python -m hermes.tools.log_parser --input $HOME/.hermes/logs/default.log --filter=error
```

It outputs a timeline of all error events.

---

## 2. State Snapshots

Certain modules figure out where into a prompt a large document, file list, or external resource was.

| Snapshot Type | Purpose |
|----------------|---------|
| `snapshot/<id>` | Serialized prompt or tool interaction, useful for reproducing a failure. It contains the raw LLM prompt (without compression). |
| `crontab/<job_id>.<date>.json` | Cronjob output stored for later on‑call or debugging. |
| `sessions/<session_id>.jsonl` | Full conversation stream, with the step number that produced the error. |

You can inspect them via `hermes snapshots view <id>` or manually open.

---

## 3. Error Messages

The LLM often emits helpful error text. For instance, a missing tool will produce:

```text
I’m sorry but I can’t complete that request. The error is: Tool "xyz" is not available or was misconfigured.
```

Follow these steps:

1. **Check the tool registry:** `hermes tools list`.
2. **Verify env vars:** `hermes config env-path`.
3. **Inspect the tool’s check_fn** – Often missing credentials or an unavailable dependency.
4. **Re‑run the LLM prompt** with `-v` to see the full original function call.
5. **If a gateway error, consult the platform’s metrics** via its own dashboard (e.g., for Discord: `https://discord.com/developers/applications/…`).

---

## 4. Diagnostic Procedure

### 4.1 Generic “nothing happened” case

1. Verify the agent is running (process list). On Linux check `ps aux | grep hermes`.
2. Confirm logs contain `Started eligibility loop for profile <profile>`.
3. Run `hermes doctor` and review any `ERROR`.
4. If the gateway died, `systemctl --user status hermes-gateway` shows exit code.

### 4.2 Skill regression

- `hermes skills update` will check each skill’s `backwards-compatibility` linters.
- If a skill fails to load, the log shows a `ModuleNotFoundError` with the stack trace.
- Re‑run `skill_view(name)` to display the source and fix any obvious oversight.

### 4.3 Cron stuck

- `hermes cron list --verbose` shows start time and status.
- Check environment: a missing file or expired key can block cron. View its output with `hermes cron logs <job_id>`.
- In background mode, `process(action='poll', session_id='…')` reveals progressive output.

---

## 5. Common Work‑Arounds

| Problem | Work‑Around |
|---------|-------------|
| 12‑hour OAuth token expires for Discord | Use OAuth refresh flow in `hermes auth add discord`. |
| `hermes` cannot run a tool because terminal isn’t on PATH | `hermes config set terminal.backend "bash"` and ensure `/usr/bin` is in PATH. |
| `hermes` logs out due to memory shortage | Switch to `hermes --yolo` and reduce `agent.max_turns` or enable `compression.enabled`. |
| Launching the dashboard fails on Pangolin | Stop Pangolin and expose port 9120 via a public tunnel, then restart the dashboard. |
| `vision_analyze` returns 401 `token_not_found_in_db` | The LiteLLM virtual key configured in `auxiliary.vision.api_key` (or any auxiliary section) no longer exists in the `LiteLLM_VerificationToken` table. Check if it's in `LiteLLM_DeletedVerificationToken` (deleted keys). Fix: create a new key via `docker exec litellm python3` with `os.environ['LITELLM_MASTER_KEY']`, then `hermes config set auxiliary.<section>.api_key <key> --force` for all 14 sections. Full procedure in the `hermes-infra-config` skill → `references/litellm-proxy-tracking.md` → « Procédure complète — Rotation de toutes les clés auxiliary Hermes ». |
| `Provider authentication failed` in gateway | Same root cause as 401 above — the LiteLLM virtual key is stale/deleted. The main model (provider `ollama-cloud` direct to `ollama.com/v1`) works independently, but auxiliary models routed through LiteLLM (`127.0.0.1:4000`) fail. See `hermes-infra-config` skill for key rotation. |
+\n+### 5.1 OIDC Discovery endpoint blocked by SSO
+* **Situation** – When a OIDC provider is exposed via a web service that requires SSO (e.g., a private Pangolin resource) but you also expose the discovery endpoint `/.well-known/openid-configuration`.  The service will return `403` for that path, causing any OAuth flow that starts with discovery to fail immediately.
+* **Root cause** – The internal Pub (Pangolin) resource config has `SSO` enabled *or* a reverse‑proxy rule that redirects `/\.well-known/` to the login page.
+* **Fix** –
+  1. Disable the SSO requirement on that specific resource or create an exception for the discovery path.
+  2. If using a reverse proxy, add a rule to bypass authentication for `/.well-known/*`.
+  3. In a Docker‑hosted provider, expose the discovery endpoint on a public, non‑protected port or add a small node/Go service that proxies to the internal OIDC server and strips the Auth header.
+* **Post‑condition** – Running `curl https://\<provider\>/\.well-known/openid-configuration` returns `200` JSON, and any OIDC client (including Hermes on iOS) can successfully complete the authentication flow.
+* **Example** – For a Pangolin instance:
+   ```bash
+   # In the Pangolin UI, open the resource menu for `id.jefe.ovh`
+   # Toggle “SSO” OFF for the “/.well‑known/” backend route
+   # OR add a rule in the reverse‑proxy:
+   # location /{/.well-known/} { allow all; proxy_pass http://127.0.0.1:1411; }
+   ```
+   After applying, restart the resource and test the discovery again.

| On Windows `Alt+Enter` doesn’t add newline | Use `Ctrl+Enter` or set terminal to use `xterm`/mintty for split‑screen. |
| Secret redactor blocks phone numbers in ALL agent outputs | Hermes secret redactor masks E.164 phone numbers (`+337****5858`) in **every** tool output: `terminal` stdout, `docker exec`, `read_file`, `execute_code`, even Python scripts reading files from disk. The agent **cannot** extract a phone number from signal-cli and write it to `.env` programmatically — `sed` captures the already-redacted string. **Fix:** the user must run the extraction + write manually in their own terminal (outside the agent), where redaction does not apply. Example for Signal setup: `NUM=$(docker exec signal-api grep '"number"' /home/.local/share/signal-cli/data/accounts.json | cut -d'"' -f4) && sed -i "s\|SIGNAL_ACCOUNT=.*\|SIGNAL_ACCOUNT=$NUM\|" /opt/data/.env` |
| `hermes config edit` fails with "No editor found" | No `$EDITOR` set and no nano/vim installed. Either `apt install nano && export EDITOR=nano`, or use `hermes config set key value` for individual values, or append to `.env` / `config.yaml` directly via `terminal`. |
| `bbernhard/signal-cli-rest-api` 404 on health check | **This Docker image is API-incompatible with Hermes.** Hermes expects SSE at `/api/v1/events` and health check at `/api/v1/check` (native signal-cli daemon HTTP mode). bbernhard exposes REST at `/v2/send` and WebSocket at `/v1/receive/{number}` — completely different endpoints. Known issues: [#31674](https://github.com/NousResearch/hermes-agent/issues/31674), [#32337](https://github.com/NousResearch/hermes-agent/issues/32337). **Fix:** use `ghcr.io/asamk/signal-cli` (native daemon, TCP JSON-RPC) + `ghcr.io/gjcourt/signal-bridge` (translates to SSE+JSON-RPC Hermes expects). See `references/signal-setup-architecture.md` for the correct Docker setup. |
| TTS fails every voice message: `output_path targets a protected credential or system path: /tmp/hermes_voice/` | `voice.auto_tts: true` in config.yaml causes Hermes to auto-generate voice replies, but the TTS output path `/tmp/hermes_voice/` is blocked by the security scanner. Every voice message triggers a TTS attempt → fail → retry/timeout → delayed text response. **Fix:** either disable `auto_tts` (`hermes config set voice.auto_tts false`) or the user must patch the TTS output path in config to a non-protected directory. This is NOT a transcription (STT) issue — the STT works fine, the delay comes from the failing TTS reply attempt. |

---

## Reference files

| File | Content |
|------|---------|
| `references/signal-setup-architecture.md` | Correct Signal setup for Hermes: signal-cli + signal-bridge Docker architecture. Documents why bbernhard/signal-cli-rest-api is incompatible, the correct ghcr.io/asamk/signal-cli + ghcr.io/gjcourt/signal-bridge stack, Docker networking pitfalls, and the secret redactor blocking phone numbers. |

## 6. Adding a new diagnostic step

To extend this skill when a new failure scenario is discovered, do the following:

1. Paste a short header and a concise description.
2. Add an example of the log or error text.
3. Provide a snippet of the relevant command or config that fixed it.
4. Copy the style of the last section.

Do NOT add user‑specific data (like a token value). Use placeholders.

---

## 7. Appendices

### 7.1 Key log transformer script

```python
# transform_logs.py
import json
import sys
for line in sys.stdin:
    entry = json.loads(line)
    if entry.get("level") == "ERROR":
        print(entry.get("timestamp"), entry.get("message"), sep=" | ")
```

Usage: `python transform_logs.py <$HOME/.hermes/logs/default.log >errors.log`

### 7.2 Snapshot template

```yaml
# snapshot-20260721_1015.yaml
prompt: |
  ...
parameters: {
  "user": "...",
  "assistant": "...
}
output: |
  ...
```

---

## License

MIT – copy, modify and redistribute freely.
