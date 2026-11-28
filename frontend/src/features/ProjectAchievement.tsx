import { useState } from 'react';
import type { FormEvent } from 'react';

export function ProjectAchievement({ title, saved, save }: {
  title: string; saved?: string | null; save: (url: string) => Promise<string>;
}) {
  const [link, setLink] = useState(saved ?? '');
  const [publishedLink, setPublishedLink] = useState(saved ?? '');
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus('');
    try {
      const url = await save(link.trim());
      setPublishedLink(url);
      setLink(url);
      setStatus('Entrega registrada.');
    } catch (error) {
      setStatus((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return <section className="project-achievement" aria-labelledby="achievement-heading">
    <h2 id="achievement-heading">{publishedLink ? 'Conquista registrada' : 'Registre sua entrega'}</h2>
    <p>{title}</p>
    <form onSubmit={submit}>
      <label htmlFor="project-url">Link privado da sua entrega</label>
      <input id="project-url" type="url" placeholder="https://…" value={link} maxLength={2048} required
        onChange={event => setLink(event.target.value)}/>
      <button className="primary" disabled={busy}>{busy ? 'Salvando…' : 'Salvar entrega'}</button>
    </form>
    <p role="status">{status}</p>
    {publishedLink && <a className="discovery-link" href={publishedLink} target="_blank" rel="noopener noreferrer">Abrir minha entrega</a>}
  </section>;
}
