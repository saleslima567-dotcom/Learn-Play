import { ArrowLeft, BookOpen, CheckCircle2, CreditCard, Download, QrCode, WalletCards } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { money } from '../presentation';
import './payment-checkout.css';

const methods = [
  { id: 'pix', label: 'Pix', description: 'QR Code para a simulação', Icon: QrCode },
  { id: 'credit', label: 'Cartão de crédito', description: 'Pagamento de teste com cartão fictício', Icon: CreditCard },
  { id: 'debit', label: 'Cartão de débito', description: 'Débito simulado em conta', Icon: WalletCards },
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
  userId: string;
  api: <T>(path: string, init?: RequestInit) => Promise<T>;
  back: () => void;
  approved: () => Promise<void>;
};

export function readPaymentEnrollment() {
  const id = new URLSearchParams(window.location.search).get('pagamento');
  return id && /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(id) ? id : null;
}

export function PaymentCheckout({ enrollmentId, userId, api, back, approved }: Props) {
  const [preparing, setPreparing] = useState<Method>();
  const heading = useRef<HTMLHeadingElement>(null);
  const queryClient = useQueryClient();
  const path = `/api/v1/me/enrollments/${enrollmentId}/payment`;
  const key = ['demo-payment', userId, enrollmentId];
  const payment = useQuery({ queryKey: key, queryFn: () => api<Payment>(path) });
  const change = useMutation({
    mutationFn: (method: Method) => api<Payment>(path, { method: 'POST', body: JSON.stringify({ method }) }),
    onSuccess: next => queryClient.setQueryData(key, next),
    onSettled: () => setPreparing(undefined),
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
  const selected = preparing ?? data?.method;
  const method = methods.find(option => option.id === selected);
  const error = confirm.error ?? change.error;
  const busy = Boolean(preparing || confirm.isPending || change.isPending || payment.isFetching);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
  }, [active]);

  function select(methodId: Method) {
    if (busy || (methodId === data?.method && data.reference)) return;
    confirm.reset();
    setPreparing(methodId);
    change.mutate(methodId);
  }

  return <main className="payment-page" aria-labelledby="payment-heading">
    <button className="back payment-back" onClick={back}><ArrowLeft size={16} aria-hidden="true"/> Meus cursos</button>
    <h1 id="payment-heading" ref={heading} tabIndex={-1}>{active ? 'Matrícula confirmada' : 'Pagamento da matrícula'}</h1>
    <p className="payment-notice"><span>Modo de teste</span> Nenhuma cobrança será feita.</p>
    {payment.isPending && <p role="status">Carregando matrícula…</p>}
    {payment.isError && !data && <div className="payment-error" role="alert">
      <p>{payment.error.message}</p>
      <button className="back" onClick={() => void payment.refetch()}>Tentar novamente</button>
    </div>}
    {data && <form className="payment-layout" onSubmit={event => {
      event.preventDefault();
      if (!busy && data.available && data.reference && !change.isError) confirm.mutate(data.reference);
    }}>
      <section className="payment-step" aria-label="Formas de pagamento">
        {active ? <div className="payment-result">
          <span className="payment-result-icon"><CheckCircle2 size={24} aria-hidden="true"/></span>
          <h2>Seu curso está liberado</h2>
          <p>Abra a sala de aula em Meus cursos. Seu comprovante também fica disponível por lá.</p>
          <div className="payment-result-actions">
            {data.receipt_url && <a className="primary" href={data.receipt_url}>
              <Download size={16} aria-hidden="true"/> Baixar comprovante em PDF
            </a>}
            <button type="button" className="back" onClick={back}>Ir para Meus cursos</button>
          </div>
        </div> : !data.available ? <p>Este curso está indisponível para pagamento.</p> : <>
          <fieldset className="payment-methods" aria-disabled={busy}>
            <legend>Como você quer pagar?</legend>
            {methods.map(({ id, label, description, Icon }) => <label className="payment-option" key={id}>
              <span className="payment-option-icon"><Icon size={21} aria-hidden="true"/></span>
              <span className="payment-option-text">
                <span id={`payment-label-${id}`}>{label}</span>
                <small id={`payment-description-${id}`}>{description}</small>
              </span>
              <input type="radio" name="payment-method" value={id} checked={selected === id}
                aria-labelledby={`payment-label-${id}`} aria-describedby={`payment-description-${id}`}
                disabled={confirm.isPending} onChange={() => select(id)}/>
            </label>)}
          </fieldset>
          <div aria-live="polite">
            {preparing ? <p className="payment-method-detail">Preparando {method?.label.toLowerCase()}…</p>
              : data.qr_url ? <div className="payment-method-detail payment-pix">
                <img src={data.qr_url} width={136} height={136} alt="QR Code do Pix de teste"/>
                <div><h3>Pix de teste</h3><p>Este QR Code identifica a simulação no LearnPlay. Para concluir, use o botão de confirmação.</p></div>
              </div>
              : method && <p className="payment-method-detail">Na simulação com cartão, basta confirmar. Nenhum dado do seu cartão é solicitado.</p>}
          </div>
        </>}
      </section>
      <section className="payment-summary" aria-labelledby="payment-summary-heading">
        <h2 id="payment-summary-heading">Resumo da matrícula</h2>
        <div className="payment-course">
          <span className="payment-course-icon"><BookOpen size={19} aria-hidden="true"/></span>
          <h3>{data.course_title}</h3>
        </div>
        <dl className="payment-totals">
          <div><dt>Forma de pagamento</dt><dd>{method?.label ?? 'A escolher'}</dd></div>
          <div className="payment-total"><dt>Total simulado</dt><dd>{money(data.amount)}</dd></div>
        </dl>
        {!active && data.available && <>
          <button type="submit" className="primary payment-confirm" disabled={busy || !data.reference || change.isError}>
            {confirm.isPending ? 'Confirmando pagamento…' : 'Confirmar pagamento'}
          </button>
          <p className="payment-summary-note">{data.reference ? 'A confirmação libera as aulas e o comprovante em PDF.' : 'Escolha uma forma de pagamento para confirmar.'}</p>
          {error && <div className="payment-error" role="alert">
            <p>{error.message}</p>
            {change.isError && change.variables && <button type="button" className="back" disabled={busy}
              onClick={() => change.variables && select(change.variables)}>Tentar preparar novamente</button>}
          </div>}
        </>}
      </section>
    </form>}
  </main>;
}
