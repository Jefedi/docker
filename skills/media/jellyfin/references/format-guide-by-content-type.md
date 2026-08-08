# Format Guide by Content Type

Research synthesis from TRaSH Guides, Dictionarry, Reddit (r/trackers, r/PleX), forums Sonarr, and community consensus (2025-2026).

## 1. Films (Movies)

| Source | Format | Compatibilité |
|--------|--------|---------------|
| WEB-DL x264 | H.264 8bit ~8-15 GB | ✅ Universelle |
| Bluray x264 | H.264 8bit ~15-30 GB | ✅ Universelle |
| WEB-DL x265 | H.265 10bit ~3-8 GB | ❌ Firefox/anciens |
| Bluray x265 | H.265 10bit ~6-15 GB | ❌ Firefox |

**Règle TRaSH** : x265 bloqué en HD (score -10000) — micro-encodes de mauvaise qualité fréquents. Exception : 4K HDR/DV.

## 2. Séries (Live Action)

| Format | Taille/ép | Verdict |
|--------|-----------|---------|
| WEB-DL x264 | ~1.4-2 GB | ✅ Meilleur équilibre |
| WEBRip x264 | ~0.8-1.5 GB | ⚠️ Re-encode, artefacts |
| x265 | ~0.5-1 GB | ❌ Trop petit, peu compatible |

## 3. Animés (Anime)

| Format | Taille/ép | Compatibilité | Qualité |
|--------|-----------|---------------|---------|
| x264 8bit (Tsundere-Raws, VARYG) | ~1.4 GB | ✅ Universelle | ✅ Bonne |
| x265 10bit (Judas, ASW, Anime Time) | ~300-500 MB | ❌ Firefox, TVs | 🏆 Excellente |

**Pourquoi x265 10bit > x264 pour l'anime :**
- Les aplats de couleur unis (ciel, murs, fonds) créent du banding en 8bit
- 10bit réduit le banding de ~20%
- x265 compresse 50-70% mieux les zones plates
- Consensus des groupes encodeurs anime (Judas, ASW)

**Mais x264 reste le safer bet** si Firefox ou TV anciennes dans l'audience.

## 4. TRaSH Profile Notes

### HD Bluray + WEB (séries/films)
- Qualités : Bluray-720p/1080p, WEB-DL-1080p
- CF requis : Repack/Proper (+5), Repack2 (+6), Repack3 (+7)
- CF bloqués (-10000) : BR-DISK, x265 (HD), LQ, LQ (Release Title), AV1, 3D

### Anime
- Quality settings : wide open (min 5 MB/min)
- TRaSH NE bloque PAS x265 pour l'anime
- Séparer du profil série standard

## 5. Arbre de décision

```text
Animé ?
├── Oui → Firefox dans l'audience ?
│   ├── Oui → x264 MULTi AD (si VF dispo)
│   └── Non → x265 10bit (Judas, ASW)
└── Non → x264 WEB-DL
    ├── HDR ? → x265 4K
    └── SDR → x264 1080p
```
