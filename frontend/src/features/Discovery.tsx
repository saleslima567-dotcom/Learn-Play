import { useState } from 'react';
import type { C } from '../model';
import { courseGuide, lessonTime, practiceTime } from './coursePractice';
import type { TopicId } from './coursePractice';
import { ProjectPreview } from './ProjectPreview';

export const projectsUrl = '/?secao=projetos';
export const topicsUrl = '/?secao=temas';
export const weeklyUrl = '/?secao=missao';

const topics = [
  { id: 'python', name: 'Python', description: 'Use listas, condições e laços para escrever seus primeiros programas.',
    project: 'Crie uma lista de tarefas', deliverable: 'Monte uma lista que roda no terminal. Você pode adicionar tarefas e marcar as que já terminou.' },
  { id: 'git', name: 'Git e GitHub', description: 'Registre mudanças, trabalhe em uma branch e revise seu código antes de integrá-lo.',
    project: 'Abra seu primeiro pull request', deliverable: 'Adicione instruções ao README do seu repositório de treino. Depois, revise e integre a alteração com um pull request.' },
  { id: 'design', name: 'Design de interfaces', description: 'Desenhe campos, rótulos e estados que ajudam as pessoas a preencher um formulário.',
    project: 'Prototipe um formulário de inscrição', deliverable: 'Desenhe uma inscrição para uma oficina e mostre como a tela responde quando o e-mail está errado ou o envio dá certo.' },
  { id: 'comunicacao', name: 'Comunicação de equipe', description: 'Alinhe prazos, dê feedback e transforme acordos em ações com responsáveis.',
    project: 'Escreva um feedback e um plano de ação', deliverable: 'Escreva o que você diria depois de um atraso e combine duas ações para a equipe cumprir na próxima entrega.' },
] as const satisfies ReadonlyArray<{ id: TopicId; name: string; description: string; project: string; deliverable: string }>;

export function readDiscoveryPage() {
  const params = new URLSearchParams(window.location.search);
  const section = params.get('secao');
  if (section === 'projetos') return 'projects';
  if (section === 'temas') return 'topics';
  if (section === 'missao') return 'weekly';
  return 'home';
}

export function projectTitle(course: C) {
  const guide = courseGuide(course);
  return topics.find(topic => topic.id === guide?.topic)?.project;
}

const topicUrl = (id: TopicId) => `${topicsUrl}&tema=${id}`;
type Entry = { course: C; minutes: number };
type Props = {
  courses: C[];
  open: (id: string, lesson?: string) => void;
  pending: boolean;
  failed: boolean;
  retry: () => void;
};

function ProjectCard({ topic, entry, open }: { topic: typeof topics[number]; entry: Entry; open: Props['open'] }) {
  const { course, minutes } = entry;
  return <article className="project-card">
    <div className="project-card-copy">
      <a className="project-category" href={topicUrl(topic.id)}>{topic.name}</a>
      <h3>{topic.project}</h3>
      <p>{topic.deliverable}</p>
      <p className="project-metadata">{course.level} · {lessonTime(minutes)} de prática sugerida</p>
      <button className="primary" onClick={() => open(course.id)} aria-label={`Ver trilha: ${course.title}`}>Ver trilha</button>
    </div>
    <details className="project-demo">
      <summary>Experimentar a prévia</summary>
      <ProjectPreview topic={topic.id}/>
    </details>
  </article>;
}

export function Discovery({ mode, courses, open, pending, failed, retry }: Props & { mode: 'projects' | 'topics' }) {
  const [level, setLevel] = useState(() => new URLSearchParams(window.location.search).get('nivel') ?? '');
  const requestedTopic = new URLSearchParams(window.location.search).get('tema');
  const topic = mode === 'topics' ? topics.find(item => item.id === requestedTopic) : undefined;
  const entries = courses.flatMap(course => {
    const guide = courseGuide(course);
    if (!guide) return [];
    return [{ course, topic: guide.topic, minutes: practiceTime(course) }];
  });
  const projectEntries = entries.filter(entry => entry.minutes > 0);
  const levels = [...new Set(projectEntries.map(entry => entry.course.level))];
  const selectedLevel = levels.includes(level) ? level : '';
  const projects = selectedLevel ? projectEntries.filter(entry => entry.course.level === selectedLevel) : projectEntries;
  function filterProjects(value: string) {
    const url = new URL(window.location.href);
    if (value) url.searchParams.set('nivel', value);
    else url.searchParams.delete('nivel');
    window.history.replaceState(null, '', url);
    setLevel(value);
  }
  const related = entries.filter(entry => entry.topic === topic?.id);

  return <main className="dash discovery">
    <div className="discovery-intro">
      {topic && <a className="discovery-link" href={topicsUrl}>Todos os temas</a>}
      <h1>{topic?.name ?? (mode === 'projects' ? 'Projetos práticos' : 'Explore por tema')}</h1>
      <p>{topic?.description ?? (mode === 'projects' ? 'Escolha o que você quer construir e abra a trilha que ensina cada etapa.' :
        'Encontre trilhas, aulas e projetos sobre o que você quer aprender.')}</p>
      {mode === 'projects' && <div className="discovery-actions">
        <a className="discovery-link" href={topicsUrl}>Explorar por tema</a>
        <a className="discovery-link" href={weeklyUrl}>Missão da semana</a>
      </div>}
      {mode === 'topics' && !topic && <a className="discovery-link" href={projectsUrl}>Ver todos os projetos</a>}
    </div>

    {pending ? <p role="status">Carregando o catálogo…</p> : failed ? <div role="alert">
      <p>Não foi possível carregar o catálogo.</p><button className="primary" onClick={retry}>Tentar novamente</button>
    </div> : mode === 'projects' ? <section aria-labelledby="projects-heading">
      <div className="discovery-toolbar">
        <div><h2 id="projects-heading">Escolha um projeto</h2><p role="status">{projects.length} {projects.length === 1 ? 'projeto encontrado' : 'projetos encontrados'}</p></div>
        <div className="project-filter"><label htmlFor="project-level">Nível</label><select id="project-level" value={selectedLevel} onChange={event => filterProjects(event.target.value)}>
          <option value="">Qualquer nível</option>{levels.map(value => <option key={value}>{value}</option>)}
        </select></div>
      </div>
      {projects.length === 0 ? <p className="empty">Nenhum projeto disponível para este nível.</p> : <div className="discovery-grid">
        {topics.flatMap(item => projects.filter(entry => entry.topic === item.id)
          .map(entry => <ProjectCard key={entry.course.id} topic={item} entry={entry} open={open}/>))}
      </div>}
    </section> : topic ? <>
      <section className="topic-contents" aria-labelledby="topic-lessons-heading">
        <h2 id="topic-lessons-heading">Trilhas e aulas</h2>
        {related.length === 0 ? <p className="empty">Ainda não há trilhas publicadas para este tema.</p> :
          related.map(({ course }) => <article className="topic-course" key={course.id}>
            <h3>{course.title}</h3>
            <p className="project-metadata">{course.level} · {course.lesson_count} aulas · {lessonTime(course.duration_minutes)}</p>
            <button className="primary" onClick={() => open(course.id)}>Ver trilha</button>
            {Boolean(course.lesson_titles?.length) && <ul>{course.lesson_titles?.map((title, index) =>
              <li key={index}><button className="discovery-link" onClick={() => open(course.id, title)}>{title}</button></li>)}</ul>}
          </article>)}
      </section>
      {related.some(entry => entry.minutes > 0) && <section className="topic-contents" aria-labelledby="topic-projects-heading">
        <h2 id="topic-projects-heading">Projetos deste tema</h2>
        <div className="discovery-grid">{related.filter(entry => entry.minutes > 0).map(entry =>
          <ProjectCard key={entry.course.id} topic={topic} entry={entry} open={open}/>)}</div>
      </section>}
    </> : <div className="discovery-grid">{topics.map(item => <article className="project-card project-card-copy" key={item.id}>
      <h2><a className="discovery-link" href={topicUrl(item.id)}>{item.name}</a></h2>
      <p>{item.description}</p>
    </article>)}</div>}
  </main>;
}
