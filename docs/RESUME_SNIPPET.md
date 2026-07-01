# RepoInsight Agent｜基于 LangChain / LangGraph 的代码仓库分析 Agent｜个人开源项目

- 基于 LangChain 构建工具调用 Agent，将文件读取、代码搜索、Git 分析、安全命令执行和结构化报告写入封装为受控仓库分析工具。
- 设计并实现 LangGraph workflow，以 Project Detector、分析计划、证据收集、结构化分析和报告生成组成可测试、可复现的本地分析流程。
- 建立安全命令白名单、路径边界和报告写入边界，禁止任意 shell、Git 破坏性操作、依赖安装和项目根目录外文件访问。
- 支持 no-LLM / with-LLM 双模式，输出 Markdown + JSON 结构化报告，兼顾本地无 Key 使用、LLM 增强分析和后续 UI/评测集成。
