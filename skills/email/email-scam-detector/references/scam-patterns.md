# Patterns d'arnaque connus

Catalogue des patterns spécifiques avec exemples concrets observés.

## 1. Faux suivi de colis (Package Delivery Scam)

**Le plus courant sur les boîtes françaises.**

### Structure
- **Expéditeur :** Nom générique ("Suivre-votre-colis", "LivraisonColis", "Chronopost-Suivi", "Colis-Livraison")
- **Domaine :** Jetable ou bizarre — `sjdckguqt.us`, `livraison-colis.xyz`, `suivi-colis.cc`
- **Sujet :** "Vous avez (1) colis en attente de livraison", "Livraison suspendue"
- **Corps :** Logo de marque volé, image de carton, "LIVRAISON SUSPENDUE", lien vers fake page de suivi
- **But :** Voler infos bancaires via faux frais de livraison

### Exemple réel (23 juil. 2026 — prendizef59)
```
De: Suivre-votre-colis uILVstjy(sjdckguqt.us
Sujet: prendizef59, Vous avez (1) colis en attente de livraison ads
Logo: "LivraisonColis" (Livraison en bleu, Colis en orange)
Texte: "LIVRAISON DU COLIS SUSPENDU !"
```

**Red flags :**
- Expéditeur avec parenthèses et caractères aléatoires : `uILVstjy(sjdckguqt.us`
- Sujet contenant l'adresse email du destinataire (personnalisation basique)
- "ads" ajouté au sujet (marqueur de campagne publicitaire/spam)
- Domaine `.us` avec suite de caractères aléatoires
- Aucun numéro de suivi réel, aucun transporteur identifiable

### Variantes
- "Colis bloqué à la douane — frais à régler"
- "Tentative de livraison échouée — cliquez pour reprogrammer"
- "Frais de stockage à payer — 2,99€"
- Imitation Chronopost/La Poste/Mondial Relay/DPD/UPS

## 2. Faux support technique (Tech Support Scam)

### Structure
- **Expéditeur :** "Microsoft Support", "Apple Security", "Google Account"
- **Sujet :** "Activité suspecte détectée", "Votre compte sera fermé"
- **Corps :** "Nous avons détecté une connexion non autorisée", lien vers fake page de login
- **But :** Voler identifiants (phishing credential harvest)

### Red flags
- Microsoft/Apple/Google ne demandent JAMAIS de saisir mot de passe par email
- Lien ne pointant pas vers le domaine officiel
- Urgence ("dans les 24h")

## 3. Arnaque à l'héritage / Nigeria (Advance Fee Fraud)

### Structure
- **Expéditeur :** Nom aléatoire, souvent prétendument africain/moyen-oriental
- **Sujet :** "Demande urgente d'assistance", "Opportunité d'investissement"
- **Corps :** "Je suis la veuve de...", "J'ai 15 millions de dollars à transférer"
- **But :** Advance fee fraud — demander des frais pour débloquer une somme qui n'existe pas

### Red flags
- Somme importante mentionnée d'emblée
- Demande de confidentialité absolue
- Anglais approximatif ou français traduit machine
- Demande de coordonnées bancaires

## 4. Faux employeur / Offre d'emploi (Job Scam)

### Structure
- **Expéditeur :** "RH", recruteur avec nom aléatoire
- **Sujet :** "Offre d'emploi", "Travail à domicile", "Opportunité"
- **Corps :** Proposition de travail facile et bien rémunéré, demande de infos personnelles
- **But :** Vol d'identité ou avance de frais ("frais de formation")

### Red flags
- Salaire disproportionné pour la tâche décrite
- Aucune entreprise identifiable ou entreprise inexistante
- Demande de scan de pièce d'identité

## 5. Faux remboursement / Impôt (Tax/Refund Scam)

### Structure
- **Expéditeur :** "Impôts Service", "DGFiP", "URSSAF"
- **Sujet :** "Remboursement en attente", "Crédit d'impôt disponible"
- **Corps :** "Vous êtes éligible à un remboursement de XXX€", lien vers formulaire
- **But :** Voler infos bancaires

### Red flags
- La DGFiP ne notifie JAMAIS un remboursement par email avec lien
- Montant précis affiché pour crédibiliser
- Lien vers un domaine non-gouvernemental

## 6. Faux service bancaire (Bank Phishing)

### Structure
- **Expéditeur :** Imitation banque (BNP, SG, CA, LCL, Revolut, etc.)
- **Sujet :** "Connexion suspecte", "Carte bloquée", "Vérification requise"
- **Corps :** "Votre compte présente une activité inhabituelle", lien vers fake login
- **But :** Voler identifiants bancaires

### Red flags
- Banque ne demande jamais de re-saisir mot de passe par email
- Lien ne pointant pas vers le domaine officiel de la banque
- Urgence ("sous 24h compte bloqué")

## 7. Faux concours / Loterie (Lottery Scam)

### Structure
- **Expéditeur :** "Lottery Winner Notification", "Promo Microsoft/Apple/Google"
- **Sujet :** "Félicitations ! Vous avez gagné"
- **Corps :** "Votre email a été sélectionné", demande de frais de transfert
- **But :** Advance fee fraud

### Red flags
- Gagné à un concours auquel on n'a pas participé
- Demande de payer des frais pour recevoir le gain
- Adresse email au lieu de nom complet

## 8. Faux VPN / Antivirus (Security Scam)

### Structure
- **Expéditeur :** "NordVPN Security", "Kaspersky Alert", "Your Antivirus"
- **Sujet :** "Votre appareil est infecté", "Renouvellement requis"
- **Corps :** Fake alerte de sécurité, lien vers renewal/achat
- **But :** Vente de faux logiciel ou vol de carte

### Red flags
- Pas de relation client établie avec le service
- Urgence et peur (technique du scareware)

## 9. Email de blackmail / Chantage (Sextortion)

### Structure
- **Expéditeur :** Varié, souvent avec un mot de passe ancien en preuve
- **Sujet :** "Je sais ce que tu as fait", "Vidéo compromettante"
- **Corps :** Prétend avoir hacké la webcam, demande Bitcoin
- **But :** Extortion de cryptomonnaie

### Red flags
- Mot de passe ancien/fuité affiché pour crédibiliser
- Menace de diffusion à des contacts
- Adresse Bitcoin fournie
- Ne JAMAIS payer — c'est du bluff dans 99% des cas

## 10. Faux investissement / Crypto (Investment Scam)

### Structure
- **Expéditeur :** "Trading Bot", "Crypto Advisor", nom d'influenceur usurpé
- **Sujet :** "Opportunité crypto", "Retour garanti 300%"
- **Corps :** Promesse de gains garantis, lien vers plateforme fake
- **But :** Vol de fonds crypto ou identifiants exchange

### Red flags
- Retours garantis = arnaque garantie
- Pas de risque mentionné
- Pression temporelle ("plus que 3 places")

---

## Détection rapide par mots-clés

### Sujets suspects (FR)
```
colis en attente, livraison suspendue, colis bloqué, frais de livraison
remboursement d'impôt, crédit d'impôt, DGFiP, impots.gouv
compte bloqué, vérification requise, connexion suspecte
vous avez gagné, loterie, félicitations
héritage, transfert de fonds, assistance urgente
votre appareil est infecté, renouvellement antivirus
vidéo compromettante, je sais ce que
```

### Sujets suspects (EN)
```
package delivery, shipment suspended, customs fee
account suspended, verify your account, security alert
you have won, lottery, congratulations
inheritance, transfer funds, urgent assistance
your device is infected, antivirus renewal
compromising video, I know what
guaranteed return, crypto opportunity, trading bot
```

### Domaines suspects — patterns regex
```
*\.xyz, *\.click, *\.top, *\.icu, *\.biz (TLD à risque)
*suivi-colis*, *livraison*, *colis-track* (faux suivi)
*paypa1*, *arnaz0n*, *micros0ft* (typosquatting)
*\d{5,}@* (nombres dans l'adresse)
```