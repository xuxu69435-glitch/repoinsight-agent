# RepoInsight Agent

RepoInsight Agent 是一个基于 LangChain 的本地代码仓库分析 Agent。用户输入本地
项目路径和分析目标后，Agent 可以读取目录结构、搜索代码、读取关键文本文件，并
在 `project_root/reports` 下生成 Markdown 分析报告。

当前状态：v0.5，已接入 LangChain Agent runtime、结构化报告、项目画像识别、
安全命令执行工具和 Git 分析工具。暂不支持 LangGraph。

## 当前功能

- 使用 Typer 实现 CLI，并用 Rich 美化输出。
- 使用 `langchain.agents.create_agent` 创建 Agent。
- 支持 OpenAI 或 OpenAI-compatible Chat API。
- 支持不依赖 API Key 的确定性项目画像识别。
- 自动识别 Python / Node / React / Vue / Vite / Next.js。
- 解析 `package.json`、`pyproject.toml`、`requirements.txt`。
- 识别入口文件、脚本命令、包管理器、依赖和关键配置文件。
- 校验本地项目路径。
- 扫描目录结构，并忽略常见依赖、缓存、构建和 IDE 目录。
- 在路径安全限制内读取 UTF-8 文本文件。
- 优先使用 `rg` 搜索代码，没有 `rg` 时回退到 Python 遍历。
- 支持白名单内的安全测试、构建和 Git 查看命令。
- 支持 Git status、diff 和 oneline log 分析。
- 支持基于 Pydantic `AnalysisReport` schema 的结构化分析报告。
- 同时生成 Markdown 和 JSON 报告。
- JSON 报告便于后续 Web UI、回归测试和 Agent 评测。
- 将 Markdown 报告写入 `project_root/reports`。
- 使用 Pydantic 定义结构化报告模型。
- 使用 pytest 覆盖基础工具和 Agent 接入逻辑。

## 安装方式

```bash
python -m pip install -e ".[dev]"
```

需要 Python 3.11 或更高版本。

## 配置方式

复制环境变量示例文件：

```bash
cp .env.example .env
```

必填：

```text
OPENAI_API_KEY=your_api_key_here
```

可选：

```text
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4.1-mini
```

如果使用 DeepSeek 或其他 OpenAI-compatible API，可以通过 `OPENAI_BASE_URL`
配置服务地址。不要提交真实 API Key。

## CLI 使用示例

```bash
repoinsight version
repoinsight scan --path ./some-project
repoinsight profile --path ./some-project
repoinsight profile --path ./some-project --json
repoinsight ask "分析这个项目的技术栈、入口文件和主要模块" --path ./some-project
repoinsight ask "分析这个项目并生成结构化报告" --path ./some-project
repoinsight ask "运行 pytest 并分析失败原因" --path ./some-project
repoinsight ask "查看当前 git diff 并生成代码审查报告" --path ./some-project
repoinsight ask "运行 pnpm build 并分析构建警告" --path ./some-project
```

也可以直接通过模块运行：

```bash
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli profile --path .
python -m repoinsight.cli profile --path . --json
python -m repoinsight.cli ask "Analyze this project architecture" --path .
python -m repoinsight.cli ask "分析这个项目并生成结构化报告" --path .
python -m repoinsight.cli ask "运行 pytest 并分析失败原因" --path .
python -m repoinsight.cli ask "查看当前 git diff 并生成代码审查报告" --path .
python -m repoinsight.cli ask "运行 pnpm build 并分析构建警告" --path .
```

`ask` 命令会校验项目路径、创建 LangChain Agent、允许 Agent 调用仓库分析工具，
并输出报告目录、返回的 Markdown/JSON 报告路径和简短结果摘要。

`profile` 命令不需要 `OPENAI_API_KEY`，不会调用 LLM，不会执行命令，也不会写报告。

## 当前能力

- 可以读取项目目录结构。
- 可以读取所选项目根目录内的 UTF-8 文本文件。
- 可以搜索所选项目根目录内的代码。
- 可以查看 Git status、diff、diff 统计和 oneline log。
- 可以运行白名单内的测试和构建命令。
- 可以分析测试、构建和 Git 输出并生成报告。
- 可以在没有 API Key 的情况下识别项目画像。
- 可以识别入口文件、脚本命令、包管理器、依赖和关键配置文件。
- 可以从同一个结构化 schema 生成 Markdown 和 JSON 报告。
- 可以生成 `reports/*.md` Markdown 报告。
- 不支持任意 shell 命令。
- 不支持安装依赖。
- 暂不支持修改源码文件。

## 安全说明

RepoInsight 的工具只能访问用户传入并校验过的 `project_root` 内文件。Agent 不会
直接接触绝对 `project_root` 参数，而是使用 Python 闭包绑定后的工具。路径守卫会
阻止 `../secret.txt` 这类路径穿越。

Agent 只能通过 `shell=False` 执行明确白名单命令。当前允许：

- `git status`
- `git diff`
- `git diff --stat`
- `git log --oneline`
- `pytest`
- `python -m pytest`
- `npm test`
- `npm run test`
- `npm run build`
- `pnpm test`
- `pnpm run test`
- `pnpm build`
- `pnpm run build`
- `yarn test`
- `yarn build`

危险命令和 shell 语法会被拒绝，包括 `rm`、`del`、`rmdir`、`format`、`curl`、
`wget`、`powershell`、`bash`、`sh`、`cmd`、`chmod`、`chown`、`sudo`、
`git commit`、`git push`、`git reset`、`git clean`，以及 `npm install`、
`pnpm install` 等安装命令。

唯一具备写入能力的是报告工具。`write_markdown_report` 只能在
`project_root/reports` 下写入 `.md` 文件；结构化报告工具会在同一目录下写入成对的
`.md` 和 `.json` 文件。RepoInsight 工具不会修改源码文件。

目录扫描和搜索会忽略 `.git`、`node_modules`、`.venv`、`__pycache__`、`dist`、
`build`、`.next`、`.idea`、`.vscode` 等目录。

项目画像识别只读取有限大小的配置文件，并用有限深度检查入口文件是否存在。它不执行
命令、不调用 LLM、不修改任何文件。

结构化报告来自同一个 `AnalysisReport` 对象。Markdown 给人阅读，JSON 便于后续
Web UI、回归测试和 Agent 评测。

## GitHub 提交前检查

提交到 GitHub 前，请确认 `.env`、本地报告、缓存目录、虚拟环境和生成的索引文件没有被 Git 跟踪。

## Roadmap

- v0.1：项目骨架、CLI、文件工具、搜索工具、报告工具。
- v0.2：接入 LangChain Agent。
- v0.3：加入安全命令执行和 Git 分析工具。
- v0.4：加入 Project Detector 和仓库画像识别。
- v0.5：加入结构化 Markdown + JSON 报告。
- v0.6：加入 LangGraph 工作流。
- v1.0：开源稳定版本。
