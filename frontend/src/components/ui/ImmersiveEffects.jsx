import { useEffect } from 'react';

const REVEAL_SELECTORS = [
  '.glass-card',
  '.glass-card-hover',
  '.stat-card',
  '.enterprise-card',
  "main [class*='rounded-xl'][class*='border'][class*='p-']",
].join(', ');

export default function ImmersiveEffects() {
  useEffect(() => {
    const root = document.documentElement;
    root.classList.add('immersive-ready');

    const targets = Array.from(document.querySelectorAll(REVEAL_SELECTORS));
    targets.forEach((el) => el.classList.add('ui-reveal-target'));

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('is-visible');
        });
      },
      { threshold: 0.12 }
    );

    targets.forEach((el, index) => {
      el.style.setProperty('--stagger', `${(index % 4) * 35}ms`);
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return null;
}
