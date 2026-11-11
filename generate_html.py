# -*- coding: utf-8 -*-
"""Render the Markdown guide into a single self-contained dark-theme HTML reader."""
import os
import re
import sys
import html

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, 'vendor'))
import markdown  # noqa: E402

SRC = os.path.join(BASE, 'AI-Agent面试指南.md')
OUT = os.path.join(BASE, 'AI-Agent面试指南.html')

text = open(SRC, encoding='utf-8').read()
md = markdown.Markdown(
    extensions=['tables', 'fenced_code', 'toc', 'sane_lists', 'attr_list'],
    extension_configs={'toc': {'permalink': False, 'toc_depth': '1-3', 'anchorlink': False}},
)
body = md.convert(text)
toc = md.toc

# Mermaid source blocks -> renderable divs
def mermaid_repl(m):
    code = html.unescape(m.group(1))
    code = re.sub(r'<[^>]+>', '', code)
    return '<div class="mermaid">' + code + '</div>'

body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', mermaid_repl, body, flags=re.S)
# checkbox rendering
body = body.replace('<li>[ ] ', '<li><span class="todo">☐</span> ')
body = re.sub(r'<li>\[ \]\s*', '<li><span class="todo">☐</span> ', body)
body = re.sub(r'(<li>\s*<p>)\[ \]\s*', r'\1<span class="todo">☐</span> ', body)
# external links open in new tab
body = re.sub(r'<a href="(https?://[^"]+)"', r'<a target="_blank" rel="noopener" href="\1"', body)

CSS = """
:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2130;--fg:#e6e9f0;--muted:#9aa5b8;--line:#283142;--accent:#7aa7ff;--accent2:#4ade9b;--warn:#f0b862}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);font-family:"Segoe UI","Microsoft YaHei","PingFang SC",system-ui,sans-serif;font-size:15.5px;line-height:1.78}
#side{position:fixed;inset:0 auto 0 0;width:340px;background:var(--panel);border-right:1px solid var(--line);display:flex;flex-direction:column;z-index:20}
#side header{padding:20px 20px 12px;border-bottom:1px solid var(--line)}
#side h1{font-size:17px;margin:0 0 6px;line-height:1.45}
#side .sub{color:var(--muted);font-size:12px;line-height:1.6}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.chip{background:var(--panel2);border:1px solid var(--line);border-radius:6px;padding:3px 8px;font-size:11.5px;color:var(--accent)}
#search{margin:14px 16px 8px;padding:9px 12px;border-radius:8px;border:1px solid var(--line);background:#0f141c;color:var(--fg);font-size:13px;outline:none;width:calc(100% - 32px)}
#search:focus{border-color:var(--accent)}
#toc{flex:1;overflow:auto;padding:4px 12px 40px 16px;font-size:13px}
#toc ul{list-style:none;margin:0;padding-left:14px}
#toc>ul{padding-left:0}
#toc li{margin:1px 0}
#toc a{display:block;color:var(--muted);text-decoration:none;padding:3px 8px;border-radius:6px;border-left:2px solid transparent;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#toc a:hover{color:var(--fg);background:var(--panel2)}
#toc>ul>li>a{color:var(--fg);font-weight:600;margin-top:8px}
#toc a.active{color:var(--accent);border-left-color:var(--accent);background:rgba(122,167,255,.09)}
#toc li.hide{display:none}
#main{margin-left:340px;padding:38px 6vw 120px;max-width:1180px}
#main h1{font-size:30px;line-height:1.4;margin:44px 0 20px;padding-bottom:12px;border-bottom:1px solid var(--line);scroll-margin-top:20px}
#main>h1:first-child{margin-top:0}
#main h2{font-size:22px;margin:34px 0 14px;color:#cfe0ff;scroll-margin-top:20px}
#main h3{font-size:18px;margin:26px 0 10px;color:#eaf0ff;scroll-margin-top:20px}
#main h4{font-size:16px;margin:20px 0 8px;color:#d6dcec;scroll-margin-top:20px}
#main h5,#main h6{font-size:15px;margin:18px 0 8px;color:var(--muted);scroll-margin-top:20px}
#main p{margin:10px 0}
#main ul,#main ol{padding-left:24px;margin:8px 0}
#main li{margin:5px 0}
#main strong{color:#fff}
#main em{color:#c8d3e8}
#main a{color:var(--accent)}
#main blockquote{margin:14px 0;padding:10px 16px;background:rgba(122,167,255,.07);border-left:3px solid var(--accent);border-radius:0 8px 8px 0;color:#cfd8ea}
#main blockquote p{margin:4px 0}
#main table{border-collapse:collapse;width:100%;margin:16px 0;font-size:13.5px;display:block;overflow-x:auto}
#main th,#main td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
#main th{background:var(--panel2);color:#dce7ff;white-space:nowrap}
#main tr:nth-child(even) td{background:rgba(255,255,255,.018)}
#main code{background:#1d2532;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12.8px;color:#ffd79a;font-family:Consolas,"Cascadia Code",monospace}
#main pre{background:#11161f;border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow:auto;line-height:1.6}
#main pre code{background:none;border:0;padding:0;color:#cfe3ff;font-size:12.8px}
#main hr{border:0;border-top:1px solid var(--line);margin:46px 0}
#main img{max-width:100%;border-radius:8px}
.todo{display:inline-block;width:17px;color:var(--accent2);font-weight:700}
.mermaid{background:#11161f;border:1px solid var(--line);border-radius:10px;padding:18px;overflow:auto;margin:16px 0;text-align:center}
#top{position:fixed;right:24px;bottom:24px;width:42px;height:42px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--fg);cursor:pointer;font-size:18px;z-index:10}
#top:hover{border-color:var(--accent);color:var(--accent)}
#burger{display:none;position:fixed;left:12px;top:12px;z-index:30;background:var(--panel);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:7px 11px;cursor:pointer}
@media(max-width:980px){#side{transform:translateX(-100%);transition:transform .2s}#side.open{transform:none}#main{margin-left:0;padding:70px 20px 100px}#burger{display:block}}
@media print{#side,#top,#burger{display:none}#main{margin:0;max-width:none}body{background:#fff;color:#000}#main h2,#main h3{color:#000}}
"""

JS = """
const search=document.getElementById('search');
const items=[...document.querySelectorAll('#toc li')];
search.addEventListener('input',()=>{
  const q=search.value.trim().toLowerCase();
  items.forEach(li=>{
    const a=li.querySelector(':scope > a');
    li.classList.toggle('hide', q!=='' && !(a && a.textContent.toLowerCase().includes(q)));
  });
  if(q!==''){items.forEach(li=>{if(!li.classList.contains('hide')){li.parentElement && (li.parentElement.style.display='block');}});}
});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();search.focus();}});
const links=[...document.querySelectorAll('#toc a')];
const heads=links.map(a=>document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
function onScroll(){let cur=null;for(const h of heads){if(h.getBoundingClientRect().top<=120)cur=h;else break;}
  links.forEach(a=>a.classList.toggle('active',cur&&a.getAttribute('href')==='#'+cur.id));}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
document.getElementById('burger').addEventListener('click',()=>document.getElementById('side').classList.toggle('open'));
document.getElementById('main').addEventListener('click',e=>{if(e.target.tagName==='A'&&window.innerWidth<980)document.getElementById('side').classList.remove('open');});
document.getElementById('top').addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
"""

page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Agent 面试指南 · JavaGuide docs/ai 全景详解版</title>
<style>{CSS}</style>
<script type="module">
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
mermaid.initialize({{startOnLoad:true,theme:'dark'}});
</script>
</head><body>
<button id="burger">☰ 目录</button>
<aside id="side"><header>
<h1>AI Agent 面试指南</h1>
<div class="sub">JavaGuide <code>docs/ai</code> 全景详解版 · 2026-11-09</div>
<div class="chips"><span class="chip">5 大图示部分</span><span class="chip">213 道原题</span><span class="chip">839 条考点</span><span class="chip">40 篇源文档</span></div>
</header>
<input id="search" placeholder="筛选目录（Ctrl+K）…" autocomplete="off">
<nav id="toc">{toc}</nav></aside>
<main id="main">{body}</main>
<button id="top" title="回到顶部">↑</button>
<script>{JS}</script>
</body></html>
"""
open(OUT, 'w', encoding='utf-8').write(page)
print('wrote', OUT, len(page), 'chars')
