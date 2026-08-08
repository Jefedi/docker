import sqlite3, json
conn = sqlite3.connect('/opt/data/scripts/n8n_db.sqlite')
c = conn.cursor()

# Get execution data for exec 248131 (last error with PDF)
c.execute("SELECT data FROM execution_data WHERE executionId = 248131")
row = c.fetchone()
if row:
    raw = row[0]
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw
    
    # The data might be a list or dict
    if isinstance(data, list):
        print(f"Data is a list of {len(data)} items")
        data = data[0] if data else {}
    
    if isinstance(data, dict):
        result = data.get('run_data', {}).get('resultData', {})
        error = result.get('error', {})
        print(f"ERROR NODE: {error.get('node', {}).get('name', '?')}")
        print(f"ERROR MSG: {error.get('message', '?')}")
        
        run_data = result.get('runData', {})
        for node_name, runs in run_data.items():
            for run in runs:
                status = 'ERROR' if run.get('error') else 'ok'
                print(f"  Node: {node_name} -> {status}")
                if run.get('error'):
                    print(f"    Error: {run['error'].get('message', '?')[:500]}")
                
                if run.get('data') and run['data'].get('main'):
                    for i, output in enumerate(run['data']['main']):
                        if output:
                            for j, item in enumerate(output[:2]):
                                json_data = item.get('json', {})
                                binary_data = item.get('binary', {})
                                print(f"    Output[{i}][{j}] json keys: {list(json_data.keys())}")
                                if binary_data:
                                    print(f"    Output[{i}][{j}] binary keys: {list(binary_data.keys())}")
                                    for bk, bv in binary_data.items():
                                        print(f"      binary.{bk}: mimeType={bv.get('mimeType','?')}, fileName={bv.get('fileName','?')}")
    else:
        print(f"Unexpected data type: {type(data)}")
else:
    print("Execution 248131 not found")

conn.close()