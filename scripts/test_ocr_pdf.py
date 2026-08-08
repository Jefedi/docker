import json, base64, urllib.request, os

API_KEY = "${MISTRAL_API_KEY}"

# Find a PDF to test with - check if there are any downloaded Telegram files
# from the n8n binary data storage
binary_dir = "/opt/data/scripts"
# Actually, let's create a simple test PDF or find one

# Check if there are any PDFs in the n8n binary storage
import subprocess
result = subprocess.run(['find', '/opt/data/cache', '-name', '*.pdf', '-o', '-name', '*.jpg', '-o', '-name', '*.png'], 
                       capture_output=True, text=True, timeout=5)
print("Files in cache:")
print(result.stdout[:500])

# Use the existing test image first
img_path = "/opt/data/cache/images/img_27485f0c6317.jpg"
if os.path.exists(img_path):
    with open(img_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    # Test with image_url (should work - we know this works)
    payload_img = {
        'model': 'mistral-ocr-latest',
        'document': {
            'type': 'image_url',
            'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}
        }
    }
    req = urllib.request.Request(
        'https://api.mistral.ai/v1/ocr',
        data=json.dumps(payload_img).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    print(f"\n=== IMAGE OCR WORKS ===")
    print(f"Pages: {len(data['pages'])}")
    print(f"Markdown preview: {data['pages'][0]['markdown'][:200]}")

# Now test with a PDF - let's create a simple one with text
# Use reportlab if available, or just create a minimal PDF
from io import BytesIO

# Create a minimal PDF with some text
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

# Test with file_url (for PDFs)
payload_pdf = {
    'model': 'mistral-ocr-latest',
    'document': {
        'type': 'file_url',
        'file_url': {'url': f'data:application/pdf;base64,{pdf_b64}'}
    }
}

req = urllib.request.Request(
    'https://api.mistral.ai/v1/ocr',
    data=json.dumps(payload_pdf).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    print(f"\n=== PDF OCR (file_url) WORKS ===")
    print(f"Pages: {len(data['pages'])}")
    print(f"Markdown preview: {data['pages'][0]['markdown'][:200]}")
except urllib.error.HTTPError as e:
    print(f"\n=== PDF OCR (file_url) FAILED ===")
    print(f"HTTP {e.code}")
    print(e.read().decode()[:500])

# Also test with image_url for PDF (should fail)
payload_pdf_img = {
    'model': 'mistral-ocr-latest',
    'document': {
        'type': 'image_url',
        'image_url': {'url': f'data:application/pdf;base64,{pdf_b64}'}
    }
}

req = urllib.request.Request(
    'https://api.mistral.ai/v1/ocr',
    data=json.dumps(payload_pdf_img).encode(),
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    print(f"\n=== PDF OCR (image_url) WORKS ===")
    print(f"Pages: {len(data['pages'])}")
except urllib.error.HTTPError as e:
    print(f"\n=== PDF OCR (image_url) FAILED ===")
    print(f"HTTP {e.code}")
    print(e.read().decode()[:300])