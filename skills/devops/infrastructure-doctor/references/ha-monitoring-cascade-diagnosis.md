# Diagnostic : Cascade d'unavailable dans le monitoring HA

## Pattern observé

Quand Home Assistant reçoit une **vague** d'événements où plusieurs sondes de monitoring passent simultanément à `unavailable`/`unavailabled`, la cause la plus probable est une **panne de la couche de monitoring** (Beszel, Uptime Kuma, Pangolin Event Streaming), **pas** une panne des services réels.

## Signaux distinctifs

### ❌ Monitoring-layer flapping (pas un vrai problème)
- Plusieurs sondes **de types différents** (response time, uptime, certificats, statut HTTP) passent à unavailable **dans la même fenêtre de quelques minutes**
- Les certificats SSL deviennent `unavailabled` — les certificats n'expirent jamais tous en même temps
- Les monitors Docker (beszel-agent) tombent en même temps que les monitors HTTP
- **Les indicateurs indépendants** (Freebox uptime, jTower consommation/tension/courant, horloges des appareils) restent normaux
- Les monitors reviennent spontanément après quelques minutes, sans intervention
- Le pattern se répète en vagues (plusieurs vagues sur 30-60 min)
- Les temps de réponse avant/pendant/après : normaux → disparus (unavailable) → normaux

### ✅ Vrai service down
- Un seul service ou famille cohérente de services (ex: tous les services Pangolin mais pas les monitors système)
- Les indicateurs hardware/physiques (Freebox, jTower) sont également touchés
- Le service ne revient pas spontanément en 1-2 minutes
- Le certificat SSL est vraiment expiré (vérifiable avec openssl)

## Workflow de diagnostic

```python
# 1. Vérifier les services physiques/indépendants
# Ceux-ci ne passent pas par la couche de monitoring Beszel/Pangolin
ha_get_state("sensor.freebox_v8_r1_temps_de_fonctionnement")
ha_get_state("sensor.jtower_pc_consommation_actuelle")
ha_get_state("sensor.jtower_pc_tension")

# 2. Vérifier les certificats d'au moins 2 services différents
# Un certificat qui revient à "80d" ou "unavailabled" confirme que la sonde CertMon est instable
ha_get_state("sensor.seerr_expiration_du_certificat")
ha_get_state("sensor.n8n_expiration_du_certificat")

# 3. Vérifier un monitor Docker (beszel-agent) — tombe en premier
ha_get_state("sensor.docker_beszel_uptime_1_day")

# 4. Vérifier un service HTTP directement (via curl)
curl -s -o /dev/null -w "%{http_code}:%{time_total}" https://service.domaine.tld/
```

## Fausses pistes fréquentes

- **Uptime 365 jours qui chute** : C'est juste le calculateur qui intègre les « 0% » des périodes où la sonde était indisponible. L'uptime réel du service n'a pas changé, c'est la sonde qui n'a pas collecté de données.
- **Temps de réponse à 0ms → unavailablems** : La sonde ne rapporte plus rien → moyenne inclut des trous.
- **Spike de temps de réponse (2000ms+) en pleine vague** : C'est le monitoring qui ralentit, pas le service. Vérifier avec curl direct.

## Réponse appropriée

Quand le diagnostic confirme une vague monitoring :
- Réponse brève : « Même motif — monitoring layer flapping, services réels sains. »
- Ne pas investiguer chaque entité individuellement
- Si les vagues persistent > 1h ou deviennent quotidiennes, proposer de regarder les logs de Beszel/Uptime Kuma

## Signaux avancés — corrélation des métriques Pangolin

Pendant les vagues monitoring, **Pangolin lui-même montre des signes de charge** :

- ⬆️ **CPU Pangolin** : peut doubler (ex: 14% → 27%) pendant la vague
- ⬆️ **RAM Pangolin** : peut grimper de 4-5 points (ex: 54% → 58%)
- ⬆️ **Bandwidth Pangolin** : passe de ~0.1 MB/s à 5-6 MB/s (les sondes qui rapatrient toutes les données en rafale)
- ⬆️ **Disk Pangolin** : peut s'incrémenter de 0.1-0.2%

Ces corrélations confirment que la **couche de monitoring Pancake/Pangolin probes** est à l'origine du flapping, et aide à distinguer d'une cause externe (réseau, DNS upstream).

## Variantes du suffixe « unavailable »

Le monitoring utilise le suffixe correspondant au type de la métrique :
- `unavailablems` — temps de réponse (numérique en ms)
- `unavailable%` — pourcentage (uptime)
- `unavailabled` — jours (certificats)
- `unavailabletags` — compteur de tags (FiveM/jeux)
- `unavailable` — statut textuel (up/down → unavailable)

Tous ces suffixes apparaissent simultanément pendant une vague, ce qui est un fort indicateur de monitoring-layer flapping plutôt que de problème métier.

## Causes possibles (si les vagues persistent)

- Surcharge passagère des sondes Pangolin / Beszel Hub / Uptime Kuma
- Tick cron surchargé ou contention sur la base de sondes
- Instabilité réseau du serveur (checker iowait, load, RAM avec `top -bn1`, `free -h`, `iostat -x 1 3`)
- Problème DNS transitoire (toutes les sondes DNS passent unavailable en même temps)
- Contention sur les métriques Pangolin elles-mêmes (CPU/RAM/bandwidth Pangolin corrélés)
