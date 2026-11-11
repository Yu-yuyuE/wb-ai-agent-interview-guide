# -*- coding: utf-8 -*-
"""Fetch all xiaolinnote.com/ai interview question pages and extract main text."""
import os
import re
import html
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
QS = json.load(open(os.path.join(BASE, 'sources', 'xiaolin_questions.json'), encoding='utf-8'))
OUTDIR = os.path.join(BASE, 'sources', 'xiaolin_pages')
os.makedirs(OUTDIR, exist_ok=True)


def clean(fragment):
    fragment = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', '', fragment, flags=re.S)
    fragment = re.sub(r'</(p|div|li|h[1-6]|tr|pre|blockquote|section)>', '\n', fragment, flags=re.I)
    fragment = re.sub(r'<br\s*/?>', '\n', fragment, flags=re.I)
    fragment = re.sub(r'<[^>]+>', '', fragment)
    text = html.unescape(fragment)
    lines = [re.sub(r'\s+', ' ', l).strip() for l in text.splitlines()]
    out, prev = [], None
    for l in lines:
        if not l:
            continue
        if l == prev and len(l) < 40:
            continue
        out.append(l)
        prev = l
    return '\n'.join(out)


def fetch(item):
    url, title = item
    full = 'https://xiaolinnote.com' + url
    section = url.split('/')[2]
    name = url.split('/')[-1].replace('.html', '')
    out = os.path.join(OUTDIR, f'{section}__{name}.txt')
    if os.path.exists(out) and os.path.getsize(out) > 500:
        return url, os.path.getsize(out), 'cached'
    raw = out + '.raw'
    r = subprocess.run(['curl', '--ssl-no-revoke', '-sL', '--max-time', '45', full, '-o', raw],
                       capture_output=True)
    if not os.path.exists(raw) or os.path.getsize(raw) < 1000:
        return url, 0, 'download_failed'
    t = open(raw, encoding='utf-8', errors='ignore').read()
    m = re.search(r'<main[^>]*>(.*?)</main>', t, flags=re.S)
    frag = m.group(1) if m else t[t.find('<main'):]
    body = clean(frag)
    text = f'# {title}\n来源：{full}\n\n{body}\n'
    open(out, 'w', encoding='utf-8').write(text)
    os.remove(raw)
    return url, len(text), 'ok'


results = {}
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch, it): it[0] for it in QS.items()}
    for f in as_completed(futs):
        url, size, status = f.result()
        results[url] = (size, status)

print('pages:', len(results), 'ok:', sum(1 for s, _ in results.values() if s == 'ok'),
      'cached:', sum(1 for s, _ in results.values() if s == 'cached'),
      'failed:', [u for u, (_, s) in results.items() if s == 'download_failed'])
print('total chars:', sum(sz for sz, _ in results.values()))

# per-section corpus for answer drafting
sections = {}
for url, title in QS.items():
    section = url.split('/')[2]
    name = url.split('/')[-1].replace('.html', '')
    p = os.path.join(OUTDIR, f'{section}__{name}.txt')
    if os.path.exists(p):
        sections.setdefault(section, []).append((url, title, open(p, encoding='utf-8').read()))
for sec, items in sections.items():
    items.sort(key=lambda x: x[0])
    corpus = '\n\n' + ('=' * 70) + '\n\n'.join(
        f'## [{i+1}] {title}\n{url}\n\n{body}' for i, (url, title, body) in enumerate(items))
    path = os.path.join(BASE, 'sources', f'xiaolin_corpus_{sec}.txt')
    open(path, 'w', encoding='utf-8').write(corpus)
    print('corpus', sec, len(items), 'pages', os.path.getsize(path), 'bytes')
