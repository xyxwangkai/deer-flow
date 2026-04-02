# Terminal-Worker 映射管理

映射存储在 `~/.merlin/devbox/worker_state.json`。

## State 文件格式

```json
{
  "mappings": {
    "<terminal_id>": {
      "worker_id": "<worker_id>",
      "created_at": "<ISO8601_timestamp>",
      "gpu_type": "<gpu_type>",
      "gpu_count": 1,
      "cpu": 32,
      "memory": 128,
      "command": "<original_launch_command>"
    }
  }
}
```

## 保存映射

在 worker launch 后记录 terminal_id → worker_id 映射：

```bash
mkdir -p ~/.merlin/devbox
python3 -c "
import json, os
from datetime import datetime

state_file = os.path.expanduser('~/.merlin/devbox/worker_state.json')
state = json.load(open(state_file)) if os.path.exists(state_file) else {'mappings': {}}

state['mappings']['<TERMINAL_ID>'] = {
    'worker_id': '<WORKER_ID>',
    'created_at': datetime.now().isoformat(),
    'gpu_type': '<GPU_TYPE>',
    'gpu_count': <GPU_COUNT>,
    'cpu': <CPU>,
    'memory': <MEMORY>,
    'command': '<COMMAND>'
}

json.dump(state, open(state_file, 'w'), indent=2)
"
```

## 查询映射

```bash
python3 -c "
import json, os
state_file = os.path.expanduser('~/.merlin/devbox/worker_state.json')
if os.path.exists(state_file):
    state = json.load(open(state_file))
    print(json.dumps(state, indent=2))
"
```

## 删除映射

```bash
python3 -c "
import json, os
state_file = os.path.expanduser('~/.merlin/devbox/worker_state.json')
state = json.load(open(state_file))
state['mappings'].pop('<TERMINAL_ID>', None)
json.dump(state, open(state_file, 'w'), indent=2)
"
```

## 验证终端可用性

使用已记录 Worker 前，必须验证终端是否仍然可用：

```bash
python3 -c "
import json, os, sys
state_file = os.path.expanduser('~/.merlin/devbox/worker_state.json')
if not os.path.exists(state_file):
    print('NO_STATE_FILE'); sys.exit(0)
state = json.load(open(state_file))
available_terminals = sys.argv[1].split(',') if len(sys.argv) > 1 else []
valid, stale = [], []
for tid, info in state.get('mappings', {}).items():
    (valid if tid in available_terminals else stale).append({'terminal_id': tid, **info})
print(json.dumps({'valid': valid, 'stale': stale}, indent=2))
" "<AVAILABLE_TERMINAL_IDS>"
```

## 清理过期映射

```bash
python3 -c "
import json, os, sys
state_file = os.path.expanduser('~/.merlin/devbox/worker_state.json')
state = json.load(open(state_file))
available_terminals = sys.argv[1].split(',') if len(sys.argv) > 1 else []
removed = [tid for tid in list(state.get('mappings', {}).keys()) if tid not in available_terminals]
for tid in removed: state['mappings'].pop(tid)
json.dump(state, open(state_file, 'w'), indent=2)
print(f'Removed stale mappings: {removed}')
" "<AVAILABLE_TERMINAL_IDS>"
```

## 管理规则

- **On worker launch**：创建映射，同时清理过期映射
- **On worker kill**：删除映射
- **On query**：读取 state 文件返回 worker 信息
- 永远不要假设已记录的终端仍然可用，必须与系统 `<available_terminal>` 交叉验证
- 如果没有有效 GPU 终端，提示用户创建新 Worker
