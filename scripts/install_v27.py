#!/usr/bin/env python3
"""Install additive v2.7 through the unchanged ownership-safe baseline backend."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COMMON = runpy.run_path(str(Path(__file__).with_name('v27_common.py')))
ADDON_SKILL = 'hackathon-orchestrator-universal'
MANDATORY = ('scripts/v27_common.py', 'scripts/deadline.py', 'scripts/v27_check.py',
             'scripts/snapshot.py', 'scripts/submit_check.py', 'scripts/clean_run.py',
             'scripts/security_check.py', 'scripts/data_audit.py', 'scripts/install_v27.py',
             'references/v27-baseline.json', 'references/v27-contract.md',
             'references/v27-r81-map.md', 'templates/ENV.md', 'templates/EXAM_POLICY_FINAL.md',
             'templates/DATA_AUDIT.md', 'templates/SAFETY_TESTS.md', 'templates/STUDY_BRIEF.md',
             'templates/V27_STATE.json', 'templates/V27_EVIDENCE.json')


def install(source, target, allow_internal_source=False):
    source, target = Path(source).absolute(), Path(target).absolute()
    errors = COMMON['check_protected'](source)
    for rel in MANDATORY:
        try:
            COMMON['read_bytes'](COMMON['safe_path'](source, rel))
        except (OSError, ValueError) as error:
            errors.append(str(error))
    skill_rel = '.agents/skills/' + ADDON_SKILL + '/SKILL.md'
    expected = COMMON['sha256_file'](COMMON['safe_path'](source, skill_rel))
    destination = COMMON['safe_path'](target, skill_rel, must_exist=False)
    if destination.exists() and COMMON['sha256_file'](destination) != expected:
        # Baseline has no required-name entry for this newly added skill. Fail
        # before its otherwise optional collision handling could silently skip it.
        errors.append('Unverified/locally changed universal skill preserved; resolve this collision before installing.')
    if errors:
        raise ValueError('; '.join(errors))
    backend = runpy.run_path(str(source / 'scripts/kit_lifecycle.py'), run_name='v27_baseline_lifecycle')
    lookup_root = target
    while not lookup_root.exists():
        lookup_root = lookup_root.parent
    context = backend['git_context'](lookup_root)
    if context:
        COMMON['_no_links'](context[1])
    # Validate every planned destination before the unchanged backend can write.
    # Windows junctions require a reparse check in addition to is_symlink().
    COMMON['_no_links'](target / '.hackathon-kit')
    COMMON['_no_links'](target / '.agents/skills')
    for directory in backend['SUPPORT_DIRS']:
        for relative in backend['files_under'](source / directory, exclude_cache=True):
            rel = directory + '/' + relative
            COMMON['safe_path'](source, rel)
            COMMON['safe_path'](target, '.hackathon-kit/' + rel, must_exist=False)
    for rel in backend['SUPPORT_FILES']:
        COMMON['safe_path'](target, '.hackathon-kit/' + rel, must_exist=False)
    for skill in (source / '.agents/skills').iterdir():
        COMMON['_no_links'](target / '.agents/skills' / skill.name)
        for relative in backend['files_under'](skill):
            COMMON['safe_path'](target, '.agents/skills/' + skill.name + '/' + relative, must_exist=False)
    for rel in ('manifest.json', 'run/INSTALLED_SKILLS.txt', 'run/LAST_10_MINUTES.md'):
        COMMON['safe_path'](target, '.hackathon-kit/' + rel, must_exist=False)
    templates = list((source / 'templates').iterdir())
    existing_templates = target / '.hackathon-kit/templates'
    COMMON['_no_links'](existing_templates)
    if existing_templates.exists():
        templates += list(existing_templates.iterdir())
    for template in templates:
        COMMON['_no_links'](template)
        COMMON['safe_path'](target, '.hackathon-kit/run/' + template.name, must_exist=False)
    backend['install'](source, target, allow_internal_source=allow_internal_source)
    kit = target / '.hackathon-kit'
    manifest = COMMON['read_json'](kit / 'manifest.json')
    for rel in MANDATORY:
        if COMMON['sha256_file'](kit / rel) != COMMON['sha256_file'](source / rel):
            raise ValueError('Add-on support file is locally changed or incomplete: ' + rel)
        if rel not in manifest['managed_files']:
            raise ValueError('Add-on file ownership was not recorded: ' + rel)
    if backend['tree_digest'](target / '.agents/skills' / ADDON_SKILL) != backend['tree_digest'](source / '.agents/skills' / ADDON_SKILL):
        raise ValueError('Universal skill identity mismatch after install')
    if COMMON['check_protected'](source):
        raise ValueError('Baseline source changed during installation')
    return {'status': 'INSTALLED', 'addon_version': '2.7',
            'baseline_version': manifest['version'], 'source_digest': manifest['source_digest'],
            'target': str(target), 'limits': 'Installation integrity only; no exam gate, runtime model or submission approval.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT)
    parser.add_argument('--target', type=Path, default=Path.cwd())
    parser.add_argument('--allow-internal-source', action='store_true')
    args = parser.parse_args()
    try:
        result = install(args.source, args.target, args.allow_internal_source)
    except (OSError, ValueError, UnicodeError, KeyError, RuntimeError) as error:
        print('V27 INSTALL FAIL: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
