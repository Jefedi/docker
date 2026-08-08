import json
d=json.load(open('/tmp/lbc_all_links.txt'))
links=d['result'].split('|')
seen=set(); unique=[]
for l in links:
    if l not in seen:
        seen.add(l); unique.append(l)
print(f'Unique links: {len(unique)}')
for l in unique: print(l.split('/')[-1])