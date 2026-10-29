/* beat-counter — 大数字滚动 + 公式框积木（数字锚点/机制推演）
 * params: {cx, cy, font_px, to, decimals, prefix, suffix, expr,
 *          t_count:[a,b], t_expr:[a,b]}
 * 数字 = 唯一发光元素（计数期间），公式框描边用强调色。 */
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
  }
};
