/* entropy-burst — 粒子爆发积木（提炼自 demo-hook-entropy，QA 8.5/10）
 * params: {cx, cy, seed, count, t_birth:[a,b], t_burst, r_max, squash}
 * 确定性：粒子集合由 seed 派生，一次生成只读；无跨帧可变状态。 */
window.BLOCKS = window.BLOCKS || {};
window.BLOCKS['entropy-burst'] = {
  l2: (function () {
    const cache = new Map();
    function parts(seed, count) {
      const key = seed + ':' + count;
      if (cache.has(key)) return cache.get(key);
      let s = seed | 0;
      const rnd = () => {
        s = s + 0x6D2B79F5 | 0;
        let t = Math.imul(s ^ s >>> 15, 1 | s);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
      };
      const arr = Array.from({ length: count }, () => {
        const ang = rnd() * Math.PI * 2;
        const spd = 0.06 + Math.pow(rnd(), 1.8) * 0.94;
        return { ang, spd, size: rnd() * 1.8 + 1.0, jitter: (rnd() - 0.5) * 0.5, ph: rnd() * Math.PI * 2 };
      });
      cache.set(key, arr);
      return arr;
    }
    return function (ctx, T, sc, P, U) {
      const CX = (P.cx ?? 0.42) * U.W, CY = (P.cy ?? 0.40) * U.H;
      const tBirth = P.t_birth || [0.05, 0.55];
      const tBurst = P.t_burst ?? 0.60;
      const rMax = P.r_max ?? 560;
      const squash = P.squash ?? 0.78;
      const born = U.easeOutBack(U.seg(T, tBirth[0], tBirth[1]));
      if (T < tBurst + 0.3) {
        ctx.save();
        ctx.shadowColor = U.ACCENT; ctx.shadowBlur = 42;
        ctx.fillStyle = U.ACCENT;
        ctx.beginPath(); ctx.arc(CX, CY, 7 * born, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
      }
      const p = U.seg(T, tBurst, sc.t_out);
      const rMain = U.easeOutCubic(U.clamp01(p * 1.9)) * rMax;
      const rSlow = rMax + U.easeOutCubic(U.clamp01(p * 0.55 - 0.45)) * (rMax * 0.32);
      const maxR = Math.max(rMain, rSlow);
      const alphaBase = 0.95 - 0.45 * p;
      for (const pt of parts(P.seed ?? 2026, P.count ?? 260)) {
        const wob = Math.sin(pt.ph + T * 2.2) * (pt.jitter * 22 + 8);
        const drift = U.easeOutCubic(U.clamp01(p * 0.4)) * 34 * pt.spd;
        const rr = Math.max(4, maxR * pt.spd + drift) + wob;
        const x = CX + Math.cos(pt.ang) * rr;
        const y = CY + Math.sin(pt.ang) * rr * squash;
        const a = alphaBase * (0.45 + 0.55 * (1 - rr / (rMax * 1.4)));
        if (a <= 0.02) continue;
        const tail = 7 + pt.spd * 11;
        ctx.strokeStyle = U.rgba(a * 0.72);
        ctx.lineWidth = pt.size * 0.9;
        ctx.beginPath();
        ctx.moveTo(CX + Math.cos(pt.ang) * (rr - tail), CY + Math.sin(pt.ang) * (rr - tail) * squash);
        ctx.lineTo(x, y);
        ctx.stroke();
        ctx.fillStyle = U.rgba(a);
        ctx.beginPath(); ctx.arc(x, y, pt.size, 0, Math.PI * 2); ctx.fill();
        if (pt.size > 2.0) {
          ctx.fillStyle = `rgba(255,224,190,${a * 0.85})`;
          ctx.beginPath(); ctx.arc(x, y, pt.size * 0.55, 0, Math.PI * 2); ctx.fill();
        }
      }
    };
  })()
};
