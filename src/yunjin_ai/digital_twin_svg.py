"""Self-drawn SVG views of runtime teaching values; no images or device data."""
from __future__ import annotations

from html import escape

from .digital_twin import STAGE_IDS, TITLES, TwinState, validate_runtime


def render_twin_svg(state: TwinState, *, reduced_motion: bool = False) -> str:
    validate_runtime(state)
    t = state.teaching
    title = TITLES[STAGE_IDS.index(state.current_stage)]
    revision = state.revision
    animate = state.last_action == "execute" and not reduced_motion
    gold, red, muted = "#A97732", "#832D42", "#D1C5B5"
    teal = "#346C6B"
    pulse = f"twinPulse{revision}"
    motion_css = f".twin-scene .event {{animation:{pulse} .55s ease-out}}" if animate else ""
    parts = [f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"/><style>
html, body {{margin:0;padding:0;background:transparent;overflow:hidden}}
.twin-scene {{box-sizing:border-box;width:100%;background:#FAF7F0;border:1px solid #E5DACE;border-radius:20px;overflow:hidden}}
.twin-scene svg {{display:block;width:100%;height:auto}}
.twin-scene text {{font-family:'Microsoft YaHei','Noto Sans CJK SC',sans-serif;fill:#40352A}}
@keyframes {pulse} {{from {{opacity:.3}} to {{opacity:1}}}}
{motion_css}
@media (prefers-reduced-motion: reduce) {{.twin-scene .event {{animation:none}}}}
</style></head><body><div class="twin-scene"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 620"
role="img" aria-labelledby="twin-title twin-desc" data-stage="{escape(state.current_stage)}"
data-revision="{revision}" data-replays="{state.replay_count}">
<title id="twin-title">{escape(title)} · 教学状态示意</title>
<desc id="twin-desc">原创几何符号与织造概念示意；画面由用户交互后的 Twin State 渲染，非机械结构复原。</desc>
<rect x="0" y="0" width="900" height="91" fill="#F0E7D9"/>
<text x="30" y="39" font-size="23" font-weight="700">从图案到织物</text>
<text x="30" y="70" font-size="17">当前观察：{escape(title)} · 用户交互驱动</text>
<rect x="686" y="23" width="180" height="40" rx="20" fill="#FFFCF7"/>
<text x="710" y="49" font-size="16">教学交互 · 六个环节</text>
<path d="M270 120V510" stroke="#DED0BE" stroke-dasharray="5 7"/>
<text x="30" y="115" font-size="18">图案 → 信息载体</text>
<text x="310" y="115" font-size="18">经纬交织 · 协作概念区</text>
''']
    # The same stage can render multiple values: selecting a stage never
    # fabricates a completed visual. All fill/visibility comes from TeachingState.
    parts.append(f'''<g id="draft" data-visible="{str(t.sketch_visible).lower()}">
<rect x="30" y="137" width="210" height="150" rx="12" fill="#FFFDF8" stroke="{red if state.current_stage == 'pattern_design' else muted}" stroke-width="{3 if state.current_stage == 'pattern_design' else 1}"/>
<text x="46" y="166" font-size="17">① 图案设计</text>''')
    if t.sketch_visible:
        parts.append(f'''<g class="event" stroke="{red}" stroke-width="2" fill="none">
<path d="M135 187L175 220L135 259L95 220Z M95 220H175 M135 187V259"/>
<circle cx="135" cy="220" r="15"/></g>''')
    else:
        parts.append('<text x="67" y="230" font-size="17" fill="#897B68">草图尚未显示</text>')
    parts.append('</g>')
    parts.append(f'''<g id="carrier" data-visible="{str(t.carrier_visible).lower()}">
<rect x="30" y="315" width="210" height="164" rx="12" fill="#FFFDF8" stroke="{red if state.current_stage == 'pattern_translation' else muted}" stroke-width="{3 if state.current_stage == 'pattern_translation' else 1}"/>
<text x="46" y="345" font-size="17">② 挑花结本</text>''')
    if t.carrier_visible:
        parts.append(f'<g class="event" stroke="{gold}" stroke-width="3" fill="#FFFDF8">')
        for row in range(3):
            y = 372 + row * 26
            parts.append(f'<path d="M60 {y}H210"/>')
            for x in (83 + row * 13, 152 - row * 9):
                parts.append(f'<circle cx="{x}" cy="{y}" r="6"/>')
        parts.append('</g>')
    else:
        parts.append('<text x="60" y="402" font-size="17">符号尚未显示</text>')
    parts.append('<text x="49" y="460" font-size="14">教学符号 · 非花本编码</text></g>')
    parts.append(f'''<g id="preparation" data-ready="{str(t.preparation_ready).lower()}">
<rect x="306" y="137" width="554" height="364" rx="16" fill="#FFFDF8" stroke="{gold if t.preparation_ready else muted}" stroke-width="{3 if t.preparation_ready else 1}"/>
<text x="324" y="166" font-size="17">③ 准备标记：{'已点亮' if t.preparation_ready else '未点亮'}</text>
<circle class="event" cx="823" cy="160" r="7" fill="{gold if t.preparation_ready else muted}"/>
</g>
<rect x="373" y="192" width="324" height="188" rx="14" fill="#F3EEE6" stroke="{red if state.current_stage == 'warp_lifting' else teal if state.current_stage == 'weft_weaving' else muted}" stroke-width="{3 if state.current_stage in ('warp_lifting', 'weft_weaving') else 1}"/>
<text x="326" y="220" font-size="15">经向</text>
<path d="M346 232V275 M341 267L346 275L351 267" fill="none" stroke="{red}" stroke-width="2"/>
<text x="326" y="323" font-size="15">纬向</text>
<g id="warp" data-emphasis="{t.warp_emphasis}" class="event">''')
    for i in range(12):
        x = 395 + i * 24
        selected = t.warp_emphasis != "rest" and i % 2 == (0 if t.warp_emphasis == "a" else 1)
        # Normalized diagram coordinates are graphic design choices only.
        d = f"M{x} 211Q{x - 10} 270 {x} 356" if selected else f"M{x} 211V356"
        parts.append(f'<path d="{d}" fill="none" stroke="{red if selected else muted}" stroke-width="{3 if selected else 1.5}"/>')
    parts.append('</g>')
    upper = red
    lower = teal
    parts.append(f'''<rect x="714" y="191" width="132" height="105" rx="12" fill="#F7ECEF" stroke="{red if state.current_stage == 'warp_lifting' else '#EDDCE0'}" stroke-width="2"/>
<circle cx="775" cy="220" r="16" fill="{upper}" opacity=".85"/>
<path d="M750 259Q775 223 800 259" stroke="{upper}" fill="none" stroke-width="6"/>
<text x="728" y="283" font-size="16">④ 拽花工</text>
<rect x="714" y="302" width="132" height="99" rx="12" fill="#EAF1EF" stroke="{teal if state.current_stage == 'weft_weaving' else '#D7E4E1'}" stroke-width="2"/>
<circle cx="775" cy="324" r="16" fill="{lower}" opacity=".85"/>
<path d="M750 363Q775 327 800 363" stroke="{lower}" fill="none" stroke-width="6"/>
<text x="736" y="389" font-size="16">⑤ 织手</text>
<g id="weft" data-direction="{t.weft_direction}" class="event">''')
    if t.weft_direction != "rest":
        head, tail, base = (663, 397, 647) if t.weft_direction == "right" else (397, 663, 413)
        parts.append(f'<path d="M{tail} 305H{head} M{base} 295L{head} 305L{base} 315" fill="none" stroke="{teal}" stroke-width="5"/>')
    parts.append('</g>')
    parts.append(f'''<text x="324" y="414" font-size="16">⑥ 织造成纹 · 显示 {t.pattern_bands}/3 段</text>
<g id="pattern" data-bands="{t.pattern_bands}">
<rect x="325" y="432" width="370" height="48" rx="6" fill="#EEE5D8" stroke="{red if state.current_stage == 'pattern_emergence' else muted}" stroke-width="{2 if state.current_stage == 'pattern_emergence' else 1}"/>
''')
    for band in range(t.pattern_bands):
        x = 330 + band * 120
        parts.append(f'<g class="event"><rect x="{x}" y="437" width="114" height="38" fill="{red}" rx="3"/>')
        for offset in (18, 57, 96):
            cx = x + offset
            parts.append(f'<path d="M{cx} 443L{cx+12} 456L{cx} 469L{cx-12} 456Z" fill="none" stroke="#EACB86" stroke-width="2"/>')
        parts.append('</g>')
    parts.append('</g>')
    for index, lesson_title in enumerate(TITLES):
        x = 30 + index * 143
        active = STAGE_IDS[index] == state.current_stage
        parts.append(f'<rect x="{x}" y="521" width="130" height="40" rx="10" fill="{red if active else "#EEE7DC"}"/>')
        parts.append(f'<text x="{x + 9}" y="547" font-size="14" style="fill:{"#FFFFFF" if active else "#40352A"}">{index + 1} {lesson_title}</text>')
    parts.append('''<text x="30" y="590" font-size="15">原创几何教学符号 · 非传统纹样复原 · 不代表真实尺寸、经线位置或机械结构</text>
</svg></div></body></html>''')
    return "".join(parts)
