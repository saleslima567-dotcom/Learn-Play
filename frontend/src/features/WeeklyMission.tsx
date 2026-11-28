import { topicsUrl } from './Discovery';

const missions = [
  { theme: 'python', title: 'Encontre as tarefas pendentes', instructions: 'Crie uma lista com três tarefas. Use um laço para exibir apenas as que ainda não foram concluídas.', check: 'O terminal exibe as duas tarefas pendentes e omite a concluída.' },
  { theme: 'git', title: 'Revise uma mudança antes de integrar', instructions: 'No seu repositório de treino, crie uma branch para ajustar uma instrução no README. Abra um pull request e escreva como alguém pode conferir a mudança.', check: 'O diff tem a alteração esperada e a descrição explica como conferi-la.' },
  { theme: 'design', title: 'Ajude alguém a corrigir um campo', instructions: 'Desenhe o estado de erro de um formulário de inscrição. Escreva a mensagem, marque o campo e mostre o que a pessoa deve digitar.', check: 'Em escala de cinza, outra pessoa identifica o campo e consegue explicar como corrigir o erro.' },
  { theme: 'comunicacao', title: 'Transforme um atraso em um acordo', instructions: 'Escreva um aviso sobre a mudança de um prazo. Feche com duas ações, cada uma com responsável e data.', check: 'Um colega consegue identificar o novo prazo e as duas ações sem pedir detalhes.' },
];
const dayMs = 86_400_000;

export function WeeklyMission() {
  const parts = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo', year: 'numeric', month: 'numeric', day: 'numeric',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map(part => [part.type, Number(part.value)]));
  const localDate = new Date(Date.UTC(values.year, values.month - 1, values.day));
  const monday = localDate.getTime() - ((localDate.getUTCDay() + 6) % 7) * dayMs;
  const elapsed = Math.round((monday - Date.UTC(2026, 10, 23)) / (7 * dayMs));
  const mission = missions[((elapsed % missions.length) + missions.length) % missions.length];
  const date = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit', timeZone: 'UTC' });
  return <main className="dash discovery">
    <h1>Missão da semana</h1>
    <p>{date.format(monday)} a {date.format(monday + 6 * dayMs)} · Horário de Brasília</p>
    <article className="project-card project-card-copy">
      <h2>{mission.title}</h2>
      <p>{mission.instructions}</p>
      <h3>Como conferir</h3><p>{mission.check}</p>
      <a className="discovery-link" href={`${topicsUrl}&tema=${mission.theme}`}>Estudar o tema desta missão</a>
    </article>
  </main>;
}
