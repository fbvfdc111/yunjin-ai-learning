"""WebGL 3D human-loom collaboration view driven by simulation state.

Python remains the digital-twin state and simulation layer. This module only
serializes the current SimulationSample into a self-contained Three.js scene
that Streamlit embeds in an iframe.
"""
from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path

from .digital_twin_simulation import SimulationSample


THREE_JS_URL = "https://unpkg.com/three@0.160.0/build/three.min.js"
GLTF_LOADER_URL = "https://unpkg.com/three@0.160.0/examples/jsm/loaders/GLTFLoader.js"
RENDERING_LAYER = "Three.js WebGL embedded in Streamlit iframe"
ASSET_POLICY = (
    "V14 bundles one CC0 rigged human GLB from Innerscene/MakeHuman-MPFB as the "
    "licensed worker body base; clothing, loom, shuttle, warp and exhibition cloth "
    "remain procedural Three.js visuals."
)
BOUNDARY_COPY = (
    "Visual reconstruction based on the sloped, beam-framed Dahualou wooden drawloom used for Nanjing Yunjin: "
    "an upper flower-tower draw worker, a lower weaver, warp/shed, reed, shuttle and take-up path. "
    "It is a scale-aware exhibition model, not a dimensionally certified mechanical reconstruction."
)

ROOT_DIR = Path(__file__).resolve().parents[2]
LICENSED_HUMAN_MODEL = ROOT_DIR / "assets" / "models" / "human-base-rigged.cc0.glb"
LICENSED_HUMAN_SHA256 = "7135e03b6259e970458deff3e0458610914d7c35164cae12611101361e4a5749"


def _licensed_human_data_uri() -> str | None:
    if not LICENSED_HUMAN_MODEL.exists():
        return None
    payload = base64.b64encode(LICENSED_HUMAN_MODEL.read_bytes()).decode("ascii")
    return f"data:model/gltf-binary;base64,{payload}"

EXPLANATIONS: dict[str, tuple[str, str]] = {
    "pattern_design": (
        "图案设计阶段：系统展示织造前的纹样构思位置，三维织机与两位工匠处于待机观察状态。",
        "Pattern design: the motif concept is prepared while the 3D loom and both workers wait in an observation state.",
    ),
    "pattern_translation": (
        "挑花结本阶段：纹样信息被转换为后续提经可使用的教学符号，上层提花工作区暂未动作。",
        "Pattern translation: motif information is represented as teaching symbols for later warp lifting; the upper drawloom area is not yet moving.",
    ),
    "weaving_preparation": (
        "织造准备阶段：经线、梭子、踏板/踩障提示与打纬筘框进入准备位置，等待协同循环开始。",
        "Weaving preparation: warp threads, shuttle, treadle cue, and beater/reed frame move into ready positions before the collaboration cycle.",
    ),
    "warp_lifting": (
        "拽花工提经阶段：上层拽花工连续拉动控制线，花综/经线随仿真 lift_mm 形成可见梭口；下层织手等待引纬。",
        "Warp lifting: the upper draw worker pulls the cords; heddle/warp groups form a visible shed while the lower weaver waits to insert weft.",
    ),
    "weft_weaving": (
        "织手织造阶段：拽花工保持梭口，织手踩障/引纬并推动筘框打纬，梭子与新纬线穿过织口。",
        "Weft weaving: the draw worker holds the shed while the lower weaver presses the treadle cue, sends the shuttle/weft through, and beats it with the reed frame.",
    ),
    "pattern_emergence": (
        "织造成纹阶段：拽花工松手复位，梭口闭合，卷取轴推进一小段，织口处新增的一纬并入连续布面。",
        "Pattern emergence: the draw worker releases, the shed closes, the take-up roller advances, and the newly inserted pick joins the continuous cloth, completing one collaboration cycle.",
    ),
}


def process_explanation(sample: SimulationSample) -> dict[str, str]:
    """Return bilingual process copy for the current simulated stage."""
    zh, en = EXPLANATIONS[sample.stage_id]
    return {"title": "正在发生什么？ / What's happening?", "zh": zh, "en": en}


def animation_mapping(sample: SimulationSample) -> dict[str, float | bool | str]:
    """Map simulation state to WebGL animation parameters for tests and rendering."""
    progress = min(1.0, max(0.0, sample.stage_progress))
    stage_base_cloth = {
        "pattern_design": 0.06,
        "pattern_translation": 0.12,
        "weaving_preparation": 0.22,
        "warp_lifting": 0.34,
        "weft_weaving": 0.50,
        "pattern_emergence": 0.68,
    }
    stage_growth = {
        "pattern_design": 0.03,
        "pattern_translation": 0.05,
        "weaving_preparation": 0.07,
        "warp_lifting": 0.05,
        "weft_weaving": 0.14,
        "pattern_emergence": 0.24,
    }
    setup_focus = {
        "pattern_design": "pattern_draft_board",
        "pattern_translation": "tie_pattern_symbols",
        "weaving_preparation": "warp_and_shuttle_ready",
        "warp_lifting": "draw_worker_pull",
        "weft_weaving": "weaver_shuttle_pass",
        "pattern_emergence": "cloth_roll_advance",
    }
    cycle_step = {
        "pattern_design": "motif_reference",
        "pattern_translation": "tie_pattern_signal",
        "weaving_preparation": "warp_shuttle_reed_ready",
        "warp_lifting": "shed_opening",
        "weft_weaving": "weft_insertion_and_beating",
        "pattern_emergence": "shed_close_and_takeup",
    }
    is_lifting = sample.stage_id == "warp_lifting"
    is_weaving = sample.stage_id == "weft_weaving"
    is_forming = sample.stage_id == "pattern_emergence"
    lift_ratio = min(1.0, max(0.0, sample.lift_mm / 19.0))
    if is_forming:
        lift_ratio *= 1.0 - progress
    return {
        "stage_id": sample.stage_id,
        "continuous_clock": True,
        "draw_worker_motion": "pulling" if is_lifting else "holding" if is_weaving else "resetting" if is_forming else "idle",
        "weaver_motion": "waiting" if is_lifting else "weaving" if is_weaving else "finishing" if is_forming else "idle",
        "warp_lift_ratio": round(lift_ratio, 3),
        "shuttle_travel_ratio": round(progress if is_weaving else 0.5, 3),
        "woven_cloth_ratio": round(stage_base_cloth[sample.stage_id] + progress * stage_growth[sample.stage_id], 3),
        "show_teaching_pattern": is_weaving or is_forming,
        "show_floating_labels": False,
        "setup_focus": setup_focus[sample.stage_id],
        "loom_cycle_step": cycle_step[sample.stage_id],
        "shed_open_ratio": round(lift_ratio if is_lifting or is_weaving else lift_ratio * 0.35, 3),
        "beater_ratio": round(progress if is_weaving else 0.0, 3),
        "treadle_ratio": round(progress if is_weaving else 0.0, 3),
        "takeup_ratio": round(progress if is_forming else 0.0, 3),
        "new_pick_ratio": round(progress if is_weaving or is_forming else 0.0, 3),
    }


def render_process_twin_3d(
    sample: SimulationSample,
    *,
    rotation_y: int = -30,
    rotation_x: int = 58,
    zoom: int = 100,
    exhibition: bool = False,
) -> str:
    """Render a self-contained WebGL loom process scene."""
    explanation = process_explanation(sample)
    mapping = animation_mapping(sample)
    zoom_scale = max(76, min(132, zoom)) / 100
    scene_state = {
        "stageId": sample.stage_id,
        "stageTitle": sample.stage_title,
        "stageIndex": sample.stage_index,
        "stageProgress": sample.stage_progress,
        "elapsedSeconds": sample.elapsed_seconds,
        "tensionN": sample.tension_n,
        "liftMm": sample.lift_mm,
        "drawWorkerStatus": sample.draw_worker_status,
        "weaverStatus": sample.weaver_status,
        "coordinationStatus": sample.coordination_status,
        "dataSource": sample.data_source,
        "mapping": mapping,
        "licensedHumanGlbDataUri": _licensed_human_data_uri(),
        "licensedHumanModelName": "human-base-rigged.cc0.glb",
        "licensedHumanLicense": "CC0-1.0",
        "licensedHumanSha256": LICENSED_HUMAN_SHA256,
        "initialRotationY": rotation_y,
        "initialRotationX": rotation_x,
        "initialZoom": zoom_scale,
        "exhibitionMode": exhibition,
    }
    state_json = json.dumps(scene_state, ensure_ascii=False)
    legacy_markers = {
        "raised": "true" if mapping["warp_lift_ratio"] > 0.2 else "false",
        "draw_state": "ACTIVE" if mapping["draw_worker_motion"] == "pulling" else "HOLDING" if mapping["draw_worker_motion"] == "holding" else sample.draw_worker_status,
        "weaver_state": sample.weaver_status,
        "shuttle_active": "true" if sample.stage_id == "weft_weaving" else "false",
        "cloth_bands": 6 if sample.stage_id == "pattern_emergence" else 4 if sample.stage_id == "weft_weaving" else 3,
    }
    cloth_band_markers = "".join('<span class="cloth-band" hidden></span>' for _ in range(legacy_markers["cloth_bands"]))
    mode_class = " exhibition" if exhibition else ""
    scene_title = (
        "南京云锦大花楼织机沉浸展示 / Nanjing Yunjin Drawloom Showcase"
        if exhibition else
        "3D Human-Loom Collaborative Digital Twin Prototype / 三维人—织机协同数字孪生原型"
    )
    scene_sub = (
        f"{BOUNDARY_COPY} Simulation-driven / Simulated Data. 展示模式突出织机、工匠协作与连续锦缎生成；说明与数据仅作为辅助。"
        if exhibition else
        f"{BOUNDARY_COPY} Simulation-driven / Simulated Data. 当前为仿真驱动原型，不声称真实传感器、真实机械参数或工匠验证。"
    )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
html,body{{margin:0;height:100%;overflow:hidden;background:transparent;font-family:'Microsoft YaHei','Noto Sans CJK SC',Arial,sans-serif;color:#2f271f}}
.webgl-wrap{{box-sizing:border-box;width:100%;min-height:720px;display:grid;grid-template-rows:auto 1fr auto;background:linear-gradient(180deg,#fffaf2 0%,#ead7ba 100%);border:1px solid #dfc9aa;border-radius:8px;overflow:hidden;position:relative}}
.webgl-wrap.exhibition{{height:100vh;min-height:0;grid-template-rows:1fr;background:radial-gradient(circle at 46% 30%,#a86c42 0%,#5a3928 38%,#241b18 82%,#151315 100%);border:0;border-radius:10px;box-shadow:0 28px 80px rgba(35,18,8,.28)}}
.scene-head{{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;padding:14px 16px 8px;z-index:2}}
.scene-title{{font-size:21px;font-weight:800;line-height:1.22;color:#2f271f}}
.scene-sub{{font-size:12px;line-height:1.42;color:#674f3a;margin-top:4px;max-width:980px}}
.exhibition .scene-head{{position:absolute;left:14px;right:14px;top:12px;padding:0;pointer-events:none;text-shadow:0 2px 14px rgba(0,0,0,.58)}}
.exhibition .scene-title{{max-width:410px;font-size:18px;line-height:1.16;color:#fff8eb;letter-spacing:0}}
.exhibition .scene-sub{{display:none}}
.badge{{font-size:12px;font-weight:800;color:#7d263a;border:1px solid #d6aeb8;background:#fff7f9;border-radius:999px;padding:7px 10px;white-space:nowrap}}
.exhibition .badge{{font-size:10px;padding:5px 8px;color:#ffd783;border-color:rgba(255,215,131,.38);background:rgba(40,20,11,.42);backdrop-filter:blur(10px)}}
#webgl-canvas{{width:100%;height:548px;display:block;cursor:grab;touch-action:none}}
.exhibition #webgl-canvas{{height:100%}}
#webgl-canvas:active{{cursor:grabbing}}
.audio-hint{{position:absolute;left:22px;bottom:24px;padding:9px 13px;border:1px solid rgba(255,226,173,.42);border-radius:999px;background:rgba(49,27,18,.74);color:#fff4d9;font:600 11px 'Microsoft YaHei',Arial,sans-serif;letter-spacing:.02em;z-index:4;cursor:pointer;box-shadow:0 8px 22px rgba(20,10,7,.22)}}
.camera-fit{{position:absolute;right:22px;bottom:24px;padding:9px 13px;border:1px solid rgba(255,226,173,.42);border-radius:999px;background:rgba(49,27,18,.74);color:#fff4d9;font:700 11px 'Microsoft YaHei',Arial,sans-serif;letter-spacing:.02em;z-index:4;cursor:pointer;box-shadow:0 8px 22px rgba(20,10,7,.22);backdrop-filter:blur(10px)}}
.camera-fit:hover{{border-color:#f0d58f;background:rgba(105,43,45,.84)}}
.interaction-hint{{position:absolute;left:50%;bottom:24px;transform:translateX(-50%);z-index:4;padding:9px 14px;border:1px solid rgba(255,226,173,.30);border-radius:999px;background:rgba(34,20,16,.68);color:rgba(255,247,226,.88);font:600 11px 'Microsoft YaHei',Arial,sans-serif;letter-spacing:.02em;pointer-events:none;backdrop-filter:blur(10px);animation:hint-away 7s ease forwards}}
.process-ribbon{{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);z-index:5;width:min(760px,60vw);display:grid;grid-template-columns:repeat(6,1fr);gap:4px;padding:5px;border:1px solid rgba(255,220,147,.18);border-radius:16px;background:rgba(31,17,14,.42);box-shadow:0 10px 26px rgba(0,0,0,.15);backdrop-filter:blur(10px);pointer-events:none}}
.process-step{{position:relative;min-width:0;padding:7px 5px;border-radius:11px;color:rgba(255,245,220,.46);font:700 10px/1.15 'Microsoft YaHei',Arial,sans-serif;text-align:center;transition:color .28s ease,background .28s ease,box-shadow .28s ease}}
.process-step:after{{content:"";position:absolute;left:18%;right:18%;bottom:2px;height:1px;background:rgba(255,220,147,.20)}}
.process-step.active{{color:#fff5d6;background:linear-gradient(135deg,rgba(145,42,57,.88),rgba(191,130,49,.54));box-shadow:0 0 18px rgba(239,194,92,.25)}}
.process-step.active:after{{left:8%;right:auto;width:calc(var(--step-progress,0) * 84%);height:2px;background:#ffe2a0;box-shadow:0 0 7px rgba(255,218,128,.75)}}
.process-step.done{{color:rgba(255,229,169,.72)}}
.process-step.holding{{color:#f3d58b;background:rgba(118,75,35,.24)}}
.process-step.holding:before{{content:"保持";position:absolute;right:4px;top:2px;color:rgba(255,225,157,.72);font-size:7px;font-weight:700}}
.process-caption{{position:absolute;left:50%;top:64px;transform:translateX(-50%);z-index:5;max-width:min(620px,72vw);padding:7px 12px;border-radius:999px;background:rgba(37,21,17,.52);color:#fff5df;font:600 11px/1.35 'Microsoft YaHei',Arial,sans-serif;text-align:center;box-shadow:0 7px 20px rgba(0,0,0,.13);backdrop-filter:blur(8px);pointer-events:none}}
@keyframes hint-away{{0%,55%{{opacity:1;transform:translateX(-50%) translateY(0)}}100%{{opacity:0;transform:translateX(-50%) translateY(8px);visibility:hidden}}}}
.webgl-wrap:not(.exhibition) .audio-hint{{display:none}}
.webgl-wrap:not(.exhibition) .camera-fit{{display:none}}
.webgl-wrap:not(.exhibition) .interaction-hint,.webgl-wrap:not(.exhibition) .process-ribbon,.webgl-wrap:not(.exhibition) .process-caption{{display:none}}
.hud{{position:absolute;right:14px;top:86px;width:min(260px,28%);display:grid;gap:8px;z-index:3;pointer-events:none}}
.panel{{background:rgba(255,250,242,.92);border:1px solid #e1cfb7;border-radius:8px;padding:9px 10px;box-shadow:0 12px 26px rgba(82,55,31,.12)}}
.panel strong{{display:block;font-size:13px;color:#7d263a;margin-bottom:4px}}
.panel span{{display:block;font-size:12px;line-height:1.35;color:#4c3d2f}}
.exhibition .hud{{display:none}}
.exhibition .panel{{background:rgba(49,27,18,.52);border:1px solid rgba(255,226,173,.30);box-shadow:0 12px 28px rgba(20,10,7,.22);backdrop-filter:blur(12px)}}
.exhibition .panel strong{{color:#ffd783;font-size:12px}}
.exhibition .panel span{{color:rgba(255,246,228,.80);font-size:11px}}
.legend{{position:absolute;left:14px;bottom:146px;max-width:410px;background:rgba(255,250,242,.92);border:1px solid #e1cfb7;border-radius:8px;padding:8px 10px;font-size:12px;line-height:1.38;color:#4b3b2c;z-index:3;pointer-events:none}}
.exhibition .legend{{display:none}}
.explain{{display:grid;gap:5px;padding:10px 14px 13px;border-top:1px solid #e0ccb0;background:#fffaf4;z-index:2}}
.explain-title{{font-weight:800;color:#7d263a;font-size:14px}}
.explain p{{margin:0;font-size:12.5px;line-height:1.42;color:#493b2d}}
.exhibition .explain{{display:none}}
.fallback{{position:absolute;inset:94px 16px 150px;display:none;place-items:center;text-align:center;background:#fffaf4;border:1px solid #e1cfb7;border-radius:8px;padding:20px;color:#5a4633;z-index:4}}
.webgl-error .fallback{{display:grid}}
@media(max-width:980px){{.exhibition .scene-title{{font-size:15px;max-width:290px}}.exhibition .badge{{display:none}}.process-ribbon{{bottom:12px;width:min(620px,64vw)}}.process-caption{{top:58px;max-width:78vw}}}}
@media(max-width:760px){{.scene-head{{display:block}}.badge{{display:inline-block;margin-top:8px}}.hud{{position:static;width:auto;padding:0 14px 8px;grid-template-columns:1fr 1fr}}#webgl-canvas{{height:500px}}.exhibition #webgl-canvas{{height:100%}}.exhibition .hud{{display:none}}.legend{{display:none}}.exhibition .scene-head{{left:10px;right:10px;top:9px}}.exhibition .scene-title{{font-size:12px;max-width:190px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.audio-hint{{left:10px;bottom:10px;padding:7px 9px;font-size:9px}}.camera-fit{{right:10px;bottom:10px;padding:7px 9px;font-size:9px}}.interaction-hint{{bottom:50px;padding:6px 9px;font-size:9px;white-space:nowrap}}.process-ribbon{{bottom:46px;width:calc(100% - 20px);grid-template-columns:repeat(3,1fr);gap:2px;padding:3px;border-radius:12px}}.process-step{{padding:5px 2px;font-size:8px}}.process-caption{{top:52px;max-width:calc(100% - 24px);font-size:9px;padding:6px 9px}}}}
@media(max-width:760px){{.audio-hint,.camera-fit{{display:none}}.process-ribbon{{bottom:8px}}}}
@media(prefers-reduced-motion:reduce){{.interaction-hint{{animation:none;opacity:1}}.process-step{{transition:none}}}}
</style>
</head>
<body>
<section class="webgl-wrap{mode_class}" id="webgl-root" data-renderer="threejs-webgl" data-stage="{escape(sample.stage_id)}" data-source="{escape(sample.data_source)}" data-lift-mm="{sample.lift_mm}" data-tension-n="{sample.tension_n}" data-asset-policy="{escape(ASSET_POLICY)}">
  <div class="scene-head">
    <div>
      <div class="scene-title">{escape(scene_title)}</div>
      <div class="scene-sub">{escape(scene_sub)}</div>
    </div>
    <div class="badge">Three.js WebGL · {escape(sample.data_source)}</div>
  </div>
  <canvas id="webgl-canvas" aria-label="{escape(sample.stage_title)} WebGL human loom collaboration scene"></canvas>
  <button id="audio-hint" class="audio-hint" type="button">开启织机音效 / Enable sound</button>
  <button id="camera-fit" class="camera-fit" type="button">整机视图 / Fit view</button>
  <div class="interaction-hint" id="interaction-hint">拖动旋转 · 滚轮缩放 · 点击“整机视图”复位</div>
  <div class="process-ribbon" id="process-ribbon" aria-label="织造动作顺序">
    <div class="process-step" data-process="0">① 踩踏板</div><div class="process-step" data-process="1">② 经线开口</div><div class="process-step" data-process="2">③ 梭子引纬</div><div class="process-step" data-process="3">④ 筘框打纬</div><div class="process-step" data-process="4">⑤ 布面前进</div><div class="process-step" data-process="5">⑥ 卷轴收布</div>
  </div>
  <div class="process-caption" id="process-caption">织手踩下踏板，经线即将分层形成梭口</div>
  <div class="hud">
    <div class="panel"><strong>状态 / State</strong><span>Stage {sample.stage_index}/6 · {escape(sample.stage_title)}</span><span>Human Coordination · {escape(sample.coordination_status)}</span></div>
    <div class="panel"><strong>仿真辅助 / Simulated Signals</strong><span>Lift {sample.lift_mm:.1f} mm · Tension {sample.tension_n:.2f} N</span><span>Draw worker {escape(sample.draw_worker_status)} · Weaver {escape(sample.weaver_status)}</span></div>
    <div class="panel"><strong>织物说明 / Cloth Note</strong><span>连续布面为教学视觉示意的程序化云锦风格纹样，不是历史实物纹样复原。</span></div>
  </div>
  <div class="legend">鼠标拖动旋转，滚轮缩放。3D 区域保留少量层级提示：上层花楼/拽花区、经线与开口区、下层织造区、卷布/成品区；说明文字移到面板，模型优先。</div>
  <div class="fallback">Three.js WebGL 渲染层未能加载。请确认浏览器允许 WebGL，并且可以访问 Three.js CDN；Python/Streamlit 仿真状态仍保留。</div>
  <div hidden aria-hidden="true" data-v3-compat="phase64">
    <span data-raised="{legacy_markers['raised']}"></span>
    <span data-worker-state="{legacy_markers['draw_state']}">拽花工</span>
    <span data-worker-state="{legacy_markers['weaver_state']}">织手</span>
    <span class="shuttle" data-active="{legacy_markers['shuttle_active']}"></span>
    {cloth_band_markers}
  </div>
  <div class="explain">
    <div class="explain-title">{escape(explanation['title'])}</div>
    <p>{escape(explanation['zh'])}</p>
    <p>{escape(explanation['en'])}</p>
  </div>
</section>
<script id="scene-state" type="application/json">{state_json}</script>
<script type="importmap">{{"imports":{{"three":"https://unpkg.com/three@0.160.0/build/three.module.js"}}}}</script>
<script src="{THREE_JS_URL}"></script>
<script>
(function(){{
  const root = document.getElementById('webgl-root');
  const canvas = document.getElementById('webgl-canvas');
  try {{
  const state = JSON.parse(document.getElementById('scene-state').textContent);
  if (!window.THREE || !THREE.WebGLRenderer) {{ root.classList.add('webgl-error'); return; }}
  const loomAudio = {{context: null, master: null, enabled: false, lastPhase: 0}};
  function startLoomAudio() {{
    if (!state.exhibitionMode) return;
    if (!loomAudio.context) {{
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      loomAudio.context = new AudioContextClass();
      loomAudio.master = loomAudio.context.createGain();
      loomAudio.master.gain.value = .22;
      loomAudio.master.connect(loomAudio.context.destination);
      const drone = loomAudio.context.createOscillator();
      const droneGain = loomAudio.context.createGain();
      drone.type = 'sine';
      drone.frequency.value = 58;
      droneGain.gain.value = .008;
      drone.connect(droneGain).connect(loomAudio.master);
      drone.start();
    }}
    if (loomAudio.context.state === 'suspended') loomAudio.context.resume();
    loomAudio.enabled = true;
    const hint = document.getElementById('audio-hint');
    if (hint) {{ hint.textContent = '织机音效已开启 / Sound on'; hint.disabled = true; }}
  }}
  function playLoomTone(frequency, duration, type, volume) {{
    if (!loomAudio.enabled || !loomAudio.context) return;
    const now = loomAudio.context.currentTime;
    const oscillator = loomAudio.context.createOscillator();
    const gain = loomAudio.context.createGain();
    oscillator.type = type;
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(.0001, now);
    gain.gain.exponentialRampToValueAtTime(volume, now + .008);
    gain.gain.exponentialRampToValueAtTime(.0001, now + duration);
    oscillator.connect(gain).connect(loomAudio.master);
    oscillator.start(now);
    oscillator.stop(now + duration + .02);
  }}
  function playLoomNoise(duration, volume, cutoff) {{
    if (!loomAudio.enabled || !loomAudio.context) return;
    const length = Math.floor(loomAudio.context.sampleRate * duration);
    const buffer = loomAudio.context.createBuffer(1, length, loomAudio.context.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < length; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / length);
    const source = loomAudio.context.createBufferSource();
    const filter = loomAudio.context.createBiquadFilter();
    const gain = loomAudio.context.createGain();
    source.buffer = buffer;
    filter.type = 'lowpass';
    filter.frequency.value = cutoff;
    gain.gain.value = volume;
    source.connect(filter).connect(gain).connect(loomAudio.master);
    source.start();
  }}
  function triggerLoomAudio(timeline) {{
    if (!state.exhibitionMode || !loomAudio.enabled) return;
    if (timeline.phase < loomAudio.lastPhase) loomAudio.lastPhase = 0;
    if (loomAudio.lastPhase < .14 && timeline.phase >= .14) playLoomNoise(.07, .055, 1800);
    if (loomAudio.lastPhase < .38 && timeline.phase >= .38) {{
      playLoomNoise(.12, .07, 2200);
      playLoomTone(340, .08, 'triangle', .035);
    }}
    if (loomAudio.lastPhase < .62 && timeline.phase >= .62) playLoomNoise(.10, .13, 1200);
    if (loomAudio.lastPhase < .91 && timeline.phase >= .91) playLoomNoise(.09, .08, 700);
    loomAudio.lastPhase = timeline.phase;
  }}
  canvas.addEventListener('pointerdown', startLoomAudio);
  root.addEventListener('click', startLoomAudio);
  const audioButton = document.getElementById('audio-hint');
  if (audioButton) audioButton.addEventListener('click', (event) => {{
    event.stopPropagation();
    startLoomAudio();
  }});
  const licensedHumanWorkerAsset = {{
    name: state.licensedHumanModelName,
    license: state.licensedHumanLicense,
    sha256: state.licensedHumanSha256,
    marker: 'v19-scene-rebuild-structured-digital-twin-view',
    drawWorkerMarker: 'upper-pattern-operator-v19-jointed-seated-worker',
    weaverMarker: 'lower-weaver-v19-jointed-seated-worker',
    transitionMarker: 'v19-single-continuous-collaboration-loop-not-stage-demo',
    loomMarker: 'v19-five-layer-dahua-lou-loom-rebuild'
  }};
  const videoStoryboardBeats = [
    {{phase: '0.00-0.18', zh: '准备停留：两位工匠贴近工位，镜头先让观众看清上下层关系。', en: 'Held setup: both workers stay grounded so the viewer can read the upper/lower relationship.'}},
    {{phase: '0.16-0.46', zh: '上层拽花停留：拽花工身体前倾、双臂下拉，红金线帘与经线同步抬升并保持一段时间。', en: 'Held upper draw: the draw worker leans and pulls down; cord curtain and warp groups rise and remain visible.'}},
    {{phase: '0.42-0.70', zh: '下层引纬停留：织手探身递梭，手、梭、纬线沿织口连成一条运动链。', en: 'Held weft insertion: the lower weaver reaches forward while shuttle and weft travel as one chain.'}},
    {{phase: '0.62-0.86', zh: '打纬停留：织手身体跟随筘框前推，织口出现撞击线，布面被压实。', en: 'Held beating: the weaver follows the reed frame forward and the woven edge visibly compresses.'}},
    {{phase: '0.82-1.00', zh: '卷取成纹停留：经线回落、卷布轴推进，新纬线并入连续红金布面。', en: 'Held take-up: warp returns, cloth roller advances, and the new pick joins the red/gold cloth.'}}
  ];
  const persistentTimelineKey = state.exhibitionMode ? 'yunjin-webgl-v33-smooth-cloth-takeup-epoch' : 'yunjin-webgl-v19-rebuild-continuous-animation-epoch';

  const renderer = new THREE.WebGLRenderer({{canvas: canvas, antialias: true, alpha: true}});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = state.exhibitionMode ? 1.22 : 1.02;

  const scene = new THREE.Scene();
  if (state.exhibitionMode) {{
    const backdropCanvas = document.createElement('canvas');
    backdropCanvas.width = 1024;
    backdropCanvas.height = 512;
    const backdropCtx = backdropCanvas.getContext('2d');
    const backdropGradient = backdropCtx.createRadialGradient(520, 150, 24, 520, 210, 680);
    backdropGradient.addColorStop(0, '#60392b');
    backdropGradient.addColorStop(.34, '#33221f');
    backdropGradient.addColorStop(.74, '#1d1718');
    backdropGradient.addColorStop(1, '#120f13');
    backdropCtx.fillStyle = backdropGradient;
    backdropCtx.fillRect(0, 0, 1024, 512);
    const backdropTexture = new THREE.CanvasTexture(backdropCanvas);
    backdropTexture.colorSpace = THREE.SRGBColorSpace;
    scene.background = backdropTexture;
  }} else {{
    scene.background = null;
  }}
  scene.fog = state.exhibitionMode ? new THREE.FogExp2(0x251a18, .028) : new THREE.Fog(0xf5ead9, 10, 22);
  const camera = new THREE.PerspectiveCamera(state.exhibitionMode ? 34 : 42, 1, 0.1, 80);
  camera.zoom = state.initialZoom;
  camera.updateProjectionMatrix();
  const cameraTarget = new THREE.Vector3(state.exhibitionMode ? -.34 : 0, state.exhibitionMode ? 2.55 : 2.45, state.exhibitionMode ? .58 : 0);
  // A new key deliberately retires the old close-up camera that many browsers
  // have persisted. The museum-scale rebuild needs a wider first view.
  const cameraStoreKey = state.exhibitionMode ? 'yunjin-webgl-v36-lower-worker-readable-camera' : 'yunjin-webgl-v13-camera';
  const motionStoreKey = 'yunjin-webgl-v13-continuous-timeline-state';
  function readStoredCamera() {{
    try {{
      const raw = (window.parent && window.parent.localStorage ? window.parent.localStorage : window.localStorage).getItem(cameraStoreKey);
      return raw ? JSON.parse(raw) : null;
    }} catch (error) {{
      return null;
    }}
  }}
  function saveStoredCamera() {{
    try {{
      const store = window.parent && window.parent.localStorage ? window.parent.localStorage : window.localStorage;
      store.setItem(cameraStoreKey, JSON.stringify({{theta: orbitTheta, phi: orbitPhi, radius: orbitRadius}}));
    }} catch (error) {{}}
  }}
  function readStoredMotion() {{
    try {{
      const raw = (window.parent && window.parent.localStorage ? window.parent.localStorage : window.localStorage).getItem(motionStoreKey);
      return raw ? JSON.parse(raw) : null;
    }} catch (error) {{
      return null;
    }}
  }}
  function saveStoredMotion(payload) {{
    try {{
      const store = window.parent && window.parent.localStorage ? window.parent.localStorage : window.localStorage;
      store.setItem(motionStoreKey, JSON.stringify(payload));
    }} catch (error) {{}}
  }}
  const storedCamera = readStoredCamera();
  let orbitTheta = storedCamera && Number.isFinite(storedCamera.theta) ? storedCamera.theta : (state.exhibitionMode ? -0.50 : -0.68);
  let orbitPhi = storedCamera && Number.isFinite(storedCamera.phi) ? storedCamera.phi : (state.exhibitionMode ? 1.03 : 0.92);
  let orbitRadius = storedCamera && Number.isFinite(storedCamera.radius) ? storedCamera.radius : (state.exhibitionMode ? 13.5 : 11.6);
  let dragging = false;
  let introTourActive = false;
  try {{
    introTourActive = state.exhibitionMode && sessionStorage.getItem('yunjin-v31-intro-tour-seen') !== '1';
  }} catch (error) {{ introTourActive = state.exhibitionMode; }}
  let userCameraTouched = !introTourActive && !!storedCamera;
  let lastX = 0;
  let lastY = 0;
  function updateCamera() {{
    orbitPhi = Math.max(0.26, Math.min(1.34, orbitPhi));
    orbitRadius = Math.max(6.8, Math.min(24, orbitRadius));
    camera.position.set(
      cameraTarget.x + Math.sin(orbitTheta) * Math.sin(orbitPhi) * orbitRadius,
      cameraTarget.y + Math.cos(orbitPhi) * orbitRadius,
      cameraTarget.z + Math.cos(orbitTheta) * Math.sin(orbitPhi) * orbitRadius
    );
    camera.lookAt(cameraTarget);
  }}
  canvas.addEventListener('pointerdown', function(event) {{
    dragging = true;
    lastX = event.clientX;
    lastY = event.clientY;
    canvas.setPointerCapture(event.pointerId);
    const interactionHint = document.getElementById('interaction-hint');
    if (interactionHint) interactionHint.style.display = 'none';
    introTourActive = false;
  }});
  canvas.addEventListener('pointermove', function(event) {{
    if (!dragging) return;
    orbitTheta -= (event.clientX - lastX) * 0.008;
    orbitPhi -= (event.clientY - lastY) * 0.006;
    lastX = event.clientX;
    lastY = event.clientY;
    userCameraTouched = true;
    updateCamera();
    saveStoredCamera();
  }});
  canvas.addEventListener('pointerup', function(event) {{
    dragging = false;
    try {{ canvas.releasePointerCapture(event.pointerId); }} catch (error) {{}}
  }});
  canvas.addEventListener('wheel', function(event) {{
    event.preventDefault();
    orbitRadius += event.deltaY * 0.012;
    userCameraTouched = true;
    updateCamera();
    saveStoredCamera();
  }}, {{passive:false}});
  const cameraFitButton = document.getElementById('camera-fit');
  if (cameraFitButton) cameraFitButton.addEventListener('click', function(event) {{
    event.stopPropagation();
    orbitTheta = -0.60;
    orbitPhi = 1.03;
    orbitRadius = 13.6;
    cameraTarget.set(-.34, 2.55, .62);
    userCameraTouched = true;
    updateCamera();
    saveStoredCamera();
  }});
  updateCamera();

  // A restrained procedural grain gives the large frame the visual weight of
  // hand-worked timber without loading external assets.
  const woodCanvas = document.createElement('canvas');
  woodCanvas.width = 256;
  woodCanvas.height = 256;
  const woodCtx = woodCanvas.getContext('2d');
  const woodGradient = woodCtx.createLinearGradient(0, 0, 256, 0);
  woodGradient.addColorStop(0, '#5c3924');
  woodGradient.addColorStop(.28, '#8a5b38');
  woodGradient.addColorStop(.56, '#6d452b');
  woodGradient.addColorStop(1, '#9a6740');
  woodCtx.fillStyle = woodGradient;
  woodCtx.fillRect(0, 0, 256, 256);
  for (let y = 5; y < 256; y += 7) {{
    woodCtx.strokeStyle = y % 21 === 5 ? 'rgba(38,18,10,.28)' : 'rgba(238,185,120,.13)';
    woodCtx.lineWidth = y % 21 === 5 ? 1.5 : .8;
    woodCtx.beginPath();
    for (let x = 0; x <= 256; x += 8) {{
      const gy = y + Math.sin(x * .055 + y * .08) * 2.2 + Math.sin(x * .017) * 1.4;
      if (x === 0) woodCtx.moveTo(x, gy); else woodCtx.lineTo(x, gy);
    }}
    woodCtx.stroke();
  }}
  const woodTexture = new THREE.CanvasTexture(woodCanvas);
  woodTexture.colorSpace = THREE.SRGBColorSpace;
  woodTexture.wrapS = THREE.RepeatWrapping;
  woodTexture.wrapT = THREE.RepeatWrapping;
  woodTexture.repeat.set(2.2, 5.0);
  woodTexture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const darkWoodTexture = woodTexture.clone();
  darkWoodTexture.repeat.set(2.8, 6.5);
  darkWoodTexture.anisotropy = woodTexture.anisotropy;
  darkWoodTexture.needsUpdate = true;
  const mats = {{
    wood: new THREE.MeshPhysicalMaterial({{color: 0xb47c4c, map: woodTexture, bumpMap: woodTexture, bumpScale: .035, roughness: .64, metalness: .015, clearcoat: .16, clearcoatRoughness: .70}}),
    darkWood: new THREE.MeshPhysicalMaterial({{color: 0x51301f, map: darkWoodTexture, bumpMap: darkWoodTexture, bumpScale: .028, roughness: .74, clearcoat: .10, clearcoatRoughness: .78}}),
    foregroundWood: new THREE.MeshPhysicalMaterial({{color: 0x9a6a45, map: woodTexture, bumpMap: woodTexture, bumpScale: .018, roughness: .84, metalness: 0, clearcoat: .035, clearcoatRoughness: .90}}),
    cord: new THREE.MeshPhysicalMaterial({{color: 0xd5b978, roughness: .48, sheen: .72, sheenColor: new THREE.Color(0xffe2a1), sheenRoughness: .52}}),
    activeCord: new THREE.MeshPhysicalMaterial({{color: 0xd83d57, roughness: .34, sheen: .88, sheenColor: new THREE.Color(0xff9b99), sheenRoughness: .38}}),
    warp: new THREE.MeshPhysicalMaterial({{color: 0xf0ddba, roughness: .42, sheen: .82, sheenColor: new THREE.Color(0xffedbf), sheenRoughness: .44}}),
    activeWarp: new THREE.MeshPhysicalMaterial({{color: 0xb52d49, roughness: .34, sheen: .92, sheenColor: new THREE.Color(0xff9d9b), sheenRoughness: .36}}),
    gold: new THREE.MeshPhysicalMaterial({{color: 0xdab253, roughness: .36, metalness: .28, clearcoat: .12, clearcoatRoughness: .46}}),
    teal: new THREE.MeshPhysicalMaterial({{color: 0x3f7972, emissive: 0x0b211f, emissiveIntensity: .13, roughness: .46, sheen: .68, sheenColor: new THREE.Color(0x91c9bb), sheenRoughness: .52}}),
    legTeal: new THREE.MeshPhysicalMaterial({{color: 0x438f83, emissive: 0x0b2824, emissiveIntensity: .16, roughness: .48, sheen: .64, sheenColor: new THREE.Color(0x8ac9b6)}}),
    red: new THREE.MeshPhysicalMaterial({{color: 0x9d344b, emissive: 0x26070d, emissiveIntensity: .12, roughness: .44, sheen: .80, sheenColor: new THREE.Color(0xe69aa5), sheenRoughness: .46}}),
    skin: new THREE.MeshPhysicalMaterial({{color: 0xe5ae88, roughness: .56, clearcoat: .025, clearcoatRoughness: .85}}),
    hair: new THREE.MeshPhysicalMaterial({{color: 0x241914, roughness: .70, sheen: .18, sheenColor: new THREE.Color(0x6c4b35)}}),
    clothDark: new THREE.MeshPhysicalMaterial({{color: 0x263a3d, roughness: .56, sheen: .58, sheenColor: new THREE.Color(0x668c87)}}),
    floor: new THREE.MeshPhysicalMaterial({{color: state.exhibitionMode ? 0x302522 : 0xe8d5bd, roughness: state.exhibitionMode ? .94 : .82, clearcoat: 0}}),
    paleWarp: new THREE.MeshPhysicalMaterial({{color: 0xffecc8, roughness: .44, sheen: .78, sheenColor: new THREE.Color(0xffe9b0)}}),
    cueRed: new THREE.MeshBasicMaterial({{color: 0xbd2745, transparent: true, opacity: .82}}),
    cueTeal: new THREE.MeshBasicMaterial({{color: 0x228978, transparent: true, opacity: .78}}),
    cueGold: new THREE.MeshBasicMaterial({{color: 0xd5a23a, transparent: true, opacity: .82}}),
    translucentGold: new THREE.MeshBasicMaterial({{color: 0xd5aa50, transparent: true, opacity: .32, side: THREE.DoubleSide}}),
    translucentRed: new THREE.MeshBasicMaterial({{color: 0xbd2745, transparent: true, opacity: .26, side: THREE.DoubleSide}}),
    redSilkSurface: new THREE.MeshBasicMaterial({{color: 0x8b1f31, transparent: true, opacity: .30, side: THREE.DoubleSide}}),
    deepVideoRed: new THREE.MeshPhysicalMaterial({{color: 0x721423, roughness: .44, metalness: .03, sheen: .72, sheenColor: new THREE.Color(0xc56e78)}}),
    silkGold: new THREE.MeshPhysicalMaterial({{color: 0xe7c469, roughness: .30, metalness: .26, sheen: .90, sheenColor: new THREE.Color(0xffe8a9), sheenRoughness: .34}}),
    warpSheet: new THREE.MeshBasicMaterial({{color: 0xf4ddb0, transparent: true, opacity: .18, side: THREE.DoubleSide}}),
    jointGold: new THREE.MeshBasicMaterial({{color: 0xf2bf4a}}),
    layerBlue: new THREE.MeshBasicMaterial({{color: 0x4f8fb7, transparent: true, opacity: .12, side: THREE.DoubleSide}}),
    layerGreen: new THREE.MeshBasicMaterial({{color: 0x4c9a73, transparent: true, opacity: .11, side: THREE.DoubleSide}}),
    layerAmber: new THREE.MeshBasicMaterial({{color: 0xd5a23a, transparent: true, opacity: .13, side: THREE.DoubleSide}}),
    motionRed: new THREE.MeshBasicMaterial({{color: 0xbd2745, transparent: true, opacity: .42, side: THREE.DoubleSide}}),
    motionTeal: new THREE.MeshBasicMaterial({{color: 0x1b8f80, transparent: true, opacity: .38, side: THREE.DoubleSide}}),
    motionGold: new THREE.MeshBasicMaterial({{color: 0xf0b640, transparent: true, opacity: .46, side: THREE.DoubleSide}})
  }};

  scene.add(new THREE.HemisphereLight(0xffefd0, state.exhibitionMode ? 0x241829 : 0x6d4a34, state.exhibitionMode ? 1.45 : 2.4));
  const key = new THREE.DirectionalLight(0xfff1d3, state.exhibitionMode ? 4.05 : 2.2);
  key.position.set(4, 8, 6);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xd3e3e2, state.exhibitionMode ? .72 : .8);
  fill.position.set(-5, 4, -5);
  scene.add(fill);
  if (state.exhibitionMode) {{
    const silkSpot = new THREE.SpotLight(0xffca78, 7.2, 19, .58, .72, 1.0);
    silkSpot.name = 'v20-exhibition-warm-stage-spotlight-on-cloth';
    silkSpot.position.set(-3.8, 5.8, 5.4);
    silkSpot.target.position.set(0, 1.18, 1.85);
    silkSpot.castShadow = true;
    scene.add(silkSpot);
    scene.add(silkSpot.target);
    const backRim = new THREE.DirectionalLight(0x9fcbd2, 1.65);
    backRim.name = 'v20-exhibition-cool-rim-light-for-loom-silhouette';
    backRim.position.set(4.8, 5.2, -4.8);
    scene.add(backRim);
    const actionSpot = new THREE.SpotLight(0xffdfad, 4.8, 12, .48, .68, 1.2);
    actionSpot.name = 'upper-worker-and-raised-warp-action-spotlight';
    actionSpot.position.set(-4.2, 5.6, 3.2);
    actionSpot.target.position.set(-1.55, 2.85, -.30);
    scene.add(actionSpot);
    scene.add(actionSpot.target);
    const galleryWash = new THREE.RectAreaLight(0xffd8aa, 5.5, 7.2, 3.8);
    galleryWash.name = 'museum-softbox-front-wash';
    galleryWash.position.set(0, 5.7, 5.8);
    galleryWash.lookAt(0, 1.7, .5);
    scene.add(galleryWash);
    const tealEdge = new THREE.PointLight(0x5aa7a1, 1.8, 10, 1.8);
    tealEdge.name = 'subtle-teal-cultural-rim-light';
    tealEdge.position.set(4.6, 2.5, -2.8);
    scene.add(tealEdge);
    const workerContour = new THREE.PointLight(0xffd5aa, 2.15, 5.6, 1.8);
    workerContour.name = 'subtle-warm-worker-contour-light';
    workerContour.position.set(-3.2, 2.75, 2.8);
    scene.add(workerContour);
  }}

  const loom = new THREE.Group();
  loom.name = 'webgl-drawloom-v3';
  scene.add(loom);

  function box(name, w, h, d, x, y, z, mat) {{
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    mesh.name = name;
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    loom.add(mesh);
    return mesh;
  }}
  function cyl(name, radius, depth, x, y, z, mat, rotZ) {{
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, depth, 12), mat);
    mesh.name = name;
    mesh.position.set(x, y, z);
    mesh.rotation.z = rotZ || Math.PI / 2;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    loom.add(mesh);
    return mesh;
  }}
  function beamBetween(name, start, end, radius, mat) {{
    const direction = new THREE.Vector3().subVectors(end, start);
    const length = direction.length();
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, length, 10), mat);
    mesh.name = name;
    mesh.position.copy(start).add(end).multiplyScalar(.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.baseLength = length;
    loom.add(mesh);
    return mesh;
  }}
  function repositionBeamBetween(mesh, start, end) {{
    const direction = new THREE.Vector3().subVectors(end, start);
    const length = direction.length();
    mesh.position.copy(start).add(end).multiplyScalar(.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    mesh.scale.y = length / Math.max(.0001, mesh.userData.baseLength || length);
  }}
  function timberBetween(name, start, end, thickness, depth, mat) {{
    const direction = new THREE.Vector3().subVectors(end, start);
    const length = direction.length();
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(thickness, length, depth), mat);
    mesh.name = name;
    mesh.position.copy(start).add(end).multiplyScalar(.5);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    loom.add(mesh);
    return mesh;
  }}

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(13, 10), mats.floor);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.04;
  if (state.exhibitionMode) floor.scale.set(1.35, 1.35, 1);
  floor.receiveShadow = true;
  scene.add(floor);
  if (state.exhibitionMode) {{
    const poolCanvas = document.createElement('canvas');
    poolCanvas.width = 256;
    poolCanvas.height = 256;
    const poolCtx = poolCanvas.getContext('2d');
    const poolGradient = poolCtx.createRadialGradient(128, 128, 8, 128, 128, 124);
    poolGradient.addColorStop(0, 'rgba(255,205,125,.22)');
    poolGradient.addColorStop(.48, 'rgba(165,92,58,.10)');
    poolGradient.addColorStop(1, 'rgba(44,24,21,0)');
    poolCtx.fillStyle = poolGradient;
    poolCtx.fillRect(0, 0, 256, 256);
    const poolTexture = new THREE.CanvasTexture(poolCanvas);
    const stagePool = new THREE.Mesh(
      new THREE.PlaneGeometry(11.5, 8.0),
      new THREE.MeshBasicMaterial({{map: poolTexture, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending}})
    );
    stagePool.name = 'museum-floor-soft-light-pool';
    stagePool.rotation.x = -Math.PI / 2;
    stagePool.position.y = -.032;
    scene.add(stagePool);
  }}
  const rebuildLayers = new THREE.Group();
  rebuildLayers.name = 'v19-five-layer-dahua-lou-loom-rebuild';
  loom.add(rebuildLayers);
  function layerSlab(name, w, h, d, x, y, z, mat) {{
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    mesh.name = name;
    mesh.position.set(x, y, z);
    mesh.renderOrder = -1;
    rebuildLayers.add(mesh);
    return mesh;
  }}
  layerSlab('v19-layer-1-body-frame-solid-wood-zone', 7.35, .05, 5.05, 0, .12, 0, mats.layerAmber);
  layerSlab('v19-layer-2-upper-flower-tower-operator-zone', 6.35, .05, 1.80, 0, 3.28, .98, mats.layerBlue);
  layerSlab('v19-layer-3-warp-shed-transparent-process-zone', 5.90, .05, 2.05, 0, 1.85, .20, mats.layerGreen);
  layerSlab('v19-layer-4-lower-weaving-shuttle-beater-zone', 5.55, .05, 1.72, 0, .94, 1.72, mats.layerAmber);
  layerSlab('v19-layer-5-cloth-takeup-finished-fabric-zone', 5.05, .05, .86, 0, .72, 2.48, mats.layerBlue);
  // These translucent slabs explain process layers in teaching mode, but
  // read as leftover platforms in the exhibition scene.
  rebuildLayers.visible = !state.exhibitionMode;

  [-3.3, 3.3].forEach(x => [-2.1, 2.1].forEach(z => {{
    const isForeground = z > 0;
    box('museum-scale-main-post', isForeground ? .34 : .40, 5.80, isForeground ? .34 : .40, x, 2.90, z, isForeground ? mats.foregroundWood : mats.wood);
  }}));
  [-3.62, 3.62].forEach(x => [-2.42, 2.42].forEach(z => {{
    const outerPost = box('v16-dahua-lou-tower-tall-outer-post', .13, 6.35, .13, x, 3.12, z, mats.wood);
    // This duplicate outer cage produced the isolated thin sticks above the
    // loom in the exhibition view.  The four main posts already carry the
    // readable frame silhouette.
    outerPost.visible = !state.exhibitionMode;
  }}));
  [-3.62, 3.62].forEach(x => {{
    const rearTowerPost = box('v16-dahua-lou-upper-pattern-tower-side-post', .12, 2.15, .12, x, 4.70, -1.38, mats.wood);
    const frontTowerPost = box('v16-dahua-lou-upper-pattern-tower-side-post', .12, 2.15, .12, x, 4.70, .96, mats.wood);
    rearTowerPost.visible = !state.exhibitionMode;
    frontTowerPost.visible = !state.exhibitionMode;
  }});
  [0.55, 2.65, 4.95].forEach(y => {{
    const frontCrossbeam = box('front-crossbeam', 7.05, y === 4.95 ? .29 : .24, y === 4.95 ? .29 : .24, 0, y, 2.1, mats.foregroundWood);
    const rearCrossbeam = box('rear-crossbeam', 7.05, .34, .34, 0, y, -2.1, mats.wood);
    // Exhibition uses only the top and bottom members so the frame reads as
    // one closed timber structure rather than six unrelated thin rods.
    frontCrossbeam.visible = !state.exhibitionMode || y !== 2.65;
    rearCrossbeam.visible = !state.exhibitionMode || y !== 2.65;
  }});
  [-3.3, 3.3].forEach(x => {{
    box('side-rail-left-right', .34, .32, 4.4, x, 4.95, 0, mats.wood);
    box('side-rail-lower', .34, .30, 4.4, x, .55, 0, mats.wood);
  }});
  // Broad timber braces and visible mortise collars give the frame believable
  // load paths; earlier thin cylindrical diagonals looked like loose sticks.
  timberBetween('left-side-museum-timber-brace', new THREE.Vector3(-3.27, .72, -1.82), new THREE.Vector3(-3.27, 4.62, 1.78), .20, .16, mats.darkWood);
  timberBetween('right-side-museum-timber-brace', new THREE.Vector3(3.27, .72, -1.82), new THREE.Vector3(3.27, 4.62, 1.78), .20, .16, mats.darkWood);
  [0.55, 4.95].forEach(y => [-3.3, 3.3].forEach(x => [-2.1, 2.1].forEach(z => {{
    const collar = new THREE.Mesh(new THREE.BoxGeometry(.52, .16, .52), mats.darkWood);
    collar.name = 'visible-mortise-and-tenon-collar';
    collar.position.set(x, y, z);
    collar.castShadow = true;
    loom.add(collar);
    const peg = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, .56, 10), mats.wood);
    peg.name = 'wooden-locking-peg-through-joint';
    peg.rotation.x = Math.PI / 2;
    peg.position.set(x, y, z);
    loom.add(peg);
  }})));
  // Hand-built wooden looms are not CAD-perfect lattices. Add the characteristic
  // sloped braces, wedges and small timber offsets so the frame reads as a
  // worked wooden machine rather than a symmetric metal scaffold.
  const handCutWood = new THREE.MeshStandardMaterial({{color: 0x95683f, roughness: .88}});
  const exhibitionBraces = [];
  exhibitionBraces.push(beamBetween('hand-cut-left-front-diagonal-brace', new THREE.Vector3(-3.30, .28, 2.05), new THREE.Vector3(-2.72, 3.88, 1.95), .095, handCutWood));
  exhibitionBraces.push(beamBetween('hand-cut-right-front-diagonal-brace', new THREE.Vector3(3.30, .34, 2.05), new THREE.Vector3(2.86, 3.72, 1.92), .082, handCutWood));
  exhibitionBraces.push(beamBetween('hand-cut-left-rear-diagonal-brace', new THREE.Vector3(-3.58, 1.08, -2.15), new THREE.Vector3(-2.98, 4.56, -1.96), .075, mats.darkWood));
  exhibitionBraces.push(beamBetween('hand-cut-right-rear-diagonal-brace', new THREE.Vector3(3.56, .94, -2.12), new THREE.Vector3(3.02, 4.38, -1.90), .070, mats.darkWood));
  exhibitionBraces.forEach((brace) => {{ brace.visible = !state.exhibitionMode; }});
  const upperLeftWedge = box('hand-cut-upper-left-wedge', .32, .22, .42, -2.58, 3.18, 1.22, handCutWood);
  const upperRightWedge = box('hand-cut-upper-right-wedge', .28, .18, .38, 2.48, 3.26, 1.20, handCutWood);
  upperLeftWedge.rotation.z = -.10;
  upperRightWedge.rotation.z = .08;
  // These loose wedges were inherited from an earlier reference build and
  // appear as two unsupported brown blocks in the exhibition camera.
  upperLeftWedge.visible = !state.exhibitionMode;
  upperRightWedge.visible = !state.exhibitionMode;
  box('top-drawloom-frame', 5.1, .58, 1.15, 0, 4.7, -1.75, mats.darkWood);
  box('pattern-control-bank', 4.4, .28, .46, 0, 3.85, -1.32, mats.wood);
  // Layered flower-tower rails support the pattern harness and make the upper
  // storey read as a working machine rather than one oversized dark block.
  [4.18, 4.62, 5.08, 5.48].forEach((y, i) => {{
    const rail = box('upper-pattern-harness-support-rail', 5.05 - i * .12, .13, .16, 0, y, -1.34, i % 2 ? mats.wood : mats.darkWood);
    rail.castShadow = true;
  }});
  [-2.48, 2.48].forEach(x => {{
    box('upper-pattern-harness-side-upright', .18, 1.62, .20, x, 4.72, -1.34, mats.wood);
  }});
  box('upper-draw-worker-platform', 4.8, .16, 1.25, 0, 3.34, -.50, mats.darkWood);
  box('v16-upper-pattern-operator-side-seat', .92, .30, .72, -2.74, 3.52, -.50, mats.darkWood);
  box('v16-upper-pattern-operator-foot-board', 1.20, .08, .46, -2.74, 3.18, -.30, mats.wood);
  const upperGuardFront = box('v16-upper-platform-guard-rail-front', 5.05, .08, .08, 0, 4.02, .12, mats.wood);
  const upperGuardRear = box('v16-upper-platform-guard-rail-rear', 5.05, .08, .08, 0, 4.02, -1.12, mats.wood);
  upperGuardFront.visible = !state.exhibitionMode;
  upperGuardRear.visible = !state.exhibitionMode;
  box('v16-pattern-tower-jacquard-block-bank', 4.55, .34, .28, 0, 5.45, -1.38, mats.darkWood);
  // A fixed access ladder explains how the upper draw worker reaches the
  // flower tower. It is structurally tied to the left rear post.
  timberBetween('upper-platform-access-ladder-left-rail', new THREE.Vector3(-3.02, .48, -1.88), new THREE.Vector3(-3.02, 3.46, -1.32), .10, .10, mats.darkWood);
  timberBetween('upper-platform-access-ladder-right-rail', new THREE.Vector3(-2.58, .48, -1.88), new THREE.Vector3(-2.58, 3.46, -1.32), .10, .10, mats.darkWood);
  for (let i = 0; i < 8; i++) {{
    const u = i / 7;
    const rung = box('upper-platform-access-ladder-rung', .56, .075, .075, -2.80, .66 + u * 2.58, -1.80 + u * .48, mats.wood);
    rung.rotation.x = -.18;
  }}
  if (!state.exhibitionMode) {{
    beamBetween('v17-reference-photo-sloped-upper-pattern-cord-bank-left', new THREE.Vector3(-2.75, 5.64, -1.74), new THREE.Vector3(-.70, 3.10, .16), .018, mats.cord);
    beamBetween('v17-reference-photo-sloped-upper-pattern-cord-bank-right', new THREE.Vector3(2.75, 5.64, -1.74), new THREE.Vector3(.70, 3.10, .16), .018, mats.cord);
  }}
  if (!state.exhibitionMode) {{
    for (let i = 0; i < 18; i++) {{
      const x0 = -2.35 + i * .28;
      const x1 = -1.20 + i * .14;
      beamBetween('v17-pdf-real-loom-diagonal-pattern-control-cords', new THREE.Vector3(x0, 5.48, -1.78), new THREE.Vector3(x1, 2.92, .02), .006, i % 4 === 0 ? mats.activeCord : mats.cord);
    }}
  }}
  // Removed the nine obsolete roof-like rods completely. They were a visual
  // reference artifact and did not participate in the weaving mechanism.
  box('lower-weaving-bench', 4.9, .16, 1.15, 0, .72, 1.55, mats.darkWood);
  // Use an open four-legged stool instead of a solid block so the viewer can
  // see the weaver's feet reaching the treadles beneath the seat.
  box('lower-weaver-stool-seat-board', .88, .12, .66, -2.55, .52, 2.40, mats.darkWood);
  [-2.87, -2.23].forEach(x => {{
    [2.16, 2.64].forEach(z => box('lower-weaver-stool-visible-leg', .11, .46, .11, x, .25, z, mats.darkWood));
  }});
  box('upper-worker-foot-contact-platform-v5', 1.22, .045, .48, -2.88, 3.45, -.46, mats.gold);
  // Keep the front work surface as a thin support under the cloth, rather
  // than a deep brown platform that dominates the exhibition camera.
  box('front-cloth-work-surface-broad', 5.05, .06, 1.08, 0, .88, 1.70, mats.wood);
  const warpRoller = cyl('rear-warp-supply-beam', .24, 5.1, 0, 2.1, -2.18, mats.darkWood);
  warpRoller.visible = true;
  [-2.68, 2.68].forEach(x => {{
    const bearing = box('rear-warp-beam-bearing-block', .34, .48, .44, x, 2.10, -2.18, mats.darkWood);
    bearing.castShadow = true;
  }});
  // In exhibition mode the warp needs a visible, structurally connected
  // supply point. A rectangular rear beam reads as part of the loom frame
  // and prevents the incoming yarns from appearing to float in mid-air.
  const rearWarpAnchor = box('rear-warp-supply-anchor-beam', 5.15, .18, .22, 0, 2.56, -1.70, mats.darkWood);
  rearWarpAnchor.visible = state.exhibitionMode;
  const takeupRoller = cyl('cloth-roller-finished-area-takeup-roll-v4', .28, 4.9, 0, .74, 2.45, mats.darkWood);
  [-2.68, 2.68].forEach(x => {{
    box('front-cloth-beam-bearing-block', .34, .52, .46, x, .74, 2.45, mats.darkWood);
  }});
  const takeupBand = new THREE.Mesh(new THREE.TorusGeometry(.31, .018, 8, 36), mats.gold);
  takeupBand.name = 'takeup-roll-rotation-cue-v4';
  takeupBand.rotation.y = Math.PI / 2;
  takeupBand.position.set(2.55, .74, 2.45);
  loom.add(takeupBand);
  const shedOpening = new THREE.Group();
  shedOpening.name = 'shed-opening-v4-visible-warp-mouth';
  const upperShedPlane = new THREE.Mesh(new THREE.PlaneGeometry(4.8, .72), mats.translucentGold);
  upperShedPlane.name = 'upper-shed-plane-v4';
  upperShedPlane.rotation.x = -Math.PI / 2.9;
  upperShedPlane.position.set(0, 1.62, .72);
  const lowerShedPlane = new THREE.Mesh(new THREE.PlaneGeometry(4.8, .72), mats.translucentRed);
  lowerShedPlane.name = 'lower-shed-plane-v4';
  lowerShedPlane.rotation.x = -Math.PI / 3.35;
  lowerShedPlane.position.set(0, 1.34, .88);
  shedOpening.add(upperShedPlane, lowerShedPlane);
  loom.add(shedOpening);

  // Lower weaving mechanism: the shuttle runs on a rigid race, two heddle
  // frames separate the ground warp, and the breast beam supports the fell.
  const shuttleRace = box('wooden-shuttle-race-under-open-shed', 5.12, .075, .24, 0, 1.13, 1.46, mats.wood);
  shuttleRace.castShadow = true;
  const breastBeam = cyl('front-breast-beam-supporting-woven-fell', .13, 5.18, 0, 1.00, 1.12, mats.darkWood);
  function makeHeddleFrame(name, z, cordOffset) {{
    const frame = new THREE.Group();
    frame.name = name;
    const top = new THREE.Mesh(new THREE.BoxGeometry(5.05, .12, .10), mats.darkWood);
    const bottom = top.clone();
    top.position.y = .40;
    bottom.position.y = -.40;
    const left = new THREE.Mesh(new THREE.BoxGeometry(.12, .88, .10), mats.wood);
    const right = left.clone();
    left.position.x = -2.48;
    right.position.x = 2.48;
    frame.add(top, bottom, left, right);
    for (let i = 0; i < 32; i++) {{
      const cord = new THREE.Mesh(new THREE.BoxGeometry(.007, .70, .008), i % 5 === cordOffset ? mats.activeCord : mats.paleWarp);
      cord.name = 'ground-heddle-frame-wire';
      cord.position.x = -2.36 + i * (4.72 / 31);
      frame.add(cord);
    }}
    frame.position.set(0, 1.82, z);
    frame.children.forEach(part => {{ part.castShadow = true; }});
    loom.add(frame);
    return frame;
  }}
  const frontHeddleFrame = makeHeddleFrame('front-ground-heddle-frame', .30, 1);
  const rearHeddleFrame = makeHeddleFrame('rear-ground-heddle-frame', .02, 3);
  const treadleLinkCords = [];
  [-2.78, -2.32].forEach((x, i) => {{
    const link = beamBetween(
      i === 0 ? 'active-treadle-to-front-heddle-link' : 'return-treadle-to-rear-heddle-link',
      new THREE.Vector3(x, .27, 1.18),
      new THREE.Vector3(i === 0 ? -1.45 : -1.12, 1.46, i === 0 ? .30 : .02),
      .012,
      i === 0 ? mats.activeCord : mats.cord
    );
    treadleLinkCords.push(link);
  }});

  const cords = [];
  const cordCurtain = new THREE.Group();
  cordCurtain.name = 'overhead-golden-cord-curtain-reference-inspired';
  cordCurtain.visible = !state.exhibitionMode;
  loom.add(cordCurtain);
  for (let i = 0; i < 44; i++) {{
    const x = -2.72 + i * .126;
    const z = -1.48 + (i % 3) * .10;
    const selectedCord = i % 5 === 0 || i % 9 === 2;
    const cord = new THREE.Mesh(new THREE.CylinderGeometry(.010, .010, 2.34 + (i % 4) * .08, 8), selectedCord ? mats.activeCord : mats.cord);
    cord.name = 'draw-cord-continuous';
    cord.position.set(x, 3.50, z);
    cord.castShadow = true;
    cordCurtain.add(cord);
    cords.push({{mesh: cord, active: selectedCord}});
  }}
  const tallWarpCurtain = new THREE.Group();
  tallWarpCurtain.name = 'v18-layered-dahua-lou-warp-curtain-reduced-line-clutter';
  tallWarpCurtain.visible = !state.exhibitionMode;
  loom.add(tallWarpCurtain);
  const frontWarpSheet = new THREE.Mesh(new THREE.PlaneGeometry(5.80, 3.85, 1, 1), mats.warpSheet);
  frontWarpSheet.name = 'v18-structural-warp-layer-sheet-front-not-individual-lines';
  frontWarpSheet.position.set(0, 2.95, .05);
  tallWarpCurtain.add(frontWarpSheet);
  const rearWarpSheet = frontWarpSheet.clone();
  rearWarpSheet.name = 'v18-structural-warp-layer-sheet-rear-not-individual-lines';
  rearWarpSheet.position.z = -.18;
  tallWarpCurtain.add(rearWarpSheet);
  for (let i = 0; i < 72; i++) {{
    const x = -2.92 + i * .082;
    const important = i % 6 === 0 || i % 11 === 3;
    const thread = new THREE.Mesh(new THREE.CylinderGeometry(important ? .0075 : .0045, important ? .0075 : .0045, 3.95, 6), important ? mats.activeWarp : mats.paleWarp);
    thread.name = important ? 'v18-highlighted-moving-warp-reference-line' : 'v18-muted-reference-warp-line';
    thread.position.set(x, 2.95, -.02 + (i % 4) * .012);
    thread.visible = important || i % 4 === 0;
    thread.castShadow = true;
    tallWarpCurtain.add(thread);
  }}

  const warpThreads = [];
  for (let i = 0; i < 86; i++) {{
    const x = -2.72 + i * .064;
    const selected = i % 5 === 1 || i % 13 === 0;
    const thread = new THREE.Mesh(new THREE.CylinderGeometry(selected ? .010 : .0065, selected ? .010 : .0065, 4.55, 8), selected ? mats.activeWarp : mats.warp);
    thread.name = selected ? 'warp-thread-raised-smooth' : 'warp-thread-fixed';
    thread.rotation.x = Math.PI / 2;
    thread.position.set(x, 1.96, .08);
    loom.add(thread);
    warpThreads.push({{mesh: thread, selected}});
  }}
  warpThreads.forEach((item) => {{ item.mesh.visible = !state.exhibitionMode; }});

  // Exhibition-only functional thread paths. Each warp now has one readable
  // route: rear supply -> heddle lift point -> open shed -> fixed fell.
  const functionalWarpLines = [];
  const functionalDrawCords = [];
  const functionalHeddleEyes = [];
  for (let i = 0; i < 64; i++) {{
    const x = -2.42 + i * (4.84 / 63);
    // The upper control bank is narrower than the lower warp field. Keep the
    // outer cord anchors inside its wooden frame, then fan them gently toward
    // the wider heddle/warp positions below.
    const controlX = -2.12 + i * (4.24 / 63);
    const bank = i % 5;
    const selected = bank === 0;
    const warpGeometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x, 2.56, -1.58),
      new THREE.Vector3(x, 1.92, .32),
      new THREE.Vector3(x, 1.52, .92),
      // Loose warp ends exactly at the fell. It must not continue over the
      // finished-cloth area before a weft pick has been packed into it.
      new THREE.Vector3(x, 1.205, 1.18)
    ]);
    const warpMaterial = new THREE.LineBasicMaterial({{
      color: selected ? 0xb52d48 : 0xf2d69b,
      transparent: false,
      opacity: 1
    }});
    const warpLine = new THREE.Line(warpGeometry, warpMaterial);
    warpLine.name = selected ? 'functional-raised-warp-path' : 'functional-lowered-warp-path';
    warpLine.visible = state.exhibitionMode;
    loom.add(warpLine);
    functionalWarpLines.push({{line: warpLine, selected, bank}});

    // Give every visible warp its own upper control route.  The earlier
    // every-third-line sampling made the upper and lower banks look unrelated.
    {{
      const cordGeometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(controlX, 5.32, -1.38),
        new THREE.Vector3(controlX, 3.62, -.38),
        new THREE.Vector3(x, 1.92, .32)
      ]);
      const cordMaterial = new THREE.LineBasicMaterial({{
        color: selected ? 0xc62e4d : 0xd9b866,
        transparent: false,
        opacity: 1
      }});
      const cordLine = new THREE.Line(cordGeometry, cordMaterial);
      cordLine.name = 'functional-draw-cord-to-heddle-path';
      cordLine.visible = state.exhibitionMode;
      loom.add(cordLine);
      functionalDrawCords.push({{line: cordLine, selected, bank, warpIndex: i}});
    }}

    const eye = new THREE.Mesh(
      new THREE.SphereGeometry(selected ? .028 : .020, 8, 6),
      selected ? mats.activeCord : mats.gold
    );
    eye.name = 'functional-heddle-eye-shared-cord-warp-junction';
    eye.position.set(x, 1.92, .32);
    eye.visible = state.exhibitionMode;
    loom.add(eye);
    functionalHeddleEyes.push({{mesh: eye, bank, warpIndex: i}});
  }}

  const clothCanvas = document.createElement('canvas');
  clothCanvas.width = 1024;
  clothCanvas.height = 512;
  const ctx = clothCanvas.getContext('2d');
  function paintTeachingCloth(progress) {{
    progress = Math.max(0, Math.min(1, progress));
    const wovenTop = Math.round(512 * (1 - progress));
    ctx.fillStyle = '#9f2538';
    ctx.fillRect(0, 0, 1024, 512);
    ctx.fillStyle = '#7d1728';
    ctx.fillRect(0, 0, 1024, 46);
    ctx.fillRect(0, 466, 1024, 46);
    ctx.strokeStyle = 'rgba(245, 212, 172, .34)';
    ctx.lineWidth = 1;
    for (let x = 8; x < 1024; x += 10) {{
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + Math.sin(x * .04) * 4, 512);
      ctx.stroke();
    }}
    ctx.strokeStyle = 'rgba(80, 20, 24, .26)';
    for (let y = 12; y < 512; y += 12) {{
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(1024, y + Math.sin(y * .05) * 2);
      ctx.stroke();
    }}
    ctx.fillStyle = '#d5aa50';
    for (let y = 74; y < 442; y += 72) {{
      for (let x = 28; x < 996; x += 92) {{
        ctx.beginPath();
        ctx.ellipse(x, y, 23, 13, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(x + 35, y + 25, 18, 10, .7, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}
    ctx.strokeStyle = '#356864';
    ctx.lineWidth = 10;
    for (let y = 92; y < 438; y += 96) {{
      ctx.beginPath();
      for (let x = 0; x <= 1024; x += 24) {{
        const yy = y + Math.sin(x / 48) * 18;
        if (x === 0) ctx.moveTo(x, yy); else ctx.lineTo(x, yy);
      }}
      ctx.stroke();
    }}
    ctx.strokeStyle = 'rgba(87,59,37,.28)';
    ctx.lineWidth = 3;
    for (let y = 70; y < 458; y += 22) {{
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(1024, y + Math.sin(y * .06) * 3);
      ctx.stroke();
    }}
    if (!state.exhibitionMode) {{
      // Teaching mode keeps an explicit unwoven white zone. Exhibition mode
      // must not paint that zone onto the cloth mesh because it looks like a
      // second sheet of fabric rather than loose warp yarns.
      ctx.fillStyle = 'rgba(255,250,242,.88)';
      ctx.fillRect(0, 0, 1024, wovenTop);
      ctx.strokeStyle = 'rgba(180, 130, 80, .82)';
      ctx.lineWidth = 2;
      for (let x = 16; x < 1024; x += 18) {{
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x + Math.sin(x * .05) * 7, wovenTop);
        ctx.stroke();
      }}
      ctx.fillStyle = '#d5aa50';
      ctx.fillRect(0, Math.max(0, wovenTop - 10), 1024, 20);
      ctx.fillStyle = '#8b2940';
      ctx.fillRect(0, Math.max(0, wovenTop - 3), 1024, 6);
      ctx.fillStyle = '#f0c46d';
      for (let n = 0; n < 4; n++) {{
        const rowY = Math.min(510, wovenTop + 16 + n * 18);
        ctx.fillRect(0, rowY, 1024, 5);
      }}
      ctx.fillStyle = '#573b25';
      ctx.font = 'bold 24px Microsoft YaHei, Arial';
      ctx.fillText('织口 / woven edge', 34, Math.max(34, wovenTop - 18));
      ctx.fillStyle = '#573b25';
      ctx.font = 'bold 28px Microsoft YaHei, Arial';
      ctx.fillText('教学视觉示意 / teaching visual motif', 32, 500);
    }} else {{
      const glow = ctx.createLinearGradient(0, 390, 1024, 512);
      glow.addColorStop(0, 'rgba(255,221,142,.12)');
      glow.addColorStop(.5, 'rgba(255,221,142,.34)');
      glow.addColorStop(1, 'rgba(255,221,142,.10)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, Math.max(0, wovenTop + 12), 1024, 512);
    }}
  }}
  paintTeachingCloth(state.mapping.woven_cloth_ratio);
  const clothTexture = new THREE.CanvasTexture(clothCanvas);
  clothTexture.colorSpace = THREE.SRGBColorSpace;
  clothTexture.wrapS = THREE.RepeatWrapping;
  clothTexture.wrapT = THREE.RepeatWrapping;
  clothTexture.anisotropy = Math.min(12, renderer.capabilities.getMaxAnisotropy());
  const clothMat = new THREE.MeshPhysicalMaterial({{
    map: clothTexture,
    bumpMap: clothTexture,
    bumpScale: state.exhibitionMode ? .010 : .006,
    roughness: state.exhibitionMode ? .40 : .70,
    metalness: state.exhibitionMode ? .055 : 0,
    sheen: state.exhibitionMode ? .96 : .54,
    sheenColor: new THREE.Color(0xffd89a),
    sheenRoughness: state.exhibitionMode ? .34 : .60,
    clearcoat: state.exhibitionMode ? .055 : 0,
    clearcoatRoughness: .72,
    emissive: new THREE.Color(0x26090e),
    emissiveIntensity: state.exhibitionMode ? .10 : .035,
    side: THREE.DoubleSide
  }});
  // Exhibition cloth exists only between the fixed fell and the take-up roll.
  // The former 4.6-unit plane extended backward through the shed and looked
  // like a finished cloth sheet floating in the middle of the loom.
  const exhibitionClothRun = 1.28;
  const clothAngle = state.exhibitionMode ? -1.47 : -Math.PI / 2.55;
  const clothPlane = new THREE.Mesh(
    new THREE.PlaneGeometry(4.85, state.exhibitionMode ? exhibitionClothRun : 4.60, 32, 24),
    clothMat
  );
  clothPlane.name = state.exhibitionMode
    ? 'finished-cloth-only-from-fixed-fell-to-takeup-roll'
    : 'continuous-cloth-plane-procedural-teaching-motif';
  clothPlane.rotation.x = clothAngle;
  if (state.exhibitionMode) {{
    clothPlane.position.set(
      0,
      1.16 - (exhibitionClothRun * .5) * Math.cos(clothAngle),
      1.18 - (exhibitionClothRun * .5) * Math.sin(clothAngle)
    );
  }} else {{
    clothPlane.position.set(0, .98, 1.28);
  }}
  clothPlane.castShadow = true;
  clothPlane.receiveShadow = false;
  loom.add(clothPlane);
  const outputClothTexture = clothTexture.clone();
  outputClothTexture.wrapS = THREE.RepeatWrapping;
  outputClothTexture.wrapT = THREE.RepeatWrapping;
  outputClothTexture.needsUpdate = true;
  const outputClothMat = clothMat.clone();
  outputClothMat.map = outputClothTexture;
  outputClothMat.transparent = true;
  outputClothMat.opacity = 0;
  const rollerWrapGeometry = new THREE.PlaneGeometry(4.75, 1, 24, 10);
  const rollerWrapPositions = rollerWrapGeometry.attributes.position;
  const rollerWrapArcRatios = new Float32Array(rollerWrapPositions.count);
  for (let i = 0; i < rollerWrapPositions.count; i++) {{
    const localY = rollerWrapPositions.getY(i);
    const arcRatio = .5 - localY;
    rollerWrapArcRatios[i] = arcRatio;
    const theta = arcRatio * Math.PI * .5;
    rollerWrapPositions.setY(i, .74 + .292 * Math.cos(theta));
    rollerWrapPositions.setZ(i, 2.45 + .292 * Math.sin(theta));
  }}
  rollerWrapPositions.needsUpdate = true;
  rollerWrapGeometry.computeVertexNormals();
  const rollerClothWrap = new THREE.Mesh(rollerWrapGeometry, outputClothMat);
  rollerClothWrap.name = 'cloth-quarter-wrap-connecting-top-run-to-cloth-roll';
  rollerClothWrap.visible = state.exhibitionMode;
  rollerClothWrap.castShadow = true;
  rollerClothWrap.receiveShadow = false;
  loom.add(rollerClothWrap);
  const clothRollMount = new THREE.Group();
  clothRollMount.name = 'finished-cloth-roll-mounted-on-wooden-takeup-axis';
  clothRollMount.position.set(0, .74, 2.45);
  clothRollMount.rotation.z = Math.PI / 2;
  const clothRollSpin = new THREE.Group();
  clothRollMount.add(clothRollSpin);
  const rollClothTexture = clothTexture.clone();
  rollClothTexture.wrapS = THREE.RepeatWrapping;
  rollClothTexture.wrapT = THREE.RepeatWrapping;
  // Cylinder UVs use U around the roll and V along its axis. Rotate the flat
  // cloth map so the fabric width stays aligned with the wooden roller rather
  // than turning into broad, mismatched colour bands around the cylinder.
  rollClothTexture.center.set(.5, .5);
  rollClothTexture.rotation = Math.PI / 2;
  rollClothTexture.needsUpdate = true;
  const clothRollMaterial = new THREE.MeshPhysicalMaterial({{
    color: 0xffffff,
    map: rollClothTexture,
    bumpMap: rollClothTexture,
    bumpScale: .008,
    roughness: .46,
    metalness: .035,
    sheen: .88,
    sheenColor: new THREE.Color(0xffd59a),
    sheenRoughness: .38,
    emissive: 0x321016,
    emissiveIntensity: .12,
    transparent: true,
    opacity: 0
  }});
  const clothRollLayer = new THREE.Mesh(
    new THREE.CylinderGeometry(.296, .296, 4.68, 32, 1, true),
    clothRollMaterial
  );
  clothRollLayer.name = 'thin-finished-cloth-layer-wound-on-takeup-axis';
  clothRollLayer.castShadow = false;
  clothRollLayer.receiveShadow = false;
  clothRollSpin.add(clothRollLayer);
  clothRollMount.visible = state.exhibitionMode;
  loom.add(clothRollMount);
  const redWarpSurface = new THREE.Mesh(new THREE.PlaneGeometry(5.02, 1.72, 1, 1), mats.redSilkSurface);
  redWarpSurface.name = 'video-observed-red-warp-surface-v9';
  redWarpSurface.rotation.x = -Math.PI / 2.55;
  redWarpSurface.position.set(0, 1.015, .90);
  redWarpSurface.visible = !state.exhibitionMode;
  loom.add(redWarpSurface);
  const videoReferencePanel = new THREE.Group();
  videoReferencePanel.name = 'v13-video-reference-red-gold-jacquard-control-wall';
  const panelBack = new THREE.Mesh(new THREE.BoxGeometry(5.32, 1.56, .075), mats.deepVideoRed);
  panelBack.name = 'v13-video-reference-red-jacquard-panel';
  panelBack.position.set(0, 2.05, -.34);
  panelBack.castShadow = true;
  panelBack.receiveShadow = true;
  videoReferencePanel.add(panelBack);
  const panelTopBand = new THREE.Mesh(new THREE.BoxGeometry(5.45, .09, .09), mats.silkGold);
  panelTopBand.name = 'v13-video-reference-gold-panel-rail';
  panelTopBand.position.set(0, 2.87, -.29);
  videoReferencePanel.add(panelTopBand);
  const panelBottomBand = panelTopBand.clone();
  panelBottomBand.name = 'v13-video-reference-gold-panel-lower-rail';
  panelBottomBand.position.set(0, 1.23, -.29);
  videoReferencePanel.add(panelBottomBand);
  const jacquardPegRows = [];
  for (let row = 0; row < 5; row++) {{
    for (let col = 0; col < 23; col++) {{
      const peg = new THREE.Mesh(new THREE.BoxGeometry(.060, .025, .030), (row + col) % 4 === 0 ? mats.activeCord : mats.silkGold);
      peg.name = 'v13-video-reference-gold-pegs-on-red-panel';
      peg.position.set(-2.55 + col * .232, 1.44 + row * .30 + Math.sin(col * .8 + row) * .018, -.245);
      peg.scale.y = .70;
      videoReferencePanel.add(peg);
      jacquardPegRows.push(peg);
    }}
  }}
  const denseVideoCordLines = [];
  for (let i = 0; i < 96; i++) {{
    const x = -2.58 + i * .054;
    const mat = i % 7 === 0 ? mats.activeCord : (i % 5 === 0 ? mats.silkGold : mats.cord);
    const line = new THREE.Mesh(new THREE.CylinderGeometry(.0048, .0048, 1.64, 6), mat);
    line.name = 'v13-video-like-dense-cord-curtain';
    line.rotation.x = Math.PI / 2;
    line.position.set(x, 2.05, -.215 + (i % 4) * .006);
    videoReferencePanel.add(line);
    denseVideoCordLines.push(line);
  }}
  loom.add(videoReferencePanel);
  // The pegs and dense control curtain are teaching/diagnostic overlays,
  // not physical loom members. Keep the exhibition view focused on the
  // actual frame, warp, reed and cloth.
  videoReferencePanel.visible = !state.exhibitionMode;
  const redClothBed = new THREE.Mesh(new THREE.BoxGeometry(5.08, .035, 1.18), mats.deepVideoRed);
  redClothBed.name = 'v13-video-reference-red-silk-cloth-bed';
  redClothBed.position.set(0, .955, 1.48);
  redClothBed.castShadow = true;
  redClothBed.receiveShadow = true;
  // The procedural cloth already supplies the exhibition fabric surface.
  // Keep this reference backing only for teaching mode to avoid a duplicate
  // red slab under the cloth.
  redClothBed.visible = !state.exhibitionMode;
  loom.add(redClothBed);
  const v13MotionProfile = new THREE.Group();
  v13MotionProfile.name = 'v13-larger-human-motion-profile-video-inspired';
  loom.add(v13MotionProfile);
  // The fell is the fixed boundary where a loose weft becomes woven cloth.
  // Keeping it stationary makes the cause-and-effect chain readable.
  const fellZ = 1.18;
  const wovenEdge = new THREE.Mesh(new THREE.BoxGeometry(4.95, .055, .055), mats.gold);
  wovenEdge.name = 'fixed-fell-boundary-where-weft-becomes-cloth';
  wovenEdge.castShadow = true;
  loom.add(wovenEdge);
  const newlyWovenPickMaterial = new THREE.MeshStandardMaterial({{
    color: 0xffd36a,
    emissive: 0x6b2f08,
    emissiveIntensity: .72,
    roughness: .42,
    transparent: true,
    opacity: .94
  }});
  const clothGrowthMarker = new THREE.Mesh(new THREE.BoxGeometry(4.76, .050, .050), newlyWovenPickMaterial);
  clothGrowthMarker.name = 'newly-woven-pick-moving-from-fell-into-finished-cloth';
  clothGrowthMarker.castShadow = true;
  loom.add(clothGrowthMarker);

  const patternDraftBoard = new THREE.Group();
  patternDraftBoard.name = 'pattern-draft-board-stage-1';
  const draftBack = new THREE.Mesh(new THREE.BoxGeometry(1.2, .82, .045), mats.translucentGold);
  draftBack.position.set(0, .42, 0);
  patternDraftBoard.add(draftBack);
  for (let i = 0; i < 5; i++) {{
    const motif = new THREE.Mesh(new THREE.TorusGeometry(.12 + i * .018, .009, 8, 36), i % 2 ? mats.cueRed : mats.cueTeal);
    motif.position.set(-.38 + i * .19, .42 + Math.sin(i) * .12, .035);
    motif.scale.y = .56;
    patternDraftBoard.add(motif);
  }}
  patternDraftBoard.position.set(2.9, 1.45, 2.32);
  patternDraftBoard.rotation.y = -.38;
  scene.add(patternDraftBoard);

  const tiePatternSymbols = new THREE.Group();
  tiePatternSymbols.name = 'tie-pattern-symbols-stage-2';
  for (let i = 0; i < 12; i++) {{
    const knot = new THREE.Mesh(new THREE.CylinderGeometry(.025, .025, .10, 8), i % 3 === 0 ? mats.activeCord : mats.gold);
    knot.position.set(-.55 + (i % 6) * .22, .18 + Math.floor(i / 6) * .26, 0);
    tiePatternSymbols.add(knot);
  }}
  tiePatternSymbols.position.set(2.8, 2.45, -1.25);
  scene.add(tiePatternSymbols);

  const warpPreparationComb = new THREE.Group();
  warpPreparationComb.name = 'warp-preparation-comb-stage-3';
  const combBack = new THREE.Mesh(new THREE.BoxGeometry(2.9, .08, .08), mats.gold);
  warpPreparationComb.add(combBack);
  for (let i = 0; i < 18; i++) {{
    const tooth = new THREE.Mesh(new THREE.BoxGeometry(.025, .36, .045), mats.paleWarp);
    tooth.position.set(-1.35 + i * .16, -.20, 0);
    warpPreparationComb.add(tooth);
  }}
  warpPreparationComb.position.set(0, 1.40, .72);
  loom.add(warpPreparationComb);

  const shuttle = new THREE.Group();
  shuttle.name = 'smooth-shuttle-and-weft';
  const shuttleBody = new THREE.Mesh(new THREE.BoxGeometry(.58, .09, .13), mats.darkWood);
  shuttleBody.name = 'wooden-boat-shuttle-body';
  shuttleBody.castShadow = true;
  shuttle.add(shuttleBody);
  [-1, 1].forEach((side) => {{
    const tip = new THREE.Mesh(new THREE.ConeGeometry(.075, .18, 6), mats.wood);
    tip.name = 'wooden-shuttle-tapered-tip';
    tip.rotation.z = side > 0 ? -Math.PI / 2 : Math.PI / 2;
    tip.position.x = side * .38;
    shuttle.add(tip);
  }});
  const shuttleBobbin = new THREE.Mesh(new THREE.CylinderGeometry(.045, .045, .24, 10), mats.gold);
  shuttleBobbin.name = 'shuttle-thread-bobbin';
  shuttleBobbin.rotation.z = Math.PI / 2;
  shuttle.add(shuttleBobbin);
  const weft = new THREE.Mesh(new THREE.CylinderGeometry(.006, .006, .68, 6), mats.activeCord);
  weft.name = 'fine-red-weft-yarn-carried-by-shuttle';
  weft.rotation.z = Math.PI / 2;
  weft.position.z = .075;
  shuttle.add(weft);
  const shuttleControlHalo = new THREE.Mesh(
    new THREE.TorusGeometry(.17, .020, 8, 36),
    mats.motionGold.clone()
  );
  shuttleControlHalo.name = 'hand-to-shuttle-control-contact-halo';
  shuttleControlHalo.rotation.y = Math.PI / 2;
  shuttleControlHalo.material.opacity = 0;
  shuttleControlHalo.visible = false;
  shuttle.add(shuttleControlHalo);
  loom.add(shuttle);
  // Five selectable pattern-cord handles replace the former single rigid red
  // lever. Their upper ends stay fixed to the flower tower while only the
  // selected lower handle travels with the draw worker's hands.
  const drawControlHandles = [];
  const controlHandleRestY = 4.20;
  for (let bank = 0; bank < 5; bank++) {{
    // Keep the five selections inside one seated worker's natural reach.
    // The cords above fan out to the mechanism; the hand grips themselves
    // form a compact operating bank beside the worker.
    const x = -2.56 + bank * .09;
    const z = -.50;
    const cordMaterial = new THREE.LineBasicMaterial({{color: bank === 0 ? 0xc62e4d : 0xd9b866}});
    const cordGeometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(x, 5.30, -1.22),
      new THREE.Vector3(x, 4.76, -.84),
      new THREE.Vector3(x, controlHandleRestY, z)
    ]);
    const cord = new THREE.Line(cordGeometry, cordMaterial);
    cord.name = 'selectable-pattern-control-cord-bank-' + bank;
    cord.visible = state.exhibitionMode;
    loom.add(cord);
    const grip = new THREE.Mesh(new THREE.CylinderGeometry(.032, .032, .30, 12), mats.darkWood);
    grip.name = 'short-wooden-pattern-cord-grip-bank-' + bank;
    // Align the short grip with the worker's shoulder line so each hand
    // reaches its own end instead of both arms converging across the body.
    grip.rotation.x = Math.PI / 2;
    grip.position.set(x, controlHandleRestY, z);
    grip.castShadow = true;
    grip.visible = state.exhibitionMode;
    loom.add(grip);
    const knot = new THREE.Mesh(new THREE.SphereGeometry(.045, 10, 8), bank === 0 ? mats.activeCord : mats.gold);
    knot.name = 'pattern-cord-selection-knot-bank-' + bank;
    knot.position.set(x, controlHandleRestY + .06, z);
    knot.visible = state.exhibitionMode;
    loom.add(knot);
    drawControlHandles.push({{bank, x, z, cord, grip, knot}});
  }}
  const beater = new THREE.Group();
  beater.name = 'weaver-beater-reed-frame-linked-to-shuttle-v4';
  const beaterBar = new THREE.Mesh(new THREE.BoxGeometry(3.1, .055, .08), mats.darkWood);
  beaterBar.castShadow = true;
  const beaterTop = new THREE.Mesh(new THREE.BoxGeometry(3.15, .055, .08), mats.darkWood);
  beaterTop.position.y = .42;
  beaterTop.castShadow = true;
  const beaterLeft = new THREE.Mesh(new THREE.BoxGeometry(.055, .47, .07), mats.darkWood);
  beaterLeft.position.set(-1.58, .20, 0);
  const beaterRight = new THREE.Mesh(new THREE.BoxGeometry(.055, .47, .07), mats.darkWood);
  beaterRight.position.set(1.58, .20, 0);
  beater.add(beaterBar, beaterTop, beaterLeft, beaterRight);
  // Pale edge lines make both sides of the reed frame read as the same
  // woven working surface, instead of leaving the enlarged frame visually
  // empty at its ends.
  const beaterLeftWhiteLine = new THREE.Mesh(new THREE.BoxGeometry(.018, .38, .024), mats.paleWarp);
  beaterLeftWhiteLine.name = 'beater-left-edge-white-warp-line';
  beaterLeftWhiteLine.position.set(-1.48, .20, .045);
  const beaterRightWhiteLine = beaterLeftWhiteLine.clone();
  beaterRightWhiteLine.name = 'beater-right-edge-white-warp-line';
  beaterRightWhiteLine.position.x = 1.48;
  beater.add(beaterLeftWhiteLine, beaterRightWhiteLine);
  const operatorGripBar = new THREE.Mesh(new THREE.BoxGeometry(1.35, .13, .20), mats.wood);
  operatorGripBar.name = 'near-side-weaver-operator-grip-extension';
  // Its rear face overlaps the reed side member at z=0, making this a single
  // connected beater assembly instead of a floating handle in front of it.
  operatorGripBar.position.set(-2.12, .20, .10);
  operatorGripBar.castShadow = true;
  beater.add(operatorGripBar);
  for (let i = 0; i < 21; i++) {{
    const reed = new THREE.Mesh(new THREE.BoxGeometry(.012, .38, .024), mats.paleWarp);
    reed.name = 'reed-tooth-for-beating-weft-v4';
    reed.position.set(-1.48 + i * (2.96 / 20), .20, .02);
    beater.add(reed);
  }}
  loom.add(beater);
  const treadleGroup = new THREE.Group();
  treadleGroup.name = 'two-visible-foot-treadles-directly-under-lower-weaver';
  for (let i = 0; i < 2; i++) {{
    // Long front-to-back wooden boards sit directly beneath the two feet.
    // Raising them to the foot plane prevents the bench from hiding them.
    const pedal = new THREE.Mesh(new THREE.BoxGeometry(.26, .07, 1.60), i === 0 ? mats.gold : mats.wood);
    pedal.name = i === 0 ? 'visible-active-treadle-under-left-foot' : 'visible-return-treadle-under-right-foot';
    pedal.position.set(-2.78 + i * .46, .285, 1.95);
    pedal.castShadow = true;
    treadleGroup.add(pedal);
  }}
  loom.add(treadleGroup);
  const insertedPick = new THREE.Mesh(new THREE.BoxGeometry(4.65, .032, .032), mats.activeCord);
  insertedPick.name = 'single-visible-weft-pick-shuttle-to-fell-to-cloth';
  insertedPick.castShadow = true;
  loom.add(insertedPick);
  const recentWovenRows = new THREE.Group();
  recentWovenRows.name = 'recent-packed-weft-rows-immediately-behind-fixed-fell';
  // Tightly packed picks immediately behind the fell expose the short zone in
  // which separate warp and weft become one continuous fabric surface.
  for (let i = 0; i < 14; i++) {{
    const row = new THREE.Mesh(
      new THREE.BoxGeometry(4.65, .014, .018),
      i % 4 === 0 ? mats.activeCord : mats.silkGold
    );
    row.name = 'packed-weft-row-already-integrated-into-cloth';
    row.position.set(0, 1.172 - i * .0015, fellZ + .025 + i * .023);
    recentWovenRows.add(row);
  }}
  loom.add(recentWovenRows);
  const drawMotionTrail = new THREE.Mesh(new THREE.BoxGeometry(.08, 1.15, .045), mats.motionRed);
  drawMotionTrail.name = 'v6-visible-motion-trail-draw-pull';
  drawMotionTrail.position.set(-2.48, 3.78, -.60);
  loom.add(drawMotionTrail);
  const shuttleMotionTrail = new THREE.Mesh(new THREE.BoxGeometry(4.55, .035, .09), mats.motionTeal);
  shuttleMotionTrail.name = 'v6-visible-motion-trail-shuttle-pass';
  shuttleMotionTrail.position.set(0, 1.46, 1.43);
  loom.add(shuttleMotionTrail);
  const beaterMotionSweep = new THREE.Mesh(new THREE.PlaneGeometry(2.55, .66), mats.motionRed);
  beaterMotionSweep.name = 'v6-visible-motion-sweep-beater';
  beaterMotionSweep.rotation.x = -Math.PI / 2;
  beaterMotionSweep.position.set(0, 1.26, 1.66);
  loom.add(beaterMotionSweep);
  const clothGrowthPulse = new THREE.Mesh(new THREE.BoxGeometry(4.75, .035, .08), mats.motionGold);
  clothGrowthPulse.name = 'v6-visible-cloth-growth-pulse-at-woven-edge';
  clothGrowthPulse.position.set(0, 1.22, 1.55);
  loom.add(clothGrowthPulse);
  const collaborationLoopRibbon = new THREE.Group();
  collaborationLoopRibbon.name = 'v19-single-continuous-collaboration-loop-visible-ribbon';
  loom.add(collaborationLoopRibbon);
  const upperToShedRibbon = new THREE.Mesh(new THREE.BoxGeometry(.08, 1.45, .035), mats.motionGold.clone());
  upperToShedRibbon.name = 'v19-loop-link-upper-operator-to-warp-shed';
  upperToShedRibbon.position.set(-2.25, 2.72, .34);
  const shedToShuttleRibbon = new THREE.Mesh(new THREE.BoxGeometry(3.95, .045, .035), mats.motionTeal.clone());
  shedToShuttleRibbon.name = 'v19-loop-link-shed-to-shuttle-path';
  shedToShuttleRibbon.position.set(-.08, 1.48, 1.36);
  const beaterToClothRibbon = new THREE.Mesh(new THREE.BoxGeometry(3.35, .045, .035), mats.motionRed.clone());
  beaterToClothRibbon.name = 'v19-loop-link-beater-to-cloth-growth';
  beaterToClothRibbon.position.set(.20, 1.16, 1.94);
  collaborationLoopRibbon.add(upperToShedRibbon, shedToShuttleRibbon, beaterToClothRibbon);
  const drawFlowBeads = [];
  for (let i = 0; i < 5; i++) {{
    const bead = new THREE.Mesh(new THREE.BoxGeometry(.045, .045, .045), mats.motionGold);
    bead.name = 'v12-draw-cord-flow-bead-continuous-step';
    bead.material = mats.motionGold.clone();
    bead.position.set(-3.05 + i * .18, 4.22, -.86);
    loom.add(bead);
    drawFlowBeads.push(bead);
  }}
  const shedFocusBand = new THREE.Mesh(new THREE.BoxGeometry(4.9, .045, .38), mats.motionGold);
  shedFocusBand.name = 'v12-shed-opening-focus-band-clear-step';
  shedFocusBand.material = mats.motionGold.clone();
  shedFocusBand.position.set(0, 1.52, .68);
  loom.add(shedFocusBand);
  const shuttlePathBand = new THREE.Mesh(new THREE.BoxGeometry(4.65, .035, .18), mats.motionTeal);
  shuttlePathBand.name = 'v12-shuttle-path-highlight-clear-step';
  shuttlePathBand.material = mats.motionTeal.clone();
  shuttlePathBand.position.set(0, 1.405, 1.47);
  loom.add(shuttlePathBand);
  const beaterImpactEdge = new THREE.Mesh(new THREE.BoxGeometry(4.75, .045, .06), mats.motionRed);
  beaterImpactEdge.name = 'v12-beater-impact-edge-clear-step';
  beaterImpactEdge.material = mats.motionRed.clone();
  beaterImpactEdge.position.set(0, 1.235, 1.72);
  loom.add(beaterImpactEdge);
  const takeupPulseRing = new THREE.Mesh(new THREE.TorusGeometry(.36, .026, 8, 48), mats.motionGold);
  takeupPulseRing.name = 'v12-takeup-roll-pulse-ring-clear-step';
  takeupPulseRing.material = mats.motionGold.clone();
  takeupPulseRing.rotation.y = Math.PI / 2;
  takeupPulseRing.position.set(-2.55, .74, 2.45);
  loom.add(takeupPulseRing);
  function makeActionArrow(name, mat) {{
    const group = new THREE.Group();
    group.name = name;
    const shaft = new THREE.Mesh(new THREE.CylinderGeometry(.025, .025, .64, 10), mat);
    shaft.position.y = .22;
    const head = new THREE.Mesh(new THREE.ConeGeometry(.09, .20, 16), mat);
    head.position.y = -.20;
    head.rotation.x = Math.PI;
    group.add(shaft, head);
    scene.add(group);
    return group;
  }}
  const drawPullCue = makeActionArrow('stage-4-obvious-pull-down-cue', mats.cueRed);
  const shuttleCue = makeActionArrow('stage-5-obvious-shuttle-travel-cue', mats.cueTeal);
  const clothAdvanceCue = makeActionArrow('stage-6-obvious-cloth-advance-cue', mats.cueGold);
  const beaterCue = makeActionArrow('stage-5-beater-forward-cue-v4', mats.cueRed);
  const treadleCue = makeActionArrow('stage-5-treadle-press-cue-v4', mats.cueGold);
  shuttleCue.rotation.z = -Math.PI / 2;
  // Cloth advances away from the fell toward +z and into the take-up roll.
  clothAdvanceCue.rotation.x = -Math.PI / 2;
  beaterCue.rotation.x = Math.PI / 2;
  treadleCue.rotation.x = Math.PI;

  function makeLimb(name, length, radius, mat) {{
    const g = new THREE.Group();
    g.name = name;
    const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 5, 10), mat);
    mesh.position.y = -length / 2;
    mesh.castShadow = true;
    g.add(mesh);
    return g;
  }}
  function hand(name, mat) {{
    const mesh = new THREE.Mesh(new THREE.CapsuleGeometry(.045, .085, 4, 8), mat);
    mesh.name = name;
    mesh.castShadow = true;
    return mesh;
  }}
  function joint(name, radius, mat) {{
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(radius, 12, 8), mat);
    mesh.name = name;
    mesh.castShadow = true;
    return mesh;
  }}
  function makeArmLink(name, radius, mat) {{
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius * .92, 1, 10), mat);
    mesh.name = name;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    return mesh;
  }}
  function positionArmLink(link, start, end) {{
    const direction = new THREE.Vector3().subVectors(end, start);
    const length = Math.max(.04, direction.length());
    link.position.copy(start).add(end).multiplyScalar(.5);
    link.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
    link.scale.set(1, length, 1);
  }}
  function addConnectedArmRig(worker, role, coatMat) {{
    const leftUpper = makeArmLink(role + '-left-connected-upper-arm', .070, coatMat);
    const rightUpper = makeArmLink(role + '-right-connected-upper-arm', .070, coatMat);
    const leftLower = makeArmLink(role + '-left-connected-forearm', .048, mats.skin);
    const rightLower = makeArmLink(role + '-right-connected-forearm', .048, mats.skin);
    const leftShoulder = joint(role + '-left-shoulder-seam', .085, coatMat);
    const rightShoulder = joint(role + '-right-shoulder-seam', .085, coatMat);
    const leftCuff = makeArmLink(role + '-left-woven-cuff-detail', .057, mats.gold);
    const rightCuff = makeArmLink(role + '-right-woven-cuff-detail', .057, mats.gold);
    worker.add(leftUpper, rightUpper, leftLower, rightLower, leftShoulder, rightShoulder, leftCuff, rightCuff);
    worker.userData.connectedArmLinks = {{leftUpper, rightUpper, leftLower, rightLower, leftCuff, rightCuff}};
    worker.userData.leftShoulder = leftShoulder;
    worker.userData.rightShoulder = rightShoulder;
    leftShoulder.position.set(-.30, .96, 0);
    rightShoulder.position.set(.30, .96, 0);
  }}
  function updateConnectedArmRig(worker) {{
    const links = worker.userData.connectedArmLinks;
    if (!links) return;
    const leftShoulder = new THREE.Vector3(-.30, .96, 0);
    const rightShoulder = new THREE.Vector3(.30, .96, 0);
    positionArmLink(links.leftUpper, leftShoulder, worker.userData.leftElbow.position);
    positionArmLink(links.rightUpper, rightShoulder, worker.userData.rightElbow.position);
    positionArmLink(links.leftLower, worker.userData.leftElbow.position, worker.userData.leftHand.position);
    positionArmLink(links.rightLower, worker.userData.rightElbow.position, worker.userData.rightHand.position);
    const leftCuffStart = worker.userData.leftElbow.position.clone().lerp(worker.userData.leftHand.position, .72);
    const leftCuffEnd = worker.userData.leftElbow.position.clone().lerp(worker.userData.leftHand.position, .82);
    const rightCuffStart = worker.userData.rightElbow.position.clone().lerp(worker.userData.rightHand.position, .72);
    const rightCuffEnd = worker.userData.rightElbow.position.clone().lerp(worker.userData.rightHand.position, .82);
    positionArmLink(links.leftCuff, leftCuffStart, leftCuffEnd);
    positionArmLink(links.rightCuff, rightCuffStart, rightCuffEnd);
  }}
  function placeHandAtWorld(worker, handMesh, worldPoint, maxReach = 1.52, shoulderSide = null) {{
    worker.updateMatrixWorld(true);
    const localTarget = worker.worldToLocal(worldPoint.clone());
    const side = shoulderSide === null ? (localTarget.x < 0 ? -1 : 1) : shoulderSide;
    const shoulder = new THREE.Vector3(side * .30, .96, 0);
    const offset = localTarget.clone().sub(shoulder);
    if (offset.length() > maxReach) {{
      localTarget.copy(shoulder).add(offset.normalize().multiplyScalar(maxReach));
    }}
    handMesh.position.copy(localTarget);
  }}
  function poseReachElbow(worker, handMesh, elbowMesh, side) {{
    const shoulder = new THREE.Vector3(side * .30, .96, 0);
    const hand = handMesh.position;
    elbowMesh.position.copy(shoulder).lerp(hand, .48);
    // A small forward/outward bend keeps the two connected arm segments
    // human-sized while allowing a mild reach extension at the loom.
    elbowMesh.position.x += side * .045;
    elbowMesh.position.y += .035;
    elbowMesh.position.z -= .075;
  }}
  function createWorker(role, coatMat) {{
    const worker = new THREE.Group();
    worker.name = role + '-low-poly-3d-worker-volume-articulated-skeleton-v11-humanized';
    const head = new THREE.Mesh(new THREE.SphereGeometry(.18, 20, 14), mats.skin);
    head.name = role + '-head';
    head.position.y = 1.24;
    head.castShadow = true;
    worker.add(head);
    const hairCap = new THREE.Mesh(new THREE.SphereGeometry(.188, 20, 12, 0, Math.PI * 2, 0, Math.PI * .58), mats.hair);
    hairCap.name = role + '-hair-cap-humanized-v11';
    hairCap.position.set(0, 1.31, -.012);
    hairCap.scale.set(1.03, .68, .95);
    hairCap.castShadow = true;
    const nose = new THREE.Mesh(new THREE.ConeGeometry(.026, .075, 8), mats.skin);
    nose.name = role + '-face-direction-nose-v11';
    nose.rotation.x = Math.PI / 2;
    nose.position.set(0, 1.245, -.18);
    const leftEye = new THREE.Mesh(new THREE.SphereGeometry(.016, 8, 6), mats.darkWood);
    leftEye.name = role + '-left-eye-v11';
    leftEye.position.set(-.055, 1.275, -.165);
    const rightEye = new THREE.Mesh(new THREE.SphereGeometry(.016, 8, 6), mats.darkWood);
    rightEye.name = role + '-right-eye-v11';
    rightEye.position.set(.055, 1.275, -.165);
    const leftEar = new THREE.Mesh(new THREE.SphereGeometry(.030, 10, 8), mats.skin);
    leftEar.name = role + '-left-ear-detail';
    leftEar.position.set(-.178, 1.245, -.012);
    leftEar.scale.set(.52, 1, .48);
    const rightEar = leftEar.clone();
    rightEar.name = role + '-right-ear-detail';
    rightEar.position.x = .178;
    worker.add(hairCap, nose, leftEye, rightEye, leftEar, rightEar);
    const torso = new THREE.Mesh(new THREE.CapsuleGeometry(.20, .58, 7, 14), coatMat);
    torso.name = role + '-torso';
    torso.position.y = .79;
    torso.scale.set(1.18, 1, .72);
    torso.castShadow = true;
    worker.add(torso);
    const robeFront = new THREE.Mesh(new THREE.BoxGeometry(.38, .42, .045), coatMat);
    robeFront.name = role + '-front-robe-plane-humanized-v11';
    robeFront.position.set(0, .74, -.17);
    robeFront.rotation.x = -.08;
    robeFront.castShadow = true;
    worker.add(robeFront);
    const robeSeam = new THREE.Mesh(new THREE.BoxGeometry(.018, .34, .052), mats.gold);
    robeSeam.name = role + '-fine-woven-front-seam';
    robeSeam.position.set(0, .75, -.198);
    const leftHem = new THREE.Mesh(new THREE.BoxGeometry(.12, .022, .052), mats.gold);
    leftHem.name = role + '-left-robe-hem-detail';
    leftHem.position.set(-.12, .545, -.195);
    const rightHem = leftHem.clone();
    rightHem.name = role + '-right-robe-hem-detail';
    rightHem.position.x = .12;
    worker.add(robeSeam, leftHem, rightHem);
    const collar = new THREE.Mesh(new THREE.TorusGeometry(.105, .014, 8, 24), mats.gold);
    collar.name = role + '-subtle-gold-collar-detail';
    collar.position.set(0, 1.045, -.035);
    collar.rotation.x = Math.PI / 2;
    collar.scale.y = .72;
    const waistSash = new THREE.Mesh(new THREE.CylinderGeometry(.215, .215, .045, 18), mats.darkWood);
    waistSash.name = role + '-woven-dark-waist-sash';
    waistSash.position.set(0, .57, 0);
    waistSash.scale.z = .74;
    waistSash.castShadow = true;
    worker.add(collar, waistSash);
    const neck = joint(role + '-neck-joint-v10', .055, mats.skin);
    neck.position.set(0, 1.05, 0);
    const waist = joint(role + '-waist-joint-v10', .075, coatMat);
    waist.position.set(0, .55, 0);
    worker.add(neck, waist);
    // One continuous clothed arm per side is easier to read in a moving
    // exhibition view than separately floating upper-arm/forearm primitives.
    const leftArm = makeLimb(role + '-left-arm-continuous', .72, .070, coatMat);
    const rightArm = makeLimb(role + '-right-arm-continuous', .72, .070, coatMat);
    const leftForearm = makeLimb(role + '-left-forearm-humanized-v11', .36, .043, mats.skin);
    const rightForearm = makeLimb(role + '-right-forearm-humanized-v11', .36, .043, mats.skin);
    const leftSleeve = makeLimb(role + '-left-sleeve-cloth-v11', .36, .066, coatMat);
    const rightSleeve = makeLimb(role + '-right-sleeve-cloth-v11', .36, .066, coatMat);
    leftArm.position.set(-.3, .96, 0);
    rightArm.position.set(.3, .96, 0);
    leftForearm.position.set(-.42, .70, -.23);
    rightForearm.position.set(.42, .70, -.23);
    leftSleeve.position.set(-.34, .88, -.08);
    rightSleeve.position.set(.34, .88, -.08);
    worker.add(leftArm, rightArm, leftForearm, rightForearm, leftSleeve, rightSleeve);
    const leftHand = hand(role + '-left-hand-targeting-tool', mats.skin);
    const rightHand = hand(role + '-right-hand-targeting-tool', mats.skin);
    const leftElbow = joint(role + '-left-elbow-joint-v11', .052, mats.skin);
    const rightElbow = joint(role + '-right-elbow-joint-v11', .052, mats.skin);
    const leftWrist = joint(role + '-left-wrist-joint-v11', .042, mats.skin);
    const rightWrist = joint(role + '-right-wrist-joint-v11', .042, mats.skin);
    worker.add(leftHand, rightHand, leftElbow, rightElbow, leftWrist, rightWrist);
    // Keep the legacy targets for the motion code. The visible arm silhouette
    // is rebuilt from shoulder -> elbow -> wrist every frame below, so hands
    // can reach the loom without visually separating from the torso.
    [leftForearm, rightForearm, leftSleeve, rightSleeve,
     leftElbow, rightElbow, leftWrist, rightWrist].forEach((part) => {{
      part.visible = false;
    }});
    leftArm.visible = false;
    rightArm.visible = false;
    addConnectedArmRig(worker, role, coatMat);
    const leftLeg = makeLimb(role + '-left-leg', .64, .065, mats.darkWood);
    const rightLeg = makeLimb(role + '-right-leg', .64, .065, mats.darkWood);
    leftLeg.position.set(-.15, .45, 0);
    rightLeg.position.set(.15, .45, 0);
    worker.add(leftLeg, rightLeg);
    worker.userData.leftArm = leftArm;
    worker.userData.rightArm = rightArm;
    worker.userData.leftForearm = leftForearm;
    worker.userData.rightForearm = rightForearm;
    worker.userData.leftSleeve = leftSleeve;
    worker.userData.rightSleeve = rightSleeve;
    worker.userData.leftLeg = leftLeg;
    worker.userData.rightLeg = rightLeg;
    worker.userData.leftHand = leftHand;
    worker.userData.rightHand = rightHand;
    worker.userData.leftElbow = leftElbow;
    worker.userData.rightElbow = rightElbow;
    worker.userData.leftWrist = leftWrist;
    worker.userData.rightWrist = rightWrist;
    worker.userData.neck = neck;
    worker.userData.waist = waist;
    worker.userData.head = head;
    worker.userData.hairCap = hairCap;
    worker.userData.nose = nose;
    worker.userData.robeFront = robeFront;
    return worker;
  }}
  function addSeatedContactRig(worker, role) {{
    worker.name += '-grounded-seated-contact-rig-v5';
    const hip = new THREE.Mesh(new THREE.BoxGeometry(.28, .18, .24), mats.teal);
    hip.name = role + '-hip-on-seat-contact-v5';
    hip.position.set(0, .43, .06);
    hip.castShadow = true;
    worker.add(hip);
    const leftFoot = new THREE.Mesh(new THREE.BoxGeometry(.18, .07, .28), mats.darkWood);
    leftFoot.name = role + '-left-foot-on-treadle-contact-v5';
    leftFoot.position.set(-.28, -.34, -.54);
    leftFoot.castShadow = true;
    worker.add(leftFoot);
    const rightFoot = new THREE.Mesh(new THREE.BoxGeometry(.18, .07, .28), mats.darkWood);
    rightFoot.name = role + '-right-foot-on-treadle-contact-v5';
    rightFoot.position.set(.18, -.34, -.52);
    rightFoot.castShadow = true;
    worker.add(rightFoot);
    worker.userData.leftFoot = leftFoot;
    worker.userData.rightFoot = rightFoot;
  }}
  function addConnectedSeatedLegRig(worker, role, coatMat) {{
    const leftThigh = makeArmLink(role + '-visible-left-thigh-to-knee', .075, coatMat);
    const rightThigh = makeArmLink(role + '-visible-right-thigh-to-knee', .075, coatMat);
    const leftShin = makeArmLink(role + '-visible-left-shin-to-active-treadle', .082, mats.legTeal);
    const rightShin = makeArmLink(role + '-visible-right-shin-to-return-treadle', .082, mats.legTeal);
    const leftKnee = joint(role + '-visible-left-knee-bending-for-treadle', .100, mats.legTeal);
    const rightKnee = joint(role + '-visible-right-knee-resting-over-treadle', .100, mats.legTeal);
    worker.add(leftThigh, rightThigh, leftShin, rightShin, leftKnee, rightKnee);
    worker.userData.connectedLegLinks = {{leftThigh, rightThigh, leftShin, rightShin}};
    worker.userData.leftKnee = leftKnee;
    worker.userData.rightKnee = rightKnee;
  }}
  function updateConnectedSeatedLegRig(worker, press) {{
    const links = worker.userData.connectedLegLinks;
    if (!links) return;
    const leftHip = new THREE.Vector3(-.15, .44, .02);
    const rightHip = new THREE.Vector3(.15, .44, .02);
    // Knees bend forward toward the loom, directly above their treadles.
    // Avoid the former lateral splay that read as a leg bending sideways.
    worker.userData.leftKnee.position.set(-.25, .14 - press * .28, -.08 - press * .10);
    worker.userData.rightKnee.position.set(.20, .10, -.08);
    positionArmLink(links.leftThigh, leftHip, worker.userData.leftKnee.position);
    positionArmLink(links.rightThigh, rightHip, worker.userData.rightKnee.position);
    positionArmLink(links.leftShin, worker.userData.leftKnee.position, worker.userData.leftFoot.position);
    positionArmLink(links.rightShin, worker.userData.rightKnee.position, worker.userData.rightFoot.position);
  }}
  function addStandingFootContacts(worker, role) {{
    const leftFoot = new THREE.Mesh(new THREE.BoxGeometry(.18, .07, .30), mats.darkWood);
    leftFoot.name = role + '-left-foot-on-upper-platform-v5';
    leftFoot.position.set(-.18, .07, .04);
    leftFoot.castShadow = true;
    const rightFoot = new THREE.Mesh(new THREE.BoxGeometry(.18, .07, .30), mats.darkWood);
    rightFoot.name = role + '-right-foot-on-upper-platform-v5';
    rightFoot.position.set(.18, .07, .04);
    rightFoot.castShadow = true;
    worker.add(leftFoot, rightFoot);
    worker.userData.leftFoot = leftFoot;
    worker.userData.rightFoot = rightFoot;
  }}
  const drawWorker = createWorker('upper-draw-worker', mats.red);
  drawWorker.name += '-v19-jointed-seated-primary-worker-stable-animation';
  // Keep the upper operator at the original side-seat position.  Moving the
  // whole figure inward makes the torso intersect the operation box.
  drawWorker.position.set(-2.74, 3.22, -.50);
  drawWorker.rotation.y = -Math.PI / 2;
  drawWorker.scale.set(.82, .756, .82);
  drawWorker.userData.leftLeg.rotation.z = .76;
  drawWorker.userData.rightLeg.rotation.z = -.76;
  drawWorker.userData.leftLeg.rotation.x = -1.18;
  drawWorker.userData.rightLeg.rotation.x = -1.12;
  addStandingFootContacts(drawWorker, 'upper-draw-worker');
  drawWorker.userData.leftArm.position.z = -.70;
  drawWorker.userData.rightArm.position.z = -.70;
  loom.add(drawWorker);
  const weaver = createWorker('lower-weaver', mats.teal);
  weaver.name += '-v19-jointed-seated-primary-worker-stable-animation';
  // Restore the original seated position beside the treadles and cloth edge.
  weaver.position.set(-2.60, .58, 2.35);
  weaver.rotation.y = -.08;
  weaver.scale.set(1.04, .84, 1.04);
  weaver.userData.leftLeg.rotation.z = .88;
  weaver.userData.rightLeg.rotation.z = -.88;
  weaver.userData.leftLeg.rotation.x = -1.08;
  weaver.userData.rightLeg.rotation.x = -1.02;
  addSeatedContactRig(weaver, 'lower-weaver');
  // Replace the old rigid leg rods with an articulated, visibly bending pair.
  weaver.userData.leftLeg.visible = false;
  weaver.userData.rightLeg.visible = false;
  addConnectedSeatedLegRig(weaver, 'lower-weaver', mats.teal);
  weaver.userData.leftArm.position.z = -.54;
  weaver.userData.rightArm.position.z = -.54;
  loom.add(weaver);
  function addProceduralClothingCoverage(worker, role, coatMat) {{
    const backPanel = new THREE.Mesh(new THREE.BoxGeometry(.48, .62, .040), coatMat);
    backPanel.name = role + '-v17-back-cloth-panel-no-nude-model';
    backPanel.position.set(0, .73, .18);
    backPanel.castShadow = true;
    const frontPanel = new THREE.Mesh(new THREE.BoxGeometry(.45, .58, .040), coatMat);
    frontPanel.name = role + '-v17-front-cloth-panel';
    frontPanel.position.set(0, .70, -.20);
    frontPanel.rotation.x = -.08;
    frontPanel.castShadow = true;
    const leftSleeve = new THREE.Mesh(new THREE.CapsuleGeometry(.070, .42, 5, 10), coatMat);
    leftSleeve.name = role + '-v17-visible-clothed-left-sleeve';
    leftSleeve.position.set(-.34, .84, -.08);
    leftSleeve.rotation.z = -.38;
    const rightSleeve = leftSleeve.clone();
    rightSleeve.name = role + '-v17-visible-clothed-right-sleeve';
    rightSleeve.position.x = .34;
    rightSleeve.rotation.z = .38;
    worker.add(backPanel, frontPanel, leftSleeve, rightSleeve);
    worker.userData.backPanel = backPanel;
    worker.userData.frontPanel = frontPanel;
    worker.userData.leftCoverSleeve = leftSleeve;
    worker.userData.rightCoverSleeve = rightSleeve;
  }}
  // The base procedural worker already owns one sleeve/arm chain per side.
  // Do not add a second clothing sleeve layer: it reads as extra arms in motion.
  function emphasizeVisibleJoints(worker, role) {{
    ['leftElbow', 'rightElbow', 'leftWrist', 'rightWrist', 'leftHand', 'rightHand'].forEach((key) => {{
      if (worker.userData[key]) {{
        worker.userData[key].name += '-v19-visible-articulation-joint';
        // Keep hands and joints skin-toned and proportionate; gold dots look like
        // detached extra hands when the exhibition camera moves.
        worker.userData[key].material = mats.skin;
        worker.userData[key].scale.setScalar(1.0);
      }}
    }});
    worker.userData.head.name += '-v19-readable-head-joint';
    worker.userData.waist.name += '-v19-readable-waist-joint';
  }}
  emphasizeVisibleJoints(drawWorker, 'upper-pattern-operator');
  emphasizeVisibleJoints(weaver, 'lower-weaver');
  // A Dahualou loom is operated by two people. Extra background worker rigs
  // made the scene read as accidental duplicate bodies and limbs, so the
  // exhibition keeps only the upper draw worker and lower weaver.

  const licensedHumanRig = {{
    draw: null,
    weaver: null,
    loading: false,
    loaded: false,
    failed: false
  }};
  function decorateLicensedWorkerRig(group, role, coatMat) {{
    const robe = new THREE.Mesh(new THREE.CapsuleGeometry(.24, .72, 5, 10), coatMat);
    robe.name = role + '-v16-full-clothed-worker-robe-over-licensed-body';
    robe.position.set(0, .70, -.025);
    robe.scale.set(1.05, 1.06, .70);
    robe.castShadow = true;
    group.add(robe);
    const apron = new THREE.Mesh(new THREE.BoxGeometry(.46, .54, .030), coatMat);
    apron.name = role + '-v16-front-and-back-apron-cloth-over-licensed-human';
    apron.position.set(0, .66, -.23);
    apron.rotation.x = -.09;
    apron.castShadow = true;
    const backApron = apron.clone();
    backApron.name = role + '-v16-back-apron-cloth-no-nude-silhouette';
    backApron.position.z = .20;
    backApron.rotation.x = .09;
    group.add(apron, backApron);
    const headWrap = new THREE.Mesh(new THREE.SphereGeometry(.125, 14, 8, 0, Math.PI * 2, 0, Math.PI * .54), role === 'upper-draw-worker' ? mats.darkWood : mats.hair);
    headWrap.name = role + '-v16-worker-headwrap-on-licensed-human';
    headWrap.position.set(0, 1.32, -.012);
    headWrap.scale.set(1.10, .58, .94);
    headWrap.castShadow = true;
    const leftSleeve = new THREE.Mesh(new THREE.CapsuleGeometry(.055, .46, 5, 10), coatMat);
    leftSleeve.name = role + '-v16-clothed-left-sleeve';
    leftSleeve.position.set(-.34, .83, -.04);
    leftSleeve.rotation.z = -.36;
    const rightSleeve = leftSleeve.clone();
    rightSleeve.name = role + '-v16-clothed-right-sleeve';
    rightSleeve.position.x = .34;
    rightSleeve.rotation.z = .36;
    group.add(headWrap, leftSleeve, rightSleeve);
  }}
  function buildLicensedHumanWorker(gltf, role, coatMat, position, scale, seated) {{
    const group = new THREE.Group();
    group.name = role + '-v14-licensed-cc0-rigged-human-worker-gltf-skeleton';
    const body = gltf.scene;
    body.name = role + '-v14-human-base-rigged-cc0-body';
    body.traverse((obj) => {{
      obj.frustumCulled = false;
      if (obj.isMesh) {{
        obj.castShadow = true;
        obj.receiveShadow = true;
        obj.name = role + '-v14-skinned-human-body-mesh-cc0';
        obj.material = new THREE.MeshStandardMaterial({{color: role === 'upper-draw-worker' ? 0x7d263a : 0x1f5f66, roughness: .78, metalness: .02}});
      }}
    }});
    body.position.set(0, 0, 0);
    body.rotation.y = role === 'upper-draw-worker' ? -Math.PI / 2 : -Math.PI / 2;
    body.scale.set(scale, scale, scale);
    group.add(body);
    decorateLicensedWorkerRig(group, role, coatMat);
    const bones = {{}};
    body.traverse((obj) => {{
      if (obj.isBone) bones[obj.name] = obj;
    }});
    group.userData.bones = bones;
    group.userData.body = body;
    group.userData.seated = seated;
    group.position.copy(position);
    group.visible = false;
    loom.add(group);
    return group;
  }}
  function setProceduralWorkerVisibility(visible) {{
    drawWorker.visible = true;
    weaver.visible = true;
  }}
  function loadLicensedHumanWorkers() {{
    licensedHumanRig.failed = true;
    setProceduralWorkerVisibility(true);
    return;
    if (!state.licensedHumanGlbDataUri || licensedHumanRig.loading) return;
    licensedHumanRig.loading = true;
    import('{GLTF_LOADER_URL}').then((module) => {{
      const loader = new module.GLTFLoader();
      loader.load(state.licensedHumanGlbDataUri, (gltf) => {{
        licensedHumanRig.draw = buildLicensedHumanWorker(gltf, 'upper-draw-worker', mats.red, new THREE.Vector3(-2.74, 3.24, .72), .62, true);
        loader.load(state.licensedHumanGlbDataUri, (gltf2) => {{
          licensedHumanRig.weaver = buildLicensedHumanWorker(gltf2, 'lower-weaver', mats.teal, new THREE.Vector3(-2.86, .45, 2.05), .58, true);
          licensedHumanRig.loaded = true;
          licensedHumanRig.draw.visible = true;
          licensedHumanRig.weaver.visible = true;
          setProceduralWorkerVisibility(false);
        }}, undefined, () => {{
          licensedHumanRig.failed = true;
          setProceduralWorkerVisibility(true);
        }});
      }}, undefined, () => {{
        licensedHumanRig.failed = true;
        setProceduralWorkerVisibility(true);
      }});
    }}).catch(() => {{
      licensedHumanRig.failed = true;
      setProceduralWorkerVisibility(true);
    }});
  }}
  function poseLicensedHumanWorker(group, role, action, timeline, pull, weave, reach, treadlePress, t) {{
    if (!group || !group.userData || !group.userData.bones) return;
    const b = group.userData.bones;
    const side = Math.sin(timeline.phase * Math.PI * 8);
    // The upper body follows the same pull travel as the lever and heddles.
    // Previously it followed action.draw only and returned early while the
    // shed was still held open, making the worker look out of sync.
    const lean = role === 'upper' ? pull * .19 : action.weave * (.10 + reach * .11);
    group.rotation.x = -lean + Math.sin(t * 1.1) * .010;
    group.rotation.z = role === 'upper' ? side * pull * .025 : side * action.weave * .055;
    if (role === 'upper') {{
      group.position.z = .72 + pull * .10;
      group.position.y = 3.24;
      if (b.thigh_l) b.thigh_l.rotation.x = -1.12;
      if (b.calf_l) b.calf_l.rotation.x = .92;
      if (b.foot_l) b.foot_l.rotation.x = -.26;
      if (b.thigh_r) b.thigh_r.rotation.x = -1.06;
      if (b.calf_r) b.calf_r.rotation.x = .86;
      if (b.foot_r) b.foot_r.rotation.x = -.22;
      if (b.upperarm_l) b.upperarm_l.rotation.set(.28 + pull * .42, .18, -1.02 - pull * .48);
      if (b.lowerarm_l) b.lowerarm_l.rotation.set(.10 + pull * .34, .08, -.42 - pull * .36);
      if (b.hand_l) b.hand_l.rotation.set(.18 + pull * .24, .04, -.18);
      if (b.upperarm_r) b.upperarm_r.rotation.set(.28 + pull * .42, -.18, 1.02 + pull * .48);
      if (b.lowerarm_r) b.lowerarm_r.rotation.set(.10 + pull * .34, -.08, .42 + pull * .36);
      if (b.hand_r) b.hand_r.rotation.set(.18 + pull * .24, -.04, .18);
      if (b.spine_03) b.spine_03.rotation.x = .04 + pull * .10;
      if (b.head) b.head.rotation.x = .04 + pull * .08;
    }} else {{
      group.position.x = -2.86 + action.weave * side * .12;
      group.position.z = 2.03 - action.weave * reach * .17;
      if (b.upperarm_l) b.upperarm_l.rotation.set(-.78 - reach * .34, .12, .34 + weave * .62);
      if (b.lowerarm_l) b.lowerarm_l.rotation.set(-.42 - reach * .28, .04, .22 + weave * .52);
      if (b.hand_l) b.hand_l.rotation.set(.10, .05, weave * .18);
      if (b.upperarm_r) b.upperarm_r.rotation.set(-.78 - reach * .34, -.12, -.34 - weave * .62);
      if (b.lowerarm_r) b.lowerarm_r.rotation.set(-.42 - reach * .28, -.04, -.22 - weave * .52);
      if (b.hand_r) b.hand_r.rotation.set(.10, -.05, -weave * .18);
      if (b.thigh_l) b.thigh_l.rotation.x = -1.05 - treadlePress * .08;
      if (b.calf_l) b.calf_l.rotation.x = .70 + treadlePress * .16;
      if (b.foot_l) b.foot_l.rotation.x = -.20 - treadlePress * .20;
      if (b.thigh_r) b.thigh_r.rotation.x = -1.00;
      if (b.calf_r) b.calf_r.rotation.x = .64;
      if (b.spine_03) b.spine_03.rotation.x = .04 + reach * .13;
      if (b.head) b.head.rotation.x = -.04 + reach * .08;
    }}
  }}
  loadLicensedHumanWorkers();

  function makeLabel(text, x, y, z) {{
    const spriteCanvas = document.createElement('canvas');
    spriteCanvas.width = 512; spriteCanvas.height = 96;
    const sctx = spriteCanvas.getContext('2d');
    sctx.fillStyle = 'rgba(255,250,242,.92)';
    sctx.fillRect(0, 0, 512, 96);
    sctx.strokeStyle = '#dbc4a6'; sctx.strokeRect(0, 0, 512, 96);
    sctx.fillStyle = '#5a4633'; sctx.font = 'bold 30px Microsoft YaHei, Arial';
    sctx.fillText(text, 18, 60);
    const tex = new THREE.CanvasTexture(spriteCanvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({{map: tex, transparent: true}}));
    sprite.name = 'minimal-layer-label';
    sprite.position.set(x, y, z);
    sprite.scale.set(1.65, .31, 1);
    sprite.visible = !state.exhibitionMode;
    scene.add(sprite);
    return sprite;
  }}
  makeLabel('上层花楼 / upper draw area', -3.9, 4.75, -1.2);
  makeLabel('经线与开口 / warp shed', -3.9, 2.35, .35);
  makeLabel('连续织物 / continuous cloth', -3.9, 1.05, 2.3);
  function makeFellCallout() {{
    const calloutCanvas = document.createElement('canvas');
    calloutCanvas.width = 640;
    calloutCanvas.height = 112;
    const calloutCtx = calloutCanvas.getContext('2d');
    calloutCtx.fillStyle = 'rgba(47,20,18,.86)';
    calloutCtx.beginPath();
    calloutCtx.roundRect(4, 4, 632, 104, 28);
    calloutCtx.fill();
    calloutCtx.strokeStyle = 'rgba(239,204,118,.76)';
    calloutCtx.lineWidth = 3;
    calloutCtx.stroke();
    calloutCtx.fillStyle = '#f7dda0';
    calloutCtx.font = '700 30px Microsoft YaHei, Arial';
    calloutCtx.textAlign = 'center';
    calloutCtx.fillText('纬线在此并入布面', 320, 68);
    const calloutTexture = new THREE.CanvasTexture(calloutCanvas);
    calloutTexture.colorSpace = THREE.SRGBColorSpace;
    const calloutMaterial = new THREE.SpriteMaterial({{map: calloutTexture, transparent: true, depthTest: false, opacity: 0}});
    const callout = new THREE.Sprite(calloutMaterial);
    callout.name = 'temporary-fell-boundary-explanation-callout';
    callout.position.set(.95, 1.54, fellZ + .02);
    callout.scale.set(2.15, .38, 1);
    callout.renderOrder = 20;
    callout.visible = false;
    scene.add(callout);
    return callout;
  }}
  const fellCallout = makeFellCallout();
  let fellCalloutPasses = 0;
  let fellCalloutWasActive = false;

  function resize() {{
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(320, rect.width);
    const height = Math.max(360, rect.height);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }}
  window.addEventListener('resize', resize);
  resize();

  const baseLift = state.mapping.warp_lift_ratio;
  const clock = new THREE.Clock();
  let lastPaintedProgress = -1;
  const cinematicViews = {{
    pattern_design: {{theta: -0.62, phi: .92, radius: 9.7, target: new THREE.Vector3(.20, 2.48, .10)}},
    pattern_translation: {{theta: -0.54, phi: .88, radius: 9.2, target: new THREE.Vector3(.20, 2.72, -.80)}},
    weaving_preparation: {{theta: -0.78, phi: .97, radius: 8.7, target: new THREE.Vector3(-.55, 1.72, 1.10)}},
    warp_lifting: {{theta: -0.98, phi: .78, radius: 7.2, target: new THREE.Vector3(-1.55, 3.08, -.45)}},
    weft_weaving: {{theta: -0.86, phi: 1.08, radius: 6.8, target: new THREE.Vector3(-1.38, 1.22, 1.56)}},
    pattern_emergence: {{theta: -0.58, phi: 1.05, radius: 7.3, target: new THREE.Vector3(.10, 1.22, 2.00)}}
  }};
  function blendTimelineViews(a, b, amount) {{
    const u = smoothstep(amount);
    return {{
      theta: lerpValue(a.theta, b.theta, u),
      phi: lerpValue(a.phi, b.phi, u),
      radius: lerpValue(a.radius, b.radius, u),
      target: a.target.clone().lerp(b.target, u)
    }};
  }}
  function responsiveOverviewRadius() {{
    const rect = canvas.getBoundingClientRect();
    const aspect = rect.height > 0 ? rect.width / rect.height : 1.6;
    if (aspect < .78) return 16.8;
    if (aspect < 1.15) return 15.1;
    return 13.5;
  }}
  function documentaryViewFromTimeline(timeline, elapsed) {{
    const overview = {{theta: -0.60, phi: 1.03, radius: responsiveOverviewRadius(), target: new THREE.Vector3(-.34, 2.48, .62)}};
    if (state.exhibitionMode) {{
      if (introTourActive && elapsed < 8.2) {{
        const upper = {{theta:-.82,phi:.76,radius:9.4,target:new THREE.Vector3(-1.25,3.65,-.35)}};
        const shed = {{theta:-.74,phi:.94,radius:8.6,target:new THREE.Vector3(-.22,2.18,.52)}};
        const weaving = {{theta:-.72,phi:1.04,radius:8.0,target:new THREE.Vector3(-.55,1.30,1.50)}};
        if (elapsed < 2.0) return blendTimelineViews(overview, upper, elapsed / 2.0);
        if (elapsed < 4.0) return blendTimelineViews(upper, shed, (elapsed - 2.0) / 2.0);
        if (elapsed < 6.1) return blendTimelineViews(shed, weaving, (elapsed - 4.0) / 2.1);
        return blendTimelineViews(weaving, overview, (elapsed - 6.1) / 2.1);
      }}
      if (introTourActive) {{
        introTourActive = false;
        try {{ sessionStorage.setItem('yunjin-v31-intro-tour-seen', '1'); }} catch (error) {{}}
      }}
      // Keep the complete loom in frame. Exhibition movement is a gentle
      // documentary drift, not a sequence of crops that loses the mechanism.
      const drift = {{theta: -0.43 + Math.sin(timeline * Math.PI * 2) * .040, phi: 1.06, radius: responsiveOverviewRadius() - .6, target: new THREE.Vector3(-.42, 2.38, .78)}};
      return blendTimelineViews(overview, drift, .42);
    }}
    const drawClose = cinematicViews.warp_lifting;
    const weaveClose = cinematicViews.weft_weaving;
    const clothClose = cinematicViews.pattern_emergence;
    if (timeline < .18) return blendTimelineViews(overview, drawClose, timeline / .18);
    if (timeline < .38) return blendTimelineViews(drawClose, weaveClose, (timeline - .18) / .20);
    if (timeline < .68) return blendTimelineViews(weaveClose, clothClose, (timeline - .38) / .30);
    if (timeline < .86) return blendTimelineViews(clothClose, overview, (timeline - .68) / .18);
    return blendTimelineViews(overview, drawClose, (timeline - .86) / .14);
  }}
  function applyCinematicCamera(view) {{
    if (userCameraTouched) return;
    orbitTheta += (view.theta - orbitTheta) * .018;
    orbitPhi += (view.phi - orbitPhi) * .018;
    orbitRadius += (view.radius - orbitRadius) * .018;
    cameraTarget.lerp(view.target, .020);
    updateCamera();
  }}
  const storedMotion = readStoredMotion();
  const stageOrder = ['pattern_design', 'pattern_translation', 'weaving_preparation', 'warp_lifting', 'weft_weaving', 'pattern_emergence'];
  function clamp01(value) {{
    return Math.max(0, Math.min(1, value));
  }}
  function smoothstep(value) {{
    const x = clamp01(value);
    return x * x * (3 - 2 * x);
  }}
  function lerpValue(a, b, amount) {{
    return a + (b - a) * amount;
  }}
  function crossfadeWeight(center, width) {{
    return clamp01(1 - Math.abs(visual.stageBlend - center) / width);
  }}
  function setCueOpacity(mesh, opacity) {{
    if (state.exhibitionMode) {{
      mesh.visible = false;
      return;
    }}
    mesh.visible = opacity > .035;
    if (mesh.material && mesh.material.transparent) mesh.material.opacity = opacity;
  }}
  function recentStoredMotion() {{
    return storedMotion && Number.isFinite(storedMotion.savedAt) && (Date.now() - storedMotion.savedAt) < 12000;
  }}
  const hasRecentMotion = recentStoredMotion();
  const visual = {{
    stageBlend: hasRecentMotion && Number.isFinite(storedMotion.stageBlend) ? storedMotion.stageBlend : stageOrder.indexOf(state.stageId),
    progress: hasRecentMotion && Number.isFinite(storedMotion.progress) ? storedMotion.progress : state.stageProgress,
    liftRatio: hasRecentMotion && Number.isFinite(storedMotion.liftRatio) ? storedMotion.liftRatio : state.mapping.warp_lift_ratio,
    shedRatio: hasRecentMotion && Number.isFinite(storedMotion.shedRatio) ? storedMotion.shedRatio : state.mapping.shed_open_ratio,
    clothRatio: hasRecentMotion && Number.isFinite(storedMotion.clothRatio) ? storedMotion.clothRatio : state.mapping.woven_cloth_ratio,
    shuttleRatio: hasRecentMotion && Number.isFinite(storedMotion.shuttleRatio) ? storedMotion.shuttleRatio : state.mapping.shuttle_travel_ratio
  }};
  let lastMotionSave = 0;
  function videoInspiredMotionScheduler(t) {{
    const drawCycle = (Math.sin(t * 1.72 - .45) + 1) / 2;
    const drawPull = smoothstep(drawCycle);
    const weavingLoop = (t * .32) % 1;
    const shuttlePass = weavingLoop < .58 ? smoothstep(weavingLoop / .58) : 1;
    const beaterHit = weavingLoop > .58 && weavingLoop < .82 ? Math.sin(((weavingLoop - .58) / .24) * Math.PI) : 0;
    const treadlePress = weavingLoop < .48 ? Math.sin((weavingLoop / .48) * Math.PI) : 0;
    const settle = weavingLoop > .82 ? smoothstep((weavingLoop - .82) / .18) : 0;
    return {{
      drawPull,
      weavingLoop,
      shuttlePass,
      beaterHit,
      treadlePress,
      settle,
      takeupPulse: Math.max(beaterHit * .45, settle)
    }};
  }}
  function smallContinuousHandWork(t, motion) {{
    return {{
      drawFinger: Math.sin(t * 6.8) * .042 + Math.sin(t * 4.1) * .024,
      weaverFinger: Math.sin(t * 7.4 + motion.weavingLoop * 3.0) * .048,
      clothTouch: Math.sin(t * 5.2 + .8) * .026,
      shoulderBreath: Math.sin(t * 1.1) * .026
    }};
  }}
  function timelinePulse(phase, start, end) {{
    if (phase < start || phase > end) return 0;
    const local = (phase - start) / (end - start);
    return Math.sin(local * Math.PI);
  }}
  function heldActionWindow(phase, start, riseEnd, holdEnd, end) {{
    if (phase < start || phase > end) return 0;
    if (phase < riseEnd) return smoothstep((phase - start) / Math.max(.0001, riseEnd - start));
    if (phase <= holdEnd) return 1;
    return 1 - smoothstep((phase - holdEnd) / Math.max(.0001, end - holdEnd));
  }}
  function documentaryWeavingTimeline(t) {{
    const cycleSeconds = 16.0;
    const cycleIndex = Math.floor(t / cycleSeconds);
    const phase = (t / cycleSeconds) % 1;
    // The labels and all mechanisms share these exact boundaries. Some
    // mechanical states deliberately remain held after their initiating step:
    // the pedal remains down and the shed remains open while the shuttle runs.
    const boundaries = [0, .14, .38, .62, .79, .91, 1.0];
    let stepIndex = 0;
    for (let i = 1; i < boundaries.length - 1; i++) if (phase >= boundaries[i]) stepIndex = i;
    const stepStart = boundaries[stepIndex];
    const stepEnd = boundaries[stepIndex + 1];
    const stepProgress = clamp01((phase - stepStart) / Math.max(.001, stepEnd - stepStart));
    const prepare = heldActionWindow(phase, .00, .025, .09, .14);
    const pedalPress = heldActionWindow(phase, .015, .055, .14, .18);
    const draw = heldActionWindow(phase, .055, .13, .33, .41);
    const shed = heldActionWindow(phase, .14, .22, .62, .70);
    const shuttle = heldActionWindow(phase, .38, .46, .58, .64);
    const beater = heldActionWindow(phase, .62, .69, .76, .81);
    const clothAdvance = heldActionWindow(phase, .79, .835, .89, .925);
    const takeup = heldActionWindow(phase, .91, .945, .985, 1.00);
    const reset = Math.max(heldActionWindow(phase, .965, .985, 1.00, 1.00), phase < .02 ? 1 - smoothstep(phase / .02) : 0);
    return {{
      phase,
      cycleIndex,
      stepIndex,
      stepProgress,
      prepare,
      pedalPress,
      draw,
      shed,
      shuttle: clamp01(shuttle),
      beater,
      clothAdvance,
      takeup,
      reset,
      weave: clamp01(shuttle * .82 + beater * .50),
      drawPull: clamp01(draw * (.72 + .28 * Math.sin(phase * Math.PI * 4))),
      treadlePress: clamp01(Math.max(pedalPress, shed * .78, shuttle * .78)),
      takeupPulse: clamp01(takeup),
      beaterHit: clamp01(beater)
    }};
  }}
  function continuousAnimationSeconds() {{
    try {{
      const store = window.parent && window.parent.localStorage ? window.parent.localStorage : window.localStorage;
      let epoch = Number(store.getItem(persistentTimelineKey));
      if (!epoch || Number.isNaN(epoch)) {{
        epoch = Date.now();
        store.setItem(persistentTimelineKey, String(epoch));
      }}
      return (Date.now() - epoch) / 1000;
    }} catch (error) {{
      return Date.now() / 1000;
    }}
  }}
  // Capture the shared documentary cycle at mount time. Introductory cloth
  // growth is counted in completed picks, never in unrelated wall-clock
  // seconds, so the worker, shuttle, reed, cloth and roller cannot drift.
  const exhibitionStartCycleIndex = Math.floor(continuousAnimationSeconds() / 16.0);
  function animate() {{
    const t = continuousAnimationSeconds();
    const elapsed = clock.getElapsedTime();
    const motion = videoInspiredMotionScheduler(t);
    const timeline = documentaryWeavingTimeline(t);
    const micro = smallContinuousHandWork(t, motion);
    const processSteps = document.querySelectorAll('.process-step');
    const processCaption = document.getElementById('process-caption');
    const processIndex = timeline.stepIndex;
    const processCaptions = [
      '踏板正在下压；脚踏动作与踏板高亮同步',
      '踏板保持下压，经线正在分层并打开梭口',
      '梭口保持打开，梭子正携带纬线横向穿过',
      '梭子到达另一侧，筘框随即前摆压紧纬线',
      '新纬线并入织口，形成的新布向卷布轴移动',
      '卷布轴正在转动收布，随后机构复位进入下一梭'
    ];
    processSteps.forEach((step, index) => {{
      step.classList.toggle('active', index === processIndex);
      step.classList.toggle('done', index < processIndex);
      step.classList.toggle('holding', (index === 0 && (processIndex === 1 || processIndex === 2)) || (index === 1 && processIndex === 2));
      if (index === processIndex) step.style.setProperty('--step-progress', timeline.stepProgress.toFixed(3));
    }});
    if (processCaption) processCaption.textContent = processCaptions[processIndex];
    triggerLoomAudio(timeline);
    const targetStageBlend = stageOrder.indexOf(state.stageId);
    visual.stageBlend = lerpValue(visual.stageBlend, targetStageBlend, .018);
    visual.progress = lerpValue(visual.progress, state.stageProgress, .045);
    visual.liftRatio = lerpValue(visual.liftRatio, state.mapping.warp_lift_ratio, .060);
    visual.shedRatio = lerpValue(visual.shedRatio, state.mapping.shed_open_ratio, .065);
    visual.clothRatio = lerpValue(visual.clothRatio, state.mapping.woven_cloth_ratio, .038);
    visual.shuttleRatio = lerpValue(visual.shuttleRatio, state.mapping.shuttle_travel_ratio, .055);
    const pulse = (Math.sin(t * 2.4) + 1) / 2;
    const stageFade = {{
      pattern_design: crossfadeWeight(0, 1.35),
      pattern_translation: crossfadeWeight(1, 1.35),
      weaving_preparation: crossfadeWeight(2, 1.35),
      warp_lifting: crossfadeWeight(3, 1.35),
      weft_weaving: crossfadeWeight(4, 1.35),
      pattern_emergence: crossfadeWeight(5, 1.35)
    }};
    const exhibitionMotionScale = state.exhibitionMode ? 2.05 : 1.0;
    const action = {{
      setup: clamp01(timeline.prepare + .18),
      draw: clamp01(timeline.draw * exhibitionMotionScale),
      hold: clamp01(timeline.shed * (state.exhibitionMode ? .78 : .65)),
      weave: clamp01(timeline.weave * exhibitionMotionScale),
      finish: clamp01((timeline.takeup + timeline.reset * .45) * exhibitionMotionScale),
      shed: clamp01(timeline.shed * exhibitionMotionScale),
      shuttle: timeline.shuttle,
      beater: clamp01(timeline.beater * exhibitionMotionScale),
      takeup: clamp01(timeline.takeup * exhibitionMotionScale),
      clothAdvance: clamp01(timeline.clothAdvance * exhibitionMotionScale)
    }};
    const lift = (visual.liftRatio * (.82 + timeline.drawPull * .34)) * Math.max(.20, action.shed);
    const setupFocus = state.mapping.setup_focus;
    const clothMotion =
      visual.clothRatio + action.beater * timeline.beaterHit * .055 + action.clothAdvance * .070 + action.takeup * timeline.takeupPulse * .110;
    // Start every exhibition session with an explicit cloth-forming reveal.
    // This makes the fabric visibly grow from the fell before continuous
    // take-up begins, instead of presenting a completed cloth at frame one.
    const wovenPicks = (timeline.cycleIndex % 24) + timeline.takeup * .92;
    const exhibitionClothProgress = .10 + (wovenPicks / 24) * .82;
    const clothProgress = state.exhibitionMode ? exhibitionClothProgress : Math.min(0.98, clothMotion);
    // Build the cloth only after a pick has been inserted and beaten. Two
    // synchronized picks introduce the flat run, wrap and wound layer. During
    // pedal, shed, shuttle and reed phases the cloth length is held still.
    const completedSessionPicks = Math.max(0, timeline.cycleIndex - exhibitionStartCycleIndex);
    const currentPickFormation = timeline.phase < .79
      ? 0
      : timeline.phase < .91
        ? .65 * smoothstep(clamp01((timeline.phase - .79) / .12))
        : .65 + .35 * smoothstep(clamp01((timeline.phase - .91) / .09));
    const clothFormation = state.exhibitionMode
      ? clamp01((completedSessionPicks + currentPickFormation) / 2.0)
      : 1;
    // Build the cloth in three overlapping, physically connected stages. The
    // flat run approaches the roller first, the free edge then curls around
    // its surface, and only after contact does the wound layer become visible.
    // Overlap avoids the old one-frame jump from a flat strip to a full roll.
    const clothReveal = state.exhibitionMode ? smoothstep(clamp01(clothFormation / .80)) : 1;
    const clothWrapReveal = state.exhibitionMode ? smoothstep(clamp01((clothFormation - .68) / .22)) : 1;
    const clothRollReveal = state.exhibitionMode ? smoothstep(clamp01((clothFormation - .80) / .20)) : 1;
    const wovenEdgeZ = state.exhibitionMode ? fellZ : 2.17 - clothProgress * 1.86;
    const cycleStep = state.mapping.loom_cycle_step;
    const shedOpen = visual.shedRatio * (.82 + timeline.drawPull * .36) * Math.max(.14, action.shed);
    // Legacy test marker: beaterForward = action.beater * timeline.beaterHit * 1.08
    // One normalized strike drives the reed, the worker's hands and the loose
    // pick together.  The reed stops at the fixed fell instead of passing
    // through the cloth, so its purpose is readable as packing the weft.
    const beaterStrike = clamp01(action.beater * timeline.beaterHit);
    const beaterForward = beaterStrike + action.finish * .08 * (1 - timeline.reset);
    const treadlePress = state.exhibitionMode
      ? clamp01(timeline.treadlePress * 1.35)
      : action.weave * timeline.treadlePress;
    const takeupTurn = action.takeup * (timeline.phase + timeline.takeupPulse * .12);

    patternDraftBoard.visible = !state.exhibitionMode && stageFade.pattern_design > .04;
    tiePatternSymbols.visible = !state.exhibitionMode && stageFade.pattern_translation > .04;
    warpPreparationComb.visible = !state.exhibitionMode && stageFade.weaving_preparation > .04;
    patternDraftBoard.rotation.z = Math.sin(t * 1.1) * .035;
    tiePatternSymbols.rotation.y = Math.sin(t * 1.4) * .10;
    warpPreparationComb.position.y = 1.40 + stageFade.weaving_preparation * pulse * .08;

    wovenEdge.position.set(0, 1.16 + pulse * .008, wovenEdgeZ);
    wovenEdge.visible = state.exhibitionMode || clothProgress > .10;
    if (state.exhibitionMode) {{
      // During the introductory reveal, anchor one edge at the fell and move
      // only the far edge toward the roller. Once connected, the physical
      // distance stays fixed and later picks are accumulated by take-up.
      const revealedRun = exhibitionClothRun * Math.max(.002, clothReveal);
      clothPlane.visible = clothReveal > .003;
      clothPlane.scale.set(1, Math.max(.002, clothReveal), 1);
      clothPlane.position.set(
        0,
        1.16 - (revealedRun * .5) * Math.cos(clothAngle),
        fellZ - (revealedRun * .5) * Math.sin(clothAngle)
      );
      const rollBuild = ((timeline.cycleIndex % 48) + timeline.takeup) / 48;
      const rollRadiusScale = 1 + rollBuild * .10;
      const emergingRollScale = .94 + clothRollReveal * (rollRadiusScale - .94);
      clothRollSpin.scale.set(emergingRollScale, 1, emergingRollScale);
      clothRollSpin.rotation.y = -takeupTurn * Math.PI * 2.0 * clothRollReveal;
      const clothFeedOffset = -((timeline.cycleIndex + timeline.clothAdvance * .32 + timeline.takeup) * .085) % 1;
      clothTexture.repeat.y = Math.max(.002, clothReveal);
      clothTexture.offset.y = (1 - clothReveal) + clothFeedOffset;
      outputClothTexture.offset.y = clothFeedOffset;
      rollClothTexture.offset.y = clothFeedOffset;
      // Uncurl the cloth edge progressively over the quarter-turn around the
      // take-up roller. Vertices farther around the roller join slightly later.
      for (let wi = 0; wi < rollerWrapPositions.count; wi++) {{
        const arcRatio = rollerWrapArcRatios[wi];
        const vertexReveal = smoothstep(clamp01((clothWrapReveal - arcRatio * .55) / .45));
        const theta = arcRatio * Math.PI * .5 * vertexReveal;
        rollerWrapPositions.setY(wi, .74 + .292 * Math.cos(theta));
        rollerWrapPositions.setZ(wi, 2.45 + .292 * Math.sin(theta));
      }}
      rollerWrapPositions.needsUpdate = true;
      rollerWrapGeometry.computeVertexNormals();
      outputClothMat.opacity = clamp01(clothWrapReveal * 1.65);
      clothRollMaterial.opacity = clothRollReveal;
      rollerClothWrap.visible = clothWrapReveal > .004;
      clothRollMount.visible = clothRollReveal > .004;
    }} else {{
      const clothLengthScale = .34 + clothProgress * 1.08;
      clothPlane.scale.set(1.0, clothLengthScale, 1.0);
      clothPlane.position.set(0, .92, 1.34 - (clothLengthScale - .58) * .30);
    }}
    const newPickTravel = clamp01((timeline.phase - .79) / .135);
    clothGrowthMarker.position.set(0, 1.19 + pulse * .006, wovenEdgeZ + .018 + newPickTravel * .94 * clothReveal);
    clothGrowthMarker.scale.x = .96 + action.takeup * .04;
    clothGrowthMarker.material.opacity = .94 - newPickTravel * .48;
    clothGrowthMarker.visible = state.exhibitionMode && timeline.phase >= .62 && timeline.phase < .93;
    shedOpening.visible = action.shed > .05;
    upperShedPlane.position.y = 1.50 + shedOpen * .40;
    lowerShedPlane.position.y = 1.38 - shedOpen * .18;
    upperShedPlane.material.opacity = .12 + shedOpen * .22;
    lowerShedPlane.material.opacity = .08 + shedOpen * .14;
    takeupRoller.rotation.x = takeupTurn * Math.PI * 2.0;
    takeupBand.rotation.x = takeupTurn * Math.PI * 2.0;
    warpRoller.rotation.x = -takeupTurn * Math.PI * .34;
    cords.forEach((item) => {{
      item.mesh.position.y = 3.50 - (item.active ? lift * .58 : lift * .06);
      item.mesh.rotation.z = Math.sin(t * 1.9 + item.mesh.position.x * 2.2) * .014;
      item.mesh.material = item.active && lift > .1 ? mats.activeCord : mats.cord;
    }});
    warpThreads.forEach((item, i) => {{
      const split = item.selected ? shedOpen * .66 : -shedOpen * .23;
      item.mesh.position.y = 1.90 + split;
      item.mesh.rotation.z = Math.sin(t * 1.5 + i * .22) * .010 + (item.selected ? shedOpen * .025 : -shedOpen * .016);
    }});
    // One master travel value drives the selected pattern-cord bank, the
    // upper worker and its corresponding raised warp group.
    const mechanicalLift = state.exhibitionMode
      ? clamp01(Math.max(timeline.drawPull, timeline.shed * .92))
      : shedOpen;
    const activeControlBank = timeline.cycleIndex % drawControlHandles.length;
    frontHeddleFrame.position.y = 1.82 + mechanicalLift * .24;
    rearHeddleFrame.position.y = 1.82 - mechanicalLift * .13;
    frontHeddleFrame.rotation.z = Math.sin(t * 1.6) * .006 * mechanicalLift;
    rearHeddleFrame.rotation.z = -Math.sin(t * 1.6) * .004 * mechanicalLift;
    repositionBeamBetween(
      treadleLinkCords[0],
      new THREE.Vector3(-2.78, .27 - treadlePress * .20, 1.18),
      new THREE.Vector3(-1.45, frontHeddleFrame.position.y - .36, .30)
    );
    repositionBeamBetween(
      treadleLinkCords[1],
      new THREE.Vector3(-2.32, .27, 1.18),
      new THREE.Vector3(-1.12, rearHeddleFrame.position.y - .36, .02)
    );
    functionalWarpLines.forEach((item, i) => {{
      const positions = item.line.geometry.attributes.position;
      const values = positions.array;
      const bankSelected = item.bank === activeControlBank;
      // The lowered yellow group must stay above the cloth support. A deeper
      // drop intersected the fabric plane and made segments disappear.
      const split = bankSelected ? mechanicalLift * 1.28 : -mechanicalLift * .28;
      item.junctionY = 1.92 + split * .74;
      values[4] = item.junctionY;
      values[7] = Math.max(1.24, 1.52 + split);
      // All warp groups converge at one fixed fell instead of dipping through
      // the newly woven cloth as the shed closes.
      values[10] = 1.205;
      values[11] = fellZ;
      positions.needsUpdate = true;
      item.line.material.color.setHex(bankSelected && mechanicalLift > .10 ? 0xff365b : (bankSelected ? 0xb52d48 : 0xf2d69b));
      item.line.material.opacity = 1;
    }});
    functionalDrawCords.forEach((item, i) => {{
      const positions = item.line.geometry.attributes.position;
      const values = positions.array;
      const connectedWarp = functionalWarpLines[item.warpIndex];
      const bankSelected = item.bank === activeControlBank;
      values[4] = 3.62 - (bankSelected ? mechanicalLift * 1.02 : mechanicalLift * .05);
      values[7] = connectedWarp && Number.isFinite(connectedWarp.junctionY) ? connectedWarp.junctionY : 1.92;
      positions.needsUpdate = true;
      item.line.material.color.setHex(bankSelected && mechanicalLift > .10 ? 0xff365b : (bankSelected ? 0xc62e4d : 0xd9b866));
      item.line.material.opacity = 1;
    }});
    functionalHeddleEyes.forEach((item) => {{
      const connectedWarp = functionalWarpLines[item.warpIndex];
      item.mesh.position.y = connectedWarp && Number.isFinite(connectedWarp.junctionY) ? connectedWarp.junctionY : 1.92;
      item.mesh.scale.setScalar(item.bank === activeControlBank ? 1 + mechanicalLift * .55 : 1);
    }});
    drawControlHandles.forEach((item) => {{
      const selectedHandle = item.bank === activeControlBank;
      const handlePull = selectedHandle ? mechanicalLift : 0;
      const handleY = controlHandleRestY - handlePull * .48;
      const positions = item.cord.geometry.attributes.position;
      const values = positions.array;
      values[4] = 4.76 - handlePull * .16;
      values[7] = handleY;
      positions.needsUpdate = true;
      item.grip.position.y = handleY;
      item.knot.position.y = handleY + .06;
      item.cord.material.color.setHex(selectedHandle ? 0xff365b : 0xd9b866);
      item.knot.material = selectedHandle ? mats.activeCord : mats.gold;
      item.grip.scale.setScalar(selectedHandle ? 1.12 : 1);
    }});
    denseVideoCordLines.forEach((line, i) => {{
      const activeLine = i % 7 === 0 || i % 13 === 4;
      line.position.y = 2.05 + (activeLine ? lift * .20 : Math.sin(t * 1.2 + i) * .008);
      line.rotation.z = Math.sin(t * 1.1 + i * .17) * .012;
      line.scale.y = 1 + (activeLine ? timeline.drawPull * .12 : 0);
    }});
    jacquardPegRows.forEach((peg, i) => {{
      const activePeg = i % 9 === 0 || i % 17 === 3;
      peg.scale.setScalar(activePeg ? 1 + timeline.drawPull * .28 : 1);
      peg.position.z = -.245 + (activePeg ? timeline.drawPull * .028 : 0);
    }});

    const pullCycle = mechanicalLift * 2 - 1;
    const setupPull = stageFade.pattern_translation * (.12 + pulse * .10);
    const pull = state.exhibitionMode
      ? mechanicalLift
      : clamp01(setupPull + action.draw * (.34 + timeline.drawPull * .96) + action.hold * .28 + action.finish * .22 * (1 - timeline.reset));
    loom.updateMatrixWorld(true);
    drawWorker.userData.leftArm.rotation.z = -1.18 - pull * .98;
    drawWorker.userData.leftArm.rotation.x = .72 + pull * .12;
    drawWorker.userData.rightArm.rotation.z = 1.18 + pull * .98;
    drawWorker.userData.rightArm.rotation.x = .72 + pull * .12;
    drawWorker.userData.leftForearm.rotation.set(.62 + pull * .32, 0, -.46 - pull * .58);
    drawWorker.userData.rightForearm.rotation.set(.62 + pull * .32, 0, .46 + pull * .58);
    drawWorker.userData.leftSleeve.rotation.copy(drawWorker.userData.leftArm.rotation);
    drawWorker.userData.rightSleeve.rotation.copy(drawWorker.userData.rightArm.rotation);
    drawWorker.userData.leftHand.position.set(-.24 + micro.drawFinger, .82 - pull * .12, -.74);
    drawWorker.userData.rightHand.position.set(.24 - micro.drawFinger, .82 - pull * .12, -.74);
    drawWorker.userData.leftElbow.position.set(-.34, .88 - pull * .14, -.49);
    drawWorker.userData.rightElbow.position.set(.34, .88 - pull * .14, -.49);
    drawWorker.userData.leftWrist.position.copy(drawWorker.userData.leftHand.position).add(new THREE.Vector3(.04, .04, .04));
    drawWorker.userData.rightWrist.position.copy(drawWorker.userData.rightHand.position).add(new THREE.Vector3(-.04, .04, .04));
    updateConnectedArmRig(drawWorker);
    drawWorker.userData.waist.position.z = .02 + pull * .075;
    drawWorker.userData.neck.position.z = -.02 + pull * .055;
    drawWorker.userData.head.rotation.x = pull * .14;
    drawWorker.userData.head.rotation.z = pullCycle * pull * .045;
    drawWorker.userData.hairCap.rotation.copy(drawWorker.userData.head.rotation);
    drawWorker.userData.nose.rotation.z = drawWorker.userData.head.rotation.z;
    drawWorker.userData.robeFront.rotation.x = -.08 - pull * .055;
    drawWorker.position.y = 3.22;
    drawWorker.position.x = -2.74;
    drawWorker.position.z = -.50 + pull * .18;
    drawWorker.rotation.x = -0.06 - pull * .25 + micro.shoulderBreath;
    drawWorker.rotation.y = -Math.PI / 2 + pull * .045;
    drawWorker.rotation.z = pull * pullCycle * .045;
    // Lock both hands to the currently selected short wooden cord grip.
    const activePatternHandle = drawControlHandles[activeControlBank];
    activePatternHandle.grip.updateMatrixWorld(true);
    const drawLeftGrip = activePatternHandle.grip.localToWorld(new THREE.Vector3(0, -.09, 0));
    const drawRightGrip = activePatternHandle.grip.localToWorld(new THREE.Vector3(0, .09, 0));
    placeHandAtWorld(drawWorker, drawWorker.userData.leftHand, drawLeftGrip, .90, -1);
    placeHandAtWorld(drawWorker, drawWorker.userData.rightHand, drawRightGrip, .90, 1);
    poseReachElbow(drawWorker, drawWorker.userData.leftHand, drawWorker.userData.leftElbow, -1);
    poseReachElbow(drawWorker, drawWorker.userData.rightHand, drawWorker.userData.rightElbow, 1);
    drawWorker.userData.leftWrist.position.copy(drawWorker.userData.leftHand.position).add(new THREE.Vector3(.04, .04, .04));
    drawWorker.userData.rightWrist.position.copy(drawWorker.userData.rightHand.position).add(new THREE.Vector3(-.04, .04, .04));
    updateConnectedArmRig(drawWorker);
    drawWorker.userData.leftFoot.position.y = .07;
    drawWorker.userData.rightFoot.position.y = .07;
    poseLicensedHumanWorker(licensedHumanRig.draw, 'upper', action, timeline, pull, 0, 0, treadlePress, t);

    const weaveCycle = Math.sin(t * 2.15);
    const handThrow = timeline.shuttle * (timeline.phase < .57 ? -1 : 1) * .72;
    const weave = timeline.shuttle * handThrow + timeline.beaterHit * .20 + action.finish * .12;
    const reach = timeline.shuttle * (.70 + timeline.shuttle * .46) + timeline.beaterHit * .38 + action.finish * (.28 + pulse * .08) + stageFade.weaving_preparation * (.14 + pulse * .05);
    weaver.userData.leftArm.rotation.z = .30 + weave * .64;
    weaver.userData.leftArm.rotation.x = -.80 - reach * .38;
    weaver.userData.rightArm.rotation.z = -.30 - weave * .64;
    weaver.userData.rightArm.rotation.x = -.80 - reach * .38;
    weaver.userData.leftForearm.rotation.set(-.50 - reach * .30, 0, .22 + weave * .58);
    weaver.userData.rightForearm.rotation.set(-.50 - reach * .30, 0, -.22 - weave * .58);
    weaver.userData.leftSleeve.rotation.copy(weaver.userData.leftArm.rotation);
    weaver.userData.rightSleeve.rotation.copy(weaver.userData.rightArm.rotation);
    weaver.userData.leftHand.position.set(-.42 + micro.weaverFinger + weave * .08, .56 + micro.clothTouch, -.58 - reach * .28);
    weaver.userData.rightHand.position.set(.42 - micro.weaverFinger + weave * .08, .56 - micro.clothTouch, -.58 - reach * .28);
    weaver.userData.leftElbow.position.set(-.35, .78 - reach * .035, -.32 - reach * .13);
    weaver.userData.rightElbow.position.set(.35, .78 - reach * .035, -.32 - reach * .13);
    weaver.userData.leftWrist.position.copy(weaver.userData.leftHand.position).add(new THREE.Vector3(.05, .025, .035));
    weaver.userData.rightWrist.position.copy(weaver.userData.rightHand.position).add(new THREE.Vector3(-.05, .025, .035));
    updateConnectedArmRig(weaver);
    weaver.userData.waist.position.z = .03 - action.weave * .075;
    weaver.userData.neck.position.z = -.02 - action.weave * .060;
    weaver.userData.head.rotation.x = -.05 - action.weave * .20;
    weaver.userData.head.rotation.z = handThrow * action.weave * .055;
    weaver.userData.hairCap.rotation.copy(weaver.userData.head.rotation);
    weaver.userData.nose.rotation.z = weaver.userData.head.rotation.z;
    weaver.userData.robeFront.rotation.x = -.08 - action.weave * .08;
    weaver.position.x = -2.55 + action.weave * handThrow * .10;
    weaver.position.y = .58 - treadlePress * .075;
    weaver.position.z = 2.35 - action.weave * reach * .08 - stageFade.weaving_preparation * .02;
    weaver.rotation.x = -.04 - timeline.shuttle * (.14 + reach * .10) - timeline.beaterHit * .12 - stageFade.weaving_preparation * .035 + micro.shoulderBreath;
    weaver.userData.leftFoot.position.y = -.34 - treadlePress * .27;
    weaver.userData.rightFoot.position.y = -.34;
    weaver.userData.leftFoot.rotation.x = -treadlePress * .30;
    weaver.userData.rightFoot.rotation.x = treadlePress * .070;
    updateConnectedSeatedLegRig(weaver, treadlePress);
    poseLicensedHumanWorker(licensedHumanRig.weaver, 'weaver', action, timeline, pull, weave, reach, treadlePress, t);

    // A single pick now follows one unambiguous route: the shuttle crosses
    // once, the full loose weft is beaten to the fixed fell, then it merges.
    // Hold the shuttle in the weaver's hand before launch. Only after this
    // readable hand-off does it cross the open shed.
    const pickPass = clamp01((timeline.phase - .38) / .24);
    const pickBeat = clamp01((timeline.phase - .62) / .17);
    const pickMerge = clamp01((timeline.phase - .79) / .12);
    const passLeftToRight = timeline.cycleIndex % 2 === 0;
    const exhibitionShuttleRatio = passLeftToRight ? pickPass : 1 - pickPass;
    const shuttleRatio = state.exhibitionMode
      ? exhibitionShuttleRatio
      : (action.shuttle > .18 ? lerpValue(visual.shuttleRatio, timeline.shuttle, action.shuttle) : visual.shuttleRatio);
    const visibleShuttleRatio = state.exhibitionMode ? shuttleRatio : (action.shuttle > .05 ? shuttleRatio : .06);
    shuttle.position.set(-2.25 + visibleShuttleRatio * 4.5, 1.42, 1.47);
    // Keep the physical shuttle parked inside the loom between passes. Only
    // its travel changes; it no longer pops in and out like a debug marker.
    shuttle.visible = state.exhibitionMode || action.shuttle > .05;
    // The lower weaver operates both tools in sequence: one hand briefly
    // launches or receives the shuttle at the reachable left shuttle box,
    // then returns to the reed grip before the beat. The hand never follows
    // the shuttle across the full width, so the arm stays anatomically short.
    // Rest behind the loose pick, then travel exactly to the fell at z=1.18.
    // A small tilt makes the hinged beat visible without letting the frame
    // cross through the finished cloth.
    beater.position.set(-.12 + action.weave * weaveCycle * .08, 1.22, 1.69 - beaterStrike * .46);
    beater.rotation.x = -.08 + beaterStrike * .14;
    const leftBeaterGrip = beater.localToWorld(new THREE.Vector3(-2.34, .20, .22));
    const rightBeaterGrip = beater.localToWorld(new THREE.Vector3(-2.02, .20, .22));
    const launchContact = heldActionWindow(timeline.phase, .35, .38, .43, .47);
    const receiveContact = heldActionWindow(timeline.phase, .55, .58, .62, .66);
    const shuttleHandContact = passLeftToRight ? launchContact : receiveContact;
    const shuttleTouchPoint = shuttle.localToWorld(new THREE.Vector3(-.16, .09, .03));
    const rightHandTarget = rightBeaterGrip.clone().lerp(shuttleTouchPoint, shuttleHandContact);
    placeHandAtWorld(weaver, weaver.userData.leftHand, leftBeaterGrip);
    placeHandAtWorld(weaver, weaver.userData.rightHand, rightHandTarget);
    shuttleControlHalo.visible = shuttleHandContact > .03;
    shuttleControlHalo.material.opacity = shuttleHandContact * (.62 + pulse * .22);
    shuttleControlHalo.scale.setScalar(1 + shuttleHandContact * .22);
    poseReachElbow(weaver, weaver.userData.leftHand, weaver.userData.leftElbow, -1);
    poseReachElbow(weaver, weaver.userData.rightHand, weaver.userData.rightElbow, 1);
    weaver.userData.leftWrist.position.copy(weaver.userData.leftHand.position).add(new THREE.Vector3(.05, .025, .035));
    weaver.userData.rightWrist.position.copy(weaver.userData.rightHand.position).add(new THREE.Vector3(-.05, .025, .035));
    updateConnectedArmRig(weaver);
    weft.visible = !state.exhibitionMode;
    weft.scale.y = .25 + action.shuttle * (.55 + shuttleRatio * 3.5) + action.finish * 2.1;
    if (state.exhibitionMode) {{
      const passActive = timeline.phase >= .38 && timeline.phase < .62;
      const beatActive = timeline.phase >= .62 && timeline.phase < .79;
      const mergeActive = timeline.phase >= .79 && timeline.phase < .91;
      insertedPick.visible = passActive || beatActive || mergeActive;
      if (passActive) {{
        const startX = passLeftToRight ? -2.325 : 2.325;
        const shuttleX = -2.25 + shuttleRatio * 4.5;
        const span = Math.max(.05, Math.abs(shuttleX - startX));
        insertedPick.position.set((startX + shuttleX) * .5, 1.42, 1.47);
        insertedPick.scale.set(span / 4.65, 1, 1);
      }} else {{
        insertedPick.position.set(0, 1.215, 1.47 + (fellZ + .025 - 1.47) * pickBeat);
        insertedPick.scale.set(1, 1, mergeActive ? Math.max(.12, 1 - pickMerge * .88) : 1);
      }}
      insertedPick.material = mats.activeCord;
      recentWovenRows.visible = true;
      recentWovenRows.position.z = action.clothAdvance * pickMerge * .070;
    }} else {{
      insertedPick.visible = action.shuttle > .05 || action.finish > .05;
      insertedPick.position.set(0, 1.205 + pulse * .012, wovenEdgeZ + .035);
      insertedPick.scale.x = action.shuttle > action.finish ? Math.max(.06, shuttleRatio) : 1;
      insertedPick.material = action.shuttle > action.finish ? mats.gold : mats.activeCord;
      recentWovenRows.visible = false;
    }}
    treadleGroup.children.forEach((pedal, i) => {{
      pedal.rotation.x = (i === 0 ? -treadlePress : treadlePress * .42) * .72;
      pedal.position.y = .285 - (i === 0 ? treadlePress * .20 : 0);
    }});
    setCueOpacity(drawPullCue, action.draw * (.24 + pulse * .30));
    drawPullCue.position.set(-2.72, 4.30 - pulse * .22, -.74);
    drawPullCue.scale.set(1.25, 1.25 + pulse * .35, 1.25);
    setCueOpacity(shuttleCue, action.shuttle * (.22 + pulse * .30));
    shuttleCue.position.set(-2.25 + shuttleRatio * 4.5, 1.72, 1.38);
    shuttleCue.scale.set(1.15 + pulse * .30, 1.15 + pulse * .30, 1.15 + pulse * .30);
    setCueOpacity(clothAdvanceCue, action.takeup * (.20 + pulse * .28));
    clothAdvanceCue.position.set(1.72, 1.34, 1.78 + timeline.takeup * .22);
    clothAdvanceCue.scale.set(1.2 + pulse * .24, 1.2 + pulse * .24, 1.2 + pulse * .24);
    setCueOpacity(beaterCue, action.beater * (.20 + beaterForward * .38));
    beaterCue.position.set(.95, 1.55, 1.62 - beaterForward * .28);
    beaterCue.scale.set(1.0 + beaterForward * .30, 1.0 + beaterForward * .30, 1.0 + beaterForward * .30);
    setCueOpacity(treadleCue, action.weave * (.14 + treadlePress * .30));
    treadleCue.position.set(-2.78, .60 - treadlePress * .16, 2.42);
    treadleCue.scale.set(.9 + treadlePress * .22, .9 + treadlePress * .22, .9 + treadlePress * .22);
    drawMotionTrail.visible = !state.exhibitionMode && action.draw > .05;
    drawMotionTrail.position.x = -2.48;
    drawMotionTrail.position.z = -.60;
    drawMotionTrail.position.y = 3.86 - pull * .32;
    drawMotionTrail.scale.y = .90 + Math.abs(pullCycle) * .82;
    drawMotionTrail.material.opacity = action.draw * (.16 + pulse * .28);
    shuttleMotionTrail.visible = !state.exhibitionMode && action.shuttle > .05;
    shuttleMotionTrail.scale.x = Math.max(.10, shuttleRatio);
    shuttleMotionTrail.position.x = -2.25 + shuttleRatio * 2.25;
    shuttleMotionTrail.material.opacity = action.shuttle * (.14 + pulse * .25);
    beaterMotionSweep.visible = action.beater > .05;
    beaterMotionSweep.position.z = 1.74 - beaterForward * .44;
    beaterMotionSweep.material.opacity = action.beater * (state.exhibitionMode ? (.045 + beaterForward * .13) : (.12 + beaterForward * .34));
    clothGrowthPulse.visible = (action.clothAdvance > .05 || action.shuttle > .05);
    clothGrowthPulse.position.z = wovenEdgeZ + .045;
    clothGrowthPulse.scale.y = 1 + pulse * .45;
    clothGrowthPulse.material.opacity = state.exhibitionMode ? action.clothAdvance * (.34 + pulse * .34) : action.clothAdvance * (.22 + pulse * .30) + action.shuttle * (.06 + pulse * .10);
    const fellExplainWindow = state.exhibitionMode && timeline.phase >= .72 && timeline.phase < .93 && clothReveal > .05;
    if (fellExplainWindow && !fellCalloutWasActive) fellCalloutPasses += 1;
    fellCalloutWasActive = fellExplainWindow;
    const fellExplainActive = fellExplainWindow && fellCalloutPasses <= 2;
    const fellFadeIn = smoothstep(clamp01((timeline.phase - .72) / .025));
    const fellFadeOut = 1 - smoothstep(clamp01((timeline.phase - .89) / .04));
    const fellExplainStrength = fellExplainActive ? fellFadeIn * fellFadeOut : 0;
    fellCallout.visible = fellExplainActive;
    fellCallout.material.opacity = .46 + fellExplainStrength * .52;
    fellCallout.position.y = 1.54 + Math.sin(t * 3.2) * .018;
    fellCallout.scale.set(2.15 + fellExplainStrength * .10, .38 + fellExplainStrength * .018, 1);
    collaborationLoopRibbon.visible = !state.exhibitionMode;
    collaborationLoopRibbon.children[0].material.opacity = .18 + action.draw * .34;
    collaborationLoopRibbon.children[0].scale.y = .82 + action.draw * .42;
    collaborationLoopRibbon.children[1].material.opacity = .16 + action.shuttle * .42;
    collaborationLoopRibbon.children[1].scale.x = .78 + action.shuttle * .34;
    collaborationLoopRibbon.children[2].material.opacity = .14 + Math.max(action.beater, action.takeup) * .44;
    collaborationLoopRibbon.children[2].scale.x = .76 + Math.max(action.beater, action.takeup) * .38;
    drawFlowBeads.forEach((bead, i) => {{
      const beadPhase = (timeline.phase * 4.8 + i * .18) % 1;
      bead.visible = action.draw > .10;
      bead.position.y = 4.24 - action.draw * (.22 + beadPhase * .62);
      bead.position.z = -.86 + Math.sin(t * 2.8 + i) * .025;
      bead.scale.setScalar(.75 + action.draw * (.85 + pulse * .35));
      bead.material.opacity = action.draw * (state.exhibitionMode ? (.12 + beadPhase * .22) : (.25 + beadPhase * .45));
    }});
    shedFocusBand.visible = action.shed > .12;
    shedFocusBand.position.y = 1.50 + shedOpen * .18;
    shedFocusBand.scale.z = .75 + action.shed * .72;
    shedFocusBand.material.opacity = action.shed * (state.exhibitionMode ? (.055 + pulse * .08) : (.14 + pulse * .20));
    shuttlePathBand.visible = action.shuttle > .06;
    shuttlePathBand.scale.x = Math.max(.16, shuttleRatio);
    shuttlePathBand.position.x = -2.25 + shuttleRatio * 2.25;
    shuttlePathBand.material.opacity = action.shuttle * (state.exhibitionMode ? (.10 + pulse * .12) : (.16 + pulse * .22));
    beaterImpactEdge.visible = action.beater > .04;
    beaterImpactEdge.position.z = wovenEdgeZ + .02;
    beaterImpactEdge.scale.y = 1 + beaterForward * 1.25;
    beaterImpactEdge.material.opacity = action.beater * (.18 + beaterStrike * (state.exhibitionMode ? .62 : .44));
    takeupPulseRing.visible = action.takeup > .04;
    takeupPulseRing.rotation.x = takeupTurn * Math.PI * 2.0;
    takeupPulseRing.scale.setScalar(1 + action.takeup * (.12 + pulse * .18));
    takeupPulseRing.material.opacity = action.takeup * (state.exhibitionMode ? (.18 + pulse * .20) : (.22 + pulse * .30));
    redWarpSurface.position.y = 1.010 + action.weave * micro.clothTouch;
    redWarpSurface.material.opacity = .22 + action.weave * .18 + action.takeup * .10;
    redClothBed.position.z = 1.48 - action.takeup * timeline.takeupPulse * .08 + action.beater * timeline.beaterHit * .035;

    // Deform the subdivided textile along its normal so it catches light like
    // flexible silk instead of behaving like a rigid sheet.
    const clothPositions = clothPlane.geometry.attributes.position;
    const clothHalfRun = state.exhibitionMode ? exhibitionClothRun * .5 : 2.30;
    for (let vi = 0; vi < clothPositions.count; vi++) {{
      const vx = clothPositions.getX(vi);
      const vy = clothPositions.getY(vi);
      const edgeRatio = clamp01((vy + clothHalfRun) / (clothHalfRun * 2));
      const pinnedEdgeFade = Math.pow(Math.sin(edgeRatio * Math.PI), 2);
      const wave = Math.sin(t * 2.25 + vx * 2.8 + vy * 1.7) * .026 * (state.exhibitionMode ? 1.45 : .65);
      const fold = Math.sin(t * 1.05 + vy * 3.4) * .014;
      // Both seam rows stay fixed; only the middle of the fabric ripples.
      clothPositions.setZ(vi, (wave + fold) * pinnedEdgeFade);
    }}
    clothPositions.needsUpdate = true;
    clothPlane.geometry.computeVertexNormals();

    if (Math.abs(clothProgress - lastPaintedProgress) > .006) {{
      paintTeachingCloth(clothProgress);
      clothTexture.needsUpdate = true;
      lastPaintedProgress = clothProgress;
    }}
    if (elapsed - lastMotionSave > .25) {{
      saveStoredMotion({{
        savedAt: Date.now(),
        stageBlend: visual.stageBlend,
        progress: visual.progress,
        liftRatio: visual.liftRatio,
        shedRatio: visual.shedRatio,
        clothRatio: visual.clothRatio,
        shuttleRatio: shuttleRatio
      }});
      lastMotionSave = elapsed;
    }}
    applyCinematicCamera(documentaryViewFromTimeline(timeline.phase, elapsed));
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }}
  animate();
  }} catch (error) {{
    console.error('Yunjin WebGL scene failed:', error);
    root.classList.add('webgl-error');
  }}
}})();
</script>
</body>
</html>"""
    return html
