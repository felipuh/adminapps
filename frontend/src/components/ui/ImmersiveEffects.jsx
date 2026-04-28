import { useEffect, useRef } from 'react';

const REVEAL_SELECTORS = [
  '.glass-card',
  '.glass-card-hover',
  '.stat-card',
  '.btn-primary',
  '.btn-secondary',
  "main [class*='rounded-xl'][class*='border'][class*='p-']",
  "main [class*='rounded-2xl'][class*='border'][class*='p-']",
].join(', ');

export default function ImmersiveEffects() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.add('immersive-ready');
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const targets = Array.from(document.querySelectorAll(REVEAL_SELECTORS));
    targets.forEach((el) => el.classList.add('ui-reveal-target'));

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('is-visible');
        });
      },
      { threshold: 0.16 }
    );

    targets.forEach((el, index) => {
      el.style.setProperty('--stagger', `${(index % 5) * 60}ms`);
      observer.observe(el);
    });

    if (prefersReducedMotion) {
      return () => observer.disconnect();
    }

    const pointer = { x: window.innerWidth * 0.5, y: window.innerHeight * 0.3 };

    const onPointerMove = (event) => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });

    const canvas = canvasRef.current;
    const context = canvas?.getContext('2d');
    let particles = [];
    let width = 0;
    let height = 0;
    let frameId = null;

    const resize = () => {
      if (!canvas || !context) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.max(24, Math.min(64, Math.floor((width * height) / 30000)));
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        r: 1 + Math.random() * 1.6,
      }));
    };

    const draw = () => {
      if (!context) return;
      context.clearRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        const dx = p.x - pointer.x;
        const dy = p.y - pointer.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 22000 && d2 > 0.001) {
          const force = 0.18 / (d2 / 9000);
          const dist = Math.sqrt(d2);
          p.vx += (dx / dist) * force;
          p.vy += (dy / dist) * force;
        }

        p.vx *= 0.992;
        p.vy *= 0.992;

        context.beginPath();
        context.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        context.fillStyle = 'rgba(0, 73, 144, 0.34)';
        context.fill();
      }

      for (let i = 0; i < particles.length; i += 1) {
        for (let j = i + 1; j < particles.length; j += 1) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 126) {
            context.strokeStyle = `rgba(59, 130, 246, ${0.14 * (1 - dist / 126)})`;
            context.lineWidth = 1;
            context.beginPath();
            context.moveTo(a.x, a.y);
            context.lineTo(b.x, b.y);
            context.stroke();
          }
        }
      }

      frameId = window.requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener('resize', resize, { passive: true });

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', resize);
      window.removeEventListener('pointermove', onPointerMove);
      if (frameId) window.cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <>
      <canvas ref={canvasRef} className="immersive-canvas" aria-hidden="true" />
    </>
  );
}
