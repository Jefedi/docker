#!/bin/bash
export LANGFLOW_SERVER_URL="https://langflow.jefe.al"
exec uvx --from lfx lfx-mcp "$@"