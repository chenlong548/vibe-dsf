/* =====================================================================
 * _easings.js — GSAP 级缓动预设集（P1 #10）
 * ---------------------------------------------------------------------
 * 命名空间 EASE，全部纯函数 (p: 0..1) -> (0..1)，无状态、确定性。
 * 由 build_html.mjs 恒定注入（下划线开头 = 非积木，不进 registry），
 * 注入点在 U 工具集之前——template 与积木都可用。
 *
 * 纪律（2026-11-06 强调语言定调，见 blocks/README）：
 *   · easeOutBack 是"阻尼版"（c=1.70158*0.6，本库定稿值）——像素与历史积木一致；
 *     只准用于一次性入场/扫出，禁用于落定后的持续状态。
 *   · 故意不提供 Elastic / Spring / Wiggle：振荡往复 = 落定后晃动，
 *     正是用户明确反感的东西。谁在库里加回来，谁先过 QA 纪律那关。
 *   · 入场时长 ≤0.2s（>0.4s 的面板淡入会被 QA 计成连续硬切）。
 * ===================================================================== */
const EASE = {
  linear:          p => p,
  easeInQuad:      p => p * p,
  easeOutQuad:     p => p * (2 - p),
  easeInOutQuad:   p => (p < 0.5 ? 2 * p * p : -1 + (4 - 2 * p) * p),
  easeOutCubic:    p => 1 - Math.pow(1 - p, 3),
  easeInOutCubic:  p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
  easeOutQuart:    p => 1 - Math.pow(1 - p, 4),
  easeInOutQuart:  p => (p < 0.5 ? 8 * p * p * p * p : 1 - Math.pow(-2 * p + 2, 4) / 2),
  easeOutQuint:    p => 1 - Math.pow(1 - p, 5),
  easeInOutQuint:  p => (p < 0.5 ? 16 * p * p * p * p * p : 1 - Math.pow(-2 * p + 2, 5) / 2),
  easeOutExpo:     p => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p)),
  easeInOutExpo:   p => (p === 0 ? 0 : p === 1 ? 1 : p < 0.5 ? Math.pow(2, 20 * p - 10) / 2 : (2 - Math.pow(2, -20 * p + 10)) / 2),
  easeOutCirc:     p => Math.sqrt(1 - Math.pow(p - 1, 2)),
  easeInOutCirc:   p => (p < 0.5 ? (1 - Math.sqrt(1 - Math.pow(2 * p, 2))) / 2 : (Math.sqrt(1 - Math.pow(-2 * p + 2, 2)) + 1) / 2),
  easeOutSine:     p => Math.sin(p * Math.PI / 2),
  easeInOutSine:   p => -(Math.cos(Math.PI * p) - 1) / 2,
  /* 阻尼版过冲（本库定稿 = 历史 U.easeOutBack 同式，渲染像素一致） */
  easeOutBack:     p => { const c = 1.70158 * 0.6; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
  /* 全强度过冲（GSAP back.out(1.7) 标准值）——新积木要更明显回弹时用，仍限一次性 */
  easeOutBackStrong: p => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); },
  easeOutBounce:   p => { const n1 = 7.5625, d1 = 2.75;
                          if (p < 1 / d1) return n1 * p * p;
                          if (p < 2 / d1) return n1 * (p -= 1.5 / d1) * p + 0.75;
                          if (p < 2.5 / d1) return n1 * (p -= 2.25 / d1) * p + 0.9375;
                          return n1 * (p -= 2.625 / d1) * p + 0.984375; },
};
