---
name: business-prospection
version: 1.0.0
description: Prospection commerciale pour renvoyer des projets d’automatisation et d’infrastructure cloud aux PME/PMI.
---

## Contexte
Jefe a besoin de monétiser ses compétences Docker, n8n, Home‑Assistant, etc. Le profil `business` est dédié à cette activité.

## Offre Packagée
| Offre | Prix | Description |
|---|---|---|
| Stack self‑hosted clé en main | 1500‑5000€ | Docker + reverse proxy (Pangolin) + SSL + monitoring (Uptime Kuma / Grafana) + doc + formation |
| Automatisation sur‑mesure | 800‑3000€ | n8n / Python / API / dashboards |
| Migration cloud → self‑hosted | 2000‑8000€ | Audit + migration progressive + formation |
| Maintenance mensuelle | 200‑500€/mois | Monitoring + MAJ + support |
| Home Assistant tertiaire | 1000‑3000€ | Automatisation bâtiment pour hôtels/restos/bureaux |

## Process de Prospection
1. Identification des cibles (PME 5‑50 employés, région : Le Havre → national). Signaux : SaaS coûteux, site obsolète, absence de SSL.
2. Recherche via `web_search` et annuaires.
3. Email d’approche (template fourni).
4. Suivi pipeline dans `pipeline.md`.
5. Devis – inclus objectifs chiffrés, périmètre, timeline, maintenance.

## Automatisations Réutilisables
- Templates Docker (monitoring, productivité, communication, sauvegarde)
- Scripts (backup, reporting, synchronisation, alerting)

## Rôle du Skill
Cette skill décrit la stratégie commerciale, le pricing et les templates. Elle sert de base pour créer de nouveaux documents de prospection.

**Références additionnelles**
- `references/email_approche_template.md`
- `templates/docker-monitoring.yaml`
- `scripts/reporting.py`

P.S. : La skill doit être utilisée dans le profil `business`.