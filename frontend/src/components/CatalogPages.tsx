// Public course catalog/detail and student-facing information pages.
import { ArrowLeft, ArrowRight, BookOpen, Clock3, Heart, ShieldCheck } from 'lucide-react';
import type { C, E, U } from '../model';
import { glyph, lessonCount, money } from '../presentation';
import { lessonTime, levelGuides, courseGuide, practiceTime } from '../features/coursePractice';
import { hasWrittenPythonCourse, lessonModules } from '../features/pythonLessons';
import { projectTitle } from '../features/Discovery';
import { CertificateShare } from '../features/CertificateShare';
import { ProjectAchievement } from '../features/ProjectAchievement';
import { lazy, Suspense, useEffect, useRef } from 'react';

const StudyProgress = lazy(() => import('../features/StudyProgress').then(module => ({ default: module.StudyProgress })));

export function InfoPage({type,back}:{type:'about'|'help';back:()=>void}){const about=type==='about',cards=about?[['Cursos práticos','Conteúdo organizado em aulas e avaliações para acompanhar seu aprendizado.'],['Para aprender e ensinar','A plataforma demonstra áreas para alunos, professores e administração.'],['Protótipo acadêmico','Matrícula paga, player e notificações são demonstrativos; não há cobrança nem transmissão de vídeo.']]:[['Como começo um curso?','Abra um curso no catálogo, faça login ou crie sua conta e solicite a matrícula.'],['Como concluo as aulas?','Entre em “meus cursos”, abra a aula e marque-a como concluída. O progresso é atualizado pela plataforma.'],['Como obtenho o certificado?','Depois de concluir todas as aulas de um curso, abra os detalhes e use “emitir certificado”. A página permite imprimir ou salvar como PDF.'],['Há pagamentos ou vídeos reais?','Não neste protótipo. A confirmação de pagamento é simulada e o player apenas ilustra a tela da aula.']];return <main className="dash info-page"><button className="back" onClick={back}>← voltar ao catálogo</button><small className="eyebrow">{about?'sobre a LearnPlay':'central de ajuda'}</small><h1>{about?<>Aprender <em>abre caminhos.</em></>:<>Como podemos <em>ajudar?</em></>}</h1><p>{about?'Uma demonstração de plataforma de cursos online, com catálogo, matrícula, acompanhamento de aulas e avaliações.':'Respostas sobre os fluxos disponíveis e os limites desta demonstração.'}</p><div className="info-grid">{cards.map(([title,body])=><article className="info-card" key={title}><span>✦</span><h2>{title}</h2><p>{body}</p></article>)}</div><button className="primary" onClick={back}>explorar cursos　→</button></main>}
type DetailProps = {
  c: C; user: U | null; enrollment?: E; back: () => void;
  join: () => void; learn: () => void; login: () => void; start: () => void; saveProject: (url: string) => Promise<string>;
  updateCertificate: (method: 'PUT' | 'DELETE') => Promise<string | null>; selectedLesson?: string;
};

export function Detail({ c, user, enrollment, back, join, learn, login, start, saveProject, updateCertificate, selectedLesson }: DetailProps) {
  const lessons = c.lessons ?? [];
  const highlightedLesson = useRef<HTMLLIElement>(null);
  const selectedIndex = selectedLesson ? lessons.findIndex(lesson => lesson.title === selectedLesson) : -1;
  useEffect(() => {
    if (selectedIndex >= 0) highlightedLesson.current?.focus();
  }, [c.id, selectedIndex]);
  const guide = courseGuide(c);
  const practiceMinutes = practiceTime(c);
  const active = enrollment?.status === 'active' || c.enrollment_status === 'active';
  const completed = new Set(c.completed_lesson_ids);
  const delivery = projectTitle(c);
  const finished = active && lessons.length > 0 && lessons.every(lesson => completed.has(lesson.id));
  return <main className="detail">
    <button className="back" onClick={back}><ArrowLeft size={14}/> Voltar</button>
    <div className="detailgrid"><section>
      <small className="eyebrow">{c.category} · {c.level}</small><h1>{c.title}</h1><p>{c.description}</p>
      <div className="course-facts"><span>{lessonCount(c.lesson_count)}</span><span>{lessonTime(c.duration_minutes)} de aulas</span>
        {practiceMinutes > 0 && <span>Prática sugerida · cerca de {practiceMinutes} min</span>}</div>
      {levelGuides[c.level] && <p><strong>Para quem é</strong> · {levelGuides[c.level]}</p>}
      {guide && <section aria-labelledby="course-prerequisites">
        <h2 id="course-prerequisites">Pré-requisitos</h2><p>{guide.preparation}</p>
        <a className="discovery-link" href="#revisao-inicial" onClick={event => {
          event.preventDefault();
          const review = document.querySelector<HTMLDetailsElement>('#revisao-inicial');
          if (review) {
            review.open = true;
            review.querySelector('summary')?.focus();
          }
        }}>Revisar antes de começar</a>
        <details className="course-review" id="revisao-inicial">
          <summary>{guide.review.title}</summary><p>{guide.review.text}</p>
        </details>
      </section>}
      <h2>Aulas do curso</h2>
      {lessonModules(c).map(module => <div className="course-module" key={module.title ?? c.id}>
        {module.title && <h3>{module.title}</h3>}
        <ol className="course-outline" start={module.lessons.length ? lessons.indexOf(module.lessons[0]) + 1 : 1}>
          {module.lessons.map(lesson => {
            const highlighted = lessons[selectedIndex]?.id === lesson.id;
            return <li key={lesson.id} ref={highlighted ? highlightedLesson : undefined} tabIndex={highlighted ? -1 : undefined}>
              <strong>{lesson.title}</strong>
              <small>{lesson.duration_seconds < 60 ? `${lesson.duration_seconds} s` : lessonTime(Math.round(lesson.duration_seconds / 60))} de aula
                {active && completed.has(lesson.id) && ' · Concluída'}</small>
            </li>;
          })}
        </ol>
      </div>)}
      {finished && delivery && <ProjectAchievement title={delivery} saved={c.project_url} save={saveProject}/>}
    </section><aside className="course-sidebar" aria-label="Matrícula e informações do curso">
      <div className={`thumb ${c.cover_color}`} aria-hidden="true">{glyph(c.cover_color)}</div><b className="price">{money(c.price)}</b>
      <button className="primary wide" onClick={active ? learn : user ? join : login}>
        {finished ? 'Revisar aulas' : active ? 'Abrir sala de aula' : 'Matricular-se'} <ArrowRight size={16}/></button>
      {!active && c.lesson_count > 0 && (!user || user.role === 'student') && <button
        className="back first-lesson-action" onClick={start}>Começar primeira aula</button>}
      <small className="secure"><ShieldCheck size={13}/> {active ? 'Matrícula ativa' : 'Acesso após confirmação'}</small>
      <section className="course-inclusions" aria-labelledby="course-inclusions-title">
        <h2 id="course-inclusions-title">O curso inclui</h2>
        <ul>
          <li>{lessonCount(c.lesson_count)} {hasWrittenPythonCourse(c) ? (c.lesson_count === 1 ? 'escrita' : 'escritas') : (c.lesson_count === 1 ? 'demonstrativa' : 'demonstrativas')}</li>
          {c.assessment && <li>Avaliação de conhecimentos</li>}
          <li>Certificado imprimível após a conclusão</li>
        </ul>
      </section>
      {finished && <a className="primary wide certificate-link" href={`/api/v1/me/certificates/${c.id}`} target="_blank" rel="noreferrer">Emitir certificado</a>}
      {finished && <CertificateShare initialUrl={c.certificate_verification_url} update={updateCertificate}/>}
      <dl className="course-instructor">
        <dt>{c.instructor_is_demo ? 'Docente demonstrativo' : 'Instrutor'}</dt>
        <dd>{c.instructor}</dd>
      </dl>
    </aside></div>
  </main>;
}
export function Favorites({items,open,toggle,explore}:{items:C[];open:(id:string)=>void;toggle:(c:C)=>void;explore:()=>void}){return <main className="dash favorites-page"><small className="eyebrow">sua lista pessoal</small><h1>cursos <em>favoritos.</em></h1><p>guarde cursos para voltar a eles quando quiser.</p>{!items.length?<div className="emptybox"><Heart/><h2>seus favoritos começam aqui</h2><p>salve um curso no catálogo e ele aparecerá nesta lista.</p><button className="primary" onClick={explore}>explorar cursos　→</button></div>:<div className="grid">{items.map(c=><article className="card" key={c.id}><button className={`cover ${c.cover_color}`} onClick={()=>open(c.id)}><small>{c.category.toUpperCase()}</small><b>{glyph(c.cover_color)}</b><span>{c.level}</span></button><div className="cardbody"><small className="meta"><span><Clock3 size={12}/> {lessonTime(c.duration_minutes)} de aulas</span><span><BookOpen size={12}/> {lessonCount(c.lesson_count)}</span></small><button className="ctitle" onClick={()=>open(c.id)}>{c.title}</button><small className="teacher">◉　com {c.instructor}</small><div className="cardfoot"><b>{money(c.price)}</b><div className="card-actions"><button className="favorite-toggle active" title="Remover dos favoritos" aria-label="Remover dos favoritos" aria-pressed={true} onClick={()=>toggle(c)}><Heart size={15} fill="currentColor"/></button><button onClick={()=>open(c.id)} aria-label="Ver curso"><ArrowRight size={16}/></button></div></div></div></article>)}</div>}</main>}
type MineProps = { items: E[]; open: (course: C, lessonId?: string) => void; detail: (id: string) => void; explore: () => void };

export function Mine({ items, open, detail, explore }: MineProps) {
  const active = items.filter(item => item.status === 'active');
  return <main className="dash">
    <small className="eyebrow">seu espaço de aprendizagem</small><h1>continue de <em>onde parou.</em></h1>
    <p>cada aula concluída é um passo na direção dos seus objetivos.</p>
    {!active.length ? <div className="emptybox"><BookOpen/><h2>sua jornada começa aqui</h2>
      <p>explore o catálogo e escolha seu primeiro curso.</p>
      <button className="primary" onClick={explore}>explorar cursos <ArrowRight size={15}/></button></div> : <>
      <Suspense fallback={<div className="lp-progress" role="status">Carregando gráfico de progresso...</div>}>
        <StudyProgress items={active}/>
      </Suspense>
      <div className="mygrid">{active.map(item => {
        const { course, resume_lesson: lesson, progress_percent: progress } = item;
        let action = 'Começar';
        if (progress === 100) action = 'Revisar';
        else if (lesson?.saved || progress > 0) action = 'Continuar';
        return <article className="mycard" key={item.id}>
          <div className={`mycover ${course.cover_color}`}>{glyph(course.cover_color)}</div>
          <div><small>CURSO · {course.level.toUpperCase()}</small><h3>{course.title}</h3>
            <div className="progress"><i style={{width: `${progress}%`}}/></div>
            <small>{progress}% concluído · {lessonCount(course.lesson_count)}</small>
            {course.lesson_count > 0
              ? <button className="primary wide resume-action" onClick={() => open(course, lesson?.id)}>
                  {lesson ? `${action}: ${lesson.title}` : `${action} curso`}
                </button>
              : <p>Aguardando a publicação da primeira aula.</p>}
            {progress === 100 && <button className="back first-lesson-action" onClick={() => detail(course.id)}>Ver conclusão</button>}
          </div>
        </article>;
      })}</div></>}
  </main>;
}
