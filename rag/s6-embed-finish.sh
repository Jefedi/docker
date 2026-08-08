#!/command/with-contenv sh
# shellcheck shell=sh
# $1 = exit code from the run script.
# Exit 125 = permanent failure, don't restart
if [ "$1" = "78" ]; then
  exit 125
fi
exit 0