#!/usr/bin/env python3
"""
FastEmbed HTTP Service for RAG
Provides embeddings via a simple HTTP API for n8n workflows.

POST /embed   {"texts": ["text1", "text2"]}  -> {"embeddings": [[...], [...]], "dim": 384}
GET  /health  -> {"status": "ok", "model": "...", "dim": 384}
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("embed-service")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PORT = 9200

# Initialize model at startup (downloads weights on first run)
log.info(f"Initializing FastEmbed model: {MODEL_NAME}")
embedder = TextEmbedding(model_name=MODEL_NAME)
DIM = 384
log.info(f"Model loaded. Dimension: {DIM}")


class EmbedHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "model": MODEL_NAME, "dim": DIM})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/embed":
            self._send_json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))

            texts = data.get("texts", [])
            if isinstance(texts, str):
                texts = [texts]
            if not texts:
                self._send_json(400, {"error": "no texts provided"})
                return

            embeddings = [e.tolist() for e in embedder.embed(texts)]
            self._send_json(200, {"embeddings": embeddings, "dim": DIM, "count": len(embeddings)})

        except Exception as e:
            log.error(f"Error: {e}")
            self._send_json(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        log.info(f"{self.client_address[0]} - {fmt % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), EmbedHandler)
    log.info(f"Embedding service listening on :{PORT}")
    server.serve_forever()