/* terminal-window — 终端证据窗（项目介绍线 · paper 风格的点睛件）
 * 独立站设计语言：暗色面板只装"技术证据"（命令/输出/闸门结果）。
 * params: {cx, cy, w, h, title, lines:[{kind:'cmd'|'out'|'ok'|'warn', text, t_in, cps}], cursor, progress_to}
 * cmd 行 = '$ ' teal + 逐字敲入（cps 字/秒）+ 敲入中闪块光标；
 * out = 墨白 / ok = '✓' teal / warn = '!' 琥珀。
 * 持续运动源（QA 教训：打完字后整块面板静止 = 10.8s 静止段，7.4 分不过闸）：
 *   ① 入场 0.18s 快速弹现（0.5s 慢淡入曾把一次淡入计成 8 连"硬切"）；
 *   ② CRT 扫描光带每 4.5s 扫过面板（两缘 ~3.9px/帧）；
 *   ③ 底部执行进度条持续填充 + 条内 barber-pole 斜纹 90px/s 流动。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['terminal-window'] = {
  l2: function (ctx, T, sc, P, U) {
    const PAL = U.PAL || {};
    const TBG = PAL.term_bg || '#0e1214';
    const TLINE = PAL.term_line || '#242c30';
    const TINK = PAL.term_ink || '#d6dde1';
    const TDIM = PAL.term_dim || '#7c878e';
    const TACC = PAL.term_accent || '#5ed3b8';
    const TAMBER = PAL.term_amber || '#e3b341';
    const w = P.w ?? 1000, h = P.h ?? 520;
    const cx = (P.cx ?? 0.5) * U.W, cy = (P.cy ?? 0.42) * U.H;
    const x0 = cx - w / 2, y0 = cy - h / 2;
    const g = U.easeOutCubic(U.seg(T, P.t_in ?? sc.t_in, (P.t_in ?? sc.t_in) + 0.18));
    if (g <= 0) return;
    const BAR = 44;
    ctx.save();
    ctx.globalAlpha = g;
    /* 面板：暗底 + 墨影 + 发丝描边 */
    ctx.shadowColor = 'rgba(22,24,28,0.18)';
    ctx.shadowBlur = 22; ctx.shadowOffsetY = 8;
    ctx.fillStyle = TBG;
    ctx.fillRect(x0, y0 + 16 * (1 - g), w, h);
    ctx.shadowColor = 'transparent'; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
    ctx.strokeStyle = TLINE; ctx.lineWidth = 1.5;
    ctx.strokeRect(x0 + 0.5, y0 + 0.5 + 16 * (1 - g), w - 1, h - 1);
    /* 标题栏：三圆点 + 标题 */
    const dots = ['#ff5f56', '#ffbd2e', '#27c93f'];
    for (let i = 0; i < 3; i++){
      ctx.fillStyle = dots[i];
      ctx.globalAlpha = g * 0.9;
      ctx.beginPath(); ctx.arc(x0 + 26 + i * 24, y0 + BAR / 2 + 16 * (1 - g), 6, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = g;
    U.drawText(ctx, P.title ?? 'terminal', cx, y0 + BAR / 2 + 8 + 16 * (1 - g), { font: '18px Consolas, monospace', color: TDIM, alpha: g, track: 2 });
    ctx.strokeStyle = TLINE; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x0, y0 + BAR + 16 * (1 - g)); ctx.lineTo(x0 + w, y0 + BAR + 16 * (1 - g)); ctx.stroke();
    /* 内容行 */
    const lines = P.lines || [];
    const lineH = P.line_h ?? 40;
    let y = y0 + BAR + 34;
    for (let i = 0; i < lines.length; i++){
      const ln = lines[i];
      const tIn = ln.t_in ?? (i * 1.2);
      if (T < tIn) break;
      const kind = ln.kind || 'out';
      const cps = ln.cps ?? 16;
      const text = ln.text ?? '';
      const nChars = kind === 'cmd' ? Math.floor(U.seg(T, tIn, tIn + text.length / cps) * text.length + 0.001) : text.length;
      const shown = text.slice(0, nChars);
      const typing = kind === 'cmd' && nChars < text.length;
      let color = TINK, prefix = '', pcolor = TINK;
      if (kind === 'cmd'){ prefix = '$ '; pcolor = TACC; }
      if (kind === 'ok'){ prefix = '✓ '; pcolor = TACC; color = TACC; }
      if (kind === 'warn'){ prefix = '! '; pcolor = TAMBER; color = TAMBER; }
      const tx = x0 + 36;
      if (prefix){
        U.drawText(ctx, prefix, tx, y, { font: '22px Consolas, monospace', color: pcolor, align: 'left', alpha: g });
      }
      U.drawText(ctx, shown, tx + 34, y, { font: '22px Consolas, monospace', color, align: 'left', alpha: g });
      /* 敲入中的块光标（呼吸）+ 末行空闲光标 */
      const idleCursor = P.cursor !== false && kind === 'cmd' && i === lines.length - 1 && !typing;
      if (typing || idleCursor){
        const on = typing || Math.sin(T * 5.5) > -0.15;
        if (on){
          ctx.font = '22px Consolas, monospace';
          const wpx = ctx.measureText(prefix + shown).width;
          ctx.fillStyle = TINK;
          ctx.globalAlpha = g * 0.85;
          ctx.fillRect(tx + wpx, y - 18, 12, 22);
        }
      }
      y += lineH;
    }
    /* ---------- 持续运动源 ---------- */
    const accRGB = (function (h){
      const m = /^#?([0-9a-f]{6})$/i.exec(h || '');
      return m ? [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4, 6), 16)].join(',') : '94,211,184';
    })(TACC);
    /* ② CRT 扫描光带：teal 微光带自上而下每 4.5s 扫一遍 */
    const tEnter = P.t_in ?? sc.t_in;
    const sw2 = ((T - tEnter) % 4.5) / 4.5;
    const bandA = 0.10 * Math.sin(Math.PI * sw2);
    if (bandA > 0.004){
      const bh = 80;
      const by2 = y0 + BAR + sw2 * (h - BAR - bh - 24);
      ctx.fillStyle = `rgba(${accRGB},${bandA.toFixed(3)})`;
      ctx.fillRect(x0 + 2, by2, w - 4, bh);
    }
    /* ③ 执行进度条：轨道自首个 cmd 起填充到场景尾，条内斜纹 90px/s 流动 */
    const t0 = lines.length ? (lines[0].t_in ?? tEnter) : tEnter;
    const tEnd = P.progress_to ?? sc.t_out ?? (t0 + 10);
    const pf = U.clamp01((T - t0) / Math.max(0.1, tEnd - t0));
    const bw = w - 72, bxx = x0 + 36, byy = y0 + h - 42;
    ctx.globalAlpha = g * 0.9;
    ctx.fillStyle = TLINE;
    ctx.fillRect(bxx, byy, bw, 7);
    if (pf > 0.003){
      ctx.save();
      ctx.beginPath(); ctx.rect(bxx, byy, bw * pf, 7); ctx.clip();
      ctx.fillStyle = `rgba(${accRGB},0.16)`;
      ctx.fillRect(bxx, byy, bw * pf, 7);
      ctx.strokeStyle = TACC; ctx.lineWidth = 4.5;
      ctx.globalAlpha = g * 0.9;
      const off = (T * 90) % 16;
      ctx.beginPath();
      for (let sx = -18 + off; sx < bw * pf + 18; sx += 16){
        ctx.moveTo(bxx + sx, byy + 9);
        ctx.lineTo(bxx + sx + 10, byy - 2);
      }
      ctx.stroke();
      ctx.restore();
    }
    ctx.restore();
  }
};
