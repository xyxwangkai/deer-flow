# 浏览器技能包手动同步命令

以下命令用于将已生成好的浏览器技能包，从输出目录同步到真实技能目录 `/mnt/skills/public`。

## 源目录

```bash
SRC=/mnt/user-data/outputs/browser-skills-package
DST=/mnt/skills/public
```

## 方式一：逐个创建目录并复制文件（最稳妥）

```bash
SRC=/mnt/user-data/outputs/browser-skills-package
DST=/mnt/skills/public

mkdir -p "$DST/agent-browser" \
         "$DST/chrome-devtools-mcp" \
         "$DST/browser-use-cli" \
         "$DST/browser-ops"

cp "$SRC/agent-browser/SKILL.md" "$DST/agent-browser/SKILL.md"
cp "$SRC/agent-browser/USAGE.md" "$DST/agent-browser/USAGE.md"

cp "$SRC/chrome-devtools-mcp/SKILL.md" "$DST/chrome-devtools-mcp/SKILL.md"
cp "$SRC/chrome-devtools-mcp/USAGE.md" "$DST/chrome-devtools-mcp/USAGE.md"

cp "$SRC/browser-use-cli/SKILL.md" "$DST/browser-use-cli/SKILL.md"
cp "$SRC/browser-use-cli/USAGE.md" "$DST/browser-use-cli/USAGE.md"

cp "$SRC/browser-ops/SKILL.md" "$DST/browser-ops/SKILL.md"
cp "$SRC/browser-ops/USAGE.md" "$DST/browser-ops/USAGE.md"
```

## 方式二：直接覆盖整个四个技能目录（更省事）

如果你确认目标目录里这四个技能内容都应以当前产物为准，可以直接执行：

```bash
SRC=/mnt/user-data/outputs/browser-skills-package
DST=/mnt/skills/public

rm -rf "$DST/agent-browser" \
       "$DST/chrome-devtools-mcp" \
       "$DST/browser-use-cli" \
       "$DST/browser-ops"

cp -R "$SRC/agent-browser" "$DST/agent-browser"
cp -R "$SRC/chrome-devtools-mcp" "$DST/chrome-devtools-mcp"
cp -R "$SRC/browser-use-cli" "$DST/browser-use-cli"
cp -R "$SRC/browser-ops" "$DST/browser-ops"
```

## 建议使用顺序

推荐先用稳妥方式：

1. 先执行**方式一**完成同步
2. 用 `ls` 检查目标目录
3. 如需后续反复更新，再考虑用**方式二**覆盖

## 同步后检查命令

```bash
ls -R /mnt/skills/public/agent-browser
ls -R /mnt/skills/public/chrome-devtools-mcp
ls -R /mnt/skills/public/browser-use-cli
ls -R /mnt/skills/public/browser-ops
```

## 可选：快速查看四个技能是否都在

```bash
for d in agent-browser chrome-devtools-mcp browser-use-cli browser-ops; do
  echo "===== $d ====="
  ls -R "/mnt/skills/public/$d"
  echo
done
```

## 当前技能包内容

- `agent-browser/SKILL.md`
- `agent-browser/USAGE.md`
- `chrome-devtools-mcp/SKILL.md`
- `chrome-devtools-mcp/USAGE.md`
- `browser-use-cli/SKILL.md`
- `browser-use-cli/USAGE.md`
- `browser-ops/SKILL.md`
- `browser-ops/USAGE.md`

## 说明

- `playwright-cli` 为现有技能，本次未改动其目录内容
- 本次新增/整理的是另外四个技能
- `browser-ops` 已包含增强后的路由说明与降级矩阵
