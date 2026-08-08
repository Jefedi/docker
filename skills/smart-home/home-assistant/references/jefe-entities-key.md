# Entités clés — Maison Jefe

Issu de l'audit HA fait le 06/06/2026. Met à jour si de nouvelles entités sont découvertes.

## Présence
- `person.jefe` — Zef (home / not_home)
- `person.alex` — Alex (Home Of Alexia / not_home)
- `sensor.jefe_place` — localisation Zef
- `sensor.alex_place` — localisation Alex

## Lumières
- `light.tapo_l530` — Lumière (Tapo)
- `light.cuisine_alex` — Cuisine Alex (souvent unavailable)
- `light.lsc_led_strip_5m` — LED Strip (souvent unavailable)
- `light.wled` — WLED (souvent unavailable)

## Musique
- `media_player.spotify_jefe` — Spotify Jefe
- `media_player.d5369777_music_assistant` — Music Assistant

## Aspirateur
- `vacuum.petit_filou` — Petit Filou

## Caméras
- `camera.petit_filou_map` — Carte aspirateur
- `camera.petit_filou_map_1` — Carte sauvegardée
- `camera.petit_filou_map_data` — Données carte

## Réseau / DNS
- `switch.jefe` — jTower DNS (on/off)
- `switch.jefe_augmentation_du_cache` — Cache DNS
- `switch.jefe_block_page` — Page de blocage
- `switch.jefe_aplatissement_cname` — Aplatir CNAME
- `switch.freebox_wifi` — Freebox Wi-Fi

## Blocages (switch.jefe_bloquer_*)
Par domaine :
- **Réseaux sociaux** : instagram, facebook, discord, bereal, 9gag, tiktok, imgur, google_chat
- **Streaming** : disney_plus, hbo_max, netflix, youtube, dailymotion, amazon, ebay, spotify
- **Jeux** : fortnite, league_of_legends, blizzard, playstation_network
- **Sensible** : la_pornographie, le_piratage, chatgpt
- **Divers** : hulu, mastodon

Aussi par machine : `switch.jtower_bloquer_*`, `switch.jlaptop_bloquer_*`, `switch.protonvpn_bloquer_*`

## Serveurs
- `binary_sensor.jlaptop_status_2` — jLaptop
- `binary_sensor.jefe_connexion_au_cloud` — jTower Cloud
- `binary_sensor.jnas_status` — jNas
- `binary_sensor.debian_trixie_latest_amd64_base_status` — Debian
- `binary_sensor.hermes_agent_status` — Hermes Agent

## Disques (S.M.A.R.T.)
- `binary_sensor.jlaptop_bc901_s_m_a_r_t_2` — jLaptop SSD
- `binary_sensor.jtower_samsung_s_m_a_r_t` — jTower Samsung
- `binary_sensor.debian_trixie_latest_amd64_base_linux_s_m_a_r_t` — Debian

## Météo & Marées
- `weather.le_havre` — Météo Le Havre
- custom:marees-france-card (device_id: ceca8d024095fd74e984795093c3bc99)

## F1
- `binary_sensor.f1_race_week` — Semaine de course active
- `binary_sensor.f1_live_timing_online` — Live Timing en ligne
- `calendar.f1_season_calendar` — Calendrier saison
- `media_player.f1_replay_player` — Replay F1

## Infos
- `sensor.iss` — Astronautes ISS
- `sensor.sun_next_rising` — Prochain lever soleil
- `sensor.sun_next_setting` — Prochain coucher soleil
- `binary_sensor.capteur_de_journee_de_travail` — Jour travaillé
- `binary_sensor.freebox_v8_r1_etat_du_reseau_etendu_wan` — Freebox WAN
- `todo.liste_dachats` — Liste de courses
