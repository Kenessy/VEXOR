import re, pathlib
p = pathlib.Path('tournament_phase6.py')
t = p.read_text()
new_fn = '''def apply_update_agc(model, grad_norm, raw_delta=None, step: int | None = None):\n    \"\"\"\n    Surgical reset: single-floor AGC. No hidden clamps, no speed governor.\n    Rules:\n      * start from AGC_SCALE_MIN\n      * adjust up/down by grad_norm\n      * clamp to [AGC_SCALE_MIN, agc_scale_max/agc_scale_cap]\n    \"\"\"\n    base_cap = float(getattr(model, \"agc_scale_max\", AGC_SCALE_MAX))\n    cap = float(getattr(model, \"agc_scale_cap\", base_cap))\n    if not math.isfinite(cap) or cap <= 0:\n        cap = base_cap\n    cap = max(AGC_SCALE_MIN, min(base_cap, cap))\n\n    scale = float(getattr(model, \"update_scale\", AGC_SCALE_MIN))\n    if not math.isfinite(scale) or scale <= 0:\n        scale = AGC_SCALE_MIN\n    if step is not None and step == 0:\n        scale = AGC_SCALE_MIN\n\n    if AGC_ENABLED and grad_norm is not None and math.isfinite(grad_norm):\n        if grad_norm < AGC_GRAD_LOW:\n            scale *= AGC_SCALE_UP\n        elif grad_norm > AGC_GRAD_HIGH:\n            scale *= AGC_SCALE_DOWN\n\n    scale = max(AGC_SCALE_MIN, min(cap, scale))\n    model.agc_scale_cap = cap\n    model.update_scale = scale\n    model.debug_scale_out = scale\n    if step is not None and step == 0:\n        dbg = {\n            \"scale_in\": scale,\n            \"scale_out\": scale,\n            \"agc_scale_min\": AGC_SCALE_MIN,\n            \"cap\": cap,\n            \"base_cap\": base_cap,\n        }\n        log(f\"[debug_scale_step0] {dbg}\")\n    return scale\n\n\n'''
pattern = r'def apply_update_agc\(.*?\nclass AbsoluteHallway'
new_text, n = re.subn(pattern, new_fn + 'class AbsoluteHallway', t, flags=re.S)
if n != 1:
    raise SystemExit(f'pattern replace count {n}')
p.write_text(new_text)
print('rewrite ok')
