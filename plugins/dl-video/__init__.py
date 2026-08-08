"""Plugin de commande /dl pour Telegram — téléchargement via MeTube."""

from __future__ import annotations

import json
import logging
import os
import subprocess

logger = logging.getLogger(__name__)

METUBE_URL = os.getenv("METUBE_URL", "https://metube.jefe.al")
DOCKER_EXEC = os.getenv("METUBE_DOCKER_CMD", "docker exec pangolin-cli")

MANIFEST = {
    "name": "dl-video",
    "version": "1.0.0",
    "description": "Commande /dl pour télécharger des vidéos via MeTube",
}


async def _dl_handler(raw_args: str) -> str:
    """Handler pour /dl <url> — ajoute un téléchargement MeTube."""
    url = raw_args.strip()
    if not url:
        return (
            "Usage: `/dl <url>`\n\n"
            "Exemple: `/dl https://www.youtube.com/watch?v=xxx`"
        )

    # Valide que c'est une URL
    if not url.startswith(("http://", "https://")):
        return (
            f"❌ `{url}` n'est pas une URL valide.\n"
            f"Format attendu: `/dl https://www.youtube.com/watch?v=xxx`"
        )

    try:
        cmd_parts = DOCKER_EXEC.split() + [
            "curl", "-sk", "-X", "POST", f"{METUBE_URL.rstrip('/')}/add",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"url": url, "quality": "best"}),
            "--max-time", "60"
        ]
        result = subprocess.run(
            cmd_parts, capture_output=True, text=True, timeout=65
        )

        if result.returncode != 0:
            return (
                f"❌ Erreur MeTube (exit={result.returncode}):\n"
                f"`{result.stderr[:200]}`"
            )

        response = json.loads(result.stdout)
        if response.get("status") == "ok":
            return (
                f"✅ Vidéo ajoutée à MeTube !\n"
                f"`{url}`\n\n"
                f"Le téléchargement est en cours."
            )
        else:
            return f"⚠️ Réponse inattendue: `{response}`"

    except json.JSONDecodeError as e:
        return f"❌ Erreur de lecture réponse: {e}"
    except subprocess.TimeoutExpired:
        return "❌ Timeout - MeTube n'a pas répondu à temps."
    except Exception as e:
        return f"❌ Erreur: {e}"


def register(ctx) -> None:
    """Plugin entry point — enregistre la commande /dl."""
    ctx.register_command(
        name="dl",
        handler=_dl_handler,
        description="Télécharger une vidéo via MeTube (ex: /dl https://youtu.be/xxx)",
        args_hint="<url>",
    )
    logger.info("Plugin dl-video: commande /dl enregistrée")
