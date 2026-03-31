---
name: feishu-cli-bitable
description: >-
  飞书多维表格（Bitable / Base）操作。适用于创建多维表格、管理数据表、字段、记录、视图，
  以及按条件查询结构化业务数据。当用户请求“创建多维表格”、“操作 base”、“查询表记录”、
  “新增/修改 bitable 记录”、“管理字段”、“创建视图”、“批量导入结构化数据”时使用。
  注意它和普通电子表格（Sheets）不是同一种产品；如果用户说的是表格单元格、工作表、xlsx/csv，
  请优先使用 `feishu-cli-toolkit`。任何会修改表结构、批量写入、删除记录、变更高级权限或所有权的操作，
  执行前必须先获得用户明确确认。
user-invocable: true
allowed-tools: Bash, Read
---

# 飞书多维表格（Bitable）

用于管理飞书的 **Bitable / Base** 数据结构，包括：
- Base
- Table
- Field
- Record
- View

## 适用范围

优先用于这些场景：
- 用户要创建结构化数据表
- 用户要按条件查询记录
- 用户要批量导入业务数据
- 用户要维护字段和视图
- 用户明确说的是 bitable / base / 多维表格

这个技能**不负责**：
- 普通电子表格（sheet）读写、单元格区域操作、csv/xlsx 导出导入（请用 `feishu-cli-toolkit`）
- 文档权限管理（请用 `feishu-cli-perm`）
- 搜索飞书资源（请用 `feishu-cli-search`）

## 前置条件

需要可用的 App 凭据。先做状态确认，再进行真实操作。

## 使用原则

1. 先区分用户要的是 **Bitable** 还是 **Sheet**。
2. 先读后写：优先查询现状，再决定是否修改。
3. 任何会改表结构、删记录、批量写入、改高级权限的操作，都要先确认。
4. 涉及真实业务数据时，优先返回“将要修改什么”，确认后再执行。

## 常见只读操作

### 查看 Base 信息

```bash
feishu-cli bitable get <app_token>
```

### 列出数据表

```bash
feishu-cli bitable tables <app_token>
```

### 列出字段

```bash
feishu-cli bitable fields <app_token> <table_id>
```

### 查询记录

```bash
feishu-cli bitable records <app_token> <table_id>
```

可进一步加过滤和排序：
- `--filter ...`
- `--sort ...`
- `--field-names ...`

## 高影响操作

以下操作执行前必须先获得用户明确确认。

### 创建或删除表

```bash
feishu-cli bitable create --name "项目管理"
feishu-cli bitable create-table <app_token> --name "任务表"
feishu-cli bitable delete-table <app_token> <table_id>
```

### 创建、修改、删除字段

```bash
feishu-cli bitable create-field <app_token> <table_id> --field '...'
feishu-cli bitable update-field <app_token> <table_id> <field_id> --field '...'
feishu-cli bitable delete-field <app_token> <table_id> <field_id>
```

### 新增、批量新增、更新、删除记录

```bash
feishu-cli bitable add-record <app_token> <table_id> --fields '{...}'
feishu-cli bitable add-records <app_token> <table_id> --data '[...]'
feishu-cli bitable update-record <app_token> <table_id> <record_id> --fields '{...}'
feishu-cli bitable delete-records <app_token> <table_id> --record-ids "rec1,rec2"
```

### 视图与高级权限变更

视图创建/删除、高级权限、角色、所有权相关操作都属于高影响动作，默认不要直接执行。

## 何时切到别的技能

- 用户说的是“电子表格 / 工作表 / 单元格 / xlsx / csv” → `feishu-cli-toolkit`
- 用户要查飞书里有没有某个表或文档 → `feishu-cli-search`
- 用户要给文档加权限 → `feishu-cli-perm`

## 最小工作流

### 场景：用户说“查一下这个多维表格里的未完成任务”
1. 先确认这是 bitable，不是普通 sheet
2. 查看 tables / fields，确认表和字段名
3. 用 `records --filter ...` 查询
4. 返回结果

### 场景：用户说“帮我批量导入这些记录”
1. 先查看字段结构
2. 告诉用户准备写入哪些字段和多少条记录
3. 获得确认后再执行批量写入

### 场景：用户说“删掉这个字段”
1. 先说明这是破坏性操作
2. 明确确认字段 ID / 名称
3. 获得确认后再执行
