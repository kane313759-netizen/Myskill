#!/usr/bin/env python3
"""Bounded offline inventory of task manifests; never executes discovered commands."""
from __future__ import annotations

import argparse
from collections import deque
import fnmatch
import json
import os
from pathlib import Path


PRUNED = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".agents", ".hackathon-kit"}
MANIFESTS = {
    "package.json", "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock",
    "Makefile", "makefile", "CMakeLists.txt", "Cargo.toml", "go.mod", "go.work",
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "pytest.ini", "tox.ini", "setup.cfg", "setup.py", "README.md", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    ".env.example", ".env.sample", "Taskfile.yml", "Justfile", "justfile",
}
MARKERS = ("jest.config.*", "vitest.config.*", "webpack.config.*", "Dockerfile.*", "*.csproj", "*.sln")
GRADERS = {"grader", "grade", "grading", "evaluate", "evaluation", "run", "test", "tests", "check"}


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def depth_value(value):
    number = int(value)
    if not 0 <= number <= 8:
        raise argparse.ArgumentTypeError("must be between 0 and 8")
    return number


def is_marker(name):
    if name in MANIFESTS or any(fnmatch.fnmatchcase(name, pattern) for pattern in MARKERS):
        return True
    path = Path(name)
    stem = path.stem.lower()
    return path.suffix.lower() in {".sh", ".ps1", ".py", ".bat", ".cmd"} and (
        stem in GRADERS or stem.startswith(("grader_", "grade_", "test_", "check_", "evaluate_"))
    )


def inventory(root, max_depth=2, max_dirs=256, max_files=2000, max_entries=10000):
    """Return sorted marker paths plus explicit completeness information."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("root must be an existing directory")
    pending = deque([(root, 0)])
    markers = []
    visited_dirs = files = entries = 0
    notices = []
    while pending:
        directory, depth = pending.popleft()
        if visited_dirs >= max_dirs:
            notices.append("directory budget reached")
            break
        visited_dirs += 1
        batch = []
        try:
            with os.scandir(directory) as iterator:
                for item in iterator:
                    if entries >= max_entries:
                        notices.append("entry budget reached")
                        break
                    entries += 1
                    batch.append(item)
        except OSError as error:
            notices.append("unreadable directory: " + str(directory.relative_to(root)) + " (" + type(error).__name__ + ")")
            continue
        for item in sorted(batch, key=lambda entry: entry.name):
            try:
                if item.is_symlink():
                    continue
                if item.is_dir(follow_symlinks=False):
                    if item.name not in PRUNED and depth < max_depth:
                        pending.append((Path(item.path), depth + 1))
                    continue
                if not item.is_file(follow_symlinks=False):
                    continue
                if files >= max_files:
                    notices.append("file budget reached")
                    break
                files += 1
                if is_marker(item.name):
                    markers.append(Path(item.path).relative_to(root).as_posix())
            except OSError as error:
                notices.append("unreadable entry: " + item.name + " (" + type(error).__name__ + ")")
        if entries >= max_entries or files >= max_files:
            if files >= max_files and "file budget reached" not in notices:
                notices.append("file budget reached")
            break
    return sorted(markers), {"directories": visited_dirs, "files": files, "entries": entries}, sorted(set(notices))


def script_names(path, max_bytes=65536):
    """Expose script keys only, never command bodies, secrets, or arbitrary file text."""
    try:
        with path.open("rb") as handle:
            content = handle.read(max_bytes + 1)
        if len(content) > max_bytes:
            return None, "package.json exceeds metadata read limit"
        data = json.loads(content.decode("utf-8-sig"))
        scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
        if not isinstance(scripts, dict):
            return None, "package.json scripts is not an object"
        names = sorted(str(key) for key in scripts)
        if len(names) > 100:
            return names[:100], "script-name limit reached"
        return names, None
    except (OSError, UnicodeError, ValueError) as error:
        return None, "cannot inspect script names: " + type(error).__name__


def render(root, markers, counts, notices, max_output_bytes):
    def lines():
        yield "PROJECT\t" + json.dumps(str(Path(root).resolve()), ensure_ascii=False)
        yield "NOTE\tInventory only; inspect original task, grading and submission evidence before choosing commands."
        yield "NOTE\tNo discovered command is executed; environment-file contents and script bodies are not printed."
        for marker in markers:
            yield "FOUND\t" + json.dumps(marker, ensure_ascii=False)
            if Path(marker).name == "package.json":
                names, warning = script_names(Path(root) / marker)
                if names is not None:
                    yield "SCRIPT_NAMES\t" + json.dumps(names, ensure_ascii=False)
                if warning:
                    yield "NOTE\t" + json.dumps(marker + ": " + warning, ensure_ascii=False)
        yield "SCANNED\t" + json.dumps(counts, sort_keys=True)
        for notice in notices:
            yield "TRUNCATED_OR_UNREADABLE\t" + json.dumps(notice, ensure_ascii=False)
    result = []
    used = 0
    marker = "TRUNCATED\toutput byte budget reached\n"
    reserve = len(marker.encode("utf-8"))
    for line in lines():
        encoded = (line + "\n").encode("utf-8")
        if used + len(encoded) + reserve > max_output_bytes:
            result.append(marker)
            return "".join(result)
        result.append(line + "\n")
        used += len(encoded)
    return "".join(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--max-depth", type=depth_value, default=2, help="subdirectory depth, 0 to 8 (default: 2)")
    parser.add_argument("--max-dirs", type=positive, default=256)
    parser.add_argument("--max-files", type=positive, default=2000)
    parser.add_argument("--max-entries", type=positive, default=10000)
    parser.add_argument("--max-output-bytes", type=positive, default=16384)
    args = parser.parse_args()
    if args.max_output_bytes < 128:
        parser.error("--max-output-bytes must be at least 128")
    try:
        markers, counts, notices = inventory(args.root, args.max_depth, args.max_dirs, args.max_files, args.max_entries)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")
    print(render(args.root, markers, counts, notices, args.max_output_bytes), end="")


if __name__ == "__main__":
    main()
