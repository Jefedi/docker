import sqlite3, json
conn = sqlite3.connect('/tmp/n8n_db.sqlite')
c = conn.cursor()
# Check column names
c.execute("PRAGMA table_info(execution_entity)")
cols = c.fetchall()
print("Columns:", [col[1] for col in cols])
# Try with jsonData or dataText
for col in [col[1] for col in cols]:
    if 'data' in col.lower() or 'json' in col.lower():
        c.execute(f'SELECT {col} FROM execution_entity WHERE id = 248094')
        row = c.fetchone()
        if row and row[0]:
            print(f"Found data in column: {col}")
            data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            result = data.get('run_data', {}).get('resultData', {}) if isinstance(data, dict) else {}
            error = result.get('error', {})
            print('Error node:', error.get('node', {}).get('name', '?'))
            print('Error msg:', error.get('message', '?'))
            rd = result.get('runData', {})
            for n, runs in rd.items():
                for r in runs:
                    s = 'ERROR' if r.get('error') else 'ok'
                    print('  Node:', n, '->', s)
                    if r.get('error'):
                        print('   ', r['error'].get('message', '?')[:300])
            break
conn.close()