#!/bin/bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

curl -s -L --max-time 15 -A "$UA" "https://www.seloger.com/recherche/location/appartement/le-havre-76600/centre-ville-76600/nbh2fr6210" -o /tmp/seloger_cv.html &
curl -s -L --max-time 15 -A "$UA" "https://www.citya.com/annonces/location/appartement/le-havre-76351" -o /tmp/citya.html &
curl -s -L --max-time 15 -A "$UA" "https://fr.foncia.com/location/le-havre-76" -o /tmp/foncia.html &
curl -s -L --max-time 15 -A "$UA" "https://www.century21.fr/annonces/location-appartement/v-le+havre/" -o /tmp/c21.html &
curl -s -L --max-time 15 -A "$UA" "https://www.orpi.com/location-immobiliere-le-havre/louer-appartement/" -o /tmp/orpi.html &
curl -s -L --max-time 15 -A "$UA" "https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600" -o /tmp/sqhab.html &
curl -s -L --max-time 15 -A "$UA" "https://www.lhimmo.com" -o /tmp/lhimmo.html &
curl -s -L --max-time 15 -A "$UA" "https://www.heuze-immo.fr" -o /tmp/heuze.html &
curl -s -L --max-time 15 -A "$UA" "https://www.jullien-allix.fr/annonce/location" -o /tmp/ja.html &
curl -s -L --max-time 15 -A "$UA" "https://www.saintrochimmo.com" -o /tmp/stroch.html &
curl -s -L --max-time 15 -A "$UA" "https://www.bienici.com/recherche/location/le-havre-76600/appartement?prix-max=500&pieces-min=2" -o /tmp/bienici.html &
wait

echo "=== File sizes ==="
for f in /tmp/seloger_cv.html /tmp/citya.html /tmp/foncia.html /tmp/c21.html /tmp/orpi.html /tmp/sqhab.html /tmp/lhimmo.html /tmp/heuze.html /tmp/ja.html /tmp/stroch.html /tmp/bienici.html; do
    if [ -f "$f" ]; then
        sz=$(wc -c < "$f")
        echo "$f: ${sz} bytes"
    else
        echo "$f: NOT FOUND"
    fi
done