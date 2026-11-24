import { useCallback, useEffect, useState } from 'react';
import useEmblaCarousel from 'embla-carousel-react';
import { ArrowLeft, ArrowRight, BookOpen, Clock3 } from 'lucide-react';
import type { C } from '../model';
import { money, glyph } from '../presentation';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';

/** Swipeable highlights from real catalog data; no autoplay or invented rankings. */
export function FeaturedCourses({ courses, onOpen }: { courses: C[]; onOpen: (id: string) => void }) {
  const [viewport, api] = useEmblaCarousel({ align: 'start', containScroll: 'trimSnaps' });
  const [canPrev, setCanPrev] = useState(false);
  const [canNext, setCanNext] = useState(false);
  const sync = useCallback(() => {
    if (!api) return;
    setCanPrev(api.canScrollPrev());
    setCanNext(api.canScrollNext());
  }, [api]);

  useEffect(() => {
    if (!api) return;
    sync();
    api.on('select', sync);
    api.on('reInit', sync);
    return () => {
      api.off('select', sync);
      api.off('reInit', sync);
    };
  }, [api, sync]);

  if (courses.length === 0) return null;
  return <section className="lp-featured" aria-labelledby="lp-featured-title">
    <div className="lp-featured__head">
      <div>
        <small className="eyebrow">seleção do catálogo</small>
        <h2 id="lp-featured-title">Encontre seu próximo <em>desafio.</em></h2>
        <p>Explore alguns cursos disponíveis e escolha por onde começar.</p>
      </div>
      {courses.length > 1 && <div className="lp-featured__controls">
        <Button type="button" variant="outline" size="icon" aria-label="Cursos anteriores" disabled={!canPrev} onClick={() => api?.scrollPrev()}><ArrowLeft size={17}/></Button>
        <Button type="button" variant="outline" size="icon" aria-label="Próximos cursos" disabled={!canNext} onClick={() => api?.scrollNext()}><ArrowRight size={17}/></Button>
      </div>}
    </div>
    <div className="lp-featured__viewport" ref={viewport}>
      <div className="lp-featured__track">
        {courses.map(course => <article className="lp-featured__slide" key={course.id}>
          <button type="button" className={`lp-featured__cover ${course.cover_color}`} onClick={() => onOpen(course.id)} aria-label={`Abrir curso ${course.title}`}>
            <span aria-hidden="true">{glyph(course.cover_color)}</span>
          </button>
          <div className="lp-featured__content">
            <Badge variant="secondary">{course.category}</Badge>
            <button type="button" className="lp-featured__title" onClick={() => onOpen(course.id)}>{course.title}</button>
            <div className="lp-featured__meta"><span><BookOpen size={14}/> {course.lesson_count} aulas</span><span><Clock3 size={14}/> {Math.round(course.duration_minutes/60)}h</span></div>
            <div className="lp-featured__foot"><strong>{money(course.price)}</strong><button type="button" aria-label={`Ver ${course.title}`} onClick={() => onOpen(course.id)}><ArrowRight size={18}/></button></div>
          </div>
        </article>)}
      </div>
    </div>
    <small className="lp-featured__hint">Arraste para ver outros cursos</small>
  </section>;
}
