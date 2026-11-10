"""r4-3.3 regression: JSONL audit falls back to the kit run folder when the system temp folder is denied (Codex sandbox)."""
import json
import pathlib
import runpy
import shutil
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RegressionR433(unittest.TestCase):
    def test_01_jsonl_scratch_falls_back_when_temp_denied(self):
        # Run a copy inside a throwaway kit so the repository never gets a run/ folder.
        holder_dir = tempfile.TemporaryDirectory()
        self.addCleanup(holder_dir.cleanup)
        kit = pathlib.Path(holder_dir.name) / 'kit'
        (kit / 'scripts').mkdir(parents=True)
        shutil.copy2(str(ROOT / 'scripts/v27_jsonl.py'), str(kit / 'scripts/v27_jsonl.py'))
        module = runpy.run_path(str(kit / 'scripts/v27_jsonl.py'), run_name='r433_jsonl')
        real = tempfile.mkdtemp
        used = []

        def guarded(suffix=None, prefix=None, dir=None):
            if dir is None:
                raise PermissionError('sandbox denied system temp')
            used.append(dir)
            return real(suffix, prefix, dir)

        with mock.patch.object(tempfile, 'mkdtemp', guarded):
            holder = module['_scratch']()
            try:
                self.assertTrue(pathlib.Path(holder.name).is_dir())
            finally:
                holder.cleanup()
        self.assertTrue(used and pathlib.Path(used[0]).name == '.v27-tmp', used)
        self.assertEqual(pathlib.Path(used[0]).parent.name, 'run')

    def test_02_jsonl_audit_still_runs_end_to_end(self):
        audit = runpy.run_path(str(ROOT / 'scripts/data_audit.py'), run_name='r433_audit')['audit']
        with tempfile.TemporaryDirectory() as td:
            rows = [{'id': i, 'value': i * 1.5, 'note': {'k': i}} for i in range(20)]
            (pathlib.Path(td) / 'events.jsonl').write_text('\n'.join(json.dumps(r) for r in rows) + '\n', encoding='utf-8')
            result = audit(pathlib.Path(td), {'files': ['events.jsonl']})
            self.assertEqual(result['errors'], [])
            item = [a for a in result['files'] if a['path'] == 'events.jsonl'][0]
            self.assertEqual(item['rows_examined'], 20)


if __name__ == '__main__':
    unittest.main()
