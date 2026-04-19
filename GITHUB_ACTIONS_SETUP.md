# GitHub Actions 配置说明

## 飞书凭证配置

您需要在 GitHub 仓库中配置以下 Secrets：

### 1. 进入仓库设置
1. 打开 https://github.com/huangdy2025/hermes-arxiv-agent
2. 点击 **Settings**（设置）
3. 左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**

### 2. 添加以下 3 个 Secrets

| Secret 名称 | 值 | 说明 |
|-----------|-----|------|
| `FEISHU_APP_ID` | `cli_a96e6d93c2381cb0` | 飞书应用 ID |
| `FEISHU_APP_SECRET` | `CItcej...8a2n` | 飞书应用密钥（完整密钥） |
| `FEISHU_CHAT_ID` | `oc_fcee3764cb8e7f6055eadc474da7ca9e` | 飞书聊天 ID |

### 3. 获取完整飞书凭证

#### FEISHU_APP_SECRET
您之前配置的是缩写形式 `CItcej...8a2n`，需要完整的密钥：
1. 打开飞书开发者后台：https://open.feishu.cn/app
2. 找到您的应用
3. 查看 **App Secret**（如果看不到，可能需要重新生成）

#### FEISHU_CHAT_ID
已经知道是：`oc_fcee3764cb8e7f6055eadc474da7ca9e`

---

## 工作流程说明

### 定时执行
- **时间**：每天北京时间 9:00 AM（UTC 1:00 AM）
- **触发**：自动执行 + 手动触发（workflow_dispatch）

### 执行流程
1. 搜索 arXiv 上的新论文（关键词：海洋学 + AI）
2. 查重（使用 crawled_ids.txt）
3. 如果有新论文：
   - 构建 Markdown 格式消息
   - 发送到飞书
   - 更新 crawled_ids.txt
4. 提交更改到仓库

### 推送消息格式
```
🔬 物理海洋学+AI 新论文推送

📅 日期：2026-04-20
📊 发现 X 篇新论文

最新论文列表：
1. [论文标题](arxiv 链接)
   作者：Author1, Author2, et al.

...

📌 搜索关键词：海洋学 (ocean/oceanography) + AI
```

---

## 手动测试

您可以在 GitHub 上手动触发工作流：
1. 进入仓库 Actions 标签
2. 选择 "Daily ArXiv Paper Monitor" 工作流
3. 点击 "Run workflow"
4. 选择分支（main）
5. 点击绿色按钮

---

## 注意事项

1. **arXiv API 限流**：最多 20 篇/次，避免触发限流
2. **GitHub Actions 免费额度**：足够每天运行一次
3. **无需本地电脑开机**：云端自动执行
