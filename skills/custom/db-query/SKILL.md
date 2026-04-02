---
name: db-query
description: 连接项目测试数据库，执行 SQL 查询获取数据。当需要查询数据库中的测试数据、验证数据状态、或为接口测试准备入参时使用。
metadata:
  short-description: 查询测试数据库
---

# 数据库查询 Skill

## 适用场景
- 需要从测试数据库中查询数据，用于接口测试（如配合 Bits MCP）
- 验证接口调用后数据库中的数据状态
- 查看表结构、索引等数据库元信息
- 为测试用例准备和查找合适的测试数据

## 前置条件
- 已安装 MySQL CLI 客户端（`/opt/homebrew/opt/mysql-client/bin/mysql` 或系统 `mysql`）
- 项目根目录下存在 `.db-config.local.json` 配置文件，包含数据库连接信息

## 快速执行（一步到位）

**每次会话首次调用时**，读取项目根目录下的 `.db-config.local.json`，提取连接信息，然后直接构建并执行 mysql 命令。

读取配置后，按以下模板拼接命令直接执行（不需要分两步）：

```bash
<mysql_client> -h '<host>' -P <port> -u <user> -p'<password>' <database> -e "<SQL>" --table 2>&1
```

**同一会话内后续调用**：连接参数已知，直接复用，无需再次读取配置文件。

### 示例（使用 default 连接）

```bash
# 读取 .db-config.local.json 获得:
# mysql_client = /opt/homebrew/opt/mysql-client/bin/mysql
# host = 10.x.x.x, port = 3306, user = xxx, password = xxx, database = xxx

# 直接执行:
/opt/homebrew/opt/mysql-client/bin/mysql -h '10.x.x.x' -P 3306 -u xxx -p'xxx' xxx -e "SELECT * FROM table LIMIT 5;" --table 2>&1
```

## 配置文件格式

配置文件路径：项目根目录下的 `.db-config.local.json`（已加入 `.gitignore`）

```json
{
  "mysql_client": "/opt/homebrew/opt/mysql-client/bin/mysql",
  "connections": {
    "default": {
      "host": "10.x.x.x",
      "port": 3306,
      "user": "your_user",
      "password": "your_password",
      "database": "your_database",
      "description": "主库描述"
    },
    "warehouse": {
      "host": "10.x.x.x",
      "port": 3306,
      "user": "your_user",
      "password": "your_password",
      "database": "warehouse_db",
      "description": "数仓库"
    }
  }
}
```

支持配置多个数据库连接，通过 connection name 区分。默认使用 `default`，用户可指定其他连接名。

### 注意：database 字段填实际 MySQL 数据库名
- 公司数据库的 PSM 格式（如 `toutiao.mysql.xxx_write`）**不是**实际的 MySQL 数据库名
- 如果不确定实际库名，先不填 database，连接后执行 `SHOW DATABASES;` 查看

## 命令构建注意事项

- 密码参数 `-p` 和密码之间**没有空格**：`-p'password'`
- **host 可能是 IPv6 地址**，必须用单引号包裹：`-h '2605:340:cd50:...'`
- 使用 `--table` 参数使输出对齐，便于阅读
- 查询大量数据时加上 `LIMIT` 避免输出过多
- 如果密码包含特殊字符，用单引号包裹：`-p'pa$$word'`
- 末尾加 `2>&1` 确保 warning 信息也能被捕获

## 常用查询模式

### 查看数据库和表
```bash
<mysql_cmd> -e "SHOW DATABASES;" --table
<mysql_cmd> -e "SHOW TABLES;" --table
<mysql_cmd> -e "DESC <table_name>;" --table
<mysql_cmd> -e "SHOW CREATE TABLE <table_name>;" --table
```

### 查询数据
```bash
# 基本查询
<mysql_cmd> -e "SELECT * FROM <table> WHERE <condition> LIMIT 10;" --table

# 统计数量
<mysql_cmd> -e "SELECT COUNT(*) FROM <table> WHERE <condition>;" --table
```

### GORM 软删除注意事项
本项目使用 GORM 软删除，表中存在 `delete_time` 字段（部分表可能为 `deleted_at`）。
- **GORM 查询会自动过滤**已软删除的记录（`WHERE delete_time IS NULL`）
- **直接用 SQL 查询时必须手动加上此条件**，否则结果会比代码实际查到的多
- 在验证接口返回与 DB 数据一致性时，务必先 `DESC <table>` 确认是否有软删除字段，然后加上 `AND delete_time IS NULL`（或 `AND deleted_at IS NULL`）
- 这一点在统计 COUNT 时尤其关键，遗漏会导致数量不匹配的误判

### 导出为 JSON（用于接口测试入参）
```bash
<mysql_cmd> -e "SELECT <fields> FROM <table> WHERE <condition> LIMIT 10;" --batch --raw | python3 -c "
import sys, json
lines = sys.stdin.read().strip().split('\n')
headers = lines[0].split('\t')
rows = [dict(zip(headers, line.split('\t'))) for line in lines[1:]]
print(json.dumps(rows, ensure_ascii=False, indent=2))
"
```

## 与 Bits MCP 联动

典型流程：
1. 用 `/db-query` 从数据库查询测试数据（如 partner_id, account_id 等）
2. 将查询到的数据作为 Bits MCP RPC 请求的入参
3. 调用接口后，再用 `/db-query` 验证数据库状态是否符合预期

## 安全提醒
- `.db-config.local.json` 已加入 `.gitignore`，**绝对不要**提交到 Git 仓库
- 仅用于线下测试环境，**不要**配置线上数据库连接
- 只允许执行 SELECT 查询，**禁止执行 INSERT/UPDATE/DELETE**
