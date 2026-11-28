import { useId, useState } from 'react';
import type { TopicId } from './coursePractice';
import { TaskPreview } from './TaskPreview';

const scenarios = {
  git: {
    question: 'Seu README mudou na branch docs/como-usar. Qual pull request inclui essa alteração?',
    options: ['Base main ← docs/como-usar', 'Base docs/como-usar ← main', 'Base main ← main'],
    answers: ['Isso mesmo. A branch main recebe a mudança feita em docs/como-usar.', 'A direção está invertida. A base é a branch que recebe a alteração.', 'Escolha docs/como-usar como origem para incluir a mudança do README.'],
  },
  design: {
    question: 'Uma pessoa digitou um e-mail sem @. Qual mensagem ajuda a concluir a inscrição?',
    options: ['Erro', 'Confira o e-mail. Use um formato como nome@exemplo.com.', 'Seu formulário foi encerrado.'],
    answers: ['Informe qual campo precisa de correção e mostre o formato esperado.', 'Isso mesmo. A mensagem localiza o problema e ajuda a corrigir o campo.', 'Mantenha os dados na tela e deixe a pessoa corrigir o e-mail.'],
  },
  comunicacao: {
    question: 'Uma revisão atrasou a entrega. Qual feedback ajuda a equipe a agir?',
    options: ['Você nunca se organiza.', 'Precisamos melhorar alguma coisa.', 'A revisão chegou após as 17h e adiou o envio. O que ajudaria a cumprir o prazo na próxima entrega?'],
    answers: ['Descreva um fato observado e seu impacto, sem generalizar sobre a pessoa.', 'Inclua o que ocorreu e abra espaço para combinar uma ação.', 'Isso mesmo. O texto descreve o fato, explica o impacto e convida a pessoa a propor uma solução.'],
  },
};

export function ProjectPreview({ topic }: { topic: TopicId }) {
  const [selected, setSelected] = useState<number>();
  const name = useId();
  if (topic === 'python') return <TaskPreview/>;
  const scenario = scenarios[topic];
  return <div className="project-scenario">
    <fieldset>
      <legend>{scenario.question}</legend>
      {scenario.options.map((option, index) => <label key={option}>
        <input type="radio" name={name} checked={selected === index} onChange={() => setSelected(index)}/>
        <span>{option}</span>
      </label>)}
    </fieldset>
    <p role="status">{selected !== undefined && scenario.answers[selected]}</p>
  </div>;
}
