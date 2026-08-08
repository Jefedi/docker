#!/bin/bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
mkdir -p /opt/data/tmp/havre
fetch() {
  url="$1"; out="$2"
  curl -s -A "$UA" -L --max-time 30 "$url" -o "$out"
  echo "Fetched $out ($(wc -c < "$out") bytes)"
}
export -f fetch
export UA

fetch "https://www.leboncoin.fr/cl/locations/cp_le+havre_76600?price=0-500&rooms=2-" /opt/data/tmp/havre/lbc.html &
fetch "https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?loyer-max=500&pieces=2" /opt/data/tmp/havre/lp.html &
fetch "https://www.pap.fr/annonce/locations-appartement-le-havre-76600-g43635" /opt/data/tmp/havre/pap.html &
fetch "https://www.citya.com/annonces/location/appartement/le-havre-76351" /opt/data/tmp/havre/citya.html &
fetch "https://fr.foncia.com/location/le-havre-76" /opt/data/tmp/havre/foncia.html &
fetch "https://www.seloger.com/recherche/location/appartement/le-havre-76600/centre-ville-76600/nbh2fr6210" /opt/data/tmp/havre/seloger_cv.html &
fetch "https://www.seloger.com/recherche/location/appartement/le-havre-76600/sanvic-76620/nbh2fr6214" /opt/data/tmp/havre/seloger_sanvic.html &
fetch "https://www.seloger.com/recherche/location/appartement/le-havre-76600/bleville-76620/nbh2fr6221" /opt/data/tmp/havre/seloger_ble.html &
fetch "https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600" /opt/data/tmp/havre/sqhab.html &
fetch "https://www.century21.fr/annonces/location-appartement/v-le+havre/" /opt/data/tmp/havre/c21.html &
fetch "https://www.orpi.com/location-immobiliere-le-havre/louer-appartement/" /opt/data/tmp/havre/orpi.html &
fetch "https://www.lhimmo.com" /opt/data/tmp/havre/lhimmo_home.html &
fetch "https://www.heuze-immo.fr" /opt/data/tmp/havre/heuze_home.html &
fetch "https://www.saintrochimmo.com" /opt/data/tmp/havre/stroch_home.html &
fetch "https://www.jullien-allix.fr/annonce/location" /opt/data/tmp/havre/ja.html &
fetch "https://www.bienici.com/recherche/location/le-havre-76600/appartement?prix-max=500&pieces-min=2" /opt/data/tmp/havre/bienici.html &
wait
echo "ALL DONE"
ls -la /opt/data/tmp/havre/