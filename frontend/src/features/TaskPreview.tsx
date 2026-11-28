import { useId, useState } from 'react';

export function TaskPreview() {
  const inputId = useId();
  const [tasks, setTasks] = useState([{ id: 0, label: 'Baixar o material da aula', done: false }]);
  const [input, setInput] = useState('');
  const completed = tasks.filter(task => task.done).length;

  return <section className="task-preview" aria-label="Prévia interativa da lista de tarefas">
    <h3>Minha lista de tarefas</h3>
    <p>Adicione uma tarefa e marque quando terminar. Na trilha, você vai programar essas duas ações em Python.</p>
    <form onSubmit={event => {
      event.preventDefault();
      const label = input.trim();
      if (!label || tasks.length >= 8) return;
      setTasks(items => [...items, { id: items.length, label, done: false }]);
      setInput('');
    }}>
      <label htmlFor={inputId}>Nova tarefa</label>
      <div><input id={inputId} value={input} maxLength={80} disabled={tasks.length >= 8}
        onChange={event => setInput(event.target.value)} placeholder="Ex.: revisar as anotações" />
      <button className="primary" disabled={!input.trim() || tasks.length >= 8}>Adicionar</button></div>
    </form>
    <ul>{tasks.map(task => <li key={task.id}><label>
      <input type="checkbox" checked={task.done} onChange={() => setTasks(items =>
        items.map(item => item.id === task.id ? { ...item, done: !item.done } : item))} />
      <span>{task.label}</span>
    </label></li>)}</ul>
    <small role="status">{completed} de {tasks.length} concluídas{tasks.length >= 8 && ' · Limite de 8 tarefas nesta prévia'}</small>
  </section>;
}
