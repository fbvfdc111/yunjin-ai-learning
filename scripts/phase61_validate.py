"""Run the actual full suite and preserved checks; write new Phase 6.1 evidence only."""
import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
               DOTS_API_KEY='', OPENAI_API_KEY='', OPENAI_VISION_MODEL='')
    commands = [
        ('pytest', ['-m', 'pytest', 'tests', '-q', '-p', 'no:cacheprovider', '--junitxml=docs/phase61_test_results.xml']),
        ('phase6_health', ['scripts/phase6_health_check.py']),
        ('phase6_protection', ['scripts/phase6_health_check.py', '--protection-only']),
        ('phase4_health', ['scripts/phase4_health_check.py']),
        ('phase5_health', ['scripts/phase5_health_check.py']),
        ('round2_health', ['scripts/phase5_round2_health_check.py']),
        ('round3_health', ['scripts/phase5_round3_health_check.py']),
        ('phase61_protection', ['scripts/phase61_protection.py']),
    ]
    results = []
    for name, args in commands:
        print('RUN', name, flush=True)
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        run = subprocess.run([sys.executable, *args], cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
        extension = 'txt' if name == 'pytest' else 'json'
        output = ROOT / f'docs/phase61_{name}_result.{extension}'
        output.write_text(run.stdout, encoding='utf-8')
        stderr = ROOT / f'docs/phase61_{name}_stderr.txt'
        stderr.write_text(run.stderr, encoding='utf-8')
        results.append({'name': name, 'command': [sys.executable, *args], 'started_utc': started,
                        'exit_code': run.returncode, 'stdout': output.relative_to(ROOT).as_posix(),
                        'stderr': stderr.relative_to(ROOT).as_posix()})
        print(name, 'exit', run.returncode, run.stdout[-220:] if name == 'pytest' else '', flush=True)
    evidence = {'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'python': sys.version, 'platform': platform.platform(),
                'packages': {name: importlib.metadata.version(name) for name in
                             ['streamlit', 'pytest', 'Pillow', 'PyYAML', 'openai', 'starlette']},
                'external_model_api_called': False,
                'full_suite_includes_phase6_and_round3': True,
                'historical_zip_used': False,
                'note': 'Preserved legacy checks use packaged manifests; only Phase 6 ZIP is the development baseline.',
                'results': results, 'ok': all(r['exit_code'] == 0 for r in results)}
    (ROOT / 'docs/phase61_validation.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if evidence['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
