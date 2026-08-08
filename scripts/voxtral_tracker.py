#!/usr/bin/env python3
"""Voxtral token tracker — intercepts Mistral TTS/STT calls and counts tokens.

Usage:
  1. As a standalone tracker: import and call log_tts/log_stt after each call
  2. As a CLI: python3 voxtral_tracker.py status     → show current usage
                python3 voxtral_tracker.py reset      → reset monthly counter
                python3 voxtral_tracker.py check      → alert if >80% (for cron)

Token estimation:
  - TTS: input text → tokens ≈ len(text) / 4 (Mistral uses ~4 chars/token)
  - STT: output transcript → tokens ≈ len(transcript) / 4

Storage: /opt/data/voxtral_usage.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Config
QUOTA_MONTHLY = 4_000_000  # 4M tokens/month (free tier)
ALERT_THRESHOLD = 0.80     # Alert at 80%
USAGE_FILE = Path("/opt/data/voxtral_usage.json")
NTFY_TOPIC = "hermes-agent-jefe"
NTFY_URL = f"https://ntfy.jefe.ovh/{NTFY_TOPIC}"
NTFY_AUTH = os.environ.get(
    "NTFY_TOKEN",
    "hermes-agent:UorgnpV0wJ61fIR5JVzaCxNVY0cNMtBKGNcmzqubrC0jMpCgECMJ26ZZbgCqh4VJ6X1Prez8",
)

# Token estimation: ~4 chars per token (Mistral/Llama tokenizer average)
CHARS_PER_TOKEN = 4


def _current_month_key() -> str:
    """Return YYYY-MM for the current month."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _load_usage() -> dict:
    """Load usage data from JSON file."""
    if not USAGE_FILE.exists():
        return {}
    try:
        with open(USAGE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_usage(data: dict) -> None:
    """Save usage data to JSON file."""
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    if not text:
        return 0
    return max(1, len(text) // CHARS_PER_TOKEN)


def log_tts(text: str, model: str = "voxtral-mini-tts-2603") -> int:
    """Log a TTS call and return estimated tokens used."""
    tokens = _estimate_tokens(text)
    return _add_usage("tts", model, tokens, len(text))


def log_stt(transcript: str, model: str = "voxtral-mini-transcribe-2507") -> int:
    """Log an STT call and return estimated tokens used."""
    tokens = _estimate_tokens(transcript)
    return _add_usage("stt", model, tokens, len(transcript))


def _add_usage(call_type: str, model: str, tokens: int, chars: int) -> int:
    """Add usage to the current month's record."""
    month_key = _current_month_key()
    data = _load_usage()

    if month_key not in data:
        data[month_key] = {
            "tts": {"tokens": 0, "calls": 0, "chars": 0, "model": ""},
            "stt": {"tokens": 0, "calls": 0, "chars": 0, "model": ""},
            "total_tokens": 0,
        }

    entry = data[month_key][call_type]
    entry["tokens"] += tokens
    entry["calls"] += 1
    entry["chars"] += chars
    entry["model"] = model
    data[month_key]["total_tokens"] = (
        data[month_key]["tts"]["tokens"] + data[month_key]["stt"]["tokens"]
    )

    _save_usage(data)
    return tokens


def get_status() -> dict:
    """Return current month's usage summary."""
    month_key = _current_month_key()
    data = _load_usage()

    if month_key not in data:
        return {
            "month": month_key,
            "tts": {"tokens": 0, "calls": 0, "chars": 0},
            "stt": {"tokens": 0, "calls": 0, "chars": 0},
            "total_tokens": 0,
            "quota": QUOTA_MONTHLY,
            "remaining": QUOTA_MONTHLY,
            "pct_used": 0.0,
        }

    month_data = data[month_key]
    total = month_data.get("total_tokens", 0)
    remaining = max(0, QUOTA_MONTHLY - total)
    pct = (total / QUOTA_MONTHLY * 100) if QUOTA_MONTHLY > 0 else 0

    return {
        "month": month_key,
        "tts": month_data.get("tts", {}),
        "stt": month_data.get("stt", {}),
        "total_tokens": total,
        "quota": QUOTA_MONTHLY,
        "remaining": remaining,
        "pct_used": round(pct, 2),
    }


def reset_month() -> None:
    """Reset current month's usage (for manual reset)."""
    month_key = _current_month_key()
    data = _load_usage()
    data[month_key] = {
        "tts": {"tokens": 0, "calls": 0, "chars": 0, "model": ""},
        "stt": {"tokens": 0, "calls": 0, "chars": 0, "model": ""},
        "total_tokens": 0,
    }
    _save_usage(data)
    print(f"✅ Reset usage for {month_key}")


def _send_ntfy(message: str, priority: str = "default", tags: str = "",
                actions: str = "") -> bool:
    """Send a notification via ntfy. URLs in message are auto-converted to buttons."""
    # Auto-extract URLs from message and convert to action buttons
    import re as _re
    urls = _re.findall(r'https?://[^\s]+', message)
    if urls and not actions:
        # Dedupe, max 5
        seen = set()
        action_parts = []
        for url in urls[:5]:
            url_clean = url.rstrip('.,;:)')
            if url_clean in seen:
                continue
            seen.add(url_clean)
            domain = _re.sub(r'https?://([^/]+).*', r'\1', url_clean)
            action_parts.append(f"view, {domain}, {url_clean}")
        actions = "; ".join(action_parts)
        # Remove URLs from message body
        message = _re.sub(r'https?://[^\s]+[.,;:)]*', '', message).strip()

    try:
        import urllib.request

        req = urllib.request.Request(NTFY_URL, data=message.encode("utf-8"), method="POST")
        req.add_header("Title", "Voxtral Quota Alert")
        req.add_header("Priority", priority)
        if tags:
            req.add_header("Tags", tags)
        if actions:
            req.add_header("Actions", actions)
        req.add_header("Authorization", f"Bearer {NTFY_AUTH}")
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"ntfy error: {e}", file=sys.stderr)
        return False


def check_and_alert() -> bool:
    """Check usage and send alert if above threshold. Returns True if alerted."""
    status = get_status()
    pct = status["pct_used"]

    if pct >= 100:
        msg = (
            f"🚨 Voxtral quota EXHAUSTÉ\n"
            f"Tokens utilisés: {status['total_tokens']:,} / {status['quota']:,}\n"
            f"Quota dépassé de {status['total_tokens'] - status['quota']:,} tokens\n"
            f"TTS: {status['tts'].get('tokens', 0):,} tokens ({status['tts'].get('calls', 0)} appels)\n"
            f"STT: {status['stt'].get('tokens', 0):,} tokens ({status['stt'].get('calls', 0)} appels)"
        )
        _send_ntfy(msg, priority="urgent", tags="warning,quota")
        print(msg)
        return True

    if pct >= ALERT_THRESHOLD * 100:
        msg = (
            f"⚠️ Voxtral quota à {pct:.1f}%\n"
            f"Tokens utilisés: {status['total_tokens']:,} / {status['quota']:,}\n"
            f"Restant: {status['remaining']:,} tokens\n"
            f"TTS: {status['tts'].get('tokens', 0):,} tokens ({status['tts'].get('calls', 0)} appels)\n"
            f"STT: {status['stt'].get('tokens', 0):,} tokens ({status['stt'].get('calls', 0)} appels)"
        )
        _send_ntfy(msg, priority="high", tags="warning,quota")
        print(msg)
        return True

    print(
        f"✅ Voxtral: {status['total_tokens']:,} / {status['quota']:,} tokens ({pct:.1f}%) — OK"
    )
    return False


def print_status() -> None:
    """Print formatted status."""
    s = get_status()
    print(f"═ Voxtral Usage — {s['month']} ═")
    print(f"")
    print(f"  TTS:  {s['tts'].get('tokens', 0):>10,} tokens  ({s['tts'].get('calls', 0)} appels, {s['tts'].get('chars', 0):,} chars)")
    print(f"  STT:  {s['stt'].get('tokens', 0):>10,} tokens  ({s['stt'].get('calls', 0)} appels, {s['stt'].get('chars', 0):,} chars)")
    print(f"  ─────────────────────────────────")
    print(f"  Total:   {s['total_tokens']:>9,} / {s['quota']:,} tokens ({s['pct_used']:.1f}%)")
    print(f"  Restant: {s['remaining']:>9,} tokens")
    print(f"")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: voxtral_tracker.py [status|reset|check]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "status":
        print_status()
    elif cmd == "reset":
        reset_month()
    elif cmd == "check":
        check_and_alert()
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: voxtral_tracker.py [status|reset|check]")
        sys.exit(1)