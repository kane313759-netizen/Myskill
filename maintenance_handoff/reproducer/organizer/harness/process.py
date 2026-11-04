"""Bounded local process runner for the isolated release-trial grader.

The caller supplies a fixed command and fresh working directory.  This module
does not discover submissions, copy a candidate's parent, or provide a security
sandbox.  Linux /proc observations are sampled and can miss short-lived peaks.
"""

import errno
import math
import os
import selectors
import signal
import stat
import subprocess
import tempfile
import time

try:
    import resource
except ImportError:  # The release environment is Linux; retained for diagnostics.
    resource = None


RSS_LIMIT_KIB = 768 * 1024
OUTPUT_TMP_LIMIT = 2 * 1024 ** 3
_CHUNK = 64 * 1024


def _regular_tree(root, excluded=()):
    """Yield (relative path, stat) without following links or opening special files."""
    excluded = set(excluded)
    pending = [(root, "")]
    while pending:
        directory, prefix = pending.pop()
        try:
            entries = os.scandir(directory)
        except OSError:
            continue
        with entries:
            for entry in entries:
                relative = prefix + entry.name
                if entry.path in excluded:
                    continue
                try:
                    info = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                if stat.S_ISDIR(info.st_mode):
                    pending.append((entry.path, relative + "/"))
                elif stat.S_ISREG(info.st_mode):
                    yield relative, info


def _growth_scan(root, baseline, excluded):
    total = 0
    count = 0
    for name, info in _regular_tree(root, excluded):
        previous = baseline.get(name)
        if previous and previous[:2] == (info.st_dev, info.st_ino):
            total += max(0, info.st_size - previous[2])
        else:
            total += info.st_size
        count += 1
        if count % 128 == 0:
            yield total
    yield total


def _processes():
    """Return pid -> (ppid, process group, start ticks, resident KiB)."""
    rows = {}
    try:
        entries = os.scandir("/proc")
    except OSError:
        return rows
    with entries:
        for entry in entries:
            if not entry.name.isdecimal():
                continue
            try:
                with open(entry.path + "/stat", "r", encoding="ascii") as source:
                    fields = source.read(8192).rsplit(")", 1)[1].split()
                pid = int(entry.name)
                rss = max(0, int(fields[21])) * os.sysconf("SC_PAGE_SIZE") // 1024
                rows[pid] = (int(fields[1]), int(fields[2]), int(fields[19]), rss)
            except (OSError, ValueError, IndexError):
                continue
    return rows


def _family(rows, group, known):
    alive = {pid for pid, row in rows.items()
             if row[1] == group or known.get(pid) == row[2]}
    while True:
        more = {pid for pid, row in rows.items() if row[0] in alive}
        if more <= alive:
            break
        alive.update(more)
    for pid in alive:
        known[pid] = rows[pid][2]
    return alive


def _stop(group, known, sig):
    try:
        os.killpg(group, sig)
    except (ProcessLookupError, PermissionError):
        pass
    # Also clean up an observed descendant that created another process group.
    rows = _processes()
    for pid, start in tuple(known.items()):
        if pid in rows and rows[pid][2] == start:
            try:
                os.kill(pid, sig)
            except (ProcessLookupError, PermissionError):
                pass


def run(cmd, cwd, timeout, logdir, *, observe_root=None):
    """Run a command with bounded streamed logs and return observed evidence.

    The 2 GiB cap covers captured stdout/stderr plus newly created or grown
    regular files under observe_root (cwd by default), including the private
    TMPDIR when it is within that root.  Pre-existing input files form a
    baseline.  Both limits and elapsed time are observed; disk/RSS sampling is
    not a hard kernel quota.  No output artifact is deleted.
    """
    if isinstance(cmd, (str, bytes)) or not cmd:
        raise TypeError("cmd must be a nonempty argument sequence")
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    cmd = [os.fspath(part) for part in cmd]
    cwd = os.path.abspath(os.fspath(cwd))
    logdir = os.path.abspath(os.fspath(logdir))
    observe_root = cwd if observe_root is None else os.path.abspath(os.fspath(observe_root))
    os.makedirs(logdir, mode=0o700, exist_ok=True)
    for directory in (cwd, logdir, observe_root):
        mode = os.lstat(directory).st_mode
        if not stat.S_ISDIR(mode):
            raise ValueError("cwd, logdir and observe_root must be real directories")

    out_fd, out_name = tempfile.mkstemp(prefix="stdout-", suffix=".log", dir=logdir)
    err_fd, err_name = tempfile.mkstemp(prefix="stderr-", suffix=".log", dir=logdir)
    logs = {"stdout": os.fdopen(out_fd, "wb"), "stderr": os.fdopen(err_fd, "wb")}
    excluded = (out_name, err_name)
    baseline = {name: (info.st_dev, info.st_ino, info.st_size)
                for name, info in _regular_tree(observe_root, excluded)}
    temp_dir = tempfile.mkdtemp(prefix=".runner-tmp-", dir=cwd)
    environment = os.environ.copy()
    environment.update(TMPDIR=temp_dir, TMP=temp_dir, TEMP=temp_dir)

    def limits():
        if resource is not None:
            cpu = max(1, math.ceil(timeout))
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
            resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_TMP_LIMIT, OUTPUT_TMP_LIMIT))

    started = time.monotonic()
    process = None
    selector = selectors.DefaultSelector()
    known = {}
    stream_bytes = 0
    scratch_bytes = 0
    peak_scratch = 0
    peak_rss = 0
    root_peak_rss = 0
    rss_observed = False
    timed_out = False
    exceeded = None
    launch_error = None
    killed_at = None
    stopped_success = False
    final_disk_scan = False
    final_disk_done = False
    scanner = None
    next_process_check = started
    next_disk_check = started
    try:
        try:
            process = subprocess.Popen(
                cmd, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                start_new_session=True, preexec_fn=limits if resource is not None else None)
        except (OSError, subprocess.SubprocessError) as error:
            launch_error = type(error).__name__ + ": " + str(error)
        if process is not None:
            for name in ("stdout", "stderr"):
                pipe = getattr(process, name)
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, name)
            while True:
                now = time.monotonic()
                if now >= next_process_check:
                    rows = _processes()
                    alive = _family(rows, process.pid, known)
                    rss = sum(rows[pid][3] for pid in alive)
                    rss_observed = rss_observed or rss > 0
                    peak_rss = max(peak_rss, rss)
                    if rss > RSS_LIMIT_KIB and exceeded is None:
                        exceeded = "rss"
                    next_process_check = now + 0.10
                if scanner is not None or now >= next_disk_check:
                    if scanner is None:
                        scanner = _growth_scan(observe_root, baseline, excluded)
                        scratch_bytes = 0
                    # Incremental scanning prevents a large directory from
                    # postponing the wall-clock check for an entire traversal.
                    until = time.monotonic() + 0.025
                    try:
                        while time.monotonic() < until:
                            scratch_bytes = next(scanner)
                            peak_scratch = max(peak_scratch, scratch_bytes)
                            if scratch_bytes + stream_bytes > OUTPUT_TMP_LIMIT:
                                exceeded = exceeded or "output_tmp_bytes"
                                break
                    except StopIteration:
                        scanner = None
                        next_disk_check = now + 0.25
                        if final_disk_scan:
                            final_disk_done = True
                if process.returncode is None and hasattr(os, "wait4"):
                    try:
                        waited, status, usage = os.wait4(process.pid, os.WNOHANG)
                    except ChildProcessError:
                        waited = 0
                    if waited:
                        process.returncode = os.waitstatus_to_exitcode(status)
                        root_peak_rss = max(root_peak_rss, int(usage.ru_maxrss))
                        peak_rss = max(peak_rss, root_peak_rss)
                        rss_observed = rss_observed or root_peak_rss > 0
                        if peak_rss > RSS_LIMIT_KIB:
                            exceeded = exceeded or "rss"
                returncode = (process.returncode if hasattr(os, "wait4")
                              else process.poll())
                if returncode is None and now - started >= timeout:
                    timed_out = True
                if (timed_out or exceeded) and killed_at is None:
                    _stop(process.pid, known, signal.SIGKILL)
                    killed_at = time.monotonic()
                if returncode is not None and not stopped_success:
                    # A successful parent may leave a server/child holding the
                    # pipes.  Every phase owns and cleans up its child group.
                    _stop(process.pid, known, signal.SIGKILL)
                    stopped_success = True
                    killed_at = killed_at or time.monotonic()
                    # A fast command can finish before the next periodic disk
                    # sample.  Traverse once after termination as well.
                    final_disk_scan = True
                    final_disk_done = False
                    scanner = None
                    next_disk_check = 0
                if returncode is not None and not selector.get_map() and final_disk_done:
                    break
                if killed_at is not None and now - killed_at >= 2.0 and final_disk_done:
                    # Detached or unobserved descendants cannot keep the
                    # runner blocked forever by retaining a pipe descriptor.
                    break
                for key, _ in selector.select(0.025):
                    try:
                        block = os.read(key.fileobj.fileno(), _CHUNK)
                    except BlockingIOError:
                        continue
                    except OSError as error:
                        if error.errno not in (errno.EBADF, errno.EIO):
                            raise
                        block = b""
                    if not block:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    allowance = max(0, OUTPUT_TMP_LIMIT - stream_bytes)
                    logs[key.data].write(block[:allowance])
                    stream_bytes += len(block)
                    if stream_bytes + scratch_bytes > OUTPUT_TMP_LIMIT:
                        exceeded = exceeded or "output_tmp_bytes"
            _stop(process.pid, known, signal.SIGKILL)
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2.0)
    finally:
        if process is not None:
            _stop(process.pid, known, signal.SIGKILL)
            for name in ("stdout", "stderr"):
                pipe = getattr(process, name)
                if pipe is not None:
                    pipe.close()
        selector.close()
        for stream in logs.values():
            stream.close()

    seconds = time.monotonic() - started
    returncode = process.returncode if process is not None else None
    if returncode == -getattr(signal, "SIGXCPU", 24):
        exceeded = exceeded or "cpu"
    if returncode == -getattr(signal, "SIGXFSZ", 25):
        exceeded = exceeded or "output_tmp_bytes"
    return {
        "returncode": returncode, "seconds": seconds,
        "peak_rss_kib": peak_rss, "rss_observed": rss_observed,
        "root_peak_rss_kib": root_peak_rss,
        "timed_out": timed_out, "limit_exceeded": exceeded,
        "stdout": out_name, "stderr": err_name,
        "stdout_file": out_name, "stderr_file": err_name,
        "stream_bytes": stream_bytes, "peak_scratch_bytes": peak_scratch,
        "observed_output_tmp_bytes": stream_bytes + peak_scratch,
        "tmpdir": temp_dir, "launch_error": launch_error,
        "cmd": cmd, "cwd": cwd, "observe_root": observe_root,
        "limits": {"wall_seconds": timeout, "rss_kib": RSS_LIMIT_KIB,
                   "output_tmp_bytes": OUTPUT_TMP_LIMIT},
    }
