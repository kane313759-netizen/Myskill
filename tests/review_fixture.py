"""Synthetic lifecycle records for validator tests, never real agent execution evidence."""
import hashlib
import json


def make_execution(task, role, checkpoint, report_path, scope):
    worker = '/synthetic-fixture/reviewer'
    directory = task / '.hackathon-kit/run/reviews' / (checkpoint + '-' + role)
    directory.mkdir(parents=True, exist_ok=True)
    observations = {}
    for index, phase in enumerate(('LAUNCHED', 'RUNNING', 'COMPLETED')):
        path = directory / (phase + '.json')
        value = {'worker_id': worker, 'phase': phase,
                 'observed_at': '2026-11-08T00:00:0%d+00:00' % index,
                 'tool': 'SYNTHETIC_TEST_FIXTURE',
                 'raw': {'worker_id': worker, 'status': phase, 'synthetic': True}}
        path.write_text(json.dumps(value), encoding='utf-8')
        observations[phase] = {'path': path.relative_to(task).as_posix(),
                               'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    report = task / report_path
    return {'version': 1, 'status': 'COMPLETE', 'worker_id': worker,
            'role': role, 'checkpoint': checkpoint, 'context_mode': 'NO_HISTORY',
            'observations': observations,
            'report': {'path': report_path, 'sha256': hashlib.sha256(report.read_bytes()).hexdigest()},
            'reviewed_files': scope}
