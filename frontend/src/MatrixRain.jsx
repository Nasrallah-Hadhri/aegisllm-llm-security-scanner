import React, { useEffect, useRef } from "react";

// Pluie « matrix » discrète en fond (vibe hacker). Désactivée si prefers-reduced-motion.
export default function MatrixRain() {
  const ref = useRef(null);
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const cv = ref.current;
    const ctx = cv.getContext("2d");
    const chars = "01<>/\\|{}[]#$%&*+=?АБ01アイウエオカキクケコサシ0123456789ABCDEF".split("");
    const fontSize = 14;
    let W, H, cols, drops, raf;

    const resize = () => {
      W = cv.width = window.innerWidth;
      H = cv.height = window.innerHeight;
      cols = Math.floor(W / fontSize);
      drops = Array.from({ length: cols }, () => Math.random() * (H / fontSize));
    };
    resize();
    window.addEventListener("resize", resize);

    const draw = () => {
      ctx.fillStyle = "rgba(7,11,9,0.10)";
      ctx.fillRect(0, 0, W, H);
      ctx.font = `${fontSize}px monospace`;
      for (let i = 0; i < cols; i++) {
        const ch = chars[(Math.random() * chars.length) | 0];
        const x = i * fontSize;
        const y = drops[i] * fontSize;
        // tête plus brillante que la traîne
        ctx.fillStyle = Math.random() > 0.97 ? "#aaffd8" : "#00ff9c";
        ctx.fillText(ch, x, y);
        if (y > H && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
      raf = requestAnimationFrame(draw);
    };

    if (reduce) {
      ctx.fillStyle = "#070b09";
      ctx.fillRect(0, 0, cv.width, cv.height);
    } else {
      draw();
    }
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", resize); };
  }, []);

  return <canvas ref={ref} className="matrix" aria-hidden="true" />;
}
