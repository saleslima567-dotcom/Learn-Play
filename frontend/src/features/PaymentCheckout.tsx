import { ArrowLeft, CheckCircle2, CreditCard, Download, QrCode } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { money } from '../presentation';
import './payment-checkout.css';

const methods = [
  { id: 'pix', label: 'Pix', Icon: QrCode },
  { id: 'credit', label: 'Cartão de crédito', Icon: CreditCard },
  { id: 'debit', label: 'Cartão de débito', Icon: CreditCard },
] as const;
type Method = typeof methods[number]['id'];

type Payment = {
  enrollment_status: string;
  available: boolean;
  course_title: string;
  amount: number;
  method: Method | null;
  reference: string | null;
  qr_url: string | null;
  receipt_url: string | null;
};

type Props = {
  enrollmentId: string;
  userId?: string;
  api: <T>(path: string, init?: RequestInit) => Promise<T>;
  back: () => void;
  approved: () => Promise<void>;
};

export function readPaymentEnrollment() {
  const id = new URLSearchParams(window.location.search).get('pagamento');
  return id && /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(id) ? id : null;
}

export function PaymentCheckout({ enrollmentId, userId, api, back, approved }: Props) {
  const [choice, setChoice] = useState<Method>();
  const [editing, setEditing] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const queryClient = useQueryClient();
  const path = `/api/v1/me/enrollments/${enrollmentId}/payment`;
  const key = ['demo-payment', userId, enrollmentId];
  const payment = useQuery({ queryKey: key, queryFn: () => api<Payment>(path) });
  const change = useMutation({
    mutationFn: (method: Method) => api<Payment>(path, { method: 'POST', body: JSON.stringify({ method }) }),
    onSuccess: next => {
      queryClient.setQueryData(key, next);
      setEditing(false);
    },
  });
  const confirm = useMutation({
    mutationFn: (reference: string) => api<Payment>(`${path}/approve`, {
      method: 'POST', body: JSON.stringify({ reference }),
    }),
    onSuccess: async next => {
      queryClient.setQueryData(key, next);
      await approved();
    },
    onError: () => {
      void payment.refetch();
    },
  });

  const data = payment.data;
  const active = data?.enrollment_status === 'active';
  const method = methods.find(option => option.id === data?.method);
  const selected = choice ?? data?.method ?? 'pix';
  const reviewing = Boolean(data?.available && data.reference && method && !editing);
  const error = confirm.error ?? change.error;
  const busy = confirm.isPending || change.isPending;
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [active, reviewing]);

  return <main className="payment-page">
    <button className="back" onClick={back}><ArrowLeft size={15}/> Meus cursos</button>
    <h1 ref={heading} tabIndex={-1}>{active ? 'Matrícula confirmada' : 'Pagamento de teste'}</h1>
    <p className="payment-notice">Demonstração do LearnPlay. Nenhuma cobrança será feita.</p>
    {payment.isPending && <p role="status">Carregando matrícula…</p>}
    {payment.isError && !data && <div role="alert"><p>{payment.error.message}</p>
      <button className="back" onClick={() => void payment.refetch()}>Tentar novamente</button></div>}
    {data && <div className="payment-layout">
      <section className="payment-summary" aria-label="Resumo da matrícula">
        <h2>{data.course_title}</h2>
        <span>Valor da simulação</span><strong>{money(data.amount)}</strong>
      </section>
      <section className="payment-step" aria-label="Pagamento">
        {active ? <div className="payment-result">
          <CheckCircle2 size={24} aria-hidden="true"/>
          <p>O curso está disponível em Meus cursos.</p>
          {data.receipt_url && <a className="primary" href={data.receipt_url}>
            <Download size={16} aria-hidden="true"/> Baixar comprovante em PDF
          </a>}
        </div> : !data.available ? <p>Este curso está indisponível para pagamento.</p> : reviewing && method ? <>
          <h2>{method.label} de teste</h2>
          {data.qr_url ? <div className="payment-pix">
            <img src={data.qr_url} width={188} height={188} alt="QR Code da simulação LearnPlay"/>
            <p>O QR Code identifica este teste e não pode ser pago pelo aplicativo do banco.</p>
          </div> : <p>A simulação usa um cartão fictício. Nenhum dado do seu cartão é necessário.</p>}
          <div className="payment-actions">
            <button className="primary" disabled={busy} onClick={() => data.reference && confirm.mutate(data.reference)}>
              {confirm.isPending ? 'Confirmando…' : 'Simular pagamento'}
            </button>
            <button className="back" disabled={busy} onClick={() => { confirm.reset(); setEditing(true); }}>
              Trocar forma de pagamento
            </button>
          </div>
        </> : <form onSubmit={event => { event.preventDefault(); confirm.reset(); change.mutate(selected); }}>
          <fieldset className="payment-methods" disabled={busy}>
            <legend>Forma de pagamento</legend>
            {methods.map(({ id, label, Icon }) => <label key={id}>
              <input type="radio" name="payment-method" value={id} checked={selected === id} onChange={() => setChoice(id)}/>
              <Icon size={18} aria-hidden="true"/><span>{label}</span>
            </label>)}
          </fieldset>
          <button className="primary" disabled={busy}>{change.isPending ? 'Preparando…' : 'Continuar'}</button>
        </form>}
        {error && <p role="alert">{error.message}</p>}
      </section>
    </div>}
  </main>;
}
