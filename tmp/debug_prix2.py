#!/usr/bin/env python3
"""Find why the price regex doesn't work - check the span tag structure."""
import re

raw = open('/tmp/scrape/lp2.html','r',errors='replace').read()

# Find all occurrences of class="prix" with surrounding context
for m in re.finditer(r'class="prix"[^>]*>', raw):
    start = m.start()
    # Get the full opening tag
    tag_end = raw.find('>', start)
    full_tag = raw[start:tag_end+1]
    # Get the content
    content_start = tag_end + 1
    content_end = raw.find('<', content_start)
    content = raw[content_start:content_end]
    print(f'Tag: {full_tag}')
    print(f'Content: {content}')
    print()

# The issue: the span might have additional attributes
# Let's try a different regex approach
# Extract ALL prices from class="prix" elements
all_prix = re.findall(r'class="prix"[^>]*>(\d[\d\s\xa0;]*€)', raw)
print(f'All prix values: {all_prix[:10]}')

# Try with &nbsp; as literal
all_prix2 = re.findall(r'class="prix"[^>]*>(\d[\d\xa0]*&nbsp;€)', raw)
print(f'All prix v2: {all_prix2[:10]}')