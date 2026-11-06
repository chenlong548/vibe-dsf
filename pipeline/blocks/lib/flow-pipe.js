/* flow-pipe — 节点链管道积木（论文 Figure 1 式通信模型：源→发射机→信道→接收机→目的地）
 * params: {cx, cy, w, h, area_pct, nodes:[{label, sub}], node_w, node_h,
 *          t_nodes:[a,b] 节点逐个生长窗口, t_flow:[a,b] 粒子流动窗口}
 * 视觉：节点方块逐个生长（生长式进场）→ 链路连线 → accent 粒子沿链向右流动。
 * 粒子流动是持续运动源（QA 密度友好），节点标签 ink，sub 标注 gray。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['flow-pipe'] = {
  l2: function (ctx, T, sc, P, U) {
    const w = P.w ?? 1500, h = P.h ?? 360;
    const cx = (P.cx ?? 0.42) * U.W, cy = (P.cy ?? 0.44) * U.H;
    const nodes = P.nodes || [];
    const n = Math.max(2, nodes.length);
    const tn = P.t_nodes || [0.4, 2.4];
    const x0 = cx - w / 2, x1 = cx + w / 2;
    const y0 = cy - h / 2, y1 = cy + h / 2;
    const nw = P.node_w ?? Math.min(170, w / n - 60);
    const nh = P.node_h ?? 120;
    const gap = (w - n * nw) / (n - 1);
    const centers = [];
    for (let i = 0; i < n; i++) centers.push(x0 + nw / 2 + i * (nw + gap));
    for (let i = 0; i < n; i++) {
      const g = U.easeOutBack(U.seg(T, tn[0] + (tn[1] - tn[0]) * i / n, tn[0] + (tn[1] - tn[0]) * (i + 0.6) / n));
      if (g <= 0) continue;
      const gx = centers[i], gy = (y0 + y1) / 2;
      ctx.save();
      ctx.translate(gx, gy);
      ctx.scale(g, g);
      const isAccent = i === Math.min(2, n - 1);
      ctx.fillStyle = isAccent ? U.rgba(0.10) : U.rgbaInk(0.05);
      ctx.strokeStyle = isAccent ? U.ACCENT : U.rgbaInk(0.45);
      ctx.lineWidth = 2;
      ctx.fillRect(-nw / 2, -nh / 2, nw, nh);
      ctx.strokeRect(-nw / 2, -nh / 2, nw, nh);
      ctx.restore();
      if (nodes[i] && nodes[i].label) {
        U.drawText(ctx, nodes[i].label, gx, gy - 8, { font: '24px "Microsoft YaHei"', color: U.INK, alpha: g });
      }
      if (nodes[i] && nodes[i].sub) {
        U.drawText(ctx, nodes[i].sub, gx, gy + nh / 2 + 34, { font: '20px "Microsoft YaHei"', color: U.GRAY, alpha: U.seg(T, tn[0] + (tn[1] - tn[0]) * i / n + 0.2, tn[0] + (tn[1] - tn[0]) * (i + 0.6) / n + 0.5) });
      }
    }
    for (let i = 0; i < n - 1; i++) {
      const g = U.easeOutCubic(U.seg(T, tn[0] + (tn[1] - tn[0]) * (i + 0.5) / n, tn[0] + (tn[1] - tn[0]) * (i + 1) / n));
      if (g <= 0) continue;
      const ax = centers[i] + nw / 2, bx = centers[i + 1] - nw / 2;
      const my = (y0 + y1) / 2;
      ctx.strokeStyle = U.rgbaInk(0.35 * g);
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(ax, my); ctx.lineTo(ax + (bx - ax) * g, my); ctx.stroke();
    }
    const tf = P.t_flow || [tn[1], sc.t_out];
    if (T >= tf[0]) {
      const per = 26;
      const speed = (x1 - x0) / 6.5;
      for (let i = 0; i < per; i++) {
        const seedPos = (i * 137 + Math.floor(T * speed * 30)) % (w + 200);
        const px = x0 - 100 + seedPos;
        const py = (y0 + y1) / 2 + 26 * Math.sin(i * 2.4 + T * 1.5);
        const pa = 0.30 + 0.30 * Math.sin(T * 8 + i * 1.9);
        if (pa <= 0.08) continue;
        ctx.fillStyle = U.rgba(pa);
        ctx.beginPath(); ctx.arc(px, py, 2.2 + (i % 3), 0, Math.PI * 2); ctx.fill();
      }
    }
  }
};
