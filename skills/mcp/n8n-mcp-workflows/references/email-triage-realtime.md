# Email Triage Temps Réel — IMAP → Hermes Agent → ntfy

Pattern for real-time email monitoring: IMAP triggers fire on new emails,
Hermes Agent (GLM-5.2) classifies each email, and ntfy sends push
notifications with priority levels (max for urgent, default for normal).

## Architecture

```
IMAP jefe15307 ──┐
                 ├──→ Merge (append) ──→ AI Agent (Hermes) ──→ IF Urgent?
IMAP prendizef59 ┘                                                    ├──→ ntfy 🚨 MAX
                                                                      └──→ ntfy 📧 default
```

## Key Components

### 1. IMAP Trigger Nodes (n8n-nodes-base.emailReadImap v2.1)

One per mailbox. Uses IMAP IDLE for real-time push (not polling).

```javascript
const imapTrigger = trigger({
  type: 'n8n-nodes-base.emailReadImap',
  version: 2.1,
  config: {
    name: 'IMAP account',
    parameters: {
      mailbox: 'INBOX',
      postProcessAction: 'nothing',  // DO NOT use 'read' — see pitfall below
      format: 'simple',              // simple = subject, from, textPlain, date
      downloadAttachments: false,
    },
    credentials: { imap: { id: '<credId>', name: 'IMAP account' } },
  },
});
```

**⚠️ CRITICAL — `postProcessAction` pitfall:** Use `'nothing'`, NOT
`'read'`. With `'read'`, the trigger marks each processed email as
Seen. On the next IDLE notification, the IMAP search for `UNSEEN`
emails skips the newly-arrived email because Gmail may have already
auto-marked it as Seen (especially for self-sent test emails or
emails opened on another device). This causes **silently missed
emails** — the trigger fires but finds nothing to process.

With `'nothing'`, emails stay UNSEEN after processing, and
`trackLastMessageId: true` (default) ensures only genuinely new
emails trigger the workflow. The tradeoff: emails pile up as unread
in the mailbox, but no emails are missed.

**`forceReconnect`:** Reduce to 30 minutes (from default 60) for
better reliability with Gmail's IMAP IDLE timeout behavior.

**IMAP credential creation via REST API:**

```bash
curl -s -X POST http://localhost:5678/api/v1/credentials \
  -H "X-N8N-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"IMAP account","type":"imap","data":{"host":"imap.gmail.com","port":993,"user":"user@gmail.com","password":"app-password"}}'
```

**Pitfall:** The IMAP credential type does NOT accept `ssl` or
`allowSelfSigned` fields. Send only `host`, `port`, `user`, `password`.
Adding extra fields → 400 validation error.

### 2. Merge Node — Combine Multiple Mailboxes

Use `mode: 'append'` to combine emails from multiple IMAP triggers into
a single stream. Each trigger connects to a different input:

```javascript
const mergeEmails = node({
  type: 'n8n-nodes-base.merge',
  version: 3.2,
  config: { name: 'Merge Emails', parameters: { mode: 'append' } },
});

export default workflow('email-triage', 'Email Triage')
  .add(imapJefe).to(mergeEmails.input(0))
  .add(imapPrendizef).to(mergeEmails.input(1))
  .add(mergeEmails).to(aiAgent);
```

### 3. Hermes Agent — Email Classification

The AI Agent receives the merged email and classifies it. Key: use
`promptType: 'define'` with a structured prompt asking for JSON output.

```javascript
const aiAgent = node({
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: 'Hermes Email Triage',
    parameters: {
      promptType: 'define',
      text: expr('Analyse cet email...\nFrom: {{ $json.from }}\nSubject: {{ $json.subject }}\nBody: {{ $json.textPlain }}\n\nRéponds en JSON: {"urgency":"urgent|normal|low","category":"arnaque|important|promo|perso|pro|autre","summary":"...","action":"..."}'),
      hasOutputParser: false,
      options: {
        systemMessage: 'You are Hermes Agent email triage assistant...',
        maxIterations: 1,  // single-pass classification, no tools needed
        enableStreaming: false,
      },
    },
    subnodes: { model: hermesModel },
  },
});
```

**Temperature:** Use `0.3` for classification tasks (low creativity,
consistent results) vs `0.7` for chat.

### 4. IF Node — Route by Urgency

After the Code node parses the JSON, the IF node checks the **parsed**
`urgency` field (not the raw `output` string):

```javascript
const checkUrgent = ifElse({
  version: 2.3,
  config: {
    name: 'Is Urgent?',
    parameters: {
      conditions: {
        options: { caseSensitive: false, typeValidation: 'loose' },
        conditions: [{
          leftValue: expr('{{ $json.urgency }}'),  // parsed field, NOT $json.output
          operator: { type: 'string', operation: 'equals' },  // equals, NOT contains
          rightValue: 'urgent',
        }],
        combinator: 'and',
      },
    },
  },
});
```

**Use `equals` not `contains`:** With the Code node extracting `urgency`
as a clean field, use `equals: 'urgent'`. Using `contains: 'urgent'`
on the raw `$json.output` would match `'urgent'` inside any JSON field
value (e.g. `"action": "Non urgent"`), causing false positives.

### 5. ntfy Notification Nodes (HTTP Request)

ntfy has no dedicated n8n node — use HTTP Request with header auth.

**ntfy credential (httpHeaderAuth type):**

```bash
curl -s -X POST http://localhost:5678/api/v1/credentials \
  -H "X-N8N-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"ntfy","type":"httpHeaderAuth","data":{"name":"Authorization","value":"Bearer <ntfy_token>"}}'
```

**Urgent notification (priority=max) — uses formatted fields:**

```javascript
const ntfyUrgent = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'ntfy Urgent',
    parameters: {
      method: 'POST',
      url: 'https://ntfy.jefe.ovh/hermes-agent-jefe',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'Title', value: expr('{{ $json.title }}') },  // from Code node
          { name: 'Priority', value: 'max' },
          { name: 'Tags', value: 'rotating_light,email,urgent' },
        ],
      },
      sendBody: true,
      contentType: 'raw',
      rawContentType: 'text/plain',
      body: expr('{{ $json.body }}'),  // from Code node
    },
    credentials: { httpHeaderAuth: { id: '<credId>', name: 'ntfy' } },
  },
});
```

**Normal notification:** Same structure but `Priority: 'default'` and
different Title/Tags.

### 6. Credential Assignment via update_workflow

Unlike `httpRequestTool` nodes (which can't have generic credentials
assigned via API — see SKILL.md pitfall), regular `httpRequest` nodes
CAN have credentials assigned via `setNodeCredential`:

```javascript
mcp_n8n_mcp_update_workflow({
  workflowId: '...',
  operations: [
    { type: 'setNodeCredential', nodeName: 'ntfy Urgent',
      credentialKey: 'httpHeaderAuth', credentialId: '<id>', credentialName: 'ntfy' },
    { type: 'setNodeCredential', nodeName: 'IMAP account',
      credentialKey: 'imap', credentialId: '<id>', credentialName: 'IMAP account' },
  ],
});
```

This works for: `httpRequest` (v4.4), `emailReadImap` (v2.1).
This does NOT work for: `httpRequestTool` (the AI tool variant).

## ntfy Priority Levels

| Priority | Value | Behavior |
|----------|-------|----------|
| Max | `max` | Sound + vibration + popup, bypasses DND |
| High | `high` | Sound + vibration |
| Default | `default` | Normal notification |
| Low | `low` | No sound |
| Min | `min` | Hidden |

## Gmail App Passwords

Gmail requires app-specific passwords for IMAP (not regular password).
Enable 2FA → generate at https://myaccount.google.com/apppasswords.

The password is the same for IMAP and SMTP. Store it in:
- Himalaya config (`~/.config/himalaya/config.toml`)
- Hermes `.env` (`EMAIL_PASSWORD`)
- n8n IMAP credential

**When the password is rotated, all three locations must be updated.**
See himalaya skill pitfall about divergent app password stores.

## Code Node — Format JSON for ntfy (CRITICAL)

The AI Agent outputs raw JSON like:
```json
{"urgency":"low","category":"perso","summary":"...","action":"..."}
```

Sending this directly to ntfy produces an **unreadable notification**
with the raw JSON as both title and body. The user will see garbled
text instead of a clear message.

**Always add a Code node between the AI Agent and the IF/ntfy nodes**
to parse the JSON and format human-readable title and body.

**⚠️ LLMs wrap JSON in markdown fences!** The AI Agent (especially
`gpt-oss-20b`) often returns output like:
```
```json
{"urgency":"low","category":"perso","summary":"...","action":"..."}
```
```
A naive `JSON.parse(raw)` FAILS on this because of the ` ```json `
prefix and ` ``` ` suffix. The Code node MUST strip markdown fences
before parsing:

```javascript
// Code node (runOnceForEachItem mode)
const raw = ($json.output || '').trim();

// Strip markdown code fences: ```json\n...\n``` or ```\n...\n```
let clean = raw;
const fenceMatch = raw.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
if (fenceMatch) {
  clean = fenceMatch[1].trim();
} else if (clean.startsWith('```')) {
  clean = clean.replace(/^```(?:json)?/, '').replace(/```$/, '').trim();
}
// Fallback: extract JSON object from surrounding text
const jsonObjMatch = clean.match(/\{[\s\S]*\}/);
if (jsonObjMatch && !clean.startsWith('{')) {
  clean = jsonObjMatch[0];
}

let parsed = {};
try { parsed = JSON.parse(clean); } catch(e) {
  parsed = { urgency: 'normal', category: 'autre', summary: raw, action: '' };
}

const urgencyEmoji = { urgent: '🚨', normal: '📧', low: '📥' };
const catLabel = { arnaque: 'Arnaque', important: 'Important',
  promo: 'Promo', perso: 'Perso', pro: 'Pro', autre: 'Autre' };

const emoji = urgencyEmoji[parsed.urgency] || '📧';
const u = parsed.urgency || 'normal';
const cat = catLabel[parsed.category] || parsed.category || 'Autre';

const title = emoji + ' ' + cat;
const body = (parsed.summary || '')
  + (parsed.action && parsed.action.trim() ? '\n→ ' + parsed.action.trim() : '');

return { json: { title, body, urgency: u } };
```

**Key changes from naive version:**
1. Regex `/```(?:json)?\s*([\s\S]*?)\s*```/` extracts JSON from fenced blocks
2. Fallback regex `/\{[\s\S]*\}/` finds JSON object in mixed text
3. Title simplified to `emoji + category label` (e.g. `📥 Perso`) — no
   urgency level in title (cleaner on phone screens)
4. Body is plain text only: summary + `→ action`
5. Use unicode escapes (`\ud83d\udce7`) for emoji in n8n Code nodes if
   direct emoji characters cause encoding issues in the JSCode field

Then the IF node checks `$json.urgency` (parsed field, not raw output)
and the ntfy nodes use `{{ $json.title }}` and `{{ $json.body }}`.

**Updated flow:**
```
Hermes Email Triage → Format Message (Code) → Is Urgent? → ntfy
```

**Connection update via API:** When inserting a Code node between
existing nodes, the operation sequence matters:
1. `addNode` (the Code node)
2. `removeConnection` (old: Agent → IF)
3. `addConnection` (Agent → Code)
4. `addConnection` (Code → IF)
5. `updateNodeParameters` (IF condition: check `$json.urgency` not `$json.output`)
6. `updateNodeParameters` (ntfy nodes: use `$json.title` and `$json.body`)

If the remove/add connection operations fail because the node hasn't
been added yet, reorder so `addNode` comes first.

## Model Selection for Email Triage

Use a lightweight model for classification tasks to save resources:

| Model | Use case | Tokens | Speed |
|-------|----------|--------|-------|
| `gpt-oss-20b` | Email classification, triage | ~29K prompt | ~2.5s |
| `glm-5.2` | Chat, complex reasoning | ~29K prompt | ~2-4s |
| `deepseek-v4-flash` | Long context (1M), fast | varies | fast |

For email triage (single-pass JSON classification, no tools), `gpt-oss-20b`
is the best choice — sufficient intelligence, lower resource usage.

Switch model via `updateNodeParameters` on the model node:
```javascript
{ type: 'updateNodeParameters', nodeName: 'Hermes GLM-5.2',
  parameters: { model: { __rl: true, mode: 'id', value: 'gpt-oss-20b' } } }
```

## IMAP IDLE — Real-Time Push (Not Polling)

The n8n `emailReadImap` trigger uses IMAP IDLE for real-time push
notifications. When the workflow is published/active, n8n opens an
IMAP IDLE connection and receives emails **instantly** — not on a
polling interval.

- `forceReconnect` (default 60 min) only forces periodic reconnection
  to prevent silent IDLE drops
- `trackLastMessageId` (default true) ensures only new emails trigger
- In testing (2026-07-25): mail received at 17:28:09 → workflow
  triggered at 17:28:25 → ntfy delivered at 17:28:28 = **3 seconds
  end-to-end**

## DISCONNECTED_NODE Warnings

IMAP trigger nodes will show `DISCONNECTED_NODE` warnings in the
validation output. These are **harmless** — IMAP triggers are source
nodes with no upstream input. The warnings are an artifact of the SDK
validator expecting all nodes to have an input connection.

## Available Models on Ollama Cloud (LiteLLM)

Query the model list:
```bash
source /opt/data/.env; curl -s http://localhost:4000/v1/models \
  -H "Authorization: Bearer $OLLAMA_API_KEY"
```

Known models (as of 2026-07-25):
- `glm-5.2` — general purpose
- `minimax-m3` — general purpose
- `gemma4-vision` — vision/multimodal
- `gpt-oss-20b` — lightweight (20B params), good for classification
- `deepseek-v4-flash` — fast, 1M context
- `local-aux` — auxiliary tasks