import json

with open('/opt/data/n8n_wf_current.json') as f:
    wf = json.load(f)

# 1. Update the Decode Base64 node to also extract the file extension from the binary data
# and set a proper filename with extension
for n in wf['nodes']:
    if n['name'] == 'Decode Base64':
        n['parameters']['jsCode'] = """const input = $input.first().json;
const body = input.body || input;

const base64Data = body.file;
const filename = body.filename || 'document';
const source = body.source || 'auto';
const target = body.target || 'fr';

if (!base64Data) {
  throw new Error('No file data provided. Expected base64-encoded file in "file" field.');
}

const fileBuffer = Buffer.from(base64Data, 'base64');

// Try to detect file type from magic bytes
let ext = 'txt';
const magic = fileBuffer.slice(0, 5).toString('hex');
if (fileBuffer.length > 4 && magic.startsWith('25504446')) ext = 'pdf';
else if (fileBuffer.length > 2 && magic.startsWith('504b')) ext = 'docx';
else if (fileBuffer.length > 8 && fileBuffer.slice(0, 8).toString('hex').startsWith('d0cf11e0a1b1')) ext = 'doc';

// Use original filename if it has an extension, otherwise append detected ext
let finalName = filename;
if (!filename.match(/\\.(pdf|docx|doc|txt|odt|odp|pptx|epub|html|srt)$/i)) {
  finalName = filename + '.' + ext;
}

return [{
  json: {
    filename: finalName,
    originalFilename: filename,
    source: source,
    target: target,
    detectedExt: ext
  },
  binary: {
    data: {
      data: fileBuffer,
      mimeType: 'application/octet-stream',
      fileName: finalName
    }
  }
}];"""

# 2. Update the Translate File HTTP Request to use the filename from json
for n in wf['nodes']:
    if n['name'] == 'Translate File':
        n['parameters']['bodyParameters'] = {
            "parameters": [
                {"name": "source", "value": "={{ $json.source }}"},
                {"name": "target", "value": "={{ $json.target }}"},
                {"name": "api_key", "value": "53e04e31-de93-4b49-a0e4-891b1806fc8d"},
                {"name": "file", "parameterType": "formBinaryData", "inputDataFieldName": "data"}
            ]
        }

# 3. Replace the Download/Encode/Respond chain with a single Code node that handles errors
# Remove Download Translated File node and replace Encode Response
new_nodes = []
for n in wf['nodes']:
    if n['name'] == 'Download Translated File':
        # Skip this node - we'll handle download in the Code node
        continue
    if n['name'] == 'Encode Response':
        n = {
            'parameters': {
                'jsCode': """const translateResponse = $('Translate File').item.json;
const error = translateResponse.error;

if (error) {
  return [{ json: { success: false, error: 'LibreTranslate: ' + error, translatedText: '', downloadUrl: '' } }];
}

const fileUrl = translateResponse.translatedFileUrl || '';
if (!fileUrl) {
  return [{ json: { success: false, error: 'No translated file URL received', translatedText: '', downloadUrl: '' } }];
}

// Download the translated file
try {
  const response = await this.helpers.httpRequest({
    method: 'GET',
    url: fileUrl,
    timeout: 60000,
    returnFullResponse: true,
  });
  const text = typeof response === 'string' ? response : (response.body || '');
  const filename = fileUrl.split('/').pop() || 'translated.txt';
  return [{ json: { success: true, filename: filename, translatedText: text, downloadUrl: fileUrl } }];
} catch (e) {
  return [{ json: { success: false, error: 'Download failed: ' + e.message, translatedText: '', downloadUrl: fileUrl } }];
}"""
            },
            'id': 'encode-response',
            'name': 'Encode Response',
            'type': 'n8n-nodes-base.code',
            'typeVersion': 2,
            'position': [660, 0]
        }
    new_nodes.append(n)
wf['nodes'] = new_nodes

# 4. Update connections - remove Download Translated File references
# Translate File -> Encode Response (direct, no Download node)
connections = wf.get('connections', {})
if 'Translate File' in connections:
    connections['Translate File'] = {'main': [[{'node': 'Encode Response', 'type': 'main', 'index': 0}]]}
if 'Download Translated File' in connections:
    del connections['Download Translated File']
if 'Encode Response' in connections:
    # Keep existing connection to Respond to Webhook
    pass

# 5. Update Respond to Webhook to always return JSON
for n in wf['nodes']:
    if n['name'] == 'Respond to Webhook':
        n['parameters'] = {
            'respondWith': 'json',
            'responseBody': '={{ JSON.stringify({ success: $json.success, filename: $json.filename, translatedText: $json.translatedText, downloadUrl: $json.downloadUrl, error: $json.error }) }}',
            'options': {'responseCode': 200}
        }

# Strip metadata
for field in ['id','versionId','createdAt','updatedAt','active','activeVersionId','triggerCount','shared','tags','sourceWorkflowId','parentFolder','activeVersion','versionCounter','isArchived','pinData','staticData','meta']:
    wf.pop(field, None)
for n in wf['nodes']:
    n.pop('webhookId', None)
wf['description'] = ''
wf['settings'] = {'executionOrder': 'v1', 'availableInMCP': False}

with open('/opt/data/n8n_wf_update.json', 'w') as f:
    json.dump(wf, f)
print('OK - nodes:', [n['name'] for n in wf['nodes']])
print('connections:', list(wf.get('connections',{}).keys()))