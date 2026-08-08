import json, urllib.request, base64, time, sys

API_KEY = "${MISTRAL_API_KEY}"
TOKEN = "${PAPERLESS_TOKEN}"
BASE = "https://paperless.jefe.al/api"

def api_get(path):
    req = urllib.request.Request(f'{BASE}/{path}', headers={'Authorization': 'Token ' + TOKEN})
    return json.loads(urllib.request.urlopen(req).read().decode())

def api_post(path, data, content_type='application/json'):
    body = json.dumps(data).encode() if content_type == 'application/json' else data
    req = urllib.request.Request(f'{BASE}/{path}', data=body,
        headers={'Authorization': 'Token ' + TOKEN, 'Content-Type': content_type}, method='POST')
    return json.loads(urllib.request.urlopen(req).read().decode())

def api_patch(path, data):
    req = urllib.request.Request(f'{BASE}/{path}', data=json.dumps(data).encode(),
        headers={'Authorization': 'Token ' + TOKEN, 'Content-Type': 'application/json'}, method='PATCH')
    return json.loads(urllib.request.urlopen(req).read().decode())

def api_get_raw(path):
    req = urllib.request.Request(f'{BASE}/{path}', headers={'Authorization': 'Token ' + TOKEN})
    return urllib.request.urlopen(req).read()

def mistral_ocr(file_bytes, mime_type):
    b64 = base64.b64encode(file_bytes).decode()
    if mime_type == 'application/pdf':
        payload = {'model': 'mistral-ocr-latest', 'document': {'type': 'document_url', 'document_url': f'data:application/pdf;base64,{b64}'}}
    else:
        payload = {'model': 'mistral-ocr-latest', 'document': {'type': 'image_url', 'image_url': {'url': f'data:{mime_type};base64,{b64}'}}}
    req = urllib.request.Request('https://api.mistral.ai/v1/ocr',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'})
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read().decode())
    return '\n\n---\n\n'.join(p['markdown'] for p in data['pages'])

def mistral_classify(ocr_markdown, types_list, correspondents_list):
    prompt = f"""Tu es un assistant intelligent qui analyse et classe des documents administratifs.

On te donne le texte OCR d'un document. Tu dois:
1. Extraire TOUTES les informations visibles (dates, noms, heures, montants, etc.)
2. Déterminer le TYPE de document (parmi les types existants ci-dessous, ou en proposer un nouveau)
3. Déterminer le CORRESPONDANT (qui a émis ce document - parmi les existants ci-dessous, ou en proposer un nouveau)
4. Déterminer à QUI appartient ce document (jefe, pere, mere, autre)
5. Proposer un titre court et descriptif pour le document

Types de documents existants dans Paperless:
{json.dumps(types_list, ensure_ascii=False)}

Correspondants existants dans Paperless:
{json.dumps(correspondents_list, ensure_ascii=False)}

Règles:
- Si le type existe déjà (insensible à la casse), utilise-le. Sinon, propose un nouveau type.
- Si le correspondant existe déjà (insensible à la casse), utilise-le. Sinon, propose-en un nouveau.
- Sois intelligent face à des documents inédits. Devine le type et le correspondant logiques.
- Le titre doit être court et descriptif (ex: "Bulletin de salaire janvier 2026", "Facture EDF mars 2026")

Réponds UNIQUEMENT en JSON:
{{"type_document":"string","correspondant":"string","proprietaire":"jefe|pere|mere|autre","titre":"string","donnees_extraites":{{"date":"string ou null","operateur":"string ou null","client":"string ou null","activites":["liste"],"heures":[{{"label":"string","valeur":"string"}}],"durees":[{{"label":"string","valeur":"string"}}],"lieux":["liste"],"montants":[{{"label":"string","valeur":"string"}}],"notes":"string ou null"}}}}"""

    payload = {
        'model': 'mistral-small-latest',
        'messages': [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': 'Voici le texte OCR à analyser:\n' + ocr_markdown[:5000]}
        ],
        'temperature': 0.1,
        'response_format': {'type': 'json_object'}
    }
    req = urllib.request.Request('https://api.mistral.ai/v1/chat/completions',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'})
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    return json.loads(data['choices'][0]['message']['content'])

def find_or_create_type(name, type_map):
    key = name.lower().strip()
    if key in type_map:
        return type_map[key], False
    new = api_post('document_types/', {'name': name.strip()})
    type_map[new['name'].lower()] = new['id']
    type_map[new['name']] = new['id']
    return new['id'], True

def find_or_create_corr(name, corr_map):
    key = name.lower().strip()
    if key in corr_map:
        return corr_map[key], False
    new = api_post('correspondents/', {'name': name.strip()})
    corr_map[new['name'].lower()] = new['id']
    corr_map[new['name']] = new['id']
    return new['id'], True

# 1. Build lookup maps
types = api_get('document_types/?page_size=100')
corrs = api_get('correspondents/?page_size=100')
tags = api_get('tags/?page_size=100')

type_map = {}
for t in types['results']:
    type_map[t['name'].lower()] = t['id']
    type_map[t['name']] = t['id']
types_list = [t['name'] for t in types['results']]

corr_map = {}
for c in corrs['results']:
    corr_map[c['name'].lower()] = c['id']
    corr_map[c['name']] = c['id']
correspondents_list = [c['name'] for c in corrs['results']]

tag_map = {}
for t in tags['results']:
    tag_map[t['name']] = t['id']
    tag_map[t['name'].lower()] = t['id']

# Get tag IDs
tag_traiter = tag_map.get('statut/a-traiter')
tag_archive = tag_map.get('statut/archivé')

# 2. Get documents with statut/a-traiter
docs = api_get('documents/?tags__id__in=24&page_size=100')
total = docs['count']
print(f'=== {total} documents à traiter ===\n')

results = []
for i, doc in enumerate(docs['results']):
    doc_id = doc['id']
    title = doc['title']
    print(f'[{i+1}/{total}] doc {doc_id}: {title}')
    sys.stdout.flush()
    
    try:
        # Download original file
        file_data = api_get_raw(f'documents/{doc_id}/download/')
        
        # Detect mime type from first bytes
        if file_data[:4] == b'%PDF':
            mime = 'application/pdf'
        elif file_data[:3] == b'\xff\xd8\xff':
            mime = 'image/jpeg'
        elif file_data[:8] == b'\x89PNG\r\n\x1a\n':
            mime = 'image/png'
        else:
            mime = 'application/octet-stream'
        
        # OCR
        ocr_md = mistral_ocr(file_data, mime)
        print(f'  OCR: {len(ocr_md)} chars')
        
        # Classify
        result = mistral_classify(ocr_md, types_list, correspondents_list)
        print(f'  Type: {result["type_document"]}')
        print(f'  Correspondant: {result["correspondant"]}')
        print(f'  Titre: {result["titre"]}')
        
        # Find or create type/correspondent
        type_id, type_created = find_or_create_type(result['type_document'], type_map)
        corr_id, corr_created = find_or_create_corr(result['correspondant'], corr_map)
        
        if type_created:
            print(f'  🆕 Type créé: {result["type_document"]} (id={type_id})')
        if corr_created:
            print(f'  🆕 Correspondant créé: {result["correspondant"]} (id={corr_id})')
        
        # Update document in Paperless
        # Remove "a-traiter" tag, add "archivé" tag, keep other tags
        current_tags = doc.get('tags', [])
        new_tags = [t for t in current_tags if t != tag_traiter]
        if tag_archive:
            new_tags.append(tag_archive)
        
        api_patch(f'documents/{doc_id}/', {
            'title': result['titre'],
            'document_type': type_id,
            'correspondent': corr_id,
            'tags': new_tags
        })
        print(f'  ✅ Mis à jour dans Paperless')
        
        results.append({'id': doc_id, 'old_title': title, 'new_title': result['titre'],
                       'type': result['type_document'], 'correspondant': result['correspondant'],
                       'status': 'ok'})
        
    except Exception as e:
        print(f'  ❌ Erreur: {str(e)[:200]}')
        results.append({'id': doc_id, 'old_title': title, 'status': 'error', 'error': str(e)[:200]})
    
    print()
    time.sleep(1)  # Rate limit

# Summary
print(f'\n=== RÉCAPITULATIF ===')
ok = sum(1 for r in results if r['status'] == 'ok')
err = sum(1 for r in results if r['status'] == 'error')
print(f'Réussis: {ok}/{total}')
print(f'Échoués: {err}/{total}')
if err:
    print('\nÉchecs:')
    for r in results:
        if r['status'] == 'error':
            print(f'  doc {r["id"]}: {r.get("error","?")}')