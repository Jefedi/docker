#!/bin/bash
# Start Hermes Dashboard for remote gateway access (iOS app)
# Bind to 0.0.0.0, basic auth configured in config.yaml (jefe / hermes-admin-2026)
export HOME=/opt/data
. /opt/hermes/.venv/bin/activate

export HERMES_DASHBOARD=1
export HERMES_DASHBOARD_SESSION_TOKEN="Pc51WZGHJTDR3rliEgvppHEXwjPBr+v311rkZYCA/9g="

exec hermes dashboard --host 0.0.0.0 --port 9120 --no-open
