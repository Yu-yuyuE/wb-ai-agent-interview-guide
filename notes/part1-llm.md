# 《AI Agent 面试指南》· 大模型基础面试题总结 —— 源文档答案笔记（非成稿）

本文件是按题目清单逐题整理的**源文档答案笔记**，供后续成稿取材，不是最终成稿。每题按「一句话核心结论 / 机制·原理 / 工程落地做法 / 常见追问与易错点 / 原文参数·字段·指标」五段组织。凡源文档未展开、由整理者补充的内容均以 **【补充】** 标注，且不引入源文档没有的具体数字或版本号。

源文档（文件名均为原路径 `/` 替换为 `_`）：
- 题目清单：`docs_ai_interview-questions_llm-interview-questions.md`（题号与分组以此为准，共 5 组、39 题；综合场景题 5 道）
- 原理：`docs_ai_llm-basis_llm-operation-mechanism.md`
- 工程：`docs_ai_llm-basis_llm-api-engineering.md`
- 结构化/工具：`docs_ai_llm-basis_structured-output-function-calling.md`
- 评测：`docs_ai_llm-basis_llm-evaluation.md`
- 专题索引：`docs_ai_llm-basis_README.md`
- 概念串联：`docs_ai_ai-core-concepts.md`（取「大模型基础 / Token / 上下文窗口 / 采样参数 / Prompt / 结构化输出 / Function Calling / 生产级 LLM 调用 / AI 应用评测 / 系统设计」相关部分）

专题 README 给出的建议阅读顺序与高频问题（保留原文，作为复习锚点）：
1. 阅读顺序：运行机制 → API 调用工程 → 结构化输出 → AI 应用评测。
2. 学习重点原文：Token、上下文窗口、Temperature、Top P、停止词等参数如何影响模型输出；生产级调用要处理流式响应、超时、重试、限流、fallback、日志和审计；结构化输出不能只靠 Prompt，要结合 JSON Schema、Function Calling、Tool Calling 和服务端校验，即便这样也要准备失败兜底；评测要区分离线 Golden Set、LLM-as-Judge、线上灰度、Trace 回放和持续回归。
3. README「高频问题」原文：为什么同一个 Prompt 每次输出不一样？上下文窗口变大是不是就一定更好？为什么结构化输出会偶发失败？如何做兜底和校验？Function Calling、Tool Calling、MCP 分别解决什么问题？AI 应用上线前如何证明「效果变好了」而不是只凭感觉？

---

## 〇、分组与逐题覆盖对照

| 分组 | 题数 | 题号 | 对应源文档 |
| --- | --- | --- | --- |
| 一、LLM 运行机制 | 8 | 1-1 ~ 1-8 | llm-operation-mechanism.md |
| 二、API 调用工程 | 8 | 2-1 ~ 2-8 | llm-api-engineering.md |
| 三、结构化输出与工具调用 | 10 | 3-1 ~ 3-10 | structured-output-function-calling.md（部分重叠 api-engineering.md） |
| 四、AI 应用评测 | 8 | 4-1 ~ 4-8 | llm-evaluation.md |
| 五、综合场景题 | 5 | 5-1 ~ 5-5 | 四篇交叉 |

合计 **39 题**，逐题覆盖，题号与题干均保留原文。

---

# 一、LLM 运行机制（8 题）

相关内容：[《LLM 运行机制：Token、上下文窗口与采样参数怎么影响输出》]。原文定位：Token、上下文窗口和采样参数共同影响一次调用能放入多少信息、花费多少资源，以及输出会有多大波动；这组题常结合长对话、RAG 证据和结构化输出继续追问。

## 1-1. Token 是什么？为什么中文、英文、代码消耗的 Token 不一样？

- **一句话核心结论**：Token 是模型自回归生成时每一步「补」出来的文本碎片，由 Tokenizer 用子词算法切分，和字、词都没有固定一一对应关系，因此中英文、代码、生僻字的 Token 消耗不同。
- **机制/原理**：模型根据当前上下文预测一个 Token，把它加入上下文再预测下一个，直到遇到结束标记或达到输出限制，这叫**自回归生成（Autoregressive Generation）**。Tokenizer 把文本切成大小不等的片段；固定按字切词表小但序列变长，固定按词切序列短但中文词组让词表膨胀，**BPE、Unigram 等子词切分算法**在两者间取舍：高频片段尽量作为整体保留，低频词继续拆小。原文示意切分：`你好，我是小 G。` → `[你好]` `[，]` `[我是]` `[小 G]` `[。]`，统计为「原文 9 字符 → Token 数 5 个 → 压缩比约 1.8 倍」；该切分只用于说明过程，实际结果取决于目标模型的 Tokenizer，换供应商或模型版本就会变，OpenAI 提供可直接查看切分结果的 Tokenizer 工具（platform.openai.com/tokenizer）。英文单词可能占多个 Token；中文也可能一词多 Token，或多字合成一个 Token；「趋近 1 字 1 Token」只可能出现在部分高频词上。中文歧义、生僻字和低频专业术语被切成的粒度也会影响模型对文本的处理效果。
- **工程落地做法**：容量规划用经验值估算并留余量，计费与监控一律读取 API 返回的 `usage`；精确计数用官方 Tokenizer 工具，不手动估算。落地时每次调用至少保存模型版本、输入 Token、缓存 Token、推理 Token（若供应商返回）、输出 Token、上下文裁剪策略和采样参数。
- **常见追问与易错点**：不要把「1 字符 = 1 Token」写死；不要拿一组换算数字直接用于结算；同一段文本跨模型、跨版本 Token 序列可能改变；多模态图片的 Token 要单独折算（见 1-7 知识点速查）。
- **原文参数·字段·指标（务必保留）**：经验值「英文 1 Token 大约对应 3~4 个字符；中文通常在 1~2 个汉字之间，混排内容继续波动」；DeepSeek 官方换算「1 个英文字符约消耗 0.3 Token、1 个中文字符约消耗 0.6 Token，即每个 Token 约为 3.3 个英文字符或 1.7 个中文字符」；Tokenizer 版本差异「早期模型（如 GPT-3.5）中文压缩率较低，约为 1 字 1.5~2 Token；GPT-4o 使用词表约 20 万的 `o200k_base` Tokenizer，Qwen2.5 词表约 15 万；现有实测中新闻类文本约为 1.5 字/Token，技术文档约为 1.2 字/Token，但这些数字不适合直接用于结算」。特殊 Token 表（也会计入 Token 总数，通常对用户不可见但占窗口）：

| 特殊 Token | 用途 | 示例 |
| --- | --- | --- |
| BOS（Beginning of Sequence） | 标记序列开始 | `<s>` |
| EOS（End of Sequence） | 标记序列结束 | `</s>` |
| PAD（Padding） | 批处理时填充短序列 | `<pad>` |
| 工具调用标记 | Function Calling 边界 | `<tool_call/>` |

## 1-2. 上下文窗口是什么？上下文窗口越大，效果一定越好吗？

- **一句话核心结论**：上下文窗口是一次调用里模型可处理的总 Token 上限（「工作记忆」Working Memory），标称值要被系统提示词、历史、工具定义、RAG 片段和输出预算共同瓜分；窗口越大只提高「能容纳的信息量」，不保证「同等利用每个位置」。
- **机制/原理**：窗口标称 128K、200K 或 1M，指一次调用能容纳的 Token 上限；大多数模型把输入与输出合并计算，部分供应商（如 Google Gemini）分别设置输入和输出上限。窗口由三块构成：**固定内容**（System Prompt、工具调用 Schema、格式标记）、**本次输入**（User Prompt、历史消息、RAG 检索片段）、**生成预算**（即将输出的 Token）。标称窗口减掉这些才是业务数据实际可用空间。ai-core-concepts 列出隐形成本：System Prompt、User Prompt、多轮对话历史、RAG 检索片段、工具调用 Schema、格式开销（特殊字符/换行/Markdown 标记），以及「模型生成的输出 Token 也占上下文窗口」。
- **长上下文背后的计算约束**：Transformer **自注意力机制（Self-Attention）**带来三类开销：计算成本平方级增长（O(N²)，输入 Token 翻倍处理能力需求可能变为 4 倍）、推理延迟增加（生成每个新 Token 要关注更多历史 Token，TTFT 显著增加）、安全风险增加（更长上下文 = 更大攻击面）。FlashAttention、GQA/MQA、Sliding Window Attention、Ring Attention 可减少计算量或显存占用，但 O(N²) 仍是标准自注意力的理论复杂度。
- **上下文溢出的真实表现**：System Prompt 明明要求「必须输出 JSON」却被漏掉；回答后半段偏题；RAG 片段太多抓不住真正相关的证据。信息放进窗口不等于模型能同等利用每个位置，「中间丢失」即更容易利用开头和结尾、对中间内容召回较弱；窗口扩到 1M 也不能自动消除。
- **工程落地做法**：出现输入 Token、账单、预填充耗时和 TTFT 同时上涨时，先检查检索片段数量、历史消息裁剪和关键信息位置，而不是继续把窗口塞满。注意「上下文窗口 ≠ 最大生成长度」，参数名可能是 `max_tokens`、`max_completion_tokens` 或 `max_output_tokens`，不要根据供应商名称推断上限，调用前读能力页。
- **常见追问与易错点**：推理模型的 `reasoning_content`（DeepSeek 思考模式）/ OpenAI Responses API 的 `previous_response_id`、reasoning item 与推理摘要要按供应商区分；推理 Token 不一定出现在下一轮消息文本里，但本轮仍消耗生成预算、可能计入输出 Token 和上下文限制，不能得出「推理过程不占窗口或不计费」的通用结论。
- **原文参数·字段·指标**：`max_tokens` / `max_completion_tokens` / `max_output_tokens`；`reasoning_content` + `content`；`previous_response_id`；128K / 200K / 1M；O(N²)；Lost in the Middle（「中间丢失」）；TTFT（Time-To-First-Token）。

## 1-3. 什么是 Lost in the Middle 问题？长上下文场景下怎么缓解？

- **一句话核心结论**：Lost in the Middle（「中间丢失」）指模型更容易利用上下文开头和结尾、对中间位置内容召回较弱，因此「塞进窗口」不等于「被用上」，扩到 1M 窗口也不能自动消除。
- **机制/原理**：原文把它归到「信息放进窗口也不等于模型能同等利用每个位置」。它与 Self-Attention 的长序列建模、位置编码、训练分布有关；【补充】直觉上，长上下文中段既离起始指令远、又不像结尾那样紧邻生成位置，注意力权重更容易被稀释，但这只是机制层面的通俗解释，源文档未给出定量结论。
- **工程落地做法**：把关键约束和关键信息放在开头或结尾（System Prompt 放前、关键证据靠近回答位）；控制 RAG 检索片段数量、合并重复片段；对历史消息做裁剪或摘要；减少无关材料占据中段的比例。评测侧用自定义指标 **Context Usage**（生成是否有效使用已进 Prompt 的材料）做诊断——原文刻意不用 RAGAS 的 `Context Utilization` 这个名字，避免把两个口径混在一起；也可参考 Noise Sensitivity（0 到 1，越低越好）检查无关 chunk 是否带偏回答。
- **常见追问与易错点**：不要以为「换个 1M 窗口模型」就解决了；不要只看最终答案准确率，要分段定位是「没召回」还是「召回了却没用上」。原文在评测篇明确：政策已出现在 Top-3、回答仍只给「请联系客服」，问题可能在上下文排序、Prompt 注入方式，或模型忽略中间内容。
- **原文参数·字段·指标**：Lost in the Middle、Context Usage（自定义，区别于 RAGAS Context Utilization）、Noise Sensitivity、Top-3、TTFT。

## 1-4. Temperature、Top-P、Top-K 分别控制什么？生产环境怎么设置更稳？

- **一句话核心结论**：三者都作用在「打分（logits）→ softmax 概率 → 抽样」链路上——Temperature 调整概率分布形状，Top-p / Top-k 截断候选集合缩小「抽签池」，Penalty 系列对已出现词降分防复读。
- **机制/原理**：模型每一步给词表中每个候选 Token 打一个 **logits** 分数，经 **softmax** 得到概率分布后采样。Temperature 在 softmax 前把所有分数除以 T：**`p(t) = softmax(z_t / T)`**，温度越低分布越尖、输出越确定，越高越平、越随机。Top-k 固定保留概率最高的 k 个；Top-p（nucleus）从高到低累加概率，达到阈值即截断，候选数量随分布变化。Penalty 在解码时降低已出现 Token 的分数。原文示例词表（补全「今天天气真__」）：

| 候选 Token | 原始分数（logit） | softmax 概率 |
| --- | --- | --- |
| 好 | 5.0 | 81.21% |
| 不错 | 3.2 | 13.42% |
| 棒 | 2.1 | 4.47% |
| 糟糕 | 0.5 | 0.90% |
| 紫色 | -8.0 | 约 0.00%（ai-core-concepts 记为 < 0.001%） |

| 温度 | 概率分布的变化 | 示例结果 |
| --- | --- | --- |
| T = 0.2 | 分布变尖，高概率 Token 更集中 | 「好」约 99.99% |
| T = 1.0 | 保持原始分布 | 「好」约 81.21%，「不错」约 13.42% |
| T = 1.5 | 分布变平，低概率 Token 获得更多机会 | 「好」约 66.85%，「不错」约 20.14%，「棒」约 9.67% |

`Top-k = 3` 固定保留「好、不错、棒」；`Top-p = 0.9` 时「好 + 不错」累计已达 94.63%，候选集只保留这两个；若第一名自身超过 90% 就只留一个。

| 组合 | 效果 | 适用场景 |
| --- | --- | --- |
| T=0（通常按贪婪解码处理） | 每步选最高分，结果仍受模型版本和服务端实现影响 | 结构化输出、低随机性场景 |
| 低温 + Top-p=0.9 | 相对稳定，但允许措辞变化 | 分析报告、摘要 |
| 中高温 + Top-p=0.95 | 多样性较高，但排除极端离谱选项 | 创意写作、对话 |

工程建议温度（经验值，非硬规则）：

| 场景 | 推荐温度 | 说明 |
| --- | --- | --- |
| 结构化提取 / JSON 输出 | 0 ~ 0.3 | 配合严格 schema + 解析失败重试策略 |
| 评估 / 分析 / 代码评审 | 0.4 ~ 0.8 | 平衡确定性与表达多样性 |
| 创作类内容（文案、头脑风暴） | 0.8 ~ 1.2+ | 增加多样性，但要承担格式一致性风险 |

采样参数配置建议总表（原文）：

| 场景 | Temperature | Top-p | Penalty | 其他建议 |
| --- | --- | --- | --- | --- |
| JSON / 结构化输出 | 0 ~ 0.3 | 1.0 | 保持默认 | 配合 Strict Mode + 重试策略 |
| 代码评审 / 技术分析 | 0.4 ~ 0.7 | 0.9 | 保持默认 | 结合 CoT Prompt |
| 多轮对话 | 0.6 ~ 0.8 | 0.9 | 适度开启 | 控制历史消息长度 |
| 创意写作 / 头脑风暴 | 0.8 ~ 1.2 | 0.95 | 按需开启 | 接受输出多样性，做好后处理 |
| 推理模型 | 查模型文档 | 查模型文档 | 查模型文档 | 过滤不支持参数，保留服务端校验 |

- **工程落地做法**：结构化任务用低温 + Strict Mode + 解析失败重试；跨供应商时按目标模型能力表过滤不支持的参数（推理模型参数支持范围由具体 API 决定，不能把 DeepSeek 思考模式和 OpenAI 推理模型概括成同一种行为）；结构稳定性仍依赖 Structured Outputs、服务端校验和失败处理，不能只调 Temperature；无明确调参依据时 Penalty 保留默认值。
- **常见追问与易错点**：贪婪解码虽然最稳定，但可能更容易陷入重复循环；Repetition Penalty 过高会把 JSON 里反复出现的 `"name"`、`"score"` 字段名一起降分导致缺字段；RAG 问答用 Presence Penalty 会倾向引入检索内容里没有的新词，削弱回答对证据的忠实度；不同供应商对 Penalty 定义不完全一致。误区「Temperature 设为 0 就一定稳定」被原文单列（见 1-5、3-10）。
- **原文参数·字段·指标**：`p(t) = softmax(z_t / T)`；logits / softmax；Top-p、Top-k；Temperature；Repetition Penalty / Presence Penalty / Frequency Penalty（三者对照见知识点速查）；`seed`；`reasoning_effort`；`strict` / Strict Mode。

## 1-5. 为什么 Temperature 设置为 0，模型输出仍然可能不完全一致？

- **一句话核心结论**：Temperature=0（贪婪解码）只让「同一次采样」确定，但模型版本更新、跨区域调用和服务端解码/并行/后端配置变化都会让结果漂移；`seed` 也只是尽力而为。
- **机制/原理**：原文列出四类仍可能不一致的原因：模型版本更新（底层权重变化）、跨区域调用（不同集群可能部署不同版本）、服务端解码实现、并行计算和后端配置发生变化。`seed` 通常只提供「尽力而为的可复现性」，不保证逐字一致；DeepSeek 当前 API 参数也没有公开 `seed`。低 Temperature 在 OpenAI、Claude 系列是常见做法，但不能替代 Schema——上下文过长、指令冲突、输出截断、工具描述模糊时，结构化输出仍然会失败。
- **工程落地做法**：把 `seed` 与固定模型版本、固定 Prompt、固定采样参数一起保存；CI/CD 把真实 LLM 调用留给冒烟测试，需要稳定复现的逻辑测试仍使用 Mock；复现实验时接受供应商服务仍可能带来的小幅非确定性。跨厂商按目标模型文档调整——原文特别标注 Gemini 3 系列官方建议保持默认 `temperature=1.0`，下调反而可能导致循环或推理退化。
- **常见追问与易错点**：这是结构化输出「偶发失败」的高频根因之一，不能只答「浮点/并行计算」；要分清「输出不完全一致」与「结构化解析失败」是两条排查路径；不要把「Temperature=0」当成 Schema 和服务端校验的替代品。
- **原文参数·字段·指标**：`seed`、`temperature=1.0`（Gemini 3 建议）、`finish_reason=length`、Strict Mode。

## 1-6. 大模型为什么会产生幻觉？常见缓解方案有哪些？

- **一句话核心结论**：幻觉源于自回归模型按概率「补」文本、任务边界不清时会偏题或补写不存在的信息；检索证据能约束回答范围但不能彻底消除幻觉，需要契约、校验、拒答、评测和人工反馈一起兜底。
- **机制/原理**：ai-core-concepts 原文：Prompt 是输入给 LLM 的任务指令，LLM 根据当前上下文生成后续 Token，能表现出一定语义理解和指令跟随，但「任务边界不清时，它仍可能偏题或补写不存在的信息」；Prompt 的作用是缩小生成范围，质量与长度没有直接关系，比堆叠修饰词更重要的是交代清楚 Role、Task、Context、Format 四项。RAG 章节原文：检索证据能约束模型的回答范围，但不能彻底消除幻觉——检索错误、上下文噪声、引用错配和模型不遵循指令仍会产生错误答案。
- **工程落地做法**：用 JSON Schema / Structured Outputs 把输出变成可校验契约；RAG 侧控制检索片段数量、避免无关内容推高输入 Token，并用引用校验、答案评估、拒答和人工反馈；评测侧用 Faithfulness（事实忠实度，检查回答里有没有超出检索结果范围的捏造）、幻觉率、引证支持率单独设门禁，高风险条件不能被平均分抵消（退款结果错误时，即使语气、完整性、用户体验得分都很高，这条任务仍应判定失败）；工具超时后不让模型基于空结果编回答（「模型只能解释『当前无法完成』，不能猜测结果」）。
- **常见追问与易错点**：「用了 RAG 就没幻觉」「用了 Structured Outputs 就不用校验」都是误区；评测里把检索到的文档直接当标准答案会混淆检索质量与生成质量；结构化输出失败后原则是「可以降级，但不能让模型编造业务事实」。
- **原文参数·字段·指标**：Faithfulness、幻觉率、引证支持率、`need_human_review` / `NEED_MORE_INFO` / `Unknown`、Role/Task/Context/Format（Prompt 四要素）、`finish_reason=length`。

## 1-7. Token 预算怎么估算？输入、输出、历史消息、RAG 证据如何取舍？

- **一句话核心结论**：把上下文窗口当固定容量的桶，先满足 `window ≥ input_tokens + max_output_tokens`，结构化任务先定 `max_output_tokens` 再给输入留 10%~20% 安全余量，不够时按固定顺序削减。
- **机制/原理**：原文给出 16K 上下文窗口典型分配（结构化输出场景，mermaid 饼图，数值只用于示意）：System Prompt（含 Schema）1500、User Prompt（业务数据）6000、历史消息（多轮对话）2000、安全边际（供应商开销）1500、输出预留（Max Tokens）5000。普通生成模型先检查 `window ≥ input_tokens + max_output_tokens`；推理模型要按目标 API 参数定义单独计算——有些 API 的 `max_output_tokens` / `max_completion_tokens` 已同时包含推理 Token 和可见回答，再加一次 `reasoning_tokens` 会重复，另一些分别限制思考过程和最终回答，可用返回的 `usage` 反推真实调用组成再校准。
- **工程落地做法**：`input_tokens` 至少包含 system prompt（含 schema / 工具定义）、user prompt（变量替换后的实际文本）、历史消息、RAG context。预算不够时按顺序：减少 RAG Top-K → 合并重复片段 → 摘要或截断长字段 → 一轮塞不下再拆成分批评估或两阶段生成。**Prompt Caching** 省钱逻辑：把不变内容放前（System Prompt、工具定义、RAG Context），变化内容放后（User Prompt）；按供应商响应字段监控缓存读取和缓存写入 Token 验证命中率；批量任务尽量在缓存时间窗口内完成。固定前缀长、重复率高的任务（多轮对话、RAG 应用、批量评估）更容易受益；OpenAI Prompt Caching、Anthropic Prompt Caching、DeepSeek Context Caching 的触发门槛、缓存寿命与价格并不相同，不要把缓存时长和折扣写死在业务代码里。
- **常见追问与易错点**：不要用经验换算数字结算；推理 Token 要单独看（reasoning tokens 经常计入输出侧费用）；输出单价经常高于输入单价，但「不存在稳定的 2~4 倍行业比例」，价格表更新频繁，成本核算应读供应商当前价格页，并在网关保存 `model_version`、各类 `usage` 和实际账单单价。
- **原文参数·字段·指标**：`window ≥ input_tokens + max_output_tokens`；10%~20% 安全余量；16K 饼图 1500/6000/2000/1500/5000；RAG Top-K；`usage`、`model_version`、`reasoning_tokens`、`max_output_tokens`、`max_completion_tokens`；输入/缓存输入/输出/reasoning tokens 分别计费。

## 1-8. 长上下文窗口会不会取代 RAG？二者分别适合什么场景？

- **一句话核心结论**：不会互相取代——长上下文只提高「单次可容纳的信息量」，RAG 负责「从大规模/动态知识源里挑出该放进来的那一小部分」；取舍要看成本、延迟、命中率和 Lost in the Middle。
- **机制/原理**：长上下文的代价可直接监控：输入 Token 随内容量增加、账单增长，预填充耗时和 TTFT 变长；自注意力 O(N²)，更长上下文还意味着更大攻击面；「信息放进窗口也不等于模型能同等利用每个位置」。RAG 的价值是检索后只把相关 chunk 拼进上下文，避免无关内容推高输入 Token。ai-core-concepts：RAG 挂载可检索知识源（公司规章、产品文档、实时数据库查询结果），可按用户、租户、角色、会话执行权限过滤或个性化检索；RAG 与长期记忆的区别在数据来源和生命周期——前者检索外部知识，后者保存交互中形成、需跨会话复用的信息。
- **工程落地做法**：先用 RAG 控制检索片段数量与排序（Hybrid Search、Reranker），再决定是否需要长窗口；图片进入多模态 RAG 时图片 Token 与文本 Token 一起计入单次预算，批量图片会拉长 TTFT 需单独压测，任务只需 OCR 结果时先提文字再把纯文本送入模型。评测侧用 Recall@k / Context Precision / Context Recall 看检索，用 Faithfulness / Context Usage / Noise Sensitivity 看生成；固定快照回归冻结检索语料与索引，实时能力探针访问当前 Web/API，两条轨道分数不能混成一个总分。
- **常见追问与易错点**：不要说「长上下文 = 全量文档塞进去更好」——检索片段太多反而抓不住真正相关证据；RAG 检索证据能约束回答范围但不能彻底消除幻觉；【补充】长上下文适合「少量文档、需要跨文档全局对照、且对延迟/成本不敏感」的一次性分析，RAG 适合「知识库规模大、频繁更新、需要权限过滤与引用溯源」的场景，二者常组合使用（先检索再放进长窗口），这个取舍框架是整理者归纳，源文档未给固定结论。
- **原文参数·字段·指标**：128K/200K/1M；O(N²)；TTFT；Recall@k、Context Precision、Context Recall、Faithfulness、Context Usage、Noise Sensitivity；Hybrid Search、Rerank、Parent-Child Chunk（ai-core-concepts：约 300 Token 子块建索引、关联约 1200 Token 父段落，300/1200 只是起始参数）。

---

# 二、API 调用工程（8 题）

相关内容：[《大模型 API 调用工程实践：流式输出、重试、限流与结构化返回》]。原文定位：模型 API 的响应时间、计费方式和错误类型都与普通业务接口不同，面试通常把 Streaming、重试、幂等、限流和模型网关放在一条调用链里考察。原文开篇列出的真实故障：用户等 8 秒看不到第一个字直接刷新页面；模型返回半截 JSON `{"answer": "根因是` 前端解析失败；供应商偶发 429 服务疯狂重试越重试越被限流；用户点取消浏览器断开但后端还在消耗 Token；同一业务请求因重试执行两次，落库、扣费、发通知全重复。

## 2-1. 大模型 API 调用的完整链路是什么？

- **一句话核心结论**：一次调用要按「业务请求进入 → 上下文组装 → Token 预算预估 → 模型网关路由 → 供应商 API 调用 → 响应解析 → 状态回写 → 观测与告警」8 个阶段治理，不能只封装成一个 HTTP 请求。
- **机制/原理**：请求会跨过业务系统、上下文系统、模型网关、外部供应商和前端展示层，任何一段缺少状态与错误处理，最后都表现成「模型不稳定」。8 阶段原文：①业务请求进入：校验用户身份、租户、套餐、功能权限、请求大小；②上下文组装：拼 System Prompt、用户输入、历史消息、RAG 证据、工具 Schema、输出格式约束；③Token 预算预估：估算输入 Token、预留输出 Token，决定是否裁剪历史、压缩上下文或换小模型；④模型网关路由：选择模型、供应商、区域、超时参数、重试策略、限流桶；⑤供应商 API 调用：同步或流式返回，可能经 SSE、WebSocket 或普通 HTTP 响应体；⑥响应解析：处理 delta、finish reason、tool call、usage、拒答、结构化 JSON、异常中断；⑦状态回写：保存完整回答、增量片段、Token 用量、调用成本、失败原因和业务状态；⑧观测与告警：记录 traceId、providerRequestId、TTFT、总耗时、重试次数、429 次数、解析失败率。
- **工程落地做法**：模型调用收口到统一的 `LLMGateway` / 共享客户端层，由它处理 API Key、超时、重试、限流、日志和供应商切换，避免每个业务模块形成略有差异的失败语义。Java 参考实现 `LLMGateway` 聚合 `LLMClient`、`RateLimiter`、`IdempotencyStore`、`TokenEstimator`、`Observation`；`chatWithRetry` 流程：取 `idempotencyKey` → `buildRequest` → `requestFingerprint` → `idempotencyStore.claim()` → 已完成直接返回历史结果 / 非 owner 抛冲突 → `tokenEstimator.estimate()` → `rateLimiter.acquire(tenantId, model, budget)` → `RetryPolicy.defaultPolicy()` 循环（attemptId = idemKey + ":attempt:" + attempt）→ `parseAndValidate(content, schema)` → `markSuccess` / `markFailed` / `observation.recordSuccess`；`stream` 分支用 `StreamBuffer` + `sequence` 去重、`markInterrupted` 处理断流。业务入口不直接调供应商 SDK；先估算 Token 并扣限流桶；幂等记录包住整次业务消息，attempt 只是系统内部重试；同步和流式分开处理；结构化解析在落库前做。
- **常见追问与易错点**：`claim` 必须落到 Redis `SET NX`、数据库唯一约束或带条件的原子更新，不能用「先查询、再写入」代替；幂等键还要绑定请求指纹，同一个键对应不同请求应返回冲突而不是历史结果；上线前补充 API Key 池和供应商路由、模型优先级和降级、Prompt 版本号、响应内容安全审查、usage 成本计算、traceId 与 providerRequestId 对齐、流式取消信号向供应商传播、SSE 出站契约。
- **原文参数·字段·指标**：8 阶段；`LLMGateway`、`LLMClient.chat/stream`、`StreamHandler(onStart/onDelta/onComplete/onError)`、`RateLimiter`、`IdempotencyStore`、`TokenEstimator`、`Observation`、`IdempotencyClaim`、`RetryPolicy.defaultPolicy()`、`requestFingerprint`、`attemptId`、`StreamBuffer`、`markInterrupted`、`NonRetryableLLMException`；traceId、providerRequestId、TTFT、总耗时、重试次数、429 次数、解析失败率。

## 2-2. Streaming 为什么能改善用户体验？它能减少总耗时和 Token 成本吗？

- **一句话核心结论**：Streaming 边生成边返回，把首字等待时间（TTFT）从「等完整答案」缩短到「等第一个片段」，因此改善体验；但它不减少总生成 Token，不保证端到端总耗时变短，也不天然省钱。
- **机制/原理**：TTFT（Time To First Token）指从请求发出到收到第一个可展示 Token 的时间。同步返回要等模型生成完全部内容再一次性返回，例如要生成 800 个 Token，后端必须等这 800 个都完成；流式只需等到第一个片段，用户就能看到内容逐步出现。原文强调：「流式输出没有让模型少算 Token，也不会天然省钱。它缩短的是首字等待时间，并不一定缩短整次生成的耗时」；流式输出不一定降低总耗时（E2E latency），不会自动省钱（Token 计费不变，仍受限流和配额影响），需要结构化输出时还要考虑「半成品 JSON」在前端/网关层的处理。
- **同步 vs 流式对比表（原文，保留）**：

| 对比项 | 同步返回 | 流式返回 |
| --- | --- | --- |
| 首字延迟 | 高，需要等完整结果 | 低，收到第一个片段即可展示 |
| 端到端总耗时 | 取决于完整生成时间 | 通常仍取决于完整生成时间 |
| 前端体验 | 像提交表单后等待结果 | 像聊天软件逐字出现 |
| 后端实现 | 简单，拿到完整字符串再处理 | 复杂，需要处理增量事件、取消、断流 |
| 结构化解析 | 简单，完整 JSON 一次解析 | 需要缓存完整内容，或使用增量解析器 |
| 适合场景 | 短文本、后台任务、严格事务 | 聊天、写作、报告生成、长回答 |
| 不适合场景 | 用户强交互的长回答 | 强事务、必须一次性校验完整结果的链路 |

- **工程落地做法**：面向用户展示的长文本优先流式；后台批处理和必须拿到完整对象才能提交的任务适合同步。流式结构化返回不要一边收 delta 一边 `JSON.parse()` 完整对象：增量阶段只展示文本或记录片段，等收到正常结束事件后拼成完整内容再做 Schema 校验；若供应商支持结构化流式事件或 SDK accumulator 可用官方累积器，否则自维护 buffer、sequence 和结束状态。
- **常见追问与易错点**：把「TTFT 降低」误答成「总耗时降低 / 省钱」是最常见错；取消、超时、断流、重连要设计成不同状态；用户取消时后端要同时取消到供应商 API 的请求、正在解析的响应流、后续 TTS/工具调用/落库任务、还没提交的增量缓存，不能只在前端停止展示（前端停了供应商仍在生成，Token 继续消耗）。
- **原文参数·字段·指标**：TTFT、E2E Latency、800 个 Token 示例、`finish_reason`、delta、sequence、Accumulator。

## 2-3. SSE、WebSocket、HTTP Chunked 在流式输出场景下怎么选？

- **一句话核心结论**：SSE 是服务端到客户端单向、浏览器原生 `EventSource` 的最简方案；WebSocket 是双向长连接，适合语音/插话/多人协作；HTTP chunked 只是 HTTP/1.1 的传输机制，不是应用事件协议。
- **机制/原理（对比表，原文保留）**：

| 方式 | 核心特点 | 适合场景 | 边界 |
| --- | --- | --- | --- |
| SSE | 浏览器原生 `EventSource`，服务端到客户端单向推送，格式是 `text/event-stream` | 文本聊天、模型增量输出、状态通知 | 单向通信；复杂双向控制需要额外 HTTP 请求 |
| WebSocket | 双向长连接，客户端和服务端都能随时发消息 | 实时语音、多人协作、需要频繁取消或插话 | 连接管理更复杂，网关、鉴权、心跳都要自己管好 |
| HTTP chunked | HTTP/1.1 的分块传输机制，响应体分块发送 | 后端到后端流式代理、低层传输 | 它是传输机制，不是应用事件协议；HTTP/2 之后有自己的流式机制 |

SSE 事件边界：媒体类型 `text/event-stream`，UTF-8 文本事件流，每个事件由若干行字段组成，**事件之间用空行分隔**，换行可为 `\n` 或 `\r\n`，常见分隔写法 `\n\n` 或 `\r\n\r\n`。字段表（原文保留）：

| 字段 | 作用 |
| --- | --- |
| `data` | 业务载荷；允许多行 `data:`，客户端会按规范拼接 |
| `event` | 自定义事件名；浏览器默认事件类型是 `message` |
| `id` | 事件序号；配合浏览器重连语义可做断点提示 |
| `retry` | 建议的重连间隔（毫秒） |

「空行才是事件分隔符」，单个换行只结束当前字段行；服务端手写 `data:` 时若没给正文每一行加字段前缀，客户端可能丢掉后续行；额外写入空行会提前结束事件，Markdown 列表和代码块很容易触发。
- **工程落地做法**：Spring Boot + Spring AI 用 `@GetMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)` 返回 `Flux<ServerSentEvent<String>>`，用 `ServerSentEvent.<String>builder().id(...).event("token").data(...).retry(Duration.ofSeconds(3)).build()` 避免手写拼串；`ChatClient` 侧启用流式后拿 `Flux<String>`（`chatClient.prompt().system(...).user(...).stream().content()`）再映射成 SSE。不要先把正文 `\n` 替换成字面量 `\\n`（会改变业务文本且要前端反转义）；中间经过自研网关可把增量封装成 JSON 如 `{"sequence":12,"delta":"第一行\n第二行"}`；两种方案都要测试 LF、CRLF、空行、代码块以及断流时的半个事件。WebMVC + `Flux` 只在 Controller 出口用了响应式类型，底层仍是 Servlet 容器，线程池/连接数/超时仍按「长请求」治理，Java 21 虚拟线程可降低「占着平台线程傻等」的成本。Nginx 最小改动：`proxy_buffering off; proxy_cache off; proxy_read_timeout 300s; proxy_set_header Connection ""; add_header Cache-Control no-cache;`，否则 `text/event-stream` 可能被攒够一整块才下发，TTFT 体感回到同步接口。
- **常见追问与易错点**：SSE 的 `EventSource` 有自动重连但大模型输出不是普通新闻推送——重连能否续传取决于服务端是否保存事件序号、增量片段和供应商调用状态，多数情况下供应商侧流已断，无法真正从 Token 级别续上；更稳做法是为每个流式响应生成 `messageId` 和递增 `sequence`、已发送片段写入短期缓存、前端重连先补发已缓存片段，供应商流已结束则提示重新生成而不是假装无缝续写。超时要分三层：连接超时、TTFT 超时、总时长超时，三者分开记录（TTFT 超时通常指向模型排队/上下文过长/供应商抖动；总时长超时可能只是用户让模型写太长）。断流时记录 `finish_reason` 或最后事件状态，无正常结束标记就把本次调用标记为 `INTERRUPTED`，前端展示「已中断，可重新生成」。
- **原文参数·字段·指标**：`text/event-stream`、`EventSource`、`data`/`event`/`id`/`retry`、`message`、`\n\n` / `\r\n\r\n`、`MediaType.TEXT_EVENT_STREAM_VALUE`、`ServerSentEvent<T>`、`Flux<ServerSentEvent<String>>`、`Flux.interval(Duration.ofMillis(500))`、`retry(Duration.ofSeconds(3))`、`Flux<String>`、Java 21 虚拟线程、`proxy_buffering off` / `proxy_read_timeout 300s`、`INTERRUPTED`、`messageId` + `sequence`。

## 2-4. 哪些大模型 API 错误可以重试？哪些错误不能重试？

- **一句话核心结论**：重试的特殊点在于「请求贵」（失败请求也可能消耗配额甚至部分 Token）和「输出非确定」（同样 Prompt 第二次返回可能不同），所以要按错误码严格区分可重试、不可重试和过载状态。
- **错误类型对照表（原文保留）**：

| 类型 | 示例 | 是否建议重试 | 处理方式 |
| --- | --- | --- | --- |
| 网络瞬断 | 连接重置、DNS 抖动、读超时 | 可以 | 指数退避 + 抖动，限制最大次数 |
| 供应商 5xx | 500、502、503、504 | 可以 | 短暂重试，超过阈值切换模型或降级 |
| 供应商过载 | Anthropic 529、类似 overloaded 错误 | 可以 | 慢重试，必要时熔断该供应商 |
| 429 限流 | RPM、TPM、RPD、并发限制超出 | 谨慎 | 优先看 `Retry-After` 和限流头，排队或降级 |
| 流式中断 | 未收到正常结束事件 | 视场景 | 用户可见任务不自动重试，后台任务可幂等重试 |
| 400 参数错误 | Schema 不合法、字段缺失、上下文超限 | 不建议 | 修请求，不要重试同一 payload |
| 401/403 鉴权错误 | API Key 无效、权限不足 | 不建议 | 告警并停用对应 Key |
| 安全拒答 | 内容策略拒绝 | 不建议 | 进入业务拒答流程 |
| 解析失败 | JSON 不完整、字段类型错误 | 可有限重试 | 带失败原因二次修复，最多 1-2 次 |

OpenAI 官方限流文档建议对 rate limit error 使用随机指数退避，并提醒失败请求也会计入每分钟限制；Anthropic 官方错误文档明确列出 429 rate limit、500 api error、504 timeout、529 overloaded。
- **机制/原理**：指数退避随失败次数增加等待时间直到最大等待或最大重试次数，**抖动（Jitter）**给等待时间加随机量，避免所有请求同时重试把刚恢复的系统再次打进限流。公式 `sleep = min(maxDelay, baseDelay * 2^retryCount) + random(0, jitter)`。两条硬约束：最大重试次数通常 **2-3 次**足够；总体截止时间按用户请求 SLA，例如 **15 秒**，到点就失败，不要因重试拖成 1 分钟。
- **工程落地做法**：能重试的错误用指数退避 + 抖动 + 最大次数 + 总截止时间；429 优先读 `Retry-After` 或供应商 rate limit header；解析失败带具体校验错误做 1-2 次格式修复，不无限重试；400/401/403/安全拒答修请求或走业务拒答流程，不重试同一 payload。
- **常见追问与易错点**：「429 疯狂重试」是反面教材；「同一 payload 重试 400」无意义；流式中断对「用户可见任务」不自动重试（体验差、浪费），后台任务才幂等重试；失败请求也计入每分钟限制。
- **原文参数·字段·指标**：500/502/503/504/529/429/400/401/403；`Retry-After`；`sleep = min(maxDelay, baseDelay * 2^retryCount) + random(0, jitter)`；2-3 次；15 秒 SLA；1-2 次格式修复；RPM/TPM/RPD。

## 2-5. 为什么大模型调用必须做幂等？

- **一句话核心结论**：只要有重试就必须讨论幂等；涉及落库、扣费、发通知或工具写操作时，必须防止同一业务请求被执行多次；纯文本生成不一定要求业务幂等，但重试仍可能产生重复费用和多个候选结果。
- **机制/原理**：原文两个坑：用户狂点「重新发送」后端创建多个模型调用；网关超时后自动重试，第一次其实已成功落库，第二次又写了一条重复消息。幂等 Key 由业务生成，例如 `tenantId:userId:conversationId:messageId:attemptGroup`。服务端拿到请求先查 Key：已成功 → 直接返回历史结果；正在生成 → 返回同一个流式任务的订阅地址；失败且允许重试 → 创建新的 attempt 但仍挂在同一业务消息下；失败但不可重试 → 直接返回失败原因。
- **工程落地做法**：响应重复处理要把一次用户消息下的多次模型调用区分为 `message_id`（业务消息 ID，对用户可见）、`attempt_id`（模型调用尝试 ID，对系统可见）、`provider_request_id`（供应商请求 ID，用于排查）、`stream_sequence`（增量片段序号，用于去重和补发）；落库时只允许一个 attempt 成为 `final`，其他保留为诊断记录，不参与用户上下文。`claim` 用 Redis `SET NX`、数据库唯一约束或带条件原子更新；幂等键绑定请求指纹，同一个键对应不同请求返回冲突。工具调用链路上 `idempotencyKey` 应由可信执行层根据业务请求 ID、动作和资源生成，而不是接收模型提供的键，数据库用唯一约束兜底，外部支付/退款接口携带相同幂等号。
- **常见追问与易错点**：「先查询、再写入」不能代替原子 claim；幂等键不绑定指纹会串结果；「纯文本生成不需要任何幂等」也不准确（重复费用与多候选）；如果一个工具不能安全重试，它就不应该被 Agent 随意调用。
- **原文参数·字段·指标**：`tenantId:userId:conversationId:messageId:attemptGroup`、`message_id`、`attempt_id`、`provider_request_id`、`stream_sequence`、`final`、Redis `SET NX`、请求指纹、`idempotencyKey`。

## 2-6. 大模型限流为什么不能只按 QPS 做？

- **一句话核心结论**：传统 API 按 QPS 限流不够，因为大模型 API 的成本和压力主要由 Token 决定，一次「请求」之间的资源消耗可能差几个数量级。
- **机制/原理**：原文例子：请求 A 输入 500 Token、输出 100 Token；请求 B 输入 80K Token、输出 8K Token。都是 1 次请求，但对模型推理、供应商配额和账单的压力完全不是一个量级。至少要同时看 **RPM**（每分钟请求数）、**TPM**（每分钟 Token 数）、**并发数**、**上下文大小**（单请求输入 Token）、**最大输出**（`max_tokens` 或类似参数）、**日/月预算**（租户或用户总成本）。Gemini 官方限流文档把维度拆成 RPM、输入 TPM、RPD，并说明限制按项目而不是单个 API Key 应用；OpenAI 官方文档展示请求数、Token 数、剩余额度等 rate limit header；具体数值和模型关系变化很快，生产系统不要把静态数字写死，要从控制台、响应头或配置中心动态管理。
- **工程落地做法**：请求进入网关后先估算 `input_tokens + reserved_output_tokens`，在用户、租户、模型、供应商几个桶里尝试扣减，扣不到就不发给供应商，直接排队、降级或拒绝——「请求应先扣预算，再发给供应商」。限流四层架构（原文保留）：

| 层级 | 限制对象 | 核心目的 | 常见策略 |
| --- | --- | --- | --- |
| 用户级 | 单个用户或账号 | 防止滥用、误操作、脚本刷接口 | 每分钟请求数、每日 Token 上限 |
| 租户级 | 企业、团队、项目 | 控制套餐成本和公平性 | 月度配额、并发上限、优先级队列 |
| 模型级 | 某个模型或模型族 | 避免热门模型被打满 | 模型维度令牌桶、降级到备用模型 |
| 供应商级 | OpenAI、Anthropic、Gemini 等 | 保护外部依赖和 API Key | 全局 RPM、TPM、并发、熔断 |

限流策略对比（原文保留）：

| 策略 | 适合场景 | 优点 | 缺点 |
| --- | --- | --- | --- |
| 固定窗口 | 简单后台任务、管理接口 | 实现简单，容易统计 | 窗口边界容易突刺 |
| 滑动窗口 | 用户级请求限制 | 边界更平滑 | 实现和存储成本更高 |
| 令牌桶 | 模型调用、Token 预算 | 支持一定突发，工程上常用 | 参数需要调优 |
| 漏桶 | 严格平滑出流量 | 输出稳定，适合保护供应商 | 突发体验差 |
| 并发信号量 | 流式生成、长任务 | 能限制同时占用连接 | 不控制单个请求 Token 成本 |
| 优先级队列 | 多租户、多套餐 | 能保护高优先级请求 | 需要处理饥饿和超时 |

生产组合：用户级 滑动窗口 + 日 Token 上限；租户级 令牌桶 + 月度预算；模型级 令牌桶 + 并发信号量；供应商级 全局令牌桶 + 熔断器；流式请求 并发信号量 + 总时长限制。收到 429 的处理顺序：①读 `Retry-After` 或供应商 rate limit header；②标记限流维度（请求数打满 / Token 打满 / 日配额耗尽）；③短请求可排队（后台摘要进延迟队列）；④用户交互请求少重试（提示稍后再试或切换轻量模型）；⑤供应商连续 429 时熔断。典型降级链路：`优先模型可用 -> 正常调用` → `优先模型 429 -> 切备用同级模型` → `备用模型也限流 -> 切轻量模型并缩短输出` → `仍不可用 -> 排队或返回"当前请求繁忙"`。
- **常见追问与易错点**：「收到供应商 429 才开始限流」说明系统缺少自己的容量管理，429 只能作为外部保护信号；降级不是偷偷变差，若轻量模型影响答案质量要在业务层明确标记（例如「当前为快速模式，复杂问题建议稍后重试」）。
- **原文参数·字段·指标**：RPM、TPM、RPD、QPS、并发数、`max_tokens`、`input_tokens + reserved_output_tokens`、500/100 vs 80K/8K、`Retry-After`、四层桶、令牌桶/漏桶/滑动窗口/固定窗口/并发信号量/优先级队列/熔断器。

## 2-7. 模型网关通常要承担哪些能力？

- **一句话核心结论**：`LLMGateway` 是应用层和模型供应商之间的统一治理入口，把 API Key、超时、重试、限流、日志、供应商切换和模型选择收口，避免每个业务模块形成不同的失败语义。
- **机制/原理**：ai-core-concepts 原文：LLM Gateway 除了处理鉴权、限流、转发等普通 API 问题，还要管理模型选择、Token 预算、上下文长度、供应商差异、流式输出、工具调用、结构化响应、成本统计和 Prompt 版本。生产级 AI 应用架构中「Prompt 与 Context 管理」负责管理模板版本、变量注入、Token 预算、灰度发布和回滚，「评测与观测层」负责记录调用链、版本、质量、延迟、成本和 Badcase，支持回放与发布门禁。
- **工程落地做法**：网关承担 8 阶段中的路由（模型/供应商/区域/超时/重试/限流桶）、预算预估与扣减、幂等、响应解析与结构化校验、状态回写、观测与告警；真实项目还要补充 API Key 池和供应商路由、模型优先级和降级策略、Prompt 版本号、响应内容安全审查、usage 成本计算、traceId 与 providerRequestId 对齐、流式取消信号向供应商请求传播、SSE 出站契约。成本核算在网关保存 `model_version`、各类 `usage` 和实际账单单价。
- **常见追问与易错点**：不要把供应商静态数字写死在业务代码里，要从控制台/响应头/配置中心动态管理；网关前面挂 Nginx 等缓冲型网关时必须关闭 buffering，否则流式失效；网关要能承载降级/熔断而不是只做转发。
- **原文参数·字段·指标**：`LLMGateway`、API Key 池、供应商路由、模型优先级、`model_version`、`usage`、`prompt_version`、traceId / providerRequestId、TTFT、429 Rate、Parse Failure Rate、Provider Error Rate、Cancel Rate。

## 2-8. AI 应用的调用日志里至少要记录哪些字段？

- **一句话核心结论**：AI 应用的观测不能只记录「成功/失败」，日志要能串起 `messageId`、`attemptId`、`providerRequestId`，并保存 TTFT、总耗时、usage、结束原因与解析结果。
- **观测指标表（原文保留）**：

| 指标 | 含义 | 用途 |
| --- | --- | --- |
| TTFT | 首个 Token 返回时间 | 判断排队、上下文过长、供应商抖动 |
| E2E Latency | 端到端完成时间 | 判断用户体验和 SLA |
| Input Tokens | 输入 Token | 成本分析、上下文膨胀排查 |
| Output Tokens | 输出 Token | 成本分析、异常长回答排查 |
| Retry Count | 重试次数 | 识别供应商不稳定或策略过激 |
| 429 Rate | 限流比例 | 判断配额和限流桶是否合理 |
| Parse Failure Rate | 结构化解析失败率 | 判断 Schema、Prompt、模型适配问题 |
| Cancel Rate | 用户取消比例 | 判断响应太慢或生成太长 |
| Provider Error Rate | 供应商错误率 | 路由、降级、熔断依据 |

日志建议字段（原文代码块，逐字保留）：

```
trace_id
tenant_id
user_id
conversation_id
message_id
attempt_id
model
provider
prompt_version
input_tokens
output_tokens
ttft_ms
latency_ms
retry_count
finish_reason
error_type
provider_request_id
```
- **工程落地做法**：原文：「没有这些字段，线上排查会非常痛苦。用户说『刚才 AI 没返回』，你连是哪家供应商、哪个模型、哪次 attempt、有没有收到第一个 delta 都查不到。」落地时每次调用至少保存模型版本、输入 Token、缓存 Token、推理 Token（若供应商返回）、输出 Token、上下文裁剪策略和采样参数；上线门禁要求观测记录能串起 `messageId`、`attemptId` 和 `providerRequestId`，并保存 TTFT、总耗时、usage、结束原因与解析结果。ai-core-concepts 的可观测性三支柱里 Metrics 关注「系统整体是否异常」：请求量、错误率、P95 延迟、Token 用量、工具失败率。
- **常见追问与易错点**：不要只记成功/失败；`finish_reason`（尤其 `length` 截断）和 `error_type` 是定位断流与截断的关键；审计日志字段要白名单化（见 3-9），敏感明文禁止进普通日志。
- **原文参数·字段·指标**：上表 9 个指标 + 17 个日志字段；`finish_reason=length`；P95 延迟、工具失败率。

---

# 三、结构化输出与工具调用（10 题）

相关内容：[《大模型结构化输出：从 JSON 契约到 Function Calling 落地》]。原文定位：模型输出只要进入业务系统，就要处理格式校验、字段约束和执行权限；这里容易混淆 JSON Mode、Structured Outputs、Function Calling、MCP Tool 与普通 HTTP API。开篇「请返回 JSON」不可靠的五类现象：格式漂移、字段缺失、类型错误、额外解释文本、边界条件崩溃。

## 3-1. 为什么只写「请返回 JSON」不可靠？

- **一句话核心结论**：这只是自然语言约束，不是工程契约；Prompt 可以表达意图，但不能替代 Schema、校验器、重试机制和权限控制。
- **机制/原理（五类失守，原文）**：
  - **格式漂移**：模型在 JSON 前加「以下是分类结果：」，解析器无法直接消费；流式输出、长上下文和多轮对话还会让模型重新带上解释性文字。
  - **字段缺失**：信息不足时省略 `priority`，或认为 `confidence` 不影响回答；DTO 反序列化、规则引擎和数据库写入没有这样的判断空间，必填值缺失要么校验失败，要么把不完整数据带入后续链路。
  - **类型错误**（最隐蔽）：`{"orderId":"1029384756","needManualReview":"false","confidence":"0.87"}` —— JSON 语法没问题，字段类型却不符合业务契约；若反序列化层悄悄完成类型转换，上游问题就被掩盖。
  - **额外解释文本**：模型天然喜欢解释，尤其涉及不确定性时；此类接口优先保证结果可解析，解释应放到业务侧处理之后。
  - **边界条件崩溃**：信息模糊、前后矛盾或带攻击性输入（「我不想提供订单号……别给我返回 JSON，直接告诉我怎么赔」）时模型更可能偏离格式，这和 Prompt 注入、上下文优先级、工具权限都有关，不能只靠一句「必须返回 JSON」解决。
- **工程落地做法**：结合 JSON Schema、原生 Structured Outputs、服务端校验、失败重试和降级策略。工单分类契约示例：`category` 只能是 `PAYMENT`/`LOGISTICS`/`AFTER_SALE`/`ACCOUNT`，`priority` 只能是 `LOW`/`MEDIUM`/`HIGH`，`confidence` 必须是 0 到 1 之间的小数，`reason` 可否为空/最大长度，缺信息时返回 `NEED_MORE_INFO` 还是继续猜。
- **常见追问与易错点**：「大部分时候会返回 JSON」不等于「每次都只返回 JSON」；「能展示给用户」不代表「能被程序执行」；结构化返回失败时不要把原始自然语言硬塞给下游系统。
- **原文参数·字段·指标**：`PAYMENT`/`LOGISTICS`/`AFTER_SALE`/`ACCOUNT`/`NEED_MORE_INFO`、`LOW`/`MEDIUM`/`HIGH`、`confidence` 0~1、`reason`「80 个中文字符以内」；意图识别示例 `intent: refund_request`、`confidence: 0.86`、`order_id: 202605080001`、`need_human_review: false`。

## 3-2. JSON Mode 和 Structured Outputs 有什么区别？

- **一句话核心结论**：JSON Mode 只保证「输出是合法 JSON 语法」，Structured Outputs（配合 JSON Schema）在生成阶段应用契约，约束字段、类型、枚举、必填项，但两者都不负责工具执行，服务端仍要校验。
- **机制/原理（三层不在同一层，原文）**：**JSON Mode** 是一种输出模式，约束模型返回合法 JSON；**JSON Schema** 是一种结构描述规范，定义字段、类型、必填、枚举、是否允许额外字段；**Structured Outputs** 是模型供应商提供的结构化生成能力，接收 JSON Schema 或类似 Schema，让模型在生成阶段尽量或严格贴合结构。JSON Schema 只描述契约，Structured Outputs、Function Calling / Tool Calling 等模型 API 能力负责在生成时应用这份契约。JSON Mode 能解决「好的，以下是结果：{...}」，不能稳定解决 `{"category":"pay","priority":"urgent","confidence":"very high"}`（合法 JSON 但不是合法业务数据）。三层约束对比表（原文保留）：

| 对比维度 | JSON Mode | JSON Schema | Structured Outputs |
| --- | --- | --- | --- |
| 角色 | 输出格式开关 | 数据结构描述规范 | 模型 API 的结构化生成能力 |
| 主要约束 | JSON 语法合法 | 字段、类型、枚举、必填、额外属性等 | 输出尽量或严格匹配 Schema |
| 是否保证业务字段完整 | 不保证 | 只描述，不执行生成 | 取决于供应商能力和 Schema 支持范围 |
| 是否负责工具执行 | 不负责 | 不负责 | 不负责，只产出结构化结果 |
| 典型用途 | 简单 JSON 输出 | 定义数据契约和校验规则 | 分类、抽取、函数参数生成、Agent 中间结果 |
| 仍需服务端校验 | 需要 | 需要 | 仍然需要 |

api-engineering 里的区别表（约束强度视角，原文保留）：

| 方式 | 约束强度 | 工程价值 | 风险 |
| --- | --- | --- | --- |
| 普通自然语言 | 几乎没有 | 适合展示型回答 | 不适合程序解析 |
| Prompt 要求 JSON | 弱 | 简单、跨模型 | 容易混入解释文本或缺字段 |
| JSON Mode | 中 | 通常能保证语法是 JSON | 不一定符合业务字段 Schema |
| JSON Schema | 强 | 明确字段、类型、必填、枚举 | 不同供应商支持子集不同 |
| Structured Outputs | 更强 | 供应商在解码或 SDK 层增强约束 | 受模型、SDK、Schema 子集限制 |
| Function Calling / Tool Use | 面向动作 | 适合让模型选择工具和参数 | 不是最终自然语言答案的万能替代 |

OpenAI 官方 Structured Outputs 文档强调可让输出遵循开发者提供的 JSON Schema 并提供 `strict` 相关配置；Gemini 用 `response_format` 和 JSON Schema，支持的是子集；Anthropic 提供 Structured Outputs 和 Strict tool use，二者解决的问题并不完全一样。OpenAI、Anthropic、Gemini 都已提供原生结构化输出能力，不应再概括成「只有 OpenAI 严格约束，其他厂商主要靠 Prompt」，三家的模型覆盖范围、拒答和截断语义、Schema 子集以及首次编译延迟不同。
- **工程落地做法**：两类落点——**响应结构化输出**（最终回答就是符合 Schema 的 JSON，如工单分类、信息抽取、情感打分，后端直接反序列化）与**工具参数结构化输出**（模型输出工具名和 arguments，arguments 符合工具参数 Schema）。结构化输出失败分四级兜底（见 3-8）。
- **常见追问与易错点**：不同供应商支持的 JSON Schema 子集不完全一致，`pattern`、`format`、递归 `$ref`、组合关键字 `allOf`/`oneOf`/`anyOf` 支持程度不同，不要照搬完整规范，先读「supported schemas」；模型返回拒答、达到 Token 上限或工具执行失败时，不能把「支持 Structured Outputs」理解成业务请求一定成功。
- **原文参数·字段·指标**：`strict`、`response_format`、`additionalProperties`、`required`、`enum`、`pattern`/`format`/`$ref`/`allOf`/`oneOf`/`anyOf`；Strict tool use；Strict Mode。

## 3-3. JSON Schema 在大模型应用里解决什么问题？

- **一句话核心结论**：它把「输出应该长什么样」变成可校验的数据契约——既给模型提供结构化约束，也给服务端做兜底校验，但不负责生成和外部调用。
- **机制/原理**：根据 JSON Schema 官方文档，`properties` 定义对象有哪些属性，`required` 声明必填字段，`additionalProperties` 控制是否允许未声明字段，`enum` 把取值限制在固定集合里；此外还有 `type`、`description`、`minimum`、`maximum`、`pattern`、`minLength`、`const`、`oneOf` 等。原文工单分类 Schema 完整示例（保留）：

```json
{
  "type": "object",
  "properties": {
    "category": {
      "type": "string",
      "enum": ["PAYMENT", "LOGISTICS", "AFTER_SALE", "ACCOUNT", "NEED_MORE_INFO"],
      "description": "工单分类。信息不足时选择 NEED_MORE_INFO。"
    },
    "priority": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH"],
      "description": "处理优先级。涉及资金损失、无法下单、批量影响时优先级更高。"
    },
    "confidence": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "分类置信度，范围为 0 到 1。"
    },
    "reason": {
      "type": "string",
      "description": "分类依据，控制在 80 个中文字符以内。"
    }
  },
  "required": ["category", "priority", "confidence", "reason"],
  "additionalProperties": false
}
```

- **工程落地做法（Schema 设计 7 条，原文）**：①一个字段只表达一件事（坏设计 `"result": "支付问题，高优先级，需要人工处理"` → 好设计拆 `category`/`priority`/`needManualReview`/`reason`），字段越原子越易校验、统计、路由、灰度；②字段说明要写「何时用」和「何时不用」（很多工具误调用根源在字段描述太模糊，要写清适用条件、排除条件和可选值，篇幅长短次要）；③枚举优先于自由文本（分类、状态、动作类型、风险等级能用 `enum` 就不用自由文本，否则 `"urgent"` 到底当 `HIGH` 还是非法值，模糊映射等于把模型不确定性扩散进业务规则）；④必填字段要谨慎但不要偷懒（严格模式常见约束 `additionalProperties: false`、所有声明属性都必须出现在 `required`、对象必须显式声明 `type`、只接受 JSON Schema 一部分关键字；字段不存在应表示协议异常而非「未知」，未知值用 `null` 如 `"refundId": null` 或状态字段 `"status": "NEED_MORE_INFO"` 表达）；⑤版本兼容：增加 `schemaVersion`（如 `ticket_classification_v1`），新增字段尽量可选、删除字段先灰度、新增枚举确认旧消费者可识别，Prompt/Schema/解析代码/看板指标使用同一版本边界；⑥校验失败重试：把校验错误反馈给模型只修结构（见 3-8）；⑦降级策略（见 3-8）。
- **常见追问与易错点**：Schema 太复杂会增加模型理解和供应商兼容成本；「Schema 越复杂越好」「用了 Structured Outputs 就不用校验」均为误区；字段不存在 ≠ 未知，不能让模型靠编造值填满 Schema。
- **原文参数·字段·指标**：`properties`、`required`、`additionalProperties`、`enum`、`type`、`description`、`minimum`/`maximum`（0~1）、`pattern`（`^O[0-9]{12,20}$`）、`const`（`query_order_v1`）、`schemaVersion`、`ticket_classification_v1`、`query_order_v1`、`$schema: https://json-schema.org/draft/2020-12/schema`。

## 3-4. Function Calling 的完整链路是什么？

- **一句话核心结论**：模型只生成「调用哪个工具、参数是什么」的结构化意图，真正执行工具的是业务服务、Agent Runtime、MCP Host 或供应商托管环境；执行权始终在业务侧。
- **机制/原理（7 步链路，原文）**：①服务端注册工具定义（工具名、用途描述、参数 Schema）；②用户发起请求（「帮我查一下订单 1029384756 到哪了」）；③模型选择工具 `query_order` 并生成参数 `{"orderId": "1029384756"}`；④业务侧校验参数（类型、必填、权限、订单归属、幂等键等）；⑤业务侧执行工具（订单系统、数据库或 HTTP API）；⑥工具结果回填模型，结果连同 `tool_use_id` 原样发回（Anthropic 要求 `tool_use_id` 严格匹配，Gemini 3 同样为每个 `functionCall` 生成唯一 `id`，回填必须带回，否则并行调用场景下结果会错配）；⑦模型生成最终回答。Anthropic 工具调用流程中 Claude 返回结构化调用，客户端工具由应用执行，结果通过 `tool_result` 回传；Gemini 也把「选择函数和填充参数」交给模型，实际调用留在应用侧。
- **机制/原理（语义鸿沟）**：用户说「我昨天买的那台咖啡机还没发货，帮我查下」，后端 API 需要 `{"userId":"U10086","orderId":"O202605070001","includeLogistics":true}`；Function Calling 的价值是完成「自然语言意图 → 结构化参数」映射，但只负责映射，不负责替你绕过权限、查数据库、扣库存、发短信。
- **工程落地做法**：Java `ToolCallDispatcher` 串起必要步骤：先按工具名分发（未知工具直接拒绝 `UNSUPPORTED_TOOL`）→ Jackson 解析 + JSON Schema Validator（networknt `JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V202012)`）做结构校验 → 权限校验 `permissionService.canReadOrder()` → 工具返回结构化结果 `ToolResult.success(payload)` → 全链路审计 `AuditEvent`。错误码 `INVALID_ARGUMENTS`/`FORBIDDEN`/`ORDER_NOT_FOUND`/`TOOL_EXECUTION_FAILED`。`ToolCall(String callId, String name, String argumentsJson)` 中 `callId` 用于回填模型（Anthropic `tool_use_id` / Gemini `functionCall.id` 必须原样带回）。只读工具的参数 Schema 不接收幂等键，写操作由服务端或 Runtime 在权限校验后生成幂等键并用 Redis `SET NX`、条件写入或数据库唯一索引去重。
- **常见追问与易错点**：「模型执行了你的 Java 方法」是新人误解；并行调用缺 ID 会错配；「如果你把模型输出的参数直接传给订单服务，等于把业务系统的入口暴露给一个概率模型」；工具调用只完成意图与参数映射，权限、资源归属、业务状态和副作用仍由执行层判断。
- **原文参数·字段·指标**：`query_order`、`{"orderId":"1029384756"}`、`tool_use_id`、`tool_result`、`functionCall.id`、`callId`、`userId: U10086`、`orderId: O202605070001`、`includeLogistics: true`、JSON-RPC 2.0、`tools/call`。

## 3-5. Function Calling 和 MCP 有什么区别？

- **一句话核心结论**：Function Calling 是模型侧「自然语言 → 工具名和参数」的调用意图生成机制；MCP 是应用层协议，负责工具如何被标准化发现、描述、调用和返回结果；MCP 可以承载工具生态，Function Calling 可作为模型选择 MCP 工具时的底层能力之一。
- **机制/原理**：Function Calling 是模型供应商侧机制，各家请求和响应格式有差异。MCP Tool 是 MCP 协议里的工具能力：根据 MCP 官方规范，MCP 允许 Server 暴露可由语言模型调用的工具，工具包含名称和描述其 Schema 的元数据；MCP 客户端与服务器之间的消息遵循 **JSON-RPC 2.0**。一个支持 MCP 的 Agent Runtime 可以先通过 MCP 发现工具，再把这些工具定义转换成某个模型供应商的 Function Calling 格式传给模型；模型选择工具后，Runtime 再把调用转成 MCP 的 `tools/call` 请求。
- **工程落地做法**：按「结果会不会触发外部动作、工具需要在多少个客户端复用」选型（见 3-10 选型表）；工具很多、客户端很多、希望跨 IDE 或跨 Agent 复用，考虑 MCP。
- **常见追问与易错点**：原文明确「这些概念没有固定的 Skill → MCP → Function Calling → HTTP API 层级」，可以按需组合；「这只是常见适配方式，不是 MCP 的协议前提」——MCP Client 也可以由规则引擎、用户界面或其他程序直接发起 `tools/call`，MCP Server 可访问 HTTP API、数据库、本地文件或进程，不要求底层再经 Function Calling。
- **原文参数·字段·指标**：JSON-RPC 2.0、`tools/call`、MCP Client / MCP Server / MCP Host、工具名称 + 描述 Schema 的元数据。

## 3-6. MCP Tool 和普通 HTTP API 有什么关系？

- **一句话核心结论**：HTTP API 是面向程序调用的确定性业务接口；MCP Tool 是暴露给 AI Host 的标准化工具能力，可以在内部再调用 HTTP API、数据库或本地脚本；MCP 解决接入标准化，HTTP API 解决具体业务能力。
- **机制/原理**：普通 HTTP API 例子 `GET /api/orders/O202605070001`；Function Calling 输出 `{"name":"query_order","arguments":{"orderId":"O202605070001","includeLogistics":true}}`；两者之间通常需要一个工具执行层映射：`模型工具调用 query_order → 服务端校验参数 → 调用 GET /api/orders/{orderId}`。能力定位表（原文保留）：

| 能力 | 定位 | 解决的问题 | 谁来执行 | 典型边界 |
| --- | --- | --- | --- | --- |
| JSON Mode | 输出格式开关 | 让模型输出合法 JSON | 模型侧生成 | 不保证字段和业务语义 |
| JSON Schema | 结构描述规范 | 定义字段、类型、枚举、必填等契约 | 本身不参与生成，只描述结构 | 不负责生成和外部调用 |
| Structured Outputs | 模型 API 结构化生成能力 | 把 Schema 接入生成，让输出贴合结构 | 模型侧生成 + 服务端校验 | 不负责外部系统调用 |
| Function Calling / Tool Calling | 模型到工具的调用意图生成机制 | 自然语言转工具名和参数 | 通常由业务侧或供应商执行 | 不等于 API 本身 |
| MCP | 工具和上下文接入协议 | 标准化工具发现、调用、资源访问 | MCP Client / Server 协作 | 不替代模型推理能力 |
| 普通 HTTP API | 业务服务接口 | 确定性业务读写 | 后端服务 | 不理解自然语言 |
| Agent Skill | 可复用任务说明和执行 SOP | 复杂任务的流程编排和上下文注入 | Agent 按说明执行 | 不一定包含工具调用 |

- **工程落地做法**：「Function Calling 可以包一层 HTTP API，但 HTTP API 本身不是 Function Calling」；MCP Server 实现可访问 HTTP API、数据库、本地文件或进程，不要求底层再经过 Function Calling。
- **常见追问与易错点**：不要把 MCP 理解成「新的 HTTP」或「替代 Function Calling」；MCP 消息是 JSON-RPC 2.0，不直接规定模型输出。
- **原文参数·字段·指标**：`GET /api/orders/{orderId}`、`tools/call`、JSON-RPC 2.0、MCP Client/Server。

## 3-7. Agent Skill 和 Function Calling 是一回事吗？

- **一句话核心结论**：不是。Skill 保存可复用的任务说明和执行 SOP（注入上下文、约束步骤、编排流程），Function Calling 只负责生成工具名和参数；一个 Skill 可以指导 Agent 调用多个 Function Calling 工具或 MCP 工具，也可以完全不调用工具。
- **机制/原理**：Skill 记录任务需要的上下文、执行步骤和处理规则，是「可复用的任务说明书」。原文「线上事故复盘 Skill」示例：①先读取事故时间线 ②再查询监控截图 ③再拉取发布记录 ④最后按「现象、影响、根因、改进项」输出；执行过程中可能调用 MCP 工具，也可能调用 Function Calling 工具，还可能只是纯文本分析。一种常见实现是 Skill 约束 Agent 流程，Runtime 将 MCP 工具定义转换为供应商 Tool Calling 格式，工具执行器把参数映射到 HTTP API；也可以让 MCP Server 直接访问数据库或本地文件，Client 不经过模型就发起 `tools/call`——组件组合取决于运行时，不存在必须经过的固定链路。
- **工程落地做法**：复杂任务有一套固定 SOP 时考虑 Skill，把工具组合和决策过程沉淀下来；Skill 要单独评测（触发用例 / 核心逻辑用例 / 产物质量用例 / 异常容错用例，见 4-5 知识点）。
- **常见追问与易错点**：「Skill 是 Function Calling 的语法糖」是错误命题；Skill 不一定包含工具调用；不要给这些概念排固定层级。ai-core-concepts：Function Calling 让模型表达调用工具的意图，MCP 规定宿主如何发现外部能力并连接后端服务，Agent 负责在多轮执行中决定下一步，Skills 则保存完成某类任务所需的流程和经验。
- **原文参数·字段·指标**：Skill 四类用例（触发/核心逻辑/产物质量/异常容错）、触发召回率、误触发率、产物合格率、异常稳态率、`grilling` 需求澄清 Skill。

## 3-8. 结构化输出失败后怎么处理？

- **一句话核心结论**：先本地校验拿具体错误，再带错误让模型只修格式做有限重试，仍失败就按场景降级；核心原则是「可以降级，但不能让模型编造业务事实」。
- **机制/原理**：失败不一定是供应商能力问题，也可能是 Schema 太复杂、上下文冲突、输出被截断、安全策略拒答。四级兜底：①**本地校验**（JSON Schema、Jackson、Bean Validation 校验字段和类型）；②**轻量修复**（只让模型修复格式，不重新生成业务内容）；③**降级 Schema**（复杂对象拆成多个小对象，或先分类再抽取字段）；④**人工或规则兜底**（高价值订单、金融、医疗、法务场景不要完全依赖自动修复）。
- **工程落地做法**：校验失败重试不要一失败就把原始问题重跑一遍，而是把校验错误反馈给模型只修结构，示例错误 `$.priority: must be one of LOW, MEDIUM, HIGH`、`$.confidence: must be number`，下一轮给「上一次输出没有通过 JSON Schema 校验，请只返回修正后的 JSON，不要添加解释」+ 校验错误 + 原始输出。策略：最多重试 1 到 2 次、每次带明确校验错误、仍失败进入降级、所有失败样本写日志用于优化 Schema 和 Prompt。降级策略表（原文保留）：

| 场景 | 降级策略 |
| --- | --- |
| 工单分类失败 | 进入人工队列，标记 `AI_PARSE_FAILED` |
| 订单查询参数缺失 | 追问用户补充订单号 |
| 风险评分失败 | 使用规则引擎兜底评分 |
| 工具调用超时 | 返回「系统繁忙」，不继续让模型猜 |
| 非关键字段缺失 | 使用默认值，但记录告警 |

api-engineering 四级兜底顺序：本地校验 → 轻量修复 → 降级 Schema → 人工或规则兜底；「结构化返回失败时，不要把原始自然语言硬塞给下游系统。能展示给用户，不代表能被程序执行」。上线前检查（Schema 层 / 模型调用层 / 服务端执行层 / 降级层）逐项：一个字段是否只承载一个业务含义；「信息不足」「无需操作」是否有明确枚举；`required`/`additionalProperties`/字段说明是否写清输入边界；多消费者是否通过 `schemaVersion` 区分版本；是否使用供应商原生 Structured Outputs 或严格工具调用；是否控制输出长度避免截断；是否避免过高采样随机性；是否为校验失败设计重试 Prompt；是否做 Schema/业务/权限校验；写操作是否幂等；高风险操作是否二次确认；工具超时后是否短路；是否有审计日志和 traceId；解析失败是否进入人工队列或规则兜底；工具失败时是否禁止模型编造结果；是否统计失败率、错误类型和高频非法枚举。
- **常见追问与易错点**：「用了 Structured Outputs 就不用校验」错误；服务端仍要防御非法参数、越权访问、重放请求和业务状态冲突；`finish_reason=length` 截断与误触 Stop Sequences（如 `"\n\n"`、` ``` `）要分别覆盖两条失败路径。
- **原文参数·字段·指标**：`AI_PARSE_FAILED`、`$.priority: must be one of LOW, MEDIUM, HIGH`、`$.confidence: must be number`、1~2 次重试、`finish_reason=length`、Stop Sequences、JSON Schema / Jackson / Bean Validation。

## 3-9. 工具调用为什么必须做安全治理？

- **一句话核心结论**：模型给出的工具参数属于不可信输入，Schema 只能检查类型和结构，检查不了业务权限；查询通常只读一条受权限约束的数据，退款/删数据/发短信/执行 SQL 会改变系统状态，必须使用更严的执行条件。
- **机制/原理**：三层校验——**结构校验**（类型、必填、枚举、长度、格式）、**业务校验**（订单归属、状态流转、库存、金额范围）、**权限校验**（用户身份、角色、租户、数据范围）。Schema 只能知道 `{"orderId":"O202605070001"}` 是一个字符串，不知道订单是不是当前用户的、是否已退款、用户是否有客服权限。风险等级分层表（原文保留）：

| 风险等级 | 工具类型 | 控制策略 |
| --- | --- | --- |
| 低风险 | 查询天气、读取公开文档 | 基础限流和日志 |
| 中风险 | 查询订单、查询用户资料 | 身份校验、数据范围校验 |
| 高风险 | 退款、发券、改地址、发短信 | 权限校验、二次确认、审计 |
| 极高风险 | 删除数据、执行 SQL、批量操作 | 默认禁止，走人工审批或专用后台 |

- **工程落地做法**：①参数校验三层；②权限控制不要把内部管理工具直接暴露给所有用户场景；③敏感操作二次确认，高风险工具拆两步 `prepare_refund`（生成退款预案，返回金额、原因、影响）和 `confirm_refund`（用户或客服确认后执行），「模型负责整理信息和建议动作，人类或业务规则负责最后确认」；④幂等由可信执行层生成 `idempotencyKey`，数据库唯一约束兜底，外部支付/退款接口携带相同幂等号，同一请求再次到达返回已有结果；⑤审计日志先定义字段白名单——工具名、校验结论、结果码、耗时、模型版本、Schema 版本和 traceId 通常可直接记录，订单号/userId 等标识符按排障需求做掩码、哈希或令牌化，密码、令牌、支付数据、私钥和原始文档正文禁止进入普通日志，确实需要保留敏感原文时写入单独受控审计存储（访问审批、加密、保留期、删除流程）；日志内容本身也属不可信输入，展示和导出要防日志注入，限制谁能按 `traceId` 反查用户请求（参考 OWASP Logging Cheat Sheet）；⑥超时和重试：查询类工具设置较短超时，写操作谨慎重试必须配幂等，外部依赖失败返回明确错误码，模型拿到工具错误后只能解释「当前无法完成」不能猜测结果。
- **常见追问与易错点**：「Function Calling 可以绕过业务权限」是误区——权限控制必须在服务端，不能藏在 Prompt 里，Prompt 里的「不要越权查询」只算提醒不算安全边界；「工具越多 Agent 越强」也是误区，工具越多误调用概率越高，设计要小而清晰。
- **原文参数·字段·指标**：`prepare_refund` / `confirm_refund`、`idempotencyKey`、`traceId`、`AI_PARSE_FAILED`、结构/业务/权限三层校验、字段白名单、掩码/哈希/令牌化、OWASP Logging Cheat Sheet。

## 3-10. 面试里怎么一句话概括结构化输出？

- **一句话核心结论**：结构化输出 = 用 JSON Schema 把「模型输出」变成可校验的数据契约，用 Structured Outputs / Function Calling 在生成阶段应用契约，再由服务端做校验、重试和降级兜底；目的是让程序能稳定消费，而不只是「看起来像 JSON」。
- **机制/原理**：原文一句话式表述可直接引用：「JSON Mode 约束语法，JSON Schema 描述契约，Structured Outputs 在生成阶段应用契约。服务端仍要校验拒答、截断、权限和业务状态。」以及「Prompt 可以表达意图，但不能替代 Schema、校验器、重试机制和权限控制。结构化输出让模型结果进入一套可校验的工程契约。」选型视角的完整表（原文保留）：

| 维度 | JSON Mode | JSON Schema | Structured Outputs | Function Calling / Tool Calling | MCP |
| --- | --- | --- | --- | --- | --- |
| 所在层次 | 模型输出格式层 | 结构描述规范层 | 模型结构化生成层 | 模型工具意图层 | 应用协议层 |
| 输入给模型的内容 | 「输出 JSON」的模式开关 | 不直接参与生成 | Schema 或响应格式定义 | 工具名、工具描述、参数 Schema | 通常由 Host 转换后给模型，协议本身在 Client 和 Server 间通信 |
| 模型输出 | JSON 文本 | — | 符合 Schema 的结构化对象 | 工具名 + 参数，或最终回答 | 不直接规定模型输出，规定 MCP 消息 |
| 是否调用外部系统 | 否 | 否 | 否 | 生成调用意图，执行在外部 | 是，MCP Client 调 MCP Server |
| 是否跨模型标准化 | 各厂商实现不同 | 规范通用，可跨模型复用 | Schema 支持子集各厂商不同 | 各厂商格式不同 | 目标是标准化工具和上下文接入 |
| 适合场景 | 简单结构化文本 | 定义数据契约和校验规则 | 数据抽取、分类、参数生成 | 订单查询、发邮件、查库存等工具任务 | 多工具、多客户端、团队共享工具生态 |
| 主要风险 | 合法 JSON 但字段不对 | 只描述不执行，容易被高估 | Schema 太复杂或支持不一致 | 工具误调用、参数越权 | Server 权限、安全边界、协议兼容 |

选型顺序：先看结果会不会触发外部动作，再看工具需要在多少个客户端复用——只做轻量数据抽取先用 Structured Outputs；需要读写业务系统优先 Function Calling / Tool Calling；工具很多、客户端很多、希望跨 IDE 或跨 Agent 复用考虑 MCP；复杂任务有固定 SOP 考虑 Skill。
- **常见追问与易错点**：五个常见误区（原文）：Temperature 设为 0 就一定稳定（Gemini 3 系列官方建议保持默认 `temperature=1.0`，下调反而可能导致循环或推理退化）；用了 Structured Outputs 就不用校验；Schema 越复杂越好；工具越多 Agent 越强；Function Calling 可以绕过业务权限。
- **原文参数·字段·指标**：`strict`、`response_format`、`schemaVersion`、`additionalProperties: false`、`temperature=1.0`（Gemini 3 建议）。

---

# 四、AI 应用评测（8 题）

相关内容：[《AI 应用评测体系：从 Golden Set 构建到线上灰度闭环》]。原文定位：评测题关注如何证明一次模型、Prompt 或系统改动确实带来了改善；Golden Set、LLM-as-Judge、Trace 回放和线上灰度分别覆盖不同阶段，不能只看公开榜单或少量演示样例。开篇场景：客服 RAG 升级混合检索和 Reranker 后「本地挑几十条问题跑一遍，答案比旧版顺，就觉得可以放量」，一周后业务方只反馈「有些问题感觉还不如以前准」，排查卡住——需要回看同一批场景的历史结果与基线。RAGAS、TruLens、LangSmith、Langfuse 等框架持续演进，生产接入以各自最新官方文档为准，本文只讨论评测方法和指标设计，不做工具横向测评，不引用未经验证的 benchmark 数字。

## 4-1. 为什么不能只靠公开 benchmark 评估 AI 应用质量？

- **一句话核心结论**：公开榜单适合粗筛模型（中文能力弱、上下文窗口不够、工具调用能力达不到业务要求的候选项），不能直接当上线依据，因为业务分布、脏输入和少数高风险失败都不在榜单里。
- **机制/原理**：榜单的任务和数据集固定，排名不能直接代替业务验证；电商客服常见退换货、快递时效、促销规则和商品参数比较，英文推理题高分无法说明模型会按这些业务规则作答。真实请求带来错别字、口语缩写、截图、多语言和前后矛盾等输入，干净测试集覆盖不到。上线前尤其要单独检查少数不能出错的路径：合同审查漏掉高风险条款影响签署判断、客服答错退款流程让用户按错路径提交材料、代码 Agent 执行危险命令影响仓库和运行环境——此类失败即使占比很低也可能被平均分掩盖，通用 benchmark 通常不会凸显。ai-core-concepts 同义表述：公开 Benchmark 可以筛掉明显不合适的模型，不能代替业务验证；真实请求带错别字、口语缩写、截图、多语言和前后矛盾，少数高风险路径也可能被平均分掩盖。
- **工程落地做法**：用自己的 Golden Set 判断一个模型能不能接进业务；每条用例包含输入、预期结果或成功标准、场景标签和评分方式；高风险失败样本单独设门禁，不能被大量正常样本的均值稀释。
- **常见追问与易错点**：不要拿榜单分数当发布门禁；「平均分提高」不等于「关键路径没退步」。
- **原文参数·字段·指标**：Golden Set、高权重失败、平均分掩盖、Faithfulness / 任务完成率等业务指标。

## 4-2. Golden Set 应该怎么构建？冷启动阶段没有生产日志怎么办？

- **一句话核心结论**：Golden Set 是应用自己的标准测试集，关键不是数量而是每条样本有明确输入和判断好坏的标准（参考答案、评分维度、验证规则或人工判断说明）；冷启动用知识库文档作种子 + 人工构造 + 真实失败样本先把流程跑起来，生成样本不能直接当发布门禁。
- **机制/原理（数据三来源 + 冷启动，原文）**：
  - **生产日志分层采样**：系统已上线时最有价值；不要只取高频问题（高频往往已被产品和 Prompt 优化过），低频、边缘和异常输入更容易暴露短板；重点看用户点了「不满意」的、出现补充追问的、最后转人工的，以及「差点失败」的边缘案例。只从正常对话流采样会漏掉图文混排、跨意图追问、用户描述前后矛盾。
  - **人工构造**：新功能尚未产生日志、退款越权、Prompt 注入等风险很少自然出现时由人工写入；第一版至少三类：①正常路径（「7 天内未拆封能否退货」，答案口径明确，先校验主流程）；②信息缺失（只说「东西坏了」，订单/时间/故障细节都缺失，预期行为是先追问）；③对抗（绕过退款规则、要求代码 Agent 执行越权命令，检查对抗处理）。
  - **失败案例回填**：每次处理用户投诉都判断能否转成评测用例；经确认的失败样本回填后 Golden Set 才随薄弱点更新。
  - **冷启动**：可以把知识库文档作为种子，生成问题、参考答案和难例，经人工抽样审核后进入候选集（RAGAS 等工具可承担生成环节）；这类样本只补足初始覆盖面，不能直接用作发布门禁——生成的问题通常较规整，错别字、截图描述、前后矛盾和非常规追问仍需通过日志、失败案例和人工审核补上。第一版可先用 **20 到 50 条真实任务**验证评测流程，该数量只是启动用的工程样本，无法支持统计结论；第一版 eval 可先纳入真实失败样本、手工测试样本和高风险路径（Anthropic 的 Agent eval 实践也采用这一思路），不必等待数据集完全成型。
- **工程落地做法**：无法穷举 Case 时按**蜕变测试（Metamorphic Testing）**思路扩展覆盖，从已确认任务出发改变可能影响结果的条件：输入扰动（错别字、口语缩写、语序变化、多语言表达、缺失信息）、上下文扰动（调整无关材料位置、加入过期或冲突信息、改变历史对话长度）、工具扰动（超时、限流、空结果、字段缺失、部分成功、第三方接口返回格式变化）、状态扰动（权限、订单状态、文件残留、缓存命中、时间条件）；断言写成「输入变化前后应保持什么关系」（加入无关上下文不应改变结论；缺少订单号应先追问；权限被撤销后必须停止写操作；同义问法最终 Outcome 应保持一致）；扩展样本留一部分作**保留集**，不参与 Prompt 调整、示例选择和规则调参。分层比总量更关键（原文保留）：

| 分层 | 典型内容 | 取样原则 |
| --- | --- | --- |
| 正常路径 | 高频、清晰的主流场景 | 按真实流量分布取样，保证主要功能都有覆盖 |
| 边缘场景 | 信息缺失、多义、跨领域 | 对历史失败和容易混淆的输入提高采样权重 |
| 对抗样本 | 模型容易犯错的特殊输入 | 按攻击面和权限风险设计，不依赖自然流量出现 |
| 高权重失败 | 业务定义的关键失败类型 | 单独设置门禁，不能被大量正常样本的均值稀释 |

样本量：「离开具体业务，50、200、500 都只是数字，不能直接当门槛」；「样本分布往往比总量更先决定评测能否发现问题。200 条同类问题不如 100 条覆盖 10 类场景」；发布门禁样本先覆盖主要功能路径和高风险场景，再按分层结果观察基线方差和可接受误差计算样本量；Agent 场景还要看 Trial 数量，区分「至少一次成功」（能力上限）和「连续成功」（更接近生产稳定性）。
- **常见追问与易错点**：Golden Set 不是一次性资产——每季度覆盖度复查、失败样本回流、版本记录（Golden Set、模型版本、Prompt 版本一起保存，否则跨版本对比失真）；高权重失败样本数量可以少但发布门禁里要单独看（合规漏识别风险条款、医疗错误用药建议即使占比不高也可能足以暂停发布）。
- **原文参数·字段·指标**：20~50 条、50/200/500、「200 条同类问题不如 100 条覆盖 10 类场景」、Metamorphic Testing、保留集、pass@k / pass^k、Trial、覆盖度复查（每季度）、`schemaVersion` 式版本记录。

## 4-3. LLM-as-Judge 有哪些主要偏差？怎么缓解？

- **一句话核心结论**：Judge 适合评开放式回答、成本比人工低，但会有位置、冗长、自我强化和有限推理四类偏差，不能当成绝对裁判；硬错误先交规则评测，高风险样本保留人工复核校准口径。
- **机制/原理（两种模式）**：**Reference-based（有参考答案）**——对照标准答案核查事实、边界条件和遗漏项，示例「参考答案：退款申请应在收货后 7 天内提交，超期不受理；模型回答：您需要在收货 7 天内提出退款申请，否则无法受理」，按事实准确性/完整性/措辞清晰度 1-5 分；**Reference-free（无参考答案）**——只依据用户问题、上下文约束和评分标准判断，用于创意写作、分析类或参考答案无法收敛到唯一版本时，事实型业务问答最好补资料、规则或人工判定口径。
- **四类偏差与局限（原文）**：
  - **位置偏差（Position Bias）**：A/B 对比里答案展示顺序影响 Judge，两个答案质量接近时有些模型偏第一个、有些偏后出现那个；处理方式是做两次评判交换 A/B 顺序取一致结论，或让 Judge 一次只评一个答案不做直接对比。
  - **冗长偏差（Verbosity Bias）**：Judge 容易把更长的答案判得更好，即使长度来自废话和重复；可把「反复粘贴政策原文」与「只保留时间、条件和例外」两类答案放进校准集，若 Judge 仍偏向前者说明 Prompt 里「避免冗长」没有实际约束力。
  - **自我强化偏差（Self-Enhancement Bias）**：Judge 与被评判模型同源甚至同模型时可能对同源输出更宽容；MT-Bench 实验中 GPT-4 和 Claude-v1 对自身输出表现出一定胜率偏好，GPT-3.5 则没有相同结果，论文同时指出数据量和差异有限，不能据此认定存在稳定系统性偏差；重要评测节点交叉使用不同厂商或模型族的 Judge 并保留人工抽样复核。
  - **有限推理能力（Limited Reasoning Ability）**：数学、代码、SQL 和复杂逻辑推理的正确性不能只交给 LLM Judge，被评答案中的错误推导可能影响它的判断，即使该模型单独解题能得到正确结果；最好用 **Reference-guided Judge** 给明确参考答案、单元测试结果、SQL 执行结果或关键推理步骤，MT-Bench 也提到 chain-of-thought judge 和 reference-guided judge 能缓解数学和推理题上的评分局限。
- **工程落地做法（Judge Prompt 模板）**：严格的评测员 Prompt 含【用户问题】`{question}`、【参考资料】`{context}`、【参考答案】`{reference_answer}`、【AI 回答】`{answer}`；评分前先提取硬性要求和隐含约束、对照资料检查事实断言有无依据、检查是否覆盖关键要点，再按三个维度各给 1-5 整数分：**事实忠实度（Faithfulness）**（5 分所有事实断言均可在参考资料找到依据 / 3 分大部分有依据少量无法核实推断 / 1 分包含矛盾或无依据断言）、**答案相关性（Answer Relevance）**（5 分直接回答无不相关内容 / 3 分基本回答但部分偏题 / 1 分未回答实际问题）、**完整性（Completeness）**（5 分覆盖全部关键要点 / 3 分覆盖主要但遗漏重要细节 / 1 分严重缺失）；输出 JSON `{"faithfulness": <分值>, "relevance": <分值>, "completeness": <分值>, "reasoning": "<一句话说明评分依据>"}`，不要展开完整推理过程。清晰的维度、分档标准和反例有助于减少凭感觉打分，但是否真的更稳定仍要用人工校准集检查一致率、分维度误差和边界样本。Judge 缺少足够证据时允许输出 `Unknown` 或 `needs_human_review`，尤其财务、法律、医疗、赔付、账号安全场景。G-Eval 把 chain-of-thought 与 form-filling 结合，工程可借鉴「先生成评估步骤、再按结构化表单打分」，对外保存分数和简短依据即可；简单格式校验或本身会内部推理的推理模型，显式步骤可能只增加 token 成本。ARES 的做法：先用合成数据训练轻量级 Judge，再结合一小批域内人工标注，通过 **PPI（Prediction-Powered Inference）**估计 RAG 系统质量的置信区间；它仍需要域内语料、少量示例和人工验证集，不是零标注方案，多数团队先用通用 LLM-as-Judge，只有成本或一致性成为持续瓶颈时再为特定领域训练 Judge。
- **常见追问与易错点**：规则评测、LLM-as-Judge、人工评测是分工不是替代（三种评测方法表见知识点速查）；能写成明确验收条件的问题优先做是/否判断且一次只检查一个条件（「是否先完成身份校验」「引用是否支持这条事实」「是否修改了范围外文件」比含义模糊的「82 分」更容易进门禁用）；每条结果至少能回答「是否通过、错在哪里、判断有多确定」：`pass/fail`、`score`、`reason`、`category`（格式错误、事实错误、工具未调用、过度承诺）、`confidence`（不等于真实正确概率，需拿人工标注集校准）；高风险条件不能被平均分抵消。
- **原文参数·字段·指标**：Position Bias / Verbosity Bias / Self-Enhancement Bias / Limited Reasoning Ability；MT-Bench；Reference-guided Judge、chain-of-thought judge、G-Eval、ARES、PPI；`Unknown` / `needs_human_review`；`pass/fail`/`score`/`reason`/`category`/`confidence`；1-5 整数分；Cohen's kappa（见 4-8）。

## 4-4. RAG 评测为什么必须分检索和生成两段？

- **一句话核心结论**：最终表现都只是「答案不准」，但修复入口取决于问题发生在哪一段——关键资料没被召回，改 Prompt 很难救；资料已进上下文模型却没用上，继续调向量库也解决不了；只看 E2E 分数很难知道该改哪一层。
- **机制/原理**：拆两张账——**检索层**看相关内容有没有进上下文，**生成层**看模型有没有基于这些内容回答。检索指标（原文保留）：

| 指标 | 关注点 | 适合场景 |
| --- | --- | --- |
| Recall@k | 召回覆盖率（`Recall@k = 被召回的相关文档数 / 总相关文档数`，知识库问答常看 Recall@3 或 Recall@5） | 关键信息不能漏的场景，比如合规、法律、医疗 |
| Hit Rate@k | 是否命中（前 k 个结果里有没有至少一条相关文档，每条样本给 0 或 1 再取平均） | 快速评估和阶段验证 |
| MRR | 相关结果排名（第一条相关文档排第几位，排得越靠前越高） | 模型重度依赖 Top-1 结果的场景 |
| Precision@k | 精准率 | 上下文 Token 预算紧张、需要高精准输入的场景 |
| Context Precision | 相关上下文是否排在前面 | 没有完整文档 ID 标注，但有参考答案或生成回答 |
| Context Recall | 参考答案中的信息是否被上下文覆盖 | 标注文档级相关性太贵，但可以提供参考答案 |

前四个传统 IR 指标通常需要标注相关文档 ID（每条问题标出「哪些文档是正确答案来源」），这是 Golden Set 里最花时间的部分；文档级标注成本太高时先用 RAGAS 这类基于 LLM 的检索指标起步——Context Precision 关注相关上下文是否排在更靠前，Context Recall 关注参考答案中的声明有多少能被检索上下文支持，二者不要求精确标注所有文档 ID 但依赖 LLM 判断，无参考答案的 Context Precision 还可能把生成回答自身的遗漏带进评分，仍要做人工抽样校验。RAGAS 文档里也有 `Context Utilization`，它在没有参考答案时把每个检索 chunk 与生成回答比较再按 Context Precision 方式计算排序分数，因此**不是**「回答使用了多少上下文信息」的直接度量；要评后者建议换自定义名称 **Context Usage**，避免两个口径混用。生成指标：**Faithfulness（事实忠实度）**（检查回答里有没有超出检索结果范围的捏造，RAGAS 判断答案中每个陈述能否从上下文推导出来）、**回答有没有接住问题**（用户问「怎么退款」，模型只贴退货政策原文，即使原文完全来自检索结果，没整理申请入口/时限/材料/下一步动作，相关性就不够）、**上下文材料有没有被用上（Context Usage 自定义指标）**（退款政策已在 Top-3 回答仍只给「请联系客服」，问题可能在上下文排序、Prompt 注入方式，或模型忽略中间内容 → Lost-in-the-Middle）、**噪声上下文会不会带偏回答**（RAGAS **Noise Sensitivity** 检查回答中的错误声明并判断是否可归因于相关或无关检索上下文，分数在 **0 到 1 之间，越低越好**；偏高先检查分块、Reranker 和上下文排序，资料已排前面再考虑 Prompt 是否缺少「只使用相关资料」的约束）。
- **工程落地做法**：用户问「怎么退款」却答错时，先看退货政策有没有被召回；没召回查分块、向量库、混合检索权重和 Reranker；政策已进上下文回答仍没给申请入口、时限和材料，再去看 Prompt、模型和上下文注入方式。客服 RAG 第一版评测可以只跟踪 Recall@k、Faithfulness、Answer Relevance、延迟和转人工/满意反馈。
- **常见追问与易错点（两个陷阱，原文）**：**陷阱一 用检索结果直接当标准答案**——把检索到的文档当标准答案再评生成回答相似度，会混淆检索质量和生成质量，检索结果只是候选不等于正确答案，算出来的分数更像「模型有没有复述检索结果」；**陷阱二 只评最终答案不分段**——检索差和生成差最终表现都可能是「回答不准」，但优化方向完全不同，分段评测是定位问题的基本前提。
- **原文参数·字段·指标**：Recall@k（Recall@3 / Recall@5）、Hit Rate@k、MRR、Precision@k、Context Precision、Context Recall、Context Utilization（RAGAS）、Context Usage（自定义）、Faithfulness、Answer Relevance / Response Relevancy、Completeness、Noise Sensitivity（0~1，越低越好）、Top-3、Top-k、Reranker、Hybrid Search。

## 4-5. Agent 评测为什么比普通问答和 RAG 更复杂？

- **一句话核心结论**：Agent 会在多轮里调用工具、修改状态、读取反馈、继续决策，前一步的小错可能在后面被放大；终点成功不代表过程可靠，要把 Outcome 和 Transcript 分开看。
- **机制/原理**：评 Agent 前先确认完成哪类任务（原文保留）：

| Agent 类型 | 主要结果 | 优先检查的内容 |
| --- | --- | --- |
| 对话 / 信息型 | 给出答案、解释、检索结果或建议 | 事实正确、证据是否支持、时效性、拒答、表达和用户反馈 |
| 任务执行型 | 发信、退款、改代码、写数据库等外部状态变化 | Outcome、权限、工具与参数、关键步骤、错误恢复和副作用 |
| 对话与执行混合型 | 先通过多轮对话补齐信息，再调用工具完成任务 | 信息收集是否充分、执行前确认、最终状态、结果说明和可追溯性 |

检查层（原文，工程拆法非行业统一分类）：

| 检查层 | 要验证的对象 | 常用证据或指标 |
| --- | --- | --- |
| 最终状态 | 任务结束后，答案或外部状态是否正确 | 任务完成率、事实断言、数据库状态、测试结果 |
| 决策与执行 | 工具、参数和不可省略的业务动作是否合理 | 工具选择、参数准确率、关键步骤断言、不必要调用率 |
| 运行稳定性 | 换一种表达、遇到故障或重复运行时能否稳住 | 错误恢复率、多次 Trial、延迟、Token、环境与 Harness 错误率 |
| 交互与边界 | 是否守住权限和风险边界，并把结果讲清楚 | 越权操作、危险动作确认、拒答、说明清晰度、转人工 |

**Outcome** 是最后状态（订单有没有退款成功、代码测试有没有通过、文件有没有按要求改好），**Transcript** 是完整过程（调用了哪些工具、传了什么参数、工具返回什么、总共跑几轮）。测试通过的 Coding Agent 也可能改了无关文件；回复「已经退款」的客服 Agent 可能跳过身份校验；数据分析 Agent 即使产出图表也可能把金额字段读成件数——这些藏在过程里。参考轨迹只标出不可省略的动作，不把每一步调用顺序写死，结果有效、权限合规且状态未被误改的运行可以采用不同路径。核心指标：**任务完成率**（`任务完成率 = 通过所有完成标准的任务数 / 总任务数`；「帮我发一封会议邀请邮件给团队」的完成标准：收件人包含团队成员列表所有人、主题含「会议」关键词、正文含会议时间和地点、工具调用返回成功状态）；**工具调用指标**（工具选择精确率 = 必要且正确的工具调用/总调用数；工具选择召回率 = 已覆盖的必要工具/标注的必要工具数；工具集合完全匹配率；参数准确率；不必要调用率 = 多余调用/总调用次数，「正确工具调用数/总调用数」只反映精确率，无法发现本应调用却完全没调用的漏召回）；**轨迹准确率**（检查实际执行的工具和参数与专家标注关键路径差多少，退款 Agent 可要求「校验身份 -> 查订单 -> 判断政策 -> 调退款工具」，但不必规定每步自然语言措辞，标太细会把有效路径误判成失败；代码执行、财务操作、账号权限、隐私数据、需审计的业务动作可严格检查关键路径；研究、写作、代码理解等开放任务把轨迹评测当诊断工具）；**错误恢复率**（`错误恢复率 = 工具失败后进入预定义恢复结果的次数 / 工具失败总次数`；预定义恢复结果可以是补齐参数后完成、换方式重试成功、高风险操作前安全停止并转人工，不同结果分开计数，不能把「任务完成」和「安全退出」混成同一种成功；工具一报错就原地结束的样本单独进回归集）；**多次运行一致性**（至少一次成功率 pass@k 反映能力上限，连续成功率 pass^k 更接近客服/支付/退款/合规需要的稳定性；各次近似独立、单次成功率稳定在 90% 时，连续 5 次都成功的概率约为 **59%**，真实运行还受任务难度、环境和模型版本影响，应直接重复 Trial 估计 pass@k 与 pass^k 并报告样本量）；平均轮次/工具次数用于成本、效率和过度探索诊断。
- **工程落地做法**：退款、转账、删库和发邮件会改变外部状态，评分时核对关键步骤；查询和整理类任务先看 Outcome 是否满足要求，失败后再从 Transcript 找原因。每个 Trial 最好从干净状态启动（环境隔离），避免上次残留文件、缓存、数据库记录影响下一次评测（Coding Agent 尤其明显）。Skill 单独评四类用例（原文保留）：

| 用例类型 | 主要检查什么 | 例子 |
| --- | --- | --- |
| 触发用例 | 该触发时有没有触发，不该触发时有没有误触发 | 用户只是闲聊时，不应该启动退款 Skill |
| 核心逻辑用例 | 主要分支和高风险分支有没有走对 | 已发货退款必须先查订单状态 |
| 产物质量用例 | 输出是否满足业务格式和质量要求 | PR 总结是否覆盖改动点、风险和测试 |
| 异常容错用例 | 输入缺失、工具失败、边界条件下能否稳住 | 订单查询失败时，是否停止退款并说明原因 |

`grilling` 这类需求澄清 Skill 要检查有没有追问关键分支、有没有过早进入实现、有没有把模糊需求收敛成可执行计划。
- **常见追问与易错点**：不要先拿一组抽象维度往所有 Agent 上套，要从「什么东西能被观察和验证」出发；「测试通过」不等于过程没问题；同一任务跑一次成功不代表稳定可用。
- **原文参数·字段·指标**：Task / Trial / Grader / Transcript·Trace / Outcome / Eval Harness（评测用例对象表见知识点速查）；任务完成率、工具选择精确率/召回率/集合完全匹配率、参数准确率、不必要调用率、轨迹准确率、错误恢复率、pass@k / pass^k、90% 单次 × 连续 5 次 ≈ 59%、平均轮次/工具次数、触发召回率/误触发率/产物合格率/异常稳态率。

## 4-6. 离线评测、Trace 回放、线上灰度分别解决什么问题？

- **一句话核心结论**：三者覆盖开发、发布前、上线后三个阶段，不能互相替换——离线评测在固定 Golden Set 上发现与阻断回归，Trace 回放用真实生产轨迹补离线盲区，线上灰度用小流量观察用户反馈和数据分布。
- **机制/原理**：流程 `开发/实验（改 Prompt / 换模型 / 调检索策略）→ 离线评测（跑 Golden Set）→ 核心指标通过阈值？→ Trace 回放（生产轨迹回放）→ 回放指标通过？→ 线上灰度 1% → 10% → 100% → 持续监控（采样回评 + 告警）`，任一门禁不通过即「阻断发布/通知排查」。
  - **离线评测**：上线前固定同一版 Golden Set，把新结果和上一个稳定版本放在同一张表里；Prompt、模型、检索策略的改动和这次评测记录绑定；提前定义「Faithfulness 从 0.82 降到 0.79 算不算回归」以及结果和哪次变更绑定。
  - **Trace 回放**：Golden Set 覆盖不了所有生产场景，从生产系统采样真实请求，带原始输入和完整上下文，用新版本模型或 Prompt 重跑，对比输出差异；要求系统记录足够完整上下文（检索到的文档、工具调用结果、当时的 Prompt 版本），否则「回放」只是用新 Prompt 处理旧问题，无法复现当时执行环境；涉及 Web Search 或实时 API 时只保存 URL 和请求参数不够，网页正文、接口响应、抓取时间和**内容哈希**也要保存。
  - **线上灰度**：新版本先接少量真实流量，比较灰度组和对照组指标；结构化输出任务用规则自动评测，开放式回答对灰度流量做 LLM-as-Judge 采样评测（每天跑一批），用户真实反馈（满意率、追问率、转人工率）作辅助；灰度门槛要在实验前写进发布规则，但「不存在通用的『下降 3% 就暂停』」——先根据历史方差、可接受损失和业务风险确定**非劣效界值**，再估算所需样本量，分析时同时看**效应量与置信区间**，样本不足应延长实验或保持当前流量，不能靠收紧一个固定百分比弥补统计不确定性。
- **工程落地做法**：持续监控——灰度通过后评测也不能停（生产数据分布会变、用户行为会变、知识库内容会更新、模型供应商也可能静默升级底层版本）；回评采样率取决于日流量、Judge 成本、场景风险和希望检测的最小回归幅度，低频高风险场景可全量评规则指标并对语义质量分层抽样，高流量低风险按预算采样；告警条件基于历史基线、置信区间或控制图设置，避免把「连续 3 天」写成所有业务都适用的规则；固定快照回归和实时能力探针同时保留，只有实时探针下降先检查外部数据/工具协议/来源变化，两条轨道一起下降再优先排查模型、Prompt、检索或 Agent 编排的共同改动。
- **常见追问与易错点**：三类证据出现阶段不同；Trace 回放依赖完整上下文记录；「下降 3% 暂停」「连续 3 天告警」不是通用规则；固定快照分数和实时探针分数不应混成一个总分。
- **原文参数·字段·指标**：Golden Set、1% → 10% → 100%、Faithfulness 0.82 → 0.79、内容哈希、非劣效界值、效应量、置信区间、控制图、满意率/追问率/转人工率、固定快照回归 / 实时能力探针。

## 4-7. CI 里的 AI 评测如何平衡速度和覆盖度？

- **一句话核心结论**：CI 里区分「能力集」和「回归集」，PR 只跑能在团队等待预算内完成的核心回归集，完整 Golden Set 放主分支或定时任务，Trace 回放放在重大发布前；样本量由等待预算、调用配额和希望发现的最小回归幅度反推。
- **机制/原理**：把离线评测接入 CI，才能从「记得测」变成「必须测」。**能力集**保留目前还做不稳的任务，用来追踪模型、Prompt 或工具设计是否真正改善，初始通过率不必很高；**回归集**要求此前已通过的任务继续稳定通过；能力集中长期稳定又有业务价值的样本迁入回归集按发布门禁处理。阈值两类：**绝对阈值**（质量底线直接写发布规则，例如 Faithfulness 低于 0.75 不通过）、**相对阈值**（相比上一个稳定版本指标下降不能超过一定比例，例如任务完成率相比 baseline 下降不得超过 5%，适合质量快速演进的早期阶段）；两者组合——绝对阈值守底线，相对阈值防退步。
- **工程落地做法**：「CI 里跑 500 条 LLM-as-Judge 评测，可能要 10 到 30 分钟。太慢的话，开发者就会想办法绕过 CI」；PR 阶段只运行能在团队等待预算内完成的核心回归集，评分器优先选规则检查和经过校准的自动评分器；完整 Golden Set 放主分支或定时任务；生产 Trace 回放按数据量和风险安排；各层样本数量与耗时结合调用延迟、配额和统计功效反推，不能直接照搬 50、200 或 1000 条这类固定数字；发布时同时检查绝对底线、相对 baseline 和置信区间，避免只凭一个阈值阻断或放行。Agent 评测的运行环境也要被版本化，Trial 之间复用工作区/缓存/临时数据库时，残留文件、接口超时、并发资源不足、评分脚本变更都可能把分数带偏，报告里要把 **harness error** 和模型失败分开记录。评测记录结构（Java，原文保留要点）：`EvalRecord` 含 `evalId`、`taskId`、`trialId`、`promptVersion`、`modelId`（例如 `gpt-4o-2024-08-06`）、`datasetVersion`、`taskAsOf`、`timezone`、`environmentVersion`、`evidenceSnapshotUri`、`inputHash`、`rawInput`、`referenceOutput`、`actualOutput`、`transcriptUri`、`outcomeStatus`（SUCCESS / FAILED / PARTIAL）、`scores`、`judgeModel`、`graderVersion`、`judgeReasoning`、`errorCategory`、`rootCauseLayer`（DATA / MODEL / AGENT / TOOL / ENV / GRADER）、`confidence`、`evaluatedAt`、`gitCommit`；`EvalRunSummary` 含 `runId`、`promptVersion`、`modelId`、`datasetVersion`、`totalCases`、`avgScores`、`passRates`、`baselineScores`、`passedRegression`、`regressionDetails`、`startedAt`、`completedAt`。三类查询：查版本（同一 `inputHash` 对比不同 `promptVersion`）、查趋势（按 `evaluatedAt` 画趋势图）、查回归（某个 `gitCommit` 之后哪些指标下降）。
- **常见追问与易错点**：不要把一个固定样本数当门槛；不要把 harness error 算成模型失败；能力集初始通过率不必高，别用它当门禁。
- **原文参数·字段·指标**：能力集/回归集、绝对阈值 Faithfulness < 0.75、相对阈值下降不得超过 5%、500 条 LLM-as-Judge 可能 10 到 30 分钟、50/200/1000 固定数字不可照搬、`EvalRecord` / `EvalRunSummary` 全字段、`gitCommit`、`inputHash`、`rootCauseLayer`。

## 4-8. 如果 LLM-as-Judge 和人工评测结果不一致，应该怎么处理？

- **一句话核心结论**：把人工与 Judge 结论不同的样本单独收集作为校准集，先判断是评分维度不够细还是标注规范问题，再用一致性指标（Cohen's kappa / 加权 kappa / 精确率 / 召回率）判断 Judge 是否可用，而不是只看一个「80% 一致率」。
- **机制/原理**：原文示例：人工因「事实正确但流程缺一步」只给 3 分，Judge 却因语气完整给出高分，说明评分维度还不够细。二分类任务可查看 **Cohen's kappa**、精确率和召回率；有序评分可使用**加权 kappa**；判断 Judge 是否可用时，不能只看一个未考虑类别基线的「80% 一致率」。这类边界样本应进入校准集。Badcase 现象→候选层表里「Judge 与人工长期分歧」对应优先检查 Rubric、Judge Prompt、Judge 模型或标注规范，需要的证据是人工校准集、分维度混淆矩阵、低置信样本。
- **工程落地做法**：低置信样本（`confidence`）进入人工复核；Judge 缺证据时允许 `Unknown` / `needs_human_review`；用人工校准集检查一致率、分维度误差和边界样本，不能只看 Prompt 写得够不够长；重要评测节点交叉使用不同厂商或模型族的 Judge 并保留人工抽样复核。评测记录里保留 `judgeModel`、`graderVersion`、`judgeReasoning`、`judgeReasoning` 便于复核；每份报告绑定数据集、Prompt、模型、检索配置、评分器、代码版本、目标时间和环境快照。
- **常见追问与易错点**：「一致率 80% 就可用」错误（未考虑类别基线）；不要急着改被测模型，先排查评分口径；人工与 Judge 分歧也是发现 Rubric 缺陷的信号。
- **原文参数·字段·指标**：Cohen's kappa、加权 kappa、精确率/召回率、混淆矩阵、`confidence`、`Unknown` / `needs_human_review`、`judgeModel` / `graderVersion` / `judgeReasoning`、`pass/fail`/`score`/`reason`/`category`/`confidence`。

---

# 五、综合场景题（5 题）

## 5-1. 客服机器人历史会话持续增长时，如何分配 Token 预算并保留关键业务状态？

- **一句话核心结论**：先按 `window ≥ input_tokens + max_output_tokens` 划桶，给 System Prompt（含 Schema）、当前输入、历史消息、安全边际和输出预留分配额度；增长的历史靠「裁剪 + 摘要 + 状态外置」而不是无限塞窗口，关键业务状态用结构化字段单独保留。
- **机制/原理**：16K 窗口典型分配（示意）：System Prompt（含 Schema）1500、User Prompt 6000、历史消息 2000、安全边际 1500、输出预留 5000；历史消息与 RAG 检索片段、工具 Schema、格式开销共同占用窗口，输出 Token 也占窗口。窗口变长还有 O(N²) 计算、TTFT 增加、Lost in the Middle（中间内容召回弱）和账单增长的代价。
- **工程落地做法**：①固定 System Prompt 与工具定义放最前、变化内容放后，利用 Prompt Caching（多轮对话「System Prompt + 历史 Message 不变」是受益场景），按响应字段监控缓存读取/写入 Token；②历史超出预算时按顺序减少 RAG Top-K → 合并重复片段 → 摘要或截断长字段 → 一轮塞不下拆成分批评估或两阶段生成；③关键业务状态（订单号、退款状态、身份校验结果、用户偏好）不要依赖模型「记住」长对话，用结构化状态字段/外部存储显式回写，每轮只注入必要状态；④给输入留 10%~20% 安全余量，用 `max_output_tokens` 控制输出，处理 `finish_reason=length` 截断；⑤保留关键约束在开头或结尾以缓解 Lost in the Middle。
- **常见追问与易错点**：「换个更大窗口模型」不解决状态丢失与成本问题；摘要会损失细节，高风险状态必须外置；推理 Token 也消耗生成预算。
- **原文参数·字段·指标**：`window ≥ input_tokens + max_output_tokens`、1500/6000/2000/1500/5000、10%~20% 余量、RAG Top-K、Prompt Caching、`finish_reason=length`、Lost in the Middle、TTFT、`usage`。

## 5-2. 流式响应中途断开后，服务端如何处理重试、续传和重复计费问题？

- **一句话核心结论**：断流不能当成成功，也不能盲目自动重试；先记录 `INTERRUPTED` 状态，按幂等 Key 决定是否能重试/续传，用 `messageId` + `sequence` 补发已缓存片段，供应商流失效就提示重新生成，并用 usage 与 attempt 记录对齐账单。
- **机制/原理**：流式异常四类：用户取消（后端要同时取消供应商请求、响应流解析、后续 TTS/工具调用/落库、未提交增量缓存，不能只在前端停展示）、超时（连接超时/TTFT 超时/总时长超时三层分开记录）、断流（记录 `finish_reason` 或最后事件状态，无正常结束标记标记 `INTERRUPTED`，前端展示「已中断，可重新生成」）、重连（SSE `EventSource` 自动重连，但多数情况下供应商侧流已断，无法真正从 Token 级别续上）。
- **工程落地做法**：①为每个流式响应生成 `messageId` 和递增 `sequence`，已发送片段写入短期缓存（`StreamBuffer` + `idempotencyStore.appendDelta`），前端重连先补发已缓存片段；②`onDelta` 用 `buffer.seen(sequence)` 去重，`onComplete` 才拼 `fullText` 做 `parseAndValidate` 再 `markSuccess`，`onError` 走 `markInterrupted`；③落库时只允许一个 attempt 成为 `final`，其他保留为诊断记录不进入下一轮 Prompt（`message_id` / `attempt_id` / `provider_request_id` / `stream_sequence` 四层 ID）；④用户可见任务不自动重试，后台任务才幂等重试；重试遵循指数退避 + 抖动 + 最大 2-3 次 + 总截止时间（如 15 秒 SLA）；⑤重复计费靠「只让一个 attempt 计费/落库 + 读 API 返回 `usage` 对齐账单」，取消信号要传播到供应商请求，避免前端停了后端仍在消耗 Token；⑥结构化输出断流时不把半截 JSON 交给下游，等正常结束事件后拼完整再 Schema 校验。
- **常见追问与易错点**：「重连 = 无缝续写」是错的；「断流半截内容当成功」会污染落库与下一轮上下文；失败请求也可能已消耗部分 Token 并计入每分钟限制。
- **原文参数·字段·指标**：`INTERRUPTED`、`messageId` + `sequence`、`StreamBuffer`、`message_id`/`attempt_id`/`provider_request_id`/`stream_sequence`、`final`、`markInterrupted`、Redis `SET NX`、`Retry-After`、2-3 次、15 秒 SLA、`usage`、`finish_reason`。

## 5-3. 上游模型触发 RPM 或 TPM 限制时，模型网关如何排队、降级或切换模型？

- **一句话核心结论**：网关先按 RPM/TPM/并发/上下文/预算自己扣桶，收到 429 后按「读 header → 标维度 → 排队或切换 → 熔断」处理，降级要显式告知业务层。
- **机制/原理**：429 只是外部保护信号，不能代替应用侧预算、排队和并发控制；限流四层（用户/租户/模型/供应商）；请求进入网关先估算 `input_tokens + reserved_output_tokens` 在几个桶里扣减，扣不到就排队、降级或拒绝；同时看 RPM、TPM、并发数、上下文大小、最大输出 `max_tokens`、日/月预算。
- **工程落地做法**：①读 `Retry-After` 或供应商 rate limit header（有明确恢复时间就尊重）；②标记限流维度（请求数打满 / Token 打满 / 日配额耗尽）；③短请求可排队（后台摘要进延迟队列）；④用户交互请求少重试，提示稍后再试或切换轻量模型；⑤供应商连续 429 时熔断，不要让所有请求继续撞墙。典型降级链路：`优先模型可用 -> 正常调用` → `优先模型 429 -> 切备用同级模型` → `备用模型也限流 -> 切轻量模型并缩短输出` → `仍不可用 -> 排队或返回"当前请求繁忙"`。策略组合：供应商级全局令牌桶 + 熔断器，模型级令牌桶 + 并发信号量，流式请求并发信号量 + 总时长限制。降级不是偷偷变差，若轻量模型影响答案质量要在业务层明确标记（「当前为快速模式，复杂问题建议稍后重试」）。
- **常见追问与易错点**：「收到 429 才开始限流」说明缺少容量管理；不要所有请求一起重试把系统再打进限流（抖动的意义）；具体数值与模型关系变化快，从控制台/响应头/配置中心动态管理，别写死。
- **原文参数·字段·指标**：RPM / TPM / RPD / 并发数 / `max_tokens` / 日月预算、`Retry-After`、`input_tokens + reserved_output_tokens`、请求 A 500/100 vs 请求 B 80K/8K、四层桶、令牌桶/漏桶/滑动窗口/固定窗口/并发信号量/优先级队列/熔断器。

## 5-4. 模型生成退款工具的调用参数后，业务系统还需要执行哪些校验？

- **一句话核心结论**：模型参数是「不可信输入」，Schema 只管类型结构；必须做结构校验 → 业务校验 → 权限校验三层，高风险退款还要二次确认、幂等、审计和超时短路。
- **机制/原理**：Schema 只能知道 `orderId` 是字符串，不知道订单是否属于当前用户、是否已退款、用户是否有客服权限。退款属于**高风险工具**（权限校验、二次确认、审计），删除数据/执行 SQL/批量操作属极高风险（默认禁止，走人工审批或专用后台）。
- **工程落地做法**：①结构校验：`query_order` 式参数 Schema（`$schema` draft 2020-12、`schemaVersion` `query_order_v1` `const`、`orderId` `pattern "^O[0-9]{12,20}$"`、`includeLogistics` boolean、`required`、`additionalProperties: false`），用 Jackson + JSON Schema Validator 校验，未知工具直接拒绝 `UNSUPPORTED_TOOL`，错误码 `INVALID_ARGUMENTS`/`FORBIDDEN`/`ORDER_NOT_FOUND`/`TOOL_EXECUTION_FAILED`；②业务校验：订单归属、状态流转（是否已退款）、库存、金额范围；③权限校验：用户身份、角色、租户、数据范围（`permissionService.canReadOrder`）；④二次确认：拆 `prepare_refund`（生成退款预案：金额、原因、影响）与 `confirm_refund`（用户或客服确认后执行）；⑤幂等：`idempotencyKey` 由可信执行层根据业务请求 ID、动作和资源生成（不接收模型提供的键），数据库唯一约束兜底，外部支付/退款接口携带相同幂等号，同一请求再次到达返回已有结果；⑥审计：字段白名单（工具名、校验结论、结果码、耗时、模型版本、Schema 版本、traceId 可直接记；订单号/userId 做掩码/哈希/令牌化；密码、令牌、支付数据、私钥、原始文档正文禁止入普通日志），防日志注入，限制按 `traceId` 反查；⑦超时短路：工具超时后返回明确错误码，模型只能解释「当前无法完成」不能猜测结果；⑧失败兜底：不要让模型编造退款结果。
- **常见追问与易错点**：「Function Calling 可以绕过业务权限」错误，权限必须在服务端不能藏在 Prompt 里；「一个工具不能安全重试，就不应该被 Agent 随意调用」；参数回填模型时 `tool_use_id` / `functionCall.id` 必须原样带回（并行调用否则错配）。
- **原文参数·字段·指标**：三层校验、`prepare_refund`/`confirm_refund`、`idempotencyKey`、Redis `SET NX`、`query_order_v1`、`^O[0-9]{12,20}$`、`INVALID_ARGUMENTS`/`FORBIDDEN`/`ORDER_NOT_FOUND`/`UNSUPPORTED_TOOL`/`TOOL_EXECUTION_FAILED`、`tool_use_id`/`functionCall.id`、字段白名单、OWASP Logging Cheat Sheet。

## 5-5. 更换模型或修改 Prompt 后，如何用离线评测、Trace 回放和线上灰度验证效果？

- **一句话核心结论**：三段证据按顺序串起来——离线评测在固定 Golden Set 上比对新旧版本并绑定变更记录，Trace 回放在真实生产轨迹上补盲区，线上灰度用 1% → 10% → 100% 小流量验证用户反馈与数据分布，任一门禁不通过即阻断发布。
- **机制/原理**：完整流程 `开发/实验 → 离线评测（跑 Golden Set）→ 核心指标通过阈值？→ Trace 回放 → 回放指标通过？→ 线上灰度 1% → 10% → 100% → 持续监控`，不通过即「阻断发布/通知排查」。离线评测：固定同一版 Golden Set，新结果和上一个稳定版本放同一张表，Prompt/模型/检索策略改动与评测记录绑定，提前定义「Faithfulness 从 0.82 降到 0.79 算不算回归」；报告每份都绑定数据集、Prompt、模型、检索配置、评分器、代码版本、目标时间和环境快照。
- **工程落地做法**：①离线：CI 中 PR 只跑核心回归集（规则评测 + 校准过的自动评分器），完整 Golden Set 放主分支/定时任务，同时检查绝对阈值（如 Faithfulness < 0.75 不通过）、相对阈值（任务完成率相比 baseline 下降不得超过 5%）和置信区间；②Trace 回放：采样真实请求带原始输入和完整上下文（检索文档、工具调用结果、当时 Prompt 版本），用新模型/Prompt 重跑对比差异；涉及 Web Search/实时 API 要保存网页正文、接口响应、抓取时间和内容哈希；③线上灰度：结构化输出用规则自动评测，开放式回答对灰度流量做 LLM-as-Judge 采样评测（每天一批），满意率/追问率/转人工率作辅助；先按历史方差、可接受损失和业务风险确定非劣效界值再估算样本量，分析看效应量与置信区间；④持续监控与回流：Badcase 统一补齐证据/现象/定位/根因/回流字段，修复后把原始 Case、根因层、修复动作和验证运行 ID 回填到回归集（「一次线上失败处理完之后，它应该变成后续版本的自动回归用例，而不是只存在某个群聊截图里」）；⑤定位时一次只替换一个变量（保留相同证据换模型、保留相同模型换检索结果、绕过 Agent 直接调工具、固定被测输出只替换 Grader）。
- **常见追问与易错点**：三类证据出现阶段不同不能互相替换；Trace 回放依赖完整上下文记录，否则只是「用新 Prompt 处理旧问题」；「下降 3% 暂停」「连续 3 天告警」不是通用规则；固定快照分数和实时探针分数不能混成一个总分；Badcase 现象→候选层表（8 行，见知识点速查）要先复现原始快照再归因。
- **原文参数·字段·指标**：1% → 10% → 100%、Faithfulness 0.82 → 0.79、Faithfulness < 0.75、下降不得超过 5%、非劣效界值、效应量与置信区间、内容哈希、`inputHash`、`promptVersion`/`modelId`/`datasetVersion`/`gitCommit`、固定快照回归 / 实时能力探针、Badcase 五类字段。

---

# 六、原文关键知识点速查（数字 · 字段 · 表格 · 专有术语）

> 本节把前面各题引用到的原文具体数字、字段名、表格内容和专有术语集中固化，便于成稿时核对；与前文重复处以前文为准，此处为索引。

## 6.1 Token 与中英文差异

- 自回归生成（Autoregressive Generation）：预测一个 Token → 加入上下文 → 预测下一个，直到结束标记或输出限制。
- 切分示意：`你好，我是小 G。` → `[你好]` `[，]` `[我是]` `[小 G]` `[。]`；原文 9 字符 → 5 Token → 压缩比约 1.8 倍；实际结果取决于目标模型 Tokenizer（OpenAI 提供 platform.openai.com/tokenizer）。
- 子词切分算法：BPE、Unigram；固定按字切词表小序列长，固定按词切序列短但中文词组让词表膨胀；高频片段尽量整体保留，低频词继续拆小。
- 经验值：英文 1 Token ≈ 3~4 字符；中文 1~2 汉字；DeepSeek 官方 1 英文字符 ≈ 0.3 Token、1 中文字符 ≈ 0.6 Token（每 Token ≈ 3.3 英文字符或 1.7 中文字符）；GPT-3.5 中文约 1 字 1.5~2 Token；GPT-4o `o200k_base` 词表约 20 万；Qwen2.5 词表约 15 万；实测新闻类约 1.5 字/Token、技术文档约 1.2 字/Token，「这些数字不适合直接用于结算」。
- 特殊 Token 表：BOS `<s>` / EOS `</s>` / PAD `<pad>` / 工具调用标记 `<tool_call/>`（详见 1-1）。
- 多模态 Token：OpenAI 512 像素分块规则 + `detail` 模式（低细节固定基础额度，高细节按缩放后分块数增加）；Anthropic `tokens ≈ width × height / 750`，未缩放 1024×1024 ≈ **1398 Tokens**（并非固定的 5 或 85 Tokens）；Gemini 官方文档 258 Tokens 有尺寸条件，不能直接套到任意 1024×1024 图片。图片 Token 与文本 Token 一起计入单次预算；批量图片拉长 TTFT 需单独压测；只需 OCR 时先提文字再送纯文本。
- 计费与监控：分别记录输入、缓存输入、输出以及供应商返回的 reasoning tokens；输出单价经常高于输入单价，但「不存在稳定的 2~4 倍行业比例」；价格表更新频繁，成本核算读当前价格页，网关保存 `model_version`、各类 `usage` 和实际账单单价；计费与监控以 `usage` 为准。

## 6.2 上下文窗口与 Lost in the Middle

- 标称 128K / 200K / 1M 是「一次调用容纳的 Token 上限」；大多数模型输入与输出合并计算，Google Gemini 分别设限；上下文窗口 ≠ 最大生成长度，参数名 `max_tokens` / `max_completion_tokens` / `max_output_tokens`。
- 窗口占用：固定内容（System Prompt、工具调用 Schema、格式标记）、本次输入（User Prompt、历史消息、RAG 检索片段）、生成预算；ai-core-concepts 补充隐形成本含格式开销（特殊字符/换行/Markdown）与输出 Token。
- 自注意力 O(N²)：输入 Token 翻倍，处理能力需求可能变 4 倍；TTFT 增加；安全风险增加。优化技术 FlashAttention、GQA/MQA、Sliding Window Attention、Ring Attention，O(N²) 仍是标准自注意力理论复杂度。
- Lost in the Middle（「中间丢失」）：更容易利用开头和结尾、对中间召回弱，1M 窗口也不能自动消除；溢出表现为「必须输出 JSON」约束被漏、后半段偏题、RAG 片段太多抓不住证据。
- 推理模型：`reasoning_content` + `content`（DeepSeek 思考模式，无工具调用时上一轮 `reasoning_content` 无需参与下一轮、传入也会被忽略；发生工具调用时当前轮 `reasoning_content` 必须随工具结果回传）；OpenAI 推理模型不暴露原始 chain-of-thought，Responses API 用 `previous_response_id` 或回传 reasoning item，只能拿可选推理摘要；推理 Token 仍消耗生成预算并可能计入输出 Token 和上下文限制。
- Token 预算公式 `window ≥ input_tokens + max_output_tokens`；16K 饼图 1500/6000/2000/1500/5000；结构化任务先定 `max_output_tokens`，给输入留 10%~20% 安全余量；削减顺序：RAG Top-K → 合并重复片段 → 摘要/截断长字段 → 分批评估/两阶段生成。
- Prompt Caching：OpenAI Prompt Caching、Anthropic Prompt Caching、DeepSeek Context Caching（触发门槛/缓存寿命/价格不同，有些区分自动缓存、显式缓存、延长缓存）；不变内容放前、变化内容放后；按响应字段监控缓存读取/写入 Token；受益场景多轮对话、RAG 应用、批量评估；不要把缓存时长和折扣写死在业务代码里。

## 6.3 Temperature / Top-P / Top-K 与「Temperature=0 仍不确定」

- logits → softmax → 采样；`p(t) = softmax(z_t / T)`；示例 logits 5.0/3.2/2.1/0.5/-8.0 → 概率 81.21%/13.42%/4.47%/0.90%/约 0.00%。
- T=0.2 → 「好」约 99.99%；T=1.0 → 81.21% / 13.42%；T=1.5 → 66.85% / 20.14% / 9.67%。
- `Top-k = 3` 保留好/不错/棒；`Top-p = 0.9` 累加「好+不错」= 94.63% 只保留两个，第一名自身超 90% 只留一个；Top-k 固定数量，Top-p 累计概率，候选数量随分布变化。
- 组合表与工程建议温度表、采样参数配置建议总表见 1-4（逐表保留）。
- Penalty 表（原文保留）：

| 参数 | 作用 | 通俗理解 |
| --- | --- | --- |
| Repetition Penalty | 降低所有已出现 Token 的概率 | 「说过的词，再说就扣分」 |
| Presence Penalty | 只要 Token 出现过就扣分（不看次数） | 「鼓励聊新话题」 |
| Frequency Penalty | Token 出现次数越多扣分越重 | 「同一个词说了三遍？重罚」 |

JSON 反复出现 `"name"`、`"score"` 字段名，Repetition Penalty 过高会连必要重复一起降分导致缺字段；RAG 问答用 Presence Penalty 会更倾向引入检索内容里没有的新词，削弱对证据的忠实度；不同供应商定义不完全一致，无明确依据保留默认值。
- 停止条件：`finish_reason=length` 标记为截断不能交下游；Stop Sequences 如 `"\n\n"`、` ``` `，与业务文本重合会截断关键字段；推理模型要确认生成上限是否同时覆盖推理过程与最终回答（部分 API 共用预算，另一些用 `reasoning_effort` 间接控制）。
- `seed` 只提供尽力而为可复现性，不保证逐字一致；DeepSeek 当前 API 未公开 `seed`；不一致原因：模型版本更新、跨区域调用、服务端解码实现/并行计算/后端配置变化；CI/CD 真实 LLM 调用留给冒烟测试，稳定复现逻辑测试用 Mock。
- 思维链参数限制：DeepSeek V4 思考模式返回 `reasoning_content` 与 `content` 并列出不支持/不生效的采样参数；OpenAI 不返回原始内部推理，不同推理模型对 `temperature`、`top_p` 支持可能不同；调用前按模型能力表过滤，结构稳定性依赖 Structured Outputs + 服务端校验 + 失败处理。
- 流式与置信度：TTFT、E2E Latency；logprobs 越接近 0 越确信，-5.0 说明犹豫，用于置信度评估（提取「金额: 1000」低 logprob 需人工复核）、异常检测（监控平均 logprob 突然下降提示 Prompt 漂移或输入异常）、多候选对比（Top-N 候选及概率）；logprobs 增加响应体积，并非所有供应商支持。

## 6.4 幻觉、RAG 与长上下文取舍

- 幻觉：任务边界不清时模型偏题或补写不存在的信息；Prompt 作用是缩小生成范围，质量与长度没有直接关系，关键是 Role、Task、Context、Format 四要素（ai-core-concepts 表：Role「你是一位 10 年经验的 Java 架构师」/ Task「请评审以下代码的性能问题」/ Context「当前线上 QPS 2000，响应时间超 500ms」/ Format「输出 JSON，包含 bottleneck、solution 两个字段」）。
- RAG 检索证据能约束回答范围但不能彻底消除幻觉：检索错误、上下文噪声、引用错配、模型不遵循指令仍会产生错误答案；生产配合引用校验、答案评估、拒答和人工反馈。
- RAG 与长上下文取舍要点：RAG 控制检索片段数量避免无关内容推高输入 Token；长上下文有 O(N²)/TTFT/账单/Lost in the Middle 代价；图片进入多模态 RAG 的预算与延迟影响；评测侧 Recall@k / Context Precision / Context Recall 看检索，Faithfulness / Context Usage / Noise Sensitivity 看生成。
- ai-core-concepts RAG 相关专有术语（挑取）：Embedding、向量检索与向量数据库、Chunking、Parent-Child Chunk（约 300 Token 子块建索引、关联约 1200 Token 父段落，300/1200 只是起始参数）、Hybrid Search（「如何取消订阅」vs「关闭自动续费」用词不同向量更易建立语义关联，`E1027`/`ABX-4421` 更适合 BM25 精确词匹配）、Query Rewrite、Rerank、GraphRAG（「向量 RAG 擅长判断『这段话和我的问题像不像』，GraphRAG 更擅长理解『这些对象之间到底怎么连起来』」）、知识库更新（索引和查询必须用同一套 Embedding 模型及版本，升级需建新索引、同批评测数据对比后切别名，旧索引保留一段时间回滚）。

## 6.5 Streaming / SSE / WebSocket / Chunked

- 同步 vs 流式对比表（7 行，见 2-2）；SSE / WebSocket / HTTP chunked 对比表（见 2-3）；SSE 字段 `data`/`event`/`id`/`retry`（见 2-3）；空行分隔 `\n\n` / `\r\n\r\n`，默认事件类型 `message`，`retry` 单位毫秒。
- Spring：`@GetMapping(produces = MediaType.TEXT_EVENT_STREAM_VALUE)`、`Flux<ServerSentEvent<String>>`、`Flux.interval(Duration.ofMillis(500))`、`ServerSentEvent.<String>builder().id(...).event("token").data(...).retry(Duration.ofSeconds(3)).build()`、`ChatClient` → `Flux<String>` → `.stream().content()`；Java 21 虚拟线程；`{"sequence":12,"delta":"第一行\n第二行"}`；测试 LF、CRLF、空行、代码块、断流半个事件。
- Nginx：`proxy_buffering off; proxy_cache off; proxy_read_timeout 300s; proxy_set_header Connection ""; add_header Cache-Control no-cache;`。
- 流式异常四类与状态：用户取消、超时（连接/TTFT/总时长三层）、断流（`INTERRUPTED`）、重连（`messageId` + 递增 `sequence` + 短期缓存补发，供应商流失效提示重新生成）。

## 6.6 可重试与不可重试错误、幂等

- 错误类型对照表（9 行，见 2-4）：网络瞬断 / 供应商 5xx 500、502、503、504 / Anthropic 529 overloaded / 429（RPM、TPM、RPD、并发）/ 流式中断 / 400 / 401·403 / 安全拒答 / 解析失败（最多 1-2 次）。
- `sleep = min(maxDelay, baseDelay * 2^retryCount) + random(0, jitter)`；最大重试 2-3 次；总体截止时间 SLA 例如 15 秒；`Retry-After`。
- 幂等 Key `tenantId:userId:conversationId:messageId:attemptGroup`；claim 四态（已完成返回历史结果 / 正在生成返回同一流式任务订阅地址 / 失败且可重试创建新 attempt 挂同一业务消息 / 失败不可重试返回失败原因）；`message_id`、`attempt_id`、`provider_request_id`、`stream_sequence`；只允许一个 attempt 为 `final`；Redis `SET NX` / 数据库唯一约束 / 条件原子更新；幂等键绑定请求指纹，同键不同请求返回冲突。
- 上线门禁四条失败链路：客户端取消能否传到供应商；可重试错误是否受总截止时间和原子幂等记录约束；RPM、TPM、并发与租户预算是否同时生效；结构化输出解析失败后是否进入明确失败状态。

## 6.7 限流、模型网关、调用日志字段

- 限流四层架构表、常见限流策略对比表（见 2-6）；四维度 RPM / TPM / 并发数 / 上下文大小 / 最大输出 / 日月预算；请求 A 500 Token + 100 Token vs 请求 B 80K + 8K；`input_tokens + reserved_output_tokens` 先扣预算再发；生产策略组合五行；429 处理 5 步；降级链路四行 + 「降级不是偷偷变差」。
- 观测指标表（9 行，见 2-8）与日志字段 17 个（见 2-8 代码块）；traceId / providerRequestId / TTFT / 总耗时 / 重试次数 / 429 次数 / 解析失败率；ai-core-concepts Metrics：请求量、错误率、P95 延迟、Token 用量、工具失败率。
- 模型网关能力：鉴权、限流、转发 + 模型选择、Token 预算、上下文长度、供应商差异、流式输出、工具调用、结构化响应、成本统计、Prompt 版本；生产级 AI 应用架构中 Prompt 与 Context 管理层（模板版本、变量注入、Token 预算、灰度发布和回滚）、评测与观测层（调用链、版本、质量、延迟、成本和 Badcase，回放与发布门禁）。

## 6.8 JSON Mode vs Structured Outputs / JSON Schema / Function Calling 完整链路

- 「请返回 JSON」五类不可靠：格式漂移、字段缺失、类型错误、额外解释文本、边界条件崩溃（示例见 3-1）。
- 三层定义、三层约束对比表、api-engineering 约束强度表、选型表（见 3-2 / 3-10）；JSON Schema 关键字 `properties`/`required`/`additionalProperties`/`enum`/`type`/`description`/`minimum`/`maximum`/`pattern`/`minLength`/`const`/`oneOf`/`allOf`/`anyOf`/`$ref`；各厂商支持子集不同（OpenAI `strict`、Gemini `response_format`、Anthropic Structured Outputs 与 Strict tool use）；Schema 设计 7 条；`schemaVersion`（`ticket_classification_v1`、`query_order_v1`）。
- Function Calling 7 步链路（见 3-4）；`tool_use_id` 严格匹配（Anthropic）、Gemini 3 每个 `functionCall` 唯一 `id`、`tool_result` 回填、`callId` 原样带回；语义鸿沟示例 `userId: U10086` / `orderId: O202605070001` / `includeLogistics: true`。
- 完整工单分类 Schema、Java `query_order` 参数 Schema（`^O[0-9]{12,20}$`、`query_order_v1`、draft 2020-12）、`ToolCallDispatcher` 分发与错误码（见 3-3 / 3-4）。
- 结构化输出失败四级兜底 + 重试 Prompt 错误示例 + 降级策略表（见 3-8）；五个常见误区（见 3-10）。
- 能力定位表（7 行，见 3-6）：JSON Mode / JSON Schema / Structured Outputs / Function Calling·Tool Calling / MCP / 普通 HTTP API / Agent Skill；「没有固定的 Skill → MCP → Function Calling → HTTP API 层级」。

## 6.9 MCP / HTTP API / Skill 三者边界与工具调用安全治理

- MCP：JSON-RPC 2.0、Server 暴露工具（名称 + 描述 Schema 的元数据）、`tools/call`、Client/Server/Host 协作；MCP Client 可由规则引擎/用户界面/其他程序直接发起 `tools/call`，Server 可访问 HTTP API、数据库、本地文件或进程，不要求底层再经 Function Calling。
- HTTP API：`GET /api/orders/O202605070001` 确定性业务读写；Skill：可复用任务说明书（线上事故复盘 Skill 四步 + 「现象、影响、根因、改进项」）；ai-core-concepts：`Agent = LLM + Planning + Memory + Tools`，Function Calling 表达调用意图、MCP 规定宿主发现外部能力并连接后端、Agent 决定下一步、Skills 保存流程与经验。
- 工具调用安全：三层校验、风险等级分层表（低/中/高/极高，见 3-9）、`prepare_refund`/`confirm_refund`、幂等 `idempotencyKey`、审计日志字段白名单与脱敏（掩码/哈希/令牌化）、OWASP Logging Cheat Sheet、超时短路「模型只能解释当前无法完成，不能猜测结果」；上线前四层检查清单（Schema 层 / 模型调用层 / 服务端执行层 / 降级层，见 3-8）。

## 6.10 Golden Set 冷启动、LLM-as-Judge 偏差、RAG/Agent 评测拆分

- 评测用例对象表（原文保留）：

| 概念 | 含义 | 例子 |
| --- | --- | --- |
| Task | 一条评测任务，包含输入和成功标准 | 「修复空密码绕过登录校验的问题」 |
| Trial | 同一条任务的一次运行 | 同一个 Agent 对同一条任务跑第 3 次 |
| Grader | 对输出或过程打分的评分器 | 单元测试、JSON Schema、LLM-as-Judge、人工复核 |
| Transcript / Trace | 一次运行的完整记录 | 用户输入、模型回复、工具调用、参数、返回值、耗时 |
| Outcome | 任务结束后的真实状态 | 代码测试通过、退款单创建成功、数据库状态更新 |
| Eval Harness | 负责跑任务、记录过程、调用评分器、汇总结果的工程骨架 | 本地脚本、评测平台、Claude Code 搭出来的评测流程 |

- 三种评测方法表（原文保留）：

| 方法 | 准确性 | 速度 | 成本 | 典型评测内容 | 典型使用场景 |
| --- | --- | --- | --- | --- | --- |
| 人工评测 | 高（依赖标注规范与一致性） | 慢 | 高 | 复杂语义判断、边界样本仲裁、业务风险判断 | Golden Set 初始标注、高风险场景最终校验、LLM-as-Judge 校准基准 |
| 规则评测 | 高（规则可描述范围内） | 最快 | 低 | JSON 格式、字段完整性、枚举值、数值边界、引用是否存在 | 格式校验、枚举字段、引用检查、数值边界 |
| LLM-as-Judge | 中（受偏差影响） | 快 | 中 | 答案相关性、事实忠实度、完整性、连贯性、语气是否合适 | 语义相关性、答案连贯性、事实忠实度、多维度综合打分 |

「格式、枚举、引用缺失这类硬错误，先交给规则评测拦住。开放式语义判断再交给 LLM-as-Judge，高风险样本和边界样本保留人工复核。」
- 评测工具表（原文保留）：

| 工具 | 更适合的环节 | 典型用途 |
| --- | --- | --- |
| RAGAS | RAG 指标评测 | Faithfulness、Response Relevancy、Context Precision、Context Recall 等指标 |
| TruLens | RAG/LLM 应用观测与反馈函数 | Groundedness、Context Relevance、Answer Relevance 等质量反馈 |
| LangSmith | LLM / Agent 开发与生产闭环 | Dataset、Trace、离线实验、线上评测、回归测试 |
| Langfuse | 生产 Trace 和评分分析 | Trace 采样、人工评分、LLM-as-Judge、Score Analytics |

「先把 Golden Set、评分标准和版本记录固定下来，再接入平台跑批和展示。」
- Golden Set 冷启动与分层（见 4-2）：20~50 条、50/200/500 只是数字、200 条同类不如 100 条覆盖 10 类场景、Metamorphic Testing、保留集、分层表、每季度复查/失败回流/版本记录。
- LLM-as-Judge 四类偏差与 Judge Prompt 模板（见 4-3）；结果字段 `pass/fail`/`score`/`reason`/`category`/`confidence`；ARES + PPI；G-Eval；MT-Bench。
- RAG 拆分检索/生成两段的指标与两个陷阱（见 4-4）；Agent 评测对象表、检查层表、四类用例表与指标（见 4-5）；任务完成率公式、错误恢复率公式、pass@k / pass^k、90% × 连续 5 次 ≈ 59%。
- 时间和外部环境变化两轨道表（原文保留）：

| 评测轨道 | 环境处理方式 | 主要用途 |
| --- | --- | --- |
| 固定快照回归 | 冻结检索语料、工具返回、数据库初始状态和目标时间 | 比较代码、Prompt、模型、RAG 和 Agent 编排改动 |
| 实时能力探针 | 访问当前 Web、API 和第三方系统 | 检查信息时效、工具兼容性和真实环境适应能力 |

每次实时 Trial 至少记录：任务目标时间、执行时间和时区；搜索查询、访问 URL、抓取时间、来源标注的发布时间或更新时间；Agent 实际读到的正文快照或内容哈希；每条关键事实对应的引证及来源是否支持；业务对证据时效和来源范围的要求。`ground_truth` 写成「目标时间 + 必须满足的事实断言 + 来源要求」，`max_age` 或有效时间段由任务定义；实时探针失败区分四种结果：内容漂移 / 工具或环境失败 / Harness 失败 / Agent 失败。
- 结构化输出评测三层：格式合法率（`JSON.parse()`）、Schema 通过率、字段语义准确率；「一个对象有 10 个字段，9 个字段正确，1 个字段错误；如果错的是关键字段，整体通过率再好看也没用」。
- **完整评测指标体系表（原文大表，逐行保留）**：

| 维度 | 指标 | 计算方式 | 适用场景 |
| --- | --- | --- | --- |
| 检索质量 | Recall@k | 相关文档召回比例 | RAG 知识库 |
|  | Hit Rate@k | 是否至少命中一条 | RAG 快速验证 |
|  | MRR | 第一条相关结果的排名 | 强依赖 Top-1 的 RAG |
|  | Precision@k | 结果精准率 | Token 预算紧张场景 |
|  | Context Precision | 相关上下文是否排在前面 | RAGAS 类 LLM 检索评测 |
|  | Context Recall | 参考答案是否被上下文覆盖 | 缺少文档 ID 标注的早期 RAG 评测 |
| 生成质量 | Faithfulness | 答案是否忠于上下文 | RAG、事实型问答 |
|  | Answer Relevance / Response Relevancy | 答案是否回答了问题 | 通用问答、客服 |
|  | Completeness | 答案是否覆盖关键要点 | 政策解读、合规问答 |
|  | Context Usage | 生成是否有效使用检索上下文 | 检索好但回答仍不好的 RAG 诊断 |
|  | Noise Sensitivity | 错误声明受检索上下文影响的比例（越低越好） | Top-k 较大、上下文混杂的 RAG |
| 动态信息 | 目标时点事实正确率（自定义） | 事实在任务目标时间点是否成立 | Web Search、行情、新闻、版本查询 |
|  | 证据时效合格率（自定义） | 引证是否满足任务定义的有效时间段 | 强时效信息检索 |
|  | 引证支持率（自定义） | 引证是否支持对应的事实声明 | 带来源回答、研究型 Agent |
|  | 必要来源覆盖率（自定义） | 关键结论是否覆盖任务要求的必要来源 | 多来源核验、合规研究 |
| 工具调用 | 工具选择精确率 | 必要且正确的工具调用 / 总工具调用数 | Agent |
|  | 工具选择召回率 | 已覆盖的必要工具调用 / 标注的必要工具调用数 | Agent |
|  | 工具集合完全匹配率 | 选择工具集合与期望集合完全一致的任务 / 总任务数 | Agent |
|  | 参数准确率 | 正确参数 / 总参数数 | Agent |
|  | 不必要调用率 | 多余调用 / 总调用次数 | Agent 效率优化 |
|  | 任务完成率 | 完成任务 / 总任务数 | Agent E2E |
|  | 错误恢复率 | 进入预定义恢复结果 / 工具失败总数 | Agent 鲁棒性 |
| Agent 稳定性 | 至少一次成功率（pass@k） | k 次运行中至少成功 1 次的比例 | 观察能力上限 |
|  | 连续成功率（pass^k） | k 次运行全部成功的比例 | 高风险生产任务 |
|  | 平均轮次 / 工具次数 | 总轮次或工具调用数均值 | 成本、效率和过度探索诊断 |
| Skill 质量 | 触发召回率 | 正确触发 / 应触发样本数 | Skill 路由 |
|  | 误触发率 | 错误触发 / 不应触发样本数 | Skill 路由 |
|  | 产物合格率 | 合格产物 / 总产物数 | PR 总结、报告生成、代码审查 |
|  | 异常稳态率 | 异常输入下安全收敛的比例 | 工具失败、缺参、越权请求 |
| 格式合规 | JSON 格式合法率 | 合法 JSON / 总输出数 | 结构化输出 |
|  | Schema 通过率 | 通过校验 / 合法 JSON 数 | 结构化输出 |
|  | 枚举准确率 | 正确枚举 / 含枚举字段总数 | 分类、状态输出 |
| 成本与延迟 | TTFT | 首 token 等待时间 | 流式输出体验 |
|  | E2E Latency | 从请求到最终结果的耗时 | 整体性能 |
|  | Input / Output Tokens | 输入和输出 token 数 | 成本控制 |
|  | 重试率 | 触发重试的请求比例 | 稳定性诊断 |
| 安全与合规 | 违规请求拦截召回率 | 被拦截的应拒答样本 / 应拒答样本数 | 内容安全 |
|  | 正常请求误拒率 | 被错误拒绝的正常样本 / 正常样本数 | 内容安全 |
|  | 越权操作率 | 未授权或超范围操作 / 总操作次数 | 任务执行型 Agent |
|  | 幻觉率 | 无依据事实断言的比例 | 事实型问答 |
|  | 格式遵循率 | 满足格式约束的输出比例 | Prompt 质量 |
| 用户体验 | 满意反馈率 | 正向反馈 / 有效反馈数 | 客服、助手类应用 |
|  | 追问率 | 需要再次澄清或纠正的会话 / 总会话数 | 对话型 Agent |
|  | 转人工率 | 转人工会话 / 总会话数 | 客服 Agent，需结合转人工策略解读 |

原文注：「其中『动态信息』这一组是本文为了落地实时 Web 评测整理的自定义口径，并非 RAGAS 等框架里的统一指标。真正接入报表前，还要写清楚每项的分母、来源优先级、允许缺失值和人工仲裁规则。」「满意反馈、追问和转人工都是代理指标，不能脱离场景直接判断高低。」「客服 RAG 的第一版评测可以只跟踪 Recall@k、Faithfulness、Answer Relevance、延迟和转人工/满意反馈；Agent 则从任务完成率、关键工具调用、错误恢复和成本开始。」

## 6.11 离线评测 / Trace 回放 / 线上灰度 / CI 评测 / 人工与 Judge 冲突

- 三阶段流程与门禁：离线评测（Golden Set）→ Trace 回放 → 线上灰度 1% → 10% → 100% → 持续监控；Faithfulness 0.82 → 0.79 回归判定问题；内容哈希；非劣效界值 + 效应量 + 置信区间；「下降 3% 就暂停」「连续 3 天」不通用。
- Eval Harness 最小四件事：读取评测集（输入 + 参考答案或成功标准）、调用被测系统、执行评分器（规则/LLM-as-Judge/人工路由）、保存结果（分数、通过状态、失败原因、Trace、模型版本、Prompt 版本、代码提交）；Agent 场景每个 Trial 从干净状态启动做环境隔离；可用 Claude Code / Codex 搭轻量 Harness（5 步：把 Prompt/工具说明/业务规则放进上下文 → 产出评测方案 → 小规模 Golden Set 统一 JSON/表格 → 生成评测脚本或评测 Agent Prompt → 跑批分析输出指标变化、badcase、疑似根因和修复建议）；5 条落到脚本/评分 Prompt 的规则（评分读真实输出不能只根据输入推测；分数/通过状态/原因落结构化 JSON；工具参数构造规则写入 Prompt；调试保留过程记录、批量只保存最终评分 JSON 减少截断；改评测 Prompt 或规则后先用少量样本人工核对排除评测系统自身问题）。
- CI 评测：能力集 / 回归集；绝对阈值 Faithfulness < 0.75、相对阈值任务完成率下降不得超过 5%；500 条 LLM-as-Judge 可能 10 到 30 分钟；harness error 与模型失败分开；`EvalRecord` / `EvalRunSummary` 全字段（见 4-7）。
- Badcase 记录表五组字段：①证据（输入、输出、Trace、工具调用、检索结果、Prompt 版本、模型版本、环境快照、错误日志）②现象（事实错误、答非所问、工具未调用、参数错误、过度承诺、格式错误等）③定位（候选责任层、复现结果、对照实验、排除依据）④根因（主根因、伴随因素、责任模块、问题枚举、置信度、修复建议）⑤回流（负责人、修复动作、回归用例 ID、验证运行 ID）。现象→候选层表（原文保留）：

| 现象 | 优先检查的层 | 需要的证据 |
| --- | --- | --- |
| 关键资料没有进入上下文 | 文档解析、索引、检索、Reranker | 候选文档、分数、过滤条件、索引版本 |
| 资料正确，但回答仍然出现事实错误 | Prompt、上下文编排、生成模型 | 实际 Prompt、上下文位置、模型版本、同证据重跑结果 |
| 应调用工具却没有调用 | 意图识别、Skill 路由、工具描述、Agent 规划 | 路由分数、工具 Schema、Transcript |
| 工具选对，但参数或调用顺序错误 | Agent 规划、参数生成、业务约束 | 实际参数、必需参数、关键步骤断言 |
| 工具返回成功，但外部状态没有变化 | 工具适配器、第三方系统、事务、幂等和结果核验 | API 响应、数据库状态、审计日志、幂等键 |
| 同一快照下多次 Trial 差异很大 | 模型采样、并发、共享状态、缓存和环境隔离 | 随机参数、Trial 初始状态、缓存键、并发日志 |
| 同一时间大量 Case 一起失败 | 外部服务、网络、配额、模型供应商或 Eval Harness | 状态码、超时、配额、Harness 日志、对照服务 |
| Judge 与人工长期分歧 | Rubric、Judge Prompt、Judge 模型或标注规范 | 人工校准集、分维度混淆矩阵、低置信样本 |

「定位时先复现原始快照，再一次只替换一个变量」；「一次线上失败处理完之后，它应该变成后续版本的自动回归用例」。
- 人工与 Judge 冲突处理：收集分歧样本进校准集；二分类看 Cohen's kappa、精确率和召回率；有序评分用加权 kappa；「不能只看一个未考虑类别基线的『80% 一致率』」。
- 评测记录用于下一次发布：每份报告绑定数据集、Prompt、模型、检索配置、评分器、代码版本、目标时间和环境快照；RAG 检索与生成分开计分；Agent 同时保存 Outcome 和 Trace；安全评测同时报告违规请求漏拦截与正常请求误拒；动态信息任务保存当时实际读取的证据；灰度结论附样本量、效应量和不确定性；线上失败经人工确认后回流回归集。
- ai-core-concepts 评测/系统设计要点：公开 Benchmark 只能筛模型；业务评测从 Golden Set 开始，每条用例含输入、预期结果或成功标准、场景标签、评分方式；RAG 分别评估检索与生成；Agent 除最终回答还要检查工具选择、参数、执行轨迹和外部系统真实状态；规则评测/LLM-as-Judge/人工评测三类表（见 4-3 同类表）；「Prompt、模型、检索策略、工具版本和评测结果必须关联，否则分数变化后仍然找不到原因」；确认过的失败 Trace 应脱敏后回流 Badcase 集合。

---

# 七、延伸追问清单：原文以问句形式出现的章节标题 / 思考题（附一句话答案）

> 本节汇总四篇 llm-basis 文章与 ai-core-concepts 中以问句形式出现的**章节标题**、文末**「面试问题」思考题**及开篇**思考题**。每题给一句话答案，作为延伸追问清单；与前文 39 题重复的只给结论指针。

## 7.1 `docs_ai_llm-basis_llm-operation-mechanism.md`

问句式章节标题：
1. **Token 和上下文为什么决定成本与效果？** —— Token 决定输入/输出计费与窗口占用，上下文窗口决定一次能放多少信息，二者加上采样参数共同决定「能放多少、花多少、输出多稳」。
2. **采样参数如何影响输出稳定性？** —— Temperature 调概率形状、Top-p/Top-k 截候选池、Penalty 防复读，低温 + 严格 Schema + 服务端校验才稳。

## 7.2 `docs_ai_llm-basis_llm-api-engineering.md`

问句式章节标题：
1. **一次生产级 LLM 调用包含哪些阶段？** —— 业务请求进入、上下文组装、Token 预算预估、模型网关路由、供应商 API 调用、响应解析、状态回写、观测与告警共 8 阶段，收口到 `LLMGateway`。
2. **同步返回和流式返回有什么区别？** —— 同步等完整结果一次性返回、解析简单；流式边生成边推降低 TTFT，但取消/超时/断流/半成品 JSON/增量落库都要额外处理。
3. **SSE、WebSocket 和 HTTP chunked 这三种流式协议怎么选？** —— 单向文本增量用 SSE，双向实时（语音/插话）用 WebSocket，chunked 只是 HTTP/1.1 传输机制、业务层仍要自定义事件协议。
4. **哪些错误能重试，哪些不能重试？** —— 网络瞬断/5xx/过载/429（谨慎）可有限重试，400/401/403/安全拒答不可重试，解析失败最多 1-2 次格式修复。
5. **为什么要限流？如何限流？** —— 成本由 Token 而非请求数决定，按用户/租户/模型/供应商四层，同时看 RPM/TPM/并发/上下文/最大输出/预算，先扣预算再发。
6. **为什么要结构化返回？** —— 让程序能稳定消费模型输出，而不只是「看起来像 JSON」，需 Schema + 原生能力 + 服务端校验 + 失败兜底。
7. **Java 后端怎么落地 LLM 调用？** —— 用 `LLMGateway` 聚合 `LLMClient`/`RateLimiter`/`IdempotencyStore`/`TokenEstimator`/`Observation`，幂等 claim 落 Redis `SET NX`，同步与流式分开、解析在落库前做。

文末「面试问题」思考题（8 条，前 7 条与第三部分 2-1~2-7 对应）：
1. **大模型 API 调用的完整链路是什么** —— 按 8 阶段生产链路治理，不能只封装成一个 HTTP 请求（见 2-1）。
2. **Streaming 为什么能改善体验** —— 降低 TTFT，不保证总耗时变短、不天然省钱，后端需处理取消/超时/断流/重连/半成品 JSON 和增量落库（见 2-2）。
3. **SSE 和 WebSocket 怎么选** —— 单向推文本用 SSE（注意 `text/event-stream` 换行与事件边界、反向代理缓冲），双向频繁交互用 WebSocket，chunked 偏底层（见 2-3）。
4. **哪些大模型 API 错误可以重试** —— 网络瞬断、部分 5xx、504、过载可有限重试；429 结合 `Retry-After`/限流头/排队/降级；400、401/403、安全拒答不重试；解析失败 1-2 次格式修复（见 2-4）。
5. **哪些大模型调用需要做幂等** —— 涉及落库、扣费、发通知或工具写操作必须做；用业务消息 ID 生成幂等 Key 绑定请求指纹，多 attempt 挂同一业务消息、只允许一个 final（见 2-5）。
6. **限流为什么不能只按 QPS** —— 成本由 Token 决定，500 Token 请求与 80K Token 请求压力差几个量级，要同时看 RPM/TPM/并发/上下文/最大输出/租户预算（见 2-6）。
7. **JSON Mode 和 Structured Outputs 有什么区别** —— 前者只保证合法 JSON 语法，后者生成阶段应用 Schema 约束字段/类型/枚举/必填，各厂商 Schema 子集不同要写兼容层（见 3-2）。
8. **流式结构化返回怎么处理** —— 不要边收 delta 边 `JSON.parse()` 完整对象，增量阶段只展示/记录片段，等正常结束事件后拼完整再做 Schema 校验，或用官方 accumulator / 自维护 buffer + sequence + 结束状态。

## 7.3 `docs_ai_llm-basis_structured-output-function-calling.md`

问句式章节标题：
1. **为什么「请返回 JSON」不可靠？** —— 自然语言约束不是工程契约，会格式漂移、缺字段、类型错误、加解释文本、边界条件崩溃。
2. **怎样把 JSON 从格式要求变成工程契约？** —— 分清 JSON Mode（语法）/ JSON Schema（契约）/ Structured Outputs（生成阶段应用契约）三层各司其职。
3. **JSON Mode 只能保证什么？** —— 通常只保证输出是合法 JSON 语法，不保证业务字段与枚举正确（`"category":"pay"` 仍是合法业务错误）。
4. **JSON Schema 负责定义什么？** —— 字段、类型、必填、枚举、额外属性等契约，只描述不执行生成，也不负责外部调用。
5. **Structured Outputs 能前移哪些约束？** —— 把 Schema 传入模型调用、在生成阶段约束结构，但拒答/截断/工具失败时业务请求仍可能不成功，且各厂商 Schema 子集不同。
6. **Function Calling 到底调用了什么？** —— 模型只生成「工具名 + 参数」的结构化调用意图，真正执行的是业务服务 / Agent Runtime / MCP Host / 供应商托管环境。
7. **为什么需要工具调用意图？** —— 弥合自然语言输入与后端确定性 API 之间的语义鸿沟，完成「意图 → 结构化参数」映射但不绕过权限与副作用。
8. **Function Calling、MCP Tool、HTTP API、Agent Skill 是什么关系？** —— 解决不同问题、可按需组合，不存在固定层级；MCP 管标准化接入、HTTP API 管业务读写、Skill 管 SOP 编排。
9. **Function Calling 如何映射到 HTTP API？** —— 由工具执行层做「模型调用意图 → 服务端校验参数 → 调用 `GET /api/orders/{orderId}`」的映射。
10. **MCP Tool 解决的是哪一层标准化？** —— Client 与 Server 之间基于 JSON-RPC 2.0 的工具发现、描述、调用和结果返回，不替代模型推理。
11. **Agent Skill 为什么不是 Function Calling 的语法糖？** —— Skill 是可复用任务说明书（上下文 + 步骤 + 规则），可调用工具也可纯文本分析，不绑定工具调用。
12. **什么时候该用 Structured Outputs，什么时候该上工具？** —— 先看结果会不会触发外部动作，再看工具要在多少客户端复用：轻量抽取用 Structured Outputs，读写业务系统用 Function Calling，多工具多客户端用 MCP，固定 SOP 用 Skill。
13. **结构化输出怎么工程化落地？** —— Schema 设计、字段说明、枚举优先、必填与版本 `schemaVersion`、校验失败带错误有限重试、按场景降级，全链路日志与审计。
14. **工具调用安全怎么保证？** —— 结构/业务/权限三层校验、风险分级、二次确认、服务端生成幂等键、审计日志白名单脱敏、超时短路。
15. **上线前应该检查哪些工程细节？** —— 沿 Schema 层 / 模型调用层 / 服务端执行层 / 降级层四层逐项核对（见 3-8）。

文末「面试问题」思考题（9 条，与第三部分 3-1~3-9 对应，一句话答案同前文）：
1. **为什么只写「请返回 JSON」不可靠** —— 只是自然语言约束，需结合 JSON Schema、Structured Outputs、服务端校验、失败重试和降级。
2. **JSON Mode 和 Structured Outputs 有什么区别** —— 前者管 JSON 可解析，后者生成时应用 Schema，权限与业务状态仍需服务端单独校验。
3. **JSON Schema 在大模型应用里解决什么问题** —— 变成可校验的数据契约（`properties`/`required`/`enum`/`additionalProperties`/`pattern`/`minimum`/`maximum`），给模型约束也给服务端兜底。
4. **Function Calling 的完整链路是什么** —— 注册工具定义 → 模型生成工具名和参数 → 业务侧校验并执行 → 结果回填模型 → 模型生成最终回答，执行权在业务侧。
5. **Function Calling 和 MCP 有什么区别** —— 前者模型侧意图生成机制，后者应用层标准化工具发现/描述/调用/返回协议。
6. **MCP Tool 和普通 HTTP API 有什么关系** —— MCP Tool 暴露给 AI Host、内部可调 HTTP API/数据库/脚本；MCP 解决接入标准化，HTTP API 解决业务能力。
7. **Agent Skill 和 Function Calling 是一回事吗** —— 不是，Skill 存任务 SOP 与上下文约束流程，Function Calling 只生成工具名和参数。
8. **结构化输出失败后怎么处理** —— 服务端校验拿具体错误 → 带错误让模型有限重试 → 仍失败进降级（人工队列/规则兜底/追问/明确失败），禁止编答案。
9. **工具调用为什么必须做安全治理** —— 模型参数是不可信输入，格式通过不代表有权访问，所有工具做参数与权限校验，副作用调用加二次确认与幂等。

## 7.4 `docs_ai_llm-basis_llm-evaluation.md`

问句式章节标题：
1. **为什么公开 benchmark 不够用？** —— 榜单用干净通用数据，覆盖不到业务术语、脏输入、权限规则和少数高风险失败，只能粗筛模型。
2. **一条评测用例里有什么？** —— Task（输入 + 成功标准）、Trial、Grader、Transcript/Trace、Outcome、Eval Harness 六类对象。
3. **Golden Set 怎么构建？** —— 生产日志分层采样 + 人工构造（正常/边缘/对抗）+ 失败案例回填 + 冷启动文档种子，分层与版本记录比总量更关键。
4. **数据从哪来？** —— 生产日志（不满意/追问/转人工/差点失败）、人工构造、失败案例回填，冷启动用知识库文档 + RAGAS 生成 + 人工审核。
5. **无法穷举 Case，怎么扩展覆盖？** —— 按输入/上下文/工具/状态扰动 + 蜕变测试（Metamorphic Testing）写关系断言，并留保留集。
6. **多少条够用？** —— 第一版 20~50 条真实任务验证流程，发布门禁样本量按风险、基线方差和最小可接受差异估算，50/200/500 只是数字。
7. **评测工具怎么选？** —— RAGAS 评 RAG 指标、TruLens 做反馈函数、LangSmith 做开发生产闭环、Langfuse 做生产 Trace 与评分分析，先固定 Golden Set 再接平台。
8. **LLM-as-Judge 怎么用才可靠？** —— 维度/分档/反例清晰的 Prompt、Reference-based 优先、交换 A/B 顺序、跨模型族 Judge、人工校准集与低置信复核。
9. **Judge Prompt 怎么写？** —— 给问题/参考资料/参考答案/回答，先检查硬性约束与事实依据，再按 Faithfulness、Answer Relevance、Completeness 三维度各 1-5 分输出结构化 JSON。
10. **RAG 应用怎么评测？** —— 拆检索（Recall@k、Hit Rate@k、MRR、Context Precision/Recall）与生成（Faithfulness、Context Usage、Noise Sensitivity）两张账。
11. **Agent 应用怎么评测？** —— 分对话/信息型、任务执行型、混合型，Outcome 与 Transcript 分开看，查最终状态、决策执行、运行稳定性、交互边界。
12. **时间和外部环境一直变化，怎么评？** —— 两条轨道：固定快照回归冻结语料/工具返回/初始状态/目标时间，实时能力探针访问当前 Web/API，结果不混成一个分数。
13. **Skill 怎么单独评？** —— 触发用例、核心逻辑用例、产物质量用例、异常容错用例四类。
14. **评测 Harness 怎么搭？** —— 读评测集、调被测系统、执行评分器、保存结果四件事，Agent 场景每 Trial 隔离环境。
15. **结构化输出怎么评测？** —— 格式合法率（`JSON.parse()`）、Schema 通过率、字段语义准确率三层，拆到字段级。
16. **阈值怎么定？** —— 绝对阈值守底线（如 Faithfulness < 0.75 不通过）+ 相对阈值防退步（如下降不得超过 5%），组合使用。
17. **速度和覆盖度怎么平衡？** —— PR 只跑核心回归集、完整 Golden Set 放主分支/定时、Trace 回放放重大发布前，样本量由等待预算/配额/统计功效反推。

文末「面试问题」思考题（13 条；前 8 条与第四部分 4-1~4-8 对应，第 9~13 条为额外延伸）：
1. **为什么不能只靠公开 benchmark 评估 AI 应用质量？** —— 榜单适合粗筛，不能代替业务 Golden Set（见 4-1）。
2. **Golden Set 应该怎么构建？** —— 生产日志分层采样 + 人工构造 + 失败回流 + 冷启动种子，发布门禁样本量按分层/方差/最小可接受差异估算并留版本记录（见 4-2）。
3. **LLM-as-Judge 有哪些主要偏差，怎么缓解？** —— 位置偏差交换 A/B 顺序、冗长偏差靠 Prompt 与校准样本、同源偏差跨模型族 + 人工复核、客观正确性给参考答案/测试结果（见 4-3）。
4. **RAG 评测为什么必须分检索和生成两段？** —— 「回答不准」可能来自没召回也可能来自没用上，先看退货政策有没有进上下文再决定改检索还是改 Prompt（见 4-4）。
5. **Agent 评测为什么比 RAG 更复杂？** —— 连续决策、调用工具、修改状态，终点成功不代表过程可靠，要查工具/参数/恢复/Trace 越权（见 4-5）。
6. **离线评测、Trace 回放、线上灰度分别解决什么问题？** —— 已知问题回归、真实轨迹补盲区、小流量观察用户反馈与数据分布，三类证据阶段不同不能互替（见 4-6）。
7. **CI 里的评测如何平衡速度和覆盖度？** —— PR 跑核心回归集、完整集放主分支/定时、Trace 回放放重大发布前，样本量由等待预算/配额/最小回归幅度反推，同时查绝对底线/相对 baseline/置信区间（见 4-7）。
8. **如果 LLM-as-Judge 和人工评测结果不一致怎么办？** —— 分歧样本进校准集、细分评分维度，二分类看 Cohen's kappa/精确率/召回率、有序评分用加权 kappa，别只看「80% 一致率」（见 4-8）。
9. **Agent eval 里的 task、trial、grader、transcript 分别是什么？** —— Task 固定输入和成功标准，Trial 是同一 Task 的一次执行（关键任务跑多次），Grader 是规则/LLM-as-Judge/人工评分器，Transcript 记录回复/工具调用/参数/返回值/中间结果；Outcome 确认最终状态、Transcript 定位过程问题。
10. **Skill 应该怎么单独评测？** —— 路由（该启动/不该误触发）、主流程（正常 + 高风险分支）、交付物（格式字段业务要求）、异常处理（缺参/工具失败/越权安全收敛）四类。
11. **评测 Harness 在 AI 应用里负责什么？** —— 把评测集、被测系统、Trace、评分器、报告和版本信息接成可重复运行流程，Agent 每个 Trial 隔离环境；早期可用 Claude Code / Codex 搭轻量 Harness，业务口径与发布决策仍由人确认。
12. **时间和 Web Search 结果一直变化，怎么评？** —— 固定快照回归冻结目标时间/网页正文/工具响应/索引/初始状态判断改动是否回归，实时能力探针按运行时检查事实/证据时效/引证支持/来源要求；报告保存任务时间、时区、URL、抓取时间、正文快照或内容哈希，失败区分内容变化/工具环境故障/Harness 缺陷/Agent 判断错误。
13. **出现 Badcase 后，怎么区分模型、第三方系统、架构和代码问题？** —— 先保存可复现输入、Trace、外部状态和环境快照，按现象定候选层，一次只替换一个变量，修复后把原始 Case、根因层、修复动作和验证运行 ID 回填回归集。

## 7.5 `docs_ai_ai-core-concepts.md`

开篇思考题（原文第 20 行，三连问）：
1. **模型为什么每次回答不完全一样？** —— 自回归生成按概率分布采样，Temperature/Top-p 等解码参数与模型版本、服务端实现共同带来非确定性。
2. **Agent 为什么需要循环？** —— 普通模型调用生成一段文本就结束，Agent Runtime 要检查工具调用、执行工具、把结果写回上下文，再让模型决定下一步，故围绕循环展开。
3. **RAG 已经检索到文档，为什么仍然可能答错？** —— 检索错误、上下文噪声、引用错配和模型不遵循指令仍会产生错误答案，检索证据只能约束范围不能彻底消除幻觉。

问句式章节标题：
4. **什么是 Agent？** —— `Agent = LLM + Planning + Memory + Tools`：LLM 管任务理解与决策，Planning 管步骤依赖，Memory 存当前状态或历史，Tools 连接数据库/API/文件系统/代码执行环境；工具返回值是 Observation，运行时追加到上下文。
5. **什么是 RAG？** —— 给模型挂可检索知识源（公司规章、产品文档、实时数据库查询结果），可按用户/租户/角色/会话做权限过滤或个性化检索；与长期记忆的区别在数据来源和生命周期。

相关原文列表中以问句形式出现的文章标题（挑与大模型基础、Token、评测相关者）：
6. **LLM 运行机制：Token、上下文窗口与采样参数怎么影响输出？** —— Token 切分决定成本、上下文窗口决定容量、采样参数决定输出波动，三者共同决定一次调用的效果与账单。
7. **大模型提示词工程（Prompt Engineering）是什么？提示词技巧有哪些？** —— Prompt 是输入给 LLM 的任务指令，作用是缩小生成范围，关键是交代清 Role、Task、Context、Format 四要素而非堆修饰词。
8. **上下文工程（Context Engineering）是什么？和 Prompt Engineering 有什么区别？** —— Context Engineering 在有限 Token 窗口中选择、组织和更新模型当前需要的信息（规则、记忆、工具描述、会话状态、外部观察、Token 预算），Prompt Engineering 更关注指令本身如何表达，是其中一个更局部的问题。
9. **什么是 Model Context Protocol (MCP)？和 Function Calling、Agent 什么关系？** —— MCP 规定宿主如何发现外部能力并连接后端服务；Function Calling 让模型表达调用工具的意图；Agent 在多轮执行中决定下一步，三者各管一段。
10. **Agent Skills 是什么？和 Prompt、MCP 到底差在哪？** —— Skills 保存完成某类任务所需的流程和经验（任务说明书），Prompt 管单次指令表达，MCP 管工具与上下文接入标准化。
11. **Loop Engineering 是什么？为什么说它是新瓶装旧酒？** —— 【补充】此处为相关原文列表中的问句标题，源文档 ai-core-concepts 正文未展开该问的答案，仅作为延伸追问列出；成稿时如需作答须另查 `docs_ai_agent_loop-engineering.md`。
12. **什么是 GraphRAG？** —— 相比向量 RAG 判断「这段话和我的问题像不像」，GraphRAG 更擅长理解「这些对象之间到底怎么连起来」。
13. **AI 可观测性与 Trace：如何还原 Agent 的完整执行过程？** —— 【补充】同为相关原文列表中的问句标题，ai-core-concepts 正文未展开；要点可指向「确认过的失败 Trace 应脱敏后回流 Badcase 集合」与 Metrics（请求量、错误率、P95 延迟、Token 用量、工具失败率）。

其他以问句形式出现、与大模型基础/评测相关的链接标题（ai-core-concepts 相关原文列表）：
14. **Harness Engineering：六层检查框架、上下文管理与工程实践？** —— 关注长链路任务中的持续执行、纠偏、观测和恢复（文件系统、沙箱、约束执行、反馈回路、观测），与 Prompt/Context Engineering 并列（ai-core-concepts 表：Prompt Engineering「怎么把指令说清楚」、Context Engineering「该给 Agent 看什么」、Harness Engineering「系统怎么持续执行、纠偏、观测和恢复」）。
15. **如何选择合适的切分策略？（Chunking 配图标题）** —— 不同文档类型先选符合其结构的切分方式，再用业务查询评测调整。

> 注：`docs_ai_llm-basis_README.md` 的「高频问题」5 条（见本笔记开头「专题 README」段）与 `docs_ai_interview-questions_llm-interview-questions.md` 题目清单不属本章节标题，已分别作为复习锚点与逐题正文覆盖，不在此重复列出。

---

# 八、【补充】源文档未展开的延伸（整理者补充，均标注）

1. **【补充】Temperature 与 Top-p 的调参顺序**：工程上通常「先固定 Temperature，再用 Top-p 收尾」，避免两个参数同时大幅调整导致分布形状与候选池一起变化、难以归因；源文档给出的是各场景推荐区间与组合效果，未明确调参顺序。
2. **【补充】贪婪解码与 beam search 的区别**：Temperature=0 通常按贪婪解码（每步取最高分）处理，与 beam search（维护多条候选序列）不是一回事；源文档只讨论了贪婪解码与重复循环风险，未展开 beam search。
3. **【补充】SSE 重连的 `Last-Event-ID`**：浏览器 `EventSource` 自动重连时会在请求头带上最后收到的 `id`，服务端据此决定补发起点；源文档提到 `id` 字段「配合浏览器重连语义可做断点提示」和服务端保存 `sequence` 补发，但未点名该请求头名称。
4. **【补充】幂等与「至少一次 / 至多一次」语义**：模型调用链路本质是「至少一次投递 + 业务侧去重」，因此幂等表要同时承载「进行中 / 成功 / 失败」状态，而不是只做去重集合；源文档给出了 claim 四态与原子存储要求，未用该分布式语义术语概括。
5. **【补充】结构化输出与「契约测试」**：把 JSON Schema 当服务间契约管理（版本、消费者兼容、灰度），思路可类比 OpenAPI/Protobuf 的 schema evolution；源文档给出 `schemaVersion` 与灰度删除字段的做法，未使用「契约测试」这一术语。
6. **【补充】评测指标的分母与置信区间**：任何比率型指标（通过率、召回率、幻觉率）在跨版本比较时都应附样本量与置信区间，否则小幅波动无法区分真实回归与抽样噪声；源文档强调「效应量与置信区间」「样本量估算」「不照搬固定数字」，未把这些统一归纳为比率指标的统计口径要求。
7. **【补充】LLM-as-Judge 与被评模型的「能力错位」**：当 Judge 明显弱于被评模型时，对复杂推理题的评分可信度会下降；源文档从「有限推理能力」和「Reference-guided Judge」角度讨论，未用「能力错位」概括，也未给出可用/不可用的能力阈值。
8. **【补充】综合场景题 5-1 的「状态外置」**：把关键业务状态放进外部结构化存储、每轮只注入必要片段，本质是把「上下文窗口」当缓存而非数据库；源文档给出「历史裁剪/摘要/减少 RAG Top-K」与 `usage` 监控，但未明确用「状态外置」表述。
9. **【补充】概念边界一句话记忆法**：JSON Mode 管「语法」、JSON Schema 管「契约」、Structured Outputs 管「生成」、Function Calling 管「意图」、MCP 管「接入」、HTTP API 管「执行」、Skill 管「流程」——这是整理者为便于记忆做的归纳，源文档明确反对给这些概念排固定层级，此处仅作助记，不构成调用链顺序。
