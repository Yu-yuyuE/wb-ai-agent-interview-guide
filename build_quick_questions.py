# -*- coding: utf-8 -*-
"""Build the question groups for the concise oral-answer interview edition."""
import os
import re
import json

BASE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.join(BASE, 'sources')
OUT = os.path.join(SOURCES, 'quick_questions.json')

import build_guide  # noqa: E402  (reuse question parsing)

JG = [
    ('J1', '大模型基础', 'docs_ai_interview-questions_llm-interview-questions.md'),
    ('J2', 'AI Agent', 'docs_ai_interview-questions_agent-interview-questions.md'),
    ('J4', 'RAG', 'docs_ai_interview-questions_rag-interview-questions.md'),
    ('J5', 'AI 系统设计', 'docs_ai_interview-questions_ai-system-design-interview-questions.md'),
]

questions = {}
for prefix, name, fn in JG:
    qs = build_guide.questions_from(fn)
    questions[prefix] = [
        {'id': f'{prefix}-{i:02d}', 'question': q, 'group': g, 'source': 'JavaGuide'}
        for i, (g, q) in enumerate(qs, 1)
    ]
    print(prefix, name, len(qs))

# Project-practice extras: 48 self-test / high-frequency questions from Appendix A
md = open(os.path.join(BASE, 'AI-Agent面试指南.md'), encoding='utf-8').read()
start = md.find('## 补充：项目实战自测题与入口页高频问题')
end = md.find('# 附录 B', start)
seg = md[start:end]
extra_qs = [re.sub(r'^- \[ \]\s*', '', l.strip()) for l in seg.splitlines() if l.strip().startswith('- [ ]')]
# 15 project self-test questions from the original guide (not part of Appendix A extras)
pg_lines = open(os.path.join(SOURCES, 'docs_ai_interview-questions_agent-project-interview-guide.md'),
                encoding='utf-8').read().splitlines()
in_self = False
for l in pg_lines:
    if '自测' in l and not in_self:
        in_self = True
        continue
    if in_self and re.match(r'^\d+[.)]\s', l.strip()):
        extra_qs.append(re.sub(r'^\d+[.)]\s*', '', l.strip()))
questions['J3'] = [
    {'id': f'J3-{i:02d}', 'question': q, 'group': '项目实战 / 高频追问', 'source': 'JavaGuide'}
    for i, q in enumerate(extra_qs, 1)
]
print('J3 项目实战 / 高频追问', len(extra_qs))

# Xiaolin: 124 questions, sorted by section + original number
xl = json.load(open(os.path.join(SOURCES, 'xiaolin_questions.json'), encoding='utf-8'))
xl_secs = {'agent': 'X1', 'rag': 'X2', 'tools': 'X3', 'llm': 'X4', 'langchain': 'X5', 'coding': 'X6'}
xl_names = {'agent': 'Agent', 'rag': 'RAG', 'tools': 'LLM 工具调用',
            'llm': '大模型工程', 'langchain': 'LangChain 框架', 'coding': 'AI 编程'}
xl_items = []
for url, title in xl.items():
    sec = url.split('/')[2]
    m = re.match(r'^(\d+)[.、]', title.strip())
    n = int(m.group(1)) if m else 999
    xl_items.append((sec, n, title, url))
xl_items.sort(key=lambda x: (list(xl_secs).index(x[0]), x[1]))
for sec in xl_secs:
    questions[xl_secs[sec]] = []
for sec, n, title, url in xl_items:
    p = xl_secs[sec]
    questions[p].append({
        'id': f'{p}-{len(questions[p]) + 1:02d}',
        'question': title,
        'group': '小林 · ' + xl_names[sec],
        'source': 'xiaolinnote',
        'url': 'https://xiaolinnote.com' + url,
    })
for p in xl_secs.values():
    print(p, questions[p][0]['group'], len(questions[p]))

ALL = {k: v for k, v in questions.items()}
json.dump(ALL, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('total questions', sum(len(v) for v in ALL.values()), '->', OUT)

GROUPS = [
    ('g1', ['J1'], '第一部分 · 大模型基础（39 题）', 'notes/part1-llm.md'),
    ('g2', ['J2'], '第二部分 · AI Agent（58 题）', 'notes/part2-agent.md'),
    ('g3', ['J3'], '第三部分 · Agent 项目实战自测与高频追问（63 题）', 'notes/part3-project.md'),
    ('g4', ['J4'], '第四部分 · RAG（60 题）', 'notes/part4-rag.md'),
    ('g5', ['J5'], '第五部分 · AI 系统设计（56 题）', 'notes/part5-system-design.md'),
    ('g6', ['X1'], '第六部分 · 小林 Agent 专题（30 题）', 'notes/xiaolin_answers_agent.md + notes/part2-agent.md'),
    ('g7', ['X2', 'X3'], '第七部分 · 小林 RAG + 工具调用（45 题）',
     'notes/xiaolin_answers_rag.md + notes/xiaolin_answers_tools.md'),
    ('g8', ['X4', 'X5', 'X6'], '第八部分 · 小林大模型工程 + LangChain + AI 编程（49 题）',
     'notes/xiaolin_answers_llm.md + notes/xiaolin_answers_langchain.md + notes/xiaolin_answers_coding.md'),
]
for gname, prefixes, title, ref in GROUPS:
    lines = [f'# {title}', '', f'> 答案素材：{ref}；也可在 `AI-Agent面试指南.md` 中用 Grep 查原题详解。', '']
    n = 0
    for p in prefixes:
        for item in ALL[p]:
            n += 1
            lines.append(f"- `{item['id']}` {item['question']}")
    lines.append('')
    path = os.path.join(SOURCES, f'quick_questions_{gname}.md')
    open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('group file', gname, n, path)
