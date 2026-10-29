#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_plan.py — SCENE-PLAN 硬闸校验器 v1.0
把 layer-templates.md 的设计纪律编译成机器检查：违规规划根本不进渲染。
用法：python validate_plan.py <plan.json> [--registry <blocks/registry.json>]
输出：JSON 报告（ok/errors/warnings/stats）；有 error 时 exit 1。
"""
import argparse
import json
import sys
import colorsys
from pathlib import Path

SEGMENTS = ["hook", "anchor", "reason", "turn", "land"]
SFX_NAMES = {"impact-low", "impact-mid", "tick", "riser", "sub-drop", "whoosh"}
CX_ALLOWED = [(0.40, 0.46), (0.54, 0.60)]
BEAT_TOL_FRAMES = 0.5

errors = []
warnings = []


def err(msg, where="plan"):
    errors.append(f"[{where}] {msg}")


def warn(msg, where="plan"):
    warnings.append(f"[{where}] {msg}")


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) != 6:
        return None
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def check_color(pal):
    bg_out = hex_rgb(pal.get("bg_out", "#000000"))
    if bg_out is None:
        err("palette.bg_out 不是合法 hex")
    elif max(bg_out) < 10:
        err("palette.bg_out 近纯黑——L0 禁纯黑底（模板规则）")
    accent = hex_rgb(pal.get("accent", ""))
    if accent is None:
        err("palette.accent 不是合法 hex")
    else:
        h, s, v = colorsys.rgb_to_hsv(*[c / 255 for c in accent])
        if s < 0.25 or v < 0.35:
            err(f"palette.accent 饱和度/明度不足 (s={s:.2f}, v={v:.2f})——QA 强调焦点会挂")
        for other in ("ink", "gray"):
            oc = hex_rgb(pal.get(other, ""))
            if oc and oc == accent:
                err(f"palette.accent 与 {other} 相同——强调色必须唯一")


def on_beat(v, beat, fps):
    if v < -1e-9:
        return False
    n = round(v / beat)
    return abs(v - n * beat) <= BEAT_TOL_FRAMES / fps


def in_ranges(v, ranges):
    return any(lo - 1e-9 <= v <= hi + 1e-9 for lo, hi in ranges)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--registry", default=None)
    args = ap.parse_args()

    plan_path = Path(args.plan)
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "errors": [f"无法读取/解析 plan: {e}"], "warnings": []},
                         ensure_ascii=False, indent=2))
        return 1

    registry_path = Path(args.registry) if args.registry else \
        Path(__file__).resolve().parents[1] / "blocks" / "registry.json"
    registry = {}
    if registry_path.exists():
        try:
            reg_doc = json.loads(registry_path.read_text(encoding="utf-8"))
            reg_doc = reg_doc.get("blocks", reg_doc)
            registry = {b["name"]: b for b in reg_doc} if isinstance(reg_doc, list) else reg_doc
        except Exception as e:
            warn(f"registry.json 读取失败（跳过积木检查）: {e}", "registry")
    else:
        warn(f"找不到 {registry_path}（跳过积木检查）", "registry")

    meta = plan.get("meta", {})
    for k in ("topic", "duration", "fps", "bpm", "palette"):
        if k not in meta:
            err(f"meta.{k} 缺失")
    if errors:
        report(meta, plan)
        return 1

    dur, fps, bpm = meta["duration"], meta["fps"], meta["bpm"]
    if fps not in (24, 30, 60):
        err(f"meta.fps={fps} 不在 {{24,30,60}}")
    if bpm <= 0 or dur <= 0:
        err("meta.bpm / meta.duration 必须为正")
        report(meta, plan)
        return 1
    beat = 60.0 / bpm
    if not on_beat(dur, beat, fps):
        err(f"duration={dur} 不在拍点网格（beat={beat:.6f}s）")

    check_color(meta["palette"])

    # ---- scenes ----
    scenes = plan.get("scenes", [])
    if not scenes:
        err("scenes 为空")
    seg_idx = -1
    total_est = 0.0
    for i, sc in enumerate(scenes):
        w = sc.get("id", f"scenes[{i}]")
        t_in, t_out = sc.get("t_in"), sc.get("t_out")
        if not isinstance(t_in, (int, float)) or not isinstance(t_out, (int, float)):
            err(f"{w} t_in/t_out 缺失或非数字")
            continue
        if t_out - t_in < 0.95:
            warn(f"{w} 时长 {t_out - t_in:.2f}s 过短（<0.95s 闪切）")
        for key, v in (("t_in", t_in), ("t_out", t_out)):
            if not on_beat(v, beat, fps):
                err(f"{w}.{key}={v} 不在拍点网格", w)
        seg = sc.get("segment")
        if seg not in SEGMENTS:
            err(f"{w}.segment='{seg}' 不在五段枚举", w)
        else:
            idx = SEGMENTS.index(seg)
            if idx < seg_idx:
                err(f"{w}.segment='{seg}' 叙事倒序（五段必须非降序）", w)
            seg_idx = max(seg_idx, idx)
        # 时间轴连续性
        if i == 0 and abs(t_in) > 1e-6:
            err(f"首场景 t_in={t_in} ≠ 0", w)
        if i > 0:
            prev = scenes[i - 1]
            if isinstance(prev.get("t_out"), (int, float)) and abs(prev["t_out"] - t_in) > 1e-6:
                err(f"{w}.t_in={t_in} 与上一场景 t_out={prev.get('t_out')} 存在空洞/重叠", w)
        # L2
        l2 = sc.get("l2") or {}
        blk = l2.get("block")
        if not blk:
            err(f"{w} 缺 l2.block", w)
        elif registry and blk not in registry:
            err(f"{w} l2.block='{blk}' 未在 blocks/registry.json 注册", w)
        params = l2.get("params", {})
        area = params.get("area_pct")
        if area is None:
            err(f"{w} l2.params.area_pct 缺失（密度预算依据）", w)
        else:
            if area < 0.12:
                err(f"{w} area_pct={area} < 0.12 爆款线——QA「画面充实」必挂", w)
            total_est += area
        cx = params.get("cx")
        if cx is not None and not in_ranges(cx, CX_ALLOWED):
            err(f"{w} l2.cx={cx} 居中或越界——必须在 {CX_ALLOWED}（F1 硬规则）", w)
        cy = params.get("cy")
        if cy is not None and not (0.22 <= cy <= 0.72):
            warn(f"{w} l2.cy={cy} 超出主体区建议范围 [0.22,0.72]", w)
        gw = l2.get("glow_window")
        if gw and len(gw) == 2 and (gw[0] < t_in - 1e-6 or gw[1] > t_out + 1e-6):
            warn(f"{w} glow_window 超出场景范围", w)
        # L1
        l1 = sc.get("l1")
        if l1:
            if l1.get("stroke", 2) < 2:
                err(f"{w} l1.stroke={l1.get('stroke')} <2——1px 细线 QA 纹理能量测不出", w)
            g = l1.get("grow")
            if g and (g[0] < t_in - 1e-6 or g[1] > t_out + 1e-6):
                err(f"{w} l1.grow 窗口 {g} 超出场景 [{t_in},{t_out}]", w)
            total_est += 0.05
        # L3
        l3 = sc.get("l3", [])
        if t_out - t_in >= 2.5 and len(l3) < 2:
            err(f"{w} 时长≥2.5s 但 l3 标注只有 {len(l3)} 条（需 ≥2）", w)
        if len(l3) > 4:
            warn(f"{w} l3 有 {len(l3)} 条（>4 会乱）")
        for j, note in enumerate(l3):
            fpx = note.get("font", 21)
            if not (20 <= fpx <= 26):
                warn(f"{w}.l3[{j}] font={fpx} 超出 20-26", w)
            if not (0.03 <= note.get("x", 0.5) <= 0.97 and 0.03 <= note.get("y", 0.5) <= 0.97):
                err(f"{w}.l3[{j}] 坐标越界", w)
        total_est += 0.012 * len(l3)
        # beats / sfx
        for bt in sc.get("beats", []):
            if not on_beat(bt, beat, fps):
                err(f"{w}.beats 里的 {bt} 不在拍点网格", w)
        for cue in sc.get("sfx", []):
            if cue.get("name") not in SFX_NAMES:
                warn(f"{w}.sfx name='{cue.get('name')}' 不在白名单", w)
            if not on_beat(cue.get("t", -1), beat, fps):
                err(f"{w}.sfx t={cue.get('t')} 不在拍点网格", w)
        total_est += 0.02  # L0 纹理基线

    if scenes:
        last = scenes[-1].get("t_out")
        if isinstance(last, (int, float)) and abs(last - dur) > 1e-3:
            err(f"末场景 t_out={last} ≠ duration={dur}")
    if scenes and dur >= 12:
        distinct = {sc.get("segment") for sc in scenes}
        if len(distinct) < 3:
            err(f"duration≥12s 但只有 {len(distinct)} 个叙事段位（需 ≥3）")
    if scenes and dur >= 20:
        distinct = {sc.get("segment") for sc in scenes}
        if len(distinct) < 4:
            err(f"duration≥20s 但只有 {len(distinct)} 个叙事段位（需 ≥4）")

    if total_est < 0.12:
        err(f"全片密度预算 est={total_est:.2f} < 0.12——画面会空（PPT 味）")
    elif total_est >= 0.18:
        warn(f"密度预算 est={total_est:.2f} 达满分线 ≥0.18")

    # ---- subtitles ----
    subs = plan.get("subtitles", [])
    spans = []
    for i, sb in enumerate(subs):
        w = f"subtitles[{i}]"
        zh = (sb.get("zh") or "").strip()
        if not zh:
            err(f"{w} zh 为空", w)
        else:
            # 全角按 1、半角按 0.55 折算（46px 字幕带宽度启发式）
            width = sum(0.55 if ord(c) < 0x2E80 else 1.0 for c in zh)
            if width > 18:
                warn(f"{w} 中文等效宽度 {width:.1f} >18（46px 字幕带可能偏挤）", w)
        t_in, t_out = sb.get("t_in"), sb.get("t_out")
        if not isinstance(t_in, (int, float)) or not isinstance(t_out, (int, float)) or t_out <= t_in:
            err(f"{w} t_in/t_out 非法", w)
            continue
        if t_in < 0 or t_out > dur + 1e-6:
            err(f"{w} 超出 [0,{duration_str(dur)}]", w)
        for j in range(i):
            p = subs[j]
            if all(isinstance(p.get(k), (int, float)) for k in ("t_in", "t_out")):
                if t_in < p["t_out"] - 1e-6 and p["t_in"] < t_out - 1e-6:
                    err(f"{w} 与 subtitles[{j}] 时间重叠", w)
        host = [sc for sc in scenes
                if isinstance(sc.get("t_in"), (int, float))
                and sc["t_in"] - 0.15 <= t_in and t_out <= sc["t_out"] + 0.15]
        if not host:
            err(f"{w} 跨场景（字幕必须完整落在单一场景内 ±0.15s）", w)
        spans.append((t_in, t_out))
    if spans and dur > 0:
        cov = sum(b - a for a, b in spans) / dur
        if cov < 0.40:
            warn(f"字幕覆盖率 {cov:.0%} < 40%——大片静默段，钩子片观感会垮")

    ok = not errors
    report(meta, plan, extra={"density_est": round(total_est, 3),
                              "beat_grid_s": round(beat, 6),
                              "subtitle_coverage": (round(sum(b - a for a, b in spans) / dur, 2) if spans and dur else 0)})
    return 0 if ok else 1


def duration_str(d):
    return f"{d:g}"


def report(meta, plan, extra=None):
    stats = {"topic": meta.get("topic"), "duration": meta.get("duration"),
             "scenes": len(plan.get("scenes", [])),
             "subtitles": len(plan.get("subtitles", []))}
    if extra:
        stats.update(extra)
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings,
                      "stats": stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
