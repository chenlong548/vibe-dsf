#!/usr/bin/env python3
"""产物报告回归夹具（纯临时目录，不依赖 Chrome / ffmpeg / 真实成片）。

覆盖：成功路径、QA 拦截、早期失败、合成失败、坏事件行、缺产物、CLI 中文往返、append-only。
用法：python pipeline/report/test_generate.py
CI：见 .github/workflows/ci.yml「Pipeline report regression」
"""
import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate  # noqa: E402

HERE = Path(__file__).resolve().parent
CLI = str(HERE / "generate.py")

QA = {
    "raw": {"frames": 30, "fps": 30, "width": 1920, "height": 1080,
            "still_runs": [[0.9, 2.1]], "cuts": 0, "edge_bleed": [],
            "edge_bleed_count": 0, "sub_band_empty": []},
    "visual": {}, "score": {"画面密度": 9, "安全区": 10, "首帧抓人": 6, "画面充实": 7},
    "avg": 8.82, "qa_version": "v4",
    "budgets": {"duration": 1.0, "still_budget": 2, "cut_budget": 6},
    "edge": {"mode": "style-aware", "style": "dark", "bleed_frames": 0},
}
PLAN = {
    "version": "1.0",
    "meta": {"topic": "复利效应", "style": "deep-space", "duration": 1.0,
             "fps": 30, "bpm": 126, "palette_name": None},
    "scenes": [{"id": "s1", "sfx": [{"t": 0.5, "name": "tick"}]}, {"id": "s2"}, {"id": "s3"}],
    "subtitles": [{"t_in": 0.1}, {"t_in": 0.4}, {"t_in": 0.8}],
    "narration": [{"text": "a"}, {"text": "b"}],
}


class TestPipelineReport(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / "demo-proj"
        self.root.mkdir()
        (self.root / "frames").mkdir()
        for i in range(1, 31):
            (self.root / "frames" / f"frame_{i:05d}.png").write_bytes(b"x")
        (self.root / "index.html").write_text("<html></html>", encoding="utf-8")
        (self.root / "final.mp4").write_bytes(b"v" * 100)
        (self.root / "qa.json").write_text(json.dumps(QA, ensure_ascii=False), encoding="utf-8")
        (self.root / "SCENE-PLAN.json").write_text(json.dumps(PLAN, ensure_ascii=False), encoding="utf-8")
        self.version_file = self.base / "VERSION"
        self.version_file.write_text("9.9.9", encoding="utf-8")
        self.events = self.root / generate.EVENTS_NAME

    def tearDown(self):
        self.tmp.cleanup()

    def emit(self, *specs):
        for stage, status, sec, code, msg in specs:
            generate.append_event(self.events, stage, status, sec, code, msg)

    def do_finalize(self, code=0, elapsed=12.34):
        a = argparse.Namespace(events=str(self.events), project_dir=str(self.root),
                               exit_code=code, elapsed=elapsed, fps=30,
                               out=None, version_file=str(self.version_file))
        self.assertEqual(generate.finalize(a), 0)
        return json.loads((self.root / generate.REPORT_NAME).read_text(encoding="utf-8"))

    def test_01_success_shape(self):
        """成功路径：阶段统计、帧数、QA 摘要、plan 摘要、产物字节数齐全。"""
        self.emit(("render", "skipped", 0.01, 0, "-SkipRender"),
                  ("qa", "ok", 1.5, 0, "QA 8.82 过闸"),
                  ("bgm", "ok", 0.8, 0, "ambient"),
                  ("audio", "ok", 6.2, 0, "三层混音"),
                  ("compose", "ok", 3.8, 0, "final.mp4"))
        r = self.do_finalize()
        self.assertEqual(r["exit_code"], 0)
        self.assertEqual(r["verdict"], "success")
        self.assertIsNone(r["failed_stage"])
        self.assertEqual(r["pipeline_version"], "9.9.9")
        self.assertEqual(r["schema_version"], "1.0")
        self.assertEqual(r["project"], "demo-proj")
        self.assertEqual(r["summary"]["stages_total"], 5)
        self.assertEqual(r["summary"]["stages_skipped"], 1)
        self.assertEqual(r["summary"]["stage_seconds"], 12.31)
        self.assertEqual(r["frames"]["count"], 30)
        self.assertEqual(r["frames"]["duration"], 1.0)
        self.assertEqual(r["frames"]["resolution"], [1920, 1080])
        self.assertEqual(r["qa"]["avg"], 8.82)
        self.assertEqual(r["qa"]["version"], "v4")
        self.assertTrue(r["qa"]["passed"])
        self.assertEqual(r["qa"]["worst"][0]["name"], "首帧抓人")
        self.assertEqual(r["qa"]["edge"]["mode"], "style-aware")
        self.assertEqual(r["qa"]["issues"]["still_runs"], 1)
        self.assertEqual(r["plan"]["scenes"], 3)
        self.assertEqual(r["plan"]["narration_lines"], 2)
        self.assertEqual(r["plan"]["sfx_events"], 1)
        self.assertEqual(r["plan"]["topic"], "复利效应")
        self.assertEqual(r["artifacts"]["video"]["bytes"], 100)
        self.assertTrue(r["artifacts"]["sfx"]["missing"])

    def test_02_qa_blocked(self):
        """QA 闸门拦截：exit 2 → verdict=qa_blocked，failed_stage 指向 qa。"""
        self.emit(("render", "ok", 2.0, 0, "343 帧"),
                  ("qa", "failed", 1.1, 2, "总分 < 8"))
        r = self.do_finalize(code=2)
        self.assertEqual(r["verdict"], "qa_blocked")
        self.assertEqual(r["failed_stage"], "qa")
        self.assertEqual(r["summary"]["stages_failed"], 1)

    def test_03_preflight_failure_without_events(self):
        """工具定位等早期失败：一条事件都没有，报告仍要落盘且标 preflight。"""
        self.events.write_text("", encoding="utf-8")
        r = self.do_finalize(code=1, elapsed=0.2)
        self.assertEqual(r["verdict"], "failed")
        self.assertEqual(r["failed_stage"], "preflight")
        self.assertEqual(r["stages"], [])
        self.assertEqual(r["summary"]["stages_total"], 0)
        self.assertEqual(r["artifacts"]["video"]["bytes"], 100)

    def test_04_compose_failure(self):
        """非 QA 的失败阶段也要能定位。"""
        self.emit(("render", "ok", 1, 0, "ok"), ("qa", "ok", 1, 0, "ok"),
                  ("bgm", "ok", 1, 0, "ok"), ("audio", "ok", 1, 0, "ok"),
                  ("compose", "failed", 0.4, 3, "ffmpeg 失败"))
        r = self.do_finalize(code=3)
        self.assertEqual(r["verdict"], "failed")
        self.assertEqual(r["failed_stage"], "compose")
        self.assertEqual(r["summary"]["stages_ok"], 4)

    def test_05_bad_event_lines_tolerated(self):
        """事件流被截断/写坏时，坏行只计数，不拖垮汇总。"""
        self.emit(("render", "ok", 1.0, 0, "ok"))
        with self.events.open("a", encoding="utf-8") as f:
            f.write('{"stage": "qa", BROKEN\n')
            f.write("[1, 2, 3]\n")
        r = self.do_finalize()
        self.assertEqual(r["summary"]["bad_event_lines"], 2)
        self.assertEqual(r["summary"]["stages_total"], 1)

    def test_06_missing_everything_tolerated(self):
        """缺 qa.json / plan / 成片：只标 missing，不抛异常、不改写退出码。"""
        for name in ("qa.json", "SCENE-PLAN.json", "final.mp4"):
            (self.root / name).unlink()
        self.emit(("qa", "failed", 0.1, 1, "无报告"))
        r = self.do_finalize(code=1)
        self.assertTrue(r["qa"]["missing"])
        self.assertTrue(r["plan"]["missing"])
        self.assertTrue(r["artifacts"]["video"]["missing"])
        self.assertEqual(r["frames"]["count"], 30)

    def test_07_cli_append_and_finalize_chinese(self):
        """CLI 两模式往返：中文消息原样保留（ensure_ascii=False）。"""
        subprocess.run([sys.executable, CLI, "--event", str(self.events),
                        "--stage", "qa", "--status", "ok", "--seconds", "1.5",
                        "--code", "0", "--message", "QA 8.82 过闸"],
                       check=True, capture_output=True)
        subprocess.run([sys.executable, CLI, "--finalize", "--events", str(self.events),
                        "--project-dir", str(self.root), "--exit-code", "0",
                        "--elapsed", "1.5", "--fps", "30",
                        "--version-file", str(self.version_file)],
                       check=True, capture_output=True)
        r = json.loads((self.root / generate.REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(r["stages"][0]["message"], "QA 8.82 过闸")
        self.assertEqual(r["exit_code"], 0)

    def test_08_append_only_order(self):
        """事件 append-only，顺序与耗时精度稳定。"""
        self.emit(("render", "ok", 1.2345, 0, "a"), ("qa", "ok", 2.0, 0, "b"))
        lines = self.events.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["stage"], "render")
        self.assertEqual(json.loads(lines[0])["seconds"], 1.234)
        self.assertEqual(json.loads(lines[1])["stage"], "qa")


if __name__ == "__main__":
    unittest.main(verbosity=2)
