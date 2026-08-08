import re
f = open('/tmp/veille/lhimmo_annonces.html')
c = f.read()
f.close()
m = re.search(r'(\d+)\s*€\s*/mois', c)
print(m)
print(repr(c[198190:198220]))
# Also check for &nbsp; or non-breaking space
m2 = re.findall(r'(\d+)\s*€\s*(?:/&nbsp;|/)?mois', c)
print(f'm2: {m2}')
m3 = re.findall(r'(\d+)€\s*/?\s*mois', c)
print(f'm3: {m3}')