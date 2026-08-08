# Shortcut Source Tool — Importer un shortcut sans macOS

## Qu'est-ce que c'est
Un **shortcut iOS** (disponible sur routinehub.co) qui permet de :
- Visualiser/modifier le code source d'un shortcut (plist/JSON/XML)
- **Importer un JSON → créer le shortcut sur l'iPhone**
- Convertir entre formats plist/json
- Copier/coller des actions entre shortcuts

## Installation
1. Ouvrir `routinehub.co/shortcut/5256/` sur l'iPhone
2. Installer **Shortcut Source Tool**
3. Installer aussi **Shortcut Source Helper** (requis)

## Utilisation pour importer un shortcut
1. Récupérer le fichier `.json` du shortcut (via GitHub Actions artifact, Drive, etc.)
2. Ouvrir le fichier → Partager → **Shortcut Source Tool**
3. L'outil lit le JSON et **crée le shortcut directement** dans l'app Raccourcis
4. Pas besoin de signature Apple car tout se passe sur l'appareil

## Avantages
- ✅ Pas de Mac requis
- ✅ Pas de signature
- ✅ Marche sur iOS 18+
- ✅ Fonctionne aussi sur iPadOS/macOS
- ✅ Peut éditer/modifier des shortcuts existants

## Limitations
- Nécessite d'installer 2 shortcuts sur l'iPhone
- L'interface est en anglais
- Les dictionnaires imbriqués peuvent être délicats à importer
