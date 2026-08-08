# Pangolin Cleanup Notes

## API Key Situation

The Pangolin MCP (mcp-pangolin) is registered in Hermes config at:
`/root/.hermes/config.yaml → mcp.pangolin`

Current state:
- `enabled: false` — MCP tools not exposed to agent
- `command: /root/mcp-pangolin/run.sh` — runs Rust binary with API key at runtime
- `env.PANGOLIN_API_KEY: e0411i...upd3` — appears truncated/redacted in config.yaml
- Base URL: `https://api.jefe.ovh/v1` (from run.sh)

The binary resolves the full key at runtime when MCP is enabled. The truncated value in config is a Hermes quirk — the real key is passed to the process at spawn time.

## How to Check Resources Without MCP

If MCP is disabled and you need to query the API:

```bash
# You need the REAL API key from the user or from enabling the MCP
# The truncated key in config.yaml won't work with curl

# List all resources
curl -sk "https://api.jefe.ovh/v1/org/jefe/resources" \
  -H "x-api-key: <REAL_KEY>"

# Delete by resource ID
curl -sk -X DELETE "https://api.jefe.ovh/v1/org/jefe/resource/<RESOURCE_ID>" \
  -H "x-api-key: <REAL_KEY>"
```

## Temporary Enable Pattern

To use the Pangolin MCP tools (instead of curl):
1. Edit config.yaml: set `enabled: true` under `mcp.pangolin`
2. The MCP server starts and exposes 157 tools
3. Use the tools for resource CRUD
4. Set back to `enabled: false` when done

## Resource-to-Container Mapping

Deleting a Docker container does NOT delete the Pangolin resource. They are independent:
- Container lives on the Docker host
- Resource lives in Pangolin API + SQLite DB
- DNS entry (jefe.ovh) is managed separately by Pangolin

Both must be removed separately.
