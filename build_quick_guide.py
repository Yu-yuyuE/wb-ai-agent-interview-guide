# -*- coding: utf-8 -*-
"""Assemble the concise oral-answer interview edition (Markdown)."""
import os
import re
import json

BASE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(BASE, 'notes')
SOURCES = os.path.join(BASE, 'sources')
OUT = os.path.join(BASE, 'AI-Agent面试简答版.md')

PARTS = [
    ('g1', '第一部分 · 大模型基础（39 题）',
     '对应 JavaGuide `llm-interview-questions.md`。沿一次模型调用链路：Token / 上下文 / 采样 → 流式 / 重试 / 限流 → 结构化输出与 Function Calling → 评测体系。'),
    ('g2', '第二部分 · AI Agent（58 题）',
     '对应 JavaGuide `agent-interview-questions.md`：Agent 基础、Memory、Prompt/Context、MCP 与 Skills、Harness、Workflow/Graph/Loop。'),
    ('g3', '第三部分 · Agent 项目实战自测与高频追问（63 题）',
     '项目面试连环追问：为什么是 Agent、架构链路、选型取舍、写操作治理、指标与 Badcase、Trace 与框架能力边界。'),
    ('g4', '第四部分 · RAG（60 题）',
     '对应 JavaGuide `rag-interview-questions.md`：文档处理、向量库与索引、检索优化、GraphRAG、知识更新与评测。'),
    ('g5', '第五部分 · AI 系统设计（56 题）',
     '对应 JavaGuide `ai-system-design-interview-questions.md`：生产架构、模型网关、安全权限、可观测评测、实时语音 Agent。'),
    ('g6', '第六部分 · 小林 Agent 专题（30 题）',
     '深挖 Agent 工程：任务拆分、记忆粒度与压缩、规划与反思、Multi-Agent 协作与容错、任务幻觉、Harness 设计、自进化、执行方差。'),
    ('g7', '第七部分 · 小林 RAG + LLM 工具调用（45 题）',
     'RAG 实战选型与排查，Function Calling 训练原理、MCP 组成与传输、A2A、SSE/WebSocket/WebRTC、Tool Routing、CLI 与代码沙箱、Skill 加载。'),
    ('g8', '第八部分 · 小林大模型工程 + LangChain + AI 编程（49 题）',
     '模型底层与训练（Transformer、位置编码、LoRA、Post-Training、KV Cache、量化、MoE、部署）、LangChain 系列框架、AI 编程工程实践。'),
]

QUESTIONS = json.load(open(os.path.join(SOURCES, 'quick_questions.json'), encoding='utf-8'))

DIALOGUE = re.compile(r'^\*\*(面试官|我（60 秒口述）|追问 [12]|答)\*\*')


def format_dialogue(body):
    """Keep every Q/A line as its own Markdown paragraph (otherwise they merge)."""
    out = []
    for line in body.splitlines():
        if DIALOGUE.match(line) and out and out[-1].strip():
            out.append('')
        out.append(line)
    return '\n'.join(out)


def appendix_a():
    out = ['## 附录 A · 400 题自测清单', '',
           '> 逐题限时 60 秒口述，能说出「结论 + 2 个要点 + 1 个工程细节」再打勾；卡住的按 ID 回对应部分。', '']
    for g, title, _ in PARTS:
        ids = []
        for line in open(os.path.join(SOURCES, f'quick_questions_{g}.md'), encoding='utf-8'):
            m = re.match(r'- `([A-Za-z0-9-]+)`', line.strip())
            if m:
                ids.append(m.group(1))
        lookup = {x['id']: x for v in QUESTIONS.values() for x in v}
        out += ['', f'**{title}**', '']
        for i in ids:
            q = lookup[i]['question'].replace('\n', ' ')
            out.append(f'- [ ] `{i}` {q}')
        out.append('')
    return '\n'.join(out)


def appendix_b():
    return '''## 附录 B · 与详解版的对照索引

| 简答版 ID 前缀 | 题目来源 | 详解版位置 | 说明 |
| --- | --- | --- | --- |
| `J1-` | JavaGuide 大模型基础 39 题 | 第一部分 1-1～5-5 | 逐题详解、原文参数与调用日志字段 |
| `J2-` | JavaGuide AI Agent 58 题 | 第二部分 Q1～Q58 | Harness 六层、MCP、Skills、Loop 完整链路 |
| `J3-` | 项目实战 15 道自测 + 48 道高频 | 第三部分 §1～§33、附录 A | 七层架构、工具八道检查、Badcase 七步复盘 |
| `J4-` | JavaGuide RAG 60 题 | 第四部分 Q1～Q60 | 索引算法参数、混合检索、GraphRAG、评测口径 |
| `J5-` | JavaGuide 系统设计 56 题 | 第五部分 题 1～题 56 | 网关模块拆分、审计字段、语音状态机 |
| `X1-` | 小林 Agent 30 题 | 第七部分 7.1（16 道补充）+ 附录 D | 已覆盖题按附录 D 定位原章节 |
| `X2-` / `X3-` | 小林 RAG 23 + 工具调用 22 题 | 第四部分 + 第七部分 7.2 + 附录 D | A2A / WebRTC / 沙箱等为新增内容 |
| `X4-` / `X5-` / `X6-` | 小林大模型工程 23 + 框架 12 + AI 编程 14 题 | 第七部分 7.3～7.5 + 附录 D | 原指南基本未覆盖，集中于第七部分补写 |

> 详解版另有「839 条 JavaGuide 问句式考点」的速答与预测题（第六部分），简答版不重复收录检查清单式设问；需要逐条核对时用详解版附录 A / D。

---

> 本简答版由两套题库共 400 道面试题整理而成，每题含 60 秒口述答案与 801 组追问回答。
> 配套详解版：`AI-Agent面试指南.md` / `AI-Agent面试指南.html`。内容随题库更新，涉及版本与参数请以官方文档为准。
'''


def main():
    chunks = [open(os.path.join(NOTES, 'quick_part0.md'), encoding='utf-8').read().strip()]
    total = 0
    for g, title, lead in PARTS:
        body = format_dialogue(open(os.path.join(NOTES, f'quick_{g}.md'), encoding='utf-8').read().strip())
        n = len(re.findall(r'^### ', body, flags=re.M))
        total += n
        chunks.append(f'\n\n---\n\n## {title}\n\n{lead}\n\n{body}\n')
    chunks.append('\n\n---\n\n' + appendix_a())
    chunks.append('\n\n---\n\n' + appendix_b())
    text = '\n'.join(chunks)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    open(OUT, 'w', encoding='utf-8').write(text)
    print('wrote', OUT, 'chars', len(text), 'lines', text.count('\n') + 1, 'questions', total)


if __name__ == '__main__':
    main()
