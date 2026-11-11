# -*- coding: utf-8 -*-
"""Assemble Part 7 (supplementary answers) from per-section coverage + answer notes."""
import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(BASE, 'notes')
OUT = os.path.join(NOTES, 'part7-xiaolin.md')

SECTIONS = [
    ('agent', 'AG', 'Agent 面试专题'),
    ('rag', 'RG', 'RAG 面试专题'),
    ('tools', 'TL', 'LLM 工具调用面试专题'),
    ('llm', 'LM', '大模型工程面试专题'),
    ('langchain', 'LC', 'LangChain 框架面试专题'),
    ('coding', 'CD', 'AI 编程面试专题'),
]

rows = []
counts = {}
for sec, prefix, name in SECTIONS:
    cov = json.load(open(os.path.join(NOTES, f'xiaolin_coverage_{sec}.json'), encoding='utf-8'))
    st = {k: sum(1 for x in cov if x['status'] == k) for k in ('covered', 'partial', 'missing')}
    counts[sec] = (len(cov), st)
    ans = open(os.path.join(NOTES, f'xiaolin_answers_{sec}.md'), encoding='utf-8').read().strip()
    rows.append((name, st['partial'] + st['missing'], ans))

total = sum(c[0] for c in counts.values())
tot_st = {k: sum(c[1][k] for c in counts.values()) for k in ('covered', 'partial', 'missing')}
supplement = tot_st['partial'] + tot_st['missing']

head = [
    '# 第七部分 · 小林面试笔记 AI 面试题逐题核对与补充',
    '',
    '## 7.0 覆盖分析结论',
    '',
    '> 题库来源：[小林面试笔记 · 大模型面试题](https://xiaolinnote.com/ai/)，抓取于 2026-11-11；'
    '共 6 个专题、**124 道题**，逐题下载详情页后与《AI Agent 面试指南》前六部分做语义级比对。',
    '',
    '判定口径：`covered`（已覆盖）＝指南中有专门一节回答该题主要考点；`partial`（部分覆盖）＝有相关概念或相邻答案，'
    '但缺关键角度、实现细节或落地方案；`missing`（未覆盖）＝指南基本没有对应内容，仅在速查表中出现关键词不算覆盖。'
    '对 **partial + missing** 的每一道题，本节都补写了完整答案；完整 124 题判定表见附录 D。',
    '',
    '| 专题 | 题数 | 已覆盖 | 部分覆盖 | 未覆盖 | 本节补写答案 |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',
]
for (sec, prefix, name), (n, st) in zip(SECTIONS, [counts[s[0]] for s in SECTIONS]):
    head.append(f'| {name} | {n} | {st["covered"]} | {st["partial"]} | {st["missing"]} | {st["partial"] + st["missing"]} |')
head += [
    f'| **合计** | **{total}** | **{tot_st["covered"]}** | **{tot_st["partial"]}** | **{tot_st["missing"]}** | **{supplement}** |',
    '',
    f'结论：**{tot_st["covered"]}/{total} 道原指南已完整覆盖**，'
    f'**{tot_st["partial"]} 道部分覆盖、{tot_st["missing"]} 道未覆盖**，'
    f'共补写 **{supplement} 道**详细答案。缺口集中在三块：'
    '① 模型底层原理与训练（Transformer、注意力变体、位置编码、Tokenizer、微调/LoRA、Post-Training、KV Cache、量化、MoE、部署框架）；'
    '② 具体开发框架（LangChain / LangGraph / LlamaIndex / LangChain4j / Deep Research）；'
    '③ AI 编程工程实践（Vibe Coding、Spec 驱动、代码定位、AI 代码审查、跨会话交接）。'
    '工具调用专题还缺 A2A、WebRTC、CLI 封装、代码沙箱、Skill 加载机制等协议与运行时细节。',
    '',
    '> 说明：以下答案依据题库详情页的考点与追问重新组织撰写，不是源站原文转载；'
    '源站未展开而由整理者补充的内容标注 `【补充】`。模型结构、框架版本与 API 能力变化较快，面试前请核对官方文档。',
    '',
]

chunks = ['\n'.join(head)]
for i, (name, cnt, ans) in enumerate(rows, 1):
    chunks.append(f'## 7.{i} {name}（{cnt} 道补充答案）\n\n{ans}\n')

text = '\n'.join(chunks)
open(OUT, 'w', encoding='utf-8').write(text)
print('wrote', OUT, len(text), 'chars;', supplement, 'supplementary answers')
