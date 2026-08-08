# Smart TV Platform Guide

Reference guide for smart TV operating systems, app installation restrictions, sideloading possibilities, and OS replacement feasibility. Covers Vidaa, Tizen, WebOS, Roku, Android TV, Google TV, and Fire TV.

## Quick Platform Reference

| OS | Brands | App format | Sideloadable? |
|----|--------|-----------|:---:|
| **Vidaa** (Linux-based) | Hisense, Qilive, Toshiba (EU), Sharp | Native store only | ❌ No APK |
| **Tizen** | Samsung | Native store only | ⚠️ Via dev mode (limited) |
| **WebOS** | LG | Native store only | ⚠️ Via dev mode (limited) |
| **Roku** | Roku, some Hisense/TCL | Native store only | ❌ Completely closed |
| **Android TV / Google TV** | Sony, TCL, Philips, Xiaomi, Hisense (US) | APK | ✅ Full sideload |
| **Fire TV** | Amazon (Toshiba, Insignia) | APK | ✅ Via ADB |

## Vidaa OS (Hisense / Qilive / Toshiba EU / Sharp)

- **Vidaa is NOT Android.** Proprietary Linux-based OS. No bootloader, no recovery, no ADB.
- **APK files cannot be installed** — the OS does not support them.
- **The OS CANNOT be replaced** with Android TV. Hardware-locked (different SoC/drivers). No custom ROMs exist.
- Some **Chinese-market** Hisense TVs have Android underneath a Vidaa skin — European models (including Qilive/Auchan) are pure Vidaa.

### Web app installation methods on Vidaa

**Method 1 — DNS-based alternate store** (Vidaa 2/3/4, pre-2022)
1. Set DNS to `89.169.10.217` in network settings
2. Open browser → `vidaahub.com`
3. Install from alternate catalog
4. Revert DNS after install

**Method 2 — `hisense://debug`** (Vidaa 2/3/4)
1. Open TV browser → `hisense://debug`
2. Fill form: App Name, App URL (e.g. `http://SERVER_IP:8096/web`), icons
3. Click INSTALL, restart TV
4. ⚠️ Newer Vidaa (8/9) may require a password or reject this URL

**Method 3 — HiUtils API via local web server** (Vidaa 9, tested)
1. Create `script.js` using `HiUtils_createRequest('fileWrite', ...)` to write to `websdk/Appinfo.json`
2. Serve via `python -m http.server 8181` on a local PC
3. Open TV browser → local server URL
4. Page installs app entry; restart TV to see it in app list
5. See `references/vidaa-os-installation.md` in this skill directory for details

**Method 4 — Browser PWA** (works on any Vidaa)
1. Open TV browser, navigate to web app URL
2. Bookmark or "Add to Home Screen" if available

### Key reference for Vidaa research
Russian forum 4PDA has the most extensive Vidaa discussion (1000+ page threads). Reddit r/Hisense and XDA Developers have no successful OS swap stories.

## When the user asks "can I install Android TV on my TV?"

**Standard answer (99% of cases):** No. The OS is burned into the TV's firmware. No custom ROMs exist for consumer TVs. The hardware bootloader is locked and there is no recovery mode for flashing alternative OSes.

**The only real solution:** An external HDMI streaming device:
| Device | Price | Notes |
|--------|:-----:|-------|
| Chromecast with Google TV 4K | ~40-50€ | Best bang for buck |
| Xiaomi Mi Box S / Stick | ~40-50€ | Solid Android TV |
| Nvidia Shield TV Pro | ~150-200€ | Best for Jellyfin transcoding, high perf |
| ONN 4K Streaming Box (US) | ~20$ | Cheap and capable |

## Approach for answering TV OS questions

1. Identify the exact brand, model, and OS version
2. Check if TV is Android-based (sideloading possible) or closed platform (no APK support)
3. For app installation: research OS-specific workarounds (store hacks, dev modes, HiUtils)
4. For OS replacement: be clear upfront that it's almost never possible — redirect to external HDMI device
5. Search sources: Reddit r/Hisense, XDA Developers, 4PDA, forum.jellyfin.org

## Pitfalls

- Do NOT suggest unlocking the bootloader on Vidaa — there is no Android bootloader to unlock
- Do NOT say "install the APK" — Vidaa doesn't support APKs
- Do NOT suggest flashing custom ROMs — none exist for consumer TVs
- Do NOT waste time searching for "Vidaa to Android conversion success stories" — they don't exist
- Some forums confuse Android-based Hisense (Chinese market) with pure Vidaa (EU market) — verify which the user has
- Qilive = Auchan house brand, OEM'd mostly by Hisense, always runs pure Vidaa in Europe

## Related

Absorbed from the `smart-tv-platform-guide` skill (archived). This skill now covers both streaming device setup (HDMI-CEC, IR volume, remote troubleshooting) and TV OS platform guidance as complementary topics under home theater configuration.
