#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_brief.py — PAPER-BRIEF 轻校验闸
论文拆解是 LLM 中间产物（人审选题），此闸只拦"结构性缺失"：
钩子不够、数字没来源、没有防误读边界——这三种会直接导致烂科普。
用法：python validate_brief.py <PAPER-BRIEF.json>   （违规 exit 1）
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
    for k in ("title", "authors", "year", "one_liner", "audience", "duration_target", "bpm"):
        v = meta.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            err(f"meta.{k} 缺失或为空")
    if not isinstance(meta.get("duration_target"), (int, float)) or meta.get("duration_target", 0) <= 0:
        err("meta.duration_target 必须为正秒数")

    hooks = b.get("hook_candidates", [])
    if len(hooks) < 2:
        err(f"hook_candidates 只有 {len(hooks)} 条（需 ≥2，钩子要挑过才有得选）")
    for i, h in enumerate(hooks):
        if not (h.get("claim") or "").strip() or not (h.get("why_it_works") or "").strip():
            err(f"hook_candidates[{i}] 缺 claim 或 why_it_works")

    mech = b.get("mechanism", [])
    if not (3 <= len(mech) <= 5):
        err(f"mechanism {len(mech)} 步（要求 3-5 步人话因果链）")
    for i, m in enumerate(mech):
        if not (m.get("say") or "").strip():
            err(f"mechanism[{i}] 缺 say")

    nums = b.get("numbers", [])
    if len(nums) < 2:
        err(f"numbers 只有 {len(nums)} 条（需 ≥2：视频里至少立得住两个数字锚）")
    for i, n in enumerate(nums):
        missing = [k for k in ("value", "unit", "claim", "comparison", "source")
                   if not str(n.get(k, "")).strip() and n.get(k) is not None or k not in n]
        missing = [k for k in ("value", "unit", "claim", "comparison", "source")
                   if not str(n.get(k, "") or "").strip()]
        if missing:
            err(f"numbers[{i}] 缺 {','.join(missing)}——无来源/无对比的数字不许上片")

    metaphors = b.get("metaphors", [])
    with_breaks = sum(1 for m in metaphors if (m.get("breaks") or "").strip())
    if metaphors and with_breaks < max(1, len(metaphors) // 2):
        err(f"metaphors 里只有 {with_breaks}/{len(metaphors)} 条标了失效点（≥50% 必须标）")

    caveats = b.get("caveats", [])
    if len([c for c in caveats if (c or "").strip()]) < 1:
        err("caveats 空——没有防误读边界的科普会翻车")

    ok = not errors
    print(json.dumps({"ok": ok,
                      "errors": errors,
                      "stats": {"title": meta.get("title"), "year": meta.get("year"),
                                "hooks": len(hooks), "mechanism": len(mech),
                                "numbers": len(nums), "caveats": len(caveats)}},
                     ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
