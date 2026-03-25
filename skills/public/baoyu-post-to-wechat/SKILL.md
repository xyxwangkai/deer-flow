---
name: baoyu-post-to-wechat
description: |
  微信公众号内容发布技能。支持通过API或Chrome CDP自动化发布文章（支持HTML、Markdown格式）和图文内容到微信公众号。
  当用户要求发布内容到微信公众号、上传文章、上传图文、发公众号文章时触发。
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - playwright
    emoji: "\U0001F4E3"
    os:
      - darwin
      - linux
---

# 微信公众号内容发布

你是"微信公众号发布助手"。目标是在用户确认后，调用脚本完成内容发布到微信公众号。

## 🔒 技能边界（强制）

**所有发布操作只能通过本项目的脚本完成：**

- **主要执行方式**：通过Python脚本调用微信公众号API或使用Chrome CDP进行浏览器自动化发布。
- **支持格式**：支持HTML、Markdown格式的文章发布，支持图文混排。
- **发布模式**：支持草稿保存和直接发布两种模式。
- **完成即止**：发布流程结束后，直接告知结果，等待用户下一步指令。

---

## 使用场景

### 触发条件
当用户提到以下关键词时触发本技能：
- "发布到微信公众号"
- "发公众号文章"
- "微信公众号发布"
- "公众号图文"
- "微信文章发布"
- "wechat official account post"
- "post to wechat"

### 支持的功能
1. **文章发布**：支持HTML和Markdown格式的文章内容发布
2. **图文发布**：支持图文混排内容发布
3. **草稿管理**：支持保存为草稿或直接发布
4. **元数据设置**：支持设置标题、摘要、封面图、标签等
5. **评论设置**：支持设置评论权限（公开/粉丝/关闭）

---

## 工作流程

### 1. 内容准备阶段
- 确认发布内容（文章/图文）
- 确认内容格式（HTML/Markdown）
- 收集必要的元数据：
  - 标题
  - 摘要
  - 封面图片
  - 标签/分类
  - 评论设置

### 2. 发布方式选择
- **API方式**：使用微信公众号API进行发布（需要API凭证）
- **浏览器方式**：使用Chrome CDP进行浏览器自动化发布（需要登录状态）

### 3. 执行发布
根据选择的方式调用相应的脚本：
- API方式：调用`scripts/api_publish.py`
- 浏览器方式：调用`scripts/browser_publish.py`

### 4. 结果反馈
- 返回发布结果（成功/失败）
- 提供文章链接或草稿ID
- 记录发布日志

---

## 脚本使用说明

### API发布脚本 (`scripts/api_publish.py`)
```bash
python scripts/api_publish.py --title "文章标题" --content "内容" --type article --format markdown
```

参数说明：
- `--title`: 文章标题（必填）
- `--content`: 文章内容（必填）
- `--type`: 内容类型（article/image-text）
- `--format`: 内容格式（html/markdown）
- `--cover`: 封面图片路径
- `--summary`: 文章摘要
- `--tags`: 标签，逗号分隔
- `--draft`: 是否保存为草稿（true/false）
- `--comments`: 评论设置（open/fans-only/closed）

### 浏览器发布脚本 (`scripts/browser_publish.py`)
```bash
python scripts/browser_publish.py --title "文章标题" --content-file "content.md" --method browser
```

参数说明：
- `--title`: 文章标题（必填）
- `--content-file`: 内容文件路径（必填）
- `--method`: 发布方法（browser）
- `--theme`: 主题名称
- `--color`: 主题颜色
- `--wait-time`: 等待时间（秒）

---

## 配置文件

### API凭证配置
创建 `config/api_credentials.json`：
```json
{
  "app_id": "YOUR_APP_ID",
  "app_secret": "YOUR_APP_SECRET",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```

### 浏览器配置
创建 `config/browser_config.json`：
```json
{
  "chrome_profile_path": "/path/to/chrome/profile",
  "headless": false,
  "timeout": 30
}
```

---

## 错误处理

### 常见错误及解决方案
1. **API认证失败**：检查API凭证是否正确，token是否过期
2. **网络连接问题**：检查网络连接，重试发布
3. **内容格式错误**：检查内容是否符合微信公众号要求
4. **浏览器自动化失败**：检查Chrome是否正常运行，profile路径是否正确

### 重试机制
- API发布失败时自动重试3次
- 浏览器发布失败时提示用户手动检查

---

## 安全注意事项

1. **API凭证保护**：不要将API凭证硬编码在脚本中
2. **内容审核**：发布前检查内容是否符合微信平台规范
3. **频率限制**：注意微信公众号API的调用频率限制
4. **数据备份**：重要内容建议本地备份后再发布

---

## 参考资源

- [微信公众号开发文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html)
- [微信公众平台](https://mp.weixin.qq.com/)
- [Playwright文档](https://playwright.dev/python/)

---

**重要提示**：发布前请确保内容符合微信平台内容规范，避免违规内容导致账号被封禁。