import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from phase6_health_check import baseline_audit, health_report


def test_all_round3_files_except_allowed_changes_have_identical_bytes():
    report = baseline_audit()
    assert report['ok']
    assert report['baseline_files'] == 305
    assert report['official_files'] == 145
    assert report['official_file_differences'] == 0
    for name in ('src/yunjin_ai/vision.py', 'src/yunjin_ai/knowledge.py', 'src/yunjin_ai/guide.py',
                 'src/yunjin_ai/product.py', 'tests/test_phase4_dots.py', 'src/yunjin_ai/training.py',
                 'data/knowledge/official_object_knowledge_map.json'):
        assert report['files'][name]['unchanged']


def test_governance_gates_and_runtime_health():
    report = health_report()
    assert report['ok']
    assert report['official_objects'] == 95
    assert report['official_label_counts'] == {'nanjing_yunjin':47, 'other_brocade':48}
    assert report['authorization_unknown'] == 95
    assert report['usable_for_training_true'] == 0
    assert report['training_gates_block']


def test_no_exaggerated_claims_or_media_sources_in_new_product_content():
    paths = [ROOT / 'app.py', *(ROOT / 'src/yunjin_ai').glob('digital_twin*.py')]
    strings = []
    for path in paths:
        strings.extend(n.value for n in ast.walk(ast.parse(path.read_text(encoding='utf-8')))
                       if isinstance(n, ast.Constant) and isinstance(n.value, str))
    strings.append((ROOT / 'data/digital_twin/twin_states.json').read_text(encoding='utf-8'))
    text = '\n'.join(strings)
    for affirmative in ('完整数字孪生', '实时同步实体织机', '工业级实时数字孪生系统'):
        assert affirmative not in text
    for path in paths[1:]:
        source = path.read_text(encoding='utf-8')
        for forbidden in ('st.image(', 'Image.open(', 'model_images_candidates', 'web_images/', 'train_level1', 'torch', 'requests.'):
            assert forbidden not in source
    state_fields = {'current_stage','executed_stages','mode','current_stage_executed','replay_count'}
    from yunjin_ai.digital_twin import TwinState, state_snapshot
    assert state_fields.issubset(state_snapshot(TwinState()))
