# n8n Telegram Node — Silent Failure Debugging

## Problem Pattern

A document OCR workflow (Telegram → Mistral OCR → extraction → Telegram recap) runs with `status: "success"` but the user receives **nothing** on Telegram. No error in n8n logs. No failed execution.

## Root Causes Found (in order of discovery)

### 1. `replyMarkup: "inlineKeyboard"` without buttons
- **Symptom**: Execution succeeds, no message delivered
- **Cause**: Telegram API silently rejects messages with an empty inline keyboard
- **Fix**: Remove `replyMarkup` field entirely from the Telegram node
- **n8n MCP gotcha**: `setNodeParameter` with value `""` does NOT clear the field. Must `removeNode` + `addNode` to recreate the node clean.

### 2. `resource: "chat"` instead of `resource: "message"`
- **Symptom**: Execution succeeds (~23s), no message delivered
- **Cause**: The `chat` resource only has operations: get, administrators, member, leave, setDescription, setTitle. **None of these send a message.** The default operation (get) fetches chat info and returns success.
- **Fix**: Set `resource: "message"` AND `operation: "sendMessage"` together
- **How to verify**: Use `mcp__n8n_mcp__search_nodes` with `["telegram send message"]` to see the correct resource/operation discriminators

### 3. IF filter rejects PDFs (<300ms "success")
- **Symptom**: Execution succeeds in <300ms, no processing
- **Cause**: `Has Photo?` IF node checks `$json.message.photo` only. PDFs arrive as `message.document`, not `message.photo`. The IF evaluates to false, workflow ends immediately.
- **Fix**: Change IF conditions to OR: `message.photo` notEmpty OR `message.document` notEmpty

### 4. Mistral OCR rejects PDFs with 422
- **Symptom**: Execution errors with HTTP 422
- **Cause**: PDFs sent with `type: "image_url"` → 422 "Image content must be a URL or base64 encoded image". PDFs sent with `type: "file_url"` → 422 "Input should be 'document_url'"
- **Fix**: Use `type: "document_url"` with `document_url` field (flat string, NOT nested object like `image_url.url`)

## Correct Telegram sendMessage Node Config

```json
{
  "resource": "message",
  "operation": "sendMessage",
  "chatId": "={{ $('Telegram Trigger').item.json.message.chat.id }}",
  "text": "={{ $json.recap_message }}",
  "appendAttribution": false
}
```

Do NOT include `replyMarkup` unless you have actual buttons defined.

## Correct IF Filter for Photos + Documents

```
conditions.combinator: "or"
conditions.conditions: [
  { leftValue: "={{ $json.message.photo }}", operator: { type: "array", operation: "notEmpty" } },
  { leftValue: "={{ $json.message.document }}", operator: { type: "object", operation: "notEmpty" } }
]
```

## Debugging Checklist

1. Check execution duration — if <300ms, the IF rejected the input
2. Check `docker logs n8n-n8n-1 --since=2m` for HTTP errors (400, 422)
3. Check the Telegram node's `resource` and `operation` — must be `message` + `sendMessage`
4. Check if `replyMarkup` is set but has no buttons — remove it
5. Check the Mistral OCR payload format — PDFs need `document_url`, images need `image_url`
6. Check binary key name — `Object.keys(item.binary)[0]` instead of hardcoded `'data'`