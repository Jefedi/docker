#!/usr/bin/env python3
"""Scrape SeLoger Sanvic and Bléville via camofox, then Le-Partenaire locations."""
import json, subprocess, time

def eval_js(tab_id, js_expr):
    payload = json.dumps({'userId': 'hermes-veille', 'expression': js_expr})
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/evaluate',
         '-H', 'Content-Type: application/json', '-d', payload],
        capture_output=True, text=True, timeout=30
    )
    try:
        data = json.loads(result.stdout)
        if data.get('ok'):
            return json.loads(data['result'])
        return []
    except:
        return []

def navigate_and_scrape(tab_id, url):
    # Navigate
    payload = json.dumps({'url': url, 'userId': 'hermes-veille'})
    subprocess.run(['curl', '-s', '-X', 'POST', f'http://127.0.0.1:9377/tabs/{tab_id}/navigate',
                    '-H', 'Content-Type: application/json', '-d', payload],
                   capture_output=True, text=True, timeout=30)
    time.sleep(5)
    # Scroll to bottom to load more
    for _ in range(3):
        eval_js(tab_id, "window.scrollTo(0, document.body.scrollHeight); 'ok'")
        time.sleep(2)
    # Extract listings
    js = '''JSON.stringify(Array.from(document.querySelectorAll("a[href*='.htm']")).filter(function(a){return a.href.indexOf("annonces/locations")>-1}).map(function(a){var c=a.closest("article")||a.parentElement;var t=c?c.innerText:a.innerText;var pm=t.match(/([\d\s]+)\s*\\u20ac/);var pcm=t.match(/(\d+)\s*pi/);var sm=t.match(/([\d,]+)\s*m/);return{url:a.href.split("?")[0],id:(a.href.match(/\\/(\d+)\\.htm/)||["",""])[1],price:pm?pm[1].replace(/\\s/g,""):"",pieces:pcm?pcm[1]:"",surface:sm?sm[1]:""}}))'''
    return eval_js(tab_id, js)

tab_id = open('/opt/data/cron/tmp/seloger_tab.txt').read().strip()

# Sanvic
print("=== SeLoger Sanvic ===")
listings = navigate_and_scrape(tab_id, "https://www.seloger.com/recherche/location/appartement/le-havre-76600/sanvic-76620/nbh2fr6214")
for r in listings:
    print(f"seloger-{r['id']} | {r['price']}€ | {r['pieces']}pi | {r['surface']}m² | {r['url'][:80]}")
print(f"Total Sanvic: {len(listings)}")

# Bléville
print("\n=== SeLoger Bléville ===")
listings = navigate_and_scrape(tab_id, "https://www.seloger.com/recherche/location/appartement/le-havre-76600/bleville-76620/nbh2fr6221")
for r in listings:
    print(f"seloger-{r['id']} | {r['price']}€ | {r['pieces']}pi | {r['surface']}m² | {r['url'][:80]}")
print(f"Total Bléville: {len(listings)}")