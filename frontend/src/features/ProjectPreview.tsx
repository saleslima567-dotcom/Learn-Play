import { useId, useRef, useState } from 'react';
import type { TopicId } from './coursePractice';
import { TaskPreview } from './TaskPreview';

function GitPreview() {
  const [stage, setStage] = useState<'branch' | 'review' | 'merged'>('branch');
  const surface = useRef<HTMLElement>(null);
  function advance(next: typeof stage, selector: string) {
    setStage(next);
    requestAnimationFrame(() => surface.current?.querySelector<HTMLElement>(selector)?.focus());
  }

  return <section className="preview-surface" aria-label="Simulação de pull request" ref={surface}>
    <h3>Uma alteração no README</h3>
    <p>A branch <code>docs/como-usar</code> tem uma instrução que ainda falta na <code>main</code>.</p>
    {stage === 'branch' ? <button className="primary" onClick={() => advance('review', 'pre')}>Comparar branches</button> :
      <div className="preview-diff">
        <p><code>docs/como-usar</code> para <code>main</code></p>
        <pre tabIndex={-1} aria-label="Alteração no README"><code> README.md{'\n'} ## Como usar{'\n'}<mark>+ Execute python tarefas.py</mark></code></pre>
        {stage === 'review' ? <button className="primary" onClick={() => advance('merged', '[role=status]')}>Simular merge</button> :
          <p role="status" tabIndex={-1}>Alteração integrada. A instrução agora aparece no README da <code>main</code> nesta simulação.</p>}
        <button className="discovery-link" onClick={() => advance('branch', 'button')}>Reiniciar demonstração</button>
      </div>}
  </section>;
}

function DesignPreview() {
  const id = useId();
  const emailInput = useRef<HTMLInputElement>(null);
  const confirmation = useRef<HTMLParagraphElement>(null);
  const [name, setName] = useState('Ana');
  const [email, setEmail] = useState('ana.exemplo.com');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);

  return <section className="preview-surface" aria-label="Demonstração do formulário de inscrição">
    <h3>Inscrição na oficina</h3>
    {sent ? <>
      <p ref={confirmation} role="status" tabIndex={-1}><strong>Inscrição confirmada na demonstração.</strong></p>
      <button className="discovery-link" onClick={() => { setSent(false); requestAnimationFrame(() => emailInput.current?.focus()); }}>Voltar ao formulário</button>
    </> : <>
      <p>Envie o formulário de exemplo, veja o erro e corrija o e-mail.</p>
      <form className="preview-fields" onSubmit={event => {
        event.preventDefault();
        if (!emailInput.current?.validity.valid) {
          setError('Confira o endereço. Use o formato ana@exemplo.com.');
          emailInput.current?.focus();
          return;
        }
        setError('');
        setSent(true);
        requestAnimationFrame(() => confirmation.current?.focus());
      }} noValidate>
        <label htmlFor={`${id}-name`}>Nome</label>
        <input id={`${id}-name`} autoComplete="off" value={name} maxLength={80} onChange={event => setName(event.target.value)}/>
        <label htmlFor={`${id}-email`}>E-mail</label>
        <input id={`${id}-email`} ref={emailInput} type="email" autoComplete="off" value={email}
          required aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined}
          maxLength={120} onChange={event => { setEmail(event.target.value); setError(''); }}/>
        {error && <p id={`${id}-error`} role="alert">{error}</p>}
        <button className="primary" disabled={!name.trim()}>Simular inscrição</button>
      </form>
    </>}
  </section>;
}

const feedbackFields = [
  { label: 'O que aconteceu?', example: 'A revisão ficou pronta depois das 17h.' },
  { label: 'O que mudou com isso?', example: 'Tivemos de enviar o trabalho na manhã seguinte.' },
  { label: 'O que vocês podem combinar?', example: 'Na próxima entrega, podemos fechar a revisão até as 16h?' },
];

function CommunicationPreview() {
  const id = useId();
  const [parts, setParts] = useState(['', '', '']);
  const message = parts.map(part => part.trim()).filter(Boolean).join(' ');

  return <section className="preview-surface" aria-label="Rascunho de feedback">
    <h3>Feedback sobre uma entrega</h3>
    <p>Uma revisão atrasou e a equipe perdeu o prazo. Escreva o que você diria a quem fez a revisão.</p>
    <button className="discovery-link" onClick={() => setParts(feedbackFields.map(field => field.example))}>Preencher com um exemplo</button>
    <div className="preview-fields">
      {feedbackFields.map((field, index) => <div key={field.label}>
        <label htmlFor={`${id}-${index}`}>{field.label}</label>
        <textarea id={`${id}-${index}`} rows={2} maxLength={220} value={parts[index]}
          onChange={event => setParts(current => current.map((part, position) => position === index ? event.target.value : part))}/>
      </div>)}
    </div>
    {message && <div className="preview-message"><strong>Seu rascunho</strong><p>{message}</p></div>}
  </section>;
}

export function ProjectPreview({ topic }: { topic: TopicId }) {
  switch (topic) {
    case 'git': return <GitPreview/>;
    case 'design': return <DesignPreview/>;
    case 'comunicacao': return <CommunicationPreview/>;
    case 'python': return <TaskPreview/>;
  }
}
