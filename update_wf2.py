import json

with open('/opt/data/n8n_wf_current.json') as f:
    wf = json.load(f)

# Update Download to return text instead of file
for n in wf['nodes']:
    if n['name'] == 'Download Translated File':
        n['parameters']['responseFormat'] = 'text'
        n['parameters']['options'] = {'timeout': 60000}

# Replace Encode Response to extract translated text
for i, n in enumerate(wf['nodes']):
    if n['name'] == 'Encode Response':
        wf['nodes'][i] = {
            'parameters': {
                'jsCode': "const item = $input.first();\nconst translatedText = item.json.data || '';\nconst translateResponse = $('Translate File').item.json;\nconst fileUrl = translateResponse.translatedFileUrl || '';\nconst filename = (fileUrl.split('/').pop()) || 'translated.txt';\nreturn [{ json: { success: true, filename: filename, translatedText: translatedText, downloadUrl: fileUrl } }];"
            },
            'id': 'encode-response',
            'name': 'Encode Response',
            'type': 'n8n-nodes-base.code',
            'typeVersion': 2,
            'position': [860, 0]
        }

# Update Respond to Webhook to return JSON with text
for n in wf['nodes']:
    if n['name'] == 'Respond to Webhook':
        n['parameters'] = {
            'respondWith': 'json',
            'responseBody': '={{ JSON.stringify({ success: $json.success, filename: $json.filename, translatedText: $json.translatedText, downloadUrl: $json.downloadUrl, error: $json.error }) }}',
            'options': {'responseCode': 200}
        }

for field in ['id','versionId','createdAt','updatedAt','active','activeVersionId','triggerCount','shared','tags','sourceWorkflowId','parentFolder','activeVersion','versionCounter','isArchived','pinData','staticData','meta']:
    wf.pop(field, None)
for n in wf['nodes']:
    n.pop('webhookId', None)
wf['description'] = ''
wf['settings'] = {'executionOrder': 'v1', 'availableInMCP': False}

with open('/opt/data/n8n_wf_update.json', 'w') as f:
    json.dump(wf, f)
print('OK')