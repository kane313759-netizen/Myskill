#!/usr/bin/env python3
"""Build a deterministic single-layer distribution ZIP from kit source files only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile


ROOT_FILES = {
    "README.md", "EXAM_POLICY.md", "FINALS_POLICY.md", "BOOTSTRAP_PROMPT.md", "CALLING.md", "AGENTS.snippet.md",
    "VERSION", "LICENSE", "LICENSE.md", "CHANGELOG.md", "RELEASE_NOTES.md", ".gitignore",
    "requirements-dev.txt", ".gitattributes",
}
# Keep the distribution contract explicit; importing source helpers would execute
# the checkout being packaged. Tests keep this aligned with the installer contract.
CORE_SKILLS = (
    "hackathon-orchestrator", "hackathon-finals", "grader-intake", "immutable-inventory", "task-router",
    "problem-intake", "constraint-discovery", "verification", "final-explain", "followup-prep",
)
REQUIRED = {
    "install.sh", "install.ps1", "README.md", "EXAM_POLICY.md", "FINALS_POLICY.md", "VERSION",
    "BOOTSTRAP_PROMPT.md", "CALLING.md", "AGENTS.snippet.md",
}
REQUIRED.update(".agents/skills/" + name + "/SKILL.md" for name in CORE_SKILLS)
REQUIRED.update("scripts/" + name for name in (
    "kit_lifecycle.py", "gate_check.py", "doctor.sh", "doctor.ps1", "clean.sh", "clean.ps1",
    "local_score.py", "data_io.py", "profile_data.py", "sanity_check.py", "env_scan.py",
    "test_summary.py", "tool_inventory.py", "package_release.py",
))
REQUIRED.update("templates/" + name for name in (
    "AI_FAILURES.md", "BASELINE.md", "CONSTRAINTS.md", "CP1_RED.md", "CP1_REVIEW.json",
    "DECISIONS.md", "EDGE_CASES.md", "FOLLOWUP_CHEATSHEET.md", "GRADER.md", "HANDOFF.md",
    "HUMAN_JUDGMENT.md", "IMMUTABLES.md", "LIMITATIONS.md", "LOCAL_RUBRIC.json", "FINALS_RUN.md",
    "SPEC_DRAFT.md", "STATE.md", "SYSTEM_MAP.md", "TASK_EVIDENCE.md", "VERIFY.md",
))
REQUIRED.update("prompts/" + name + ".md" for name in (
    "CODE_RED", "CONSTRAINT_RED", "ESCALATE_SOL", "MAIN_SOL", "RECORDER", "TUTOR",
))
REQUIRED.update("references/" + name + ".md" for name in (
    "constraint-matrix", "followup-question-bank", "local-evaluation", "model-policy", "finals-playbook",
    "optional-tools", "task-types",
))


def permitted(name):
    path = PurePosixPath(name)
    parts = path.parts
    if path.is_absolute() or not parts or any(part in {"..", ".git", "__pycache__", ".hackathon-kit", "node_modules", ".venv"} for part in parts):
        return False
    if name in ROOT_FILES or name in {"install.sh", "install.ps1"}:
        return True
    if len(parts) == 2 and parts[0] == "scripts" and path.suffix in {".py", ".sh", ".ps1"}:
        return True
    if len(parts) >= 2 and parts[0] == "tests" and path.suffix == ".py":
        return True
    if len(parts) == 2 and parts[0] in {"prompts", "references"} and path.suffix == ".md":
        return True
    if len(parts) == 2 and parts[0] == "templates" and path.suffix in {".md", ".json"}:
        return True
    if len(parts) == 3 and parts[:2] == (".github", "workflows") and path.suffix in {".yml", ".yaml"}:
        return True
    return len(parts) >= 4 and parts[:2] == (".agents", "skills") and path.suffix == ".md"


def archive_source_paths(source):
    """Inspect distribution roots only, with a finite traversal budget."""
    roots = {"scripts", "tests", "prompts", "references", "templates", ".agents", ".github"}
    candidates = []
    pending = [(source, 0)]
    examined = 0
    while pending:
        directory, depth = pending.pop()
        with os.scandir(directory) as iterator:
            for item in iterator:
                examined += 1
                if examined > 50000:
                    raise ValueError("distribution source scan exceeds entry limit")
                path = Path(item.path)
                relative = path.relative_to(source)
                if item.is_dir(follow_symlinks=False):
                    if item.is_symlink() or item.name in {".git", ".hackathon-kit", "__pycache__", "node_modules", ".venv"}:
                        continue
                    if (depth == 0 and item.name in roots) or (0 < depth < 8 and relative.parts[0] in roots):
                        pending.append((path, depth + 1))
                elif permitted(relative.as_posix()):
                    candidates.append(relative.as_posix())
    return candidates


def source_paths(source, include_untracked=False):
    """Git checkout: tracked paths, including working changes. ZIP source: allowlisted paths."""
    git = shutil.which("git")
    # The root prefix is empty: inspect bytes instead of decoding a non-ASCII absolute path.
    result = subprocess.run([git, "-C", str(source), "rev-parse", "--show-prefix"], capture_output=True) if git else None
    is_checkout = result is not None and result.returncode == 0 and result.stdout in (b"", b"\n", b"\r\n")
    if is_checkout:
        command = [git, "-C", str(source), "ls-files", "--cached", "-z"]
        if include_untracked:
            command += ["--others", "--exclude-standard"]
        result = subprocess.run(command, check=True, capture_output=True)
        candidates = result.stdout.decode("utf-8").split("\0")
    else:
        candidates = archive_source_paths(source)
    return sorted({name for name in candidates if name and permitted(name) and ((source / name).exists() or (source / name).is_symlink())})


def safe_file(source, name):
    current = source
    for component in PurePosixPath(name).parts:
        current = current / component
        if current.is_symlink():
            raise ValueError("refusing symlink in distribution: " + name)
    if not current.is_file():
        raise ValueError("distribution file is missing or not regular: " + name)
    return current


def build(source, output, include_untracked=False, max_files=10000, max_file_bytes=16 * 1024 * 1024, max_total_bytes=128 * 1024 * 1024):
    source = Path(source).resolve()
    output = Path(output).absolute()
    if not source.is_dir():
        raise ValueError("source must be an existing kit directory")
    if output.suffix.lower() != ".zip":
        raise ValueError("output must have a .zip extension")
    if output.is_symlink():
        raise ValueError("refusing a symlink output path")
    paths = source_paths(source, include_untracked)
    missing = REQUIRED.difference(paths)
    if missing:
        raise ValueError("required kit files missing from package: " + ", ".join(sorted(missing)))
    if len(paths) > max_files:
        raise ValueError("distribution exceeds file-count limit")
    payload = []
    total = 0
    for name in paths:
        path = safe_file(source, name)
        if path.stat().st_size > max_file_bytes:
            raise ValueError("distribution file exceeds size limit: " + name)
        with path.open("rb") as handle:
            content = handle.read(max_file_bytes + 1)
        if len(content) > max_file_bytes:
            raise ValueError("distribution file exceeds size limit: " + name)
        total += len(content)
        if total > max_total_bytes:
            raise ValueError("distribution exceeds total size limit")
        payload.append((name, content))
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".myskill-package-", suffix=".zip", dir=output.parent)
    os.close(handle)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in payload:
                info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = ((0o100755 if name.endswith(".sh") else 0o100644) << 16)
                archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"output": str(output), "files": len(paths), "source_bytes": total, "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-untracked", action="store_true", help="also include new allowlisted source files in a Git checkout")
    args = parser.parse_args()
    try:
        result = build(args.source, args.output, args.include_untracked)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(2, "PACKAGE FAIL: " + str(error) + "\n")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
