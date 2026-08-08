import urllib.request, json

url = "http://127.0.0.1:9119/v1/chat/completions"
api_key = "hermes-ios-shortcut-a80ac18a29ed5d62"

# Test 1: Basic chat (what Basic LLM Chain does)
print("=== Test 1: Basic chat ===")
payload = {
    "model": "hermes-agent",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Bonjour, ça va ?"}
    ],
    "max_tokens": 200
}
req = urllib.request.Request(url, data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
        choice = result["choices"][0]
        print(f"finish_reason: {choice['finish_reason']}")
        print(f"content: {choice['message'].get('content', '(none)')[:200]}")
        print(f"message keys: {list(choice['message'].keys())}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: With tools (what AI Agent does)  
print("\n=== Test 2: With tools ===")
payload2 = {
    "model": "hermes-agent",
    "messages": [
        {"role": "user", "content": "What's the weather in Paris?"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"]
                }
            }
        }
    ],
    "max_tokens": 200
}
req2 = urllib.request.Request(url, data=json.dumps(payload2).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req2, timeout=60) as resp:
        result = json.loads(resp.read().decode())
        choice = result["choices"][0]
        print(f"finish_reason: {choice['finish_reason']}")
        msg = choice["message"]
        print(f"message keys: {list(msg.keys())}")
        print(f"content: {msg.get('content', '(none)')[:200]}")
        print(f"tool_calls: {msg.get('tool_calls', 'NOT PRESENT')}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: With stream=false and tool_choice="auto"
print("\n=== Test 3: With tool_choice=auto ===")
payload3 = dict(payload2)
payload3["tool_choice"] = "auto"
req3 = urllib.request.Request(url, data=json.dumps(payload3).encode(),
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req3, timeout=60) as resp:
        result = json.loads(resp.read().decode())
        choice = result["choices"][0]
        print(f"finish_reason: {choice['finish_reason']}")
        msg = choice["message"]
        print(f"message keys: {list(msg.keys())}")
        print(f"tool_calls: {msg.get('tool_calls', 'NOT PRESENT')}")
except Exception as e:
    print(f"Error: {e}")