"""r4-3.15 regression: execution receipts written by a Windows PowerShell agent.

In eleven unattended runs every final v27_check failed with "native command is not the exact retained argv".
The agents ran kit helpers as `$env:PYTHONUTF8='1'; $env:OMP_NUM_THREADS='2'; & 'python.exe' '-I' 'helper.py' ...`.
The retained cmd was accepted only as list2cmdline/shlex.join of argv, so the environment prefix and PowerShell's
quote-every-word style were rejected, and the interpreter flag check refused `-X utf8`, the only way to turn on
UTF-8 mode under -I (which ignores PYTHONUTF8).

The receipt does not say which shell ran the command, so a command is accepted only when its meaning is the
same in every shell that could run it (PowerShell, cmd.exe, bash): each either reads exactly argv or cannot run
the line. A first fix read every command one way; review showed cmd.exe running `&`/`>` inside single quotes,
PowerShell closing a quote with a typographic quote, and bash expanding `*.probe`.
"""
import json
import os
import pathlib
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / '.agents/skills/hackathon-orchestrator-universal/SKILL.md'
CONTRACT = ROOT / 'references/v27-contract.md'
CHECK = runpy.run_path(str(ROOT / 'scripts/v27_check.py'))


def match(command, argv):
    return CHECK['command_matches'](command, argv)

WIN = [r'C:\Users\kane3\venv\Scripts\python.exe', '-I', r'C:\Users\kane3\runs\N20-t20\work\.hackathon-kit\scripts\clean_run.py',
       '--root', r'C:\Users\kane3\runs\N20-t20\work', '--plan', r'C:\Users\kane3\runs\N20-t20\work\run\clean_run_plan.json']
KOR = [r'C:\Users\kane3\OneDrive\문서\ChatGPT\해커톤\venv\Scripts\python.exe', '-X', 'utf8', '-I',
       r'C:\Users\kane3\Documents\Codex\overnight\runs\N17-t17\work\.hackathon-kit\scripts\submit_check.py',
       '--root', r'C:\Users\kane3\Documents\Codex\overnight\runs\N17-t17\work', '--rules', r'C:\작업 폴더 (v2)\run\rules.json']
POSIX = ['/opt/venv/bin/python3', '-I', '/task/.hackathon-kit/scripts/submit_check.py', '--root', '/task', '--rules', '/task/run/rules.json']
PS_PREFIX = "$env:PYTHONUTF8='1'; $env:OMP_NUM_THREADS='2'; $env:OPENBLAS_NUM_THREADS='2'; $env:MKL_NUM_THREADS='2'; "


def ps(argv):
    return '& ' + ' '.join("'" + value + "'" for value in argv)


def dq(argv):
    return ' '.join('"' + value + '"' for value in argv)


class RegressionR4315(unittest.TestCase):
    def test_01_observed_powershell_receipts_match_their_argv(self):
        self.assertTrue(match(PS_PREFIX + ps(WIN), WIN))
        self.assertTrue(match(PS_PREFIX + ps(KOR), KOR))
        self.assertTrue(match(ps(WIN), WIN))
        self.assertTrue(match('$env:PYTHONIOENCODING = "utf-8";' + ps(WIN), WIN))
        flags_bare = "& '" + WIN[0] + "' -I " + ' '.join("'" + value + "'" for value in WIN[2:])
        self.assertTrue(match(flags_bare, WIN))
        self.assertTrue(match('& ' + ' '.join(value if value.startswith('-') else '"' + value + '"' for value in WIN), WIN))

    def test_02_posix_and_neutral_shapes_match(self):
        self.assertTrue(match(' '.join(POSIX), POSIX))
        self.assertTrue(match(subprocess.list2cmdline(POSIX), POSIX))
        self.assertTrue(match(subprocess.list2cmdline(WIN), WIN))
        self.assertTrue(match('OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ' + ' '.join(POSIX), POSIX))
        spaced = ['/opt/my venv/bin/python3', '-I', '/task dir/x.py']
        self.assertTrue(match("OMP_NUM_THREADS=2 '/opt/my venv/bin/python3' -I '/task dir/x.py'", spaced))
        self.assertTrue(match("'/opt/my venv/bin/python3' -I '/task dir/x.py'", spaced))
        self.assertTrue(match(dq(spaced), spaced))
        program_files = [r'C:\Program Files\Python312\python.exe', '-I', r'C:\RnD docs\task (v2)\clean_run.py']
        self.assertTrue(match(subprocess.list2cmdline(program_files), program_files))
        self.assertTrue(match(ps(program_files), program_files))

    def test_03_reported_cross_shell_cases_are_rejected(self):
        bad = [
            # PowerShell closes a single quote with a typographic quote; cmd/bash read one word.
            ("& 'C:\\py.exe' '-I' 'C:\\x.py\u2019; Remove-Item x; \u2018'", ['C:\\py.exe', '-I', 'C:\\x.py\u2019; Remove-Item x; \u2018']),
            ("& 'C:\\py.exe' '-I' \"a\u201d; Remove-Item x; \u201cb\"", ['C:\\py.exe', '-I', 'a\u201d; Remove-Item x; \u201cb']),
            # cmd.exe does not treat single quotes as quotes: & and > run or redirect.
            ("C:\\py.exe -I C:\\h.py --root 'x & calc & '", ['C:\\py.exe', '-I', 'C:\\h.py', '--root', 'x & calc & ']),
            ("C:\\py.exe -I C:\\h.py --out 'a > b'", ['C:\\py.exe', '-I', 'C:\\h.py', '--out', 'a > b']),
            ("$env:PYTHONUTF8='1'; & C:\\py.exe -I 'C:\\h.py'", ['C:\\py.exe', '-I', 'C:\\h.py']),
            ('C:\\py.exe -I "C:\\%PATH%\\h.py"', ['C:\\py.exe', '-I', 'C:\\%PATH%\\h.py']),
            ('C:\\py.exe -I "C:\\a^b\\h.py"', ['C:\\py.exe', '-I', 'C:\\a^b\\h.py']),
            ('C:\\py.exe -I "C:\\R&D\\h.py"', ['C:\\py.exe', '-I', 'C:\\R&D\\h.py']),
            # bash expands globs, tilde and braces, and reads backslashes.
            ('/usr/bin/python3 -I /k/h.py *.probe', ['/usr/bin/python3', '-I', '/k/h.py', '*.probe']),
            ('/usr/bin/python3 -I /k/h.py ~/x', ['/usr/bin/python3', '-I', '/k/h.py', '~/x']),
            ('/usr/bin/python3 -I /k/h.py {a,b}', ['/usr/bin/python3', '-I', '/k/h.py', '{a,b}']),
            ('/usr/bin/python3 -I /k/h.py a\\b', ['/usr/bin/python3', '-I', '/k/h.py', 'a\\b']),
            ('/usr/bin/python3 -I "/k/h.py" "a\\\\b"', ['/usr/bin/python3', '-I', '/k/h.py', 'a\\\\b']),
            ("/usr/bin/python3 -I '/k/a b.py'", ['/usr/bin/python3', '-I', '/k/a b.py']),
        ]
        for command, argv in bad:
            with self.subTest(command=command):
                self.assertFalse(match(command, argv))

    def test_04_other_shell_syntax_is_rejected(self):
        bad = [
            ("$env:PATH='C:\\x'; " + ps(WIN), WIN),
            ("$env:PYTHONPATH='C:\\x'; " + ps(WIN), WIN),
            ('PYTHONPATH=/x ' + ' '.join(POSIX), POSIX),
            ("$env:OMP_NUM_THREADS='2;rm'; " + ps(WIN), WIN),
            (PS_PREFIX + ps(WIN) + '; Remove-Item x', WIN + [';', 'Remove-Item', 'x']),
            (PS_PREFIX + ps(WIN) + '; Remove-Item x', WIN),
            (PS_PREFIX + ps(WIN) + ' | Out-Null', WIN + ['|', 'Out-Null']),
            (' '.join(POSIX) + ' > out.json', POSIX + ['>', 'out.json']),
            (' '.join(POSIX) + ' && echo ok', POSIX + ['&&', 'echo', 'ok']),
            (' '.join(POSIX) + ' # --plan other.json', POSIX + ['#', '--plan', 'other.json']),
            (ps(WIN) + ' "$HOME"', WIN + ['$HOME']),
            (ps(WIN) + " 'a''b'", WIN + ["a'b"]),
            (ps(WIN) + " 'a''b'", WIN + ['ab']),
            (ps(WIN) + ' `whoami`', WIN + ['`whoami`']),
            (ps(WIN) + ' @args', WIN + ['@args']),
            (ps(WIN) + ' --% x', WIN + ['--%', 'x']),
            (ps(WIN) + " ''", WIN + ['']),                                  # Windows PowerShell drops empty words
            (ps(WIN) + " 'a\"b'", WIN + ['a"b']),                          # and mangles embedded double quotes
            (ps(WIN) + " 'C:\\dir with space\\'", WIN + ['C:\\dir with space\\']),
            (ps(WIN) + ' -Dlog.level=x', WIN + ['-Dlog.level=x']),       # PowerShell splits -name.part
            (ps(WIN) + ' -X:utf8', WIN + ['-X:utf8']),
            (ps(WIN) + " 'a\u00a0b'", WIN + ['a\u00a0b']),
            (ps(WIN) + ' 0x10', WIN + ['0x10']),                            # PowerShell numbers
            (ps(WIN) + ' +5', WIN + ['+5']),
            (ps(WIN) + ' -5', WIN + ['-5']),
            (ps(WIN) + ' .5', WIN + ['.5']),
            (ps(WIN) + ' =x', WIN + ['=x']),
            (ps(WIN) + ' --', WIN + ['--']),
            (subprocess.list2cmdline(WIN) + ' C:\\dir\\', WIN + ['C:\\dir\\']),
            ("$env:PYTHONUTF8='1'; " + "'" + WIN[0] + "' '-I'", [WIN[0], '-I']),  # no call operator: nothing runs
            (ps(WIN) + '\n' + ps(WIN), WIN),
            ('Remove-Item x; ' + ps(WIN), WIN),
            ('OMP_NUM_THREADS=2 & ' + ' '.join(POSIX), POSIX),
            (' ' + ' '.join(POSIX), POSIX),
            ('', POSIX),
        ]
        for command, argv in bad:
            with self.subTest(command=command):
                self.assertFalse(match(command, argv))

    def test_05_tokens_must_equal_argv_exactly(self):
        self.assertFalse(match(PS_PREFIX + ps(WIN[:-1] + [WIN[-1] + 'x']), WIN))
        self.assertFalse(match(PS_PREFIX + ps(WIN[:3]), WIN))
        self.assertFalse(match(PS_PREFIX + ps(WIN + ['--extra']), WIN))
        self.assertFalse(match(PS_PREFIX + ps(WIN), [WIN[0]] + ['-I', '-c', 'print(1)']))
        self.assertFalse(match(' '.join(POSIX), tuple(POSIX)))

    @unittest.skipIf(os.name == 'nt' or not shutil.which('bash'), 'needs a POSIX bash')
    def test_06_bash_reads_accepted_commands_as_argv_or_runs_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            probe = pathlib.Path(tmp) / 'probe.py'
            probe.write_text('import json, sys\nprint(json.dumps(sys.argv[1:], ensure_ascii=False))\n', encoding='utf-8')
            marker = pathlib.Path(tmp) / 'ran.txt'
            pathlib.Path(tmp, 'x.probe').write_text('', encoding='utf-8')
            words = ['--root', '/t/작업 폴더 (v2)', 'a=b', '+x', 'C:x', '@at', '#hash', 'comma,word', 'ㄱㄴ']
            argv = [sys.executable, '-I', str(probe)] + words
            accepted = [
                ('OMP_NUM_THREADS=2 ' + ' '.join("'" + value + "'" for value in argv), argv),
                (' '.join("'" + value + "'" for value in argv), argv),
                (' '.join(value if value.startswith('-') else '"' + value + '"' for value in argv), argv),
            ]
            for command, expected in accepted:
                with self.subTest(command=command):
                    self.assertTrue(match(command, expected))
                    run = subprocess.run(['bash', '-c', command], capture_output=True, text=True, cwd=tmp)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertEqual(json.loads(run.stdout), expected[3:])
            ran_marker = "touch '" + str(marker) + "'"
            powershell_only = [(PS_PREFIX + ps(argv), argv), (ps(argv), argv),
                               ("$env:PYTHONUTF8='1'; & " + ' '.join(argv[:3]), argv[:3])]
            for command, expected in powershell_only:
                with self.subTest(command=command):
                    self.assertTrue(match(command, expected))
                    run = subprocess.run(['bash', '-c', ran_marker + '; ' + command], capture_output=True, text=True, cwd=tmp)
                    self.assertNotEqual(run.returncode, 0)
                    self.assertEqual(run.stdout, '')
                    self.assertFalse(marker.exists(), 'bash ran part of a PowerShell-shaped line')

    def test_07_utf8_mode_is_the_only_extra_interpreter_flag(self):
        ok = CHECK['interpreter_flags_ok']
        self.assertTrue(ok(['-X', 'utf8', '-I']))
        self.assertTrue(ok(['-I', '-X', 'utf8', '-B']))
        self.assertTrue(ok(['-Xutf8', '-I', '-u']))
        for flags in (['-X', 'dev', '-I'], ['-X'], ['-I', '-X'], ['-O', '-I'], ['-I', '-E'], ['-I', 'helper.py']):
            self.assertFalse(ok(flags), flags)

    def test_08_end_to_end_final_check_accepts_x_utf8_and_powershell_receipts(self):
        from test_v27_check import EvidenceTests

        class XUtf8(EvidenceTests):
            def native_argv(self, argv):
                argv = super().native_argv(argv)
                return [argv[0], '-X', 'utf8'] + argv[1:] if argv[1:2] == ['-I'] else argv

        t = XUtf8('runTest')
        t.setUp()
        self.addCleanup(t.doCleanups)
        t.product_records()
        self.assertEqual(t.result('final')['errors'], [])
        for name in ('submission', 'security', 'clean_run'):
            ref = t.plan['records'][name]['execution']
            proof = json.loads((t.root / ref['path']).read_text(encoding='utf-8'))
            self.assertEqual(proof['argv'][1:3], ['-X', 'utf8'])
            proof['request']['cmd'] = PS_PREFIX + ps(proof['argv'])
            t.plan['records'][name]['execution'] = t.write(ref['path'], json.dumps(proof))
        self.assertEqual(t.result('final')['errors'], [])
        ref = t.plan['records']['clean_run']['execution']
        proof = json.loads((t.root / ref['path']).read_text(encoding='utf-8'))
        proof['request']['cmd'] += '; Remove-Item result.txt'
        t.plan['records']['clean_run']['execution'] = t.write(ref['path'], json.dumps(proof))
        self.assertTrue(any('exact retained argv' in error for error in t.result('final')['errors']))

    def test_09_end_to_end_rejects_other_interpreter_flags(self):
        from test_v27_check import EvidenceTests

        class XDev(EvidenceTests):
            def native_argv(self, argv):
                argv = super().native_argv(argv)
                return [argv[0], '-X', 'dev'] + argv[1:] if argv[1:2] == ['-I'] else argv

        t = XDev('runTest')
        t.setUp()
        self.addCleanup(t.doCleanups)
        t.product_records()
        self.assertTrue(any('actual isolated native command/result required' in error for error in t.result('final')['errors']))

    def test_10_clean_run_plan_may_use_x_utf8(self):
        from test_v27_check import EvidenceTests
        t = EvidenceTests('runTest')
        t.setUp()
        self.addCleanup(t.doCleanups)
        t.product_records()
        plan = dict(t.plan['clean_run_plan'], command=['{python}', '-X', 'utf8', '-I', 'product.py'])
        selected = t.write('clean_run_xutf8.json', json.dumps(plan))
        scratch = t.root / 'scratch_xutf8'
        scratch.mkdir()
        process = subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/clean_run.py'), '--root', str(t.root),
                                  '--plan', str(t.root / selected['path']), '--scratch', str(scratch)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(json.loads(process.stdout)['status'], 'PASS')

    def test_11_warning_and_guidance_point_to_x_utf8(self):
        warning = CHECK['utf8_warning'](True, 0)
        self.assertIn('UTF-8 mode is off', warning)
        self.assertIn('-X utf8 -I', warning)
        self.assertNotIn('use PYTHONUTF8=1', warning)
        skill = SKILL.read_text(encoding='utf-8')
        for phrase in ("& '<실제 python.exe>' '-X' 'utf8' '-I'", '셸마다 다르게 읽힐 수 있는 글자', '(r4-3.15)', '결과를 손으로 고치지 않는다'):
            self.assertIn(phrase, skill)
        contract = CONTRACT.read_text(encoding='utf-8')
        self.assertIn('`-I`·`-B`·`-u`·`-X utf8`만 허용한다', contract)
        self.assertIn('어느 셸이 실행했든', contract)


if __name__ == '__main__':
    unittest.main()
