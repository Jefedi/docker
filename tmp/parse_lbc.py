import json
data=json.load(open('/tmp/lbc_raw.json'))
items=json.loads(data['result'])
print(f'Total: {len(items)}')
for i,it in enumerate(items):
    text=it['text']
    href=it['href']
    ad_id=href.split('/')[-1] if href else 'N/A'
    print(f'{i+1}. ID={ad_id} | {text[:250]}')