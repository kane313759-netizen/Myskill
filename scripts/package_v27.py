#!/usr/bin/env python3
"""Package the baseline plus additive v2.7 without editing baseline allowlists."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMON = runpy.run_path(str(Path(__file__).with_name('v27_common.py')))
EXTRAS = ('R81_MAP.md', 'V27_ADDON.md', 'references/v27-baseline.json')


def build(source, output, include_untracked=False):
    source, output = Path(source).absolute(), Path(output).absolute()
    errors = COMMON['check_protected'](source)
    if errors:
        raise ValueError('; '.join(errors))
    if output.suffix.lower() != '.zip' or output.is_symlink():
        raise ValueError('a regular .zip output is required')
    for rel in EXTRAS:
        COMMON['read_bytes'](COMMON['safe_path'](source, rel))
    installer = runpy.run_path(str(source / 'scripts/install_v27.py'), run_name='v27_install_contract')
    for rel in installer['MANDATORY']:
        COMMON['read_bytes'](COMMON['safe_path'](source, rel))
    if not (source / '.agents/skills/hackathon-orchestrator-universal/SKILL.md').is_file():
        raise ValueError('universal skill missing')
    base = runpy.run_path(str(source / 'scripts/package_release.py'), run_name='v27_base_packager')
    with tempfile.TemporaryDirectory(prefix='v27-package-') as temporary:
        intermediate = Path(temporary) / 'base.zip'
        base['build'](source, intermediate, include_untracked=include_untracked)
        with zipfile.ZipFile(intermediate) as archive:
            payload = {item.filename: archive.read(item) for item in archive.infolist()}
        for rel in EXTRAS:
            payload[rel] = COMMON['read_bytes'](COMMON['safe_path'](source, rel))
        required = set(installer['MANDATORY']) | set(EXTRAS) | {'.agents/skills/hackathon-orchestrator-universal/SKILL.md'}
        missing = required - set(payload)
        if missing:
            raise ValueError('Add-on files are untracked or missing from package; commit them or explicitly use --include-untracked: ' + ', '.join(sorted(missing)))
        # The baseline packager intentionally excludes JSON references. This one
        # explicitly adds the protected-file manifest instead of relaxing its rules.
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary_output = Path(temporary) / 'final.zip'
        with zipfile.ZipFile(temporary_output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(payload.items()):
                info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = ((0o100755 if name.endswith('.sh') else 0o100644) << 16)
                archive.writestr(info, data)
        # Atomic write at destination, including a cross-volume source scratch.
        data = temporary_output.read_bytes()
        import os
        fd, staged = tempfile.mkstemp(prefix='.v27-package-', suffix='.zip', dir=output.parent)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data)
            os.replace(staged, output)
        finally:
            if os.path.exists(staged):
                os.unlink(staged)
    return {'output': str(output), 'files': len(payload), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'baseline_preserved': True, 'addon_version': '2.7'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-untracked', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.source, args.output, args.include_untracked), ensure_ascii=True))
    except (OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile) as error:
        print('V27 PACKAGE FAIL: ' + str(error))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
