import { Heart, Search } from 'lucide-react';
import type { C, E } from '../model';
import { glyph, money } from '../presentation';
import { categoryGoals, lessonTime, levelGuides, normalizeSearch } from './coursePractice';

type Props = {
  courses: C[]; favorites: C[]; enrollments: E[];
  category: string; level: string; search: string;
  setCategory: (value: string) => void; setLevel: (value: string) => void; setSearch: (value: string) => void;
  open: (id: string) => void; learn: (course: C) => void; toggle: (course: C) => void;
  pending: boolean; failed: boolean; retry: () => void;
};

export function CourseExplorer(props: Props) {
  const { courses, category, level, search } = props;
  const categories = [...new Set(courses.map(course => course.category))];
  const levels = [...new Set(courses.map(course => course.level))];
  const query = normalizeSearch(search);
  const results = courses.flatMap(course => {
    if ((category && category !== course.category) || (level && level !== course.level)) return [];
    const matches = query ? (course.lesson_titles ?? []).filter(title => normalizeSearch(title).includes(query)) : [];
    const text = [course.title, course.description, course.category, course.instructor, categoryGoals[course.category]].join(' ');
    return !query || normalizeSearch(text).includes(query) || matches.length ? [{ course, matches }] : [];
  });
  function reset() {
    props.setCategory(''); props.setLevel(''); props.setSearch('');
  }
  return <section className="catalog explorer" id="catalog" aria-labelledby="catalog-heading">
    <div className="sectiontop"><h1 id="catalog-heading">Cursos</h1></div>
    <div className="explorer-tools">
      <label>O que você quer aprender?
        <span className="explorer-search"><Search size={17}/><input id="search" type="search" value={search}
          onChange={event => props.setSearch(event.target.value)} placeholder="Busque um curso, assunto ou aula" /></span>
      </label>
      <label>Objetivo<select aria-label="Objetivo" value={category} onChange={event => props.setCategory(event.target.value)}>
        <option value="">Todos os objetivos</option>
        {categories.map(name => <option key={name} value={name}>{categoryGoals[name] ?? name}</option>)}
      </select></label>
      <label>Nível<select aria-label="Nível" value={level} onChange={event => props.setLevel(event.target.value)}>
        <option value="">Qualquer nível</option>{levels.map(name => <option key={name}>{name}</option>)}
      </select></label>
    </div>
    {levelGuides[level] && <p className="explorer-hint">{levelGuides[level]}</p>}
    {props.pending ? <p role="status">Carregando cursos…</p> : props.failed ? <div role="alert">
      <p>Não foi possível carregar o catálogo.</p><button className="back" onClick={props.retry}>Tentar novamente</button>
    </div> : <>
      <div className="result-count"><span role="status">{results.length} {results.length === 1 ? 'curso encontrado' : 'cursos encontrados'}</span>
        {(search || category || level) && <button onClick={reset}>Limpar filtros</button>}</div>
      <div className="grid">{results.map(({ course, matches }) => {
        const saved = props.favorites.some(item => item.id === course.id);
        const active = props.enrollments.find(item => item.course_id === course.id && item.status === 'active');
        return <article className="card" key={course.id}>
          <button className={`cover ${course.cover_color}`} onClick={() => props.open(course.id)} aria-label={`Ver curso: ${course.title}`}>
            <small>{course.category}</small><b aria-hidden="true">{glyph(course.cover_color)}</b><span>{course.level}</span>
          </button>
          <div className="cardbody">
            <small className="meta">{course.lesson_count} aulas · {lessonTime(course.duration_minutes)}</small>
            <h3><button className="ctitle" onClick={() => props.open(course.id)}>{course.title}</button></h3>
            <small className="teacher">Com {course.instructor}</small>
            {matches.length > 0 && <p className="lesson-hit">Aula encontrada · {matches.join(' · ')}</p>}
            <div className="cardfoot"><b>{money(course.price)}</b>
              <button aria-label={`${saved ? 'Remover dos' : 'Salvar nos'} favoritos: ${course.title}`}
                aria-pressed={saved} onClick={() => props.toggle(course)}><Heart size={17} fill={saved ? 'currentColor' : 'none'}/></button>
            </div>
            <div className="course-actions"><button onClick={() => props.open(course.id)}>Ver curso</button>
              {active && <button onClick={() => props.learn(course)}>{active.progress_percent === 100 ? 'Revisar aulas' : 'Abrir sala de aula'}</button>}
            </div>
          </div>
        </article>;
      })}</div>
      {!results.length && <p className="empty">{courses.length ? 'Tente outro termo ou limpe os filtros para ver todos os cursos.' : 'Ainda não há cursos publicados.'}</p>}
    </>}
  </section>;
}
