# Codec Support & Direct Play Reference

## Video Compatibility (par client)

Source : https://jellyfin.org/docs/general/clients/codec-support/

| Codec | Chrome | Edge | Firefox | Safari | Android | Android TV | iOS | Roku | Kodi | JMP |
|---|---|---|---|---|---|---|---|---|---|---|
| H.264 8Bit | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| H.264 10Bit | ✅ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| H.265 8Bit (HEVC) | ⚠️ | ✅* | ⚠️** | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ |
| H.265 10Bit (HEVC) | ⚠️ | ✅* | ⚠️** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ |
| VP9 | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ✅ | ✅ | ✅ |
| AV1 | ✅ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ❌ | ✅ | ✅ | ✅ |

*Edge : nécessite HEVC Video Extension du Microsoft Store
**Firefox : 134+ (Win), 136+ (macOS), 137+ (Linux). Linux nécessite ffmpeg système

## Audio Compatibility

| Codec | Chrome | Edge | Firefox | Safari | Android | iOS | Roku | Kodi |
|---|---|---|---|---|---|---|---|---|
| AAC | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AC3 | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| EAC3 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| DTS | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ | ✅ |
| TrueHD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Passthrough |
| FLAC | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| OPUS | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ |

## Jellyfin Hardware Acceleration Config

Intel VAAPI (Linux) — config complète :

```json
{
  "HardwareAccelerationType": "vaapi",
  "VaapiDevice": "/dev/dri/renderD128",
  "HardwareDecodingCodecs": ["h264", "hevc", "vc1", "mpeg2video", "vp9"],
  "EnableHardwareEncoding": true,
  "AllowHevcEncoding": false,
  "EnableDecodingColorDepth10Hevc": true,
  "EnableDecodingColorDepth10Vp9": true,
  "H264Crf": 23,
  "H265Crf": 28
}
```

⚠️ "hevc" souvent absent de HardwareDecodingCodecs par défaut → ajouter manuellement.

## Diagnostiquer le playback

1. Dashboard → Active dashboard → colonne "Play Method"
2. Logs : `grep -i "transcode\|directplay\|DirectStream" /config/log/*.log`
3. API encoding : `GET /System/Configuration/encoding`
4. Sessions : `GET /Sessions`

## Profil Sonarr/Radarr "1080p Direct Play"

Qualités autorisées (Sonarr IDs) :
- 3 : WEBDL-1080p
- 7 : Bluray-1080p
- 15 : WEBRip-1080p

Qualités refusées (partiel) :
- 1 : SDTV | 2 : DVD | 4 : HDTV-720p | 5 : WEBDL-720p
- 6 : Bluray-720p | 9 : HDTV-1080p | 16 : HDTV-2160p
- 17-19 : 2160p (tous) | 30-31 : Remux
