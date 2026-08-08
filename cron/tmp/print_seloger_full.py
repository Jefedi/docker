import json, re

with open('/tmp/hermes-results/call_lfk1h454.txt') as f:
    data = json.load(f)

# Print full SeLoger content to find descriptions
for idx in [1, 2, 3]:
    content = data['results'][idx]['content']
    url = data['results'][idx]['url']
    quartier = ['Centre-ville', 'Sanvic', 'Bléville'][idx-1]
    
    print(f"\n{'='*80}")
    print(f"SELOGER {quartier} - URL: {url}")
    print(f"Content length: {len(content)}")
    print(f"{'='*80}")
    print(content)