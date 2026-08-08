#!/bin/bash
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
mkdir -p /opt/data/cron/tmp/havre_rental

# Le-Partenaire locations page 1
curl -s -L --max-time 30 -A "$UA" "https://www.le-partenaire.fr/immobilier/location/appartement/le-havre/76600?loyer-max=500&pieces=2" -o /opt/data/cron/tmp/havre_rental/lp_page1.html 2>/dev/null
echo "LP page1: $(wc -c < /opt/data/cron/tmp/havre_rental/lp_page1.html) bytes"

# Jullien & Allix location page
curl -s -L --max-time 30 -A "$UA" "https://www.jullien-allix.fr/annonce/location" -o /opt/data/cron/tmp/havre_rental/ja_page.html 2>/dev/null
echo "JA: $(wc -c < /opt/data/cron/tmp/havre_rental/ja_page.html) bytes"

# Saint Roch Immobilier - location page
curl -s -L --max-time 30 -A "$UA" "https://www.saintrochimmo.com/location/appartement/le-havre/76600" -o /opt/data/cron/tmp/havre_rental/stroch_page.html 2>/dev/null
echo "SaintRoch: $(wc -c < /opt/data/cron/tmp/havre_rental/stroch_page.html) bytes"

# HEUZE Immobilier - location page
curl -s -L --max-time 30 -A "$UA" "https://www.heuze-immo.fr/location/appartement/le-havre/76600" -o /opt/data/cron/tmp/havre_rental/heuze_page.html 2>/dev/null
echo "HEUZE: $(wc -c < /opt/data/cron/tmp/havre_rental/heuze_page.html) bytes"

# LH Immo - annonces page
curl -s -L --max-time 30 -A "$UA" "https://www.lhimmo.com/annonces/" -o /opt/data/cron/tmp/havre_rental/lhimmo_page.html 2>/dev/null
echo "LH Immo: $(wc -c < /opt/data/cron/tmp/havre_rental/lhimmo_page.html) bytes"

# Citya
curl -s -L --max-time 30 -A "$UA" "https://www.citya.com/annonces/location/appartement/le-havre-76351" -o /opt/data/cron/tmp/havre_rental/citya_page.html 2>/dev/null
echo "Citya: $(wc -c < /opt/data/cron/tmp/havre_rental/citya_page.html) bytes"

# SquareHabitat
curl -s -L --max-time 30 -A "$UA" "https://www.squarehabitat.fr/annonces/location/bien/appartement/immobilier/normandie/seine-maritime/le-havre-76600" -o /opt/data/cron/tmp/havre_rental/sqhab_page.html 2>/dev/null
echo "SquareHabitat: $(wc -c < /opt/data/cron/tmp/havre_rental/sqhab_page.html) bytes"

# Orpi
curl -s -L --max-time 30 -A "$UA" "https://www.orpi.com/location-immobiliere-le-havre/louer-appartement/" -o /opt/data/cron/tmp/havre_rental/orpi_page.html 2>/dev/null
echo "Orpi: $(wc -c < /opt/data/cron/tmp/havre_rental/orpi_page.html) bytes"

# Century 21
curl -s -L --max-time 30 -A "$UA" "https://www.century21.fr/annonces/location-appartement/v-le+havre/" -o /opt/data/cron/tmp/havre_rental/c21_page.html 2>/dev/null
echo "C21: $(wc -c < /opt/data/cron/tmp/havre_rental/c21_page.html) bytes"

# Foncia
curl -s -L --max-time 30 -A "$UA" "https://fr.foncia.com/location/le-havre-76" -o /opt/data/cron/tmp/havre_rental/foncia_page.html 2>/dev/null
echo "Foncia: $(wc -c < /opt/data/cron/tmp/havre_rental/foncia_page.html) bytes"

# PAP.fr
curl -s -L --max-time 30 -A "$UA" "https://www.pap.fr/annonce/locations-appartement-le-havre-76600-g43635" -o /opt/data/cron/tmp/havre_rental/pap_page.html 2>/dev/null
echo "PAP: $(wc -c < /opt/data/cron/tmp/havre_rental/pap_page.html) bytes"

# Leboncoin search results page
curl -s -L --max-time 30 -A "$UA" "https://www.leboncoin.fr/cl/locations/cp_le+havre_76600?price=0-500&rooms=2-" -o /opt/data/cron/tmp/havre_rental/lbc_page.html 2>/dev/null
echo "Leboncoin: $(wc -c < /opt/data/cron/tmp/havre_rental/lbc_page.html) bytes"

# SeLoger Centre-ville
curl -s -L --max-time 30 -A "$UA" "https://www.seloger.com/recherche/location/appartement/le-havre-76600/centre-ville-76600/nbh2fr6210" -o /opt/data/cron/tmp/havre_rental/seloger_cv.html 2>/dev/null
echo "SeLoger CV: $(wc -c < /opt/data/cron/tmp/havre_rental/seloger_cv.html) bytes"

# Bien'ici
curl -s -L --max-time 30 -A "$UA" "https://www.bienici.com/recherche/location/le-havre-76600/appartement?prix-max=500&pieces-min=2" -o /opt/data/cron/tmp/havre_rental/bienici_page.html 2>/dev/null
echo "Bienici: $(wc -c < /opt/data/cron/tmp/havre_rental/bienici_page.html) bytes"

echo "=== ALL DOWNLOADS COMPLETE ==="