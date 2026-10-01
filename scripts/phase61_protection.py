"""Verify the Phase 6 archive contract without using any older code baseline."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'app.py', 'README.md', 'src/yunjin_ai/digital_twin_page.py',
           'src/yunjin_ai/digital_twin_svg.py'}


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def app_contract(source):
    tree = ast.parse(source)
    return [ast.dump(n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            or isinstance(n, ast.If) and any(isinstance(x, ast.Constant) and x.value in {'AI探锦', 'AI文化助手'}
                                             for x in ast.walk(n.test))]


def callback_contract(source):
    return [ast.dump(n) for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)
            and n.name in {'apply_twin_event', 'change_mode'}]


def audit():
    baseline = json.loads((ROOT / 'docs/phase61_baseline_manifest.json').read_text(encoding='utf-8'))
    changed, missing, files = [], [], {}
    for name, expected in baseline['files'].items():
        path = ROOT / name
        actual = digest(path.read_bytes()) if path.is_file() else None
        files[name] = {'expected': expected, 'actual': actual, 'unchanged': actual == expected}
        if actual is None:
            missing.append(name)
        elif actual != expected:
            changed.append(name)
    unexpected = sorted(set(changed) - ALLOWED)
    app_ok = app_contract((ROOT / 'app.py').read_text(encoding='utf-8')) == baseline['app_contract']
    callbacks_ok = callback_contract((ROOT / 'src/yunjin_ai/digital_twin_page.py').read_text(encoding='utf-8')) == baseline['callback_contract']
    return {'baseline_zip_sha256': baseline['zip_sha256'], 'baseline_files': len(files),
            'allowed_modified_files': sorted(ALLOWED), 'actual_modified_files': changed,
            'missing_files': missing, 'unexpected_modified_files': unexpected,
            'app_vision_and_guide_ast_unchanged': app_ok,
            'twin_event_callbacks_ast_unchanged': callbacks_ok,
            'all_original_tests_unchanged': all(v['unchanged'] for k, v in files.items() if k.startswith('tests/')),
            'twin_state_bytes_unchanged': files['src/yunjin_ai/digital_twin.py']['unchanged'],
            'knowledge_and_data_bytes_unchanged': all(v['unchanged'] for k, v in files.items() if k.startswith('data/')),
            'historical_reports_unchanged': all(v['unchanged'] for k, v in files.items() if k.startswith('docs/')),
            'ok': not missing and not unexpected and app_ok and callbacks_ok, 'files': files}


if __name__ == '__main__':
    result = audit()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
