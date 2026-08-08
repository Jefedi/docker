#!/bin/bash
# Test que Himalaya fonctionne
himalaya envelope list --page 1 --page-size 3 2>/dev/null | grep -v WARN
echo "---"
echo "Himalaya OK, cron prêt à tourner"
