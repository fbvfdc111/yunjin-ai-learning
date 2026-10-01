"""Read-only Phase 6 health and baseline integrity checks; prints JSON."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from yunjin_ai.digital_twin import STAGE_IDS, TwinState, load_stages, transition
from yunjin_ai.digital_twin_svg import render_twin_svg
from yunjin_ai.guide import answer_from_knowledge
from yunjin_ai.knowledge import (
    load_knowledge, load_sources, load_official_objects, load_official_relations,
    validate_knowledge, validate_official_relations,
)
from yunjin_ai.training import assert_level1_ready, assert_level2_ready


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def baseline_audit(root: Path = ROOT, baseline_zip: Path | None = None) -> dict:
    manifest = json.loads((root / 'docs/phase6_baseline_manifest.json').read_text(encoding='utf-8'))
    changed, missing, protected = [], [], {}
    for relative, record in manifest['files'].items():
        path = root / relative
        actual = sha256(path.read_bytes()) if path.is_file() else None
        if actual is None:
            missing.append(relative)
        elif actual != record['sha256']:
            changed.append(relative)
        protected[relative] = {'expected': record['sha256'], 'actual': actual, 'unchanged': actual == record['sha256']}
    unexpected = sorted(set(changed) - set(manifest['allowed_modified_files']))
    zip_verified = None
    app_protection = None
    if baseline_zip is not None:
        zip_verified = sha256(baseline_zip.read_bytes()) == manifest['baseline_sha256']
        with zipfile.ZipFile(baseline_zip) as archive:
            archived = {e.filename.split('/', 1)[1]: sha256(archive.read(e)) for e in archive.infolist() if not e.is_dir()}
            zip_verified = zip_verified and archived == {p: r['sha256'] for p, r in manifest['files'].items()}
            original_app = archive.read(next(e for e in archive.infolist() if e.filename.endswith('/app.py'))).decode('utf-8')
        def protected_app_parts(source):
            tree = ast.parse(source)
            result = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result.append(ast.dump(node))
                elif isinstance(node, ast.If) and any(isinstance(n, ast.Constant) and n.value in {'AI探锦', 'AI文化助手'} for n in ast.walk(node.test)):
                    result.append(ast.dump(node))
            return result
        app_protection = protected_app_parts(original_app) == protected_app_parts((root / 'app.py').read_text(encoding='utf-8'))
    official = {p: r for p, r in protected.items() if p.startswith('data/official/')}
    return {
        'baseline_zip_sha256': manifest['baseline_sha256'],
        'baseline_files': len(protected), 'unchanged_files': sum(r['unchanged'] for r in protected.values()),
        'allowed_modified_files': manifest['allowed_modified_files'], 'actual_modified_files': sorted(changed),
        'unexpected_modified_files': unexpected, 'missing_files': missing,
        'official_files': len(official), 'official_file_differences': sum(not r['unchanged'] for r in official.values()),
        'original_zip_and_manifest_verified': zip_verified,
        'original_vision_and_guide_app_blocks_unchanged': app_protection,
        'ok': not missing and not unexpected and zip_verified is not False and app_protection is not False,
        'files': protected,
    }


def health_report(baseline_zip: Path | None = None) -> dict:
    knowledge = load_knowledge(ROOT / 'data/knowledge/knowledge_base.json')
    sources = load_sources(ROOT / 'data/knowledge/sources.json')
    stages = load_stages(ROOT / 'data/digital_twin/twin_states.json', knowledge, sources)
    official = load_official_objects(ROOT / 'data/metadata/official_metadata.csv')
    relations = load_official_relations(ROOT / 'data/knowledge/official_object_knowledge_map.json')
    errors = validate_knowledge(knowledge, sources) + validate_official_relations(relations, official, knowledge)
    answers = {s.id: [hit.item.id for hit in answer_from_knowledge(s.ai_question, knowledge, sources).hits] for s in stages}
    state, observations = TwinState(), []
    for stage in stages:
        before = render_twin_svg(state)
        for _ in range(3 if stage.id == STAGE_IDS[-1] else 1):
            state = transition(state, 'execute')
        observations.append(state.current_stage == stage.id and state.current_stage_executed and before != render_twin_svg(state))
        state = transition(state, 'next')
    gates = []
    for gate in (assert_level1_ready, assert_level2_ready):
        try:
            gate(official)
        except RuntimeError:
            gates.append(True)
        else:
            gates.append(False)
    counts = dict(Counter(row['level1_label'] for row in official))
    governance = len(official) == 95 and counts == {'nanjing_yunjin':47,'other_brocade':48} and all(
        row['authorization_status'] == 'unknown' and row['usable_for_training'] == 'false' for row in official)
    protection = baseline_audit(baseline_zip=baseline_zip)
    report = {
        'phase': 'phase6', 'prototype': '知识驱动、状态驱动的南京云锦织造教学型数字孪生原型',
        'state_driver': 'user_interaction', 'physical_sensors': False,
        'real_time_bidirectional_sync': False, 'physical_parameter_simulation': False,
        'expert_mechanical_structure_validation': False,
        'stage_count': len(stages), 'knowledge_items': len(knowledge), 'sources': len(sources),
        'knowledge_relation_errors': errors, 'question_answer_hits': answers,
        'six_runtime_transitions_and_svg_changes_ok': all(observations),
        'all_teaching_stages_executed': state.executed_stages == STAGE_IDS,
        'official_objects': len(official), 'official_label_counts': counts,
        'authorization_unknown': sum(r['authorization_status'] == 'unknown' for r in official),
        'usable_for_training_true': sum(r['usable_for_training'] == 'true' for r in official),
        'governance_invariants_ok': governance, 'relation_records': len(relations),
        'training_gates_block': all(gates), 'protected_sha256_ok': protection['ok'],
        'real_external_api_called': False,
    }
    report['ok'] = all((not errors, all(answers.values()), all(observations), governance,
                        len(relations) == 47, all(gates), protection['ok']))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-zip', type=Path)
    parser.add_argument('--protection-only', action='store_true')
    args = parser.parse_args()
    report = baseline_audit(baseline_zip=args.baseline_zip) if args.protection_only else health_report(args.baseline_zip)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
