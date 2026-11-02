#!/usr/bin/env python3
"""Observe a few optional PATH candidates without executing or importing them.

Python 3.8+ standard library only. This is an inventory, not a tool selector:
PATH presence establishes neither identity, version, compatibility, nor approval.
"""

import argparse
import json
import os
import shutil
import sys


COMMANDS = ("jq", "gitleaks", "ruff", "duckdb")
PYTHON_PACKAGES = ("duckdb", "pdfplumber")
MAX_PATH_ENTRIES = 128
MAX_PATH_CHARACTERS = 32768
MAX_PATHEXT_SUFFIXES = 16
MAX_PATHEXT_CHARACTERS = 2048


def bounded_path():
    """Supply only a fixed-size PATH prefix, keeping complete directory entries."""
    value = os.environ.get("PATH", os.defpath)
    truncated = len(value) > MAX_PATH_CHARACTERS
    prefix = value[:MAX_PATH_CHARACTERS]
    if truncated and value[MAX_PATH_CHARACTERS] != os.pathsep:
        prefix, separator, _ = prefix.rpartition(os.pathsep)
        entries = prefix.split(os.pathsep, MAX_PATH_ENTRIES) if separator else []
    else:
        entries = prefix.split(os.pathsep, MAX_PATH_ENTRIES) if prefix else []
    truncated = truncated or len(entries) > MAX_PATH_ENTRIES
    entries = entries[:MAX_PATH_ENTRIES]
    path = os.pathsep.join(entries)
    # A complete empty entry denotes cwd, while which(path="") searches nothing.
    if entries == [""]:
        path = os.curdir
    return path, {
        "max_entries": MAX_PATH_ENTRIES,
        "max_characters": MAX_PATH_CHARACTERS,
        "entries_supplied": len(entries),
        "characters_supplied": len(path),
        "truncated": truncated,
        "native_which_may_add_cwd": sys.platform == "win32",
        "cwd_policy": (
            "Native Windows shutil.which policy may also search cwd."
            if sys.platform == "win32" else
            "Only supplied PATH entries; empty entries can denote cwd."
        ),
    }


def windows_pathext_scope():
    """Skip native Windows lookup if its environment suffix expansion is too large."""
    scope = {
        "applies": sys.platform == "win32",
        "max_suffixes": MAX_PATHEXT_SUFFIXES,
        "max_characters": MAX_PATHEXT_CHARACTERS,
        "limit_exceeded": False,
        "native_lookup_skipped": False,
    }
    if scope["applies"]:
        value = os.environ.get("PATHEXT", "")
        scope["source"] = "environment" if value else "native_default_or_empty"
        scope["limit_exceeded"] = (
            len(value) > MAX_PATHEXT_CHARACTERS or
            len(value.split(os.pathsep, MAX_PATHEXT_SUFFIXES)) > MAX_PATHEXT_SUFFIXES
        )
        scope["native_lookup_skipped"] = scope["limit_exceeded"]
    return scope


def task_local_candidate(candidate_path, task_root):
    """Conservatively flag a local PATH entry or a target resolving into the task.

    This classification does not read candidate contents or establish provenance.
    An entry inside the task remains local even if it links outside the task.
    """
    try:
        entry_local = os.path.commonpath((candidate_path, task_root)) == task_root
        real_root = os.path.realpath(task_root)
        target_local = os.path.commonpath(
            (os.path.realpath(candidate_path), real_root)
        ) == real_root
        return entry_local or target_local
    except (OSError, ValueError):
        return None


def inventory(task_root=None):
    """Return bounded availability observations; never run a candidate or import it."""
    root = os.path.abspath(task_root if task_root is not None else os.getcwd())
    search_path, path_scope = bounded_path()
    pathext_scope = windows_pathext_scope()
    commands = []
    for name in COMMANDS:
        item = {
            "name": name,
            "status": "UNKNOWN",
            "candidate_path": None,
            "task_local_candidate": None,
            "provenance_review_required": None,
        }
        if pathext_scope["native_lookup_skipped"]:
            item["reason"] = "Windows PATHEXT exceeds inventory limits; native lookup skipped."
            commands.append(item)
            continue
        try:
            candidate = shutil.which(name, path=search_path)
        except (OSError, ValueError):
            item["reason"] = "PATH lookup could not be completed."
        else:
            if candidate is None:
                if path_scope["truncated"]:
                    item["reason"] = "No candidate found in the bounded PATH prefix; search truncated."
                else:
                    item["status"] = "NOT_FOUND"
                    item["reason"] = "No executable candidate found on the current PATH."
            else:
                path = os.path.abspath(candidate)
                item.update(
                    status="PATH_CANDIDATE",
                    candidate_path=path,
                    task_local_candidate=task_local_candidate(path, root),
                    provenance_review_required=True,
                )
        commands.append(item)
    return {
        "inventory_only": True,
        "selection_performed": False,
        "approval_granted": False,
        "task_root": root,
        "path_scope": path_scope,
        "windows_pathext_scope": pathext_scope,
        "notice": (
            "PATH presence does not establish identity, version, compatibility, "
            "or approval. Every candidate needs provenance review, including "
            "task-local candidates. No candidate executable is run and no "
            "candidate Python package is imported."
        ),
        "commands": commands,
        "python_packages": [
            {
                "name": name,
                "status": "UNKNOWN",
                "reason": "Package availability is not probed; imports can execute code.",
            }
            for name in PYTHON_PACKAGES
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task-root",
        help="Classify task-local PATH candidates relative to this directory (default: cwd).",
    )
    args = parser.parse_args(argv)
    print(json.dumps(inventory(args.task_root), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
