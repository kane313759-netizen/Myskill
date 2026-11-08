#!/usr/bin/env python3
"""Local-only installer/doctor/cleanup. Python 3.8+; no network or third-party packages."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid

REQUIRED = ('hackathon-orchestrator', 'hackathon-finals', 'edge-redteam', 'grader-intake', 'immutable-inventory',
            'task-router', 'problem-intake', 'constraint-discovery',
            'verification', 'final-explain', 'followup-prep')
SUPPORT_DIRS = ('prompts', 'references', 'templates', 'scripts')
SUPPORT_FILES = ('EXAM_POLICY.md', 'FINALS_POLICY.md', 'BOOTSTRAP_PROMPT.md', 'CALLING.md',
                 'AGENTS.snippet.md', 'VERSION')
MANIFEST = 'manifest.json'
KIT_ID = 'sk-hynix-exam-kit'
METADATA_LIMIT = 8 * 1024 * 1024
VERSION_LIMIT = 64 * 1024
SCRIPT_LIMIT = 16 * 1024 * 1024


class LifecycleError(Exception):
    pass


def inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def safe_path(path):
    """Never read/write/delete through a link in a managed path."""
    for part in (path,) + tuple(path.parents):
        if part.is_symlink():
            raise LifecycleError('Symlink path is protected: ' + str(part))


def name_ok(name):
    return isinstance(name, str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', name)) and name not in ('.', '..')


def rel_ok(rel):
    if not isinstance(rel, str) or '\\' in rel:
        return False
    p = PurePosixPath(rel)
    return bool(rel) and not p.is_absolute() and all(x not in ('', '.', '..') for x in rel.split('/'))


def internal_source_ok(rel):
    return (rel_ok(rel) and not PureWindowsPath(rel).drive
            and not any(ord(ch) < 32 or ord(ch) == 127 for ch in rel)
            and rel.split('/')[0].casefold() not in ('.git', '.agents', '.hackathon-kit'))


@contextmanager
def open_regular(path):
    """Reject special files before opening and check the opened descriptor too."""
    path = Path(path)
    safe_path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise LifecycleError('Non-regular file is protected: ' + str(path))
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(str(path), flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise LifecycleError('Opened file is not regular: ' + str(path))
        handle = os.fdopen(descriptor, 'rb')
        descriptor = None
        with handle:
            yield handle
    finally:
        if descriptor is not None:
            os.close(descriptor)


def read_regular(path, limit):
    with open_regular(path) as handle:
        if os.fstat(handle.fileno()).st_size > limit:
            raise LifecycleError('File exceeds byte limit: ' + str(path))
        content = handle.read(limit + 1)
    if len(content) > limit:
        raise LifecycleError('File exceeds byte limit: ' + str(path))
    return content


def digest(path):
    h = hashlib.sha256()
    with open_regular(path) as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def files_under(root, exclude_cache=False):
    safe_path(root)
    if not root.is_dir():
        raise LifecycleError('Expected directory: ' + str(root))
    result = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            safe_path(Path(current) / name)
        if exclude_cache:
            dirs[:] = [d for d in dirs if d != '__pycache__']
        for name in files:
            p = Path(current) / name
            if exclude_cache and name.endswith(('.pyc', '.pyo')):
                continue
            if not p.is_file():
                raise LifecycleError('Non-regular file is protected: ' + str(p))
            result[p.relative_to(root).as_posix()] = digest(p)
    return result


def tree_digest(root):
    entries = files_under(root)
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode('utf-8')).hexdigest()


def load_manifest(kit, optional=False):
    p = kit / MANIFEST
    safe_path(p)
    if not p.exists():
        if optional:
            return None
        raise LifecycleError('No verified ownership manifest. Legacy cleanup is refused; reinstall from a trusted kit to migrate identical skills first.')
    try:
        data = json.loads(read_regular(p, METADATA_LIMIT).decode('utf-8-sig'))
    except (ValueError, OSError, RecursionError) as e:
        raise LifecycleError('Invalid ownership manifest: ' + str(e))
    if not isinstance(data, dict) or data.get('schema') != 1 or data.get('kit_id') != KIT_ID:
        raise LifecycleError('Unrecognized ownership manifest')
    for key in ('owned_skills', 'borrowed_skills', 'managed_files'):
        if not isinstance(data.get(key), dict):
            raise LifecycleError('Invalid manifest field: ' + key)
        for name, value in data[key].items():
            if not (rel_ok(name) if key == 'managed_files' else name_ok(name)):
                raise LifecycleError('Unsafe manifest path: ' + repr(name))
            if key == 'managed_files' and (name == MANIFEST or name.startswith('run/')):
                raise LifecycleError('Invalid managed support path: ' + name)
            if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
                raise LifecycleError('Invalid manifest digest: ' + name)
    if set(data['owned_skills']) & set(data['borrowed_skills']):
        raise LifecycleError('Duplicate skill ownership')
    allowed_dirs = {'.agents', '.agents/skills', '.hackathon-kit'}
    if not isinstance(data.get('created_dirs'), list) or any(x not in allowed_dirs for x in data['created_dirs']):
        raise LifecycleError('Invalid created-directory manifest')
    if not isinstance(data.get('version'), str) or not isinstance(data.get('source_digest'), str) or not re.fullmatch('[0-9a-f]{64}', data['source_digest']):
        raise LifecycleError('Missing source version/hash')
    internal = data.get('internal_sources', [])
    if not isinstance(internal, list) or any(not internal_source_ok(x) for x in internal):
        raise LifecycleError('Unsafe internal source path')
    if len(internal) != len(set(internal)):
        raise LifecycleError('Duplicate internal source path')
    return data


def validate_legacy(kit):
    p = kit / 'run/INSTALLED_SKILLS.txt'
    safe_path(p)
    if not p.exists():
        return []
    try:
        names = [x for x in read_regular(p, METADATA_LIMIT).decode('utf-8-sig').splitlines() if x]
    except UnicodeError as e:
        raise LifecycleError('Invalid legacy ownership encoding: ' + str(e))
    if any(not name_ok(x) for x in names):
        raise LifecycleError('Unsafe legacy skill ownership name; nothing changed')
    return names


def write_bytes(path, value):
    safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.kit-write-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(value)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def copy_regular(source, path):
    """Stream support files without imposing a new limit on their content sizes."""
    safe_path(path)
    with open_regular(source) as original:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix='.kit-write-', dir=str(path.parent))
        try:
            with os.fdopen(fd, 'wb') as destination:
                shutil.copyfileobj(original, destination, length=1024 * 1024)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def run_git(root, *args):
    try:
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, encoding='utf-8', errors='surrogateescape')
    except FileNotFoundError:
        return None


def git_context(root):
    result = run_git(root, 'rev-parse', '--show-toplevel')
    if result is None or result.returncode:
        return None
    top = Path(result.stdout.rstrip('\r\n')).resolve()
    result = run_git(root, 'rev-parse', '--git-path', 'info/exclude')
    if result is None or result.returncode:
        raise LifecycleError('Could not resolve local Git exclusions')
    exclude = Path(result.stdout.rstrip('\r\n'))
    if not exclude.is_absolute():
        exclude = root / exclude
    safe_path(exclude)
    return top, exclude


def ignore_patterns(root, owned, context, internal_sources=()):
    top, _ = context
    prefix = root.relative_to(top).as_posix()
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in prefix):
        raise LifecycleError('Unsafe target path: control characters cannot be represented in Git exclusions.')
    prefix = '' if prefix == '.' else prefix + '/'
    # Escape Git wildmatch metacharacters in legitimate directory names.
    def esc(s):
        return re.sub(r'([\\*?\[\]])', r'\\\1', s)
    return ['/' + esc(prefix + '.hackathon-kit') + '/'] + [
        '/' + esc(prefix + '.agents/skills/' + name) + '/' for name in sorted(owned)] + [
        '/' + esc(prefix + rel) + '/' for rel in internal_sources]


def prepare_excludes(root, owned, internal_sources=()):
    lookup_root = root
    while not lookup_root.exists():
        lookup_root = lookup_root.parent
    context = git_context(lookup_root)
    if context is None:
        return None
    _, exclude = context
    for parent in exclude.parents:
        if parent.exists() and not parent.is_dir():
            raise LifecycleError('Expected Git metadata directory: ' + str(parent))
    old = read_regular(exclude, METADATA_LIMIT) if exclude.exists() else b''
    lines = old.splitlines()
    additions = [x.encode('utf-8') for x in ignore_patterns(root, owned, context, internal_sources) if x.encode('utf-8') not in lines]
    return exclude, old, additions


def add_excludes(prepared):
    if prepared is None:
        print('[WARN] No Git worktree; helper files must be excluded by the submission procedure.')
        return
    exclude, old, additions = prepared
    if additions:
        # Preserve the existing final line, including when it has no newline.
        separator = b'' if not old or old.endswith((b'\n', b'\r')) else b'\n'
        write_bytes(exclude, old + separator + b'\n'.join(additions) + b'\n')


def remaining_internal_sources(root, manifest):
    remaining = []
    for rel in manifest.get('internal_sources', []):
        path = root / rel
        safe_path(path)
        if path.exists():
            remaining.append(rel)
    return remaining


def install(source, root, allow_internal_source=False):
    source, root = source.absolute(), root.absolute()
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in str(root)):
        raise LifecycleError('Unsafe target path: control characters are not allowed; nothing installed.')
    safe_path(source)
    safe_path(root)
    source, root = source.resolve(), root.resolve()
    if inside(root, source):
        raise LifecycleError('Source and target must not be identical; target must not be inside the kit source.')
    internal_source = inside(source, root)
    if internal_source:
        if not allow_internal_source:
            raise LifecycleError('Keep the kit source outside the task tree, or explicitly use --allow-internal-source for a separate temporary source directory.')
        if not internal_source_ok(source.relative_to(root).as_posix()):
            raise LifecycleError('Unsafe internal source path; use a separate temporary directory without control characters, drive prefixes, or reserved helper names.')
        for name in ('.git', '.agents', '.hackathon-kit'):
            protected = root / name
            if inside(source, protected) or inside(protected, source):
                raise LifecycleError('Internal source overlaps a protected task/helper path: ' + name)
    kit = root / '.hackathon-kit'
    skills = root / '.agents/skills'
    safe_path(kit)
    safe_path(skills)
    old = load_manifest(kit, optional=True)
    internal_sources = set((old or {}).get('internal_sources', []))
    if internal_source:
        internal_sources.add(source.relative_to(root).as_posix())
    internal_sources = sorted(internal_sources)
    legacy_names = validate_legacy(kit)
    if kit.exists() and old is None and not (kit / 'run/INSTALLED_SKILLS.txt').is_file():
        raise LifecycleError('Existing .hackathon-kit has no recognized ownership; preserved without changes.')
    source_skills = source / '.agents/skills'
    source_hashes = {}
    for p in sorted(source_skills.iterdir()):
        if not name_ok(p.name):
            raise LifecycleError('Invalid source skill name: ' + p.name)
        source_hashes[p.name] = tree_digest(p)
    if not set(REQUIRED).issubset(source_hashes):
        raise LifecycleError('Source kit is missing required core skills')
    source_files = {}
    version = read_regular(source / 'VERSION', VERSION_LIMIT).decode('utf-8-sig').strip()
    if not version:
        raise LifecycleError('Source VERSION is empty')
    for directory in SUPPORT_DIRS:
        for rel, value in files_under(source / directory, exclude_cache=True).items():
            source_files[directory + '/' + rel] = value
    for name in SUPPORT_FILES:
        safe_path(source / name)
        source_files[name] = digest(source / name)
    owned, borrowed, updates, warnings = {}, {}, [], []
    old_owned = old['owned_skills'] if old else {}
    # Complete conflict preflight before creating any task paths.
    for name, expected in source_hashes.items():
        dst = skills / name
        safe_path(dst)
        if not dst.exists():
            owned[name] = expected
            updates.append(name)
            continue
        current = tree_digest(dst)
        if name in old_owned:
            if current == old_owned[name]:
                owned[name] = expected
                if current != expected:
                    updates.append(name)
            else:
                owned[name] = old_owned[name]
                warnings.append('Locally changed owned skill preserved: ' + name)
        elif current == expected:
            # A legacy installed skill can be adopted only with verified bytes.
            if name in legacy_names:
                owned[name] = expected
            else:
                borrowed[name] = expected
        elif name in REQUIRED:
            raise LifecycleError('Required skill name collision: ' + name + '. Existing skill preserved; resolve/rename the collision before installing.')
        else:
            warnings.append('Unrelated existing optional skill preserved: ' + name)
    # Preserve prior owned optional skills removed from a newer kit for safe cleanup.
    for name, value in old_owned.items():
        if name not in source_hashes:
            owned[name] = value
    managed = {}
    preserve_support = set()
    old_files = old['managed_files'] if old else {}
    for rel, expected in source_files.items():
        dst = kit / rel
        safe_path(dst)
        conflict = dst.exists() and ((old and (rel not in old_files or digest(dst) != old_files[rel])) or (not old and digest(dst) != expected))
        if conflict:
            managed[rel] = old_files.get(rel, expected)
            preserve_support.add(rel)
            warnings.append('Locally changed or unverified legacy support file preserved: ' + rel)
        else:
            managed[rel] = expected
    # Do not forget obsolete files: retain ownership until a deliberate cleanup.
    for rel, value in old_files.items():
        managed.setdefault(rel, value)
    created = set(old['created_dirs'] if old else [])
    for rel in ('.agents', '.agents/skills', '.hackathon-kit'):
        if not (root / rel).exists():
            created.add(rel)
    # Read and validate existing Git metadata before copying any helpers.
    prepared_excludes = prepare_excludes(root, owned, internal_sources)
    skills.mkdir(parents=True, exist_ok=True)
    (kit / 'run').mkdir(parents=True, exist_ok=True)
    for name in updates:
        dst = skills / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(source_skills / name, dst)
    for rel, expected in source_files.items():
        dst = kit / rel
        if rel not in preserve_support:
            copy_regular(source / rel, dst)
    for template in sorted((kit / 'templates').iterdir()):
        if template.is_file() and template.suffix.lower() in ('.md', '.json'):
            dst = kit / 'run' / template.name
            safe_path(dst)
            if not dst.exists():
                copy_regular(template, dst)
    last = kit / 'run/LAST_10_MINUTES.md'
    if not last.exists():
        write_bytes(last, b'# LAST 10 MINUTES\n\n## Solved\n\n## Changed\n\n## Remaining risks\n\n## Follow-up explanation points\n')
    source_digest = hashlib.sha256(json.dumps({'skills': source_hashes, 'files': source_files}, sort_keys=True).encode()).hexdigest()
    manifest = dict(schema=1, kit_id=KIT_ID, installation_id=(old or {}).get('installation_id', str(uuid.uuid4())),
                    version=version, source_digest=source_digest, owned_skills=owned,
                    borrowed_skills=borrowed, managed_files=managed, created_dirs=sorted(created),
                    internal_sources=internal_sources)
    write_bytes(kit / MANIFEST, (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    add_excludes(prepared_excludes)
    for message in warnings:
        print('[WARN] ' + message)
    print('Installed kit version ' + version + ' into: ' + str(root))
    print('Run notes preserved under .hackathon-kit/run/. Python 3 is required for lifecycle and gate checks.')
    print('Local Git exclusions do not exclude files from directory/ZIP submission snapshots.')
    for rel in remaining_internal_sources(root, manifest):
        print('[WARN] Internal kit source remains: ' + rel + '. After verifying installation, remove only the temporary source you created; never delete preexisting/task content.')


def inspect_install(root, manifest):
    kit = root / '.hackathon-kit'
    errors = []
    version = kit / 'VERSION'
    version_matches = (version.is_file() and
                       read_regular(version, VERSION_LIMIT).decode('utf-8-sig').strip() == manifest['version'])
    for name in REQUIRED:
        expected = manifest['owned_skills'].get(name, manifest['borrowed_skills'].get(name))
        if expected is None:
            errors.append('Required skill is not verified: ' + name)
    for name, expected in dict(manifest['owned_skills'], **manifest['borrowed_skills']).items():
        p = root / '.agents/skills' / name
        if not p.is_dir() or tree_digest(p) != expected:
            errors.append('Skill missing or locally changed: ' + name)
    for rel, expected in manifest['managed_files'].items():
        p = kit / rel
        safe_path(p)
        if not p.is_file() or digest(p) != expected:
            errors.append('Support file missing or locally changed: ' + rel)
    if not version_matches:
        errors.append('Installed VERSION does not match ownership metadata')
    return errors


def doctor(root, pre_submit):
    root = root.absolute()
    safe_path(root)
    kit = root / '.hackathon-kit'
    manifest = load_manifest(kit)
    validate_legacy(kit)
    errors = inspect_install(root, manifest)
    for rel in remaining_internal_sources(root, manifest):
        message = 'Internal kit source remains in the task tree: ' + rel
        if pre_submit:
            errors.append(message + '; verify and remove your temporary source before submission.')
        else:
            print('[WARN] ' + message)
    for name in ('STATE.md', 'GRADER.md', 'BASELINE.md'):
        p = kit / 'run' / name
        safe_path(p)
        if not p.is_file():
            errors.append('Missing runtime record: ' + name)
    for p in (kit / 'scripts').glob('*.py'):
        try:
            compile(read_regular(p, SCRIPT_LIMIT), str(p), 'exec')
        except (SyntaxError, ValueError) as e:
            errors.append('Python helper syntax error: ' + str(e))
    context = git_context(root)
    if context is not None:
        for pattern in ignore_patterns(root, manifest['owned_skills'], context, manifest.get('internal_sources', [])):
            # check-ignore receives real paths, not escaped patterns.
            path = pattern[1:-1]
            path = re.sub(r'\\([\\*?\[\]])', r'\1', path)
            result = run_git(context[0], 'check-ignore', '-q', '--', path + '/')
            if result is None or result.returncode:
                errors.append('Helper path is not excluded from Git: ' + path)
    else:
        print('[WARN] No Git worktree; verify the submission file list manually.')
    state = kit / 'run/STATE.md'
    gate_path = kit / 'scripts/gate_check.py'
    gate_expected = manifest['managed_files'].get('scripts/gate_check.py')
    gate_verified = gate_path.is_file() and digest(gate_path) == gate_expected
    gate_state = None
    if gate_verified:
        try:
            # Import the installed gate without its CLI main or bytecode writes.
            # Doctor and gate intentionally share status grammar and size limits.
            policy = runpy.run_path(str(gate_path), run_name='kit_gate_policy')
            read_record, parse_state = policy['read_text'], policy['parse_state']
            values, parse_errors = parse_state(read_record(state))
            errors.extend(parse_errors)
            initial, initial_errors = parse_state(read_record(kit / 'templates/STATE.md'))
            errors.extend('STATE template: ' + message for message in initial_errors)
            for key, completed in policy['REQUIRED_STATE'].items():
                allowed = set(completed) | {initial.get(key)}
                if key not in values or values[key] not in allowed:
                    errors.append('STATE.md invalid or missing status %s=%s' % (key, values.get(key, '<missing>')))
            gate_state = values.get('constraint_gate')
            if not pre_submit and gate_state == 'OPEN' and not parse_errors:
                print('[WARN] Constraint gate is open; normal immediately after installation.')
        except (OSError, UnicodeError, ValueError, SyntaxError, KeyError, TypeError) as error:
            errors.append('STATE/gate parser: ' + str(error))
    else:
        errors.append('Verified installed gate parser unavailable; restore the kit before validation.')
    if gate_verified and (pre_submit or gate_state == 'CLOSED'):
        result = subprocess.run([sys.executable, '-B', str(gate_path), '--kit', str(kit)])
        if result.returncode:
            errors.append('Pre-submit gate check failed' if pre_submit else 'Closed gate evidence check failed')
    print('Installed source VERSION: ' + manifest['version'])
    print('Recorded source SHA256: ' + manifest['source_digest'])
    print('Local Git exclusions do not exclude helpers from directory/ZIP submission snapshots.')
    print('Second preliminary: Computer Use, external task-data transmission, external AI, and Git Push remain prohibited.')
    print('Finals: use FINALS_POLICY.md and current official rules; this doctor does not establish finals readiness. --pre-submit checks the preliminary gate only.')
    for message in errors:
        print('[FAIL] ' + message)
    if not errors:
        print('[OK] Required/owned skill identities, support files, and local Git exclusions verified.')
    return 2 if errors else 0


def cleanup(root, apply):
    root = root.absolute()
    safe_path(root)
    kit = root / '.hackathon-kit'
    safe_path(kit)
    if not apply:
        print('Dry-run only. Nothing removed. Use --apply after final explanation preparation.')
        return 0
    if not kit.exists():
        print('No .hackathon-kit found.')
        return 0
    validate_legacy(kit)
    manifest = load_manifest(kit)
    remaining = remaining_internal_sources(root, manifest)
    if remaining:
        raise LifecycleError('Internal kit source remains; verify and remove only your temporary source before helper cleanup: ' + ', '.join(remaining))
    protected = []
    # Inspect all deletion candidates before deleting anything. Run notes are dynamic
    # content intentionally removed only after their complete external local backup.
    actual = files_under(kit)
    allowed = set(manifest['managed_files']) | {MANIFEST}
    for rel, value in actual.items():
        if rel.startswith('run/'):
            continue
        if rel not in allowed:
            protected.append('Unexpected helper content: ' + rel)
        elif rel != MANIFEST and value != manifest['managed_files'][rel]:
            protected.append('Locally changed support file: ' + rel)
    for name, expected in manifest['owned_skills'].items():
        p = root / '.agents/skills' / name
        safe_path(p)
        if p.exists() and tree_digest(p) != expected:
            protected.append('Locally changed owned skill: ' + name)
    if protected:
        raise LifecycleError('Cleanup refused; helpers remain intact. ' + '; '.join(protected))
    temp_root = Path(tempfile.gettempdir()).resolve()
    if inside(temp_root, root):
        raise LifecycleError('Backup temp directory is inside the task tree. Set TMPDIR/TEMP to an external local directory.')
    backup = Path(tempfile.mkdtemp(prefix='hackathon-kit-run-backup-', dir=str(temp_root)))
    run = kit / 'run'
    if run.exists():
        shutil.copytree(run, backup / 'run')
    print('Run-note backup: ' + str(backup))
    for name in manifest['owned_skills']:
        p = root / '.agents/skills' / name
        if p.exists():
            shutil.rmtree(p)
    shutil.rmtree(kit)
    for rel in sorted(manifest['created_dirs'], key=lambda x: x.count('/'), reverse=True):
        p = root / rel
        safe_path(p)
        if p.exists():
            try:
                p.rmdir()
            except OSError:
                pass
    print('Removed verified kit-owned helpers; borrowed/unrelated skills preserved.')
    print('Shared/preexisting local Git exclude rules retained safely for other worktrees.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('install')
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--target', type=Path, default=Path('.'))
    p.add_argument('--allow-internal-source', action='store_true',
                   help='Allow a separate temporary source below the target, excluding .git/.agents/.hackathon-kit. Never removes the source automatically.')
    for name in ('doctor', 'clean'):
        p = sub.add_parser(name)
        p.add_argument('--kit', type=Path, default=Path(__file__).resolve().parents[1])
        if name == 'doctor':
            p.add_argument('--pre-submit', action='store_true')
        else:
            p.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'install':
            install(args.source, args.target, args.allow_internal_source)
            return 0
        kit = args.kit.absolute()
        safe_path(kit)
        kit = kit.resolve()
        if kit.name != '.hackathon-kit':
            raise LifecycleError('--kit must point to the installed .hackathon-kit directory')
        if args.command == 'doctor':
            return doctor(kit.parent, args.pre_submit)
        return cleanup(kit.parent, args.apply)
    except (LifecycleError, OSError, UnicodeError) as e:
        print('[FAIL] ' + str(e), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
