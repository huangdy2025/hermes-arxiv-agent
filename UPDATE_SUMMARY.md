# GitHub Actions 多源论文监控更新

## 📋 更新内容

### 1. 删除基础版 Workflow
- ✅ 已删除 `.github/workflows/daily-monitor.yml`
- 避免与多源版重复运行

### 2. 增强多源版监控脚本 (`multi_source_monitor.py`)

#### 新增功能
- **Excel 记录生成**: 自动创建/更新 `papers_record.xlsx`
  - 包含所有论文字段：arxiv_id, title, authors, affiliations, published_date, categories, abstract, summary_cn, pdf_filename, crawled_date, notes, source, url
  - 自动设置表头样式和列宽
  
- **Viewer JSON 导出**: 自动生成 `viewer/papers_data.json`
  - 从 Excel 读取数据并转换为 GitHub Pages 所需格式
  - 支持去重和质量排序（优先保留有中文总结、信息更完整的记录）

#### 新增函数
```python
load_or_create_excel()      # 加载或创建 Excel 文件
append_to_excel(wb, paper)  # 添加论文到 Excel
save_excel(wb)              # 保存 Excel
export_viewer_json_from_excel()  # 导出 Viewer JSON
```

### 3. 更新 GitHub Actions Workflow

#### 修改内容 (`.github/workflows/multi-source-monitor.yml`)
- **权限提升**: `contents: write`, `pages: write`, `id-token: write`
- **移除**: Semantic Scholar API key（已不可用）
- **新增**: Commit & Push 步骤
  - 自动提交 `papers_record.xlsx` 和 `viewer/papers_data.json`
  - 触发 GitHub Pages 自动部署

---

## 🔄 执行流程

```
GitHub Actions (每天 9:00 AM UTC+8)
    │
    ├── 1. 搜索论文 (arXiv + Scopus)
    │
    ├── 2. 去重查重
    │
    ├── 3. 发送飞书消息
    │
    ├── 4. 更新 papers_record.xlsx ← 新增
    │
    ├── 5. 导出 viewer/papers_data.json ← 新增
    │
    ├── 6. Git commit & push ← 新增
    │
    └── 7. 触发 GitHub Pages 部署 ← 自动
```

---

## 📁 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `.github/workflows/daily-monitor.yml` | ❌ 删除 | 基础版 workflow |
| `.github/workflows/multi-source-monitor.yml` | ✏️ 修改 | 添加 commit/push 步骤 |
| `multi_source_monitor.py` | ✏️ 修改 | 添加 Excel 和 Viewer JSON 功能 |

---

## ✅ 验证步骤

1. **语法检查**: `python3 -m py_compile multi_source_monitor.py` ✅
2. **Git 状态**: 确认文件已修改
3. **手动测试**: 
   ```bash
   cd ~/hermes-arxiv-agent
   git add -A
   git commit -m "feat: multi-source monitor with Excel and Pages support"
   git push
   ```

---

## 🌐 GitHub Pages 访问

部署完成后，论文列表网站将在：
```
https://huangdy2025.github.io/hermes-arxiv-agent/
```

---

## 📝 注意事项

1. **API Keys**: 确保 GitHub Secrets 中已配置：
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
   - `FEISHU_CHAT_ID`
   - `SCOPUS_API_KEY`

2. **首次运行**: 首次运行时会创建新的 `papers_record.xlsx`，可能需要几分钟

3. **Pages 部署**: 第一次 commit 后，GitHub Pages 可能需要 5-10 分钟完成初始部署

4. **数据来源**: 当前仅使用 arXiv + Scopus（Semantic Scholar 个人 API 已不可用）
