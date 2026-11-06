#!/usr/bin/env python3
"""QA v4 边缘检测回归夹具（纯合成帧，不依赖任何成片/Chrome/ffmpeg）。

它把三个历史事故钉死成断言：
  1. 深底片里「中灰内容贴边」——绝对亮度线 235 看不见，v4 必须看见；
  2. 浅底片里「暗色文字贴边」——edge_max 纹丝不动，v4 必须看见；
  3. 浅底片正常背景（亮度 252）——绝对亮度线全帧误报，v4 必须不报。

用法：python pipeline/qa/test_edge_v4.py
CI：见 .github/workflows/ci.yml「QA v4 edge regression」
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_check import EDGE_AREA, EDGE_BAND, EDGE_DELTA, EDGE_LEGACY, edge_flags, edge_histogram  # noqa: E402

H, W = 270, 480
EX, EY = int(W * EDGE_BAND), int(H * EDGE_BAND)


def frame(bg, *, vignette=0.0, speckle=None, spill=None):
    """造一帧：均匀背景 + 可选暗角 + 可选零散噪点 + 可选贴边溢出块。"""
    a = np.full((H, W), bg, dtype=np.float32)
    if vignette:
        # 让四条边带整体略暗，模拟 paper 浅底的暗角（中心 252 → 边缘 ~232）
        a[:EY, :] -= vignette
        a[-EY:, :] -= vignette
        a[:, :EX] -= vignette
        a[:, -EX:] -= vignette
    if speckle:
        val, frac = speckle
        n = int(frac * (2 * EY * W + 2 * EX * H))
        rng = np.random.default_rng(7)
        ys = rng.integers(0, H, n)
        xs = rng.choice(np.concatenate([rng.integers(0, EX, n),
                                        rng.integers(W - EX, W, n)]), n)
        a[ys, xs] = val
    if spill:
        val, y0, y1, x0, x1 = spill
        a[y0:y1, x0:x1] = val
    return np.clip(a, 0, 255)


def verdict(frames, bg, legacy=False):
    hists = np.zeros((len(frames), 256), dtype=np.int64)
    emax = np.zeros(len(frames))
    for i, a in enumerate(frames):
        hists[i], emax[i] = edge_histogram(a, EX, EY)
    idx, ratios, style = edge_flags(hists, emax, bg, legacy=legacy)
    return idx, ratios, style, emax


class TestEdgeV4(unittest.TestCase):

    def test_01_dark_normal_no_bleed(self):
        """深底正常帧：边带只有极少量亮点，不该报。"""
        a = frame(14, speckle=(83, 0.0004))
        idx, ratios, style, emax = verdict([a], 13.8)
        self.assertEqual(style, 'dark')
        self.assertEqual(idx, [])
        self.assertLess(ratios[0], EDGE_AREA)
        self.assertLess(emax[0], EDGE_LEGACY)

    def test_02_light_normal_no_bleed(self):
        """浅底正常帧：暗角 + 零散深色像素，不该报；v3 绝对线会全帧误报。"""
        a = frame(252, vignette=20, speckle=(120, 0.001))
        idx, ratios, style, emax = verdict([a], 221.3)
        self.assertEqual(style, 'light')
        self.assertEqual(idx, [])
        self.assertLess(ratios[0], EDGE_AREA)
        # 同样的帧交给 legacy：emax 232 侥幸不过线；把暗角去掉就必然误报
        self.assertEqual(verdict([frame(252)], 252.0, legacy=True)[0], [0])

    def test_03_dark_white_spill_detected(self):
        """深底纯白溢出：v4 与 legacy 都该报。"""
        a = frame(14, spill=(245, 60, 160, 2, EX - 2))
        idx, _, _, emax = verdict([a], 13.8)
        self.assertEqual(idx, [0])
        self.assertEqual(verdict([a], 13.8, legacy=True)[0], [0])
        self.assertGreater(emax[0], EDGE_LEGACY)

    def test_04_dark_midgray_spill_legacy_blind(self):
        """深底中灰溢出（L=140）：legacy 完全漏检，v4 必须报。"""
        a = frame(14, spill=(140, 60, 160, 2, EX - 2))
        idx, _, _, emax = verdict([a], 13.8)
        self.assertEqual(idx, [0])
        self.assertLess(emax[0], EDGE_LEGACY)
        self.assertEqual(verdict([a], 13.8, legacy=True)[0], [])

    def test_05_light_dark_spill_legacy_blind(self):
        """浅底暗色文字溢出：edge_max 不变（仍是暗角值 232），legacy 瞎，v4 必须报。"""
        clean = frame(252, vignette=20)
        dirty = frame(252, vignette=20, spill=(30, 60, 160, 2, EX - 2))
        idx, _, _, emax = verdict([clean, dirty], 221.3)
        self.assertEqual(idx, [1])
        _, _, _, legacy_max = verdict([clean, dirty], 221.3, legacy=True)
        self.assertAlmostEqual(legacy_max[0], legacy_max[1], places=3)
        self.assertEqual(verdict([clean, dirty], 221.3, legacy=True)[0], [])

    def test_06_style_boundary_and_area_gate(self):
        """画风按全片中位数判定；异常必须「有面积」，单个噪点不算溢出。"""
        self.assertEqual(edge_flags(np.zeros((1, 256), dtype=np.int64), np.zeros(1), 127.9)[2], 'dark')
        self.assertEqual(edge_flags(np.zeros((1, 256), dtype=np.int64), np.zeros(1), 128.0)[2], 'light')
        tiny = frame(14, speckle=(200, 0.0001))
        idx, ratios, _, _ = verdict([tiny], 13.8)
        self.assertEqual(idx, [])
        self.assertLess(ratios[0], EDGE_AREA)

    def test_07_multiframe_bleed_count(self):
        """多帧序列：只报真正溢出的那一帧，不因前后帧翻转画风。"""
        frames_ = [frame(14), frame(14, spill=(180, 60, 160, 2, EX - 2)), frame(14)]
        idx, _, style, _ = verdict(frames_, 13.8)
        self.assertEqual(style, 'dark')
        self.assertEqual(idx, [1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
