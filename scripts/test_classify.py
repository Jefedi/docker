import json, base64, urllib.request

API_KEY = "${MISTRAL_API_KEY}"
TOKEN = "${PAPERLESS_TOKEN}"
BASE = "https://paperless.jefe.al/api"

# Step 1: Get existing document types and correspondents from Paperless
def get_paperless_options():
    options = {}
    for endpoint in ['document_types', 'correspondents', 'tags']:
        req = urllib.request.Request(f'{BASE}/{endpoint}/?page_size=100', 
                                     headers={'Authorization': 'Token ' + TOKEN})
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode())
        items = {item['name']: item['id'] for item in data.get('results', [])}
        options[endpoint] = items
    return options

paperless = get_paperless_options()

# Step 2: OCR the test image
img_path = "/opt/data/cache/images/img_27485f0c6317.jpg"
with open(img_path, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

ocr_payload = {
    'model': 'mistral-ocr-latest',
    'document': {
        'type': 'image_url',
        'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}
    }
}
req = urllib.request.Request('https://api.mistral.ai/v1/ocr',
    data=json.dumps(ocr_payload).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'})
resp = urllib.request.urlopen(req, timeout=30)
ocr_data = json.loads(resp.read().decode())
ocr_markdown = ocr_data['pages'][0]['markdown']

# Step 3: LLM analysis - classify the document
# Build context with existing Paperless options
existing_types = list(paperless['document_types'].keys())
existing_correspondents = list(paperless['correspondents'].keys())
existing_tags = list(paperless['tags'].keys())

classify_prompt = f"""Tu es un assistant intelligent qui analyse et classe des documents administratifs.

On te donne le texte OCR d'un document. Tu dois:
1. Extraire TOUTES les informations visibles (dates, noms, heures, montants, etc.)
2. Déterminer le TYPE de document (parmi les types existants ci-dessous, ou en proposer un nouveau)
3. Déterminer le CORRESPONDANT (qui a émis ce document - parmi les correspondants existants ci-dessous, ou en proposer un nouveau)
4. Déterminer à QUI appartient ce document (jefe, père, mère, autre)
5. Proposer un titre court et descriptif pour le document

Types de documents existants dans Paperless:
{json.dumps(existing_types, ensure_ascii=False)}

Correspondants existants dans Paperless:
{json.dumps(existing_correspondents, ensure_ascii=False)}

Tags existants dans Paperless:
{json.dumps(existing_tags, ensure_ascii=False)}

Règles:
- Si le type de document existe déjà dans la liste, utilise-le. Sinon, propose un nouveau type.
- Si le correspondant existe déjà, utilise-le. Sinon, propose-en un nouveau.
- Sois intelligent face à des documents inédits. Devine le type et le correspondant logiques.
- Le titre doit être court et descriptif (ex: "Bulletin de salaire janvier 2026", "Facture EDF mars 2026")
- Pour les feuilles d'heures journalières, inclure la date dans le titre.

Réponds UNIQUEMENT en JSON:
{{
  "type_document": "nom du type (existant ou nouveau)",
  "correspondant": "nom du correspondant (existant ou nouveau)",
  "proprietaire": "jefe|pere|mere|autre",
  "titre": "titre court et descriptif",
  "donnees_extraites": {{
    "date": "string ou null",
    "operateur": "string ou null",
    "client": "string ou null",
    "activites": ["liste"],
    "heures": [{{"label": "string", "valeur": "string"}}],
    "durees": [{{"label": "string", "valeur": "string"}}],
    "lieux": ["liste"],
    "montants": [{{"label": "string", "valeur": "string"}}],
    "notes": "string ou null"
  }}
}}"""

payload = {
    'model': 'mistral-small-latest',
    'messages': [
        {'role': 'system', 'content': classify_prompt},
        {'role': 'user', 'content': 'Voici le texte OCR à analyser:\n' + ocr_markdown}
    ],
    'temperature': 0.1,
    'response_format': {'type': 'json_object'}
}

req = urllib.request.Request('https://api.mistral.ai/v1/chat/completions',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'})
resp = urllib.request.urlopen(req, timeout=30)
llm_data = json.loads(resp.read().decode())
content = llm_data['choices'][0]['message']['content']
result = json.loads(content)

print("=== RÉSULTAT LLM ===")
print(json.dumps(result, indent=2, ensure_ascii=False))

# Step 4: Check if document type exists, create if not
doc_type_name = result['type_document']
if doc_type_name in paperless['document_types']:
    print(f"\n✅ Type '{doc_type_name}' existe (id={paperless['document_types'][doc_type_name]})")
else:
    print(f"\n🆕 Type '{doc_type_name}' n'existe pas - création...")
    create_payload = json.dumps({"name": doc_type_name}).encode()
    req = urllib.request.Request(f'{BASE}/document_types/',
        data=create_payload,
        headers={'Authorization': 'Token ' + TOKEN, 'Content-Type': 'application/json'},
        method='POST')
    resp = urllib.request.urlopen(req)
    new_type = json.loads(resp.read().decode())
    print(f"   Créé: id={new_type['id']}")
    paperless['document_types'][doc_type_name] = new_type['id']

# Step 5: Check if correspondent exists, create if not
corr_name = result['correspondant']
if corr_name in paperless['correspondents']:
    print(f"✅ Correspondant '{corr_name}' existe (id={paperless['correspondents'][corr_name]})")
else:
    print(f"🆕 Correspondant '{corr_name}' n'existe pas - création...")
    create_payload = json.dumps({"name": corr_name}).encode()
    req = urllib.request.Request(f'{BASE}/correspondents/',
        data=create_payload,
        headers={'Authorization': 'Token ' + TOKEN, 'Content-Type': 'application/json'},
        method='POST')
    resp = urllib.request.urlopen(req)
    new_corr = json.loads(resp.read().decode())
    print(f"   Créé: id={new_corr['id']}")
    paperless['correspondents'][corr_name] = new_corr['id']

# Step 6: Build recap message
recap = f"📄 Document: {result['type_document']}\n"
recap += f"🏢 Émetteur: {result['correspondant']}\n"
recap += f"👤 Propriétaire: {result['proprietaire']}\n"
recap += f"📝 Titre: {result['titre']}\n"
d = result.get('donnees_extraites', {})
if d.get('date'): recap += f"📅 Date: {d['date']}\n"
if d.get('client'): recap += f"🏢 Client: {d['client']}\n"
if d.get('heures'):
    recap += "\n⏰ Heures:\n"
    for h in d['heures']:
        recap += f"   {h.get('label','?')}: {h.get('valeur','?')}\n"
if d.get('durees'):
    recap += "\n⏱️ Durées:\n"
    for dd in d['durees']:
        recap += f"   {dd.get('label','?')}: {dd.get('valeur','?')}\n"
if d.get('activites'):
    recap += f"\n🔧 Activités: {', '.join(d['activites'])}\n"
if d.get('montants'):
    recap += "\n💰 Montants:\n"
    for m in d['montants']:
        recap += f"   {m.get('label','?')}: {m.get('valeur','?')}\n"
if d.get('notes'): recap += f"\n📝 Notes: {d['notes']}\n"
recap += "\n⚠️ Vérifie ces données. Si quelque chose est faux, corrige."

print(f"\n=== RÉCAP ===\n{recap}")
print("\n=== TOUT FONCTIONNE ✅ ===")