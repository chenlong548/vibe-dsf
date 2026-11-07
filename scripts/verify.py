#!/usr/bin/env python3
"""One-command MVP acceptance check for VIBE-DSF.

Runs the core release-surface checks WITHOUT Chrome, ffmpeg, audio files or
rendered frames. The same command is used locally and in CI, so the two never
drift apart. It does not test the optional extensions (paper2video,
project2video, review page, creative-model helpers) -- see docs/24-MVP.md.

Usage:  python scripts/verify.py
Exit:   0 = MVP READY, 1 = MVP NOT READY

Output is deliberately ASCII-only: Windows host consoles may decode UTF-8
stdout as ANSI, and a garbled PASS/FAIL line is worse than a plain one.
"""
from __future__ import annotations

import glob
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
NODE = shutil.which("node")

# Machine-readable definition of the MVP release surface. Anything not listed
# here is an optional extension and must never block a release.
CORE_FILES = (
    "VERSION", "CHANGELOG.md", "README.md", "README.en.md", "LICENSE",
    "SECURITY.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md",
    ".gitignore", ".github/workflows/ci.yml",
    "docs/24-MVP.md", "docs/25-ROADMAP.md", "docs/23-RELEASE.md",
    "brand/BRAND.md", "brand/logo.svg",
    "site/index.html", "site/check.py",
    "scripts/setup.ps1", "scripts/verify.py",
    "pipeline/requirements.txt", "pipeline/palette.json",
    "pipeline/run_all.ps1", "pipeline/render/render_frames.mjs",
    "pipeline/qa/qa_check.py", "pipeline/qa/test_edge_v4.py",
    "pipeline/report/generate.py", "pipeline/report/test_generate.py",
    "pipeline/scene_writer/PROMPT.md", "pipeline/scene_writer/template.html",
    "pipeline/scene_writer/SCENE-PLAN.schema.md",
    "pipeline/scene_writer/validate_plan.py",
    "pipeline/scene_writer/build_html.mjs",
    "pipeline/blocks/registry.json", "pipeline/blocks/lib/_easings.js",
    "pipeline/audio/synth_bgm.py", "pipeline/audio/synth_sfx.py",
    "pipeline/audio/wave_png.py",
    "pipeline/audio/narrate/tts_edge.py",
    "pipeline/audio/narrate/build_narration.py",
    "pipeline/audio/narrate/mix_audio.py",
    "pipeline/compose/build.ps1",
    "projects/_probe/SCENE-PLAN.json",
)

NODE_PATTERNS = (
    "pipeline/*.mjs",
    "pipeline/render/*.mjs",
    "pipeline/scene_writer/*.mjs",
    "pipeline/blocks/lib/*.js",
)

results: list[tuple[str, bool, str]] = []


def safe(text: str, limit: int = 500) -> str:
    """Force ASCII and keep only the tail, so failures stay readable."""
    s = (text or "").strip().encode("ascii", "replace").decode("ascii")
    return s[-limit:] if len(s) > limit else s


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, bool(ok), detail))
    tag = "PASS" if ok else "FAIL"
    line = f"[{tag}] {name:<22}"
    if detail:
        line += f" {safe(detail, 160)}"
    print(line, flush=True)


def run(name: str, argv: list[str], check=None, timeout: int = 180) -> None:
    try:
        p = subprocess.run(
            argv, cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001 - report, never crash the runner
        record(name, False, f"{type(exc).__name__}: {exc}")
        return
    extra = ""
    if check is not None:
        try:
            ok, extra = check(p)
        except Exception as exc:  # noqa: BLE001
            ok, extra = False, f"check error: {type(exc).__name__}: {exc}"
    else:
        ok = p.returncode == 0
    if not ok:
        tail = safe((p.stderr or "") + "\n" + (p.stdout or ""))
        extra = (extra + " | " + tail).strip(" |")
    record(name, ok, extra or f"exit={p.returncode}")


def check_version() -> None:
    try:
        v = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except Exception as exc:  # noqa: BLE001
        record("version-sync", False, f"cannot read VERSION: {exc}")
        return
    targets = {
        "CHANGELOG.md": f"[{v}]",
        "README.md": f"v{v}",
        "README.en.md": f"v{v}",
        "site/index.html": f"v{v}",
    }
    missing = []
    for rel, needle in targets.items():
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            missing.append(rel)
            continue
        if needle not in text:
            missing.append(rel)
    record("version-sync", not missing,
           f"v{v} in {len(targets) - len(missing)}/{len(targets)} files"
           + (f" | missing: {', '.join(missing)}" if missing else ""))


def check_core_files() -> None:
    missing = [rel for rel in CORE_FILES if not (ROOT / rel).is_file()]
    record("core-files", not missing,
           f"{len(CORE_FILES) - len(missing)}/{len(CORE_FILES)} required files"
           + (f" | missing: {', '.join(missing)}" if missing else ""))


def check_node_syntax() -> None:
    if not NODE:
        record("node-syntax", False, "node not found on PATH (Node 20+ required)")
        return
    files = sorted({p for pat in NODE_PATTERNS
                    for p in glob.glob(str(ROOT / pat))})
    bad = []
    for f in files:
        try:
            p = subprocess.run([NODE, "--check", f], cwd=str(ROOT),
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60)
            if p.returncode != 0:
                bad.append(Path(f).name + ": " + safe(p.stderr or p.stdout, 120))
        except Exception as exc:  # noqa: BLE001
            bad.append(Path(f).name + ": " + type(exc).__name__)
    record("node-syntax", bool(files) and not bad,
           f"{len(files) - len(bad)}/{len(files)} js/mjs files"
           + (f" | {'; '.join(bad[:3])}" if bad else ""))


def check_assemble() -> None:
    if not NODE:
        record("assemble-smoke", False, "node not found on PATH")
        return
    with tempfile.TemporaryDirectory(prefix="vibe-mvp-") as tmp:
        out = Path(tmp) / "smoke_index.html"
        argv = [NODE, "pipeline/scene_writer/build_html.mjs",
                "--plan", "projects/_probe/SCENE-PLAN.json",
                "--out", str(out)]

        def verify(p, out=out):
            if p.returncode != 0:
                return False, "build_html exited non-zero"
            if not out.is_file() or out.stat().st_size == 0:
                return False, "output html missing or empty"
            body = out.read_text(encoding="utf-8", errors="replace")
            if "render(" not in body:
                return False, "output html has no render() entry point"
            return True, f"single-file html {out.stat().st_size} bytes, render() present"

        run("assemble-smoke", argv, check=verify)


def main() -> int:
    print("=== VIBE-DSF MVP acceptance ===", flush=True)
    check_version()
    check_core_files()
    run("python-syntax", [PY, "-m", "compileall", "-q",
                          "pipeline", "site", "scripts"])
    check_node_syntax()
    run("plan-gate", [PY, "pipeline/scene_writer/validate_plan.py",
                      "projects/_probe/SCENE-PLAN.json"])
    check_assemble()
    run("qa-edge-regression", [PY, "pipeline/qa/test_edge_v4.py"])
    run("report-regression", [PY, "pipeline/report/test_generate.py"])
    run("site-self-check", [PY, "site/check.py"])

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    failed = [name for name, ok, _ in results if not ok]
    print("-" * 46, flush=True)
    if failed:
        print(f"--- {passed}/{total} PASS | MVP NOT READY | "
              f"failed: {', '.join(failed)} ---", flush=True)
        return 1
    print(f"--- {passed}/{total} PASS | MVP READY ---", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
