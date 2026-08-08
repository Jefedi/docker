---
name: home-theater-setup
description: >-
  Configure streaming devices (Apple TV, Fire TV, Chromecast) to control TV/soundbar
  volume, power, and input via HDMI-CEC and IR. Covers Vidaa, Tizen, WebOS, Android TV,
  and other TV platforms. Troubleshoot remote integration, volume control, CEC handshake
  failures, and IR learning.
triggers:
  - User asks why Apple TV (or other streaming stick/box) remote can't control TV volume
  - User asks about HDMI-CEC not working between TV and streaming device
  - User asks why "Learn New Device" / "Apprendre un nouvel appareil" fails
  - User has two remotes and wants to consolidate to one
  - User asks why volume buttons on Apple TV remote show on-screen feedback but don't change actual volume
  - User mentions a TV brand like Qilive, Hisense, Vestel running Vidaa OS
---

# Home Theater Setup — Remote & Volume Troubleshooting

## Core Concepts

### How Apple TV remote controls volume

| Method | Mechanism | When it works |
|--------|-----------|---------------|
| **HDMI-CEC** | Sends volume commands through HDMI cable | TV/receiver supports CEC volume control **and** Apple TV → Settings → Volume Control → **HDMI** selected |
| **IR (Infrared)** | Remote has IR emitter at the top (black plastic) — aims at TV's IR receiver | TV has a visible IR receiver + pre-programmed codes match the TV brand |
| **Learn New Device** | Apple TV records IR codes from the TV's original remote | TV's remote actually emits IR (not Bluetooth-only) |

**Key Apple quirk:** When connected directly to a TV (no AV receiver), Apple TV defaults to **IR** for volume control even when CEC is enabled. HDMI-CEC handles power on/off, but volume is often IR-only unless explicitly set to "HDMI" in Volume Control settings.

### Identifying TV remote type (IR vs Bluetooth)

Quick diagnostic: point the TV remote **away from the TV** and press Volume +/‑

| If volume still changes | If volume stops |
|-------------------------|-----------------|
| Remote is **Bluetooth** | Remote is **IR** |
| No IR signals to learn | Apple TV "Learn New Device" will work |

Bluetooth remotes are common on Vidaa OS TVs (Qilive, Hisense, Vestel) with voice control. These remotes do NOT emit IR — the Apple TV cannot learn codes from them.

---

## Step-by-Step Troubleshooting

### 1. Enable HDMI-CEC on the TV

**Vidaa OS (Hisense / Qilive / Vestel):**
- Press ☰ (3 lines) on TV remote
- **Réglages** → **Connexion** (or **Système**) → **HDMI & CEC** → **Contrôle CEC** → **Activé**
- Also enable: *Extinction automatique des périphériques*, *Mise en route automatique*

**Other platforms:** Look for "HDMI Control", "CEC", "Bravia Sync", "Anynet+", "SimpLink", "VIERA Link" depending on brand.

### 2. Configure Apple TV volume control

**Settings** → **Remotes and Devices** → **Volume Control**:

| Option | When to try |
|--------|-------------|
| **Auto** | Default. Try first. |
| **HDMI** | Try if Auto didn't work — forces CEC volume (may work where Auto doesn't) |
| **TV via IR** | Try if CEC fails AND TV has an IR receiver |
| **Learn New Device** | Try if IR codes don't match your TV brand. Requires TV remote to emit IR. |
| **Off** | Last resort — disables external volume control |

### 3. Refresh the HDMI-CEC connection

1. Turn off Apple TV and TV (unplug both)
2. Disconnect HDMI cable
3. Wait 30 seconds
4. Plug HDMI back in
5. Power on: TV first, then Apple TV
6. This forces a fresh CEC handshake

### 4. Try a different HDMI port

Not all HDMI ports support CEC equally. On budget TVs, the **first HDMI port** (HDMI 1) or the **ARC-labeled port** typically has the best CEC support.

### 5. Hairline cases — Bluetooth-only TV remote

On TVs where the bundled remote is **Bluetooth-only** (common on Qilive/Vestel/Vidaa):

- "Learn New Device" will fail — no IR codes to learn
- "TV via IR" may fail if the TV has no IR receiver
- CEC volume may or may not work (depends on TV firmware)

**Workarounds in order of preference:**

| Solution | How | Cost |
|----------|-----|:----:|
| Accept two remotes | TV remote for volume, Apple remote for everything else | Free |
| External IR blaster | e.g. SwitchBot Hub Mini — connects to Apple TV over WiFi/Bluetooth, sends IR to TV | ~25-35€ |
| Soundbar via HDMI ARC | Soundbar handles audio + volume via CEC, Apple TV remote controls it | 80-500€ |
| AV receiver | Full home theater receiver bypasses TV audio entirely | 200-1000€ |

### 6. On-screen feedback but no actual volume change

If the Apple TV shows the volume slider but the TV volume doesn't change:

- The remote IS sending a signal (good)
- The signal isn't reaching the TV's audio controller
- Switch from Auto → TV via IR, or vice versa
- Check if TV speakers are set as the default audio output

---

## Device-Specific Notes

### Qilive (Auchan) — Vidaa OS

- OEM = Vestel (Turkish manufacturer), runs licensed Vidaa OS from Hisense
- TV has **Bluetooth** support — bundled remote is Bluetooth for voice commands
- TV **may or may not** have an IR receiver (check for a small dark window on front/bottom bezel)
- CEC and remote control are hit-or-miss due to Vestel firmware quality

### Hisense — Vidaa OS

- Same CEC path as Qilive (Réglages > Connexion > HDMI & CEC)
- Hisense uses both IR and Bluetooth remotes depending on model year
- Newer models (2023+) tend toward Bluetooth remotes

### Samsung — Tizen

- CEC = **Anynet+**
- Settings → General → External Device Manager → Anynet+ (HDMI-CEC)

### LG — WebOS

- CEC = **SimpLink**
- Settings → Connection → HDMI Device Settings → SimpLink

### Sony — Android TV / Google TV

- CEC = **Bravia Sync**
- Settings → Channels & Inputs → External Inputs → Bravia Sync settings

---

## Smart TV Platform Guide

For TV OS comparison, app installation workarounds (Vidaa, Tizen, WebOS, Roku, Android TV), sideloading methods, and OS replacement feasibility, see `references/smart-tv-platform-guide.md`. The Vidaa HiUtils API install method is detailed in `references/vidaa-os-installation.md`.

## Pitfalls

- Do NOT assume "Auto" in Apple TV Volume Control will pick CEC — often defaults to IR
- Do NOT assume a TV with Bluetooth has an IR receiver — some budget models skip the IR receiver entirely
- "Learn New Device" requires the **TV remote to emit IR** — if the TV remote is Bluetooth, this WILL fail
- Disconnecting HDMI while TV is on can damage the port — always power off first
- CEC behaves differently across firmware versions — a TV that didn't work last year may work after an update
- Qilive/Vestel TVs have inconsistent firmware — what works on one unit may not on another of the same model

## Sources

- Apple Support: https://support.apple.com/en-us/108769
- Apple Support (tvOS guide): https://support.apple.com/guide/tv/apple-tv-4k-remote-control-receiver-atvbbe2477c9/tvos
- Hisense Vidaa manual (CEC path): https://hisense.fr/download/serie/E7NQ/manuelsys.pdf
- Apple Community (Hisense volume): https://discussions.apple.com/thread/251720875
- ComputerBase forum (CEC vs IR behavior): https://www.computerbase.de/forum/threads/apple-tv-lautstaerke-via-hdmi-nicht-via-ir-wird-nicht-angezeigt.2095701/
- Frandroid (Vidaa OS overview): https://www.frandroid.com/marques/hisense/2456532_hisense-vidaa-rubriques-parametres-fonctions-tout-savoir-sur-le-systeme-pour-tv-et-videoprojecteurs
