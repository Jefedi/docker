import json, re

with open('/tmp/hermes-results/call_lfk1h454.txt') as f:
    data = json.load(f)

# Print full leboncoin content
lbc = data['results'][0]['content']
print("="*80)
print("LEBONCOIN FULL CONTENT:")
print("="*80)
print(lbc)