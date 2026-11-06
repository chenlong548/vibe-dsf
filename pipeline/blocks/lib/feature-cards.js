/* feature-cards — 编辑部式特性卡（项目介绍线 · paper 风格）
 * params: {cx, cy, card_w, card_h, gap, cards:[{tag, title, sub, t_in}]}
 * 视觉：白面卡片 + 发丝线框 + 墨影（独立站 surface/line 语言）；
 * 命中 = teal 顶条从 0 拉满（easeOutCubic）+ 卡片上浮淡入（easeOutBack）；
 * 命中后 tag 前的 accent 点持续脉冲。
 * 持续运动源（QA 教训：四卡弹入完毕后仅剩微脉冲 → 4.86s 静止段）：
 *   ① teal 微光带沿卡行横向巡游（每 4.2s 一轮，两缘 ~19px/帧）；
 *   ② 各卡底部进度线自命中起持续填充到场景尾。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['feature-cards'] = {
  l2: function (ctx, T, sc, P, U) {
    const PAL = U.PAL || {};
    const SFC = PAL.surface || '#ffffff';
    const LINE = PAL.line || '#e6e5e1';
    const INK_SHADOW = '22,24,28';
    const cw = P.card_w ?? 380, ch = P.card_h ?? 300, gap = P.gap ?? 40;
    const cards = P.cards || [];
    const cx = (P.cx ?? 0.5) * U.W, cy = (P.cy ?? 0.42) * U.H;
    const total = cards.length * cw + (cards.length - 1) * gap;
    const x0 = cx - total / 2, y0 = cy - ch / 2;
    for (let i = 0; i < cards.length; i++) {
      const it = cards[i];
      const tIn = it.t_in ?? (i * 0.9);
      const g = U.seg(T, tIn, tIn + 0.7);
      if (g <= 0) continue;
      const pop = U.easeOutBack(g);
      const x = x0 + i * (cw + gap), y = y0;
      ctx.save();
      ctx.globalAlpha = g;
      /* 卡面 + 墨影 */
      ctx.shadowColor = `rgba(${INK_SHADOW},0.08)`;
      ctx.shadowBlur = 14; ctx.shadowOffsetY = 6;
      ctx.fillStyle = SFC;
      ctx.fillRect(x, y + 24 * (1 - pop), cw, ch);
      ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
      /* 发丝线框 */
      ctx.strokeStyle = LINE; ctx.lineWidth = 1.5;
      ctx.strokeRect(x + 0.5, y + 0.5 + 24 * (1 - pop), cw - 1, ch - 1);
      /* teal 顶条：命中即从 0 拉满 */
      const bar = U.easeOutCubic(U.seg(T, tIn + 0.05, tIn + 0.75));
      ctx.fillStyle = U.ACCENT;
      ctx.fillRect(x, y + 24 * (1 - pop), cw * bar, 4);
      /* tag：accent 点脉冲 + 灰色小标 */
      const oy = y + 24 * (1 - pop);
      const dotR = 5 + 1.6 * Math.sin(T * 5.0 + i * 1.7);
      ctx.fillStyle = U.ACCENT;
      ctx.beginPath(); ctx.arc(x + 34, oy + 62, Math.max(2.5, dotR * g), 0, Math.PI * 2); ctx.fill();
      U.drawText(ctx, it.tag ?? '', x + 52, oy + 68, { font: '20px Consolas, monospace', color: U.GRAY, align: 'left', alpha: g, track: 2 });
      /* 标题 + 副行 */
      U.drawText(ctx, it.title ?? '', x + 34, oy + 138, { font: '600 34px "Microsoft YaHei"', color: U.INK, align: 'left', alpha: g });
      if (it.sub) U.drawText(ctx, it.sub, x + 34, oy + 190, { font: '21px "Microsoft YaHei"', color: U.GRAY, align: 'left', alpha: g * 0.95, maxW: cw - 68 });
      /* ② 底部进度线：自命中起填充到场景尾 */
      const pf = U.clamp01((T - tIn) / Math.max(0.1, (sc.t_out ?? tIn + 8) - tIn));
      const py = oy + ch - 30;
      ctx.globalAlpha = g * 0.9;
      ctx.fillStyle = LINE;
      ctx.fillRect(x + 34, py, cw - 68, 3);
      if (pf > 0.003){
        ctx.fillStyle = U.ACCENT;
        ctx.globalAlpha = g;
        ctx.fillRect(x + 34, py, (cw - 68) * pf, 3);
      }
      ctx.restore();
    }
    /* ① 巡游光带：120px 宽 teal 微光带沿卡行横向扫过（两缘 ~19px/帧） */
    const accRGB = (function (h){
      const m = /^#?([0-9a-f]{6})$/i.exec(h || '');
      return m ? [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4, 6), 16)].join(',') : '13,110,99';
    })(U.ACCENT);
    const tFirst = cards.length ? (cards[0].t_in ?? 0) : 0;
    const swp = ((T - tFirst) % 4.2) / 4.2;
    const bA = 0.10 * Math.min(1, Math.min(swp, 1 - swp) / 0.12);
    if (bA > 0.004){
      const span = total + 2 * cw;
      const sx = x0 - cw + swp * span;
      ctx.fillStyle = `rgba(${accRGB},${bA.toFixed(3)})`;
      ctx.fillRect(sx, y0 - 10, 120, ch + 20);
    }
  }
};
