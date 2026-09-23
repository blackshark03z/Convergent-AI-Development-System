from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def snapshot(root: Path) -> tuple[tuple[str, str], ...]:
    return tuple(
        (p.relative_to(root).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
        for p in sorted(root.rglob('*'))
        if p.is_file() and '.git' not in p.relative_to(root).parts
    )


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({'status': 'FAIL', 'reason': 'usage: xp005_oracle_runner.py <candidate-dir>'}))
        return 1
    candidate = Path(sys.argv[1]).resolve()
    before = snapshot(candidate)
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONPATH'] = str(candidate)
    try:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).with_name('xp005_oracle.py')), str(candidate)],
            cwd=candidate, env=env, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=150, check=False,
        )
        result = json.loads(proc.stdout)
        if not isinstance(result, dict) or result.get('status') not in {'PASS', 'FAIL'}:
            raise ValueError('invalid oracle result')
        if proc.returncode != (0 if result['status'] == 'PASS' else 1):
            raise ValueError('oracle status/exit mismatch')
    except Exception as exc:
        result = {'status': 'FAIL', 'reason': f'oracle runtime: {type(exc).__name__}: {exc}'}
    if snapshot(candidate) != before:
        result = {'status': 'FAIL', 'reason': 'oracle mutated candidate files'}
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
