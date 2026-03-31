# EXTEND

This file contains implementation guidance, safety policy, and execution details for the `shit` meta-skill.

## Design philosophy

`shit` is not a raw delete command. It is a retirement workflow.

The goal is to reduce skill sprawl without introducing hidden damage. In practice, most user intent falls into one of three buckets:
- reversible cleanup (`archive`)
- temporary retirement (`disable`)
- final removal (`delete`)

Default to the least surprising reversible option.

## Supported modes

### archive
Recommended archive root:
- `/mnt/skills/_archive/` for workspace/global skills
- `/opt/tiger/deer-flow/skills/_archive/` for live DeerFlow skills
- or a project-local archive directory if the workspace is not using the global skills root

Archive naming convention:
- `{skill_name}_{YYYYMMDD_HHMMSS}`
- optional suffix: `{skill_name}_{YYYYMMDD_HHMMSS}_{reason}`

Behavior:
- preserve all files
- move rather than copy if the original should disappear from active use
- use copy+delete only when move is unsafe or not possible

### disable
Potential disable implementations:
1. rename `SKILL.md` to `SKILL.md.disabled`
2. add frontmatter flag such as `disabled: true`
3. move the entire skill directory into `_disabled/`
4. remove the skill from an index while keeping the folder in place

Preferred order:
- if the runtime supports a disabled metadata flag, use it
- otherwise rename or relocate in a reversible way

### delete
Deletion is the highest-risk mode.

Allow delete only when all of the following are true:
- the target path resolves to a concrete skill directory
- the path is inside an allowlisted root
- the user explicitly chose `delete`
- the agent obtained explicit confirmation
- backup policy is clear

Recommended confirmation sentence:
`Confirm permanent deletion of skill <name> at <path>.`

## Path validation policy

The script or workflow must reject:
- `/`
- `/mnt`
- `/mnt/skills`
- broad namespace roots like `/mnt/skills/public`
- `..` traversal
- symlink escapes outside the skills root
- non-directory targets unless explicitly supported

Recommended allowlisted roots:
- `/mnt/skills`
- `/mnt/user-data/workspace`
- `/opt/tiger/deer-flow/skills` for live DeerFlow skill retirement after explicit user approval
- additional user-approved skill roots

## Reference cleanup

Before or after retirement, search references in:
- skill registry files
- `available_skills`-like declarations
- README files
- example scripts
- evaluation files
- internal docs mentioning the target skill

Reference cleanup actions:
- remove exact registry entries
- update links if archive paths are published
- leave a note when an automatic cleanup is unsafe

If automatic cleanup is unreliable, produce a list of files needing manual review.

## Dry-run behavior

`dry-run` should be supported whenever possible.

A dry-run should report:
- resolved target
- selected mode
- backup path to be created
- files or directories to move/delete
- candidate references to clean
- blockers that would stop execution

Dry-run must not modify the filesystem.

## Rollback guidance

### archive rollback
Move the archived directory back to its original location.

### disable rollback
Restore the original filename, metadata, or registry entry.

### delete rollback
Restore from the backup archive if one exists.

If no backup exists, say clearly that rollback is not possible.

## Suggested CLI contract

```bash
/shit <skill_name>
/shit <skill_name> --mode archive
/shit <skill_name> --mode disable
/shit <skill_name> --mode delete --backup
/shit <skill_name> --mode delete --dry-run
/shit /mnt/skills/custom/foo --mode archive
```

## Suggested execution contract

Inputs:
- `target`: skill name or path
- `mode`: `archive|disable|delete`
- `backup`: boolean
- `cleanup_refs`: boolean
- `dry_run`: boolean
- `confirm`: boolean

Outputs:
- resolved path
- mode
- actions performed
- backup path
- cleaned references
- warnings

## Suggested Python API

```python
def retire_skill(
    target: str,
    mode: str = "archive",
    backup: bool = True,
    cleanup_refs: bool = True,
    dry_run: bool = False,
    confirm: bool = False,
) -> dict:
    ...
```

## Recommended report schema

```json
{
  "target": "eat",
  "resolved_path": "/mnt/skills/public/eat",
  "mode": "archive",
  "dry_run": false,
  "backup_created": "/mnt/skills/_archive/eat_20260330_120000",
  "references_cleaned": [],
  "actions": [
    "moved /mnt/skills/public/eat -> /mnt/skills/_archive/eat_20260330_120000"
  ],
  "warnings": [],
  "rollback": "move archived directory back to original path"
}
```

## Failure handling

Return structured failures for:
- target not found
- multiple matches
- invalid mode
- unsafe path
- delete requested without confirmation
- archive root unavailable
- permission denied

Do not partially delete and then report success.

## Future enhancements

Possible future additions:
- batch archive of stale skills
- duplicate-skill detection before retirement
- automatic trigger overlap analysis
- reference graph visualization
- soft-delete TTL with delayed purge
- audit log integration
