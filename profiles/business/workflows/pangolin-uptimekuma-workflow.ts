import { workflow, node, trigger, ifElse, splitInBatches, nextBatch, merge, expr, newCredential } from '@n8n/workflow-sdk';

// ===== CREDENTIALS =====
const pangolinCred = newCredential('Pangolin api key');
const uptimeKumaCred = newCredential('Uptime Kuma API');
const discordCred = newCredential('Discord Bot Test AI');

// ===== 1. SCHEDULE TRIGGER =====
const scheduleTrigger = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: 'Toutes les heures',
    parameters: {
      rule: {
        interval: [{
          field: 'hours',
          hoursInterval: 1,
          triggerAtMinute: 0
        }]
      }
    }
  }
});

// ===== 2. FETCH PANGOLIN RESOURCES =====
const fetchPangolin = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'GET Pangolin resources',
    parameters: {
      method: 'GET',
      url: 'https://api.jefe.ovh/api/org/jorganisation/resources',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBearerAuth',
      sendQuery: true,
      specifyQuery: 'keypair',
      queryParameters: {
        parameters: [
          { name: 'pageSize', value: '100' }
        ]
      },
      options: {
        response: {
          response: {
            responseFormat: 'json'
          }
        }
      }
    },
    credentials: { httpBearerAuth: pangolinCred }
  }
});

// ===== 3. FETCH UPTIME KUMA MONITORS =====
const fetchUptimeKuma = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'GET Uptime Kuma monitors',
    parameters: {
      method: 'GET',
      url: 'https://status.losgalactique.fr/monitor/list',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBasicAuth',
      options: {
        response: {
          response: {
            responseFormat: 'json'
          }
        }
      }
    },
    credentials: { httpBasicAuth: uptimeKumaCred }
  }
});

// ===== 4. MERGE BOTH STREAMS =====
const mergeStreams = merge({
  version: 3.2,
  config: {
    name: 'Merge streams',
    parameters: { mode: 'append' }
  }
});

// ===== 5. CODE: COMPARE & FIND NEW =====
const findNewResources = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Trouver nouveaux sites',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'pythonNative',
      pythonCode: `
# Les inputs arrivent mergées (append) - items[0] = Pangolin, items[1] = Uptime Kuma
pangolin_data = items[0] if len(items) > 0 else {}
uptime_data = items[1] if len(items) > 1 else []

# Extraire les resources HTTP de Pangolin (celles avec un fullDomain)
pangolin_resources = []
if isinstance(pangolin_data, dict) and 'json' in pangolin_data:
    body = pangolin_data['json']
    resources = body.get('data', {}).get('resources', []) if isinstance(body, dict) else []
    for r in resources:
        full_domain = r.get('fullDomain')
        name = r.get('name', '')
        enabled = r.get('enabled', False)
        http = r.get('http', False)
        health = r.get('health', 'unknown')
        if full_domain and enabled and http:
            pangolin_resources.append({
                'name': name,
                'domain': full_domain,
                'url': f"https://{full_domain}",
                'health': health
            })

# Extraire les noms des monitors Uptime Kuma existants
existing_names = set()
if isinstance(uptime_data, dict) and 'json' in uptime_data:
    monitors = uptime_data['json']
    if isinstance(monitors, list):
        for m in monitors:
            existing_names.add(m.get('name', ''))

# Filtrer les nouveaux
new_resources = [r for r in pangolin_resources if r['name'] not in existing_names]

# Output
result = []
for r in new_resources:
    result.append({'json': r})

if not result:
    result.append({'json': {'_note': 'Aucun nouveau site trouve'}})

return result
`
    }
  }
});

// ===== 6. IF: check if we have new resources =====
const hasNew = ifElse({
  version: 2.3,
  config: {
    name: 'Nouveaux sites ?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json._note }}'), operator: { type: 'string', operation: 'isEmpty' } }
        ],
        combinator: 'and'
      }
    }
  }
});

// ===== 7. SPLIT IN BATCHES =====
const batchNew = splitInBatches({
  version: 3,
  config: {
    name: 'Creer monitors',
    parameters: { batchSize: 1 }
  }
});

// ===== 8. CREATE UPTIME KUMA MONITOR =====
const createMonitor = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.3,
  config: {
    name: 'POST create monitor',
    parameters: {
      method: 'POST',
      url: 'https://status.losgalactique.fr/monitor',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBasicAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{\n  "name": "{{ $json.name }}",\n  "type": "http",\n  "url": "{{ $json.url }}",\n  "method": "GET",\n  "interval": 60,\n  "retryInterval": 60,\n  "maxretries": 3\n}'),
      options: {
        response: {
          response: { responseFormat: 'json' }
        }
      }
    },
    credentials: { httpBasicAuth: uptimeKumaCred }
  }
});

// ===== 9. DISCORD NOTIFICATION =====
const notifyDiscord = node({
  type: 'n8n-nodes-base.discord',
  version: 2,
  config: {
    name: 'Notifier Discord',
    parameters: {
      resource: 'message',
      operation: 'send',
      authentication: 'botToken',
      guildId: { __rl: true, mode: 'list', value: '' },
      sendTo: 'channel',
      channelId: { __rl: true, mode: 'list', value: '' },
      content: expr('✅ **Nouveau site surveillé**\\n**{{ $json.name }}** : {{ $json.url }}')
    },
    credentials: { discordBotApi: discordCred }
  }
});

// ===== BUILD WORKFLOW =====
export default workflow('pangolin-uptimekuma-sync', 'Pangolin → Uptime Kuma Auto-Surveillance')
  .add(scheduleTrigger)
  .to(fetchPangolin.to(mergeStreams.input(0)))
  .add(scheduleTrigger)
  .to(fetchUptimeKuma.to(mergeStreams.input(1)))
  .add(mergeStreams)
  .to(findNewResources)
  .to(hasNew
    .onTrue(batchNew
      .onEachBatch(createMonitor.to(notifyDiscord).to(nextBatch(batchNew)))
    )
  );
