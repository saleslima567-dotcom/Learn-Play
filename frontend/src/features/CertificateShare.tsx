import { useId, useState } from 'react';

export function CertificateShare({ initialUrl, update }: {
  initialUrl?: string | null;
  update: (method: 'PUT' | 'DELETE') => Promise<string | null>;
}) {
  const [url, setUrl] = useState(initialUrl ?? null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const id = useId();

  async function change(method: 'PUT' | 'DELETE') {
    setBusy(true);
    setStatus('');
    try {
      setUrl(await update(method));
      setStatus(method === 'PUT' ? 'Link gerado.' : 'Link desativado.');
    } catch (error) {
      setStatus((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return <section className="certificate-share" aria-labelledby={`${id}-title`}>
    <h2 id={`${id}-title`}>Compartilhar certificado</h2>
    <p>Quem tiver o link poderá ver seu nome, o curso e a data de emissão do link.</p>
    {url ? <>
      <label htmlFor={id}>Link de verificação</label>
      <input id={id} type="url" readOnly value={new URL(url, window.location.origin).href}
        onFocus={event => event.target.select()}/>
      <a className="discovery-link" href={url} target="_blank" rel="noopener noreferrer">Abrir página de verificação</a>
      <button className="back" disabled={busy} onClick={() => void change('DELETE')}>Desativar link</button>
    </> : <button className="back" disabled={busy} onClick={() => void change('PUT')}>Gerar link de verificação</button>}
    {status && <p role="status">{status}</p>}
  </section>;
}
