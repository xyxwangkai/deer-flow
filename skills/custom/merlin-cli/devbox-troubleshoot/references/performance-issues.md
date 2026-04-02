# 排查开发机性能问题

## 适用场景

- 开发机卡顿、白屏
- VSCode 连接不上
- SSH 总是断开

## 排查步骤

### 1. 获取开发机信息

使用 `merlin-cli devbox list` 获取目标用户的开发机信息（包括实例 ID）。

### 2. 执行诊断脚本

```bash
bash /workspace/vscode/perf.sh
```

远程执行：
```bash
merlin-cli devbox execute-script --json '{"resource_id": "<resource_id>", "cmd": "bash /workspace/vscode/perf.sh"}'
```

### 3. 分析与处理

- 分析脚本输出，找出资源占用最高的进程
- 向用户报告问题原因，并询问是否可以停止相关进程以临时缓解

## 注意事项

- 停止进程是破坏性操作，必须在执行前得到用户明确确认
- 此技能主要用于诊断，根治问题可能需要用户优化代码或调整开发机规格

## 兆底

- 如果诊断脚本执行失败，检查开发机状态是否为 `running`
- 如果无法定位问题，建议用户检查其运行的应用程序是否存在内存泄漏或死循环
