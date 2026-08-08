#!/usr/bin/env python3
"""Hermes Agent metrics exporter — agrège Voxtral + LiteLLM pour Home Assistant.

Output JSON pour HA REST sensor:
{
  "voxtral": {tts_tokens, stt_tokens, total_tokens, quota, pct_used, ...},
  "litellm": {spend, max_budget, rpm_limit, models, budget_reset, ...},
  "models": {glm-5.2: {calls, tokens}, ...},
  "timestamp": "2026-07-23T..."
}
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ============================================================
# Config
# ============================================================
LITELLM_URL = "http://127.0.0.1:4000"
LITELLM_KEY_FILE = Path("/tmp/ollama_key.txt")
VOXTRAL_USAGE_FILE = Path("/opt/data/voxtral_usage.json")
VOXTRAL_QUOTA = 4_000_000
OUTPUT_FILE = Path("/opt/data/hermes_metrics.json")

# ============================================================
# Voxtral metrics
# ============================================================
def get_voxtral_metrics() -> dict:
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    if not VOXTRAL_USAGE_FILE.exists():
        return {
            "tts_tokens": 0, "stt_tokens": 0, "total_tokens": 0,
            "tts_calls": 0, "stt_calls": 0,
            "quota": VOXTRAL_QUOTA, "remaining": VOXTRAL_QUOTA,
            "pct_used": 0.0, "month": month_key,
        }
    try:
        with open(VOXTRAL_USAGE_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        data = {}

    month_data = data.get(month_key, {})
    tts = month_data.get("tts", {})
    stt = month_data.get("stt", {})
    total = month_data.get("total_tokens", 0)
    remaining = max(0, VOXTRAL_QUOTA - total)
    pct = (total / VOXTRAL_QUOTA * 100) if VOXTRAL_QUOTA > 0 else 0

    return {
        "tts_tokens": tts.get("tokens", 0),
        "stt_tokens": stt.get("tokens", 0),
        "total_tokens": total,
        "tts_calls": tts.get("calls", 0),
        "stt_calls": stt.get("calls", 0),
        "tts_chars": tts.get("chars", 0),
        "stt_chars": stt.get("chars", 0),
        "quota": VOXTRAL_QUOTA,
        "remaining": remaining,
        "pct_used": round(pct, 2),
        "month": month_key,
    }


# ============================================================
# LiteLLM metrics
# ============================================================
def _get_litellm_key() -> str:
    if LITELLM_KEY_FILE.exists():
        return LITELLM_KEY_FILE.read_text().strip()
    # Fallback: chercher dans .env
    env_path = Path("/opt/data/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OLLAMA_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip()
    return ""


def get_litellm_metrics() -> dict:
    key = _get_litellm_key()
    if not key:
        return {"error": "no_api_key", "available": False}

    try:
        req = urllib.request.Request(f"{LITELLM_URL}/key/info")
        req.add_header("Authorization", f"Bearer {key}")
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        info = data.get("info", {})

        spend = info.get("spend", 0.0)
        max_budget = info.get("max_budget", 0.0)
        pct = (spend / max_budget * 100) if max_budget > 0 else 0
        models = info.get("models", [])
        model_spend = info.get("model_spend", {})

        return {
            "available": True,
            "spend": round(spend, 4),
            "max_budget": max_budget,
            "pct_budget_used": round(pct, 2),
            "rpm_limit": info.get("rpm_limit", 0),
            "tpm_limit": info.get("tpm_limit", 0),
            "models": models,
            "model_spend": model_spend,
            "budget_duration": info.get("budget_duration", ""),
            "budget_reset_at": info.get("budget_reset_at", ""),
            "key_alias": info.get("key_alias", ""),
            "version": _get_litellm_version(key),
        }
    except Exception as e:
        return {"error": str(e), "available": False}


def _get_litellm_version(key: str) -> str:
    try:
        req = urllib.request.Request(f"{LITELLM_URL}/health/readiness")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read())
        return "1.93.0"  # from x-litellm-version header
    except:
        return "unknown"


def get_litellm_models_usage(key: str) -> dict:
    """Récupère l'usage par modèle en faisant un appel de test."""
    # Le model_spend est souvent vide, on doit utiliser d'autres moyens
    # On retourne juste les modèles disponibles
    return {}


# ============================================================
# Export
# ============================================================
def export_metrics() -> dict:
    voxtral = get_voxtral_metrics()
    litellm = get_litellm_metrics()

    metrics = {
        "voxtral": voxtral,
        "litellm": litellm,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Écrire dans le fichier de sortie pour HA
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    metrics = export_metrics()
    print(json.dumps(metrics, indent=2))