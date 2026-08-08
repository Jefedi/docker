# Hermes iOS — Améliorations ergonomie mobile

## Fichiers créés/modifiés

### 1. `apps/desktop/src/ios/ios-gestures.ts` (NOUVEAU)
Couche de gestures tactile qui s'installe sans modifier les composants React existants.

**Gestures implémentés :**
- **Swipe droite depuis le bord gauche** → ouvrir la sidebar (sessions)
- **Swipe gauche depuis le bord droit** → ouvrir le file browser
- **Swipe gauche quand la sidebar est ouverte** → fermer la sidebar
- **Swipe droite quand le file browser est ouvert** → fermer le file browser
- **Swipe vers le bas depuis le haut** → fermer tout overlay ouvert
- **Tap sur le scrim** (zone sombre derrière un drawer) → fermer l'overlay

**Comment ça marche :**
- Écoute `touchstart`/`touchmove`/`touchend` sur `document` (passive)
- Détecte le bord de départ (28px depuis le bord), la direction et la vélocité
- Dispatche `PANE_TOGGLE_REVEAL_EVENT` — le même événement que les boutons titlebar et les raccourcis clavier utilisent déjà
- Synchronise `data-ios-drawer-open` sur `<body>` via `$sidebarOpen.listen()` pour que le CSS affiche/masque le scrim

**Seuils (calibrés sur les HIG Apple) :**
- Distance minimum : 50px (ou vélocité > 0.4px/ms pour un flick rapide)
- Dérive verticale max : 60px (évite les faux positifs avec le scroll vertical)
- Durée max : 600ms
- Zone de bord : 28px

### 2. `apps/desktop/src/ios/ios-keyboard.ts` (NOUVEAU)
Gestion du clavier logiciel iOS via `visualViewport` API.

- Détecte la hauteur du clavier en comparant `window.innerHeight` avec `visualViewport.height`
- Set `--keyboard-height` sur `<body>` → le CSS offset le composer vers le haut
- Toggle `data-ios-keyboard-open` pour les ajustements CSS
- Scroll la message list vers le bas à l'ouverture du clavier
- Fallback `window.innerHeight` pour les anciens iOS sans `visualViewport`

### 3. `apps/desktop/src/ios/ios.css` (REMPLACE l'existant)
Améliorations ergonomiques par-dessus le CSS existant (safe-area, tap highlight, statusbar).

**Ajouts :**

**Tap targets (44px minimum) :**
- Boutons titlebar : `min-width/min-height: 44px` (au lieu de 28px)
- Lignes sidebar : 44px de hauteur minimum
- Bouton send/stop du composer : 44px
- Lignes settings : 44px

**Overlay drawers (slide-in) :**
- Sidebar : `position: fixed`, `width: min(85vw, 320px)`, slide depuis la gauche
- File browser : slide depuis la droite
- Transition : `transform 0.28s cubic-bezier(0.32, 0.72, 0, 1)` (courbe iOS native)
- Box-shadow pour la profondeur
- Scrim backdrop (`body::after`) avec `rgba(0,0,0,0.4)` et animation fade-in

**Composer (zone de saisie) :**
- Bottom-anchored avec padding safe-area
- `font-size: 16px` sur le textarea (évite l'auto-zoom iOS au focus)
- `max-height: 35dvh` (grandit avec le contenu jusqu'à 35% de l'écran)
- Padding horizontal avec safe-area

**Message list :**
- `padding-bottom: 6rem` (dégage le composer)
- `overscroll-behavior: contain` (pas de rubber-band)
- Messages en pleine largeur avec padding réduit (0.75rem)

**Font sizes mobile :**
- Base : 15px (densité)
- Code blocks : 13px avec scroll horizontal
- Headings : réduits pour mobile

**Smooth scrolling :**
- `-webkit-overflow-scrolling: touch` sur tous les containers scrollables

### 4. `apps/desktop/src/ios/main.tsx` (REMPLACE l'existant)
Ajoute deux imports : `./ios-gestures` et `./ios-keyboard`, avant `../main`.

## Comment appliquer sur le repo

```bash
# Cloner le fork et checkout la branche iOS
git clone https://github.com/Jefedi/hermes-agent.git
cd hermes-agent
git checkout claude/hermes-gateway-ios-app-r8k0hi

# Copier les 4 fichiers
cp /opt/data/hermes-ios-patch/ios-gestures.ts apps/desktop/src/ios/ios-gestures.ts
cp /opt/data/hermes-ios-patch/ios-keyboard.ts apps/desktop/src/ios/ios-keyboard.ts
cp /opt/data/hermes-ios-patch/ios.css apps/desktop/src/ios/ios.css
cp /opt/data/hermes-ios-patch/main.tsx apps/desktop/src/ios/main.tsx

# Commit + push
git add apps/desktop/src/ios/
git commit -m "feat(ios): mobile ergonomics — swipe gestures, drawers, keyboard awareness, 44px tap targets"
git push origin claude/hermes-gateway-ios-app-r8k0hi
```

## Références UX utilisées

- **Apple HIG** : 44px touch target minimum, swipe-back gesture, safe-area insets
- **ChatGPT iOS** : swipe from left edge to open conversation list sidebar
- **Apple Mail / Notes** : drawer pattern with scrim backdrop, 85% width
- **Gesture-based navigation 2025** : edge gestures > buttons, discoverability via affordance
- **AI chat UX** : composer docked at bottom, full-width messages, keyboard pushes layout