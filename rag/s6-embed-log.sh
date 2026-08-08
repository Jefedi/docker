#!/command/with-contenv sh
# shellcheck shell=sh
# s6-log → $HERMES_HOME/logs/embed-service/
: "${HERMES_HOME:=/opt/data}"
log_dir="$HERMES_HOME/logs/embed-service"
mkdir -p "$log_dir"
chown hermes:hermes "$log_dir" 2>/dev/null || true
rm -f "$log_dir/lock"
[ "$(id -u)" = 0 ] || exec s6-log 1 n10 s1000000 T "$log_dir"
exec s6-setuidgid hermes s6-log 1 n10 s1000000 T "$log_dir"