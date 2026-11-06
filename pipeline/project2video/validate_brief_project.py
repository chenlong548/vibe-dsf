#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_brief_project.py — PROJECT-BRIEF 轻校验闸（项目介绍线）
项目片怕的不是讲错理论，是吹牛。此闸拦三种"直接导致烂介绍片"的结构性缺失：
特性没证据、钩子没有反差素材、没有项目边界。
用法：python validate_brief_project.py <PROJECT-BRIEF.json>   （违规 exit 1）
"""
import argparse
import json
import sys
from pathlib import Path

errors = []


def err(msg):
    errors.append(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brief")
    a = ap.parse_args()

    try:
        b = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "errors": [f"无法解析 brief: {e}"]}, ensure_ascii=False))
        return 1

    meta = b.get("meta", {})
    for k in ("repo", "title", "one_liner", "audience", "language", "duration_target", "bpm"):
        v = meta.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            err(f"meta.{k} 缺失或为空")
    if not isinstance(meta.get("duration_target"), (int, float)) or meta.get("duration_target", 0) <= 0:
        err("meta.duration_target 必须为正秒数")
    ol = str(meta.get("one_liner", ""))
    if len(ol) > 34:
        err(f"meta.one_liner {len(ol)} 字（≤32 字：一句话定位说不长 = 没想清楚）")

    pain = b.get("pain", {})
    for k in ("who", "problem", "old_way_cost"):
        if not str(pain.get(k, "") or "").strip():
            err(f"pain.{k} 缺失——hook 对撞的素材来源")

    hooks = b.get("hook_candidates", [])
    if len(hooks) < 2:
        err(f"hook_candidates 只有 {len(hooks)} 条（需 ≥2，钩子要挑过才有得选）")
    for i, h in enumerate(hooks):
        if not (h.get("claim") or "").strip() or not (h.get("why_it_works") or "").strip():
            err(f"hook_candidates[{i}] 缺 claim 或 why_it_works")

    feats = b.get("features", [])
    if not (3 <= len(feats) <= 6):
        err(f"features {len(feats)} 条（要求 3-6：少了撑不起介绍，多了记不住）")
    for i, f in enumerate(feats):
        missing = [k for k in ("name", "what", "proof")
                   if not str(f.get(k, "") or "").strip()]
        if missing:
            err(f"features[{i}] 缺 {','.join(missing)}——proof 是防吹牛闸，空话特性不许上片")

    qs = b.get("quickstart", {})
    cmds = qs.get("install", [])
    if not (1 <= len(cmds) <= 3) or any(not str(c).strip() for c in cmds):
        err("quickstart.install 需 1-3 条非空命令（终端窗素材，按 README 原文）")
    if not str(qs.get("first_output", "") or "").strip():
        err("quickstart.first_output 缺失——终端窗要真实输出，不许编")
    if not str(qs.get("time_to_demo", "") or "").strip():
        err("quickstart.time_to_demo 缺失")

    metrics = b.get("metrics", [])
    if len(metrics) < 1:
        err("metrics 空——至少一条立得住的数字（规模/性能/质量）")
    for i, n in enumerate(metrics):
        missing = [k for k in ("value", "unit", "claim", "comparison", "source")
                   if not str(n.get(k, "") or "").strip()]
        if missing:
            err(f"metrics[{i}] 缺 {','.join(missing)}——无来源的数字不许上片")

    limits = [x for x in b.get("limits", []) if str(x or "").strip()]
    if len(limits) < 1:
        err("limits 空——敢说做不到什么，介绍片才可信（防吹牛闸）")

    cta = b.get("cta", {})
    url = str(cta.get("repo_url", "") or "")
    if not url.startswith("http"):
        err("cta.repo_url 必须是完整 URL")
    if not str(cta.get("install_short", "") or "").strip():
        err("cta.install_short 缺失——land 要给一行可行动命令")

    ok = not errors
    print(json.dumps({"ok": ok,
                      "errors": errors,
                      "stats": {"repo": meta.get("repo"), "one_liner": meta.get("one_liner"),
                                "hooks": len(hooks), "features": len(feats),
                                "metrics": len(metrics), "limits": len(limits)}},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
