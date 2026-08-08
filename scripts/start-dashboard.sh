#!/bin/bash
# Start Hermes Dashboard on 0.0.0.0:9120 with basic auth + OIDC
# PYTHONPATH override loads patched files from /opt/data/hermes_patch/
# (adds /app-connect endpoint for iOS app authentication)
export HOME=/opt/data
. /opt/hermes/.venv/bin/activate

export HERMES_DASHBOARD=1
export HERMES_DASHBOARD_SESSION_TOKEN="Pc51WZGHJTDR3rliEgvppHEXwjPBr+v311rkZYCA/9g="

# PYTHONPATH: patched hermes_cli takes priority over installed version
export PYTHONPATH="/opt/data/hermes_patch:/opt/hermes:${PYTHONPATH:-}"

exec hermes dashboard --host 0.0.0.0 --port 9120 --no-open