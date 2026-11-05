/* vs-counters — 左右双数字对撞积木（双结局/反转落点）
 * params: {font_px, cy, t_count:[a,b], left:{cx,to,decimals,label,expr,t_label},
 *          right:{...同 left}}
 * 约定：右侧 = 强调色 + 发光（赢家），左侧 = 辅助灰。中缝竖线脉冲一次。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['vs-counters'] = {
  l2: function (ctx, T, sc, P, U) {
    const fs = P.font_px ?? 150;
    const tc = P.t_count || [0.3, 1.6];
    const g = U.easeOutCubic(U.seg(T, tc[0], tc[1]));
    const items = [['left', P.left, false], ['right', P.right, true]];
    for (const [side, cfg, isAccent] of items) {
      if (!cfg) continue;
      const cx = (cfg.cx ?? (side === 'left' ? 0.31 : 0.69)) * U.W;
      const cy = (cfg.cy ?? (P.cy ?? 0.40)) * U.H;
      const val = (cfg.to ?? 1) * g;
      const txt = (cfg.prefix ?? '') + val.toFixed(cfg.decimals ?? 2);
      const color = isAccent ? U.ACCENT : U.GRAY;
      const isPulse = T > tc[1] + 0.4;
      const pulse = isPulse ? 1 + 0.035 * Math.sin((T - tc[1] - 0.4) * 3.7) : 1;
      if (isAccent && T >= tc[0] && T < tc[1] + 0.4) {
        ctx.save();
        ctx.shadowColor = U.ACCENT; ctx.shadowBlur = 26;
      }
      ctx.fillStyle = color;
      ctx.font = `700 ${fs}px Consolas, monospace`;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'alphabetic';
      const w = ctx.measureText(txt).width;
      ctx.save();
      ctx.translate(cx, cy);
      ctx.scale(pulse, pulse);
      ctx.translate(-cx, -cy);
      ctx.fillText(txt, cx - w / 2, cy + fs * 0.35);
      ctx.restore();
      if (isAccent && T >= tc[0] && T < tc[1] + 0.4) ctx.restore();
      const tl = cfg.t_label ?? tc[0];
      const la = U.seg(T, tl, tl + 0.8);
      if (la > 0) {
        if (cfg.label) U.drawText(ctx, cfg.label, cx, cy - fs * 0.62,
          { font: '25px "Microsoft YaHei"', color: U.GRAY, alpha: la });
        if (cfg.expr) U.drawText(ctx, cfg.expr, cx, cy + fs * 0.35 + 64,
          { font: '36px Consolas, monospace', color: isAccent ? U.ACCENT : U.GRAY, alpha: la });
      }
    }
    if (P.divider === true) {
      const va = U.seg(T, tc[0] - 0.1, tc[0] + 0.5);
      if (va > 0 && va < 1) {
        ctx.strokeStyle = U.rgbaInk(0.3 * (1 - Math.abs(2 * va - 1)));
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(U.W * 0.5, U.H * 0.26);
        ctx.lineTo(U.W * 0.5, U.H * 0.58);
        ctx.stroke();
      }
    }
  }
};
