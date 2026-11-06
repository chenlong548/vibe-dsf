#!/usr/bin/env python3
"""generate.py —— 一键流水线的机器可读执行档案（pipeline_report.json）

两种模式：

1) 事件追加（run_all.ps1 每阶段调一次，append-only JSONL）
   python generate.py --event _pipeline_events.jsonl --stage qa --status ok \
          --seconds 8.234 --code 0 --message "QA 8.82 过闸"

2) 汇总落盘（run_all.ps1 统一出口调一次，**成功和失败都调**）
   python generate.py --finalize --events _pipeline_events.jsonl \
          --project-dir projects/demo-hook-compound --exit-code 0 \
          --elapsed 42.71 --fps 30

设计要点
- 事件流 append-only：流水线中途崩溃，已完成阶段也留得下，不用等 finalize。
- 汇总阶段**自己扫项目目录**，PowerShell 侧不拼任何 JSON —— 避开 PS 5.1 的
  UTF-8/转义/单元素数组退化坑，报告里的中文是原样的。
- 可观测性不能反过来卡住生产：报告生成出错也只写一份带 error 的最小档案，
  始终返回 0，绝不改变 run_all.ps1 的退出码。

产物：pipeline_report.json（schema_version 见 SCHEMA_VERSION）
文档：docs/21-PIPELINE-REPORT.md
"""
import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = "1.0"
REPORT_NAME = "pipeline_report.json"
EVENTS_NAME = "_pipeline_events.jsonl"
QA_GATE = 8.0

# 汇总时扫描的固定产物（键 = 报告里的语义名）
ARTIFACT_MAP = {
    "html": "index.html",
    "plan": "SCENE-PLAN.json",
    "qa_report": "qa.json",
    "bgm": "bgm.wav",
    "sfx": "sfx.wav",
    "narration": "narration.wav",
    "mix": "final_audio.wav",
    "video": "final.mp4",
}


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_event(path, stage, status, seconds, code, message):
    """追加一条阶段事件。任何字段都允许为空，格式错误也不抛给调用方。"""
    ev = {
        "ts": now_iso(),
        "stage": str(stage or "unknown"),
        "status": str(status or "unknown"),
        "seconds": round(float(seconds or 0), 3),
        "code": int(code or 0),
        "message": str(message or ""),
    }
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def read_events(path):
    """返回 (事件列表, 坏行数)。utf-8-sig 兼容 PS 5.1 可能写出的 BOM。"""
    p = Path(path)
    out, bad = [], 0
    if not p.exists():
        return out, bad
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            if isinstance(d, dict) and "stage" in d:
                out.append(d)
            else:
                bad += 1
        except Exception:
            bad += 1
    return out, bad


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def file_info(path):
    p = Path(path)
    if not p.is_file():
        return {"path": p.name, "missing": True}
    st = p.stat()
    return {
        "path": p.name,
        "bytes": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds"),
    }


def scan_frames(root, fps):
    d = root / "frames"
    n = len(list(d.glob("frame_*.png"))) if d.is_dir() else 0
    return {
        "dir": "frames",
        "count": n,
        "fps": fps,
        "duration": round(n / fps, 2) if fps else None,
    }


def qa_summary(root):
    d = load_json(root / "qa.json")
    if not d:
        return {"report": "qa.json", "missing": True}
    raw = d.get("raw") or {}
    score = d.get("score") or {}
    avg = d.get("avg")
    worst = [{"name": k, "score": v} for k, v in sorted(score.items(), key=lambda kv: kv[1])[:3]]
    return {
        "report": "qa.json",
        "avg": avg,
        "version": d.get("qa_version"),
        "gate": QA_GATE,
        "passed": (avg is not None and avg >= QA_GATE),
        "worst": worst,
        "budgets": d.get("budgets") or {},
        "edge": d.get("edge") or {},
        "issues": {
            "still_runs": len(raw.get("still_runs") or []),
            "cuts": raw.get("cuts"),
            "edge_bleed_frames": raw.get("edge_bleed_count", len(raw.get("edge_bleed") or [])),
            "subtitle_gaps": len(raw.get("sub_band_empty") or []),
        },
        "resolution": [raw.get("width"), raw.get("height")],
    }


def plan_summary(root):
    d = load_json(root / "SCENE-PLAN.json")
    if not d:
        return {"file": "SCENE-PLAN.json", "missing": True}
    meta = d.get("meta") or {}
    sfx = sum(len(sc.get("sfx") or []) for sc in (d.get("scenes") or [])
              if isinstance(sc.get("sfx"), list))
    return {
        "file": "SCENE-PLAN.json",
        "version": d.get("version"),
        "topic": meta.get("topic"),
        "style": meta.get("style"),
        "palette_name": meta.get("palette_name"),
        "duration": meta.get("duration"),
        "fps": meta.get("fps"),
        "bpm": meta.get("bpm"),
        "scenes": len(d.get("scenes") or []),
        "subtitles": len(d.get("subtitles") or []),
        "narration_lines": len(d.get("narration") or []),
        "sfx_events": sfx,
    }


def build_report(args, events, bad_lines):
    root = Path(args.project_dir).resolve()
    code = int(args.exit_code)
    elapsed = round(float(args.elapsed or 0), 2)
    version_file = Path(args.version_file) if args.version_file else Path(__file__).resolve().parents[2] / "VERSION"
    try:
        pipeline_version = version_file.read_text(encoding="utf-8").strip()
    except Exception:
        pipeline_version = "unknown"

    failed_stage = next((e.get("stage") for e in reversed(events)
                         if e.get("status") == "failed"), None)
    if code != 0 and not failed_stage:
        failed_stage = "preflight"      # 工具定位 / html 检查等早期失败
    verdict = "success" if code == 0 else ("qa_blocked" if code == 2 else "failed")

    statuses = [e.get("status") for e in events]
    qa = qa_summary(root)
    frames = scan_frames(root, args.fps)
    frames["resolution"] = qa.get("resolution")

    return {
        "schema_version": SCHEMA_VERSION,
        "pipeline_version": pipeline_version,
        "project": root.name,
        "project_dir": str(root).replace("\\", "/"),
        "started_at": events[0].get("ts") if events else now_iso(),
        "finished_at": now_iso(),
        "elapsed": elapsed,
        "exit_code": code,
        "verdict": verdict,
        "failed_stage": failed_stage,
        "summary": {
            "stages_total": len(events),
            "stages_ok": statuses.count("ok"),
            "stages_skipped": statuses.count("skipped"),
            "stages_failed": statuses.count("failed"),
            "stage_seconds": round(sum(float(e.get("seconds") or 0) for e in events), 2),
            "bad_event_lines": bad_lines,
        },
        "stages": events,
        "frames": frames,
        "qa": qa,
        "plan": plan_summary(root),
        "artifacts": {key: file_info(root / name) for key, name in ARTIFACT_MAP.items()},
        "events_file": EVENTS_NAME,
    }


def finalize(args):
    """汇总并落盘。返回 0 恒定：报告失败不能改变流水线退出码。"""
    root = Path(args.project_dir).resolve()
    out = Path(args.out) if args.out else root / REPORT_NAME
    try:
        events, bad = read_events(args.events)
        report = build_report(args, events, bad)
    except Exception as e:
        report = {
            "schema_version": SCHEMA_VERSION,
            "project": root.name,
            "finished_at": now_iso(),
            "exit_code": int(args.exit_code),
            "verdict": "report_error",
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc(limit=4),
        }
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        qa_avg = (report.get("qa") or {}).get("avg", "—")
        print(f"[report] {out.name} · exit {report.get('exit_code')} · "
              f"{len(report.get('stages') or [])} 阶段 · {report.get('elapsed', 0)}s · QA {qa_avg}")
    except Exception as e:
        print(f"[report][warn] 报告写入失败（不影响流水线）：{e}", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description="一键流水线执行报告生成器")
    ap.add_argument("--event", help="事件流 JSONL 路径（追加一条阶段事件）")
    ap.add_argument("--finalize", action="store_true", help="汇总事件流并写 pipeline_report.json")
    ap.add_argument("--stage")
    ap.add_argument("--status", choices=["ok", "skipped", "failed", "unknown"], default="unknown")
    ap.add_argument("--seconds", type=float, default=0.0)
    ap.add_argument("--code", type=int, default=0)
    ap.add_argument("--message", default="")
    ap.add_argument("--events", help="finalize 用：事件流路径")
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--exit-code", type=int, default=0)
    ap.add_argument("--elapsed", type=float, default=0.0)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--out", help="finalize 用：报告输出路径（默认 <project>/pipeline_report.json）")
    ap.add_argument("--version-file", help="VERSION 路径（默认自动定位仓库根）")
    a = ap.parse_args()

    if a.finalize:
        return finalize(a)
    if a.event:
        try:
            append_event(a.event, a.stage, a.status, a.seconds, a.code, a.message)
        except Exception as e:
            print(f"[report][warn] 事件写入失败（不影响流水线）：{e}", file=sys.stderr)
        return 0
    ap.error("需要 --event <events.jsonl> 或 --finalize")
    return 2


if __name__ == "__main__":
    sys.exit(main())
