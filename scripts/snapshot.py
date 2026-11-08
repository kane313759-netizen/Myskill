#!/usr/bin/env python3
"""Bounded local snapshots of an explicit manifest; raw inputs are hash-only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import uuid

KIND = 'myskill-v27-snapshot'
MAX_FILES = 5000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
RECORD_LIMIT = 2 * 1024 * 1024
PINNED = {'M1', 'FINAL', '최종'}


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def _linked(path):
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) &
                                    getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400))


def _safe(root, relative, must_exist=True):
    if not isinstance(relative, str) or not relative:
        raise ValueError('manifest paths must be nonempty task-relative strings')
    rel = Path(relative)
    windows = PureWindowsPath(relative)
    if (rel.is_absolute() or windows.drive or windows.root or '..' in rel.parts or
            '..' in windows.parts or any(':' in part or '\x00' in part for part in windows.parts)):
        raise ValueError('path must stay relative to the intended root')
    path = root / rel
    if root.resolve() not in path.resolve().parents:
        raise ValueError('path resolves outside its intended root')
    current = root
    for part in rel.parts:
        current = current / part
        try:
            if _linked(current):
                raise ValueError('symlink/junction/reparse path is not allowed')
        except FileNotFoundError:
            if must_exist:
                raise
    return path


def _read_regular(path, limit, destination=None, capture=False):
    """Hash/copy once through a bounded regular descriptor, preserving originals."""
    before = path.lstat()
    if _linked(path) or not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError('source must be a bounded regular non-link file: ' + str(path))
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    result, count, captured = hashlib.sha256(), 0, []
    target = None
    try:
        descriptor = os.open(str(path), flags)
        with os.fdopen(descriptor, 'rb') as handle:
            target = destination.open('xb') if destination is not None else None
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError('opened source is not regular')
            while True:
                chunk = handle.read(min(1024 * 1024, limit - count + 1))
                if not chunk:
                    break
                count += len(chunk)
                if count > limit:
                    raise ValueError('source exceeds snapshot byte limit')
                result.update(chunk)
                if capture:
                    captured.append(chunk)
                if target is not None:
                    target.write(chunk)
            after = os.fstat(handle.fileno())
        current = path.lstat()
        fingerprint = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
        if _linked(path) or fingerprint(opened) != fingerprint(after) or fingerprint(after) != fingerprint(current):
            raise ValueError('source changed during snapshot; retry a stopped writer')
    finally:
        if target is not None:
            target.close()
    summary = {'sha256': result.hexdigest(), 'bytes': count}
    return (summary, b''.join(captured)) if capture else summary


def _read_json(path):
    _, data = _read_regular(path, RECORD_LIMIT, capture=True)
    return json.loads(data.decode('utf-8-sig'), object_pairs_hook=_unique)


def _readonly(path):
    if os.name == 'nt':
        return bool(getattr(path.stat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_READONLY)
    return not bool(path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def _set_readonly(path, directory=False):
    mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
    if directory:
        mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(str(path), mode)
    if not _readonly(path):
        raise ValueError('read-only attribute was not applied: ' + str(path))


def _walk(directory, budget=MAX_FILES * 3 + 20):
    """Inventory only one owned snapshot; never scan the task tree."""
    pending, files, dirs = [directory], [], []
    count = 0
    while pending:
        parent = pending.pop()
        dirs.append(parent)
        with os.scandir(str(parent)) as entries:
            for entry in entries:
                count += 1
                if count > budget:
                    raise ValueError('snapshot inventory exceeds its entry limit')
                path = Path(entry.path)
                if _linked(path):
                    raise ValueError('snapshot contains a linked/reparse path')
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(path)
                else:
                    raise ValueError('snapshot contains a special file')
    return files, dirs


def verify_snapshot(path):
    """Verify this snapshot's recorded bytes and attributes, not OS immutability."""
    path = Path(path).absolute()
    if path.name == 'MANIFEST.json':
        path = path.parent
    if path.parent.name != 'snapshots' or path.parent.parent.name != '.hackathon-kit':
        raise ValueError('snapshot must be directly inside .hackathon-kit/snapshots')
    if _linked(path.parent) or _linked(path.parent.parent):
        raise ValueError('snapshot ancestors cannot be linked/reparse directories')
    if _linked(path) or not path.is_dir():
        raise ValueError('snapshot root must be a real directory')
    record_path = _safe(path, 'MANIFEST.json')
    record = _read_json(record_path)
    if not isinstance(record, dict) or record.get('kind') != KIND or type(record.get('version')) is not int or record.get('version') != 1 or record.get('snapshot_id') != path.name:
        raise ValueError('snapshot ownership marker is not recognized')
    if not isinstance(record.get('name'), str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}|최종', record['name']):
        raise ValueError('snapshot name is invalid')
    if record.get('pinned') is not (record['name'].upper() in PINNED):
        raise ValueError('snapshot pin marker conflicts with its name')
    if not isinstance(record.get('created_at'), str):
        raise ValueError('snapshot creation time must be an ISO string')
    created = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
    if created.tzinfo is None or created.utcoffset() is None:
        raise ValueError('snapshot creation time needs a timezone')
    payload, data_files = record.get('files'), record.get('data_files')
    if not isinstance(payload, dict) or not payload or not isinstance(data_files, dict):
        raise ValueError('snapshot manifest needs copied and hash-only file maps')
    if len(payload) + len(data_files) > MAX_FILES:
        raise ValueError('snapshot file-count limit exceeded')
    expected, total, identities = {'MANIFEST.json'}, 0, set()
    for relative, stated in payload.items():
        if not isinstance(stated, dict):
            raise ValueError('snapshot file record must be an object')
        target = _safe(path, 'files/' + relative)
        identity = os.path.normcase(str(target.resolve()))
        if identity in identities:
            raise ValueError('snapshot paths overlap after normalization')
        identities.add(identity)
        actual = _read_regular(target, MAX_FILE_BYTES)
        if actual != stated:
            raise ValueError('snapshot file changed: ' + relative)
        total += actual['bytes']
        expected.add('files/' + Path(relative).as_posix())
    for relative, stated in data_files.items():
        target = _safe(path, 'files/' + relative, must_exist=False)
        identity = os.path.normcase(str(target.resolve()))
        if identity in identities:
            raise ValueError('hash-only data overlaps a copied file or another declaration')
        identities.add(identity)
        if relative in payload or not isinstance(stated, dict) or not isinstance(stated.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', stated['sha256']):
            raise ValueError('hash-only data record is invalid or also copied')
        if type(stated.get('bytes')) is not int or stated['bytes'] < 0 or stated['bytes'] > MAX_FILE_BYTES:
            raise ValueError('hash-only data size is invalid')
        total += stated['bytes']
    if total > MAX_TOTAL_BYTES:
        raise ValueError('snapshot total-byte limit exceeded')
    actual_files, directories = _walk(path)
    if {item.relative_to(path).as_posix() for item in actual_files} != expected:
        raise ValueError('snapshot contains unexpected or missing files; preserved')
    if not all(_readonly(item) for item in actual_files + directories):
        raise ValueError('snapshot read-only attributes changed')
    return {'status': 'VERIFIED', 'path': str(path), 'name': record['name'],
            'pinned': record['pinned'], 'created_at': record['created_at'],
            'copied_files': len(payload), 'data_hashes': len(data_files),
            'manifest_sha256': _read_regular(record_path, RECORD_LIMIT)['sha256'],
            'notice': 'Local accidental-change recovery only; not remote backup or OS isolation.'}


def _remove_owned_snapshot(parent, path):
    # Literal resolved targets are verified before any recursive-scope removal.
    parent, path = parent.absolute(), path.absolute()
    if path.parent != parent or parent.resolve() not in path.resolve().parents:
        raise ValueError('retention target escapes the intended snapshots directory')
    verify_snapshot(path)
    files, directories = _walk(path)
    for item in files + directories:
        if parent.resolve() not in item.resolve().parents or _linked(item):
            raise ValueError('retention path escaped or changed')
    # POSIX unlink requires a writable parent directory, even when the file
    # itself is writable. Change only this verified snapshot's owned directories
    # before removing files; never change the snapshots parent or task originals.
    for item in sorted(directories, key=lambda item: len(item.parts)):
        if parent.resolve() not in item.resolve().parents or _linked(item):
            raise ValueError('retention directory escaped or changed')
        os.chmod(str(item), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    for item in files:
        if parent.resolve() not in item.resolve().parents or _linked(item):
            raise ValueError('retention file escaped or changed')
        os.chmod(str(item), stat.S_IRUSR | stat.S_IWUSR)
        item.unlink()
    for item in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        if parent.resolve() not in item.resolve().parents or _linked(item):
            raise ValueError('retention directory escaped')
        # Nonempty/changed directories fail and survive; never delete unknown additions.
        item.rmdir()


def _retain(parent, keep_recent):
    candidates, skipped = [], []
    with os.scandir(str(parent)) as entries:
        for index, entry in enumerate(entries):
            if index >= 1000:
                return {'removed': [], 'preserved_unverified': skipped,
                        'warning': 'retention inspection limit reached; no deletion performed'}
            if not entry.is_dir(follow_symlinks=False):
                continue
            try:
                info = verify_snapshot(Path(entry.path))
                if not info['pinned']:
                    candidates.append((info['created_at'], entry.name, Path(entry.path)))
            except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
                skipped.append(entry.name)
    removed = []
    for _, name, path in sorted(candidates, reverse=True)[keep_recent:]:
        _remove_owned_snapshot(parent, path)
        removed.append(name)
    return {'removed': removed, 'preserved_unverified': skipped}


def create_snapshot(root, manifest, name, keep_recent=5, now=None):
    root = Path(root).absolute()
    if not root.is_dir() or _linked(root):
        raise ValueError('task root must be a real existing directory')
    if not isinstance(manifest, dict) or not isinstance(manifest.get('files'), list) or not manifest['files']:
        raise ValueError('snapshot needs an explicit nonempty files list')
    data_files = manifest.get('data_files', [])
    if not isinstance(data_files, list):
        raise ValueError('data_files must be an explicit hash-only list')
    if type(keep_recent) is not int or keep_recent < 1 or keep_recent > 100:
        raise ValueError('keep_recent must be between 1 and 100')
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}|최종', name):
        raise ValueError('snapshot name must be a short plain identifier')
    if len(manifest['files']) + len(data_files) > MAX_FILES:
        raise ValueError('snapshot file-count limit exceeded')
    source_paths, identities = {}, set()
    for relative in manifest['files'] + data_files:
        path = _safe(root, relative)
        rel = Path(relative)
        parts = tuple(part.lower() for part in rel.parts)
        if '.git' in parts or '.agents' in parts or (parts[0] == '.hackathon-kit' and (len(parts) < 2 or parts[1] != 'run')):
            raise ValueError('helper/source metadata or snapshots cannot be snapshotted')
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError('manifest lists a directory/special file; enumerate only intended files')
        identity = os.path.normcase(str(path.resolve()))
        if identity in identities:
            raise ValueError('duplicate or overlapping copied/hash-only file')
        identities.add(identity)
        source_paths[relative] = path
    parent = _safe(root, '.hackathon-kit/snapshots', must_exist=False)
    parent.mkdir(parents=True, exist_ok=True)
    instant = now if now is not None else datetime.now(timezone.utc)
    if isinstance(instant, str):
        instant = datetime.fromisoformat(instant.replace('Z', '+00:00'))
    if not isinstance(instant, datetime) or instant.tzinfo is None:
        raise ValueError('snapshot observation time needs an explicit timezone')
    stamp = instant.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    snapshot_id = stamp + '_' + name + '_' + uuid.uuid4().hex[:10]
    staging = parent / ('.building-' + uuid.uuid4().hex)
    staging.mkdir()
    record = {'version': 1, 'kind': KIND, 'snapshot_id': snapshot_id, 'name': name,
              'created_at': instant.astimezone(timezone.utc).isoformat(),
              'pinned': name.upper() in PINNED, 'files': {}, 'data_files': {}}
    total = 0
    # A failed attempt is left as its unique .building directory, never mistaken
    # for a verified snapshot or recursively deleted with unknown contents.
    for relative in manifest['files']:
        destination = _safe(staging, 'files/' + relative, must_exist=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        item = _read_regular(source_paths[relative], MAX_FILE_BYTES, destination)
        total += item['bytes']
        if total > MAX_TOTAL_BYTES:
            raise ValueError('snapshot total-byte limit exceeded')
        record['files'][Path(relative).as_posix()] = item
    for relative in data_files:
        item = _read_regular(source_paths[relative], MAX_FILE_BYTES)
        total += item['bytes']
        if total > MAX_TOTAL_BYTES:
            raise ValueError('snapshot total-byte limit exceeded')
        record['data_files'][Path(relative).as_posix()] = item
    marker = staging / 'MANIFEST.json'
    encoded = (json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
    if len(encoded) > RECORD_LIMIT:
        raise ValueError('snapshot manifest exceeds record limit')
    marker.write_bytes(encoded)
    final = parent / snapshot_id
    staging.rename(final)
    files, directories = _walk(final)
    for item in files:
        _set_readonly(item)
    for item in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        _set_readonly(item, directory=True)
    result = verify_snapshot(final)
    result['retention'] = _retain(parent, keep_recent)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('create')
    create.add_argument('--root', type=Path, required=True)
    create.add_argument('--manifest', type=Path, required=True)
    create.add_argument('--name', required=True)
    create.add_argument('--keep-recent', type=int, default=5)
    verify = sub.add_parser('verify')
    verify.add_argument('--snapshot', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'create':
            result = create_snapshot(args.root, _read_json(args.manifest), args.name, args.keep_recent)
        else:
            result = verify_snapshot(args.snapshot)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError) as error:
        print('SNAPSHOT FAIL: ' + str(error))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
