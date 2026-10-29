/* data-chart — 双曲线分叉对比积木（自带生长式坐标轴，l1 可省）
 * params: {cx, cy, w, h, t_axes:[a,b], t_grow:[a,b],
 *          series: [{kind:'flat'|'exp', color:'ink'|'gray'|'accent', width>=2,
 *                    level(高 度比例), k(指数陡度), label, label_font}]}
 * 曲线末端在 grow>0.96 后出现端点 + 标签（ '?' 可作悬念钩子）。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['data-chart'] = {
  l2: function (ctx, T, sc, P, U) {
    const w = P.w ?? 980, h = P.h ?? 560;
    const cx = (P.cx ?? 0.42) * U.W, cy = (P.cy ?? 0.46) * U.H;
    const x0 = cx - w / 2, y0 = cy + h / 2;
    const tAx = P.t_axes || [0.4, 1.2];
    const ag = U.easeOutCubic(U.seg(T, tAx[0], tAx[1]));
    if (ag > 0) {
      ctx.strokeStyle = U.rgbaInk(0.28 * ag);
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0 + w * ag, y0); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0, y0 - h * ag); ctx.stroke();
      ctx.lineWidth = 1.6;
      ctx.strokeStyle = U.rgbaInk(0.20 * ag);
      for (let i = 1; i <= 4; i++) {
        const gx = x0 + w * i / 4 * ag, gy = y0 - h * i / 4 * ag;
        ctx.beginPath(); ctx.moveTo(gx, y0 - 7); ctx.lineTo(gx, y0 + 7); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x0 - 7, gy); ctx.lineTo(x0 + 7, gy); ctx.stroke();
      }
    }
    const tg = P.t_grow || [0.6, 3.2];
    const g = U.easeOutCubic(U.seg(T, tg[0], tg[1]));
    if (g <= 0) return;
    for (const s of (P.series || [])) {
      const color = s.color === 'accent' ? U.ACCENT : (s.color === 'ink' ? U.INK : U.GRAY);
      const lw = s.width ?? 2.5;
      const n = 72;
      ctx.strokeStyle = color;
      ctx.lineWidth = lw;
      ctx.lineJoin = 'round';
      ctx.beginPath();
      let lx = 0, ly = 0, drawn = 0;
      for (let i = 0; i <= n; i++) {
        const q = i / n;
        if (q > g) break;
        const px = x0 + w * q;
        let py;
        if (s.kind === 'flat') py = y0 - h * (s.level ?? 0.14);
        else {
          const k = s.k ?? 5;
          py = y0 - h * 0.92 * (Math.exp(k * q) - 1) / (Math.exp(k) - 1);
        }
        if (drawn === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        lx = px; ly = py; drawn++;
      }
      ctx.stroke();
      if (g > 0.96 && drawn > 0 && s.label) {
        ctx.fillStyle = color;
        ctx.beginPath(); ctx.arc(lx, ly, lw * 1.6 + 2, 0, Math.PI * 2); ctx.fill();
        U.drawText(ctx, s.label, lx + 20, ly + 6,
          { font: `${s.label_font ?? 34}px Consolas, monospace`, color, align: 'left' });
      }
    }
  }
};
