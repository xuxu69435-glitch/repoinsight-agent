# RepoInsight Agent

RepoInsight Agent 是一个基于 LangChain + LangGraph 的本地代码仓库分析 Agent。

它面向本地仓库分析场景：用户提供一个经过校验的项目路径，工具只在该项目根目录内读取文件、搜索代码、检查 Git 状态，并在 `project_root/reports` 下生成结构化 Markdown + JSON 报告。

当前状态：v0.8.0 GitHub 发布准备版本。

## 核心特性

- LangChain 工具调用 Agent
- LangGraph 确定性 workflow
- Project profile detector
- 安全命令白名单
- Git status / diff 分析
- 结构化 Markdown + JSON 报告
- 不需要 API Key 的 no-LLM workflow
- 可选的 LLM 增强 workflow
- 用于本地诊断的 `doctor` 命令

## 为什么适合本地代码仓库分析

- 默认 workflow 不调用 LLM，适合快速、本地、可重复的仓库检查。
- Project Detector 可以识别语言、框架、入口文件、脚本、包管理器和关键配置。
- Git 分析只读取状态、diff 和 diff 统计，不修改仓库历史。
- 报告同时输出 Markdown 和 JSON，既方便阅读，也方便后续 UI、测试和评测。
- 工具层有明确安全边界，不会访问项目根目录外的文件。

## 快速开始

```bash
python -m pip install -e ".[dev]"
python -m repoinsight.cli version
python -m repoinsight.cli profile --path .
python -m repoinsight.cli workflow "Analyze this project for open-source readiness" --path . --no-llm
```

需要 Python 3.11 或更高版本。

## API Key 配置

只有 LLM 相关命令需要 API Key。复制示例文件后填入自己的配置：

```bash
cp .env.example .env
```

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4.1-mini
```

- `ask` 命令需要 `OPENAI_API_KEY`。
- `workflow --with-llm` 需要 `OPENAI_API_KEY`。
- `workflow --no-llm` 不需要 API Key。
- `doctor` 不需要 API Key。

不要提交真实 API Key。

## 命令示例

```bash
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli profile --path .
python -m repoinsight.cli profile --path . --json
python -m repoinsight.cli doctor --path .
python -m repoinsight.cli workflow "Analyze this project" --path . --no-llm
python -m repoinsight.cli ask "Analyze this project architecture" --path .
```

`profile`、`doctor` 和 `workflow --no-llm` 都可以在没有 API Key 的情况下运行。

`ask` 会创建 LangChain Agent，让 Agent 调用仓库分析工具，并输出报告目录和返回的 Markdown/JSON 报告路径。

`workflow` 会运行 LangGraph 流程：

```text
Project Profile -> Plan -> Evidence -> Analyze -> Report
```

默认 `--no-llm` 模式不会调用 LLM，会生成：

```text
reports/workflow_analysis_report.md
reports/workflow_analysis_report.json
```

使用 `--with-llm` 时，LLM 只基于 workflow 已收集的 profile、plan 和 evidence 生成结构化分析结果。LLM analyzer 不直接读取文件、不执行命令、不写文件。

## 安全边界

- Agent 只能访问 `project_root` 内的文件。
- 命令执行使用白名单，并通过 `shell=False` 运行。
- 不允许 `git commit`、`git push`、`git reset`、`git clean`。
- 不允许 `npm install`、`pnpm install` 等安装命令。
- 唯一写入位置是 `project_root/reports/`。
- LLM workflow analyzer 不直接读文件、不执行命令、不写文件。
- `doctor` 只显示 API Key 是否配置，不会打印真实 key。

## 架构说明

- CLI：Typer 命令和 Rich 输出。
- Tools：文件、搜索、报告、命令和 Git 工具。
- Analyzers：确定性 Project Detector。
- LangChain Agent：面向交互式问题的工具调用 Agent。
- LangGraph Workflow：profile、plan、evidence、analyze、report 的确定性流程。
- Reporting：Pydantic `AnalysisReport` 渲染为 Markdown 和 JSON。
- Safety Guards：路径边界、命令白名单、报告写入检查。

## GitHub 提交前检查

```bash
python -m ruff check . --no-cache
python -m pytest
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli profile --path . --json
python -m repoinsight.cli doctor --path .
python -m repoinsight.cli workflow "Analyze this project for open-source readiness" --path . --no-llm
git status --short
```

提交前确认不要提交 `.env`、`reports/`、`.pytest_cache/`、`.ruff_cache/`、`__pycache__/`、`.venv/` 和其他本地生成文件。

## 示例输出

workflow 会在被分析项目下生成：

```text
reports/workflow_analysis_report.md
reports/workflow_analysis_report.json
```

静态示例报告位于 `examples/reports/example_report.md`。

## Roadmap

- v0.8 GitHub-ready release
- v0.9 example gallery and more project detectors
- v1.0 stable CLI and packaged release

## License

MIT。详见 `LICENSE`。
