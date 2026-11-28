import projectFile from './materials/tarefas.py?url';
import summaryFile from './materials/resumo-python.txt?url';

const questions = [
  {
    id: 'lista', title: 'Depois de atribuir tarefas[1] = "Testar", o que muda na lista?',
    lesson: 'Variáveis e tipos de dados',
    options: ['O primeiro item muda.', 'O segundo item muda.', 'Um novo item é adicionado.'],
    correct: 1, explanation: 'Contamos as posições a partir de 0. A posição 1 é a segunda.',
  },
  {
    id: 'laco', title: 'Se tarefas for uma lista vazia, o que acontece num laço for tarefa in tarefas?',
    lesson: 'Decisões e repetições',
    options: ['O corpo do laço não executa.', 'O corpo executa uma vez.', 'Python cria um item vazio.'],
    correct: 0, explanation: 'O laço executa uma vez por item. Uma lista vazia não fornece nenhum item.',
  },
  {
    id: 'menu', title: 'Se a pessoa selecionar a tarefa 3 no menu, qual índice o programa deve usar?',
    lesson: 'Projeto: lista de tarefas',
    options: ['3', '1', '2'],
    correct: 2, explanation: 'Os números do menu começam em 1. Subtraia 1 para obter o índice da lista.',
  },
];

export type PracticeAnswers = Record<string, number>;

export function PythonMaterials({ projectLesson }: { projectLesson: boolean }) {
  return <section className="python-materials" aria-labelledby="python-materials-title">
    <h3 id="python-materials-title">Materiais da aula</h3>
    <a className="discovery-link" href={summaryFile} download="resumo-python.txt">Baixar resumo de Python</a>
    {projectLesson && <a className="discovery-link" href={projectFile} download="tarefas.py">Baixar tarefas.py</a>}
  </section>;
}

export function PythonPractice({ answers, checked, choose, check, review }: {
  answers: PracticeAnswers; checked: PracticeAnswers;
  choose: (id: string, option: number) => void; check: () => void; review: (title: string) => void;
}) {
  return <form className="quiz" aria-labelledby="lesson-content-title" onSubmit={event => {
    event.preventDefault();
    check();
  }}>
    <h2 id="lesson-content-title" tabIndex={-1}>Prática de Python</h2>
    <p>Confira uma ou mais respostas. Você pode revisar a aula e tentar de novo.</p>
    {questions.map(question => {
      const submitted = checked[question.id] !== undefined && checked[question.id] === answers[question.id];
      const correct = checked[question.id] === question.correct;
      return <fieldset key={question.id}>
        <legend>{question.title}</legend>
        {question.options.map((option, index) => <label key={option}>
          <input type="radio" name={question.id} checked={answers[question.id] === index}
            onChange={() => choose(question.id, index)}/>{option}
        </label>)}
        {submitted && <p role="status">{correct ? question.explanation : 'Vale revisar este ponto da aula.'}</p>}
        {submitted && !correct && <button type="button" className="discovery-link" onClick={() => review(question.lesson)}>
          Revisar: {question.lesson}
        </button>}
      </fieldset>;
    })}
    <button className="primary" disabled={!Object.keys(answers).length}>Conferir respostas</button>
  </form>;
}
