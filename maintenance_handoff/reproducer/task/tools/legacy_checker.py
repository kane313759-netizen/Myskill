#!/usr/bin/env python3
"""Optional legacy result comparison; does not define the task contract or native score."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--answers',required=True);a=p.parse_args()
expected=[json.loads(x) for x in (Path(__file__).resolve().parents[1]/'expected/sample-first12.jsonl').read_text(encoding='utf-8').splitlines()]
# Historical tie-order convention used by this auxiliary checker.
expected[0]['sources']=list(reversed(expected[0]['sources']))
actual=[json.loads(x) for x in Path(a.answers).read_text(encoding='utf-8').splitlines()]
bad=[e['qid'] for i,e in enumerate(expected) if i>=len(actual) or actual[i]!=e]
print(json.dumps({'tool':'legacy_checker','checks':12,'failed_qids':bad},ensure_ascii=False))
raise SystemExit(1 if bad else 0)
