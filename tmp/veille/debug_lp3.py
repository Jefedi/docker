import re, html as htmllib

raw = open('/opt/data/tmp/veille/lp_p1.html').read()
unesc = htmllib.unescape(raw)
cards = re.split(r'class="card w-100 mb-5 item-annonce"', unesc)
card = cards[1]
link_m = re.search(r'href="(/immobilier/location/appartement/(?:havre|le-havre)/76600/[^"]+)"', card)
print(f"link: {link_m}")
if link_m:
    print(link_m.group(1))
# Maybe the href has &amp; that got unescaped? Check raw
print("---")
# Check in raw
link_m2 = re.search(r'href="(/immobilier/location/appartement/(?:havre|le-havre)/76600/[^"]+)"', cards[1])
print(f"link in unescaped card: {link_m2}")