/* beat-counter — 大数字滚动 + 公式框积木（数字锚点/机制推演）
 * params: {cx, cy, font_px, to, decimals, prefix, suffix, expr,
 *          t_count:[a,b], t_expr:[a,b]}
 * 数字 = 唯一发光元素（计数期间），公式框描边用强调色。
 * 强调语言（2026-11-06 用户定调）：数字落定后绝对静止——不呼吸不缩放；
 * 强调 = 落定瞬间下方 accent 下划线一次性扫出（之后静态保持）；
 * 持续运动源交给场景级巡游光带（数字本体永远稳）。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['beat-counter'] = {
  l2: function (ctx, T, sc, P, U) {
    const cx = (P.cx ?? 0.42) * U.W, cy = (P.cy ?? 0.42) * U.H;
    const fs = P.font_px ?? 200;
    const tc = P.t_count || [0.5, 3.0];
    const g = U.easeOutCubic(U.seg(T, tc[0], tc[1]));
    const val = (P.to ?? 37.8) * g;
    const txt = (P.prefix ?? '') + val.toFixed(P.decimals ?? 1) + (P.suffix ?? '');
    const glow = T >= tc[0] && T < tc[1] + 0.4;
    if (glow) {
      ctx.save();
      ctx.shadowColor = U.ACCENT; ctx.shadowBlur = 30;
    }
    ctx.fillStyle = U.ACCENT;
    ctx.font = `700 ${fs}px Consolas, monospace`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    const w = ctx.measureText(txt).width;
    ctx.fillText(txt, cx - w / 2, cy + fs * 0.35);
    if (glow) ctx.restore();
    /* 落定下划线：定格后一次性扫出，静态保持 */
    const ulA = U.easeOutCubic(U.seg(T, tc[1] + 0.4, tc[1] + 1.0));
    if (ulA > 0) {
      ctx.fillStyle = U.rgba(0.85 * ulA);
      ctx.fillRect(cx - w / 2, cy + fs * 0.35 + 22, w * ulA, 5);
    }
    const te = P.t_expr || [tc[0] + 0.2, tc[0] + 1.0];
    const ea = U.seg(T, te[0], te[1]);
    if (ea > 0 && P.expr) {
      ctx.font = '44px Consolas, monospace';
      ctx.textAlign = 'left';
      const ew = ctx.measureText(P.expr).width;
      const ex = cx - ew / 2, ey = cy + fs * 0.35 + 96;
      ctx.globalAlpha = ea;
      ctx.fillStyle = 'rgba(234,234,242,0.92)';
      ctx.fillText(P.expr, ex, ey);
      ctx.strokeStyle = U.ACCENT;
      ctx.lineWidth = 2;
      ctx.strokeRect(ex - 24, ey - 44, ew + 48, 64);
      ctx.globalAlpha = 1;
    }
    /* 巡游光带：扫过数字+公式区（大面积匀速平移才是够 0.35%/帧的运动源） */
    const zoneW = Math.max(w, 720) + 280;
    const swp = ((T - tc[0]) % 4.2) / 4.2;
    const bA = 0.085 * Math.min(1, Math.min(swp, 1 - swp) / 0.12);
    if (bA > 0.004) {
      const sx = cx - zoneW / 2 - 60 + swp * (zoneW + 120);
      ctx.fillStyle = U.rgba(bA);
      ctx.fillRect(sx, cy - fs * 1.05, 110, fs * 1.45 + 170);
    }
  }
};
