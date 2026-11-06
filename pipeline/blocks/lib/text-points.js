/* text-points — 要点逐条点亮积木（机制步骤/三要点展开）
 * params: {cx, cy, w, area_pct, items:[{text, sub, t_in}], row_h, t_hold}
 * 视觉：每条 = accent 编号点（命中亮起后恒定不脉冲）+ 主文 ink + 副行 gray；
 * 进场 = 点亮 + 文本上移淡入；未进场条不可见。
 * 持续运动源：进度下划线（点亮→场景尾持续填充）+ 编号点脉冲 + 巡游光带。
 * QA 教训（paper-shannon-deep 实测）：3px 细线怎么动都凑不够 0.35%/帧 的
 * 变化像素底线（~7.2k px/帧 @1080p）——细线没有面积。长场景尾部要靠
 * 大面积匀速平移的光带（110px 宽 accent 微光，两缘 ~10px/帧 ≈ 9.7k px/帧）。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['text-points'] = {
  l2: function (ctx, T, sc, P, U) {
    const w = P.w ?? 1100;
    const cx = (P.cx ?? 0.42) * U.W, cy = (P.cy ?? 0.44) * U.H;
    const items = P.items || [];
    const rowH = P.row_h ?? 150;
    const x0 = cx - w / 2;
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      const tIn = it.t_in ?? (i * 1.2);
      const g = U.easeOutCubic(U.seg(T, tIn, tIn + 0.7));
      if (g <= 0) continue;
      const iy = cy - ((items.length - 1) * rowH) / 2 + i * rowH;
      const isActive = (it.t_out === undefined) || (T < it.t_out);
      /* 编号点恒定（不脉冲不伸缩——用户定调：晃动别扭）；运动源 = 下划线 + 巡游光带 */
      const col = isActive ? U.ACCENT : U.GRAY;
      ctx.fillStyle = col;
      ctx.globalAlpha = g * 0.9;
      ctx.beginPath(); ctx.arc(x0 + 16, iy, Math.max(3, 8 * g), 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 1;
      /* 进度下划线：从点亮到 t_out（默认场景尾）持续填充 */
      const iEnd = it.t_out ?? sc.t_out;
      const pg = U.clamp01((T - tIn) / Math.max(0.1, iEnd - tIn));
      if (pg > 0) {
        ctx.fillStyle = U.rgba(0.5 * g);
        ctx.fillRect(x0 + 44, iy + 54, (w - 70) * pg, 3);
      }
      ctx.save();
      ctx.translate(x0 + 44, iy + 8 * (1 - g));
      U.drawText(ctx, it.text, 0, 0, { font: '30px "Microsoft YaHei"', color: isActive ? U.INK : U.GRAY, align: 'left', alpha: g });
      if (it.sub) U.drawText(ctx, it.sub, 0, 40, { font: '21px "Microsoft YaHei"', color: U.GRAY, align: 'left', alpha: g * 0.9 });
      ctx.restore();
    }
    /* 巡游光带：accent 微光带横扫要点区（每 4s 一轮，两端 12% 行程内淡入淡出） */
    const bh = items.length * rowH;
    const t0 = items.length ? (items[0].t_in ?? 0) : 0;
    const swp = ((T - t0) % 4.0) / 4.0;
    const bA = 0.085 * Math.min(1, Math.min(swp, 1 - swp) / 0.12);
    if (bA > 0.004) {
      const sx = x0 - 60 + swp * (w + 120);
      ctx.fillStyle = U.rgba(bA);
      ctx.fillRect(sx, cy - bh / 2 - 14, 110, bh + 28);
    }
  }
};
