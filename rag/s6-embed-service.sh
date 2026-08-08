#!/command/with-contenv sh
# shellcheck shell=sh
# FastEmbed embedding service for RAG
# Provides embeddings via HTTP on port 9200
set -e
export HOME=/opt/data
cd /opt/data/rag
. /opt/data/rag-venv/bin/activate
[ "$(id -u)" = 0 ] || exec python3 embedding_service.py
exec s6-setuidgid hermes python3 embedding_service.py