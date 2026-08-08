import json, base64, urllib.request, os

API_KEY = "${MISTRAL_API_KEY}"

def mistral_ocr(file_b64, mime_type):
    """Call Mistral OCR - handles both images and PDFs"""
    if mime_type == 'application/pdf':
        payload = {
            'model': 'mistral-ocr-latest',
            'document': {
                'type': 'document_url',
                'document_url': f'data:application/pdf;base64,{file_b64}'
            }
        }
    else:
        payload = {
            'model': 'mistral-ocr-latest',
            'document': {
                'type': 'image_url',
                'image_url': {'url': f'data:{mime_type};base64,{file_b64}'}
            }
        }
    
    req = urllib.request.Request(
        'https://api.mistral.ai/v1/ocr',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    
    all_markdown = ''
    for page in data['pages']:
        all_markdown += page['markdown'] + '\n\n---\n\n'
    return all_markdown

def extract_data(ocr_markdown):
    """Call mistral-small-latest for structured extraction"""
    system_prompt = """Tu es un assistant OCR qui analyse des documents numérisés ou photographiés.
On te donne le résultat d'un OCR (texte brut markdown).

Tu DOIS:
1. Identifier le type de document (feuille de mission, facture, bon de commande, etc.)
2. Extraire TOUTES les informations visibles: dates, noms, heures, durées, activités, lieux, montants
3. Ne jamais inventer ou supposer. Si une info n'est pas lisible, mets null.
4. Garder les valeurs exactes telles que lues (ex: "17H15" pas "17:15")
5. Lister toutes les activités mentionnées (départ, déchargement, chargement, etc.)
6. Lister toutes les heures avec leur label (départ, arrivée, etc.)
7. Lister toutes les durées mentionnées

Réponds UNIQUEMENT en JSON avec ce format:
{
  "type_document": "string",
  "date": "string ou null",
  "operateur": "string ou null",
  "client": "string ou null",
  "activites": ["liste"],
  "heures": [{"label": "string", "valeur": "string"}],
  "durees": [{"label": "string", "valeur": "string"}],
  "lieux": ["liste"],
  "montants": [{"label": "string", "valeur": "string"}],
  "notes": "string ou null"
}"""

    payload = {
        'model': 'mistral-small-latest',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': 'Voici le texte OCR à analyser:\n' + ocr_markdown}
        ],
        'temperature': 0.1,
        'response_format': {'type': 'json_object'}
    }
    
    req = urllib.request.Request(
        'https://api.mistral.ai/v1/chat/completions',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    content = data['choices'][0]['message']['content']
    return json.loads(content)

def build_recap(data):
    """Format the recap message"""
    recap = f"📄 Document: {data.get('type_document', 'Non identifié')}\n\n"
    if data.get('date'): recap += f"📅 Date: {data['date']}\n"
    if data.get('operateur'): recap += f"👤 Opérateur: {data['operateur']}\n"
    if data.get('client'): recap += f"🏢 Client: {data['client']}\n"
    
    if data.get('heures'):
        recap += "\n⏰ Heures:\n"
        for h in data['heures']:
            recap += f"   {h.get('label', '?')}: {h.get('valeur', '?')}\n"
    
    if data.get('durees'):
        recap += "\n⏱️ Durées:\n"
        for d in data['durees']:
            recap += f"   {d.get('label', '?')}: {d.get('valeur', '?')}\n"
    
    if data.get('activites'):
        recap += f"\n🔧 Activités: {', '.join(data['activites'])}\n"
    
    if data.get('lieux'):
        recap += f"📍 Lieux: {', '.join(data['lieux'])}\n"
    
    if data.get('montants'):
        recap += "\n💰 Montants:\n"
        for m in data['montants']:
            recap += f"   {m.get('label', '?')}: {m.get('valeur', '?')}\n"
    
    if data.get('notes'): recap += f"\n📝 Notes: {data['notes']}\n"
    recap += "\n⚠️ Vérifie ces données. Si quelque chose est faux, corrige. Si tout est correct, clique sur ✅ Valider."
    return recap

# ===== TEST 1: IMAGE =====
print("=" * 50)
print("TEST 1: IMAGE (feuille de mission)")
print("=" * 50)
img_path = "/opt/data/cache/images/img_27485f0c6317.jpg"
with open(img_path, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

ocr_md = mistral_ocr(img_b64, 'image/jpeg')
print(f"OCR OK ({len(ocr_md)} chars)")

data = extract_data(ocr_md)
print(f"Extraction OK")
print(json.dumps(data, indent=2, ensure_ascii=False))

recap = build_recap(data)
print(f"\nRECAP:\n{recap}")

# ===== TEST 2: PDF =====
print("\n" + "=" * 50)
print("TEST 2: PDF (test document)")
print("=" * 50)

pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 55 >>
stream
BT /F1 12 Tf 100 700 Td (FEUILLE DE MISSION JOURNALIERE - Test PDF) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000370 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
451
%%EOF"""

pdf_b64 = base64.b64encode(pdf_content).decode()

ocr_md = mistral_ocr(pdf_b64, 'application/pdf')
print(f"OCR OK ({len(ocr_md)} chars)")
print(f"OCR content: {ocr_md[:100]}")

data = extract_data(ocr_md)
print(f"Extraction OK")
print(json.dumps(data, indent=2, ensure_ascii=False))

recap = build_recap(data)
print(f"\nRECAP:\n{recap}")

print("\n" + "=" * 50)
print("ALL TESTS PASSED ✅")
print("=" * 50)