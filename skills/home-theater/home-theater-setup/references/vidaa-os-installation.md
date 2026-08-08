# Vidaa OS — App Installation & OS Replacement Research

## Context

User had a **Qilive TV** (Auchan house brand, OEM'd by Hisense) running **Vidaa OS** and wanted to:
1. Install Jellyfin and other apps not in the Vidaa store
2. Replace Vidaa OS with Android TV entirely

## Sources Consulted

| Source | URL | Key Finding |
|--------|-----|-------------|
| thecodeninja.net | https://thecodeninja.net/2024/09/jellyfin-on-hisense-vidaa/ | hisense://debug + HiUtils methods documented; also browserDeviceProfile.js patching for HEVC remux |
| Reddit r/Hisense | Multiple threads | Universal consensus: OS replacement impossible, buy an external streaming device |
| XDA Developers | Multiple threads | No successful custom ROM flash for Vidaa TVs |
| 4PDA (Russian) | 1000+ page threads | Most extensive Vidaa discussion; only app-store-hack methods, no OS swap |
| Jellyfin Forum | https://forum.jellyfin.org/t-install-jellyfin-on-vidaaos-based-tv-hisense-sharp-toshiba-etc | Community reports on hisense://debug + HiUtils, some playback issues |
| Pikabu (Russian) | https://pikabu.ru/story/jellyfin_na_vidaa_9_13617347 | Detailed HiUtils API install guide for Vidaa 9 with Python local server |
| GetsApp.ru | https://getsapp.ru/posts/ustanovka-prilojenii-na-vidaa-os-hisense-toshiba-i-drugie | DNS-based alternate store (89.169.10.217 → vidaahub.com) |

## Method Details

### hisense://debug Install (Vidaa 2/3/4)

1. Open TV browser → navigate to `hisense://debug`
2. Fill form:
   - App Name: `Jellyfin`
   - App URL: `http://<jellyfin-server>:8096/web`
   - Thumbnail: `http://<jellyfin-server>:8096/web/assets/splash/iphone5_splash_l.png`
   - Icons: `http://<jellyfin-server>:8096/web/assets/img/icon-transparent.png`
   - Resolution: `1080`
3. Click INSTALL, restart TV

**Known passwords** (often don't work on newer models): `11111`, `hisenseservice`, `0000`, `1234`.

### HiUtils API Install (Vidaa 9, most reliable)

Runs a local Python HTTP server to inject an app entry into `websdk/Appinfo.json` via the `HiUtils_createRequest` JavaScript API available in the TV's web runtime.

**server/index.html:**
```html
<!DOCTYPE html>
<html>
<head><title>Jellyfin Installer</title></head>
<body>
<h1>Installing Jellyfin app...</h1>
<script src="http://<PC_IP>:8181/script.js"></script>
</body>
</html>
```

**server/script.js** (key structure):
```javascript
(function() {
const current = HiUtils_createRequest('fileRead', {path: 'websdk/Appinfo.json', mode: 6});
const apps = current.ret ? JSON.parse(current.msg) : { AppInfo: [] };
const jellyfin = {
  Id: "jellyfin-web", AppName: "Jellyfin", URL: "http://<SERVER_IP>:8096/web",
  Type: "Browser", StoreType: "custom", PreInstall: false,
  // include IconURL, Icon_96, Image, Thumb fields
};
apps.AppInfo.push(jellyfin);
return HiUtils_createRequest('fileWrite', {path: 'websdk/Appinfo.json', mode: 6, writedata: JSON.stringify(apps)});
})();
```

Run: `python -m http.server 8181` in the server directory.
Open TV browser → `http://<PC_IP>:8181` → page displays → restart TV.

**⚠️ Works for any web app** — just change the name, URL, and icon paths.

### DNS Alternate Store

1. Network settings → Manual DNS → Primary DNS: `89.169.10.217`
2. Browser → `vidaahub.com`
3. Install the alternate app store
4. Revert DNS to auto after install

### Browser PWA (safest, always works)

Just open the TV browser and navigate to the web app directly. Can bookmark or sometimes "Add to Home Screen". No native app lifecycle but requires no hacks.

## The Impossible: OS Replacement

**Cannot replace Vidaa with Android TV.** Reasons:

1. **Vidaa is not Android** — it's a proprietary Linux-based OS from Hisense. No fastboot, no recovery, no ADB.
2. **Bootloader** — there is no Android-style bootloader to unlock. The firmware is signed and encrypted.
3. **No custom ROMs** — no community develops custom firmware for consumer TVs.
4. **Different hardware** — EU-market Vidaa TVs use different SoCs than US-market Android TV models of the same brand. Even the same model number can have different internals per region.
5. **No success stories** — zero confirmed cases across Reddit, XDA, 4PDA, or any other forum.

### The real solution: external HDMI streaming device

| Device | Price (≈) | Notes |
|--------|:---------:|-------|
| Chromecast with Google TV 4K | 40-50€ | Google TV UI, Google Play Store, all apps |
| Xiaomi Mi Box S / Stick | 40-50€ | Android TV 12, reliable |
| Nvidia Shield TV Pro | 150-200€ | Best for Jellyfin (transcoding, audio passthrough) |
| ONN 4K Streaming Box | 20$ | Cheap, surprisingly good (US only) |

Plug into HDMI → use CEC to control with the dongle's remote → all apps work natively. TV reverts to normal when unplugged. Zero risk.

## Vidaa vs Android TV: Quick OS Comparison

| Feature | Vidaa | Android TV / Google TV |
|---------|:-----:|:----------------------:|
| App store size | ~1,000 apps | 5,000+ apps |
| Google Play Store | ❌ | ✅ |
| APK sideload | ❌ | ✅ |
| Jellyfin app | ❌ (web only) | ✅ (native Android TV app) |
| IPTV apps | Limited | Many (TiviMate, etc.) |
| Casting | Limited | ✅ Chromecast built-in |
| Google Assistant | ❌ | ✅ |
| OS updates | Rare, manufacturer-dependent | More frequent (device-dependent) |
| Bootloader unlock | N/A (not Android) | Possible on some devices |
| Custom ROM | None | Exists for some devices |
