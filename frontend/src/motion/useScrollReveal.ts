import { useEffect } from 'react';

/**
 * Progressive content reveal inspired by React Bits AnimatedContent.
 * Uses native IntersectionObserver and respects reduced-motion preferences.
 * Content remains visible if the browser does not support the observer.
 */
export function useScrollReveal(refreshKey: string) {
  useEffect(() => {
    const elements = Array.from(document.querySelectorAll<HTMLElement>('[data-reveal]'));
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || !('IntersectionObserver' in window)) {
      elements.forEach(element => element.classList.add('is-revealed'));
      return;
    }

    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const element = entry.target as HTMLElement;
        element.classList.add('is-revealed');
        observer.unobserve(element);
      }
    }, { rootMargin: '0px 0px -36px 0px', threshold: 0.08 });

    for (const element of elements) {
      if (element.classList.contains('is-revealed')) continue;
      // Only add the hidden state once observation is available.
      element.classList.add('motion-observed');
      observer.observe(element);
    }
    return () => observer.disconnect();
  }, [refreshKey]);
}
