# 修复 Notebook 连接远程 Worker 失败

## 适用场景

- 在开发机中使用 Notebook，点击 "Connect to remote worker" 后无反应或跳转到创建页面
- 新建的 Worker 无法在 VSCode Jupyter Notebook 中被识别和使用

## 排查步骤

### 1. 检查 workers.json 配置文件

```bash
cat $HOME/.merlin/notebook/workers.json
```

### 2. 修复配置文件

如果文件不存在或内容为空，执行：

```bash
mlx worker list > $HOME/.merlin/notebook/workers.json
```

`mlx worker list` 的输出需处理成 `workers.json` 要求的格式。

## 注意事项

- `connect to worker` 功能强依赖 `$HOME/.merlin/notebook/workers.json` 文件的正确性
- 直接修改配置文件存在风险，操作前最好备份原文件

## 兆底

- 如果 `mlx worker list` 失败或没有返回可用 Worker，说明用户可能没有创建 Worker，引导用户去 Merlin 平台创建
- 如果填充文件后问题依旧，建议用户重启 VSCode 或开发机后重试
