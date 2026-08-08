# Dashboard Hermes loopback derrière Pangolin

## Contexte

Le dashboard Hermes protège contre le DNS rebinding : quand il est lié à `127.0.0.1`, il n’accepte que les en-têtes Host loopback. Un reverse proxy Pangolin envoie normalement `Host: <domaine-public>`, ce qui produit :

```text
HTTP 400
Invalid Host header. Dashboard requests must use the hostname the server was bound to.
```

Ne pas contourner ce contrôle en liant le dashboard à `0.0.0.0` lorsque la politique est de garder les services en loopback.

## Architecture

```text
Pangolin → 127.0.0.1:8999 (proxy local, loopback)
             → 127.0.0.1:9119 (dashboard Hermes, loopback)
```

Le proxy reçoit la première requête HTTP, remplace seulement `Host:` par `127.0.0.1:9119`, puis relaie le flux TCP dans les deux sens. Après le handshake cela couvre HTTP, SSE et WebSockets sans interpréter le trafic.

## Vérification

1. Vérifier le dashboard :
   ```bash
   curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9119/api/status
   ```
   Attendu : `200`.
2. Démarrer le proxy sur une autre adresse loopback, par exemple `127.0.0.1:8999`.
3. Vérifier la normalisation Host :
   ```bash
   curl -sS -o /dev/null -w '%{http_code}\n' \
     -H 'Host: hermes.example.com' http://127.0.0.1:8999/api/status
   ```
   Attendu : `200`.
4. Dans Pangolin, garder l’IP `127.0.0.1`, le mode HTTP, et changer seulement le port cible vers celui du proxy.
5. Tester l’URL publique. Un 502 signifie encore que le dashboard/proxy est indisponible ; un 400 Host signifie que la réécriture n’est pas appliquée.

## Exploitation

Le proxy doit être géré par un superviseur (systemd ou s6) plutôt que par un shell temporaire. Ne modifiez pas la cible Pangolin avant que le test local avec un Host public n’ait renvoyé 200.
