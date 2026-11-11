# -*- coding: utf-8 -*-
"""Build the final AI Agent interview guide from notes + JavaGuide source docs."""
import os
import re
import json
import difflib

BASE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(BASE, 'notes')
SOURCES = os.path.join(BASE, 'sources')
OUT = os.path.join(BASE, 'AI-Agent面试指南.md')

PART_INFO = [
    {
        'file': 'part1-llm.md',
        'title': '第一部分 · 大模型基础面试题总结',
        'lead': '对应源文档：`interview-questions/llm-interview-questions.md`（39 题）、`llm-basis/` 4 篇专题与 `ai-core-concepts.md`。沿「一次大模型调用」链路展开：Token 化 → 上下文组装 → 采样生成 → 流式/重试/限流 → 结构化解析 → 日志与评测。每题按「核心结论 / 机制原理 / 工程落地 / 追问链 / 易错点」组织，末尾附篇内延伸追问。',
        'src': 'docs_ai_interview-questions_llm-interview-questions.md',
        'short': '第一部分',
    },
    {
        'file': 'part2-agent.md',
        'title': '第二部分 · AI Agent 面试题总结',
        'lead': '对应源文档：`interview-questions/agent-interview-questions.md`（58 题）与 `agent/` 全部 10 篇专题。覆盖 Agent 基础、Memory、Prompt/Context、MCP、Agent Skills、Harness 六层检查框架、Workflow/Graph/Loop 与外层 Loop Engineering，以及 6 道综合设计题。',
        'src': 'docs_ai_interview-questions_agent-interview-questions.md',
        'short': '第二部分',
    },
    {
        'file': 'part3-project.md',
        'title': '第三部分 · Agent 项目面试实战',
        'lead': '对应源文档：`interview-questions/agent-project-interview-guide.md` 全文、`ai-interview-guide.md` 项目经历追问、各 README 高频问题。以「智能售后工单 Agent」为贯穿案例，把项目面试方法论拆成逐题 Q&A：架构七层、技术选型六问、工具八道检查、超时幂等、稳定性与降级、指标与评测、Badcase 复盘、Trace 还原、15 道自测题与可复用讲述模板。',
        'src': 'docs_ai_interview-questions_agent-project-interview-guide.md',
        'short': '第三部分',
    },
    {
        'file': 'part4-rag.md',
        'title': '第四部分 · RAG 面试题总结',
        'lead': '对应源文档：`interview-questions/rag-interview-questions.md`（60 题）与 `rag/` 7 篇专题、`llm-evaluation.md`。沿「解析 → Chunk → Embedding → 索引 → 召回 → 重排 → 上下文组装 → 生成 → 更新 → 评测」全链路逐题作答，含 6 道综合排查题。',
        'src': 'docs_ai_interview-questions_rag-interview-questions.md',
        'short': '第四部分',
    },
    {
        'file': 'part5-system-design.md',
        'title': '第五部分 · AI 系统设计面试题总结',
        'lead': '对应源文档：`interview-questions/ai-system-design-interview-questions.md`（56 题）与 `system-design/` 6 篇专题。覆盖生产级架构、模型网关与调用治理、安全权限审计、可观测/评测/发布、实时语音 Agent，以及 7 道综合设计题。',
        'src': 'docs_ai_interview-questions_ai-system-design-interview-questions.md',
        'short': '第五部分',
    },
    {
        'file': 'part6-extra.md',
        'title': '第六部分 · 文档内嵌问句式考点速答',
        'lead': '补齐前面五部分未逐字覆盖的 110 条「正文内嵌问句」：MCP 生产检查清单、Multi-Agent 设计六问、GraphRAG 查询路由、LLM 安全上线清单、结构化输出上线检查、AI 可观测五类信号、Agent 项目正文设问等；末尾附 `TODO.md` 待办专题转化出的 15 道【预测题】。',
        'src': None,
        'short': '第六部分',
    },
]


def norm(s):
    return re.sub(r'[`*#|\\\s：:，,。.、；;？?（）()「」“”"\'\[\]0-9.\-—｜■□→+]', '', s)


def load_part(path):
    """Drop agent-only preamble, normalize heading levels, skip fenced code."""
    lines = open(path, encoding='utf-8').read().splitlines()
    # drop first H1 (note title)
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    # drop leading preamble up to first heading
    idx = 0
    while idx < len(lines) and not lines[idx].startswith('#'):
        idx += 1
    lines = lines[idx:]
    if lines and lines[0].startswith('# ') and ('覆盖' in lines[0] or '速查' in lines[0]):
        pass
    # find minimum heading level
    levels = []
    in_fence = False
    for l in lines:
        if re.match(r'^\s*(```|~~~)', l):
            in_fence = not in_fence
            continue
        if not in_fence:
            m = re.match(r'^(#{1,6})\s', l)
            if m:
                levels.append(len(m.group(1)))
    min_level = min(levels) if levels else 2
    delta = 2 - min_level
    out = []
    in_fence = False
    for l in lines:
        if re.match(r'^\s*(```|~~~)', l):
            in_fence = not in_fence
            out.append(l)
            continue
        if not in_fence:
            m = re.match(r'^(#{1,6})\s+(.*)$', l)
            if m:
                lvl = min(6, len(m.group(1)) + delta)
                l = '#' * lvl + ' ' + m.group(2)
        out.append(l)
    # editorial cleanups
    text = '\n'.join(out)
    text = text.replace('§0 源文档清单、题目覆盖索引与待办登记', '§0 本部分题目覆盖索引')
    text = text.replace('## 覆盖统计', '## 本部分覆盖统计')
    text = text.replace('## §33 覆盖统计', '## 本部分覆盖统计')
    text = re.sub(r'^>\s*.*(非成稿|不是最终成稿|源文档答案笔记|本文件是|供后续成稿|取用素材).*$', '', text, flags=re.M)
    return text.strip()


def heading_index(notes_file):
    heads = []
    for l in open(os.path.join(NOTES, notes_file), encoding='utf-8').read().splitlines():
        m = re.match(r'^#{1,6}\s+(.*)$', l)
        if m:
            heads.append(m.group(1).strip())
    return heads


def questions_from(path):
    """Return (group, question) pairs from a question page."""
    res = []
    group = ''
    for l in open(os.path.join(SOURCES, path), encoding='utf-8'):
        l = l.strip()
        if l.startswith('## '):
            group = l[3:].strip()
        elif l.startswith('- ') and ('？' in l or '?' in l) and '](' not in l[:20]:
            q = re.sub(r'参考：\[.*?\]\(.*?\)', '', l[2:].strip()).strip()
            res.append((group, q))
    return res


def find_heading(q, heads):
    """Map an original question to the most similar answer heading in the notes."""
    nq = norm(q)
    if not nq:
        return None
    best, best_score = None, 0.0
    for h in heads:
        clean = re.sub(r'^(\d+[-.)]\d*\s*|Q-?A?\d+\s*[｜|]?\s*|题\s*\d+[.)]?\s*|Q\d+\s*|第[一二三四五六]\S{0,3}题\s*)', '', h)
        clean = re.sub(r'^\s*[.)｜|]\s*', '', clean)
        nh = norm(clean)
        if nq in nh:
            score = 1.0 + min(len(nq) / max(len(nh), 1), 1.0)
        else:
            score = difflib.SequenceMatcher(None, nq, nh).ratio()
        if score > best_score:
            best, best_score = clean.strip(), score
    return best if best_score >= 0.62 else None


def build_appendix_a():
    out = ['# 附录 A · 原题覆盖索引（自测清单）', '',
           '> 用法：逐条遮住答案自测，能同时说出「核心结论 + 一个工程细节 + 一个追问」再打勾。右侧给出本指南中对应的题目小节，方便回查。', '']
    total = 0
    for p in PART_INFO[:5]:
        if p['short'] == '第三部分':
            continue
        qs = questions_from(p['src'])
        heads = heading_index(p['file'])
        out += [f'## {p["short"]}（{len(qs)} 题）', '']
        cur = None
        for g, q in qs:
            if g != cur:
                out += ['', f'**{g}**', '']
                cur = g
            h = find_heading(q, heads)
            ref = f'→ `{h.replace(chr(96), "")}`' if h else f'→ {p["short"]}对应小节'
            out.append(f'- [ ] {q} {ref}')
            total += 1
        out.append('')
    # extra high-frequency & self-test questions
    extras = []
    pg = os.path.join(SOURCES, 'docs_ai_interview-questions_agent-project-interview-guide.md')
    lines = open(pg, encoding='utf-8').read().splitlines()
    in_self = False
    for l in lines:
        s = l.strip()
        if '自测' in s and s.startswith('#'):
            in_self = True
            continue
        if in_self and re.match(r'^\d+[.)]\s', s) and ('？' in s or '?' in s):
            extras.append(('项目实战 15 道自测题', re.sub(r'^\d+[.)]\s*', '', s)))
    for fn, label in [
        ('docs_ai_interview-questions_ai-interview-guide.md', '项目经历常见追问'),
        ('docs_ai_interview-questions_README.md', '面试题专题高频问题'),
        ('docs_ai_README.md', '知识体系高频问题'),
        ('docs_ai_agent_README.md', 'Agent 专题高频问题'),
        ('docs_ai_rag_README.md', 'RAG 专题高频问题'),
        ('docs_ai_llm-basis_README.md', '大模型基础专题高频问题'),
        ('docs_ai_system-design_README.md', '系统设计专题高频问题'),
    ]:
        for l in open(os.path.join(SOURCES, fn), encoding='utf-8'):
            s = l.strip()
            if s.startswith('- ') and ('？' in s or '?' in s) and '](' not in s[:20]:
                extras.append((label, s[2:].strip()))
    out += [f'## 补充：项目实战自测题与入口页高频问题（{len(extras)} 题）', '',
            '> 对应第三部分（方法论与自测题答案）、第六部分（延伸速答）。', '']
    cur = None
    for label, q in extras:
        if label != cur:
            out += ['', f'**{label}**', '']
            cur = label
        out.append(f'- [ ] {q}')
    out.append('')
    return '\n'.join(out), total, len(extras)


def build_appendix_b():
    tree = json.load(open(os.path.join(SOURCES, '_tree.json'), encoding='utf-8'))
    items = [(i['path'], i.get('size', 0)) for i in tree['tree']
             if i['path'].startswith('docs/ai/') and i['path'].endswith('.md')]
    groups = {}
    for path, size in items:
        parts = path.split('/')
        key = '/'.join(parts[2:-1]) or '根目录'
        groups.setdefault(key, []).append((path, size))
    out = ['# 附录 B · 40 篇源文档索引', '',
           '> 全部链接指向 `Snailclimb/JavaGuide` 的 `main` 分支；括号内为文件字节数。', '']
    for key in ['根目录', 'interview-questions', 'llm-basis', 'agent', 'rag', 'system-design']:
        if key not in groups:
            continue
        out += [f'## `{key}/`（{len(groups[key])} 篇）', '',
                '| 文档 | 体量 |', '| --- | ---: |']
        for path, size in sorted(groups[key]):
            url = 'https://github.com/Snailclimb/JavaGuide/blob/main/' + path
            out.append(f'| [{path}]({url}) | {size:,} |')
        out.append('')
    return '\n'.join(out)


def build_appendix_c():
    return '''# 附录 C · 复习自评表与失分点清单

## 自评表（每格按 0～3 分打：0 不会 / 1 只会结论 / 2 能讲机制 / 3 能结合项目答追问）

| 部分 | 核心结论 | 机制原理 | 工程落地 | 追问与易错点 | 结合自己的项目 | 合计 /15 |
| --- | --- | --- | --- | --- | --- | --- |
| 第一部分 大模型基础 |  |  |  |  |  |  |
| 第二部分 AI Agent |  |  |  |  |  |  |
| 第三部分 Agent 项目实战 |  |  |  |  |  |  |
| 第四部分 RAG |  |  |  |  |  |  |
| 第五部分 AI 系统设计 |  |  |  |  |  |  |

## 面试中最常见的十类失分点

1. 只报技术栈和框架名，不讲约束、取舍与代价。
2. 把「效果很好 / 准确率高」当结论，没有评测集、样本量、基线和统计口径。
3. 把 RAG 答非所问一律归咎于模型，不会分「召回 / 排序 / 上下文 / 生成」定位。
4. 把 Prompt 当安全边界，认为工具 description 或 Schema 校验等价于权限校验。
5. 认为超时＝失败，对写操作盲目重试，答不出幂等键、状态查询与对账。
6. 把 Chat History 当长期记忆，混淆 Memory / Context / State / 权威业务数据库。
7. 说不出 Agent Loop 的停止条件、成本预算与中断恢复，只讲 ReAct 四个词。
8. 动辄 Multi-Agent，答不出通信成本、状态一致性、调试代价和「先治理工具」的替代方案。
9. 评测只谈公开榜单或 LLM-as-Judge，不提偏差校准、版本绑定、Trace 回放与线上灰度。
10. 讲 Badcase 只说「优化了 Prompt」，没有现场证据、控制变量、根因确认与回归用例。

## 考前一页纸

- **四要素**：约束 → 选择 → 代价 → 证据（+ 替代方案 + 何时换方案）。
- **三条边界**：模型只产出意图；执行、授权、幂等、状态由代码负责；外部内容一律不可信。
- **四条链路**：调用链路（Token/上下文/采样/流式/重试）、RAG 链路（解析/切块/召回/重排/生成）、Agent 链路（观察/决策/工具/状态/停止）、治理链路（网关/权限/Trace/评测/灰度）。
- **五个必背 ID**：`requestId`、`runId`、`toolCallId`、`actionId`、`sessionId`。
- **六类必背指标**：任务完成率、工具选择/参数正确率、P50/P95 与 Token 成本、转人工率与重复副作用数、Recall@K/MRR/NDCG/Context Precision、Faithfulness。
'''


def main():
    chunks = [open(os.path.join(NOTES, 'part0-overview.md'), encoding='utf-8').read().strip()]
    for p in PART_INFO:
        body = load_part(os.path.join(NOTES, p['file']))
        chunks.append('\n\n---\n\n# ' + p['title'] + '\n\n' + p['lead'] + '\n\n' + body)
    app_a, total, extra = build_appendix_a()
    chunks.append('\n\n---\n\n' + app_a)
    chunks.append('\n\n---\n\n' + build_appendix_b())
    chunks.append('\n\n---\n\n' + build_appendix_c())
    chunks.append('\n\n---\n\n> 本指南由 JavaGuide `docs/ai`（`main` 分支，2026-11-09 抓取）全部 40 篇 Markdown 整理而成；'
                 '正式面试题 213 道逐题作答，合计 839 条问句式考点均有答案或速答。'
                 '文档内容随上游仓库更新，涉及模型能力、版本与参数请以官方文档为准。\n')
    text = '\n'.join(chunks)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    open(OUT, 'w', encoding='utf-8').write(text)
    print('wrote', OUT)
    print('chars', len(text), 'lines', text.count('\n') + 1)
    print('official questions indexed', total, 'extra questions', extra)


if __name__ == '__main__':
    main()
