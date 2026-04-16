# hermes-arxiv-agent

一个基于 Hermes 的 agent skill：每天自动从 arXiv 抓取论文，用 AI 生成中文摘要和作者单位，并支持两种使用方式：本地/飞书模式，以及可选的 GitHub Pages 静态网站发布模式。

## 使用模式

这个项目面向两类用户：

- 本地/飞书模式（默认）
  - 只需要本地仓库、Excel、PDF 和 Hermes 定时任务
  - 每天抓取论文并推送到你自己的飞书
  - 不要求 fork 项目，也不要求 GitHub 写权限
- GitHub Pages 模式（可选）
  - 适合还想公开部署静态网站的人
  - 必须先 fork 项目到你自己的 GitHub 仓库
  - 定时任务会在补全完成后把 `viewer/papers_data.json` 推到你自己的 fork，再触发你自己的 GitHub Pages

## Hermes 对话安装

推荐只使用下面两条固定安装话术，不要临时自由发挥。

### 1. 本地/飞书模式

```text
请从该地址 https://github.com/genggng/hermes-arxiv-agent/blob/main/AGENT_SKILL.md 安装 skill，并按本地/飞书模式部署。不要配置 GitHub Pages 发布。
```

### 2. GitHub Pages 模式

先 fork 本项目到你自己的 GitHub 仓库，然后把下面的占位符替换成你自己的 fork 地址：

```text
请从该地址 https://github.com/<your-github-id>/hermes-arxiv-agent/blob/main/AGENT_SKILL.md 安装 skill，并按 GitHub Pages publishing 模式部署。请使用当前 fork 仓库作为发布仓库，不要使用上游仓库作为推送目标。
```

Hermes 会按对应模式自动完成：

- 克隆仓库
- 安装依赖
- 生成对应模式的定时任务 prompt
- 创建定时任务

如果你启用 GitHub Pages 模式，推荐让仓库 `origin` 使用 SSH：

```text
git@github.com:<your-github-id>/hermes-arxiv-agent.git
```

这样每日自动发布 GitHub Pages 时不会依赖 HTTPS token 或图形化凭证管理器。

## 效果展示

### 飞书推送

![Feishu Push](images/feishu.png)

每天自动推送论文日报，包含标题、作者、单位、PDF 链接和中文摘要。

### Web 阅读网站

![Web Viewer](images/web.png)

本地部署后可在浏览器中按日期筛选、关键词检索，并查看论文摘要与收藏结果。

## 功能

- 每天按关键词监控 arXiv 新论文
- 自动下载 PDF，维护本地 Excel 记录
- 由 Hermes/LLM 补全作者单位和中文摘要
- 自动推送飞书日报
- 提供静态阅读网站，支持本地运行或 GitHub Pages 发布
- 以 Hermes skill 的形式完成部署和日常运行

## Hermes 安装

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc
hermes
```

飞书配置：

```bash
hermes gateway setup
```

GitHub 推送认证建议使用 SSH key。如果你启用了 GitHub Pages 模式，且当前仓库 remote 还是 HTTPS，可以切换为：

```bash
git remote set-url origin git@github.com:<your-github-id>/hermes-arxiv-agent.git
```

## 定时任务说明

定时任务相关逻辑以 [AGENT_SKILL.md](AGENT_SKILL.md) 和 prompt 模板为准。

不推荐手工复制 prompt 或手工改路径，正确做法是让 Hermes 在部署时自动完成。

现在有两种不同的定时任务模板：

- 本地/飞书模式：使用 [cronjob_prompt.txt](cronjob_prompt.txt)
- GitHub Pages 模式：使用 [cronjob_prompt.pages.txt](cronjob_prompt.pages.txt)

`prepare_deploy.sh` 会根据部署模式生成对应的 `cronjob_prompt.generated.txt`。

如果你已经有可用的本地仓库，只想刷新 cron prompt 和定时任务，不要删仓库重装。

可以在 Hermes 对话里直接说：

```text
请使用当前仓库里的 UPDATE_CRON_SKILL.md，只更新 hermes-arxiv-agent 的定时任务。不要重新克隆仓库，不要重装依赖。请基于当前本地仓库运行 prepare_deploy.sh，读取最新 cronjob_prompt.generated.txt，并将现有 cron 更新到最新版本；如果不能直接编辑，就删除旧任务后重建一个新的同名任务。
```

这个流程会复用当前本地仓库和现有数据，只更新定时任务配置，适合在仓库逻辑变更后同步 cron。

如果现有仓库最早是用 HTTPS clone 的，且你启用了 GitHub Pages 模式，也建议在更新 cron 前把 `origin` 改成你自己 fork 的 SSH 地址，避免后续定时发布时出现凭证问题。

## 安装流程

### 1. 本地/飞书模式（默认）

适合只想本地使用和推送自己飞书的人。

在 Hermes 对话中直接说固定安装话术：

```text
请从该地址 https://github.com/genggng/hermes-arxiv-agent/blob/main/AGENT_SKILL.md 安装 skill，并按本地/飞书模式部署。不要配置 GitHub Pages 发布。
```

这个模式下：

- 可以直接使用上游公开仓库
- 不要求 fork
- `prepare_deploy.sh` 默认生成本地模式 cron prompt
- 定时任务不会执行 `bash scripts/publish_viewer.sh`

### 2. GitHub Pages 模式（可选）

适合还想公开部署静态网站的人。

先 fork 本项目到你自己的 GitHub 账号，然后使用你自己 fork 仓库里的固定安装话术：

```text
请从该地址 https://github.com/<your-github-id>/hermes-arxiv-agent/blob/main/AGENT_SKILL.md 安装 skill，并按 GitHub Pages publishing 模式部署。请使用当前 fork 仓库作为发布仓库，不要使用上游仓库作为推送目标。
```

这个模式下：

- 必须先 fork 项目
- `origin` 应该指向你自己的 fork，而不是上游仓库
- 推荐 `origin` 使用 SSH
- `prepare_deploy.sh` 会以 `DEPLOY_MODE=pages` 运行
- 定时任务会执行 `bash scripts/publish_viewer.sh`

## 关键词默认配置

默认监控方向是 LLM 量化相关论文。

如需修改监控方向，编辑 [search_keywords.txt](search_keywords.txt) 即可。

## 本地阅读网站

启动方式：

```bash
cd viewer
python3 run_viewer.py
```

浏览器访问：

```text
http://localhost:8765
```

支持：

- 日期筛选
- 关键词全文检索
- 收藏（浏览器本地保存）
- Abstract 展开查看

## GitHub Pages

仓库已支持用 GitHub Actions 发布 `viewer/` 目录到 GitHub Pages。

只有在 GitHub Pages 模式下，才应该启用这条发布链路。

首次启用时需要在 GitHub 仓库设置中将 Pages 的 source 切到 `GitHub Actions`。

日常更新流程：

```bash
cd /path/to/hermes-arxiv-agent
DEPLOY_MODE=pages bash prepare_deploy.sh
python3 viewer/build_data.py
bash scripts/publish_viewer.sh
```

说明：

- `viewer/papers_data.json` 会随提交推送到 GitHub
- push 到 `main` 后会触发 `.github/workflows/pages.yml`
- 推送目标应当是你自己 fork 的仓库
- 公开站点的收藏功能使用浏览器 `localStorage`，不再依赖服务器端 `favorites.json`
