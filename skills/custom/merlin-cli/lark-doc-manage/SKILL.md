---
name: lark-doc-manage
description: 飞书文档管理技能，支持创建、编辑、获取飞书文档，以及获取用户 Open ID 用于 @ 提及。
---

# 飞书文档管理 (Lark Doc Management)

## 摘要

本技能提供了一组脚本，用于管理飞书云文档，包括：
- **创建文档**：将本地 Markdown 文件发布为新的飞书文档
- **编辑文档**：更新现有飞书文档内容（支持多种更新模式）
- **获取文档**：将飞书文档内容导出为本地 Markdown 文件
- **用户查询**：获取用户 Open ID 用于在文档中 @ 提及

## 飞书文档 URL 格式

飞书文档支持以下 URL 格式：
- `https://bytedance.larkoffice.com/docx/xxxxxxxxxx`
- `https://bytedance.region.larkoffice.com/docx/xxxxxxxxxx`

其中：
- `region` 为可选的区域标识（如 `sg`、`us` 等）
- `docx` 为文档类型标识
- `xxxxxxxxxx` 为文档 ID（如 `doxcnxxxxxxxxxx`）

脚本支持直接传入完整 URL 或文档 ID。

## 适用场景

- 用户在本地编写了 Markdown 文档，希望快速发布到飞书
- 需要自动化地将生成的报告或文档同步到飞书
- 希望对现有的飞书文档内容进行覆盖更新或局部修改
- 需要将飞书文档内容导出到本地进行编辑或备份
- 需要在文档中 @ 提及特定用户

## 前置条件

- 能够访问本地的 Markdown 文件。
- 需要先通过 `merlin-cli login` 登录以获取访问权限。

## Markdown 语法参考

创建和编辑 Markdown 时，可以使用飞书支持的高级语法（如高亮块、分栏、表格、Mermaid 图表等）。
详细语法说明请参考：[references/syntax.md](references/syntax.md)

## 包含的脚本

### 1. 创建文档 (create_doc.py)

根据标题和 Markdown 文件创建新的飞书文档。

- **脚本路径**: `scripts/create_doc.py`
- **参数**:
  - `title`: 文档标题
  - `markdown_file`: 本地 Markdown 文件路径
- **用法示例**:
  ```bash
  python3 scripts/create_doc.py "My Doc Title" ./docs/readme.md
  ```

### 2. 编辑文档 (edit_doc.py)

根据文档 ID 和 Markdown 文件更新飞书文档内容，支持多种更新模式。

- **脚本路径**: `scripts/edit_doc.py`
- **参数**:
  - `doc_id`: 飞书文档 ID 或 URL
  - `markdown_file`: 本地 Markdown 文件路径
  - `--mode`: 更新模式 (默认: overwrite)
    - `overwrite`: 覆盖全文
    - `append`: 追加到文末
    - `replace_range`: 定位替换（需配合 selection 参数）
    - `replace_all`: 全文替换
    - `insert_before`: 插入到定位内容之前
    - `insert_after`: 插入到定位内容之后
    - `delete_range`: 删除定位内容
  - `--new_title`: 新的文档标题（可选）
  - `--selection_by_title`: 按标题定位章节 (例如 "## 章节标题")
  - `--selection_with_ellipsis`: 按内容定位 (例如 "开头...结尾")
- **用法示例**:
  ```bash
  # 覆盖更新
  python3 scripts/edit_doc.py "doxcnxxxxxxxxxx" ./docs/update.md

  # 追加内容
  python3 scripts/edit_doc.py "doxcnxxxxxxxxxx" ./docs/append.md --mode append

  # 替换特定章节
  python3 scripts/edit_doc.py "doxcnxxxxxxxxxx" ./docs/section.md --mode replace_range --selection_by_title "## 目标"
  ```

### 3. 获取文档 (fetch_doc.py)

获取飞书文档内容并保存为本地 Markdown 文件。

- **脚本路径**: `scripts/fetch_doc.py`
- **参数**:
  - `doc_id`: 飞书文档 ID 或 URL
  - `output_path`: 保存 Markdown 文件的路径
- **注意**: 该工具直接将获取的 Markdown 内容写入指定文件，不需要 `limit` 或 `offset` 参数。
- **用法示例**:
  ```bash
  python3 scripts/fetch_doc.py "doxcnxxxxxxxxxx" ./docs/fetched.md
  ```

### 4. 获取用户 Open ID (get_user_open_id.py)

根据用户邮箱前缀获取飞书用户的 Open ID，用于在文档中 @ 用户。

- **脚本路径**: `scripts/get_user_open_id.py`
- **参数**:
  - `email_prefix`: 邮箱前缀或完整邮箱地址
- **功能说明**:
  - 如果只提供邮箱前缀（如 `xiawei.690`），会自动补全为 `xiawei.690@bytedance.com`
  - 返回用户的 `open_id`，可用于在飞书文档中生成 `<mention-user id="ou_xxx" />` 格式的用户提及
- **用法示例**:
  ```bash
  # 使用邮箱前缀
  python3 scripts/get_user_open_id.py xiawei.690
  
  # 使用完整邮箱
  python3 scripts/get_user_open_id.py xiawei.690@bytedance.com
  ```

## 约束与注意事项

- 脚本通过 `curl` 调用 MCP 接口，确保网络连通性。
- 创建文档时，会自动设置为公开读写权限（参考 `create_lark_doc` 实现）。
- 编辑文档会覆盖原有内容。
- 获取用户的open_id时，请求的mcp url不同
