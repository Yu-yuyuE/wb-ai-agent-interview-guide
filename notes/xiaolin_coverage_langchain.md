# 小林面试笔记 · LangChain 框架专题（12 题）覆盖度判定

统计：covered **0** / partial **5** / missing **7**（共 12 题）。

判定口径：`covered` = 指南里有专门一节回答该题主要考点；`partial` = 指南有相关概念（Workflow、Graph、State、Memory、Tools 等）但缺该框架的具体机制 / API / 版本细节；`missing` = 指南基本没有对应内容。本指南主体是 JavaGuide `docs/ai` 的通用大模型基础、AI Agent、项目实战、RAG 与系统设计知识，基本不覆盖 LangChain / LangGraph / LlamaIndex / LangChain4j / Deep Research 的具体 API 与架构，且框架专题在附录 TODO 表中多处标注「待写」，因此本专题没有 `covered` 题。

| 题号 | 题干 | 判定 | 对应指南章节 | 判定依据 / 缺口说明 |
| --- | --- | --- | --- | --- |
| LC-01 | 1. 你了解过哪些 AI Agent 开发框架？ | missing | — | 无专门章节列举主流框架定位与选型。仅第三部分 §13 Q-A28 讲 Spring AI 2.0.0 / AgentScope Java 2.0.1 的「框架能力 vs 自研能力」边界，【预测题 13–15】与附录 TODO G09/G11/G12 标注 Java 框架专题「待写」；缺 LangChain、LangGraph、LlamaIndex、CrewAI、OpenAI Agents SDK 各自的抽象层次、适用场景与选型依据。 |
| LC-02 | 2. 如何理解 LangChain 中的 Chain？ | missing | — | 全文 `Chain` 只出现在 CoT（思维链）、Prompt Chain（多阶段提示链）等通用词条里，与 LangChain 的 Chain 概念无关；无 Runnable、LCEL、`RunnableSequence` / `RunnableParallel`、旧式 `LLMChain` / `SequentialChain` 迁移到 `langchain-classic` 等任何内容。 |
| LC-03 | 3. LangChain 的底层架构与实现原理是什么？ | missing | — | 指南讲通用 Agent 组成与 Agent Loop，但没有任何框架分层架构：`langchain-core` 标准协议、独立集成包、`create_agent` 编译成 LangGraph 状态图、Message/ToolMessage 回写、State / Context / Store 划分、Middleware 扩展点全部缺失。 |
| LC-04 | 4. 使用 LangChain 构建 Agent 的核心步骤是什么？ | partial | 第二部分 Q1–Q8、Q53–Q58；第三部分 §14–§19 | 有 `Agent = LLM + Planning + Memory + Tools`、Agent Loop 完整流程、工具注册、结构化输出、超时/幂等/重试、HITL 恢复、Trace 与评测等通用工程步骤，能覆盖「完整 Agent 不止是调一次模型」这一层；但缺 `create_agent` 的七步主线与 `system_prompt`、`response_format`、`checkpointer`、`store`、`middleware` 等 LangChain 具体入口。 |
| LC-05 | 5. 在 LangChain 中，如何为 Agent 注册工具？ | partial | 第二部分 Q6；第一部分 3-4 / 3-9；第三部分 §14–§15 | 有工具 `description` 为何关键、Function Calling 完整链路、JSON Schema 参数约束、工具调用八道检查与风险四级分级，能覆盖「工具是模型与业务代码之间的调用合同」；但缺 `@tool`、`StructuredTool.from_function`、`BaseTool`、`args_schema`、`ToolRuntime` 注入可信身份，以及同步/异步工具与错误分类的框架实现。 |
| LC-06 | 6. LangChain 如何实现短期记忆和长期记忆？ | partial | 第二部分 Q9–Q16 | 第二部分有整套 Agent Memory 章节，Q9 专门讲短期记忆（Session 级、上下文窗口）与长期记忆（跨 Session、Record & Retrieve）的区别，Q10–Q16 覆盖压缩、过期、冲突、污染与治理；但缺 LangChain 的 `State` + `thread_id` + `Checkpointer` 与 `namespace/key` + `Store`、`ToolRuntime` 读取边界、旧 `Conversation*Memory` 迁入 `langchain-classic` 等具体机制。 |
| LC-07 | 7. LangChain 和 LlamaIndex 有什么区别？ | missing | — | 指南第四部分是 RAG 系统知识而非框架知识；`LlamaIndex` 仅在「Context Engineering 工具清单」「GraphRAG 的 PropertyGraphIndex」处作为名字零星出现，没有任何框架定位对比，也没有 LlamaIndex 的 Document/Node/Index/Query Engine/Workflow 数据抽象或「检索能力包装成 Tool 交给 Agent」的组合方式。 |
| LC-08 | 8. LangChain4j 主要解决了哪些问题？ | missing | — | 仅【预测题 13】给出「Spring AI 和 LangChain4j 怎么选」的几句要点，且附录 TODO G09/G11 明确标注框架专题「待写」；§13 讲的是 Spring AI / AgentScope Java 的能力边界。缺 `ChatModel` / `EmbeddingModel` / `EmbeddingStore` 统一抽象、AI Services 声明式接口、`@Tool`、`ChatMemory`、`RetrievalAugmentor`、Spring Boot / Quarkus 集成与 Guardrails 边界。 |
| LC-09 | 9. LangChain 和 LangGraph 的核心区别是什么？ | partial | 第二部分 Q41–Q52（重点 Q42 / Q48 / Q49） | 有 Workflow、Graph、Loop 三者关系、Graph Loop 与 Agent Loop 区别、State 的 Replace/Append/Reducer、条件边与动态路由等整节通用概念，Q42 / Q48 / Q49 还给出 `TypedDict`、`add_conditional_edges`、`add_messages`、`Send` 等 LangGraph 具体 API 对照；但没有「高层 Agent 框架 vs 低层编排运行时」的定位对比、`create_agent` 构建在 LangGraph 之上的版本事实，以及 middleware 与图编排的分工。 |
| LC-10 | 10. LangGraph 相比于 LangChain 有哪些核心优势？ | partial | 第二部分 Q41–Q52（重点 Q42 / Q48 / Q49 / Q51） | 有 State + Node + Edge、并行写入需 Reducer、条件边、`MemorySaver`、`interrupt_before` / `update_state`、工作流中断恢复（持久化 + checkpoint）等概念与部分 API，可支撑「显式状态机、可恢复」这一层；但缺 `interrupt()` / `Command(resume=...)`、时间旅行、Functional API、durable execution 幂等、子图与 Graph/Functional 选型，以及 LangGraph 优势与适用场景的系统对比。 |
| LC-11 | 11. LangChain 大版本升级有哪些核心变化？ | missing | — | 指南只有 Spring AI 2.0.0 / AgentScope Java 2.0.1 的版本号与「按实际 API 重新核对」的提醒、第六部分「工具接口是否有版本号」等通用工程点；完全没有 LangChain 的拆包（`langchain-core` / `langchain` / `langchain-community` / 独立厂商包）、Runnable 与 LCEL 统一协议、Agent 运行时转向 LangGraph、v1 以 `create_agent` + middleware 聚焦 Agent、旧 Chain 迁入 `langchain-classic` 等演进主线，也没有跨版本迁移的回归测试要点。 |
| LC-12 | 12. Deep Research 的实现逻辑和适用场景是什么？ | missing | — | 指南仅在多 Agent 编排模式里出现 Supervisor-Manager、在评测表里出现「研究型 Agent / 引证支持率」、在上下文工程里出现 Sub-agent 上下文隔离，均无研究型 Agent 架构；缺 Research Brief、Supervisor 拆子课题、Researcher 并行取证、证据压缩与缺口补搜、统一写作、`open_deep_research` 与 Deep Agents 的区分，以及宽度/深度预算与提示词注入治理。 |

## 判定分布

- `covered`：0 题。
- `partial`：LC-04、LC-05、LC-06、LC-09、LC-10，共 5 题。共同点是指南有直接对应的整节通用概念（Agent 构建与工程化、Tools 注册与治理、Agent Memory、Workflow/Graph/Loop），只缺框架机制 / API / 版本细节。
- `missing`：LC-01、LC-02、LC-03、LC-07、LC-08、LC-11、LC-12，共 7 题。共同点是题目考点落在框架生态、框架自身架构、框架对比、框架版本或框架专有特性上，指南没有对应章节，最多只有框架名被顺带提及或 TODO「待写」登记。
