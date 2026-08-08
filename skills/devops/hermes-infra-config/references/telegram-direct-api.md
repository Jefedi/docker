# Send Telegram Messages Directly via Bot API

## When to use

When you need to send a Telegram message from a session that doesn't have
the `messaging` toolset loaded (e.g. WebUI session, CLI session without
messaging tools, cron job with restricted toolsets). This is the fallback
pattern — prefer the native `send_message` tool when available.

## Prerequisites

- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_HOME_CHANNEL` set in `/opt/data/.env`
  (or the profile's `.env`)
- The bot must be started and authorized for the target chat

## Procedure

### 1. Source the credentials

```bash
source /opt/data/.env
```

**Pitfall:** `.env` may contain lines that produce shell errors (e.g.
`Vault: command not found`, `dztg: command not found`) from unrelated
entries. These errors are harmless — the Telegram variables still load
correctly. Don't abort on these errors.

Alternatively, extract just the needed vars without sourcing:

```bash
TOKEN=$(grep '^TELEGRAM_BOT_TOKEN=' /opt/data/.env | cut -d= -f2)
CHAT_ID=$(grep '^TELEGRAM_HOME_CHANNEL=' /opt/data/.env | cut -d= -f2)
```

### 2. Send the message

```bash
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": ${CHAT_ID}, \"text\": \"Your message here.\"}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('OK' if r.get('ok') else f'ERROR: {r}')"
```

### 3. Verify

The response JSON contains `ok: true` on success. The `python3` one-liner
above extracts just the status. For debugging, pipe to `jq .` instead.

## Finding the credentials

| Variable | Location | Example |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | `/opt/data/.env` (uncommented line) | `8666533764:AAE...` |
| `TELEGRAM_HOME_CHANNEL` | `/opt/data/.env` (uncommented line) | `7509874421` |
| `TELEGRAM_CRON_THREAD_ID` | `/opt/data/.env` (optional, for forum topics) | topic ID |

Check which vars are set (uncommented):
```bash
grep -i 'TELEGRAM_BOT_TOKEN\|TELEGRAM_HOME_CHANNEL' /opt/data/.env | grep -v '^#'
```

## Other Telegram Bot API endpoints

Same pattern with different method names:
- `sendPhoto` — send an image (use `multipart/form-data` with `-F` options)
- `sendDocument` — send a file
- `sendMessage` with `parse_mode: "MarkdownV2"` or `"HTML"` — formatted text

API reference: https://core.telegram.org/bots/api#sendmessage

## Security notes

- The bot token is a secret — avoid echoing it to logs or terminal output
- Hermes redacts `sk-*` patterns but may not redact Telegram tokens — be
  careful with `set -x` or verbose curl output
- The `TELEGRAM_HOME_CHANNEL` is the user's personal chat ID — don't share
  it in outputs destined for other platforms