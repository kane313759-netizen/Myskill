#!/usr/bin/env python3
"""Small stdlib helpers for the additive v2.7 layer; no network or role authority."""
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import tempfile

RECORD_LIMIT = 2 * 1024 * 1024
FILE_LIMIT = 64 * 1024 * 1024


class V27Error(ValueError):
    pass


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise V27Error('duplicate JSON key: ' + key)
        value[key] = item
    return value


def _no_links(path):
    path = Path(path).absolute()
    for current in (path,) + tuple(path.parents):
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if current.is_symlink() or getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400):
            raise V27Error('linked/reparse paths are not allowed: ' + str(current))
    return path


def safe_path(root, relative, must_exist=True):
    root = _no_links(root)
    if not isinstance(relative, str) or not relative.strip():
        raise V27Error('explicit task-relative path required')
    rel = Path(relative)
    if rel.is_absolute() or PureWindowsPath(relative).drive or '..' in rel.parts or any(ord(c) < 32 for c in relative):
        raise V27Error('path must stay within the selected root')
    target = _no_links(root / rel)
    if root.resolve() not in target.resolve().parents:
        raise V27Error('path resolves outside or to the selected root')
    if must_exist and not target.exists():
        raise V27Error('required file is missing: ' + relative)
    return target


def read_bytes(path, limit=RECORD_LIMIT):
    path = _no_links(path)
    if type(limit) is not int or limit < 1:
        raise V27Error('positive byte bound required')
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
        raise V27Error('record must be a bounded regular file: ' + str(path))
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(str(path), flags)
    with os.fdopen(descriptor, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise V27Error('opened record is not regular')
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise V27Error('record exceeds its byte bound')
    return data


def read_json(path, limit=RECORD_LIMIT):
    return json.loads(read_bytes(path, limit).decode('utf-8-sig'), object_pairs_hook=_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(V27Error('non-finite JSON is not allowed')))


def extract_json_document(path):
    text = read_bytes(path).decode('utf-8-sig')
    if Path(path).suffix.lower() == '.json':
        return json.loads(text, object_pairs_hook=_object, parse_constant=lambda x: (_ for _ in ()).throw(V27Error('non-finite JSON is not allowed')))
    blocks = re.findall(r'^```json\s*\n(.*?)^```\s*$', text, re.M | re.S)
    if len(blocks) != 1:
        raise V27Error('document needs exactly one machine-readable JSON block')
    return json.loads(blocks[0], object_pairs_hook=_object, parse_constant=lambda x: (_ for _ in ()).throw(V27Error('non-finite JSON is not allowed')))


def sha256_file(path, max_bytes=FILE_LIMIT):
    return hashlib.sha256(read_bytes(path, max_bytes)).hexdigest()


def atomic_json(path, value):
    path = _no_links(path)
    encoded = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode('utf-8')
    if len(encoded) > FILE_LIMIT:
        raise V27Error('output record exceeds byte bound')
    path.parent.mkdir(parents=True, exist_ok=True)
    _no_links(path.parent)
    fd, temporary = tempfile.mkstemp(prefix='.v27-', suffix='.json', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(encoded)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def check_protected(source):
    source = Path(source).absolute()
    manifest = read_json(source / 'references/v27-baseline.json')
    if not isinstance(manifest, dict) or not isinstance(manifest.get('files'), dict) or not manifest['files']:
        raise V27Error('protected baseline manifest missing')
    errors = []
    for relative, expected in manifest['files'].items():
        try:
            if sha256_file(safe_path(source, relative)) != expected:
                errors.append('protected baseline changed: ' + relative)
        except (OSError, ValueError) as error:
            errors.append(str(error))
    return errors
