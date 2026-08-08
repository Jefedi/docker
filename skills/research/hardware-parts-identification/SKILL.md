---
name: hardware-parts-identification
description: Identify mechanical/hardware parts from user-submitted photos, with emphasis on French building hardware (shutters, locks, doors, windows, garage mechanisms).
triggers:
  - User sends photos of a mechanical/hardware part asking "what is this" or "find me the same model"
  - User asks to identify an unknown hardware component from images
  - User needs to find a replacement part for broken hardware
---

# Hardware Parts Identification from Photos

## 🚨 FIRST STEP: ASK FOR CONTEXT

Before trying to identify anything from photos, ALWAYS ask:
1. **"Ça vient de quoi ?"** / "What is this from?" — door, window, roller shutter, garage door, gate, cabinet, vehicle?
2. **"C'est cassé ? Tu cherches une pièce de rechange ?"** — replacement vs identification
3. **"Tu as la clé ?"** — if a lock/cylinder, the key shape identifies the brand instantly
4. **"Y a-t-il des marquages ? Logo ? Chiffres ?"** — often on the hidden side

## Key Distinctions: French Building Hardware

### Roller Shutter vs Door Lock Cylinders

| Feature | Sortie de caisson (roller shutter) | Verrou/barillet (door lock) |
|---------|------------------------------------|----------------------------|
| Tige | Longue tige carrée (8mm) ou hexagonale (7mm) | Courte, entraîneur plat ou carré |
| Platine | Rectangulaire, 2 ou 4 trous | Ronde ou rectangulaire compacte |
| Embout supérieur | Cardan/rotule/genouillère articulé(e) | Clé/keyhole ou bouton |
| Usage | Relie manivelle au treuil dans le coffre | Verrouille la porte |
| Marques courantes | Bubendorff, Somfy, Geiger, ZF | Fichet, Muel, Vak, Mottura, Vachette |

### Common Roller Shutter Parts (France)

- **Sortie de caisson** (cardan/genouillère) — connects crank handle to winding mechanism. Key specs: angle (45°/90°), tige shape (carré 6/8mm, hexagonal 7mm, rond 12mm), platine dimensions
- **Déport de manœuvre** — offset mechanism for tricky installations (Bubendorff Bloc R)
- **Treuil** — the winding winch inside the shutter box
- **Verrou à pompe** — pump lock for roller shutter, often with rectangular plate + 2 holes
- **Bloc guide / Tulipe** — wall-mounted guide for the crank rod
- **Manivelle** — the crank handle itself

### Common Door Lock Cylinders (France)

- **Muel / Vak** — 8 gorges 1 pompe, rectangular plate, used on blindé doors
- **Fichet 787** — monobloc with 2 "ears" for screws, pump key
- **Mottura** — garage door or security door, pump or reversible key
- **Bubendorff (volet roulant manuel)** — specific pump key system, rectangular plate

## Photos Analysis Protocol

1. **Analyze each photo independently** with vision_analyze, asking for:
   - Shape of rod (square/round/hexagonal)
   - Type of plate (rectangular/round, number of screw holes)
   - Any markings/logos/numbers
   - Material, rust, wear patterns
2. **Look for connected parts** — if one photo shows a cylinder with a rod extending, confirm they're the same assembly
3. **Synthesize across photos** to determine if it's one or several parts
4. **Ask clarifying questions** before searching — saves 5+ rounds of wrong guesses

## Search Strategy

When searching for a part:
1. Use French keywords for French hardware (even if the user writes in English)
2. Search specific dimensions: `"sortie de caisson" "carré 8" platine 2 trous`
3. Check these sites: Castorama.fr, LeroyMerlin.fr, toutpourlesvolets.com, pieces-volets-roulants.fr, servistores-sud.com, lacentrale-eco.com, serrures-cyc.com
4. For locks: serrures-cyc.com, bricoserrure.fr, a2pro.com

## Pitfalls to Avoid

- ❌ Don't assume a cylinder with a rod is a door lock — roller shutter sorties de caisson look similar
- ❌ Don't search for products without first asking the user what type of equipment it's from
- ❌ Don't guess the brand from the shape alone — pump cylinders look similar across brands
- ✅ Always ask for the KEY if it's a lock — key shape = instant brand identification
- ✅ Always ask for DIMENSIONS (entraxe des trous, longueur de tige, section)
