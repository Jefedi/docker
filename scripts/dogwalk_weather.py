#!/usr/bin/env python3
"""Dog-walk weather watchdog for Le Havre.

Script-only mode (no_agent=True): prints a message to send, or stays silent.
Silent = condition not met (no notification sent to user).
"""

import json
import urllib.request
import urllib.error
import os
import sys
from datetime import datetime, timezone, timedelta

LAT, LON = 49.493, 0.107  # Le Havre
TIMEZONE = "Europe/Paris"

# Dog-walk thresholds
MAX_OK_TEMP = 25       # still ok but warm
MAX_COMFORT_TEMP = 23  # comfortably cool for a dog
MIN_TEMP = 5           # too cold

# Cooldown file to avoid spamming "patience" messages
COOLDOWN_FILE = os.path.expanduser("~/.hermes/scripts/.dogwalk_patience_cooldown")


def fetch_weather():
    """Fetch current + hourly forecast from Open-Meteo (free, no key)."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}"
        f"&current=temperature_2m,apparent_temperature,weather_code,is_day"
        f"&hourly=temperature_2m,apparent_temperature,weather_code"
        f"&timezone={TIMEZONE}"
        f"&forecast_hours=48"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "HermesAgent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def weather_description(code):
    descs = {
        0: "dégagé", 1: "peu nuageux", 2: "partiellement nuageux", 3: "couvert",
        45: "brumeux", 48: "brouillard givrant", 51: "bruine légère",
        53: "bruine modérée", 55: "bruine dense", 61: "pluie légère",
        63: "pluie modérée", 65: "pluie forte", 71: "neige légère",
        73: "neige modérée", 75: "neige forte", 80: "averses légères",
        81: "averses modérées", 82: "averses fortes", 95: "orage",
        96: "orage grêle léger", 99: "orage grêle fort",
    }
    return descs.get(code, f"code {code}")


def is_good_for_walk(temp, weather_code):
    if temp is None:
        return False
    if temp < MIN_TEMP or temp > MAX_OK_TEMP:
        return False
    if weather_code in (65, 75, 82, 95, 96, 99):
        return False
    return True


def comfort_label(temp):
    if temp <= MAX_COMFORT_TEMP:
        return "idéal 🐕✅"
    elif temp <= MAX_OK_TEMP:
        return "correct ✅"
    return "trop chaud ❌"


def check_patience_cooldown():
    """Only send one 'patience' message per 6 hours."""
    now = datetime.now().timestamp()
    try:
        with open(COOLDOWN_FILE) as f:
            last = float(f.read().strip())
            if now - last < 21600:  # 6 hours
                return False
    except (FileNotFoundError, ValueError):
        pass
    return True


def mark_patience_sent():
    with open(COOLDOWN_FILE, "w") as f:
        f.write(str(datetime.now().timestamp()))


def build_message(data):
    now_utc = datetime.now(timezone.utc)
    now_paris = now_utc.astimezone(timezone(timedelta(hours=2)))
    current = data.get("current", {})
    hourly = data.get("hourly", {})

    current_temp = current.get("temperature_2m")
    current_feels = current.get("apparent_temperature")
    current_weather = current.get("weather_code", 0)
    is_day = current.get("is_day", 1)
    current_desc = weather_description(current_weather)

    now_iso = now_paris.strftime("%Y-%m-%dT%H:%M")
    now_hour = now_paris.hour

    # Sleep hours: silence everything between 23:00 and 05:00
    if now_hour >= 23 or now_hour < 5:
        return ""

    good_now = False
    if current_temp is not None:
        good_now = is_good_for_walk(current_temp, current_weather) and is_day == 1

    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weather_code", [])
    feels = hourly.get("apparent_temperature", [])

    # --- CASE 1: Good NOW → ALERT ---
    if good_now:
        label = comfort_label(current_temp)
        lines = [
            f"🐕 **BALADE TOUT DE SUITE AU HAVRE !**",
            f"",
            f"🌡️ {current_temp:.0f}°C (ressenti {current_feels:.0f}°C) — {label}",
            f"☁️ {current_desc}",
        ]
        if current_temp <= MAX_COMFORT_TEMP:
            lines.append(f"✅ Sol frais, température parfaite pour le chien !")
        if current_temp <= 20:
            lines.append(f"🌟 Conditions idéales, c'est le moment !")
        return "\n".join(lines)

    # --- CASE 2: Good windows coming in daytime hours → "patience" message ---
    # Only send between 06:00 and 20:00, with cooldown
    good_windows = []
    for i in range(len(times)):
        if times[i] <= now_iso:
            continue
        if len(good_windows) >= 6:
            break
        if i >= len(temps) or i >= len(codes):
            break
        t = temps[i]
        wc = codes[i]
        if t is not None and is_good_for_walk(t, wc):
            hour_str = times[i][11:16]
            # Only show daytime windows (6h-22h) for the patience message
            h = int(times[i][11:13])
            if 5 <= h < 22:
                good_windows.append((hour_str, t, feels[i] if i < len(feels) else t, wc))

    if good_windows and 5 <= now_hour < 20 and check_patience_cooldown():
        lines = [
            f"🐕 **ÇA VA BIENTÔT ÊTRE BON au Havre !**",
            f"",
            f"🌡️ Actuellement {current_temp:.0f}°C ({current_desc})",
            f"",
            f"**Meilleurs créneaux à venir :**",
        ]
        for hour_str, t, f, wc in good_windows[:3]:
            label = comfort_label(t)
            desc = weather_description(wc)
            lines.append(f"• {hour_str} — {t:.0f}°C (ressenti {f:.0f}°C) — {label}")
        mark_patience_sent()
        return "\n".join(lines)

    return ""


def main():
    try:
        data = fetch_weather()
        msg = build_message(data)
        if msg:
            print(msg)
        # Empty stdout = silent (watchdog pattern)
    except Exception as e:
        # Stay silent on errors — don't spam the user
        sys.stderr.write(f"dogwalk_weather error: {e}\n")


if __name__ == "__main__":
    main()
