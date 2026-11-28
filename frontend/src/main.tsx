// TypeScript / frontend/src/main.tsx / React 19 + Vite 8 / LearnPlay web client
import React,{useEffect,useState}from'react';import{createRoot}from'react-dom/client';import{ArrowRight,GraduationCap,LogOut,Moon,Play,Search,Sun,X}from'lucide-react';import { Detail, Favorites, InfoPage, Mine } from './components/CatalogPages';
import { Dialog } from 'radix-ui';
import { WeeklyMission } from './features/WeeklyMission';
import type { U, L, A, C, E, AssessmentResult } from './model';
import { PaymentCheckout, readPaymentEnrollment } from './features/PaymentCheckout';
import { CourseExplorer } from './features/CourseExplorer';
import { Discovery, readDiscoveryPage } from './features/Discovery';
import { hasWrittenPythonCourse, lessonModules, pythonLessonFor } from './features/pythonLessons';
import { PythonMaterials, PythonPractice } from './features/PythonPractice';
import type { PracticeAnswers } from './features/PythonPractice';
import { courseGuide } from './features/coursePractice';
import { useScrollReveal } from './motion/useScrollReveal';
import { motion, useReducedMotion } from 'motion/react';
import { Toaster, toast } from 'sonner';
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import'./index.css';import'./features/learning-experience.css';import'./style.css';import'./design-refresh.css';import'./motion.css';
import './features/trails.css';
const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: 1, refetchOnWindowFocus: false } } });
let csrf='';
async function api<T>(path:string,init:RequestInit={},csrfRetry=false):Promise<T>{const h=new Headers(init.headers);if(init.body)h.set('Content-Type','application/json');const mutating=['POST','PUT','PATCH','DELETE'].includes((init.method||'GET').toUpperCase());if(mutating){if(!csrf)csrf=(await api<{csrf_token:string}>('/api/v1/auth/csrf')).csrf_token;h.set('X-CSRF-Token',csrf)}const r=await fetch(path,{...init,headers:h,credentials:'include'});if(r.status===204)return undefined as T;const d=await r.json().catch(()=>({}));if(!r.ok&&r.status===403&&mutating&&!csrfRetry&&/csrf/i.test(d.detail||'')){csrf='';csrf=(await api<{csrf_token:string}>('/api/v1/auth/csrf')).csrf_token;return api<T>(path,init,true)}if(!r.ok)throw Error(d.detail||`Erro ${r.status}`);return d}
const initialView = () => readPaymentEnrollment() ? 'payment' : readDiscoveryPage();
const cats=['Todos','Programação','Design','Tecnologia','Negócios'];
function App(){const queryClient = useQueryClient();const[user,SUser]=useState<U|null>(null),[enrollments,SE]=useState<E[]>([]),[favorites,SFav]=useState<C[]>([]),[course,SActive]=useState<C|null>(null),[cat,SCat]=useState(''),[level,setLevel]=useState(''),[search,SS]=useState(''),[view,setView]=useState<string>(initialView),[selectedLesson,setSelectedLesson]=useState<string>(),[modal,SM]=useState(''),[loading,SL]=useState(true),[drawer,SD]=useState(false),[theme,STheme]=useState<'light'|'dark'>(()=>{try{return localStorage.getItem('learnplay-theme')==='dark'?'dark':'light'}catch{return'light'}});useEffect(()=>{document.documentElement.dataset.theme=theme;document.documentElement.classList.toggle('dark',theme==='dark');document.documentElement.style.colorScheme=theme;try{localStorage.setItem('learnplay-theme',theme)}catch{}},[theme]);const note=(message:string)=>toast(message,{duration:4500});const reduceMotion=useReducedMotion();
function SV(next: string) {
  if (next !== 'payment' && readPaymentEnrollment()) {
    const url = new URL(window.location.href);
    url.search = '';
    window.history.pushState(null, '', url);
  }
  if (readDiscoveryPage() !== 'home' && next !== 'topics' && next !== 'projects' && next !== 'weekly') {
    const url = new URL(window.location.href);
    url.searchParams.delete('secao');
    url.searchParams.delete('tema');
    url.searchParams.delete('nivel');
    window.history.pushState(null, '', url);
  }
  setView(next);
}
const menuToggle = React.useRef<HTMLButtonElement>(null);

function goToPage(next: string) {
  const focusPage = drawer;
  SD(false);
  SActive(null);
  SV(next);
  window.scrollTo({ top: 0, behavior: 'instant' });
  if (focusPage) {
    requestAnimationFrame(() => {
      const heading = document.querySelector<HTMLHeadingElement>('main h1');
      if (!heading) return;
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    });
  }
}

function openPayment(enrollmentId: string) {
  const url = new URL(window.location.href);
  url.search = new URLSearchParams({ pagamento: enrollmentId }).toString();
  window.history.pushState(null, '', url);
  goToPage('payment');
}

function scrollToCourses() {
  const heading = document.getElementById('catalog-heading');
  heading?.focus({ preventScroll: true });
  heading?.scrollIntoView({ block: 'start', behavior: reduceMotion ? 'instant' : 'smooth' });
}

useEffect(() => {
  const restore = () => { SActive(null); SD(false); setView(initialView()); };
  window.addEventListener('popstate', restore);
  return () => window.removeEventListener('popstate', restore);
}, []);
const courseQuery=useQuery({queryKey:['catalog','courses',user?.id??'public'],queryFn:async()=> (await api<{items:C[]}>('/api/v1/courses')).items});const courses=courseQuery.data??[];
async function refresh(){await queryClient.invalidateQueries({queryKey:['catalog','courses']});if(user)SE((await api<{items:E[]}>('/api/v1/me/enrollments')).items)}useEffect(()=>{void(async()=>{try{csrf=(await api<{csrf_token:string}>('/api/v1/auth/csrf')).csrf_token;const me=await api<{user:U}>('/api/v1/me').catch(()=>null);if(me)SUser(me.user);await queryClient.invalidateQueries({queryKey:['catalog','courses']})}catch(e){note((e as Error).message)}finally{SL(false)}})()},[]);useEffect(()=>{if(user){void api<{items:E[]}>('/api/v1/me/enrollments').then(x=>SE(x.items)).catch(e=>note(e.message));if(user.role==='student')void api<{items:C[]}>('/api/v1/me/favorites').then(x=>SFav(x.items)).catch(e=>note(e.message));else SFav([])}else{SE([]);SFav([])}},[user]);
const pendingResume = React.useRef(Promise.resolve());
const startAfterAuth = React.useRef<C | null>(null);
const enrolling = React.useRef(false);
const rememberLesson = React.useCallback((courseId: string, lesson: L) => {
  SE(items => items.map(item => item.course_id === courseId
    ? {...item, resume_lesson: {id: lesson.id, title: lesson.title, saved: true}} : item));
  pendingResume.current = pendingResume.current.then(async () => {
    await api(`/api/v1/me/resume/${courseId}`, {method: 'PUT', body: JSON.stringify({lesson_id: lesson.id})});
  }).catch(() => { toast('Não foi possível salvar a aula para a próxima sessão.'); });
}, []);
useScrollReveal(`${loading}:${view}:${course?.id ?? ''}`);
async function open(id:string, lesson?:string){try{const detail=await api<C>(`/api/v1/courses/${id}`);
  setSelectedLesson(lesson);SActive(detail);if(view==='learn')SV('home');scrollTo(0,0)}catch(e){note((e as Error).message)}}async function auth(email: string, password: string, name?: string) {
  const d = await api<{user: U; csrf_token: string}>(name ? '/api/v1/auth/register' : '/api/v1/auth/login', {
    method: 'POST', body: JSON.stringify({email, password, ...(name ? {name} : {})}),
  });
  csrf = d.csrf_token;
  const pending = startAfterAuth.current;
  startAfterAuth.current = null;
  SUser(d.user);
  SD(false);
  SM('');
  note(`bem-vindo, ${d.user.name.split(' ')[0]}!`);
  if (pending && d.user.role === 'student') await join(pending, true);
  else if (pending) note('Entre com uma conta de aluno para iniciar o curso.');
}

function startCourse(c: C) {
  if (user) {
    void join(c, true);
  } else {
    startAfterAuth.current = c;
    SM('login');
  }
}

async function join(c: C, start = false) {
  if (enrolling.current) return;
  enrolling.current = true;
  try {
    const enrollment = await api<E>(`/api/v1/courses/${c.id}/enrollments`, {
      method: 'POST', headers: {'X-Idempotency-Key': crypto.randomUUID()},
    });
    if (enrollment.status !== 'active') {
      openPayment(enrollment.id);
      SE(items => [enrollment, ...items.filter(item => item.id !== enrollment.id)]);
      return;
    }
    await refresh();
    if (start) {
      const current = await api<{items: E[]}>('/api/v1/me/enrollments');
      SE(current.items);
      await learn(c, c.lessons?.[0]?.id);
    } else {
      SActive(await api<C>(`/api/v1/courses/${c.id}`));
    }
    note('matrícula confirmada.');
  } catch (error) {
    note((error as Error).message);
  } finally {
    enrolling.current = false;
  }
}
async function learn(c:C, requestedLessonId?:string){try{await pendingResume.current;const d=await api<{items:{lessons:L[]}[];progress_percent:number}>(`/api/v1/courses/${c.id}/lessons`),detail=await api<C>(`/api/v1/courses/${c.id}`),resume=await api<{lesson_id:string|null}>(`/api/v1/me/resume/${c.id}`);detail.lessons=d.items.flatMap(x=>x.lessons);detail.resume_lesson_id=requestedLessonId ?? resume.lesson_id;SActive(detail);SV('learn')}catch(e){note((e as Error).message)}}async function toggleFavorite(c:C){if(!user){SM('login');note('entre para salvar cursos favoritos.');return}if(user.role!=='student'){note('favoritos estão disponíveis para alunos.');return}const exists=favorites.some(x=>x.id===c.id);try{if(exists){await api(`/api/v1/me/favorites/${c.id}`,{method:'DELETE'});SFav(favorites.filter(x=>x.id!==c.id));note('curso removido dos favoritos.')}else{await api(`/api/v1/me/favorites/${c.id}`,{method:'POST'});SFav([c,...favorites]);note('curso salvo nos favoritos.')}}catch(e){note((e as Error).message)}}async function logout(){await pendingResume.current;await api('/api/v1/auth/logout',{method:'POST'});csrf='';SUser(null);SFav([]);SActive(null);SV('home');note('sessão encerrada')}
const paymentEnrollmentId = view === 'payment' ? readPaymentEnrollment() : null;
return <div className="shell"><header onKeyDown={event => {
  if (event.key === 'Escape' && drawer && !modal) {
    SD(false);
    menuToggle.current?.focus();
  }
}}>
<button className="brand" onClick={() => goToPage('home')}><i><GraduationCap size={19}/></i>LearnPlay</button>
<nav id="primary-navigation" aria-label="Navegação principal" className={drawer ? 'show' : ''}>
  <button aria-current={view === 'home' && !course ? 'page' : undefined} onClick={() => goToPage('home')}>Explorar</button>
  {user && <button aria-current={view === 'mine' && !course ? 'page' : undefined} onClick={() => goToPage('mine')}>Meus cursos</button>}
  {user?.role === 'student' && <button aria-current={view === 'favorites' ? 'page' : undefined} onClick={() => goToPage('favorites')}>Favoritos</button>}
  <button aria-current={view === 'about' ? 'page' : undefined} onClick={() => goToPage('about')}>Sobre</button>
  <button aria-current={view === 'help' ? 'page' : undefined} onClick={() => goToPage('help')}>Ajuda</button>
  {!user && <button className="mobile-login" onClick={() => SM('login')}>Entrar</button>}
  {user?.role === 'instructor' && <button aria-current={view === 'teacher' ? 'page' : undefined} onClick={() => goToPage('teacher')}>Ensinar</button>}
  {user?.role === 'admin' && <button aria-current={view === 'admin' ? 'page' : undefined} onClick={() => goToPage('admin')}>Administração</button>}
</nav><div className="headright"><button className="icon theme-toggle" onClick={()=>STheme(theme==='dark'?'light':'dark')} title={theme==='dark'?'Ativar tema claro':'Ativar tema escuro'} aria-label={theme==='dark'?'Ativar tema claro':'Ativar tema escuro'}>{theme==='dark'?<Sun size={16}/>:<Moon size={16}/>}</button><button className="searchicon" aria-label="Buscar cursos" onClick={()=>{SActive(null);SV('home');requestAnimationFrame(()=>document.getElementById('search')?.focus())}}><Search size={18}/></button>{user?<><span className="hello">{user.name.split(' ')[0]}</span><button className="icon" onClick={()=>void logout()} title="sair"><LogOut size={16}/></button></>:<><button className="plain" onClick={()=>SM('login')}>entrar</button><button className="primary tiny" onClick={()=>SM('register')}>criar conta <ArrowRight size={14}/></button></>}</div><button className="hamb" ref={menuToggle} type="button" aria-label={drawer?'Fechar menu':'Abrir menu'} aria-expanded={drawer} aria-controls="primary-navigation" onClick={()=>SD(!drawer)}>☰</button></header><Toaster theme={theme} position="top-right" closeButton visibleToasts={3} duration={4500} toastOptions={{className:'learnplay-toast'}} />
<motion.div className="page-transition" key={`${course?.id??'none'}:${view}`} initial={reduceMotion?false:{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:reduceMotion?0:0.28,ease:'easeOut'}}>{loading?<div className="loading" role="status" aria-live="polite">carregando LearnPlay...</div>:course&&view==='learn'?<Learn course={course} remember={rememberLesson} back={()=>{SActive(null);SV('mine')}} done={async l=>{try{await api(`/api/v1/lessons/${l.id}/completion`,{method:'PUT'});await learn(course);await refresh();note('aula concluída. progresso atualizado.')}catch(e){note((e as Error).message)}}} quiz={(assessment, answers) => api<AssessmentResult>(
  `/api/v1/courses/${course.id}/assessments/${assessment.id}/attempts`,
  { method: 'POST', body: JSON.stringify({ answers }) },
)}/>:course?<Detail c={course} selectedLesson={selectedLesson} user={user} enrollment={enrollments.find(e=>e.course_id===course.id)} back={()=>SActive(null)} join={()=>void join(course)} learn={()=>void learn(course)} login={()=>SM('login')} start={()=>startCourse(course)}
  updateCertificate={async method => {
    const data = await api<{verification_url:string} | undefined>(`/api/v1/me/certificates/${course.id}/share`, {method});
    return data?.verification_url ?? null;
  }}
  saveProject={async url => (await api<{project_url:string}>(`/api/v1/me/projects/${course.id}`, {
    method: 'PUT', body: JSON.stringify({url}),
  })).project_url}/> :paymentEnrollmentId ? (user?.role === 'student'
  ? <PaymentCheckout key={`${user.id}:${paymentEnrollmentId}`} enrollmentId={paymentEnrollmentId} userId={user.id}
      api={api} back={()=>goToPage('mine')} approved={refresh}/>
  : <main className="payment-page"><h1>Pagamento de teste</h1><p>Entre com uma conta de aluno para acessar sua matrícula.</p>
      {!user && <button className="primary" onClick={()=>SM('login')}>Entrar</button>}</main>)
  :view==='projects'||view==='topics'?<Discovery mode={view} courses={courses} open={open}
  pending={courseQuery.isPending} failed={courseQuery.isError} retry={()=>void courseQuery.refetch()}/>:view==='weekly'?<WeeklyMission/>:view==='mine'?<Mine items={enrollments} open={learn} detail={open} explore={()=>SV('home')} payment={openPayment}/>:view==='favorites'?<Favorites items={favorites} open={open} toggle={toggleFavorite} explore={()=>SV('home')}/>:view==='teacher'?<Teacher note={note}/>:view==='about'?<InfoPage type="about" back={()=>SV('home')}/>:view==='help'?<InfoPage type="help" back={()=>SV('home')}/>:view==='admin'?<Admin note={note} currentUserId={user?.id||''}/>:<><main>
<section className="hero explore-intro" aria-labelledby="explore-title">
  <div>
    <h1 id="explore-title">Seu próximo passo <em>começa aqui.</em></h1>
    <p>Aprenda no seu ritmo. Encontre cursos por assunto ou nível e veja o que você vai estudar em cada um.</p>
    <button className="primary" onClick={scrollToCourses}>Explorar cursos <ArrowRight size={16}/></button>
  </div>
</section>
<CourseExplorer courses={courses} favorites={favorites} enrollments={enrollments} category={cat} level={level} search={search}
  setCategory={SCat} setLevel={setLevel} setSearch={SS} open={open} learn={learn} toggle={toggleFavorite}
  pending={courseQuery.isPending} failed={courseQuery.isError} retry={()=>void courseQuery.refetch()}/>
<section className="banner" data-reveal><i><GraduationCap/></i><div><b>ensina algo que você domina?</b><small>compartilhe sua experiência com quem quer aprender.</small></div><button onClick={()=>user?.role==='instructor'?SV('teacher'):SM('register')}>conheça a área de ensino　→</button></section></main><footer><b className="footbrand">▣ LearnPlay</b><small>© 2026 LearnPlay · aprender abre caminhos</small><div className="footer-links"><button onClick={()=>{SActive(null);SV('home')}}>cursos</button><button onClick={()=>SV('about')}>sobre</button><button onClick={()=>SV('help')}>ajuda</button></div></footer></>}</motion.div>{modal&&<Auth mode={modal} close={()=>{startAfterAuth.current=null;SM('')}} submit={auth} setMode={SM}/>}</div>}
type LearnProps = {
  course: C; remember: (courseId: string, lesson: L) => void;
  back: () => void; done: (lesson: L) => void;
  quiz: (assessment: A, answers: Record<string, number>) => Promise<AssessmentResult>;
};

function Learn({ course, remember, back, done, quiz }: LearnProps) {
  const lessons = course.lessons ?? [];
  const assessment = course.assessment;
  const [selectedId, selectLesson] = useState(() => course.resume_lesson_id ?? lessons.find(lesson => !lesson.completed)?.id);
  const [activity, setActivity] = useState<'quiz' | 'practice'>();
  const [reviewing, setReviewing] = useState<'quiz' | 'practice'>();
  const [practiceAnswers, setPracticeAnswers] = useState<PracticeAnswers>({});
  const [checked, setChecked] = useState<PracticeAnswers>({});
  const showQuiz = activity === 'quiz';
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<AssessmentResult>();
  const [quizError, setQuizError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const selected = lessons.find(lesson => lesson.id === selectedId) ?? lessons.find(lesson => !lesson.completed) ?? lessons[0];
  const mission = selected ? courseGuide(course)?.steps[selected.title] : undefined;
  const written = selected ? pythonLessonFor(course, selected.title) : undefined;
  useEffect(() => {
    if (selected && !reviewing) remember(course.id, selected);
  }, [course.id, selected?.id, remember, reviewing]);
  const focusHeading = () => requestAnimationFrame(() => document.getElementById('lesson-content-title')?.focus());
  function openActivity(next: 'quiz' | 'practice') {
    setActivity(next);
    focusHeading();
  }
  function reviewLesson(lesson: L, from: 'quiz' | 'practice') {
    selectLesson(lesson.id);
    setReviewing(from);
    setActivity(undefined);
    focusHeading();
  }
  async function submitQuiz(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assessment || submitting) return;
    setSubmitting(true);
    setQuizError('');
    try { setResult(await quiz(assessment, answers)); }
    catch (error) { setQuizError((error as Error).message); }
    finally { setSubmitting(false); }
  }
  return <main className="learning">
    <div className="learnhead"><button className="back" onClick={back}>← meus cursos</button>　{course.title}</div>
    <div className="learnlayout"><aside><b>CONTEÚDO DO CURSO</b>
      {lessonModules(course).map(module => <div className={module.title ? 'lesson-module' : undefined} key={module.title ?? course.id}>
        {module.title && <div className="lesson-module-heading">
          <h3>{module.title}</h3>
          <small>{module.lessons.filter(lesson => lesson.completed).length} de {module.lessons.length} {module.lessons.length === 1 ? 'concluída' : 'concluídas'}</small>
        </div>}
        {module.lessons.map(lesson => <button className={selected?.id === lesson.id && !activity ? 'chosen' : ''}
          aria-current={selected?.id === lesson.id && !activity ? 'step' : undefined}
          key={lesson.id} onClick={() => { selectLesson(lesson.id); setReviewing(undefined); setActivity(undefined); }}>
          {lesson.completed ? '✓' : String(lessons.indexOf(lesson) + 1).padStart(2, '0')}　{lesson.title}
        </button>)}
      </div>)}
      {hasWrittenPythonCourse(course) && <button onClick={() => openActivity('practice')}>Praticar Python</button>}
      {assessment && <button onClick={() => openActivity('quiz')}>◎　{assessment.title}</button>}
    </aside><section>
      {activity === 'practice' ? <PythonPractice answers={practiceAnswers} checked={checked}
        choose={(id, option) => {
          setPracticeAnswers(current => ({ ...current, [id]: option }));
          setChecked(current => {
            const next = { ...current };
            delete next[id];
            return next;
          });
        }}
        check={() => setChecked(practiceAnswers)}
        review={title => {
          const lesson = lessons.find(item => item.title === title);
          if (lesson) reviewLesson(lesson, 'practice');
        }}/> : showQuiz && assessment ? <form className="quiz" onSubmit={submitQuiz}>
        <h2 id="lesson-content-title" tabIndex={-1}>{assessment.title}</h2>
        {result && <p role="status">Nota: {result.score}%. {result.passed ? 'Avaliação aprovada.' : 'Revise suas respostas.'} Tentativas restantes: {result.attempts_remaining}.</p>}
        {assessment.questions.map((question, index) => {
          const needsReview = result?.incorrect_question_ids.includes(question.id);
          const related = question.prompt === 'Qual é uma boa forma de consolidar o aprendizado?' ? lessons.at(-1) : lessons[0];
          return <fieldset key={question.id}><legend>{index + 1}. {question.prompt}</legend>
            {question.options.map((option, position) => <label key={position}><input type="radio"
              name={question.id} checked={answers[question.id] === position} disabled={submitting || result?.attempts_remaining === 0}
              onChange={() => setAnswers({...answers, [question.id]: position})}/>{option}</label>)}
            {needsReview && related && <button type="button" className="discovery-link" onClick={() => {
              reviewLesson(related, 'quiz');
            }}>Revisar aula: {related.title}</button>}
          </fieldset>;
        })}
        {quizError && <p role="alert">{quizError}</p>}
        <button className="primary" disabled={submitting || result?.attempts_remaining === 0
          || Object.keys(answers).length !== assessment.questions.length}>{submitting ? 'Enviando…' : 'Enviar respostas'}</button>
      </form> : selected && <>
        {reviewing && <button className="discovery-link" onClick={() => openActivity(reviewing)}>
          {reviewing === 'practice' ? 'Voltar à prática' : 'Voltar à avaliação'}</button>}
        {!written && <div className="video"><Play aria-hidden="true" fill="currentColor"/><small>AULA DEMONSTRATIVA · PLAYER DE VÍDEO</small></div>}
        <small className="eyebrow">aula {String(lessons.indexOf(selected) + 1).padStart(2, '0')}</small>
        <h2 id="lesson-content-title" tabIndex={-1}>{selected.title}</h2>
        {written ? <div className="written-lesson">
          {written.explanation.map(paragraph => <p key={paragraph}>{paragraph}</p>)}
          <h3>Exemplo em Python</h3>
          <pre><code>{written.example}</code></pre>
          <p><strong>Resultado esperado.</strong> {written.expected}</p>
          <div className="lesson-mission">
            <h3>Agora pratique</h3><p>{written.exercise}</p><p><strong>Como conferir.</strong> {written.check}</p>
          </div>
          <PythonMaterials projectLesson={selected.title === 'Projeto: lista de tarefas'}/>
        </div> : <p>{selected.description}</p>}
        {mission && !written && <div className="lesson-mission"><small className="eyebrow">Missão prática · cerca de {mission.minutes} min</small>
          <h3>{mission.mission}</h3><p><strong>Como conferir</strong> · {mission.check}</p></div>}
        <button className="primary" disabled={selected.completed} onClick={() => done(selected)}>
          {selected.completed ? '✓ aula concluída' : 'marcar como concluída　✓'}</button>
      </>}
    </section></div>
  </main>;
}

function Teacher({note}:{note:(s:string)=>void}){const queryClient=useQueryClient();const[items,SI]=useState<C[]>([]),[f,SF]=useState({title:'',description:'',category:'Programação',level:'Iniciante',price:'0'});useEffect(()=>{void api<{items:C[]}>('/api/v1/instructor/courses').then(x=>SI(x.items)).catch(e=>note(e.message))},[]);async function create(e:React.FormEvent){e.preventDefault();try{const r=await api<{course:C}>('/api/v1/instructor/courses',{method:'POST',body:JSON.stringify({...f,price:Number(f.price)})});SI([r.course,...items]);SF({...f,title:'',description:''});note('rascunho criado. inclua e publique ao menos uma aula para publicar o curso.')}catch(x){note((x as Error).message)}}async function addLesson(c:C){const title=prompt('Título da nova aula');if(!title)return;try{await api(`/api/v1/instructor/courses/${c.id}/lessons`,{method:'POST',body:JSON.stringify({title,description:'Aula criada pelo professor',duration_seconds:600,status:'published'})});note('aula adicionada e publicada.');SI((await api<{items:C[]}>('/api/v1/instructor/courses')).items)}catch(x){note((x as Error).message)}}async function saveQuiz(c:C){try{await api(`/api/v1/instructor/courses/${c.id}/assessment`,{method:'PUT',body:JSON.stringify({title:'Avaliação do curso',passing_score:70,max_attempts:3,questions:[{prompt:'Qual a melhor maneira de consolidar o conteúdo?',options:['Praticar em um projeto','Pular as aulas'],correct_option:0}]})});note('avaliação demonstrativa configurada.')}catch(x){note((x as Error).message)}}async function publish(c:C){try{await api(`/api/v1/instructor/courses/${c.id}`,{method:'PATCH',body:JSON.stringify({status:'published'})});note('curso publicado no catálogo.');await queryClient.invalidateQueries({queryKey:['catalog','courses']});SI((await api<{items:C[]}>('/api/v1/instructor/courses')).items)}catch(x){note((x as Error).message)}}return <main className="dash"><small className="eyebrow">painel do professor</small><h1>compartilhe o que <em>você sabe.</em></h1><div className="panels"><form className="panel" onSubmit={create}><h2>novo curso</h2><label>título<input required minLength={4} value={f.title} onChange={e=>SF({...f,title:e.target.value})}/></label><label>descrição<textarea required value={f.description} onChange={e=>SF({...f,description:e.target.value})}/></label><label>categoria<select value={f.category} onChange={e=>SF({...f,category:e.target.value})}>{cats.slice(1).map(x=><option key={x}>{x}</option>)}</select></label><label>nível<select value={f.level} onChange={e=>SF({...f,level:e.target.value})}>{['Iniciante','Intermediário','Avançado','Todos os níveis'].map(x=><option key={x}>{x}</option>)}</select></label><label>preço em reais<input type="number" min="0" step=".01" value={f.price} onChange={e=>SF({...f,price:e.target.value})}/></label><button className="primary wide">criar rascunho →</button></form><section className="panel"><h2>seus cursos · {items.length}</h2>{items.map(c=><div className="row" key={c.id}><b>{c.title}</b><small>{c.status} · {c.lesson_count} aulas</small><div className="rowactions"><button onClick={()=>void addLesson(c)}>+ aula</button><button onClick={()=>void saveQuiz(c)}>avaliação</button><button onClick={()=>void publish(c)}>publicar</button></div></div>)}</section></div></main>}
function Admin({note,currentUserId}:{note:(s:string)=>void;currentUserId:string}){const[items,SI]=useState<U[]>([]),[query,SQ]=useState('');async function load(){SI((await api<{items:U[]}>('/api/v1/admin/users')).items)}useEffect(()=>{void load().catch(e=>note(e.message))},[]);async function role(u:U,r:string){try{await api(`/api/v1/admin/users/${u.id}`,{method:'PATCH',body:JSON.stringify({role:r})});await load();note('perfil atualizado.')}catch(e){note((e as Error).message)}}async function toggleStatus(u:U){try{await api(`/api/v1/admin/users/${u.id}`,{method:'PATCH',body:JSON.stringify({status:u.status==='active'?'suspended':'active'})});await load();note(u.status==='active'?'acesso suspenso.':'acesso reativado.')}catch(e){note((e as Error).message)}}async function removeStudent(u:U){if(u.role!=='student')return;if(!window.confirm(`Excluir permanentemente o aluno ${u.name} (${u.email})? Matrículas, favoritos e progresso também serão apagados.`))return;try{await api(`/api/v1/admin/users/${u.id}`,{method:'DELETE'});await load();note('aluno excluído do site e do banco de dados.')}catch(e){note((e as Error).message)}}const visible=items.filter(u=>`${u.name} ${u.email} ${u.role} ${u.status}`.toLowerCase().includes(query.trim().toLowerCase()));return <main className="dash"><small className="eyebrow">área administrativa</small><h1>visão geral da <em>plataforma.</em></h1><section className="panel"><h2>usuários · {items.length}</h2><div className="admin-tools"><label className="search"><Search size={15}/><input aria-label="Buscar por nome, e-mail, perfil ou estado" value={query} onChange={e=>SQ(e.target.value)} placeholder="buscar nome, e-mail ou perfil"/></label><small>{visible.length} encontrados</small></div>{visible.length?visible.map(u=><div className="row adminrow" key={u.id}><b>{u.name}<small>{u.email} · {u.status==='active'?'ativo':'suspenso'}</small></b><div className="admin-actions"><select aria-label={`Perfil de ${u.name}`} disabled={u.id===currentUserId} value={u.role} onChange={e=>void role(u,e.target.value)}><option value="student">aluno</option><option value="instructor">professor</option><option value="admin">administrador</option></select><button className="status-action" disabled={u.id===currentUserId} onClick={()=>void toggleStatus(u)}>{u.status==='active'?'suspender':'reativar'}</button>{u.role==='student'&&<button className="delete-action" onClick={()=>void removeStudent(u)}>excluir</button>}</div></div>):<p className="empty">nenhum usuário corresponde à busca.</p>}</section></main>}
const authSchema=z.object({name:z.string().optional(),email:z.email('Informe um e-mail válido.'),password:z.string().min(10,'A senha precisa ter ao menos 10 caracteres.')});
type AuthFields=z.infer<typeof authSchema>;
function Auth({mode,close,submit,setMode}:{mode:string;close:()=>void;submit:(e:string,p:string,n?:string)=>Promise<void>;setMode:(s:string)=>void}){
  const opener = React.useRef<HTMLElement | null>(null);
  const{register,handleSubmit,setFocus,setError,clearErrors,formState:{errors,isSubmitting}}=useForm<AuthFields>({resolver:zodResolver(authSchema),defaultValues:{name:'',email:'',password:''}});
  useEffect(() => {
    clearErrors();
    setFocus(mode === 'register' ? 'name' : 'email');
  }, [mode, clearErrors, setFocus]);
  const go=async(values:AuthFields)=>{
    if(mode==='register'&&(!values.name||values.name.trim().length<2)){
      setError('name',{message:'Informe seu nome com pelo menos 2 caracteres.'});return;
    }
    try{await submit(values.email,values.password,mode==='register'?values.name:undefined)}
    catch(x){setError('root',{message:(x as Error).message})}
  };
  return <Dialog.Root open onOpenChange={open => { if (!open) close(); }}>
    <Dialog.Portal><Dialog.Overlay className="veil" onClick={event => {
      if (event.target === event.currentTarget) close();
    }}><Dialog.Content className="modal"
      onOpenAutoFocus={event => {
        event.preventDefault();
        opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        setFocus(mode === 'register' ? 'name' : 'email');
      }}
      onCloseAutoFocus={event => {
        event.preventDefault();
        const trigger = opener.current;
        const target = trigger?.isConnected && trigger.getClientRects().length ? trigger : document.querySelector<HTMLElement>('header .brand');
        target?.focus();
      }}>
    <button className="close" type="button" aria-label="Fechar" onClick={close}><X/></button><i><GraduationCap/></i>
    <small className="eyebrow">sua próxima conquista começa aqui</small>
    <Dialog.Title>{mode==='login'?'bem-vindo de volta.':'crie sua conta.'}</Dialog.Title>
    <Dialog.Description>aprenda no seu ritmo com a LearnPlay.</Dialog.Description>
    <form noValidate onSubmit={handleSubmit(go)}>
      {mode==='register'&&<label>nome<input required minLength={2} autoComplete="name" aria-invalid={!!errors.name} {...register('name')}/>{errors.name&&<small className="error" role="alert">{errors.name.message}</small>}</label>}
      <label>e-mail<input required type="email" autoComplete="email" aria-invalid={!!errors.email} {...register('email')}/>{errors.email&&<small className="error" role="alert">{errors.email.message}</small>}</label>
      <label>senha<input required minLength={10} type="password" autoComplete={mode==='login'?'current-password':'new-password'} aria-invalid={!!errors.password} {...register('password')}/>{errors.password&&<small className="error" role="alert">{errors.password.message}</small>}</label>
      {errors.root&&<small className="error" role="alert">{errors.root.message}</small>}
      <button className="primary wide" disabled={isSubmitting}>{isSubmitting?'aguarde...':mode==='login'?'entrar':'criar minha conta'}　→</button>
    </form>
    <small className="switch">{mode==='login'?'ainda não tem conta?':'já tem conta?'} <button type="button" onClick={()=>setMode(mode==='login'?'register':'login')}>{mode==='login'?'crie agora':'entrar'}</button></small>
    {['localhost','127.0.0.1'].includes(window.location.hostname)&&<div className="demo"><b>contas para teste local</b><span>aluno: aluna@learnplay.local · Aluno12345!</span><span>professor: professor@learnplay.local · Professor123!</span><span>admin: admin@learnplay.local · Admin123456!</span></div>}
  </Dialog.Content></Dialog.Overlay></Dialog.Portal>
  </Dialog.Root>
}

createRoot(document.getElementById('root')!).render(<QueryClientProvider client={queryClient}><App/></QueryClientProvider>);



