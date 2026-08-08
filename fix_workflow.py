import sqlite3, json

conn = sqlite3.connect('/tmp/n8n.db')
cur = conn.cursor()

# Get current workflow
cur.execute("SELECT id, name, nodes, connections FROM workflow_entity WHERE name='My workflow 4'")
row = cur.fetchone()
wf_id = row[0]
nodes = json.loads(row[2])
connections = json.loads(row[3])

# Replace AI Agent with Basic LLM Chain - simple chat without tools
# Keep the chat trigger and OpenAI Chat Model
# Change the AI Agent node to a Basic LLM Chain
for n in nodes:
    if n.get("type") == "@n8n/n8n-nodes-langchain.agent":
        # Replace with Basic LLM Chain
        n["type"] = "@n8n/n8n-nodes-langchain.chainLlm"
        n["typeVersion"] = 1.4
        n["name"] = "Basic LLM Chain"
        n["parameters"] = {
            "promptType": "auto",
            "text": "={{ $json.message }}",
            "options": {
                "systemMessage": "You are a helpful assistant."
            }
        }
        print(f"Changed AI Agent -> Basic LLM Chain")
    
    # Make sure OpenAI Chat Model has the model field set
    if n.get("type") == "@n8n/n8n-nodes-langchain.lmChatOpenAi":
        n["parameters"]["model"]["value"] = "hermes-agent"
        n["parameters"]["model"]["mode"] = "string"
        print(f"Set model to hermes-agent")

# Update connections: Chat trigger -> Basic LLM Chain, OpenAI Chat Model -> Basic LLM Chain
new_connections = {
    "When chat message received": {
        "main": [
            [
                {
                    "node": "Basic LLM Chain",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "OpenAI Chat Model": {
        "ai_languageModel": [
            [
                {
                    "node": "Basic LLM Chain",
                    "type": "ai_languageModel",
                    "index": 0
                }
            ]
        ]
    }
}

# Update the workflow
cur.execute(
    "UPDATE workflow_entity SET nodes = ?, connections = ? WHERE id = ?",
    (json.dumps(nodes), json.dumps(new_connections), wf_id)
)
conn.commit()
print(f"\nWorkflow updated: {wf_id}")
print(f"Nodes: {[n['name'] + ' (' + n['type'] + ')' for n in nodes]}")

conn.close()