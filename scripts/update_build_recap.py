import json, subprocess

with open('/opt/data/scripts/build_recap_code.js', 'r') as f:
    code = f.read()

# Use the n8n MCP API to update the node
# We'll call the n8n API directly via curl
import urllib.request

# First get the n8n API key from the MCP config
# Actually, let's use the n8n REST API directly
# We need the n8n API key - let's check the workflow directly

# The MCP tool is the way to go - but the inline JSON is too large
# Let's try a different approach: use the n8n API to update the workflow

n8n_url = "https://n8n.jefe.ovh/api/v1/workflows/iRdoNkAhwSAbkeT7"

# We need the API key - let's try without it first (internal access)
# Actually, let's just print the code so we can pass it to the MCP tool
print(f"Code length: {len(code)} chars")
print("Code is ready to be passed to MCP tool")