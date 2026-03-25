# baoyu-post-to-wechat

微信公众号内容发布技能，支持通过API或浏览器自动化发布文章和图文内容到微信公众号。

## 功能特性

- ✅ 支持文章发布（HTML/Markdown格式）
- ✅ 支持图文混排内容发布
- ✅ 支持API方式发布（需要微信公众号开发权限）
- ✅ 支持浏览器自动化发布（使用Playwright）
- ✅ 支持草稿保存和直接发布
- ✅ 支持评论权限设置
- ✅ 支持封面图片上传

## 安装要求

### 系统要求
- Python 3.8+
- Playwright（用于浏览器自动化）
- 微信公众号开发者权限（API方式）

### Python依赖
```bash
pip install playwright requests
playwright install chromium
```

## 快速开始

### 1. 配置API凭证（API方式）
复制配置文件模板并填写你的微信公众号API凭证：

```bash
cp config/api_credentials.example.json config/api_credentials.json
```

编辑 `config/api_credentials.json`：
```json
{
  "app_id": "你的AppID",
  "app_secret": "你的AppSecret",
  "access_token": "你的AccessToken"
}
```

### 2. 配置浏览器设置（浏览器方式）
复制浏览器配置文件模板：

```bash
cp config/browser_config.example.json config/browser_config.json
```

编辑 `config/browser_config.json`：
```json
{
  "chrome_profile_path": "/path/to/your/chrome/profile",
  "headless": false,
  "timeout": 30,
  "wait_time": 2
}
```

### 3. 使用API方式发布文章

```bash
python scripts/api_publish.py \
  --title "文章标题" \
  --content-file "content.md" \
  --format markdown \
  --summary "文章摘要" \
  --draft
```

### 4. 使用浏览器方式发布文章

```bash
python scripts/browser_publish.py \
  --title "文章标题" \
  --content-file "content.html" \
  --format html \
  --wait-time 3
```

## 详细使用说明

### API发布参数

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--title` | 文章标题 | 是 | - |
| `--content` | 文章内容（直接提供） | 与content-file二选一 | - |
| `--content-file` | 文章内容文件路径 | 与content二选一 | - |
| `--type` | 内容类型 | 否 | article |
| `--format` | 内容格式 | 否 | html |
| `--cover` | 封面图片路径 | 否 | - |
| `--summary` | 文章摘要 | 否 | - |
| `--author` | 作者 | 否 | - |
| `--tags` | 标签，逗号分隔 | 否 | - |
| `--draft` | 保存为草稿 | 否 | false |
| `--publish` | 直接发布 | 否 | false |
| `--comments` | 评论设置 | 否 | open |

### 浏览器发布参数

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--title` | 文章标题 | 是 | - |
| `--content` | 文章内容（直接提供） | 与content-file二选一 | - |
| `--content-file` | 文章内容文件路径 | 与content二选一 | - |
| `--format` | 内容格式 | 否 | html |
| `--theme` | 主题名称 | 否 | - |
| `--color` | 主题颜色 | 否 | - |
| `--wait-time` | 等待时间（秒） | 否 | 2 |

## 内容格式支持

### Markdown格式
支持基本的Markdown语法：
- 标题（#,##,###）
- 粗体（**text**）
- 斜体（*text*）
- 换行
- 列表

### HTML格式
支持完整的HTML标签，但需符合微信公众号的HTML规范。

## 注意事项

### 安全注意事项
1. **API凭证保护**：不要将API凭证提交到版本控制系统
2. **内容审核**：发布前检查内容是否符合微信平台规范
3. **频率限制**：注意微信公众号API的调用频率限制
4. **数据备份**：重要内容建议本地备份后再发布

### 浏览器自动化注意事项
1. **登录状态**：确保Chrome用户数据目录中包含有效的微信公众号登录状态
2. **网络环境**：确保网络连接稳定
3. **页面变化**：微信公众号平台界面可能更新，脚本可能需要相应调整

## 错误处理

### 常见错误及解决方案

1. **API认证失败**
   - 检查API凭证是否正确
   - 检查access_token是否过期
   - 检查IP白名单设置

2. **浏览器自动化失败**
   - 检查Chrome是否已安装
   - 检查Playwright是否已正确安装
   - 检查用户数据目录路径是否正确

3. **网络连接问题**
   - 检查网络连接
   - 检查防火墙设置
   - 尝试重试

## 开发指南

### 项目结构
```
baoyu-post-to-wechat/
├── SKILL.md              # 技能定义文件
├── README.md             # 项目文档
├── scripts/              # 脚本目录
│   ├── api_publish.py    # API发布脚本
│   └── browser_publish.py # 浏览器发布脚本
├── config/               # 配置目录
│   ├── api_credentials.example.json
│   └── browser_config.example.json
├── references/           # 参考文档
└── templates/            # 模板文件
```

### 扩展开发
如需扩展功能，可以：
1. 修改现有脚本添加新功能
2. 创建新的脚本文件
3. 更新SKILL.md文件中的触发条件
4. 添加新的配置文件选项

## 许可证

本项目基于MIT许可证开源。

## 支持与反馈

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 查看项目文档
- 参考微信公众号开发文档

---

**重要提示**：使用本技能发布内容前，请确保内容符合微信平台内容规范，避免违规内容导致账号被封禁。