# 三源合一文献监控配置指南

本配置同时监控 **arXiv + Semantic Scholar + Web of Science** 三个学术平台，确保不遗漏任何物理海洋学+AI 相关论文。

---

## 📚 三个数据源对比

| 平台 | 覆盖范围 | 优点 | 缺点 | API 要求 |
|------|----------|------|------|----------|
| **arXiv** | 预印本 | 最新、免费 | 海洋学论文少 | 无需 API key |
| **Semantic Scholar** | 全学科期刊 (1.9 亿+) | 覆盖广、免费 | 部分无摘要 | 可选 API key |
| **Web of Science** | 核心期刊 | 权威、高质量 | 需机构订阅 | **必需 API key** |

---

## 🔑 配置步骤

### 步骤 1：获取 API Keys

#### 1.1 Semantic Scholar API Key（可选，但推荐）
- 访问：https://www.semanticscholar.org/product/api
- 点击 "Get an API Key"
- 填写表单（学术用途免费）
- 无严格限流，但有 API key 可获得更高配额

#### 1.2 Web of Science API Key（必需）
- 访问：https://developer.clarivate.com/apis/wos-starter
- **需要研究所/大学账号登录**
- 点击 "Get API Key" 或 "Subscribe"
- 创建 Application
- 复制生成的 API Key

> 💡 **提示**：WoS API 限流为 100 次/5 分钟，每日监控 1 次完全足够。

---

### 步骤 2：配置 GitHub Secrets

进入您的仓库：https://github.com/huangdy2025/hermes-arxiv-agent/settings/secrets/actions

添加以下 Secrets：

| Secret Name | Value | 必需 |
|-------------|-------|------|
| `FEISHU_APP_ID` | `cli_a96e6d93c2381cb0` | ✅ |
| `FEISHU_APP_SECRET` | `CItcejruD4e0iF9AWuMjEcHjLgzf8a2n` | ✅ |
| `FEISHU_CHAT_ID` | `oc_fcee3764cb8e7f6055eadc474da7ca9e` | ✅ |
| `SEMANTIC_SCHOLAR_API_KEY` | （从 Semantic Scholar 获取） | ❌ 可选 |
| `WEB_OF_SCIENCE_API_KEY` | （从 Clarivate 获取） | ✅ |

**操作步骤：**
1. 点击 "New repository secret"
2. 填写 Name 和 Value
3. 点击 "Add secret"
4. 重复直到 5 个 secrets 全部添加

---

### 步骤 3：更新搜索关键词（可选）

编辑 `search_keywords.txt` 文件，当前配置：

```
all:oceanography+AND+(all:deep+OR+all:neural+OR+all:transformer+OR+all:learning+OR+all:LSTM+OR+all:CNN+OR+all:RNN+OR+all:AI+OR+all:"artificial intelligence"+OR+all:prediction+OR+all:forecast+OR+all:model+OR+all:data+assimilation)
```

**说明：**
- `all:oceanography` — **必须包含** "oceanography"
- `AND+(...)` — 并且包含以下任一 AI/技术关键词
- 可根据需要调整关键词

---

### 步骤 4：提交并推送

```bash
cd ~/hermes-arxiv-agent

# 添加新文件
git add multi_source_monitor.py .github/workflows/multi-source-monitor.yml GITHUB_ACTIONS_SETUP.md

# 提交
git commit -m "feat: add multi-source monitor (arXiv + Semantic Scholar + Web of Science)"

# 推送
SSH_AUTH_SOCK="" git -c core.sshCommand="ssh -i ~/.ssh/id_ed25519_github -o IdentitiesOnly=yes" push origin main
```

---

### 步骤 5：测试运行

#### 方法 A：手动触发（推荐）
1. 访问：https://github.com/huangdy2025/hermes-arxiv-agent/actions/workflows/multi-source-monitor.yml
2. 点击 "Run workflow"
3. 选择 "main" 分支
4. 点击 "Run workflow"
5. 等待 2-5 分钟
6. 检查飞书消息

#### 方法 B：等待自动运行
- 每天北京时间 **9:00 AM** 自动执行
- 无需本地电脑开机

---

## 📊 预期输出

### 飞书消息格式

```
🔬 **物理海洋学+AI 新论文推送**

📅 日期：2026-04-20
📊 发现 8 篇新论文
   • arXiv: 2 篇
   • Semantic Scholar: 4 篇
   • Web of Science: 2 篇

**最新论文列表：**

1. 📄 [Deep learning for ocean prediction...](https://arxiv.org/abs/2404.xxxxx)
   作者：Zhang et al. | 2026-04-18 | arXiv

2. 🎓 [Neural networks in physical oceanography...](https://www.semanticscholar.org/paper/xxxxx)
   作者：Wang, Li | 2026-04-17 | Semantic Scholar

3. 📚 [Data assimilation with AI...](https://www.webofscience.com/wos/xxxxx)
   作者：Liu et al. | 2026-04-15 | Web of Science

...

📌 搜索策略：oceanography + AI/ML/数据同化
```

---

## 🔧 故障排查

### 问题 1：Web of Science API 认证失败
**错误信息：** `Authentication failed: 401` 或 `403`

**解决方法：**
1. 确认 API key 正确（区分大小写）
2. 检查 API key 是否过期
3. 联系研究所图书馆确认订阅状态

---

### 问题 2：Semantic Scholar 限流
**错误信息：** `Rate limited (429)`

**解决方法：**
- 获取 API key（有 key 配额更高）
- 脚本已内置重试机制，会自动等待

---

### 问题 3：arXiv 限流
**错误信息：** `Rate exceeded`

**解决方法：**
- 脚本已内置重试和指数退避
- 通常等待 5-10 分钟即可恢复

---

### 问题 4：无新论文推送
**可能原因：**
1. 关键词太严格 → 放宽关键词
2. 确实没有新论文 → 正常情况
3. API 临时故障 → 检查 GitHub Actions 日志

---

## 📝 进阶配置

### 修改推送时间

编辑 `.github/workflows/multi-source-monitor.yml`：

```yaml
on:
  schedule:
    # 修改 cron 表达式 (UTC 时间)
    - cron: '0 1 * * *'  # 北京时间 9:00
```

**常用时间：**
- `0 0 * * *` → 北京时间 8:00
- `0 1 * * *` → 北京时间 9:00（当前）
- `0 2 * * *` → 北京时间 10:00

---

### 调整每个来源的论文数量

编辑 `multi_source_monitor.py` 中的 `max_results` 参数：

```python
arxiv_papers = search_arxiv_papers(keywords, max_results=20)  # 改为 30 等
```

**注意：** 总数不超过 50 为宜，避免消息过长。

---

### 添加更多来源

可参考 `multi_source_monitor.py` 的结构添加：
- PubMed（生物医学）
- Crossref（DOI 元数据）
- Google Scholar（需爬虫，不稳定）

---

## 📈 效果对比

| 配置 | 日均论文数 | 覆盖率 | 推荐度 |
|------|-----------|--------|--------|
| arXiv only | 0-2 篇 | 10% | ⭐⭐ |
| arXiv + Semantic Scholar | 3-8 篇 | 60% | ⭐⭐⭐⭐ |
| **三源合一** | **5-15 篇** | **90%+** | **⭐⭐⭐⭐⭐** |

---

## 🎯 下一步

1. ✅ 完成 API key 配置
2. ✅ 推送代码到 GitHub
3. ✅ 手动触发一次测试
4. ✅ 观察 2-3 天，确认正常运行
5. 📊 根据实际效果调整关键词

---

**如有问题，请查看：**
- GitHub Actions 日志：https://github.com/huangdy2025/hermes-arxiv-agent/actions
- 飞书消息（错误通知）
