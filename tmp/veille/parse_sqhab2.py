import re, html as htmllib, json

raw = open('/opt/data/tmp/veille/sqhab.html').read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', raw, re.DOTALL)
s = scripts[6]
print(f"Script 6 len: {len(s)}")
print(s[:1000])