#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

ALLOWED_ROOTS = [
    Path('/mnt/skills'),
    Path('/mnt/user-data/workspace'),
    Path('/opt/tiger/deer-flow/skills'),
]
DEFAULT_ARCHIVE_ROOT = Path('/mnt/skills/_archive')
DISABLED_ROOT = Path('/mnt/skills/_disabled')
LIVE_SKILLS_ROOT = Path('/opt/tiger/deer-flow/skills')
LIVE_ARCHIVE_ROOT = LIVE_SKILLS_ROOT / '_archive'
LIVE_DISABLED_ROOT = LIVE_SKILLS_ROOT / '_disabled'
PROTECTED_PATHS = {
    Path('/'),
    Path('/mnt'),
    Path('/mnt/skills'),
    Path('/mnt/skills/public'),
    Path('/mnt/skills/custom'),
    Path('/opt'),
    Path('/opt/tiger'),
    Path('/opt/tiger/deer-flow'),
    Path('/opt/tiger/deer-flow/skills'),
    Path('/opt/tiger/deer-flow/skills/public'),
    Path('/opt/tiger/deer-flow/skills/custom'),
    Path('/mnt/user-data'),
    Path('/mnt/user-data/workspace'),
}

REFERENCE_SCAN_FILENAMES = {
    'SKILL.md', 'EXTEND.md', 'USAGE.md', 'README.md', 'README',
    'pyproject.toml', 'package.json', 'requirements.txt'
}
REFERENCE_SCAN_SUFFIXES = {'.md', '.py', '.sh', '.yaml', '.yml', '.json', '.toml', '.txt'}


class RetireSkillError(Exception):
    pass


@dataclass
class ReferenceHit:
    path: str
    line: int
    text: str
    category: str


@dataclass
class Report:
    target: str
    resolved_path: str
    mode: str
    dry_run: bool
    environment: str
    allowed_root: str
    archive_root: Optional[str]
    disable_root: Optional[str]
    execution_state: str
    backup_created: Optional[str]
    references_cleaned: List[str]
    reference_hits: List[dict]
    patch_plan: List[str]
    actions: List[str]
    warnings: List[str]
    blockers: List[str]
    rollback: str
    recommended_commands: List[str]


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def detect_allowed_root(path: Path) -> Path:
    resolved = path.resolve()
    matched = [root for root in ALLOWED_ROOTS if is_within(resolved, root)]
    if not matched:
        raise RetireSkillError(f'Path outside allowed roots: {resolved}')
    return max(matched, key=lambda p: len(str(p)))


def validate_path(path: Path) -> Path:
    resolved = path.resolve()

    if resolved in PROTECTED_PATHS:
        raise RetireSkillError(f'Protected path cannot be modified: {resolved}')

    detect_allowed_root(resolved)

    if not resolved.exists():
        raise RetireSkillError(f'Target does not exist: {resolved}')

    if not resolved.is_dir():
        raise RetireSkillError(f'Target is not a directory: {resolved}')

    if '..' in str(path):
        raise RetireSkillError('Path traversal detected')

    return resolved


def looks_like_skill(path: Path) -> bool:
    return (path / 'SKILL.md').exists() or (path / 'SKILL.md.disabled').exists()


def resolve_target(target: str) -> Path:
    raw = Path(target)
    if raw.is_absolute() or str(raw).startswith('.'):
        path = validate_path(raw)
        if not looks_like_skill(path):
            raise RetireSkillError(f'Target is not a recognizable skill directory: {path}')
        return path

    candidates = []
    for root in ALLOWED_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob(target):
            if p.is_dir() and looks_like_skill(p):
                candidates.append(p.resolve())

    unique = sorted(set(candidates))
    if not unique:
        raise RetireSkillError(f'No skill found for target name: {target}')
    if len(unique) > 1:
        joined = '\n'.join(str(p) for p in unique)
        raise RetireSkillError(f'Multiple matching skills found for {target}:\n{joined}')
    return validate_path(unique[0])


def timestamp() -> str:
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def classify_environment(skill_path: Path) -> str:
    return 'live' if is_within(skill_path, LIVE_SKILLS_ROOT) else 'workspace'


def default_archive_root_for(skill_path: Path) -> Path:
    return LIVE_ARCHIVE_ROOT if is_within(skill_path, LIVE_SKILLS_ROOT) else DEFAULT_ARCHIVE_ROOT


def default_disable_root_for(skill_path: Path) -> Path:
    return LIVE_DISABLED_ROOT if is_within(skill_path, LIVE_SKILLS_ROOT) else DISABLED_ROOT


def archive_destination(skill_path: Path, archive_root: Path) -> Path:
    return archive_root / f'{skill_path.name}_{timestamp()}'


def ensure_confirmed(mode: str, confirm: bool):
    if mode == 'delete' and not confirm:
        raise RetireSkillError('Delete mode requires explicit --confirm')


def should_scan_file(path: Path) -> bool:
    return path.name in REFERENCE_SCAN_FILENAMES or path.suffix in REFERENCE_SCAN_SUFFIXES


def categorize_reference(path: Path) -> str:
    s = str(path)
    name = path.name.lower()
    if 'skill' in name or 'available_skills' in s:
        return 'registry'
    if 'readme' in name or path.suffix == '.md':
        return 'docs'
    if 'example' in name or path.suffix in {'.py', '.sh'}:
        return 'example'
    return 'other'


def scan_references(skill_path: Path) -> Tuple[List[ReferenceHit], List[str]]:
    needle_terms = {
        skill_path.name,
        str(skill_path),
        f'name: {skill_path.name}',
        f'<name>{skill_path.name}</name>',
    }
    hits: List[ReferenceHit] = []
    patch_plan: List[str] = []

    for root in ALLOWED_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob('*'):
            if not p.is_file() or not should_scan_file(p):
                continue
            if is_within(p, skill_path):
                continue
            try:
                text = p.read_text(encoding='utf-8')
            except Exception:
                continue
            lines = text.splitlines()
            file_hits = 0
            for idx, line in enumerate(lines, start=1):
                if any(term in line for term in needle_terms):
                    file_hits += 1
                    hits.append(ReferenceHit(
                        path=str(p),
                        line=idx,
                        text=line.strip()[:240],
                        category=categorize_reference(p),
                    ))
            if file_hits:
                patch_plan.append(f'review {p} ({file_hits} hits)')

    return hits, patch_plan


def infer_execution_state(skill_path: Path, dry_run: bool) -> Tuple[str, List[str], List[str]]:
    warnings: List[str] = []
    blockers: List[str] = []
    environment = classify_environment(skill_path)

    if dry_run:
        state = 'planned'
    else:
        state = 'ready'

    if environment == 'live':
        warnings.append('Target is inside the live DeerFlow skills tree; filesystem permissions may block execution.')
        if not dry_run:
            warnings.append('If this command is executed inside a restricted sandbox, permission or path policy failure is expected.')

    return state, warnings, blockers


def do_archive(skill_path: Path, archive_root: Path, dry_run: bool, actions: List[str]) -> Path:
    dst = archive_destination(skill_path, archive_root)
    actions.append(f'move {skill_path} -> {dst}')
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(skill_path), str(dst))
    return dst


def do_disable(skill_path: Path, disable_root: Path, dry_run: bool, actions: List[str]) -> Path:
    skill_md = skill_path / 'SKILL.md'
    disabled_md = skill_path / 'SKILL.md.disabled'

    if skill_md.exists():
        actions.append(f'rename {skill_md} -> {disabled_md}')
        if not dry_run:
            skill_md.rename(disabled_md)
        return disabled_md

    if disabled_md.exists():
        actions.append(f'skill already disabled: {disabled_md}')
        return disabled_md

    fallback = disable_root / f'{skill_path.name}_{timestamp()}'
    actions.append(f'move {skill_path} -> {fallback}')
    if not dry_run:
        fallback.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(skill_path), str(fallback))
    return fallback


def do_delete(skill_path: Path, backup: bool, archive_root: Path, dry_run: bool, actions: List[str]) -> Optional[Path]:
    backup_path = None
    if backup:
        backup_path = archive_destination(skill_path, archive_root)
        actions.append(f'backup move {skill_path} -> {backup_path}')
        if not dry_run:
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(skill_path), str(backup_path))
        return backup_path

    actions.append(f'delete directory {skill_path}')
    if not dry_run:
        shutil.rmtree(skill_path)
    return None


def build_recommended_commands(skill_path: Path, mode: str, archive_root: Path, cleanup_refs: bool, dry_run: bool, backup: bool) -> List[str]:
    base = [
        'python scripts/retire_skill.py',
        str(skill_path),
        f'--mode {mode}',
        f'--archive-root {archive_root}',
    ]
    if cleanup_refs:
        base.append('--cleanup-refs')
    if mode == 'delete' and not backup:
        base.append('--no-backup')
    execute_cmd = ' '.join(base + (['--confirm'] if mode == 'delete' else []))
    dry_run_cmd = ' '.join(base + ['--dry-run'] + (['--confirm'] if mode == 'delete' else []))
    if dry_run:
        return [dry_run_cmd, execute_cmd]
    return [dry_run_cmd, execute_cmd]


def retire_skill(target: str, mode: str = 'archive', backup: bool = True, cleanup_refs: bool = False,
                 dry_run: bool = False, confirm: bool = False, archive_root: Optional[str] = None) -> Report:
    if mode not in {'archive', 'disable', 'delete'}:
        raise RetireSkillError(f'Unsupported mode: {mode}')

    ensure_confirmed(mode, confirm)
    skill_path = resolve_target(target)
    allowed_root = detect_allowed_root(skill_path)
    environment = classify_environment(skill_path)
    archive_root_path = Path(archive_root).resolve() if archive_root else default_archive_root_for(skill_path)
    disable_root_path = default_disable_root_for(skill_path)

    actions: List[str] = []
    refs: List[str] = []
    backup_created: Optional[str] = None

    execution_state, warnings, blockers = infer_execution_state(skill_path, dry_run)
    reference_hits, patch_plan = scan_references(skill_path) if cleanup_refs else ([], [])

    if cleanup_refs and not reference_hits:
        warnings.append('No reference hits found in the allowlisted roots.')
    elif cleanup_refs:
        warnings.append('Reference cleanup is plan-only in this version; review patch_plan before editing files.')

    if mode == 'archive':
        archived = do_archive(skill_path, archive_root_path, dry_run, actions)
        backup_created = str(archived)
        rollback = f'move {archived} back to {skill_path}'
    elif mode == 'disable':
        disabled_path = do_disable(skill_path, disable_root_path, dry_run, actions)
        rollback = f'restore original active state for {skill_path} from {disabled_path}'
    else:
        backup_path = do_delete(skill_path, backup, archive_root_path, dry_run, actions)
        backup_created = str(backup_path) if backup_path else None
        rollback = f'restore from backup {backup_path}' if backup_path else 'not recoverable without external backup'

    if not dry_run:
        execution_state = 'executed'

    recommended_commands = build_recommended_commands(
        skill_path=skill_path,
        mode=mode,
        archive_root=archive_root_path,
        cleanup_refs=cleanup_refs,
        dry_run=dry_run,
        backup=backup,
    )

    return Report(
        target=target,
        resolved_path=str(skill_path),
        mode=mode,
        dry_run=dry_run,
        environment=environment,
        allowed_root=str(allowed_root),
        archive_root=str(archive_root_path),
        disable_root=str(disable_root_path),
        execution_state=execution_state,
        backup_created=backup_created,
        references_cleaned=refs,
        reference_hits=[asdict(hit) for hit in reference_hits],
        patch_plan=patch_plan,
        actions=actions,
        warnings=warnings,
        blockers=blockers,
        rollback=rollback,
        recommended_commands=recommended_commands,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description='Safely archive, disable, or delete a skill directory.')
    parser.add_argument('target', help='Skill name or absolute path')
    parser.add_argument('--mode', choices=['archive', 'disable', 'delete'], default='archive')
    parser.add_argument('--no-backup', action='store_true', help='Disable backup before delete')
    parser.add_argument('--cleanup-refs', action='store_true', help='Request reference cleanup planning')
    parser.add_argument('--dry-run', action='store_true', help='Plan actions without changing files')
    parser.add_argument('--confirm', action='store_true', help='Required for delete mode')
    parser.add_argument('--archive-root', default=None)
    args = parser.parse_args()

    report = retire_skill(
        target=args.target,
        mode=args.mode,
        backup=not args.no_backup,
        cleanup_refs=args.cleanup_refs,
        dry_run=args.dry_run,
        confirm=args.confirm,
        archive_root=args.archive_root,
    )
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except RetireSkillError as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
