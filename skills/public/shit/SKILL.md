---
name: shit
description: Safely archive, disable, or permanently delete an existing skill, and clean related references from the workspace. Use whenever the user wants to 删除某个技能、下线一个技能、归档技能、禁用技能、清理重复技能、remove a skill, retire a skill, disable a skill, archive an old skill, or simplify an overloaded skill workspace. Prefer this skill even when the user does not explicitly say “skill cleanup” but the intent is clearly to retire or remove existing capabilities.
---

# shit

`shit` is a context cleanup and skill retirement meta-skill.

Its purpose is to safely remove capability clutter from the agent workspace. Instead of treating deletion as a raw filesystem operation, this skill turns skill retirement into a controlled workflow with resolution, inspection, confirmation, execution, and reporting.

一句话：吃多了要拉出来。

## What this skill does

Use this skill to:
- archive an outdated skill for later recovery
- disable a skill without deleting source files
- permanently delete a skill after explicit confirmation
- clean references to the retired skill from indexes, docs, or examples
- produce a retirement report describing exactly what changed

## When to use

Use this skill when the user wants to:
- 删除某个技能
- 下线某个技能
- 归档某个技能
- 禁用某个技能
- 清理重复技能
- 清理实验失败的技能
- 精简技能工作区
- remove / retire / disable / archive an existing skill

If the user gives only a skill name and the exact target is not unique, resolve candidates first and ask for clarification.

## Operation modes

### 1. archive
Move the skill directory into an archive area with a timestamp suffix.

Choose this when:
- the user wants safe cleanup
- the skill may be needed later
- reversibility matters more than space saving

This is the default recommendation.

### 2. disable
Keep the skill files, but deactivate it from active discovery or routing.

Choose this when:
- the skill should stop triggering
- the user wants a reversible off switch
- deleting is too risky

Common disable strategies:
- rename `SKILL.md` to `SKILL.md.disabled`
- add `disabled: true` metadata if supported
- move the skill under a `_disabled/` namespace
- remove it from an active registry while preserving files

### 3. delete
Permanently remove the skill directory.

Choose this only when:
- the user explicitly requests permanent deletion
- the target skill path is resolved exactly
- backup or archive policy is clear
- explicit confirmation has been obtained

## Safety rules

1. Never guess which skill to delete.
2. Never delete a skill on a fuzzy name match.
3. Always resolve the exact path before action.
4. Prefer `archive` over `delete` by default.
5. For `delete`, require explicit confirmation.
6. Before destructive deletion, validate the target path is inside an allowed skills root.
7. Refuse any path traversal or suspicious path like `/`, `..`, home root, or broad parent directories.
8. Inspect references before cleanup when possible.
9. Report exactly what was moved, disabled, deleted, or updated.
10. If cleanup is partial, say so clearly.

## Required inputs

Collect or infer these inputs before execution:
- target skill name or path
- requested mode: `archive`, `disable`, or `delete`
- whether backup is required
- whether reference cleanup is required
- whether this is a dry run

## Standard workflow

### Step 1: Resolve target
- find the candidate skill directory
- validate that it exists
- normalize and display the exact resolved path
- if multiple candidates exist, ask the user to choose

### Step 2: Inspect dependencies
Check whether the skill is referenced by:
- central skill list or registry
- router descriptions
- README or docs
- examples and test prompts
- sibling skill references

### Step 3: Confirm high-risk actions
For `delete`, present:
- skill name
- exact path
- mode
- backup behavior
- reference cleanup behavior

Require a confirmation phrase before executing.

Recommended confirmation text:
`CONFIRM DELETE <skill_name>`

### Step 4: Execute selected mode

#### archive
- create archive directory if needed
- move the skill to archive with timestamp
- preserve contents and structure

#### disable
- apply the selected disable strategy
- keep source files intact
- mark the skill as inactive

#### delete
- optionally archive first as backup
- remove the skill directory
- clean dangling references if requested

### Step 5: Return a retirement report
Always report:
- target skill
- resolved path
- mode
- whether backup was created
- whether references were cleaned
- exact files changed
- rollback advice

## Output format

Use this structure in the final response:

- Target skill:
- Resolved path:
- Operation mode:
- Dry run:
- Backup created:
- References cleaned:
- Result:
- Rollback advice:

## Behavioral expectations

- Be conservative by default.
- If the user asks vaguely to “删掉这个”, resolve the target first.
- If the request mixes multiple actions, split them clearly.
- If the skill cannot safely confirm references, still perform the main operation only if safe, and report the limitation.

## Example requests

- `/shit eat`
- `/shit eat --mode archive`
- `/shit /mnt/skills/public/eat --mode disable`
- `/shit my-old-skill --mode delete --backup`
- `帮我下线这个技能`
- `删除重复的 skill，但先给我 dry-run`

## Non-goals

This skill should not:
- silently delete multiple skills
- delete arbitrary non-skill directories
- remove unrelated docs or code without confirmation
- claim a cleanup succeeded if parts were skipped

## Allowed roots and environment notes

This skill should only operate inside explicitly allowlisted skill roots, such as:
- `/mnt/skills`
- `/mnt/user-data/workspace`
- `/opt/tiger/deer-flow/skills` when operating on the live DeerFlow skills tree

Default live-ready behavior:
- if target is under `/mnt/skills`, archive to `/mnt/skills/_archive`
- if target is under `/opt/tiger/deer-flow/skills`, archive to `/opt/tiger/deer-flow/skills/_archive`
- if target is under live skills, mark environment as `live` in the report
- if `--cleanup-refs` is set, produce `reference_hits` and `patch_plan` even when automatic edits are skipped

Even if a path is allowlisted, real execution can still fail due to runtime filesystem permissions. In that case, return a clear failure report instead of claiming success.

## Implementation note

If deterministic execution is needed, use `scripts/retire_skill.py` for path validation, dry-run planning, environment-aware archive root selection, reference scan planning, archive/delete execution, and report generation.
