import json, re

with open('/tmp/hermes-results/call_lfk1h454.txt') as f:
    data = json.load(f)

# Print the tail of leboncoin content to see if there are more listings after #20
lbc = data['results'][0]['content']
lines = lbc.split('\n')

# Print from line 3200 onwards (after listing #19)
print("=== LBC TAIL (from line 3200 to end) ===")
for i in range(3200, len(lines)):
    line = lines[i].strip()
    if line:
        print(f"{i}: {line[:200]}")