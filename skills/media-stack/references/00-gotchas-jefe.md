# Media Stack — Field Knowledge (Jefe's Infrastructure)

Savoir terrain absent de la doc officielle, compilé depuis les skills existantes
et sessions passées.

## Hardlinks et mount unique /data

**Les hardlinks nécessitent un SEUL point de montage /data.** Si /data est séparé en
/data/media et /data/downloads (deux volumes Docker différents), les hardlinks sont
impossibles — les fichiers sont copiés, doublant l'espace disque.

Pattern correct (docker-compose):
```yaml
volumes:
  - /mnt/nfs/data:/data    # UN SEUL mount, pas de split
```

Pattern incorrect:
```yaml
volumes:
  - /mnt/nfs/media:/media       # ❌ mount séparé
  - /mnt/nfs/downloads:/downloads  # ❌ mount séparé
```

Voir `servarr__docker-guide.md` section hardlinks pour le schéma complet.

## Permissions PUID/PGID

Tous les conteneurs (*arr, qBittorrent, cross-seed) doivent utiliser les mêmes
PUID/PGID (généralement 1000:1000). Si qBittorrent écrit avec un UID différent,
les *arr ne peuvent pas importer (permissions denied).

Vérifier:
```bash
ls -n /data/downloads/  # Vérifier l'UID propriétaire
id  # Sur le host
```

## NFS jNas -> AX42

TODO — Documenter le passage du NAS jNas au serveur AX42:
- Paths avant: /mnt/jnas/data
- Paths après: TODO (vérifier montage AX42)
- Impact sur la config *arr (root folder), qBittorrent (save path), cross-seed (data dirs)
- Vérifier que le mount NFS reste un seul /data pour préserver les hardlinks

## Recyclarr et TRaSH Guides sync

Recyclarr synchronise automatiquement les Custom Formats et Quality Profiles
depuis TRaSH Guides vers Sonarr/Radarr. Le fichier de config `recyclarr.yml`
définit quelles configs synchroniser.

**Important**: Recyclarr utilise des "trash IDs" pour matcher les CF. Si un CF
est renommé dans TRaSH Guides, Recyclarr le détecte via l'ID, pas le nom.

TODO: Documenter le recyclarr.yml exact de Jefe (quelles sync actives, quels
profiles, quels tags).

## TRaSH Guides — Custom Formats français

TRaSH Guides propose des profils français (French EN audio, French FR audio).
Pour les releases VOSTFR/VF, utiliser:
- `sonarr-setup-quality-profiles-french-fr.md` (VOSTFR + FR subs)
- `radarr-setup-quality-profiles-french-fr.md` (VF + VOSTFR)

TODO: Documenter quels CF français sont activés dans la config Recyclarr de Jefe.

## Recyclarr et CF Groups

Recyclarr v6+ supporte les CF Groups (groupes de custom formats opt-in).
Un CF Group permet d'activer/désactiver un ensemble de CF en une seule ligne
dans recyclarr.yml. Voir `recyclarr__decisions__product__005-cf-group-opt-in-semantics.md`.

## Torrents hybrides v1+v2

qBittorrent 5.x (libtorrent 2.x) rejette certains torrents hybrides BitTorrent v1+v2.
Les *arr peuvent marquer ces releases comme failed sans erreur explicite.
Solution: désactiver les torrents hybrides dans qBittorrent ou utiliser un client
alternatif. Voir aussi `00-gotchas-jefe.md` dans la skill `torrent-vpn`.

## TODO: Hardlinks sur NFS

Les hardlinks fonctionnent sur NFS SI le serveur NFS exporte le filesystem avec
`no_root_squash` et que les deux paths (media + downloads) sont sur le même
export NFS. Vérifier la config NFS du jNas/AX42:
```bash
cat /etc/exports | grep data
mount | grep nfs | grep data
```
TODO: Confirmer que les hardlinks fonctionnent réellement sur le montage NFS actuel.