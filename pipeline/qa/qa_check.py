#!/usr/bin/env python3
"""
qa_check.py v4 —— 把"这条片子好不好看"变成可测的数字

为什么需要它：flash 的自我评价不可信——它会说"挺好的"，而画面里字被截了。
验收器必须比模型更严格，否则省下的 token 钱，会以"你盯着看 200 帧"的时间成本还回去。

v1 检测项（运动/结构，逐帧实测）：
  1. 画面密度   —— 每帧有多少比例的像素在变（变化像素占比 %）
  2. 静止段     —— 连续多少秒画面几乎不动（铁律：≤ 4 秒）
  3. 硬切次数   —— 帧间突变（差 > 25）的个数；全片 2–6 次最佳
  4. 边缘溢出   —— 内容超出安全区（画面四边亮像素）
  5. 字幕带空档 —— 85%–91% 高度是否长时间无内容
  6. 首帧抓人   —— 前 2 秒的差分是否 > 全片均值

v2 新增（审美维度，每秒采样 1 帧，全部校准自真实成片）：
  7. 画面充实   —— 中央视觉区"内容占比"（偏离背景中位数的像素）。
                   实测：空的天平镜头 3.5%，正常镜头 8–10%，爆款密度应 ≥ 12%
  8. 构图偏置   —— 主视觉重心的水平位置。中位数落在 [0.47,0.53] = 居中癖（F1 违规）
  9. 强调焦点   —— 高饱和强调色像素占比。实测：PPT 灰字帧 ≈ 0.04%，有金/红焦点 ≈ 1%
 10. 字幕占用   —— 字幕带内文字像素占比（字幕太小太细 = 看不见）

v3 新增（评分口径，见 docs/19-QA-V3.md）：
 11. 时长预算   —— 断点/硬切预算按片长缩放，长片不再被按短片校准的固定阈值冤枉；
                   --v2 可回退旧口径做同帧对比。

v4 新增（检测口径，见 docs/20-QA-V4.md）：
 12. 画风感知边缘 —— 弃用绝对亮度线 edge_max>235：深底片只抓得到纯白溢出（中灰漏检），
                   浅底片背景本身就过线（全帧误报）、暗色文字溢出反而完全看不见。
                   改为"相对背景 ±96 灰阶 + 边带异常面积 ≥0.3%"：深底查亮溢出、
                   浅底查暗溢出。--legacy-edge 可回退旧检测做同帧对比。

门禁：总分 < 8 → 退出码 1（流水线据此硬卡，不许带病交付）。

用法：
  python ../pipeline/qa/qa_check.py frames/ --fps 30
  python ../pipeline/qa/qa_check.py frames/ --fps 30 --json report.json
  python ../pipeline/qa/qa_check.py frames/ --fps 30 --no-gate     # 只看报告，不卡门禁
  python ../pipeline/qa/qa_check.py frames/ --fps 30 --v2           # v2 全口径回退
  python ../pipeline/qa/qa_check.py frames/ --fps 30 --legacy-edge  # 仅回退边缘检测（= v3）
"""
import argparse
import json
import math
import os
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("需要依赖：pip install pillow numpy")

# Windows 控制台默认 GBK，中文会乱码；强制 UTF-8（老终端可先执行 chcp 65001）
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ---- v4 边缘检测参数（校准自 demo-hook-compound 深底 / project-vibe-dsf 浅底，见 docs/20）----
EDGE_BAND = 0.025     # 安全区：四边各 2.5%
EDGE_DELTA = 96.0     # 相对背景亮度差：超过才算"不像背景"
EDGE_AREA = 0.003     # 边带内异常像素占比门槛（0.3% ≈ 620px @1080p）
EDGE_LEGACY = 235.0   # v2/v3 绝对亮度线（只用于回退对比，别再用于判断）


def edge_histogram(a, ex, ey):
    """四条边带的 256 级亮度直方图 + 最大亮度。

    直方图是紧凑缓存：长片 5400 帧只多占 ~11MB，判定画风时无需二次读帧。
    """
    e = np.concatenate([a[:ey, :].ravel(), a[-ey:, :].ravel(),
                        a[:, :ex].ravel(), a[:, -ex:].ravel()])
    return np.histogram(e, bins=256, range=(0, 256))[0], float(e.max())


def edge_flags(hists, edge_max, bg, delta=EDGE_DELTA, area=EDGE_AREA, legacy=False):
    """返回 (溢出帧索引, 逐帧异常占比, 画风)。

    画风与背景基线都取**全片**亮度中位数，不逐帧翻转——否则白闪/黑场一帧
    就会把风格判定带跑。深底查亮内容溢出，浅底查暗内容溢出；两者都要求
    "有面积"，单个噪点不算。
    """
    if legacy:
        return [i for i in range(len(edge_max)) if edge_max[i] > EDGE_LEGACY], None, 'legacy'
    dark = bg < 128
    centers = np.arange(256) + 0.5
    sel = centers > bg + delta if dark else centers < bg - delta
    ratios = hists[:, sel].sum(axis=1) / np.maximum(hists.sum(axis=1), 1)
    return [i for i in range(len(ratios)) if ratios[i] >= area], ratios, ('dark' if dark else 'light')


def load_frames(folder):
    files = sorted(f for f in os.listdir(folder) if f.startswith('frame_') and f.endswith('.png'))
    if not files:
        sys.exit(f'{folder} 里没有 frame_*.png')
    return [os.path.join(folder, f) for f in files]


def runs_of(mask, fps, min_sec=0.8):
    """把布尔序列压成连续区间（秒）"""
    out, start = [], None
    for i, s in enumerate(mask):
        if s and start is None:
            start = i
        elif not s and start is not None:
            out.append((start, i)); start = None
    if start is not None:
        out.append((start, len(mask)))
    return [(a / fps, b / fps) for a, b in out if (b - a) / fps >= min_sec]


def analyze(paths, fps, still_thresh, cut_thresh, grace=1.0, legacy_edge=False):
    """
    两个指标，缺一不可：
      diff_mean  —— 全屏平均亮度差（绝对值小，因为大片背景不动）
      changed    —— **画面有多少比例的像素真的在变**（感知上更接近"有没有动"）
    """
    n = len(paths)
    W = H = None
    diff_mean = np.zeros(n)
    changed = np.zeros(n)               # 变化像素占比 %
    luma = np.zeros(n)
    edge_max = np.zeros(n)
    hists = np.zeros((n, 256), dtype=np.int64)
    sub_band = np.zeros(n)
    prev = None
    sub_lo = sub_hi = None

    for i, p in enumerate(paths):
        a = np.asarray(Image.open(p).convert('L'), dtype=np.float32)
        if W is None:
            H, W = a.shape
            ex, ey = int(W * EDGE_BAND), int(H * EDGE_BAND)
            sub_lo, sub_hi = int(H * 0.85), int(H * 0.91)
        luma[i] = a.mean()
        sub_band[i] = a[sub_lo:sub_hi, :].mean()
        hists[i], edge_max[i] = edge_histogram(a, ex, ey)
        if prev is not None:
            d = np.abs(a - prev)
            diff_mean[i] = d.mean()
            changed[i] = (d > 8).mean() * 100.0
        prev = a

    # 静止 = 变化像素占比低于阈值（默认 0.35%）
    still_runs = runs_of(changed[1:] < still_thresh, fps, 0.8)
    duration = n / fps
    longest_still = max((b - a for a, b in still_runs), default=0.0)

    cuts = [i for i in range(1, n) if changed[i] > cut_thresh]
    density = float(changed[1:].mean()) if n > 1 else 0.0
    head = float(changed[1:min(n, int(2 * fps))].mean()) if n > 4 else 0.0

    # 字幕带为空：只在"应该已有字幕"的中段判定（跳过片头/片尾 grace 秒）
    empty_runs = [r for r in runs_of(sub_band < 4.0, fps, 0.5)
                  if r[1] > grace and r[0] < duration - grace]

    bg = float(np.median(luma))
    bleed, ratios, style = edge_flags(hists, edge_max, bg, legacy=legacy_edge)

    return dict(
        frames=n, fps=fps, width=W, height=H,
        density=round(density, 2),
        diff_mean=round(float(diff_mean[1:].mean()) if n > 1 else 0.0, 3),
        head_density=round(head, 2),
        longest_still=round(float(longest_still), 2),
        still_runs=[(round(a, 2), round(b, 2)) for a, b in still_runs],
        cuts=len(cuts), cut_times=[round(i / fps, 2) for i in cuts[:12]],
        edge_bleed=[round(i / fps, 2) for i in bleed][:10],
        edge_bleed_count=len(bleed),
        edge_mode='absolute-235' if legacy_edge else 'style-aware',
        edge_style=style,
        edge_bg=round(bg, 1),
        edge_delta=EDGE_DELTA,
        edge_area=EDGE_AREA,
        edge_anomaly_max=round(float(ratios.max() * 100), 3) if ratios is not None else None,
        sub_band_empty=[(round(a, 2), round(b, 2)) for a, b in empty_runs][:10],
    )


def analyze_visual(paths, fps):
    """
    v2 审美维度：每秒采 1 帧（fps 步长），逐帧算 4 个数字再取中位数。
    阈值全部校准自真实成片（见 docs/10-GAP-ANALYSIS.md 附录）：
      空镜头纹理能量 ~3.7%，正常镜头 7–8%，满镜 10%+；
      PPT 灰字强调色 ~0.04%，有金/红焦点 ~1%。
    """
    stride = max(1, int(round(fps)))
    samples = paths[::stride]
    content_r, com_xs, accents, sub_occs = [], [], [], []
    for p in samples:
        im = Image.open(p)
        W, H = im.size
        rgb = np.asarray(im.convert('RGB'), dtype=np.float32) / 255.0
        L = np.asarray(im.convert('L'), dtype=np.float32)
        cy, cx = H // 2, W // 2
        ch, cw = int(H * 0.30), int(W * 0.40)          # 中央视觉区：y 20–80%，x 10–90%
        cL = L[cy - ch:cy + ch, cx - cw:cx + cw]
        med = float(np.median(cL))

        # 内容占比 = 纹理能量占比（3x3 邻域局部标准差 > 4 的像素）。
        # v2.1 起弃用 |L-median|>12 口径：它对中央亮渐变失真、对细线条不敏感。
        d = cL[::4, ::4]                                # 1/4 下采样提速
        pad = np.pad(d, 1, mode='edge')
        st = [pad[i:i + d.shape[0], j:j + d.shape[1]] for i in range(3) for j in range(3)]
        sq = sum(s * s for s in st) / 9.0
        mu = sum(st) / 9.0
        std = np.sqrt(np.maximum(sq - mu * mu, 0))
        content_r.append(float((std > 4).mean() * 100))

        # 主视觉重心（y 15–72%，避开字幕带；亮于背景 +25 才算内容）
        m2 = L[int(H * 0.15):int(H * 0.72), :]
        ys, xs = np.where(m2 > med + 25)
        com_xs.append(float(xs.mean()) / W if len(xs) > 0.0005 * W * H else -1.0)

        mx = rgb.max(axis=2); mn = rgb.min(axis=2)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        accents.append(float(((sat > 0.30) & (mx > 0.35)).mean() * 100))

        band = L[int(H * 0.85):int(H * 0.91), :]
        sub_occs.append(float((band > 120).mean() * 100))

    def med(v, drop_missing=True):
        v = [x for x in v if not (drop_missing and x < 0)]
        return round(float(np.median(v)), 2) if v else -1.0

    return dict(
        sampled=len(samples),
        content_ratio=med(content_r),
        com_x=med(com_xs),
        accent_ratio=med(accents),
        sub_occupancy=med(sub_occs),
        com_x_values=[round(x, 2) for x in com_xs][:30],   # 逐帧值给人工评审用
    )


def score(r, v, v2=False):
    """风格 DNA 打分（1–10）。低于 8 的地方要改，不是"再看看"。

    v3（默认）：断点/硬切预算按时长缩放——180s 长片天然累积更多静止段与切点，
    固定阈值（≤2/≤4 断点、≤6/≤9 硬切）会冤枉长片。短片预算与 v2 完全等价，
    历史分数可比；--v2 可回退旧口径做同帧对比。

    v4 只改边缘**检测**（analyze 里），评分函数口径不变。
    """
    s = {}
    duration = r['frames'] / r['fps']
    still_budget = max(2, math.ceil(duration / 20.0))   # 每 20s 允许 1 个断点：8s→2, 50s→3, 180s→9
    cut_budget = max(6, math.ceil(duration / 15.0))     # 每 15s 允许 1 个硬切：8s→6, 180s→12
    d = r['density']
    s['画面密度'] = 10 if d >= 0.5 else 9 if d >= 0.3 else 7 if d >= 0.15 else 5 if d >= 0.08 else 3
    s['静止控制'] = 10 if r['longest_still'] <= 1.5 else 9 if r['longest_still'] <= 2.5 \
        else 7 if r['longest_still'] <= 4 else 4   # 最长段与片长无关，保持 v2 口径
    n_still = len(r['still_runs'])
    c = r['cuts']
    if v2:
        s['断点数量'] = 10 if n_still <= 2 else 8 if n_still <= 4 else 5
        s['切点节奏'] = 10 if 2 <= c <= 6 else 8 if c <= 9 else 5
    else:
        s['断点数量'] = 10 if n_still <= still_budget else 8 if n_still <= 2 * still_budget else 5
        s['切点节奏'] = 10 if 2 <= c <= cut_budget else 8 if c <= 1.5 * cut_budget else 5
    s['首帧抓人'] = 10 if r['head_density'] >= max(0.1, d) else 6
    s['安全区'] = 10 if r.get('edge_bleed_count', len(r['edge_bleed'])) == 0 else 5
    s['字幕覆盖'] = 10 if not r['sub_band_empty'] else 4
    # ---- v2 审美维度 ----
    cr = v['content_ratio']
    s['画面充实'] = 10 if cr >= 14 else 9 if cr >= 11 else 7 if cr >= 8 else 5 if cr >= 5 else 3
    cx = v['com_x']
    if cx < 0:
        s['构图偏置'] = 5          # 采不到主视觉 = 画面太空，本身已是问题
    else:
        centered = 0.47 <= cx <= 0.53
        s['构图偏置'] = 4 if centered else 10
    ac = v['accent_ratio']
    s['强调焦点'] = 10 if ac >= 0.8 else 8 if ac >= 0.3 else 6 if ac >= 0.1 else 3
    so = v['sub_occupancy']
    s['字幕占用'] = 10 if so >= 3 else 7 if so >= 1 else 4
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames')
    ap.add_argument('--fps', type=float, default=30)
    ap.add_argument('--still', type=float, default=0.35, help='判定"静止"的变化像素占比 %%（默认 0.35）')
    ap.add_argument('--cut', type=float, default=25.0, help='判定"硬切"的变化像素占比 %%（默认 25）')
    ap.add_argument('--grace', type=float, default=1.0, help='片头/片尾多少秒内不检查字幕带')
    ap.add_argument('--json', default=None)
    ap.add_argument('--no-gate', action='store_true', help='只出报告，不用退出码卡门禁')
    ap.add_argument('--v2', action='store_true', help='回退 v2 全部口径（固定阈值 + 绝对亮度边缘）')
    ap.add_argument('--legacy-edge', action='store_true',
                    help='仅把边缘检测回退到 v3 绝对亮度线 edge_max>235（同帧对比用）')
    a = ap.parse_args()

    legacy = a.v2 or a.legacy_edge
    paths = load_frames(a.frames)
    r = analyze(paths, a.fps, a.still, a.cut, a.grace, legacy_edge=legacy)
    v = analyze_visual(paths, a.fps)
    s = score(r, v, v2=a.v2)
    duration = r['frames'] / a.fps
    budgets = {'duration': round(duration, 2),
               'still_budget': max(2, math.ceil(duration / 20.0)),
               'cut_budget': max(6, math.ceil(duration / 15.0))}
    qa_version = 'v2' if a.v2 else ('v3' if a.legacy_edge else 'v4')

    print(f"\n帧序列：{r['frames']} 帧 / {duration:.2f}s  @ {r['width']}x{r['height']} {a.fps:g}fps")
    print(f"画面密度：每帧有 {r['density']}% 的像素在变   （参考：字幕整句淡入 ≈0.5%，粒子爆炸 ≈10%）")
    print(f"亮度差均值：{r['diff_mean']}   前 2 秒密度：{r['head_density']}%")
    print(f"最长静止段：{r['longest_still']}s   断点数：{len(r['still_runs'])}")
    if a.v2:
        print("QA 口径：v2（固定阈值 断点≤2/4、硬切≤6/9）")
    else:
        print(f"QA 口径：{qa_version} 时长预算（{budgets['duration']}s → 断点≤{budgets['still_budget']} / "
              f"硬切≤{budgets['cut_budget']}）；--v2 可回退旧口径")
    if legacy:
        print(f"边缘检测：{'v2/v3' if a.v2 else 'v3'} 绝对亮度线 edge_max>235（legacy，{r['edge_bleed_count']} 帧报溢出）")
    else:
        print(f"边缘检测：v4 画风感知（画风 {r['edge_style']} / 背景 {r['edge_bg']} / "
              f"阈值 ±{r['edge_delta']:g} / 面积门槛 {r['edge_area'] * 100:g}% / "
              f"异常峰值 {r['edge_anomaly_max']}%）")
    if r['still_runs']:
        print("  → 这些时间段画面几乎不动，去加东西：")
        for a1, b1 in r['still_runs'][:8]:
            print(f"     {a1:6.2f}s – {b1:6.2f}s   ({b1-a1:.2f}s)")
    print(f"硬切：{r['cuts']} 次  {r['cut_times']}")
    if r['edge_bleed']:
        more = (f"（共 {r['edge_bleed_count']} 帧，仅列前 10）"
                if r['edge_bleed_count'] > len(r['edge_bleed']) else "")
        print(f"[!] 疑似内容溢出安全区：{r['edge_bleed']}{more}")
    if r['sub_band_empty']:
        print(f"[!] 字幕带出现空档（中段）：{r['sub_band_empty']}")

    print(f"\n—— 审美维度（每秒采样，共 {v['sampled']} 帧）——")
    print(f"  纹理能量（中央视觉区）：{v['content_ratio']}%    参考：空镜头 3.7% / 正常 7–8% / 爆款 ≥11%")
    print(f"  主视觉重心 x：{v['com_x']}    参考：0.47–0.53 = 居中癖（F1 违规），目标 0.42–0.46 或 0.54–0.58")
    print(f"  强调色占比：{v['accent_ratio']}%    参考：PPT 灰字 ≈0.04%，有金/红焦点 ≈1%")
    print(f"  字幕文字占用：{v['sub_occupancy']}%    参考：≥3% 健康")

    print("\n—— 自检评分 ——")
    total = 0
    for k, val in s.items():
        flag = '[OK]' if val >= 8 else '[X] '
        print(f"  {flag} {k}: {val}/10")
        total += val
    avg = total / len(s)
    verdict = "通过，可以发" if avg >= 8 else "不通过：先修 [X] 项，只重渲受影响的那几秒"
    print(f"\n总分：{avg:.1f}/10（{len(s)} 项）  {verdict}")

    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'raw': r, 'visual': v, 'score': s, 'avg': round(avg, 2),
                       'qa_version': qa_version, 'budgets': budgets,
                       'edge': {'mode': r['edge_mode'], 'style': r['edge_style'],
                                'bg': r['edge_bg'], 'delta': r['edge_delta'],
                                'area': r['edge_area'], 'anomaly_max_pct': r['edge_anomaly_max'],
                                'bleed_frames': r['edge_bleed_count']}},
                      f, ensure_ascii=False, indent=2)
        print(f"报告：{a.json}")

    # 门禁：流水线靠退出码硬卡（--no-gate 可跳过）
    sys.exit(0 if (avg >= 8 or a.no_gate) else 1)


if __name__ == '__main__':
    main()
