/* timeline — 年份轴积木（历史脉络/演化）
 * params: {cx, cy, w, area_pct, marks:[{year, label, t_in}], t_axis:[a,b]}
 * 视觉：水平轴线生长 → 刻度点逐个亮起 → 年份 mono + 事件标签上移淡入；
 * 轴线上 accent 粒子持续向右流动（持续运动源）。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['timeline'] = {
  l2: function (ctx, T, sc, P, U) {
    const w = P.w ?? 1400;
    const cx = (P.cx ?? 0.42) * U.W, cy = (P.cy ?? 0.46) * U.H;
    const ta = P.t_axis || [0.4, 1.4];
    const marks = P.marks || [];
    const x0 = cx - w / 2, x1 = cx + w / 2;
    const ag = U.easeOutCubic(U.seg(T, ta[0], ta[1]));
    if (ag > 0) {
      ctx.strokeStyle = U.rgbaInk(0.4 * ag);
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(x0, cy); ctx.lineTo(x0 + w * ag, cy); ctx.stroke();
    }
    const span = (marks.length > 1) ? (marks[marks.length - 1].year - marks[0].year) || 1 : 1;
    for (let i = 0; i < marks.length; i++) {
      const m = marks[i];
      const g = U.easeOutBack(U.seg(T, m.t_in ?? ta[1], (m.t_in ?? ta[1]) + 0.6));
      if (g <= 0) continue;
      const mx = x0 + w * ag * (m.year - marks[0].year) / span;
      const isAccent = i === marks.length - 1;
      const col = isAccent ? U.ACCENT : U.INK;
      ctx.fillStyle = col;
      ctx.globalAlpha = g;
      ctx.beginPath(); ctx.arc(mx, cy, (isAccent ? 9 : 6) * g, 0, Math.PI * 2); ctx.fill();
      if (isAccent) {
        /* 终点年静态双环：强调 = 大小 + 颜色 + 环，不呼吸不伸缩 */
        ctx.strokeStyle = U.rgba(0.55);
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(mx, cy, 16, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.globalAlpha = 1;
      const rise = 14 * (1 - g);
      U.drawText(ctx, String(m.year), mx, cy - 46 - rise, { font: '36px Consolas, monospace', color: col, alpha: g });
      if (m.label) U.drawText(ctx, m.label, mx, cy + 52 - rise, { font: '21px "Microsoft YaHei"', color: U.GRAY, alpha: g });
    }
    if (T > ta[1]) {
      /* 粒子流：两股加粗提速（静止段治理：18×r2 太小测不出） */
      for (let i = 0; i < 30; i++) {
        const lane = (i % 2) * 10 - 5;
        const px = x0 + ((i * 173 + T * 95) % (w * ag));
        const pa = 0.45 + 0.4 * Math.sin(T * 7 + i * 2.1);
        if (pa <= 0.12) continue;
        ctx.fillStyle = U.rgba(pa);
        ctx.beginPath(); ctx.arc(px, cy + lane + 3 * Math.sin(T * 2 + i), 3, 0, Math.PI * 2); ctx.fill();
      }
      /* teal 扫掠游标：6s 一轮横扫整根轴，两端淡出（大运动源） */
      if (ag >= 1) {
        const sw = ((T - ta[1]) % 6) / 6;
        const sx = x0 + sw * w;
        const sa = Math.sin(Math.PI * sw);
        ctx.strokeStyle = U.rgba(0.5 * sa);
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(sx, cy - 64); ctx.lineTo(sx, cy + 64); ctx.stroke();
        ctx.fillStyle = U.rgba(0.85 * sa);
        ctx.beginPath();
        ctx.moveTo(sx, cy - 70); ctx.lineTo(sx - 6, cy - 82); ctx.lineTo(sx + 6, cy - 82);
        ctx.closePath(); ctx.fill();
      }
    }
  }
};
