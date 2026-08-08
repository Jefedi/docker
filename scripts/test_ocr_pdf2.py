import json, base64, urllib.request

API_KEY = "${MISTRAL_API_KEY}"

# Create a minimal PDF
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

# Test with document_url type (as the error message says)
payload = {
    'model': 'mistral-ocr-latest',
    'document': {
        'type': 'document_url',
        'document_url': f'data:application/pdf;base64,{pdf_b64}'
    }
}

req = urllib.request.Request(
    'https://api.mistral.ai/v1/ocr',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    print("=== PDF OCR (document_url) WORKS ===")
    print(f"Pages: {len(data['pages'])}")
    for p in data['pages']:
        print(f"  Page {p['index']}: {p['markdown'][:200]}")
except urllib.error.HTTPError as e:
    print(f"=== PDF OCR (document_url) FAILED ===")
    print(f"HTTP {e.code}")
    body = e.read().decode()
    print(body[:500])