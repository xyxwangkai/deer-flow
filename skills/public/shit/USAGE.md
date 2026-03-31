# Usage Examples

## Safe default

```bash
python scripts/retire_skill.py eat --mode archive --dry-run
python scripts/retire_skill.py eat --mode archive
```

## Disable without deleting files

```bash
python scripts/retire_skill.py /mnt/skills/public/eat --mode disable --dry-run
python scripts/retire_skill.py /mnt/skills/public/eat --mode disable
```

## Permanent delete with explicit confirmation

```bash
python scripts/retire_skill.py my-old-skill --mode delete --dry-run --confirm
python scripts/retire_skill.py my-old-skill --mode delete --confirm
```

## Delete without backup (not recommended)

```bash
python scripts/retire_skill.py my-old-skill --mode delete --no-backup --confirm
```

## Live DeerFlow skills examples

```bash
python scripts/retire_skill.py /opt/tiger/deer-flow/skills/public/surprise-me --mode archive --dry-run --cleanup-refs
python scripts/retire_skill.py /opt/tiger/deer-flow/skills/public/surprise-me --mode archive --archive-root /opt/tiger/deer-flow/skills/_archive
```

## Expected confirmation policy

For agent-side interaction, require a confirmation phrase like:

```text
CONFIRM DELETE my-old-skill
```

Then translate that into the script flag `--confirm` only after the phrase has been validated.

## Example structured result

```json
{
  "target": "eat",
  "resolved_path": "/mnt/skills/public/eat",
  "mode": "archive",
  "dry_run": true,
  "backup_created": "/mnt/skills/_archive/eat_20260330_120000",
  "references_cleaned": [],
  "actions": [
    "move /mnt/skills/public/eat -> /mnt/skills/_archive/eat_20260330_120000"
  ],
  "warnings": [],
  "rollback": "move /mnt/skills/_archive/eat_20260330_120000 back to /mnt/skills/public/eat"
}
```
