# -*- coding: utf-8 -*-
"""Render the concise oral-answer edition into a dark-theme HTML reader."""
import os
import re
import sys
import html

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'vendor'))
import markdown  # noqa: E402

SRC = os.path.join(BASE, 'AI-Agent面试简答版.md')
OUT = os.path.join(BASE, 'AI-Agent面试简答版.html')

# Reuse the base reader's CSS/JS, then specialize for the Q&A dialogue layout.
base_src = open(os.path.join(BASE, 'generate_html.py'), encoding='utf-8').read()
CSS = re.search(r'CSS = """(.*?)"""', base_src, re.S).group(1)
JS = re.search(r'JS = """(.*?)"""', base_src, re.S).group(1)

CSS += """
#main .qa{margin:9px 0;padding:9px 14px;border-radius:8px;background:var(--panel2);border-left:3px solid var(--line);font-size:14.5px;line-height:1.75}
#main .qa strong{color:#fff}
#main .qa.q{background:rgba(122,167,255,.07);border-left-color:var(--accent)}
#main .qa.a{background:rgba(74,222,155,.055);border-left-color:var(--accent2)}
#main .qa.f{background:rgba(240,184,98,.06);border-left-color:var(--warn)}
#main .qa.r{background:rgba(122,167,255,.05);border-left-color:#5b7fb8}
#main h3{font-size:16.5px;margin:24px 0 8px;padding-top:6px;border-top:1px dashed var(--line)}
#main .wrap>h1:first-child+h2{margin-top:18px}
"""

# Default: expand top-level (chapters), collapse question lists; add a third tool button.
JS = JS.replace(
    "  setOpen(li,false);\n});",
    "  let d=0,p=li.parentElement;\n"
    "  while(p&&p!==tocRoot){if(p.tagName==='UL')d++;p=p.parentElement;}\n"
    "  setOpen(li,d<=1);\n});")
JS = JS.replace(
    "document.getElementById('collapseAll').addEventListener('click',collapseAll);",
    "document.getElementById('collapseAll').addEventListener('click',collapseAll);\n"
    "function sectionsOnly(){branches.forEach(li=>{let d=0,p=li.parentElement;"
    "while(p&&p!==tocRoot){if(p.tagName==='UL')d++;p=p.parentElement;}setOpen(li,d<=1);});"
    "items.forEach(li=>li.classList.remove('hide'));search.value='';snapshot=null;}\n"
    "document.getElementById('sectionsOnly').addEventListener('click',sectionsOnly);")

text = open(SRC, encoding='utf-8').read()
md = markdown.Markdown(
    extensions=['tables', 'fenced_code', 'toc', 'sane_lists', 'attr_list'],
    extension_configs={'toc': {'permalink': False, 'toc_depth': '1-3', 'anchorlink': False}},
)
body = md.convert(text)
toc = md.toc

for label, cls in [('面试官', 'q'), ('我（60 秒口述）', 'a'), ('追问 1', 'f'),
                   ('追问 2', 'f'), ('答', 'r')]:
    body = re.sub(r'<p><strong>' + re.escape(label) + r'</strong>([：:])',
                  f'<p class="qa {cls}"><strong>{label}</strong>\\1', body)
body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>',
              lambda m: '<div class="mermaid">' + html.unescape(re.sub(r'<[^>]+>', '', m.group(1))) + '</div>',
              body, flags=re.S)
body = body.replace('<li>[ ] ', '<li><span class="todo">☐</span> ')
body = re.sub(r'<li>\[ \]\s*', '<li><span class="todo">☐</span> ', body)
body = re.sub(r'(<li>\s*<p>)\[ \]\s*', r'\1<span class="todo">☐</span> ', body)
body = re.sub(r'<a href="(https?://[^"]+)"', r'<a target="_blank" rel="noopener" href="\1"', body)

page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Agent 面试简答版 · 400 题口述与追问</title>
<style>{CSS}</style>
</head><body>
<button id="burger">☰ 目录</button>
<aside id="side"><header>
<h1>AI Agent 面试简答版</h1>
<div class="sub">口述答案 + 面试官追问 · 2026-11-11</div>
<div class="chips"><span class="chip">8 个部分</span><span class="chip">400 道题</span><span class="chip">801 组追问</span><span class="chip">60 秒口述</span></div>
</header>
<input id="search" placeholder="筛选目录（Ctrl+K）…" autocomplete="off">
<div class="toctools"><button id="sectionsOnly" type="button">只看章节</button><button id="expandAll" type="button">展开全部</button><button id="collapseAll" type="button">折叠全部</button></div>
<nav id="toc">{toc}</nav></aside>
<main id="main"><div class="wrap">{body}</div></main>
<button id="top" title="回到顶部">↑</button>
<script>{JS}</script>
</body></html>
"""
open(OUT, 'w', encoding='utf-8').write(page)
print('wrote', OUT, len(page), 'chars')
