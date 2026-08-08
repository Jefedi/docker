import re
html = open('/opt/data/tmp/veille/lp_p1.html').read()
m = re.search(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL)
if m:
    start = max(0, m.start()-200)
    end = min(len(html), m.end()+3000)
    block = html[start:end]
    print(block[:3500])