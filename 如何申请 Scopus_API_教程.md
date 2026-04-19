# 🔑 Scopus API 手把手申请教程 (2025 最新版)

**完全免费！无需机构账号！5 分钟搞定！**

---

## 📋 申请前准备

- ✅ 一个邮箱（Gmail、QQ 邮箱、研究所邮箱均可）
- ✅ 5 分钟时间
- ✅ 能访问国际网站（无需特殊网络）

---

## 🎯 详细步骤

### 步骤 1：访问 Elsevier Developer Portal

打开浏览器，访问：
```
https://dev.elsevier.com
```

您会看到首页，点击右上角的 **"Log in"** 或 **"Register"**。

> 💡 如果没有 Elsevier 账号，直接点 **"Register"** 注册新账号。

---

### 步骤 2：注册账号（如果没有）

![注册页面](https://www.elsevier.com/__data/assets/image/0004/1073228/registration-form-example.png)

1. 点击 **"Register"**（注册）

2. 填写注册表单：
   - **First Name**: 您的名（如：Dayong）
   - **Last Name**: 您的姓（如：Huang）
   - **Email address**: 您的邮箱（推荐用研究所邮箱或 Gmail）
   - **Password**: 设置密码（至少 8 位，包含大小写字母和数字）
   - **Confirm Password**: 确认密码

3. 勾选同意条款：
   - ✅ I agree to the Terms & Conditions
   - ✅ I agree to the Privacy Policy

4. 点击 **"Create account"** 创建账号

---

### 步骤 3：验证邮箱

注册后，Elsevier 会发送验证邮件到您的邮箱。

1. 打开邮箱，找到来自 Elsevier 的邮件
   - 标题：`Verify your email address | Elsevier`
   - 发件人：Elsevier <noreply@elsevier.com>

2. 点击邮件中的 **"Verify email"** 按钮或链接

3. 验证成功后，页面会提示 "Email verified successfully"

> ⚠️ **如果没收到邮件**：
> - 检查垃圾邮件文件夹
> - 等待 1-2 分钟
> - 在登录页面点击 "Resend verification email"

---

### 步骤 4：登录并创建 API Key

1. 回到 https://dev.elsevier.com
2. 点击右上角 **"Log in"**
3. 输入刚才注册的邮箱和密码
4. 登录成功后，点击右上角的 **"My account"** 或 **"API Keys"**

---

### 步骤 5：申请 API Key

找到并点击 **"Create API Key"** 或 **"Request API Key"** 按钮。

![创建 API Key 页面](https://dev.elsevier.com/images/api-key-form.png)

填写申请表单：

1. **API Key Label**（必填）
   - 输入：`Hermes Paper Monitor`
   - 这是 API Key 的备注名称，随便填，方便自己识别

2. **Website URL**（必填）
   - 输入：`http://example.com`
   - 或者填您的 GitHub 主页：`https://github.com/huangdy2025`
   - **这不是审核项**，只是形式填写

3. **Description**（可选）
   - 输入：`Daily paper monitoring for oceanography research`
   - 简单描述用途

4. **API Product**（选择）
   - 勾选：✅ **Scopus API**
   - 也可以同时勾选 ScienceDirect API（如果需要全文）

5. **使用用途**（重要）
   - 选择：✅ **Non-Commercial/Academic Use**（非商业/学术用途）
   - 这是**免费**的关键！

6. 阅读并勾选同意条款：
   - ✅ I agree to the Terms & Conditions
   - ✅ I confirm this is for non-commercial use

7. 点击 **"Submit"** 或 **"Create API Key"**

---

### 步骤 6：获取 API Key

提交后，您会立即看到生成的 API Key！

```
API Key Created Successfully!

Your API Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**🚨 立即复制并保存！**

复制这个字符串（32 位字母数字组合），保存到：
- 记事本
- 密码管理器
- 手机备忘录

> ⚠️ **重要提示**：
> - API Key **只显示一次**！刷新页面后就看不到了！
> - 如果丢失，需要重新创建一个新的
> - 不要分享给他人

---

### 步骤 7：配置到 GitHub Secrets

1. 打开 GitHub 仓库：
   ```
   https://github.com/huangdy2025/hermes-arxiv-agent/settings/secrets/actions
   ```

2. 点击 **"New repository secret"**

3. 填写：
   - **Name**: `SCOPUS_API_KEY`
   - **Value**: （刚才复制的 32 位 API Key）

4. 点击 **"Add secret"**

✅ 完成！

---

## 📊 API Key 使用限制

| 限制类型 | 数值 | 说明 |
|----------|------|------|
| **请求频率** | 200 次/5 分钟 | 我们的脚本每天只运行 1 次，完全够用 |
| **单次检索** | 最多 2000 条结果 | 我们每次只取 20 条 |
| **每日配额** | 无明确限制 | 合理使用即可 |
| **有效期** | 永久 | 除非违反条款 |

---

## ❓ 常见问题

### Q1: 我没有研究所邮箱，可以用 Gmail/QQ 邮箱吗？
**可以！** Gmail、QQ 邮箱、163 邮箱都可以注册，**不需要机构邮箱**。

### Q2: 我是学生/研究人员，可以用免费 API 吗？
**可以！** 只要是**非商业用途**（学术研究、个人学习），都是免费的。

### Q3: API Key 会过期吗？
**不会**，API Key 永久有效，除非：
- 您主动删除
- 违反使用条款（如商业用途、滥用 API）

### Q4: 我刚才没复制 API Key，页面刷新了怎么办？
没关系！重新申请一个新的：
1. 回到 https://dev.elsevier.com/apikey/manage
2. 删除旧的 Key（如果有）
3. 点击 "Create API Key" 重新生成

### Q5: Scopus API 能获取全文吗？
**不能**。Scopus API 只提供：
- ✅ 标题、摘要、作者
- ✅ 引用次数、期刊信息
- ❌ 不提供全文 PDF

如需全文，需要通过研究所图书馆或 ScienceDirect API（需订阅）。

### Q6: 申请被拒绝了怎么办？
极少数情况下可能被拒（如填写商业用途），解决方法：
1. 重新申请，确保选择 **"Non-Commercial/Academic Use"**
2. Description 写清楚是学术研究用途
3. 如果还是不行，联系 Elsevier 支持：https://service.elsevier.com

---

## 🎯 快速验证 API Key 是否有效

复制以下代码到浏览器控制台（F12 → Console），替换 `YOUR_API_KEY`：

```javascript
fetch('https://api.elsevier.com/content/search/scopus?query=oceanography&count=1', {
  headers: {
    'X-ELS-APIKey': 'YOUR_API_KEY'
  }
})
.then(r => r.json())
.then(d => console.log('有效！找到', d['search-results']?.['opensearch:totalResults']?.['$text'] || 0, '篇论文'))
.catch(e => console.error('无效:', e))
```

如果看到 `有效！找到 XXXX 篇论文`，说明 API Key 配置成功！

---

## 📚 官方资源

- **Scopus API 文档**: https://dev.elsevier.com/sc_apis.html
- **Getting Started Guide (PDF)**: https://supportcontent.elsevier.com/Support%20Hub/DaaS/37062-Scopus_API_Guide_V1_20230907.pdf
- **技术支持**: https://service.elsevier.com/app/contact/supporthub/researchproductsapis

---

## ✅ 检查清单

申请完成后，确认以下几点：

- [ ] 已注册 Elsevier 账号
- [ ] 已验证邮箱
- [ ] 已创建 Scopus API Key
- [ ] **已复制并保存 API Key**（32 位字符串）
- [ ] 已添加到 GitHub Secrets (`SCOPUS_API_KEY`)
- [ ] 准备手动触发 GitHub Actions 测试

---

## 🎉 下一步

完成 Scopus API 配置后：

1. **手动触发测试**：
   ```
   https://github.com/huangdy2025/hermes-arxiv-agent/actions/workflows/multi-source-monitor.yml
   ```

2. **等待飞书消息**（约 2-5 分钟）

3. **查看结果**：应该能看到 8-20 篇新论文！

---

**祝您申请顺利！如有问题随时询问！** 🚀
