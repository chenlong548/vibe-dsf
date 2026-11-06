/* repo-card — 收尾卡（项目介绍线 · land 段）
 * params: {cx, cy, w, repo:'owner/name', stars, lang, chips:[..], install, t_star, area?}
 * 视觉：owner/name 等宽大字（owner 灰、name 墨）+ teal 星标脉冲 + 星数滚动；
 * 语言 chips（发丝线圆角胶囊 + accent 点）逐个弹入（easeOutBack）；
 * 底部一行 $ 安装命令（sunken 胶囊 + 呼吸光标）= 可行动的收口。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['repo-card'] = {
  l2: function (ctx, T, sc, P, U) {
    const PAL = U.PAL || {};
    const SUNKEN = PAL.sunken || '#f4f4f1';
    const LINE = PAL.line || '#e6e5e1';
    const w = P.w ?? 1200;
    const cx = (P.cx ?? 0.5) * U.W, cy = (P.cy ?? 0.45) * U.H;
    const tIn = P.t_in ?? sc.t_in;
    const g0 = U.seg(T, tIn, tIn + 0.4);
    if (g0 <= 0) return;
    const mono = 'Consolas, monospace';
    /* --- repo 名：owner/ 灰 + name 墨 --- */
    const repo = P.repo ?? '';
    const slash = repo.lastIndexOf('/');
    const owner = slash > 0 ? repo.slice(0, slash + 1) : '';
    const name = slash > 0 ? repo.slice(slash + 1) : repo;
    ctx.font = '600 52px ' + mono;
    const ownerW = ctx.measureText(owner).width;
    const nameW = ctx.measureText(name).width;
    const rx = cx - (ownerW + nameW) / 2;
    const ry = cy - 90;
    const rise = 18 * (1 - U.easeOutBack(g0));
    U.drawText(ctx, owner, rx, ry + rise, { font: '600 52px ' + mono, color: U.GRAY, align: 'left', alpha: g0 });
    U.drawText(ctx, name, rx + ownerW, ry + rise, { font: '600 52px ' + mono, color: U.INK, align: 'left', alpha: g0 });
    /* --- 星标 + 星数滚动（stars 未提供则显示语言，不编数字） --- */
    const tStar = P.t_star ?? (tIn + 0.8);
    const gs = U.seg(T, tStar, tStar + 0.9);
    if (gs > 0){
      const rowY = ry + 64;
      const starX = cx - 110;
      ctx.globalAlpha = gs;
      if ((P.stars ?? 0) > 0){
        U.drawText(ctx, '★', starX, rowY, { font: '34px sans-serif', color: U.ACCENT, align: 'left', alpha: gs });
        ctx.globalAlpha = 1;
        const stars = Math.round((P.stars ?? 0) * U.easeOutCubic(gs));
        U.drawText(ctx, String(stars), starX + 30, rowY, { font: '600 32px ' + mono, color: U.INK, align: 'left', alpha: gs });
        U.drawText(ctx, P.lang ? P.lang : '', starX + 170, rowY, { font: '22px ' + mono, color: U.GRAY, align: 'left', alpha: gs * 0.9 });
      } else {
        U.drawText(ctx, '●', starX, rowY, { font: '30px sans-serif', color: U.ACCENT, align: 'left', alpha: gs });
        ctx.globalAlpha = 1;
        U.drawText(ctx, P.lang ? P.lang : '', starX + 30, rowY, { font: '22px ' + mono, color: U.GRAY, align: 'left', alpha: gs * 0.9 });
      }
    }
    /* --- chips：发丝线胶囊 + accent 点，逐个弹入 --- */
    const chips = P.chips || [];
    const chipY = ry + 130;
    let chipX = cx - (function est(){
      ctx.font = '20px ' + mono;
      let s = 0;
      for (const c of chips) s += ctx.measureText(c).width + 74;
      return (s - 40) / 2;
    })();
    for (let i = 0; i < chips.length; i++){
      const tci = tIn + 0.5 + i * 0.18;
      const gc = U.easeOutBack(U.seg(T, tci, tci + 0.5));
      if (gc <= 0) break;
      ctx.font = '20px ' + mono;
      const cw = ctx.measureText(chips[i]).width + 52;
      const chH = 44;
      const shy = chipY + 10 * (1 - gc);
      ctx.save();
      ctx.globalAlpha = Math.min(1, gc);
      ctx.fillStyle = SUNKEN;
      ctx.strokeStyle = LINE; ctx.lineWidth = 1.5;
      const rr = 10;
      const bx = chipX, by = shy;
      ctx.beginPath();
      ctx.moveTo(bx + rr, by); ctx.arcTo(bx + cw, by, bx + cw, by + chH, rr);
      ctx.arcTo(bx + cw, by + chH, bx, by + chH, rr);
      ctx.arcTo(bx, by + chH, bx, by, rr);
      ctx.arcTo(bx, by, bx + cw, by, rr);
      ctx.closePath();
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = U.ACCENT;
      ctx.beginPath(); ctx.arc(bx + 22, by + chH / 2, 5, 0, Math.PI * 2); ctx.fill();
      U.drawText(ctx, chips[i], bx + 36, by + chH / 2 + 7, { font: '20px ' + mono, color: U.INK, align: 'left', alpha: 1 });
      ctx.restore();
      chipX += cw + 22;
    }
    /* --- 安装命令：sunken 胶囊 + $ teal + 呼吸光标 --- */
    if (P.install){
      const tci = tIn + 1.2;
      const gi = U.seg(T, tci, tci + 0.5);
      if (gi > 0){
        ctx.font = '22px ' + mono;
        const iw = ctx.measureText(P.install).width + 96;
        const ih = 52;
        const ix = cx - iw / 2, iy = ry + 196 + 8 * (1 - U.easeOutBack(gi));
        ctx.save();
        ctx.globalAlpha = gi;
        ctx.fillStyle = SUNKEN;
        ctx.strokeStyle = LINE; ctx.lineWidth = 1.5;
        const rr = 12;
        ctx.beginPath();
        ctx.moveTo(ix + rr, iy); ctx.arcTo(ix + iw, iy, ix + iw, iy + ih, rr);
        ctx.arcTo(ix + iw, iy + ih, ix, iy + ih, rr);
        ctx.arcTo(ix, iy + ih, ix, iy, rr);
        ctx.arcTo(ix, iy, ix + iw, iy, rr);
        ctx.closePath();
        ctx.fill(); ctx.stroke();
        U.drawText(ctx, '$', ix + 28, iy + ih / 2 + 8, { font: '22px ' + mono, color: U.ACCENT, align: 'left' });
        /* 安装命令逐字敲入（一次性，终端语言）；打完只剩终端光标闪烁 */
        const nCh = Math.floor(U.seg(T, tci, tci + P.install.length / 18) * P.install.length + 0.001);
        const shown = P.install.slice(0, nCh);
        U.drawText(ctx, shown, ix + 56, iy + ih / 2 + 8, { font: '22px ' + mono, color: U.INK, align: 'left' });
        /* 静态 teal 描边（胶囊外圈，恒定不呼吸） */
        ctx.strokeStyle = U.ACCENT; ctx.lineWidth = 2.5;
        ctx.globalAlpha = gi * 0.16;
        ctx.beginPath();
        ctx.moveTo(ix + rr, iy); ctx.arcTo(ix + iw, iy, ix + iw, iy + ih, rr);
        ctx.arcTo(ix + iw, iy + ih, ix, iy + ih, rr);
        ctx.arcTo(ix, iy + ih, ix, iy, rr);
        ctx.arcTo(ix, iy, ix + iw, iy, rr);
        ctx.closePath();
        ctx.stroke();
        ctx.font = '22px ' + mono;
        const typing = nCh < P.install.length;
        if (typing || Math.sin(T * 5.5) > -0.15){
          ctx.fillStyle = U.INK; ctx.globalAlpha = gi * 0.8;
          ctx.fillRect(ix + 62 + ctx.measureText(shown).width, iy + ih / 2 - 9, 11, 20);
        }
        ctx.restore();
      }
    }
  }
};
